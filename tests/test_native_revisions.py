"""Synthetic root-write publication and retention; no native skill activation."""

import json

import pytest
from pydantic import ValidationError

from mcbench.checkpoints import Checkpoints
from mcbench.native import NativeExec
from mcbench.native_export import NativeExports
from mcbench.native_revisions import MANIFEST, POLICY, NativeSkillPublications
from mcbench.storage import CAS, Database, Fault, canonical, extended_path
from test_native_admission import broker_meta
from test_native_checkpoint import admitted as _admitted, stage
from test_native_export import OPERATOR, stopped as _stopped

stopped = _stopped


@pytest.fixture
def admitted(database, cas, tmp_path, example, configs, request):
    admitted = _admitted.__wrapped__(database, cas, tmp_path, example, configs, request)
    b = admitted[2]
    original = b.call
    case = getattr(request.node, "callspec", None)
    change = case.params.get("request_change") if case else None
    def call(name, arguments, meta, **kwargs):
        result = original(name, arguments, meta, **kwargs)
        if name == "artifact_write" and arguments["path"] == "notes/root.md":
            evidence = original("artifact_write", {"path": "notes/development.md", "expected_ref": None,
                "text": "Synthetic fixture development observation; no real game or activation result."}, broker_meta())
            candidates = []
            for skill, paths in [("learned-crafting", ["SKILL.md", "references/steps.md", "scripts/check.py"]),
                                 ("learned-movement", ["SKILL.md"])]:
                files = {}
                for path in paths:
                    value = original("artifact_write", {"path": f"skills/{skill}/{path}",
                        "text": ("x" * 262144 if change == "aggregate_quota" and path == "SKILL.md"
                            else "Synthetic learned content: " + path), "expected_ref": None}, broker_meta())
                    files[path] = value["ref"]
                candidates.append({"revision_id": skill + ":1", "name": skill, "kind": "procedure",
                    "parent_revision_id": None, "files": files, "inputs": {"notes/root.md": result["ref"]},
                    "development_evidence": {"notes/development.md": evidence["ref"]}})
            body = {"schema": "strata/NativeSkillPublicationRequest/1", "policy": POLICY, "candidates": candidates}
            if change == "initial_name":
                candidates[0]["name"] = "better-skill-creator"
            elif change == "initial_local_skill":
                candidates[0]["name"] = "minecraft-keybindings"
            elif change == "baseline_input":
                candidates[0]["inputs"] = {"docs/allowed.md": original("artifact_read", {
                    "path": "docs/allowed.md"}, broker_meta())["ref"]}
            elif change == "duplicate_id":
                candidates[1]["revision_id"] = candidates[0]["revision_id"]
            elif change == "evidence_missing":
                candidates[0]["development_evidence"] = {}
            elif change == "parent":
                candidates[0]["parent_revision_id"] = "unbound-prior-revision"
            elif change == "unknown_field":
                candidates[0]["activate"] = True
            original("artifact_write", {"path": MANIFEST, "text": canonical(body).decode(),
                                       "expected_ref": None}, broker_meta())
        return result
    b.call = call
    return admitted


def publication(stopped):
    runtime, _, _ = stopped
    service = NativeSkillPublications(runtime)
    export = runtime.export_broker_state("job")
    ref = service.publish(export)
    return service, export, ref


def test_atomic_complete_publication_root_provenance_and_restart(stopped):
    runtime, _, _ = stopped
    before = runtime.budgets.status("a1")
    service, export, ref = publication(stopped)
    body = service.load(ref)
    assert not body["activates_skills"] and not body["native_activation_verified"] and not body["executes_scripts"]
    assert len(body["records"]) == 2
    source = NativeExports(runtime).load(export)
    captured = runtime.cas.json(OPERATOR, "operator", source.source_ref)
    calls = {c["cursor"]: c for c in captured["broker_calls"]}
    for record in body["records"]:
        assert record["status"] == "candidate" and record["activated_at"] is None
        assert record["origin"] == "campaign" and record["agent_id"] == "a1"
        for call in record["generating_call_ids"]:
            event = calls[int(call.removeprefix("broker:"))]
            assert event["state"] == "RETURNED"
            assert json.loads(event["body"])["thread"] == "root"
        bundle = runtime.cas.json(OPERATOR, "operator", record["content"])
        assert "SKILL.md" in bundle["files"] and bundle["inputs"] and bundle["development_evidence"]
        assert not bundle["executes_scripts"]
        for value in bundle["files"].values():
            assert runtime.cas.read(OPERATOR, "operator", value)
    assert service.publish(export) == ref
    assert runtime.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='native.skills_published'").fetchone()[0] == 1
    db = Database(runtime.db.path)
    try:
        restarted = NativeSkillPublications(NativeExec(db, CAS(db, runtime.cas.root), simulation=True))
        assert restarted.load(ref) == body
        assert restarted.publish(export) == ref
    finally:
        db.close()
    assert runtime.budgets.status("a1") == before


