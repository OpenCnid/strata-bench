"""Selected native frozen-skills write boundary; scripted provider/world only."""

import json

from mcbench.native_cell_lifecycle import _status
from mcbench.native_checkpoint import parse_retention_policy
from mcbench.native_export import OPERATOR
from mcbench.native_note_policy import CLASSIFIER, classify_note
from mcbench.native_skill_activation import NativeSkillSets
from mcbench.storage import require
from native_active_script_probe import artifact_returns
from native_matched_retention_probe import ACTORS, MatchedActivationProbe, fresh_context

POLICY = "native-frozen-note-fixture/1"
PROMPT = "Inspect permitted artifacts, record an observation and ask one clean-context helper to inspect the permitted artifacts."
PROSE = "If hungry, inspect the available food. The visible chest was empty."
DENIED = (
    ("fence.md", "```js\ntext(1)\n```", "FROZEN_NOTE_CODE"),
    ("indent.md", "    text(1)", "FROZEN_NOTE_CODE"),
    ("metadata.md", "---\nname: procedure\n---", "FROZEN_NOTE_CODE"),
    ("tool.md", "Use functions.exec to run it.", "FROZEN_NOTE_CODE"),
    ("computed.md", 'globalThis["te"+"xt"](1)', "FROZEN_NOTE_CODE"),
    ("assignment.md", 'store["key"]=1', "FROZEN_NOTE_CODE"),
    ("payload.md", '{"tool":"game","arguments":{}}', "FROZEN_NOTE_CODE"),
    ("unicode.md", "ＡＬＬ＿ＴＯＯＬＳ", "FROZEN_NOTE_CODE"),
    ("control.md", "foo\u200bbar", "FROZEN_NOTE_CODE"),
    ("script.js", "Plain text.", "FROZEN_NOTE_FORMAT"),
)


def native_call_results(frames):
    result = []
    for frame in frames:
        for line in frame.get("text", "").splitlines():
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and set(value) == {"name", "result"}:
                result.append(value)
    return result


