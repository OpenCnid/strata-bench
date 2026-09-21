"""Permanent helper capability retirement, backed by captured native tool evidence.

Revocation fences access immediately. Slot/envelope release additionally requires
a post-fence native status call, its actual return and settled descendant usage.
This operator-only service is not a gameplay tool or a provider-cancellation API.
"""

from typing import Annotated, Literal

from pydantic import Field

from .contracts import Digest, Id, Strict
from .inference_transport import MAX_RESPONSE_BYTES, ResponsesUsage, strict_json
from .records import BudgetLedger
from .storage import Principal, canonical, digest, require

POLICY = "native-fenced-participant-retirement/1"


class NativeParticipantRetirement(Strict):
    schema_: Literal["strata/NativeParticipantRetirement/1"] = Field(alias="schema")
    policy: Literal["native-fenced-participant-retirement/1"]
    is_example: bool
    job_id: Id
    profile_digest: Digest
    thread_id: Id
    issuance_operation: Id
    observation_operation: Id
    call_id: Annotated[str, Field(min_length=1, max_length=256)]


def private_bytes(db, cas, ref, limit):
    row = db.execute("SELECT visibility,media_type FROM objects WHERE namespace='operator' AND ref=?",
                     (ref,)).fetchone()
    require(row is not None and row["visibility"] == "operator", "RETIREMENT_EVIDENCE_PRIVATE")
    return cas.read(Principal("operator", "operator"), "operator", ref, max_bytes=limit), row["media_type"]


def index_native_tool_calls(db, cas, request, *, body=None):
    """Keep first observation across compaction; lazily index a legacy job's raw captures."""
    old = db.execute("SELECT raw_ref FROM native_tool_call_indexed_requests WHERE operation=?",
                     (request["operation"],)).fetchone()
    if old:
        require(old[0] == request["raw_ref"], "RETIREMENT_INDEX_SOURCE_CHANGED")
        return
    if body is None:
        raw, _ = private_bytes(db, cas, request["raw_ref"], 1024 * 1024)
        body = strict_json(raw)
    require(isinstance(body.get("input"), list), "RETIREMENT_INDEX_SOURCE_INVALID")
    for item in body["input"]:
        if not isinstance(item, dict) or item.get("type") not in {
                "function_call", "custom_tool_call", "function_call_output", "custom_tool_call_output"}:
            continue
        call = item.get("call_id")
        require(isinstance(call, str) and 0 < len(call) <= 256, "RETIREMENT_INDEX_SOURCE_INVALID")
        db.execute("INSERT INTO native_tool_call_ids VALUES(?,?,?,?) ON CONFLICT(job,thread,call_id) "
            "DO UPDATE SET first_ordinal=min(first_ordinal,excluded.first_ordinal)",
            (request["job"], request["thread"], call, request["ordinal"]))
    db.execute("INSERT INTO native_tool_call_indexed_requests VALUES(?,?)",
               (request["operation"], request["raw_ref"]))


class _CompletedResponse(ResponsesUsage):
    def __init__(self, model, media):
        super().__init__(model, media)
        self.response = None

    def _receipt(self, response):
        super()._receipt(response)
        require(response["status"] == "completed" and isinstance(response.get("output"), list),
                "RETIREMENT_TOOL_ISSUANCE")
        require(all(isinstance(item, dict) for item in response["output"]), "RETIREMENT_TOOL_ISSUANCE")
        require(self.response is None or canonical(self.response) == canonical(response),
                "RETIREMENT_TOOL_ISSUANCE")
        self.response = response


