"""Matched full/frozen native retention fixture; never a scientific comparison."""

import json

from mcbench.native_cell_lifecycle import _status
from mcbench.native_export import OPERATOR
from mcbench.native_skill_activation import active_files
from mcbench.storage import canonical, digest, require
from native_activation_probe import ActivationProbe
from native_active_script_probe import artifact_returns

PROMPT = "Record one scoped observation and a concise reusable procedure with your available artifacts. Ask one clean-context helper to inspect the permitted artifacts."
POLICY = "native-matched-retention-fixture/2"
HELPER_TASK = "Inspect the permitted artifacts with your available tools."
ACTORS = ("/root", "/root/identity_child")
READS = ("initial/SKILL.md", "notes/seed.md", "notes/root.md", "notes/development.md", "handoff/next.md",
         "skills/publish.json", "active/learned-crafting/SKILL.md", "active/learned-crafting/references/steps.md",
         "active/learned-crafting/scripts/check.py", "active/learned-crafting/scripts/check.js", "active/revisions.json")
STATE_CODE = '''text({initial_private_state:load("matched-retention-private")??null});
store("matched-retention-private","permitted actor state");
text({retained_private_state:load("matched-retention-private")});
'''
PUBLICATION_CODE = r'''
async function artifact(name,args) {
  const t=ALL_TOOLS.find(t=>t.name.endsWith("__"+name));
  if(!t) throw new Error("MISSING_BROKER_TOOL");
  const r=await tools[t.name](args);
  if(r.isError) throw new Error("BROKER_PUBLICATION_FAILED:"+JSON.stringify(r));
  return JSON.parse(r.content[0].text);
}
const index=JSON.parse((await artifact("artifact_read",{path:"active/revisions.json"})).text);
const listing=await artifact("artifact_list",{});
const files=Object.fromEntries(listing.files.map(x=>[x.path,x.ref]));
async function write(path,text) {
  const result=await artifact("artifact_write",{path,text,expected_ref:files[path]??null});
  files[path]=result.ref; return result;
}
const epoch=PUBLIC_EPOCH;
await write("notes/root.md","Recorded scoped observation at epoch "+epoch+".\n");
await write("notes/development.md","Synthetic scoped observation evidence at epoch "+epoch+".\n");
await write("handoff/next.md","Continue from the permitted observation at epoch "+epoch+".\n");
await write("skills/learned-crafting/SKILL.md","---\nname: learned-crafting\ndescription: Scoped observation procedure\n---\nUse scoped observations before proposing an action. Recorded epoch "+epoch+".\n");
await write("skills/learned-crafting/references/steps.md","Read the permitted observation. Recorded epoch "+epoch+".\n");
await write("skills/learned-crafting/scripts/check.py","# Recorded epoch "+epoch+"; no Python execution capability.\n");
await write("skills/learned-crafting/scripts/check.js","text({recorded_epoch:"+epoch+"});\n");
const prefix="skills/learned-crafting/";
const candidate={revision_id:"learned-crafting:episode-"+epoch,name:"learned-crafting",kind:"executable",
 parent_revision_id:index.skills["learned-crafting"]??null,
 files:Object.fromEntries(Object.entries(files).filter(([p])=>p.startsWith(prefix)).map(([p,r])=>[p.slice(prefix.length),r])),
 inputs:{"notes/root.md":files["notes/root.md"]},development_evidence:{"notes/development.md":files["notes/development.md"]}};
text({native_publication:await write("skills/publish.json",JSON.stringify({schema:"strata/NativeSkillPublicationRequest/2",policy:"native-root-written-skill-bundles/2",candidates:[candidate]}))});
'''