class FrozenNoteProbe(MatchedActivationProbe):
    def prepare(self, runtime, plan, *, helper_free=False):
        require(helper_free is False, "FROZEN_NOTE_HELPER_REQUIRED")
        service = NativeSkillSets(runtime)
        self.body = service.load(self.ref)
        state, _ = service.components.load(self.body["checkpoint_ref"])
        policy = parse_retention_policy(runtime.cas.json(OPERATOR, "operator", state.retention_policy))
        require(policy.schema_ == "strata/NativeRetentionPolicy/2" and policy.arm == "frozen-skills" and
                policy.note_classifier == CLASSIFIER and not self.body["skills"] and self.body["is_example"] is True
                and self.body["model_identity"] == "gpt-6-luna" and self.body["campaign_id"] == "c1"
                and self.body["agent_id"] == "a1", "FROZEN_NOTE_SOURCE")
        self.initial_body = runtime.cas.read(OPERATOR, "operator", self.body["workspace"]["initial/SKILL.md"]).decode()
        self.before = runtime.budgets.status("a1")
        require(not self.before["uncertain"], "METERING_UNKNOWN")
        self.limits = runtime.db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0]
        self.runtime, self.reset, self.discarded = runtime, False, {}
        self.calls_issued, self.outputs, self.initial = {}, {}, {}
        view = self.output / "activated-workspace"
        service.materialize(self.ref, view)
        return plan.model_copy(update={"campaign_id": "c1", "agent_id": "a1", "epoch": self.body["source_epoch"]+1,
            "workspace": str(view), "skill_activation_ref": self.ref, "helper_skill_activation_ref": self.ref,
            "purpose": "campaign"})

    @property
    def instructions(self):
        return ("Initial procedures are immutable. Keep notes, handoff and helper results as prose in .md or .txt files. "
                "New skill packages and executable or tool-triggering note blocks are unavailable. "
                "Use only supplied artifacts and scoped tools. Helpers cannot read executor history or act in the game.")

    def cases(self, actor):
        require(actor in ACTORS, "FROZEN_NOTE_ACTOR")
        prefix = "notes" if actor == ACTORS[0] else "results"
        cases = []
        for path, text, fault in DENIED:
            cases.append((prefix + "/denied-" + path, text, fault))
        if actor == ACTORS[0]:
            cases.extend((p, "New procedure.", "FROZEN_SKILL_WRITE") for p in (
                "skills/new/SKILL.md", "skills/new/scripts/check.js", "skills/publish.json"))
        cases.extend((p, "forbidden", "BROKER_WRITE_FORBIDDEN") for p in ("initial/SKILL.md", "active/revisions.json"))
        return cases

    def calls(self, actor):
        initial = "initial/SKILL.md" if actor == ACTORS[0] else "supplied/plan.md"
        calls = [("artifact_read", {"path": p}) for p in (initial, "active/revisions.json", "notes/root.md")]
        calls.extend(("artifact_write", {"path": p, "text": text, "expected_ref": None}) for p, text, _ in self.cases(actor))
        prefix = "notes" if actor == ACTORS[0] else "results"
        calls.append(("artifact_write", {"path": prefix + "/retained.md", "text": PROSE, "expected_ref": None}))
        if actor == ACTORS[0]:
            calls.append(("artifact_write", {"path": "handoff/retained.md", "text": "Continue from the visible chest observation.", "expected_ref": None}))
        return calls

    def publish_code(self):
        return ""  # A new package/publication would violate this arm.

    def report(self, provider, db, plan, *, helper_free=False):
        require(helper_free is False, "FROZEN_NOTE_HELPER_REQUIRED")
        checks = {
            "both_native_calls_completed": set(self.outputs) == set(ACTORS) and all(_status(v)[0] == "completed" for v in self.outputs.values()),
            "both_fresh_contexts": set(self.initial) == set(ACTORS) and all(fresh_context(a, b) for a, b in self.initial.items()),
            "original_allowance_preserved": db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0] == self.limits,
        }
        for actor in ACTORS:
            results = native_call_results(self.outputs.get(actor, []))
            own = self.calls(actor)
            checks[actor + "_all_expected_results"] = len(results) >= len(own) and [x["name"] for x in results[:len(own)]] == [x[0] for x in own]
            denials = results[3:3+len(self.cases(actor))]
            checks[actor + "_exact_packaging_denials"] = len(denials) == len(self.cases(actor)) and all(
                r["result"].get("isError") is True and r["result"].get("content") == [{"type": "text", "text": fault}]
                for r, (_, _, fault) in zip(denials, self.cases(actor), strict=True))
            reads = list(artifact_returns(self.outputs.get(actor, [])))
            initial = "initial/SKILL.md" if actor == ACTORS[0] else "supplied/plan.md"
            checks[actor + "_initial_procedure_returned"] = any(v["path"] == initial and v["text"] == self.initial_body for v in reads)
            checks[actor + "_no_active_procedure"] = any(v["path"] == "active/revisions.json" and json.loads(v["text"])["skills"] == {} for v in reads)
            grant = db.connection.execute("SELECT * FROM broker_grants WHERE runtime=? AND parent IS " + ("NULL" if actor == ACTORS[0] else "NOT NULL"), (plan.job_id,)).fetchone()
            files = {r[0]: r[1] for r in db.connection.execute("SELECT path,ref FROM broker_files WHERE namespace=?", (grant["namespace"],))}
            prefix = "notes" if actor == ACTORS[0] else "results"
            checks[actor + "_permitted_prose_preserved"] = prefix + "/retained.md" in files and self.runtime.cas.read(OPERATOR, grant["namespace"], files[prefix + "/retained.md"]).decode() == PROSE
            checks[actor + "_denied_files_absent"] = not any(p in files for p, _, _ in self.cases(actor) if not p.startswith(("initial/", "active/")))
            if actor == ACTORS[1]:
                checks["helper_no_root_history_returned"] = not any(v["path"].startswith(("notes/", "handoff/", "skills/")) for v in reads)
        audits = [json.loads(r[0]) for r in db.connection.execute("SELECT body FROM outbox WHERE kind='broker.note_classified' AND json_extract(body,'$.runtime')=?", (plan.job_id,))]
        writes = list(db.connection.execute("SELECT w.*,g.body FROM broker_artifact_writes w JOIN broker_grants g ON w.runtime=g.runtime AND w.thread=g.thread WHERE w.runtime=?", (plan.job_id,)))
        checks["all_five_positive_writes_audited"] = len(audits) == len(writes) == 5 and all(any(
            a["source_event"] == w["event"] and a["ref"] == w["ref"] and a["path"] == w["path"] and a["thread"] == w["thread"]
            and a["classifier"] == CLASSIFIER and a["implicit_procedure_ambiguity"] is True for a in audits) for w in writes)
        sample = []
        for w in writes:
            text = self.runtime.cas.read(OPERATOR, json.loads(w["body"])["namespace"], w["ref"]).decode()
            sample.append({"path": w["path"], "ref": w["ref"], "text": text, **classify_note(w["path"], text)})
        settled = db.connection.execute("SELECT count(*) FROM inference_attempts WHERE json_extract(request,'$.runtime_job_id')=? AND state='SETTLED'", (plan.job_id,)).fetchone()[0]
        checks["prior_usage_preserved_once"] = self.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == self.before["committed_and_reserved"]["spend_microusd"] + 14*settled
        return {"policy": POLICY, "classifier": CLASSIFIER, "before": self.before, "calls": self.calls_issued,
            "outputs": self.outputs, "sample": sample, "settled_native_calls": settled, "checks": checks,
            "sample_scope": "all writes from scripted native fixture; not model-produced prose", "production_qualified": False}
