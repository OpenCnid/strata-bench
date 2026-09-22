"""Native CLI + existing real worker integration. The model provider is scripted.

No server/admin/credential path is sent to the native agent. This is a plumbing
test with authentic game actions, not evidence of model reasoning or G0 closure.
"""

import json

from mcbench.broker_stdio import WorkerTransport
from mcbench.storage import require


class GameProbe:
    def __init__(self, descriptor, lease_id, *, recovery=False):
        WorkerTransport(descriptor)
        self.descriptor = dict(descriptor)
        self.scope = {k: descriptor[k] for k in ("campaign_id", "agent_id", "epoch")}
        require(isinstance(lease_id, str) and 0 < len(lease_id) <= 128, "GAME_LEASE_REQUIRED")
        self.lease_id = lease_id
        self.request_id = "native-bounded-look" + (f"-epoch-{descriptor['epoch']}" if recovery else "")

    def code(self):
        # All state/action arguments below are derived inside the native tool
        # invocation from the public observation. The provider sees no raw world.
        code = "const scope=" + json.dumps(self.scope) + "; const lease=" + json.dumps(self.lease_id) + r''';
const tool=ALL_TOOLS.find(t=>t.name.endsWith("__game"));
if (!tool) throw new Error("GAME_TOOL_MISSING");
let seq=0;
async function game(method, action=null, target_request_id=null) {
  const request={schema:"strata/GameRequest/1",...scope,request_id:"native-game-"+(++seq),
    deadline_at:new Date(Date.now()+5000).toISOString(),method,action,target_request_id,after:null};
  const returned=await tools[tool.name]({request});
  if (returned.isError) throw new Error(returned.content[0].text);
  const response=JSON.parse(returned.content[0].text);
  if (response.status!=="ok") throw new Error(response.error?.code||"GAME_RPC_FAILED");
  text({game_step:method,response});
  return response.result;
}
const capabilities=await game("capabilities");
await new Promise(resolve=>setTimeout(resolve,550));
const before=await game("observe");
if (!before.state.connected || before.is_example) throw new Error("REAL_GAME_NOT_CONNECTED");
const p=before.state.position;
const yaw=before.state.yaw+Math.PI/4;
const batch={schema:"mcbench/ActionBatch/1",is_example:false,...scope,
  seq:(before.last_action_seq||0)+1,recorded_at:new Date().toISOString(),lease_id:lease,
  request_id:"native-bounded-look",observation_id:before.observation_id,
  expected_state_revision:before.state_revision,capability_digest:before.capability_digest,
  control_revision:before.control_revision,keymap_digest:null,mode:"structured",
  deadline_at:new Date(Date.now()+2000).toISOString(),duration_ms:2000,
  action:{kind:"look_at",target:{x:p.x-Math.sin(yaw)*3,y:p.y+1.62,z:p.z-Math.cos(yaw)*3}},events:[],release_at_end:true};
let receipt=await game("act",batch);
for(let i=0;i<6 && ["accepted","executing"].includes(receipt.status);i++) {
  await new Promise(resolve=>setTimeout(resolve,100));
  receipt=await game("action_status",null,batch.request_id);
}
if (receipt.status!=="completed" || !receipt.release_confirmed || receipt.requires_resync)
  throw new Error("GAME_ACTION_NOT_COMPLETED");
await new Promise(resolve=>setTimeout(resolve,550));
const after=await game("observe");
if (after.last_action_seq!==batch.seq || after.state_revision<=before.state_revision)
  throw new Error("GAME_ACTION_NOT_OBSERVED");
text({native_game_completed:true,request_id:batch.request_id,receipt,
  before_observation:before.observation_id,after_observation:after.observation_id});
'''
        return code.replace('"native-bounded-look"', json.dumps(self.request_id))

    def report(self, db, plan, provider):
        rows = [dict(r) for r in db.connection.execute(
            "SELECT thread,request,state,result FROM broker_game_calls WHERE runtime=? ORDER BY rowid",
            (plan.job_id,))]
        responses = [json.loads(r["result"]) for r in rows if r["result"] is not None]
        observations = [r["result"] for r in responses if r.get("status") == "ok"
                        and isinstance(r.get("result"), dict)
                        and r["result"].get("schema") == "mcbench/Observation/1"]
        receipts = [r["result"] for r in responses if r.get("status") == "ok"
                    and isinstance(r.get("result"), dict)
                    and r["result"].get("request_id") == self.request_id]
        closed = db.connection.execute("SELECT state,stop_result FROM native_worker_bindings WHERE job=?",
                                       (plan.job_id,)).fetchone()
        outputs = json.dumps(provider.outputs)
        def completed(value):
            if isinstance(value, dict):
                return value.get("native_game_completed") is True or any(completed(v) for v in value.values())
            if isinstance(value, list):
                return any(completed(v) for v in value)
            if isinstance(value, str):
                for line in [value, *value.splitlines()]:
                    try:
                        parsed = json.loads(line)
                    except ValueError:
                        continue
                    if parsed != value and completed(parsed):
                        return True
            return False
        checks = {
            "real_observation_returned": len(observations) >= 3 and all(
                o["is_example"] is False and o["state"]["connected"] for o in observations),
            "one_executor_used_worker": len({r["thread"] for r in rows}) == 1,
            "all_game_requests_settled": bool(rows) and all(r["state"] == "SETTLED" for r in rows),
            "bounded_action_completed": any(r.get("status") == "completed" and
                r.get("release_confirmed") is True and r.get("requires_resync") is False for r in receipts),
            "native_observed_action_completion": completed(provider.outputs),
            "native_exit_stopped_game_lane": closed is not None and closed["state"] == "STOPPED",
            "worker_credential_not_returned": self.descriptor["token"] not in outputs,
        }
        return {"game_evidence": "authentic_worker", "model_evidence": "synthetic_provider",
                "reasoning_qualified": False, "checks": checks, "game_calls": rows,
                "stop_result": json.loads(closed["stop_result"]) if closed and closed["stop_result"] else None}