def fresh_context(actor, body):
    """Only the exact public launch task may accompany a fresh helper."""
    tasks = []
    for item in body["input"]:
        if item.get("role") == "assistant":
            return False
        if item.get("type") == "agent_message":
            tasks.append(item)
        elif item.get("type") not in {"message", "additional_tools"}:
            return False
    if actor == ACTORS[0]:
        return not tasks
    return actor == ACTORS[1] and len(tasks) == 1 and set(tasks[0]) == {
        "type", "id", "author", "recipient", "content"} and isinstance(tasks[0]["id"], str) and bool(tasks[0]["id"]) and (
        tasks[0]["author"], tasks[0]["recipient"], tasks[0]["content"]) == (ACTORS[0], ACTORS[1], [
            {"type": "input_text", "text": "Message Type: NEW_TASK\nTask name: /root/identity_child\nSender: /root\nPayload:\n"},
            {"type": "encrypted_content", "encrypted_content": HELPER_TASK}])


def call_code(calls):
    # Compute a bounded observation deadline at the actual call, after prior
    # artifact reads. Never widen the game boundary or retry an expired action.
    return 'const calls=' + json.dumps(calls) + '; for (const [name,args] of calls) {' + (
        ' const t=ALL_TOOLS.find(t=>t.name.endsWith("__"+name)); '
        ' if (!t) throw new Error("MCP_TOOL_MISSING:"+name); '
        ' if(name==="game") args.request.deadline_at=new Date(Date.now()+2000).toISOString(); '
        ' text({name,result:await tools[t.name](args)}); }')