def _request(db, cas, plan, operation, after):
    from .native_admission import context_metadata
    row = db.execute("SELECT a.rowid ordinal,a.*,p.depth,p.state participant_state FROM "
        "native_request_admissions a JOIN native_participants p ON a.job=p.job AND a.thread=p.thread "
        "WHERE a.operation=?", (operation,)).fetchone()
    require(row is not None and row["job"] == plan.job_id and row["account"] == plan.account and
            row["depth"] == 0 and row["participant_state"] == "ACTIVE" and row["ordinal"] > after,
            "RETIREMENT_OBSERVATION_SCOPE")
    attempt = db.execute("SELECT state,request FROM inference_attempts WHERE operation=?",
                         (operation,)).fetchone()
    require(attempt is not None and attempt["state"] in {"DISPATCHING", "SETTLED"},
            "RETIREMENT_OBSERVATION_SCOPE")
    request = strict_json(attempt["request"])
    require(request["runtime_job_id"] == plan.job_id and request["profile_digest"] == plan.profile_digest()
            and request["request_digest"] == row["request_digest"] and
            row["raw_ref"] == "cas:sha256:" + row["request_digest"], "RETIREMENT_OBSERVATION_SCOPE")
    if plan.ingress_policy is not None:
        from .native_ingress import require_ingress_request
        require_ingress_request(db, plan, operation, row["request_digest"])
    raw, _ = private_bytes(db, cas, row["raw_ref"], 1024 * 1024)
    body = strict_json(raw)
    meta = context_metadata(body)
    require(meta["thread_id"] == row["thread"] == meta["session_id"] and meta["agent_name"] == "/root",
            "RETIREMENT_OBSERVATION_SCOPE")
    return row, attempt["state"], body


def _terminal_status(db, cas, plan, participant, fence, proof):
    issued, state, _ = _request(db, cas, plan, proof.issuance_operation, fence)
    require(state == "SETTLED", "RETIREMENT_ISSUANCE_UNSETTLED")
    receipts = list(db.execute("SELECT body FROM ledger WHERE json_extract(body,'$.operation_id')=? "
        "AND json_extract(body,'$.posting')='settle'", (proof.issuance_operation,)))
    require(len(receipts) == 1, "RETIREMENT_TOOL_ISSUANCE")
    receipt = BudgetLedger.model_validate_json(receipts[0][0])
    raw, media = private_bytes(db, cas, receipt.raw_usage_ref, MAX_RESPONSE_BYTES)
    captured = _CompletedResponse(plan.model, media)
    captured.feed(raw)
    captured.finish()
    calls = [x for x in captured.response["output"] if x.get("call_id") == proof.call_id]
    require(len(calls) == 1, "RETIREMENT_TOOL_ISSUANCE")
    call = calls[0]
    require(call.get("type") == "function_call" and call.get("namespace") == "collaboration"
            and call.get("name") == "list_agents" and isinstance(call.get("arguments"), str),
            "RETIREMENT_TOOL_ISSUANCE")
    args = strict_json(call["arguments"])
    require(args in ({}, {"path_prefix": participant["name"]}), "RETIREMENT_TOOL_ISSUANCE")
    observed, _, body = _request(db, cas, plan, proof.observation_operation, issued["ordinal"])
    # Existing jobs may predate the index. Fill only missing captures from this
    # authenticated root; never infer freshness from a compacted current context.
    for previous in db.execute("SELECT a.rowid ordinal,a.* FROM native_request_admissions a LEFT JOIN "
            "native_tool_call_indexed_requests i ON a.operation=i.operation WHERE a.job=? AND a.thread=? "
            "AND a.rowid<=? AND i.operation IS NULL ORDER BY a.rowid",
            (plan.job_id, issued["thread"], observed["ordinal"])).fetchall():
        index_native_tool_calls(db, cas, previous)
    first = db.execute("SELECT first_ordinal FROM native_tool_call_ids WHERE job=? AND thread=? AND call_id=?",
                       (plan.job_id, issued["thread"], proof.call_id)).fetchone()
    require(first is not None and issued["ordinal"] < first[0] <= observed["ordinal"],
            "RETIREMENT_TOOL_CALL_REUSED")
    matches = [(i, x) for i, x in enumerate(body["input"]) if x.get("call_id") == proof.call_id]
    require(len(matches) == 2 and matches[0][1].get("type") == "function_call" and
            matches[1][1].get("type") == "function_call_output", "RETIREMENT_TOOL_RESULT")
    observed_call, output = matches[0][1], matches[1][1]
    require(all(observed_call.get(k) == call.get(k) for k in (
        "type", "namespace", "name", "arguments", "call_id")) and isinstance(output.get("output"), str),
        "RETIREMENT_TOOL_RESULT")
    value = strict_json(output["output"])
    require(isinstance(value, dict) and set(value) == {"agents"} and isinstance(value["agents"], list)
            and 1 <= len(value["agents"]) <= 1024, "RETIREMENT_TOOL_RESULT")
    agents = {}
    for item in value["agents"]:
        require(isinstance(item, dict) and set(item) == {"agent_name", "agent_status"} and
                isinstance(item["agent_name"], str) and item["agent_name"] not in agents,
                "RETIREMENT_TOOL_RESULT")
        agents[item["agent_name"]] = item["agent_status"]
    status = agents.get(participant["name"])
    require(status == "interrupted" or isinstance(status, dict) and set(status) == {"completed"} and
            isinstance(status["completed"], str), "NATIVE_HELPER_NOT_TERMINAL")
    return "interrupted" if status == "interrupted" else "completed"


