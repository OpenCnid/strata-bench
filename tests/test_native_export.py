"""Stopped native component export; synthetic receipts are not game checkpoints."""

import json

import pytest

from mcbench.native import NativeExec
from mcbench.native_export import NativeExports, NativeStateV2
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Database, Fault, Principal, canonical
from test_native_admission import admitted as _admitted, broker_meta
from test_native_retirement import scenario, settle

admitted = _admitted
OPERATOR = Principal("operator", "operator")


@pytest.fixture
def stopped(admitted):
    admission, gate, broker, plan, _, _, put = admitted
    def files():
        broker.project("root", "initial/SKILL.md", "Immutable initial body.")
        broker.project("root", "docs/allowed.md", "Admitted document.")
        broker.project("child", "supplied/plan.md", "Only helper task.")
        for path, text in [("notes/root.md", "Own prior note."), ("skills/draft.md", "Unactivated draft."),
                           ("handoff/next.md", "Fresh goal continuation.")]:
            broker.call("artifact_write", {"path": path, "text": text, "expected_ref": None}, broker_meta())
        broker.call("artifact_write", {"path": "results/private.md", "text": "Unshared helper result.",
            "expected_ref": None}, broker_meta("child", "root"))
    _, ref, _, observed = scenario(admitted, before_revoke=files)
    settle(admitted, observed)
    admission.retire("job", "child", ref)
    gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED',returncode=0")
    seal = put({"schema": "strata/InferenceIngressSeal/1", "is_example": True, "job_id": "job",
        "profile_digest": plan.profile_digest(), "process_tree_dead": True, "ingress_closed": True,
        "handlers_fenced": True, "participant_threads": ["child", "root"],
        "attempt_ids": ["child-call", "root-call", "status-issue", "status-observed"]})
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    runtime.close_dispatch_budget("job", seal)
    return runtime, plan, seal


def test_complete_own_inventory_private_helpers_and_cost_continuity_survive_restart(stopped):
    runtime, _, _ = stopped
    before = runtime.budgets.status("a1")
    limits = runtime.db.connection.execute("SELECT limits FROM accounts WHERE id='a1'").fetchone()[0]
    ref = runtime.export_broker_state("job")
    assert runtime.export_broker_state("job") == ref
    assert runtime.budgets.status("a1") == before
    export = NativeExports(runtime).load(ref)
    body = runtime.cas.json(OPERATOR, "operator", export.root_artifacts)
    assert body["namespace"] != "operator" and body["activates_skills"] is False
    files = {x["path"]: x for x in body["files"]}
    assert set(files) == {"initial/SKILL.md", "docs/allowed.md", "notes/root.md", "skills/draft.md", "handoff/next.md"}
    assert files["skills/draft.md"]["category"] == "skill_draft" and not files["skills/draft.md"]["immutable"]
    assert files["initial/SKILL.md"]["immutable"]
    helper = runtime.cas.json(OPERATOR, "operator", export.helper_artifacts["child"])
    assert {x["path"] for x in helper["files"]} == {"results/private.md", "supplied/plan.md"}
    principal = Principal(body["namespace"], "executor")
    for private_ref in (ref, export.root_artifacts, export.helper_artifacts["child"], export.accounting_ref):
        with pytest.raises(Fault, match="FORBIDDEN"):
            runtime.cas.read(principal, "operator", private_ref)
    with pytest.raises(Fault, match="FORBIDDEN"):
        runtime.cas.read(principal, helper["namespace"], helper["files"][0]["ref"])
    accounting = runtime.cas.json(OPERATOR, "operator", export.accounting_ref)
    assert accounting["accounts"][0]["committed_and_reserved"]["spend_microusd"] == 56
    assert accounting["accounts"][0]["identity"]["limits"] == limits
    assert accounting["cost_rollback"] is False and accounting["grants_new_allowance"] is False
    assert accounting["usage_classes"] == ["synthetic_fixture"]
    assert export.session is None and export.runtime_cache is None and not export.restore_authorized
    db = Database(runtime.db.path)
    try:
        restarted = NativeExec(db, CAS(db, runtime.cas.root), simulation=True)
        assert restarted.export_broker_state("job") == ref
        assert NativeExports(restarted).load(ref) == export
    finally:
        db.close()
    assert runtime.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='native.export_committed'").fetchone()[0] == 1