class MatchedActivationProbe(ActivationProbe):
    def prepare(self, runtime, plan, *, helper_free=False):
        require(helper_free is False, "MATCHED_RETENTION_HELPERS_REQUIRED")
        plan = super().prepare(runtime, plan, helper_free=False)
        # Use the actual component reader, never a caller-supplied arm label.
        from mcbench.native_checkpoint import NativeCheckpointStates
        state, _ = NativeCheckpointStates(runtime).load(self.body["checkpoint_ref"])
        self.arm = runtime.cas.json(OPERATOR, "operator", state.retention_policy)["arm"]
        require(self.arm in {"full", "frozen-persistence"}, "MATCHED_RETENTION_ARM")
        self.calls_issued, self.outputs, self.initial = {}, {}, {}
        self.next_revision = "learned-crafting:episode-" + str(plan.epoch)
        return plan

    def calls(self, agent):
        require(agent in ACTORS, "MATCHED_RETENTION_ACTOR")
        return [("artifact_read", {"path": p}) for p in READS] + [
            ("artifact_write", {"path": p, "expected_ref": None, "text": "forbidden"})
            for p in ("initial/SKILL.md", "active/learned-crafting/SKILL.md", "active/revisions.json")]

    def publish_code(self):
        # Same program in both arms, branching only on public artifact content.
        return PUBLICATION_CODE.replace("PUBLIC_EPOCH", str(self.body["source_epoch"] + 1))

    def expect_call(self, actor, item):
        require(actor in ACTORS and actor not in self.calls_issued and item["type"] == "custom_tool_call",
                "MATCHED_RETENTION_REPLAY")
        self.calls_issued[actor] = item

    def observe(self, actor, body):
        require(actor in ACTORS and isinstance(body.get("input"), list), "MATCHED_RETENTION_ACTOR")
        self.initial.setdefault(actor, body)
        expected = self.calls_issued.get(actor)
        if expected is None:
            return
        key = expected["call_id"]
        for item in body["input"]:
            if item.get("type") != "custom_tool_call_output" or item.get("call_id") != key:
                continue
            echoed = [i for i in body["input"] if i.get("type") == "custom_tool_call" and i.get("call_id") == key]
            require(len(echoed) == 1 and all(echoed[0].get(k) == v for k, v in expected.items() if k != "id"),
                    "MATCHED_RETENTION_CALL_CHANGED")
            value = item.get("output")
            require(isinstance(value, list) and (actor not in self.outputs or
                canonical(value) == canonical(self.outputs[actor])), "MATCHED_RETENTION_RETURN_CHANGED")
            self.outputs[actor] = value

    def report(self, provider, db, plan, *, helper_free=False):
        require(helper_free is False, "MATCHED_RETENTION_HELPERS_REQUIRED")
        returned = {actor: list(artifact_returns(self.outputs.get(actor, []))) for actor in ACTORS}
        wanted = {p: r for p, r in active_files(self.body).items() if p in READS}
        def matches(values, path, ref):
            return {"path": path, "ref": ref, "text": self.runtime.cas.read(OPERATOR, "operator", ref).decode()} in values
        checks = {
            "both_native_code_calls_completed": set(self.outputs) == set(ACTORS) and
                all(_status(v)[0] == "completed" for v in self.outputs.values()),
            "both_fresh_contexts": set(self.initial) == set(ACTORS) and all(
                fresh_context(actor, body) for actor, body in self.initial.items()),
            "both_exact_active_reads": all(all(matches(returned[a], p, r) for p, r in wanted.items()) for a in ACTORS),
            "prior_root_notes_available_exactly_when_admitted": all(matches(returned["/root"], p, r)
                for p, r in self.body["workspace"].items() if p in READS and p.startswith(("notes/", "handoff/"))),
            "helper_no_root_history_returned": not any(v["path"].startswith(("notes/", "skills/", "handoff/")) for v in returned[ACTORS[1]]),
            "original_allowance_preserved": db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0] == self.limits,
        }
        for actor in ACTORS:
            text = '\n'.join(v.get("text", "") for v in self.outputs.get(actor, []))
            values = []
            for line in text.splitlines():
                try:
                    values.append(json.loads(line))
                except ValueError:
                    pass
            checks[actor + "_fresh_private_state"] = {"initial_private_state": None} in values and {"retained_private_state": "permitted actor state"} in values
        if self.reset:
            checks["discarded_refs_not_returned"] = bool(self.discarded) and not any(
                self.discarded.get(v["path"]) == v["ref"] for values in returned.values() for v in values)
            forbidden = [self.runtime.cas.read(OPERATOR, "operator", ref).decode().strip()
                         for p, ref in self.discarded.items() if p.endswith("SKILL.md")]
            from native_plugin_probe import text_content
            checks["discarded_skill_bodies_absent_from_initial_context"] = bool(forbidden) and all(
                all(value not in text_content(body).replace("\r\n", "\n") for value in forbidden) for body in self.initial.values())
        root = db.connection.execute("SELECT namespace FROM broker_grants WHERE runtime=? AND json_extract(body,'$.role')='executor'", (plan.job_id,)).fetchone()
        files = {r[0]: r[1] for r in db.connection.execute("SELECT path,ref FROM broker_files WHERE namespace=?", (root[0],))}
        checks["new_notes_handoff_and_skill_written"] = all(p in files for p in (
            "notes/root.md", "notes/development.md", "handoff/next.md", "skills/learned-crafting/scripts/check.js", "skills/publish.json")) and self.next_revision.encode() in self.runtime.cas.read(OPERATOR, root[0], files["skills/publish.json"])
        settled = db.connection.execute("SELECT count(*) FROM inference_attempts WHERE json_extract(request,'$.runtime_job_id')=? AND state='SETTLED'", (plan.job_id,)).fetchone()[0]
        checks["prior_usage_preserved_once"] = self.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == self.before["committed_and_reserved"]["spend_microusd"] + 14 * settled
        return {"policy": POLICY, "arm": self.arm, "frozen_reset": self.reset, "before": self.before,
                "settled_native_calls": settled, "schedule_digest": digest({"policy": POLICY,
                    "prompt": PROMPT, "helper_task": HELPER_TASK, "game_deadline_ms": 2000, "reads": READS,
                    "state": STATE_CODE, "publication": PUBLICATION_CODE}), "calls": self.calls_issued,
                "outputs": self.outputs, "checks": checks, "production_qualified": False}
