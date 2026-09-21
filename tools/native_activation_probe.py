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
        self.reset = not self.body["skills"]
        self.discarded = {}
        if self.reset:
            from mcbench.native_export import OPERATOR
            state, _ = service.components.load(self.body["checkpoint_ref"])
            policy = runtime.cas.json(OPERATOR, "operator", state.retention_policy)
            require(policy["arm"] == "frozen-persistence" and state.boundary == "episode",
                    "ACTIVATION_FIXTURE_RESET")
            initial = runtime.cas.json(OPERATOR, "operator", policy["initial_artifacts"])["files"]
            require(self.body["workspace"] == initial, "ACTIVATION_FIXTURE_RESET")
            exported = service.publications.exports.load(state.source_export)
            inventory = runtime.cas.json(OPERATOR, "operator", exported.root_artifacts)
            self.discarded = {f["path"]: f["ref"] for f in inventory["files"]
                              if initial.get(f["path"]) != f["ref"]}
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
        if self.reset and agent == "/root":
            calls += [("artifact_read", {"path": p}) for p in sorted(self.discarded)
                      if not p.startswith("active/")]
        return calls

    def publish_code(self):
        if self.reset:
            return ""  # A fresh frozen episode begins with only its initial tree.
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
        returned = []
        for path in self.output.glob("dispatch-*-request.json"):
            body = json.loads(path.read_bytes())
            name = json.loads(body["client_metadata"]["x-codex-turn-metadata"])["agent_name"]
            outputs = [i for i in body.get("input", []) if i.get("type") in {"custom_tool_call_output", "function_call_output"}]
            items = list(values(outputs))
            returned.extend((name, v) for v in items)
            per_agent.setdefault(name, {}).update({v["path"]: v for v in items})
        wanted = {p: r for p, r in active_files(self.body).items() if "learned-crafting/" in p or p == "active/revisions.json"}
        checks = {}
        from native_plugin_probe import text_content
        initial = db.connection.execute("SELECT a.raw_ref FROM native_request_admissions a JOIN native_participants p "
            "ON p.job=a.job AND p.thread=a.thread WHERE a.job=? AND p.depth=0 ORDER BY a.rowid LIMIT 1", (plan.job_id,)).fetchone()
        if self.reset:
            starts = list(db.connection.execute("SELECT a.raw_ref FROM native_request_admissions a "
                "WHERE a.job=? AND a.rowid=(SELECT min(b.rowid) FROM native_request_admissions b "
                "WHERE b.job=a.job AND b.thread=a.thread)", (plan.job_id,)))
            # Compare actual first native contexts, before newly permitted writes.
            forbidden = [self.runtime.cas.read(OPERATOR, "operator", ref).decode().strip()
                         for path, ref in self.discarded.items() if path.endswith("SKILL.md")]
            checks["frozen_initial_contexts_no_learned_bodies"] = len(starts) == 2 and bool(forbidden) and all(
                all(value not in text_content(json.loads(self.runtime.cas.read(OPERATOR, "operator", row[0],
                    max_bytes=1024*1024))).replace("\r\n", "\n") for value in forbidden) for row in starts)
            checks["frozen_discarded_values_not_returned"] = bool(self.discarded) and not any(
                self.discarded.get(value["path"]) == value["ref"] for _, value in returned)
            checks["frozen_initial_tree_restored"] = self.reset and "notes/seed.md" in per_agent.get("/root", {})
        else:
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
        checks["frozen_no_candidate_written" if self.reset else "native_candidate_written"] = (not any(
            r["path"] == "skills/publish.json" for r in rows) if self.reset else any(r["path"] == "skills/publish.json" and
            self.runtime.cas.read(OPERATOR, json.loads(r["body"])["namespace"], r["ref"]).find(
                getattr(self, "next_revision", "MISSING_REVISION").encode()) >= 0 for r in rows))
        checks["original_allowance_preserved"] = db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0] == self.limits
        settled = db.connection.execute("SELECT count(*) FROM inference_attempts "
            "WHERE json_extract(request,'$.runtime_job_id')=? AND state='SETTLED'", (plan.job_id,)).fetchone()[0]
        checks["prior_usage_preserved_once"] = self.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == (
            self.before["committed_and_reserved"]["spend_microusd"] + 14 * settled)
        return {"source": self.source, "skill_set_ref": self.ref, "before": self.before, "frozen_reset": self.reset,
                "settled_native_calls": settled,
                "returned_paths": {k: sorted(v) for k, v in per_agent.items()}, "checks": checks,
                "production_qualified": False}