@pytest.mark.parametrize("case,code", [
    ("running", "RUNTIME_NOT_QUIESCENT"), ("owned", "RUNTIME_NOT_QUIESCENT"),
    ("unknown_usage", "METERING_UNKNOWN"), ("helper_active", "NATIVE_EXPORT_PARTICIPANTS"),
    ("missing_receipt", "NATIVE_EXPORT_LEDGER"), ("missing_grant", "NATIVE_EXPORT_PARTICIPANTS"),
    ("untracked_work", "BROKER_DRAIN_UNTRACKED"), ("pending_work", "BROKER_DRAIN_PENDING"),
    ("game_unknown", "NATIVE_EXPORT_GAME_UNKNOWN"), ("missing_blob", "MISSING_EVIDENCE")])
def test_unfinished_or_incomplete_source_never_commits_export(stopped, case, code):
    runtime, _, _ = stopped
    db = runtime.db.connection
    if case == "running":
        db.execute("UPDATE native_jobs SET state='RUNNING'")
    elif case == "owned":
        runtime.live["job"] = {"owned": True}
    elif case == "unknown_usage":
        db.execute("UPDATE operations SET uncertain=1 WHERE id='child-call'")
    elif case == "helper_active":
        db.execute("UPDATE native_participants SET state='ACTIVE' WHERE thread='child'")
    elif case == "missing_receipt":
        db.execute("DELETE FROM ledger WHERE json_extract(body,'$.operation_id')='child-call' AND json_extract(body,'$.posting')='settle'")
    elif case == "missing_grant":
        db.execute("DELETE FROM broker_grants WHERE thread='child'")
    elif case == "untracked_work":
        with runtime.db.transaction() as transaction:
            runtime.db.event(transaction, "broker.call", {"runtime": "job", "thread": "child"})
    elif case == "pending_work":
        db.execute("UPDATE broker_call_lifecycle SET state='STARTED'")
    elif case == "game_unknown":
        db.execute("INSERT INTO broker_game_calls VALUES('job','root','lost','digest','DISPATCHING',NULL)")
    else:
        ref = db.execute("SELECT ref FROM broker_files WHERE path='notes/root.md'").fetchone()[0]
        runtime.cas._path(ref).unlink()
    with pytest.raises(Fault, match=code):
        runtime.export_broker_state("job")
    assert db.execute("SELECT count(*) FROM native_exports").fetchone()[0] == 0


@pytest.mark.parametrize("path,immutable,code", [
    ("notes/Root.md", 0, "AMBIGUOUS_PATHS"), ("notes/root.md/nested", 0, "AMBIGUOUS_PATHS"),
    ("notes/auth.json", 0, "SECRET_IN_SNAPSHOT"), ("notes/private", 1, "NATIVE_EXPORT_ARTIFACT_POLICY"),
    ("results/alien.md", 0, "NATIVE_EXPORT_ARTIFACT_POLICY"), ("notes/../private", 0, "UNSAFE_PATH")])
def test_unportable_or_wrong_policy_inventory_is_not_exported(stopped, path, immutable, code):
    runtime, _, _ = stopped
    db = runtime.db.connection
    row = db.execute("SELECT namespace,ref FROM broker_files WHERE path='notes/root.md'").fetchone()
    db.execute("INSERT INTO broker_files VALUES(?,?,?,?)", (row["namespace"], path, row["ref"], immutable))
    with pytest.raises(Fault, match=code):
        runtime.export_broker_state("job")


def test_source_mutation_between_capture_and_commit_is_not_a_valid_export(stopped, monkeypatch):
    runtime, _, _ = stopped
    put = runtime.cas.put
    changed = False
    def racing_put(*args, **kwargs):
        nonlocal changed
        ref = put(*args, **kwargs)
        if not changed:
            changed = True
            runtime.db.connection.execute("DELETE FROM broker_files WHERE path='notes/root.md'")
        return ref
    monkeypatch.setattr(runtime.cas, "put", racing_put)
    before = runtime.budgets.status("a1")
    with pytest.raises(Fault, match="NATIVE_EXPORT_SOURCE_CHANGED"):
        runtime.export_broker_state("job")
    assert runtime.db.connection.execute("SELECT count(*) FROM native_exports").fetchone()[0] == 0
    assert runtime.budgets.status("a1") == before


def test_later_source_change_invalidates_old_export_without_replacing_it(stopped):
    runtime, _, _ = stopped
    ref = runtime.export_broker_state("job")
    runtime.db.connection.execute("DELETE FROM broker_files WHERE path='skills/draft.md'")
    with pytest.raises(Fault, match="NATIVE_EXPORT_SOURCE_CHANGED"):
        NativeExports(runtime).load(ref)
    with pytest.raises(Fault, match="NATIVE_EXPORT_SOURCE_CHANGED"):
        runtime.export_broker_state("job")
    assert runtime.db.connection.execute("SELECT ref FROM native_exports").fetchone()[0] == ref