def close_helper_envelope(budgets, db, plan, participant, proof_ref):
    source = db.execute("SELECT body FROM ledger WHERE json_extract(body,'$.operation_id')=? "
        "AND json_extract(body,'$.posting')='reserve'", (participant["envelope"],)).fetchone()
    require(source is not None, "OPERATION_LINEAGE")
    reserve = BudgetLedger.model_validate_json(source[0])
    closure = "envelope-close:" + digest({"job": plan.job_id, "thread": participant["thread"]})
    receipt = BudgetLedger.model_validate(reserve.model_dump() | {
        "posting": "settle", "ledger_id": closure, "source_event_id": closure,
        "metering": "reported", "raw_usage_ref": proof_ref,
        "reason": "fenced native helper ingress; usage belongs to descendants",
        "usage": dict.fromkeys(reserve.usage.model_dump(), 0)})
    budgets.post_in_transaction(db, plan.account, receipt, close_envelope=True)


def retire_participant(admission, job, thread, proof_ref):
    """Close a revoked leaf only; retained participants/envelopes prevent reuse."""
    with admission.db.transaction() as db:
        fence = db.execute("SELECT * FROM native_participant_retirements WHERE job=? AND thread=?",
                           (job, thread)).fetchone()
        row = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?", (job, thread)).fetchone()
        require(row is not None and row["depth"] > 0, "NATIVE_HELPER_REQUIRED")
        require(fence is not None, "RETIREMENT_FENCE_REQUIRED")
        if fence["proof_ref"] is not None:
            require(row["state"] == "CLOSED" and proof_ref == fence["proof_ref"], "IDEMPOTENCY_CONFLICT")
            return dict(row)
        require(row["state"] == "REVOKED", "RETIREMENT_FENCE_REQUIRED")
        plan = admission._plan(db, job)
        raw, _ = private_bytes(db, admission.cas, proof_ref, 16384)
        proof = NativeParticipantRetirement.model_validate(strict_json(raw))
        simulation = db.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()[0]
        require(simulation == 1 or plan.ingress_policy is not None, "RETIREMENT_INGRESS_REQUIRED")
        require(proof.is_example is bool(simulation) and proof.job_id == job and proof.thread_id == thread
                and proof.profile_digest == plan.profile_digest(), "RETIREMENT_EVIDENCE_SCOPE")
        terminal = _terminal_status(db, admission.cas, plan, row, fence["fence_ordinal"], proof)
        require(db.execute("SELECT 1 FROM native_participants WHERE job=? AND parent=? AND state IS NOT 'CLOSED'",
                           (job, thread)).fetchone() is None, "DESCENDANT_UNSETTLED")
        require(db.execute("SELECT 1 FROM native_request_admissions a JOIN inference_attempts i "
            "ON i.operation=a.operation WHERE a.job=? AND a.thread=? AND i.state!='SETTLED'",
            (job, thread)).fetchone() is None, "METERING_UNKNOWN")
        close_helper_envelope(admission.budgets, db, plan, row, proof_ref)
        db.execute("UPDATE native_participants SET state='CLOSED' WHERE job=? AND thread=?", (job, thread))
        db.execute("UPDATE native_participant_retirements SET proof_ref=? WHERE job=? AND thread=?",
                   (proof_ref, job, thread))
        admission.db.event(db, "native.participant_retired", {"policy": POLICY, "job": job,
            "thread": thread, "envelope": row["envelope"], "native_status": terminal,
            "proof_ref": proof_ref, "fence_ordinal": fence["fence_ordinal"]})
        return dict(row) | {"state": "CLOSED"}
