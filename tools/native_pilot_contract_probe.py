"""Scripted native consumer of the public game contract; no Minecraft or model."""

import json

from mcbench.native_piloting import GAME_CONTRACT_PATH, PURPOSE, game_contract
from mcbench.storage import Principal, require


def response(agent, step, operation):
    require(agent == "/root" and 0 <= step <= 2, "PILOT_CONTRACT_FIXTURE_SEQUENCE")
    if step == 2:
        return {"id": "message-" + operation, "type": "message", "role": "assistant",
            "status": "completed", "content": [{"type": "output_text",
            "text": "Synthetic public game contract check finished.", "annotations": []}]}
    if step == 0:
        code = '''const t=ALL_TOOLS.find(t=>t.name.endsWith("__artifact_read"));
if(!t) throw new Error("ARTIFACT_TOOL_MISSING");
const result=await tools[t.name]({path:"initial/game/contract.json"});
if(result.isError) throw new Error("PUBLIC_CONTRACT_UNAVAILABLE");
const artifact=JSON.parse(result.content[0].text);
const doc=JSON.parse(artifact.text);
if(doc.schema!=="strata/PublicGameInstructions/1") throw new Error("PUBLIC_CONTRACT_FORMAT");
store("public_game_contract",doc);
text("PUBLIC_GAME_CONTRACT_READ");'''
    else:
        code = '''const doc=load("public_game_contract");
if(!doc) throw new Error("PUBLIC_CONTRACT_NOT_READ");
const rpc=doc.arguments_schema.$defs.RpcRequest;
const t=ALL_TOOLS.find(t=>t.name.endsWith("__game"));
if(!t) throw new Error("GAME_TOOL_MISSING");
const invalid=await tools[t.name]({request:{op:"observe",SECRET_FIELD_CANARY:"SECRET_VALUE_CANARY"}});
if(!invalid.isError) throw new Error("BAD_REQUEST_ACCEPTED");
const errorText=invalid.content[0].text;
if(errorText.includes("SECRET_FIELD_CANARY")||errorText.includes("SECRET_VALUE_CANARY"))
  throw new Error("REJECTED_INPUT_ECHOED");
const error=JSON.parse(errorText);
if(error.code!=="BROKER_ARGUMENTS_INVALID" ||
   JSON.stringify(error.expected_arguments_schema)!==JSON.stringify(doc.arguments_schema))
  throw new Error("PUBLIC_ERROR_SCHEMA_CHANGED");
const method=rpc.properties.method.enum.find(x=>x==="observe");
if(!method || !rpc.required.includes("deadline_at")) throw new Error("RPC_SCHEMA_INCOMPLETE");
const request={schema:rpc.properties.schema.const,request_id:"game-root",
  campaign_id:"synthetic-campaign",agent_id:"a1",epoch:1,
  deadline_at:new Date(Date.now()+2000).toISOString(),method,
  action:null,target_request_id:null,after:null};
const tooFar=await tools[t.name]({request:{...request,request_id:"game-too-far",
  deadline_at:new Date(Date.now()+60000).toISOString()}});
const timingError=JSON.parse(tooFar.content[0].text);
if(!tooFar.isError||timingError.code!=="DEADLINE_EXCEEDED"||
   timingError.maximum_future_ms!==doc.timing.maximum_request_future_ms||
   !timingError.guidance.includes(doc.timing.deadline_expression))
  throw new Error("DEADLINE_GUIDANCE_MISSING");
text("GAME_DEADLINE_WINDOW_REJECTED");
request.deadline_at=new Date(Date.now()+doc.timing.pilot_maximum_action_ms).toISOString();
const result=await tools[t.name]({request});
const reply=JSON.parse(result.content[0].text);
if(result.isError||reply.status!=="ok"||reply.request_id!==request.request_id||
   reply.result.visible_control!=="STRATA_SCOPED_GAME_CONTROL") throw new Error("GAME_FORWARD_FAILED");
text("PUBLIC_GAME_CONTRACT_ROUNDTRIP_PASS");'''
    return {"id": "tool-" + operation, "type": "custom_tool_call", "call_id": "call-" + operation,
            "namespace": "functions", "name": "exec", "input": code}


def report(db, cas, plan, result, provider, worker_calls):
    files = list(db.connection.execute("SELECT namespace,ref,immutable FROM broker_files WHERE path=?",
                                      (GAME_CONTRACT_PATH,)))
    read_events = [json.loads(r[0]) for r in db.connection.execute(
        "SELECT body FROM outbox WHERE kind='broker.call' AND json_extract(body,'$.runtime')=?",
        (plan.job_id,))]
    original = result["checks"]
    keep = {"every_request_admitted", "participants_closed", "all_envelopes_closed",
        "aggregate_no_double_charge", "every_request_projection_checked",
        "ingress_all_requests_bound", "native_oauth_headers_all_requests",
        "oauth_secrets_absent_from_context_and_journal", "gateway_all_requests_settled_and_fenced"}
    checks = {key: original[key] for key in keep}
    visible = json.dumps(provider.outputs)
    checks.update(
        public_contract_read="PUBLIC_GAME_CONTRACT_READ" in visible and len(files) == 1 and
            files[0]["immutable"] == 1 and cas.read(Principal(files[0]["namespace"], "executor"),
                files[0]["namespace"], files[0]["ref"]).decode() == game_contract(),
        malformed_calls_rejected="PUBLIC_GAME_CONTRACT_ROUNDTRIP_PASS" in visible,
        deadline_window_rejected="GAME_DEADLINE_WINDOW_REJECTED" in visible and
            db.connection.execute("SELECT count(*) FROM broker_call_lifecycle l JOIN outbox o ON o.cursor=l.event "
                "WHERE json_extract(o.body,'$.runtime')=? AND l.state='REJECTED' AND l.fault='DEADLINE_EXCEEDED'",
                (plan.job_id,)).fetchone()[0] == 1,
        valid_observation_forwarded_once=len(worker_calls) == 1 and worker_calls[0]["method"] == "observe" and
            worker_calls[0]["request_id"] == "game-root" and
            [e["tool"] for e in read_events] == ["artifact_read", "game", "game"],
        native_completed=result["closure"].get("state") == "FINALIZED" and
            result["closure"].get("returncode") == 0 and result["closure"].get("reason") == "native_exit" and
            "closure_error" not in result["closure"],
        zero_helpers=plan.purpose == PURPOSE and plan.helper_limit == 0 and
            len(result["participants"]) == 1 and result["participants"][0]["depth"] == 0,
        three_settled_fixture_requests=not provider.errors and len(provider.requests) == 3)
    return checks