@pytest.mark.parametrize("admitted", ["full", "frozen-persistence", "frozen-skills", "no-self-play"], indirect=True)
@pytest.mark.parametrize("boundary", ["episode", "recovery"])
def test_checkpoint_preserves_or_discards_candidates_by_registered_arm(stopped, boundary):
    runtime, _, _ = stopped
    _, _, published = publication(stopped)
    service, state, ref, _ = stage(stopped, boundary=boundary)
    part = runtime.cas.json(OPERATOR, "operator", state.skills)
    retained = boundary == "recovery" or runtime.db.checkpoint_fixture["arm"] in {"full", "no-self-play"}
    assert (part.get("publication_ref") == published) is retained
    assert not part["activates_skills"]
    assert ("skills/learned-crafting/SKILL.md" in part["files"]) is retained
    assert service.load(ref)[0] == state


@pytest.mark.parametrize("case,code", [("journal_absent", "NATIVE_REVISION_PROVENANCE"),
    ("write_rejected", "NATIVE_REVISION_PROVENANCE"), ("helper_copy", "FORBIDDEN"),
    ("omitted_file", "NATIVE_REVISION_FILES"), ("foreign_provenance", "NATIVE_REVISION_PROVENANCE"),
    ("evaluation", "PROBE_IMPORT_FORBIDDEN")])
def test_unproven_or_incomplete_bundles_never_publish(stopped, case, code):
    runtime, _, _ = stopped
    db = runtime.db.connection
    if case == "journal_absent":
        db.execute("DELETE FROM broker_artifact_writes")
    elif case == "write_rejected":
        db.execute("UPDATE broker_call_lifecycle SET state='REJECTED' WHERE event IN "
            "(SELECT event FROM broker_artifact_writes WHERE path=?)", (MANIFEST,))
    elif case == "evaluation":
        db.execute("UPDATE accounts SET category='evaluation'")
        # Ledger/source account binding rejects an unrecorded account mutation;
        # construct a matching synthetic history to exercise the origin rule.
        for row in db.execute("SELECT rowid,body FROM ledger").fetchall():
            from mcbench.storage import digest
            record = json.loads(row["body"])
            record["campaign_account"] = "evaluation"
            db.execute("UPDATE ledger SET body=?,digest=? WHERE rowid=?",
                (canonical(record).decode(), digest({"account": "a1", "body": record}), row["rowid"]))
        for row in db.execute("SELECT operation,reservation,fingerprint,request FROM inference_attempts").fetchall():
            reserve = json.loads(row["reservation"])
            reserve["campaign_account"] = "evaluation"
            db.execute("UPDATE inference_attempts SET reservation=?,fingerprint=? WHERE operation=?", (
                canonical(reserve).decode(), digest({"account": "a1", "attempt": json.loads(row["request"]),
                    "reserve": reserve}), row["operation"]))
    else:
        namespace = db.execute("SELECT namespace FROM broker_files WHERE path=?", (MANIFEST,)).fetchone()[0]
        if case == "omitted_file":
            db.execute("DELETE FROM broker_files WHERE path='skills/learned-crafting/scripts/check.py'")
        elif case == "foreign_provenance":
            db.execute("DELETE FROM broker_files WHERE path='notes/root.md'")
        else:
            helper_ref = db.execute("SELECT ref FROM broker_files WHERE path='results/private.md'").fetchone()[0]
            db.execute("INSERT INTO broker_files VALUES(?,?,?,0)",
                (namespace, "skills/learned-crafting/private.md", helper_ref))
    service = NativeSkillPublications(runtime)
    with pytest.raises(Fault, match=code):
        service.publish(runtime.export_broker_state("job"))
    assert db.execute("SELECT count(*) FROM native_skill_publications").fetchone()[0] == 0


