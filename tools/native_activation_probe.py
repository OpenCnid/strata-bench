"""Actual CLI activation fixture on a copied synthetic complete checkpoint.

Reuses the existing native accounting/identity harness. Never imports a live
authorization, changes a copied allowance, or claims synthetic worlds are real.
"""

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

from mcbench.native_skill_activation import INSTRUCTIONS, NativeSkillSets, active_files
from mcbench.storage import require


class ActivationProbe:
    def __init__(self, source, output):
        require(set(source) == {"directory", "seal_sha256", "skill_set_ref"}, "ACTIVATION_FIXTURE_SOURCE")
        self.output = output
        self.ref = source["skill_set_ref"]
        origin = Path(source["directory"])
        raw = (origin / "seal.json").read_bytes()
        require(hashlib.sha256(raw).hexdigest() == source["seal_sha256"], "ACTIVATION_SOURCE_CHANGED")
        manifest = json.loads(raw)
        selected = {f["path"]: f for f in manifest["files"] if f["path"] == "synthetic.sqlite" or f["path"].startswith("objects/")}
        require("synthetic.sqlite" in selected, "ACTIVATION_FIXTURE_SOURCE")
        for name, entry in selected.items():
            path = origin / name
            require(not path.is_symlink() and path.is_file(), "ACTIVATION_SOURCE_CHANGED")
            with path.open("rb") as stream:
                require(hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"], "ACTIVATION_SOURCE_CHANGED")
        require(not (output / "synthetic.sqlite").exists() and not (output / "objects").exists(), "TARGET_EXISTS")
        with sqlite3.connect((origin / "synthetic.sqlite").as_uri() + "?mode=ro", uri=True) as src:
            require(src.execute("SELECT simulation FROM native_profile").fetchone()[0] == 1, "SIMULATION_STORE")
            with sqlite3.connect(output / "synthetic.sqlite") as dst:
                src.backup(dst)
        shutil.copytree(origin / "objects", output / "objects")
        self.source = source
        self.body = None

    def prepare(self, runtime, plan):
        service = NativeSkillSets(runtime)
        self.body = service.load(self.ref)
        require(self.body["is_example"] is True and self.body["campaign_id"] == "c1" and
                self.body["agent_id"] == "a1" and self.body["source_epoch"] >= 1,
                "ACTIVATION_FIXTURE_SCOPE")
        self.before = runtime.budgets.status("a1")
        require(not self.before["uncertain"], "METERING_UNKNOWN")
        self.limits = runtime.db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0]
        view = self.output / "activated-workspace"
        service.materialize(self.ref, view)
        self.runtime = runtime
        return plan.model_copy(update={"campaign_id": self.body["campaign_id"], "agent_id": self.body["agent_id"],
            "epoch": self.body["source_epoch"] + 1, "workspace": str(view), "skill_activation_ref": self.ref,
            "helper_skill_activation_ref": self.ref, "purpose": "campaign"})

    @property
    def instructions(self):
        return INSTRUCTIONS

    def calls(self, agent):
        calls = [("artifact_read", {"path": p}) for p in (
            "active/learned-crafting/SKILL.md", "active/learned-crafting/references/steps.md",
            "active/learned-crafting/scripts/check.py", "active/revisions.json")]
        calls += [("artifact_write", {"path": "active/learned-crafting/SKILL.md", "expected_ref": None, "text": "forbidden"}),
                  ("artifact_write", {"path": "active/revisions.json", "expected_ref": None, "text": "forbidden"})]
        if agent == "/root":
            calls += [("artifact_read", {"path": "initial/SKILL.md"}),
                      ("artifact_write", {"path": "initial/SKILL.md", "expected_ref": None, "text": "forbidden"})]
        else:
            calls += [("artifact_read", {"path": p}) for p in (
                "notes/root.md", "notes/development.md", "skills/publish.json", "handoff/next.md")]
        return calls

    def publish_code(self):
        previous = self.body["skills"]["learned-crafting"]["revision"]["revision_id"]
        require(previous.startswith("learned-crafting:") and previous.rsplit(":", 1)[1].isdigit(),
                "ACTIVATION_FIXTURE_REVISION")
        self.next_revision = "learned-crafting:" + str(int(previous.rsplit(":", 1)[1]) + 1)
        return r'''
async function artifact(name,args) {
  const t=ALL_TOOLS.find(t=>t.name.endsWith("__"+name));
  if (!t) throw new Error("MISSING_BROKER_TOOL");
  const r=await tools[t.name](args);
  if(r.isError) throw new Error("BROKER_PUBLICATION_FAILED:"+JSON.stringify(r));
  return JSON.parse(r.content[0].text);
}
const index=JSON.parse((await artifact("artifact_read",{path:"active/revisions.json"})).text);
const existing=await artifact("artifact_list",{});
const files=Object.fromEntries(existing.files.map(x=>[x.path,x.ref]));
const prefix="skills/learned-crafting/";
const path=prefix+"SKILL.md";
const current=await artifact("artifact_read",{path});
const updated=await artifact("artifact_write",{path,expected_ref:current.ref,text:current.text+"\nNative synthetic replacement.\n"});
files[path]=updated.ref;
const candidate={revision_id:REVISION_ID,name:"learned-crafting",kind:"procedure",
 parent_revision_id:index.skills["learned-crafting"],
 files:Object.fromEntries(Object.entries(files).filter(([p])=>p.startsWith(prefix)).map(([p,r])=>[p.slice(prefix.length),r])),
 inputs:{"notes/root.md":files["notes/root.md"]},
 development_evidence:{"notes/development.md":files["notes/development.md"]}};
const publication={schema:"strata/NativeSkillPublicationRequest/2",policy:"native-root-written-skill-bundles/2",candidates:[candidate]};
text({native_publication:await artifact("artifact_write",{path:"skills/publish.json",expected_ref:files["skills/publish.json"],text:JSON.stringify(publication)})});
'''.replace("REVISION_ID", json.dumps(self.next_revision))

    def report(self, provider, db, plan):
        from mcbench.native_export import OPERATOR
        # Decode actual returned broker content, never echoed call inputs.
        def values(value):
            if isinstance(value, dict):
                if set(value) >= {"path", "ref", "text"}:
                    yield value
                for child in value.values():
                    yield from values(child)
            elif isinstance(value, list):
                for child in value:
                    yield from values(child)
            elif isinstance(value, str):
                for line in [value, *value.splitlines()]:
                    try:
                        parsed = json.loads(line)
                    except (TypeError, ValueError):
                        continue
                    if parsed != value:
                        yield from values(parsed)
        per_agent = {}
        for path in self.output.glob("dispatch-*-request.json"):
            body = json.loads(path.read_bytes())
            name = json.loads(body["client_metadata"]["x-codex-turn-metadata"])["agent_name"]
            outputs = [i for i in body.get("input", []) if i.get("type") in {"custom_tool_call_output", "function_call_output"}]
            per_agent.setdefault(name, {}).update({v["path"]: v for v in values(outputs)})
        wanted = {p: r for p, r in active_files(self.body).items() if "learned-crafting/" in p or p == "active/revisions.json"}
        checks = {}
        from native_plugin_probe import text_content
        initial = db.connection.execute("SELECT a.raw_ref FROM native_request_admissions a JOIN native_participants p "
            "ON p.job=a.job AND p.thread=a.thread WHERE a.job=? AND p.depth=0 ORDER BY a.rowid LIMIT 1", (plan.job_id,)).fetchone()
        expected = self.runtime.cas.read(OPERATOR, "operator", self.body["skills"]["learned-crafting"]["files"]["SKILL.md"]).decode()
        checks["native_explicit_body_injection"] = bool(initial) and expected.strip() in text_content(json.loads(
            self.runtime.cas.read(OPERATOR, "operator", initial[0], max_bytes=1024*1024))).replace("\r\n", "\n")
        for name in ("/root", "/root/identity_child"):
            reads = per_agent.get(name, {})
            checks[name + "_unchanged_active_reads"] = all(p in reads and reads[p]["ref"] == ref and
                reads[p]["text"].encode() == self.runtime.cas.read(OPERATOR, "operator", ref) for p, ref in wanted.items())
        child = per_agent.get("/root/identity_child", {})
        checks["helper_no_root_history_returned"] = not any(p.startswith(("notes/", "skills/", "handoff/")) for p in child)
        rows = list(db.connection.execute("SELECT g.body,f.path,f.ref,f.immutable FROM broker_grants g "
            "JOIN broker_files f ON json_extract(g.body,'$.namespace')=f.namespace WHERE g.runtime=?", (plan.job_id,)))
        checks["active_bytes_still_immutable"] = all(r["immutable"] == 1 and
            active_files(self.body).get(r["path"]) == r["ref"] for r in rows if r["path"].startswith("active/"))
        checks["native_candidate_written"] = any(r["path"] == "skills/publish.json" and
            self.runtime.cas.read(OPERATOR, json.loads(r["body"])["namespace"], r["ref"]).find(
                getattr(self, "next_revision", "MISSING_REVISION").encode()) >= 0 for r in rows)
        checks["original_allowance_preserved"] = db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0] == self.limits
        settled = db.connection.execute("SELECT count(*) FROM inference_attempts "
            "WHERE json_extract(request,'$.runtime_job_id')=? AND state='SETTLED'", (plan.job_id,)).fetchone()[0]
        checks["prior_usage_preserved_once"] = self.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == (
            self.before["committed_and_reserved"]["spend_microusd"] + 14 * settled)
        return {"source": self.source, "skill_set_ref": self.ref, "before": self.before,
                "settled_native_calls": settled,
                "returned_paths": {k: sorted(v) for k, v in per_agent.items()}, "checks": checks,
                "production_qualified": False}
