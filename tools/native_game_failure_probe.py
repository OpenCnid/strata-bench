"""Fixed local truncated-response control; real game observation, zero paid calls/helpers."""

import hashlib
import json

from mcbench.storage import Fault, Principal, require
from native_game_probe import GameProbe

POLICY = "truncated-response-after-observation/1"


def contains_observation(value, depth=0):
    if depth > 16:
        return False
    if isinstance(value, dict):
        return value.get("native_failure_observation_received") is True or any(
            contains_observation(v, depth + 1) for v in value.values())
    if isinstance(value, list):
        return any(contains_observation(v, depth + 1) for v in value)
    if isinstance(value, str):
        for line in [value, *value.splitlines()]:
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if parsed != value and contains_observation(parsed, depth + 1):
                return True
    return False


class GameTransportFailureProbe(GameProbe):
    def __init__(self, descriptor, lease_id):
        super().__init__(descriptor, lease_id)
        self.injected = None

    def code(self):
        return 'const scope=' + json.dumps(self.scope) + r''';
const tool=ALL_TOOLS.find(t=>t.name.endsWith("__game"));
if (!tool) throw new Error("GAME_TOOL_MISSING");
await new Promise(resolve=>setTimeout(resolve,550));
const request={schema:"strata/GameRequest/1",...scope,request_id:"native-failure-observe",
  deadline_at:new Date(Date.now()+5000).toISOString(),method:"observe",action:null,
  target_request_id:null,after:null};
const returned=await tools[tool.name]({request});
if (returned.isError) throw new Error("GAME_OBSERVATION_FAILED");
const response=JSON.parse(returned.content[0].text);
if(response.status!=="ok" || response.result.is_example || !response.result.state.connected)
  throw new Error("REAL_GAME_NOT_CONNECTED");
// The full filtered observation is already retained by the broker. Keep the
// acknowledgment small so native output truncation cannot cut its JSON record.
text({native_failure_observation_received:true,observation_id:response.result.observation_id,
  connected:response.result.state.connected});
'''

    def truncate(self, handler, operation, model, outputs):
        from native_dispatch_probe import sse
        require(self.injected is None and model == "gpt-6-luna"
                and contains_observation(outputs), "GAME_FAILURE_TRIGGER")
        response = {"id": "response-" + operation, "object": "response", "created_at": 1,
                    "model": model, "status": "in_progress", "output": []}
        raw = sse("response.created", response=response) + b'data: {"type":"response.completed","response":'
        self.injected = {"operation": operation, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        handler.response_started = True
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.end_headers()
        handler.wfile.write(raw)
        handler.wfile.flush()
        raise Fault("SYNTHETIC_STREAM_INTERRUPTED")

    def report(self, db, plan, provider):
        rows = [dict(r) for r in db.connection.execute(
            "SELECT c.thread,c.request,c.state,c.result,r.body AS request_body FROM broker_game_calls c "
            "LEFT JOIN broker_game_requests r ON (r.runtime=c.runtime AND r.thread=c.thread AND r.request=c.request) "
            "WHERE c.runtime=? ORDER BY c.rowid", (plan.job_id,))]
        observations = [json.loads(r["result"]) for r in rows if r["result"]]
        observed = [r["result"] for r in observations if r.get("status") == "ok"
                    and isinstance(r.get("result"), dict)
                    and r["result"].get("schema") == "mcbench/Observation/1"]
        lane = db.connection.execute("SELECT state,stop_result FROM native_worker_bindings WHERE job=?", (plan.job_id,)).fetchone()
        return {"game_evidence": "authentic_worker", "model_evidence": "synthetic_provider", "reasoning_qualified": False,
                "game_calls": rows, "stop_result": json.loads(lane["stop_result"]) if lane and lane["stop_result"] else None,
                "checks": {"real_observation_returned": len(observed) >= 2 and all(
                    o["is_example"] is False and o["state"]["connected"] for o in observed),
                    "no_game_mutation": bool(rows) and all(r["request_body"] is not None and
                        json.loads(r["request_body"])["method"] == "observe" for r in rows),
                    "all_game_requests_settled": bool(rows) and all(r["state"] == "SETTLED" for r in rows),
                    "one_executor_used_worker": len({r["thread"] for r in rows}) == 1,
                    "native_exit_stopped_game_lane": lane is not None and lane["state"] == "STOPPED",
                    "worker_credential_not_returned": self.descriptor["token"] not in json.dumps(provider.outputs)}}

    def failure_report(self, db, cas, plan, provider, result):
        attempts = [dict(r) for r in db.connection.execute("SELECT operation,state FROM inference_attempts ORDER BY rowid")]
        unknown = [r for r in attempts if r["state"] == "UNSETTLED"]
        events = [(r["kind"], json.loads(r["body"])) for r in db.connection.execute(
            "SELECT kind,body FROM outbox WHERE kind IN ('inference.transport_failure','inference.wire_capture') ORDER BY cursor")]
        target = self.injected or {}
        operation = target.get("operation")
        failures = [v for kind, v in events if kind == "inference.transport_failure" and v["operation_id"] == operation]
        captures = [v for kind, v in events if kind == "inference.wire_capture" and v["operation_id"] == operation]
        retained = db.connection.execute("SELECT uncertain,actual FROM operations WHERE id=?", (operation,)).fetchone()
        participants = [dict(r) for r in db.connection.execute("SELECT depth,state FROM native_participants WHERE job=?", (plan.job_id,))]
        raw = cas.read(Principal("operator", "operator"), "operator", captures[0]["raw_usage_ref"]) if len(captures) == 1 else b""
        checks = dict(result["game_integration"]["checks"])
        checks.update({
            "only_root_no_helpers": plan.helper_limit == 0 and len(participants) == 1 and participants[0]["depth"] == 0,
            "observation_delivered_before_fault": contains_observation(provider.outputs),
            "one_settled_one_unknown_dispatch": len(attempts) == 2 and len(unknown) == 1
                and unknown[0]["operation"] == operation and sum(r["state"] == "SETTLED" for r in attempts) == 1,
            "no_unknown_replay": len(provider.upstream_requests) == 2 and len({
                r["operation_id"] for r in provider.upstream_requests}) == 2,
            "unknown_reservation_retained": retained is not None and retained["uncertain"] == 1 and retained["actual"] is None,
            "no_fabricated_unknown_receipt": db.connection.execute("SELECT count(*) FROM ledger WHERE "
                "json_extract(body,'$.operation_id')=? AND json_extract(body,'$.posting')='settle'", (operation,)).fetchone()[0] == 0,
            "partial_wire_retained": len(captures) == 1 and len(raw) == target.get("bytes")
                and hashlib.sha256(raw).hexdigest() == target.get("sha256"),
            "typed_failure_diagnosed": len(failures) == 1 and failures[0]["phase"] == "receipt_validation"
                and failures[0]["reason"] == "TRUNCATED_EVENT_STREAM" and failures[0]["captured_bytes"] == len(raw),
            "accounting_closure_refused": result["closure"].get("state") == "UNSETTLED"
                and result["closure"].get("closure_error") == "METERING_UNKNOWN",
        })
        return {"policy": POLICY, "checks": checks, "injected": target, "attempts": attempts,
                "failures": failures, "captures": captures, "participants": participants,
                "real_model_requests": 0, "complete_checkpoint": False, "G0": "fail"}