def test_crash_before_publication_does_not_commit_partial_set(stopped, monkeypatch):
    runtime, _, _ = stopped
    service = NativeSkillPublications(runtime)
    export = runtime.export_broker_state("job")
    original = runtime.cas.put
    count = 0
    def crash(*args, **kwargs):
        nonlocal count
        count += 1
        result = original(*args, **kwargs)
        if count == 3:
            raise RuntimeError("synthetic publication crash")
        return result
    monkeypatch.setattr(runtime.cas, "put", crash)
    with pytest.raises(RuntimeError, match="synthetic publication crash"):
        service.publish(export)
    assert runtime.db.connection.execute("SELECT count(*) FROM native_skill_publications").fetchone()[0] == 0
    monkeypatch.setattr(runtime.cas, "put", original)
    assert len(service.load(service.publish(export))["records"]) == 2


def test_sealed_checkpoint_cannot_gain_later_publication(stopped):
    runtime, _, _ = stopped
    service, state, ref, _ = stage(stopped)
    publications = NativeSkillPublications(runtime)
    with pytest.raises(Fault, match="NATIVE_REVISION_TOO_LATE"):
        publications.publish(state.source_export)
    assert service.load(ref)[0] == state


def test_changed_write_journal_invalidates_published_source(stopped):
    runtime, _, _ = stopped
    service, _, ref = publication(stopped)
    runtime.db.connection.execute("UPDATE broker_artifact_writes SET expected_ref=ref WHERE path=?", (MANIFEST,))
    with pytest.raises(Fault, match="NATIVE_EXPORT_SOURCE_CHANGED"):
        service.load(ref)


@pytest.mark.parametrize("request_change,code", [("aggregate_quota", "ARTIFACT_QUOTA"),
    ("initial_name", "INITIAL_IMMUTABLE"), ("duplicate_id", "REVISION_CONFLICT"),
    ("initial_local_skill", "INITIAL_IMMUTABLE"), ("evidence_missing", "NATIVE_REVISION_FILES"),
    ("parent", None), ("unknown_field", None)])
def test_recorded_root_requests_still_require_complete_safe_bundles(stopped, request_change, code):
    runtime, _, _ = stopped
    service = NativeSkillPublications(runtime)
    export = runtime.export_broker_state("job")
    with pytest.raises(Fault if code else ValidationError, match=code):
        service.publish(export)
    assert runtime.db.connection.execute("SELECT count(*) FROM native_skill_publications").fetchone()[0] == 0


@pytest.mark.parametrize("request_change", ["baseline_input"])
def test_existing_private_baseline_keeps_its_cas_metadata(stopped, request_change):
    runtime, _, _ = stopped
    doc = runtime.db.checkpoint_fixture["initial"]["docs/allowed.md"]
    before = dict(runtime.db.connection.execute("SELECT * FROM objects WHERE namespace='operator' AND ref=?", (doc,)).fetchone())
    assert before["media_type"] == "application/json"
    service, _, ref = publication(stopped)
    bundle = runtime.cas.json(OPERATOR, "operator", service.load(ref)["records"][0]["content"])
    assert bundle["inputs"] == {"docs/allowed.md": doc}
    assert dict(runtime.db.connection.execute("SELECT * FROM objects WHERE namespace='operator' AND ref=?", (doc,)).fetchone()) == before


def test_complete_materialization_keeps_revision_metadata_private(stopped, tmp_path):
    runtime, _, _ = stopped
    service, _, publication_ref = publication(stopped)
    _, state, _, manifest = stage(stopped)
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    config = runtime.db.checkpoint_fixture["config"]
    checkpoints.commit(config, manifest, "operator")
    target = extended_path(tmp_path / ("deep-" + "n" * 75) / ("skill-" + "n" * 74) / "complete")
    restored = checkpoints.materialize_set("cp1", config, 2, target)
    member = restored["members"]["a1"]
    assert not member["skills_activated"] and not restored["dispatch_authorized"]
    private = target / member["directory"] / "private"
    assert json.loads((private / "skill_candidates.json").read_bytes()) == service.load(publication_ref)
    records = service.load(publication_ref)["records"]
    assert len(list((private / "skill-bundles").iterdir())) == 2
    for record in records:
        assert (private / "skill-bundles" / (record["content"][11:] + ".json")).read_bytes() == runtime.cas.read(
            OPERATOR, "operator", record["content"])
    workspace = private.parent / "workspace"
    assert not (workspace / "skill_candidates.json").exists()
    assert (workspace / "skills/learned-crafting/scripts/check.py").is_file()
    assert "results/private.md" not in runtime.cas.json(OPERATOR, "operator", state.workspace)["files"]