def test_legacy_blobs_or_new_component_do_not_authorize_broker_resume(stopped):
    runtime, plan, _ = stopped
    with pytest.raises(Fault, match="NATIVE_EXPORT_BROKER_INVENTORY_REQUIRED"):
        runtime.export_state("job", workspace_ref="unused", skills_ref="unused", handoff_ref=None,
                             artifact_namespace="campaign:c1:agent:a1")
    ref = runtime.export_broker_state("job")
    with pytest.raises(Fault, match="NATIVE_COMPLETE_RESTORE_REQUIRED"):
        runtime.resume(ref, plan, None)
    legacy = runtime.cas.put(OPERATOR, "operator", "operator", canonical({"schema": "strata/NativeState/1"}))
    with pytest.raises(Fault, match="NATIVE_STATE_LEGACY"):
        runtime.resume(legacy, plan, None)


def test_arbitrary_valid_state_blob_requires_committed_export_row(stopped):
    runtime, _, _ = stopped
    ref = runtime.export_broker_state("job")
    value = runtime.cas.json(OPERATOR, "operator", ref)
    value["source_epoch"] = 2
    NativeStateV2.model_validate(value)
    forged = runtime.cas.put(OPERATOR, "operator", "operator", canonical(value))
    with pytest.raises(Fault, match="NATIVE_EXPORT_UNCOMMITTED"):
        NativeExports(runtime).load(forged)


@pytest.mark.parametrize("case,code", [
    ("actual", "NATIVE_EXPORT_LEDGER"), ("reserved", "NATIVE_EXPORT_LEDGER"),
    ("parent", "OPERATION_LINEAGE"), ("envelope", "OPERATION_LINEAGE"),
    ("receipt", "NATIVE_EXPORT_LEDGER"), ("dispatch", "NATIVE_EXPORT_LEDGER")])
def test_changed_accounting_cannot_authorize_export(stopped, case, code):
    runtime, _, _ = stopped
    db = runtime.db.connection
    if case in {"actual", "reserved"}:
        value = json.loads(db.execute(f"SELECT {case} FROM operations WHERE id='child-call'").fetchone()[0])
        value["spend_microusd"] = 0
        db.execute(f"UPDATE operations SET {case}=? WHERE id='child-call'", (canonical(value).decode(),))
    elif case == "parent":
        db.execute("UPDATE operations SET parent=NULL WHERE id='child-call'")
    elif case == "envelope":
        db.execute("DELETE FROM budget_envelopes")
    elif case == "receipt":
        db.execute("UPDATE inference_attempts SET receipt_digest=? WHERE operation='child-call'", ("0" * 64,))
    else:
        db.execute("UPDATE inference_attempts SET fingerprint=? WHERE operation='child-call'", ("0" * 64,))
    with pytest.raises(Fault, match=code):
        runtime.export_broker_state("job")
    assert db.execute("SELECT count(*) FROM native_exports").fetchone()[0] == 0


@pytest.mark.parametrize("before_export", [True, False])
def test_unrelated_unknown_hold_is_neither_erased_nor_reset_from_export(stopped, before_export):
    runtime, _, _ = stopped
    db = runtime.db.connection
    reserve = BudgetLedger.model_validate_json(db.execute("SELECT body FROM ledger WHERE "
        "json_extract(body,'$.operation_id')='child-call' AND json_extract(body,'$.posting')='reserve'").fetchone()[0])
    reserve.operation_id = "other-request"
    reserve.source_event_id = "other-reserve"
    reserve.ledger_id = "other-reserve"
    reserve.parent_operation_id = None
    ref = None if before_export else runtime.export_broker_state("job")
    runtime.budgets.post("a1", reserve)
    db.execute("UPDATE operations SET uncertain=1 WHERE id='other-request'")
    status = runtime.budgets.status("a1")
    assert status["uncertain"] and not status["dispatch_allowed"]
    exported = runtime.export_broker_state("job")
    assert ref is None or ref == exported
    state = NativeExports(runtime).load(exported)
    accounting = runtime.cas.json(OPERATOR, "operator", state.accounting_ref)
    assert accounting["accounts"][0]["uncertain"] is before_export
    assert runtime.budgets.status("a1") == status


def test_unregistered_broker_grant_cannot_disappear_from_export(stopped):
    runtime, _, _ = stopped
    db = runtime.db.connection
    db.execute("INSERT INTO broker_grants SELECT runtime,'unregistered','unregistered',parent,body,"
               "fingerprint,remaining,revoked FROM broker_grants WHERE thread='root'")
    with pytest.raises(Fault, match="NATIVE_EXPORT_PARTICIPANTS"):
        runtime.export_broker_state("job")
