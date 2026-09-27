# ruff: noqa: F401, F811
"""Synthetic provider receipts through the real repair/dispatch/budget transactions."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches, verified_rejections
from mcbench.repair_inference import RepairInference
from mcbench.storage import CAS, Database, Fault
from test_reconfiguration import repair_env
from test_inference_dispatch import make_attempt


@pytest.fixture
def gateway(repair_env):
    e = repair_env
    return InferenceDispatches(e.database, e.cas, simulation=True)


def test_overlapping_root_helper_retry_calls_close_without_reposting(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    a, r, s = make_attempt("before", epoch=e.epoch)
    gateway.execute("a1", a, r, lambda: ("before-event", s()))
    a, r, s = make_attempt("pre", epoch=e.epoch)
    gateway._begin("a1", a, r)
    e.request()
    service = RepairInference(e.repairs)
    for op, kind in [("helper", "helper"), ("retry", "model")]:
        a1, r1, s1 = make_attempt(op, kind=kind, parent_operation_id="pre", epoch=e.epoch)
        gateway.execute("a1", a1, r1, lambda: (op + "-event", s1()))
    before = gateway.budgets.status("a1")
    audit = service.freeze("tx", "owner", e.epoch)
    assert audit["admission_closed"] and not audit["tracked_dispatches_settled"]
    assert {c["operation_id"] for c in audit["calls"]} == {"pre", "helper", "retry"}
    assert {c["attribution"] for c in audit["calls"]} == {"in_flight_at_repair_request", "admitted_during_repair"}
    assert service.freeze("tx", "owner", e.epoch) == audit
    assert gateway.budgets.status("a1") == before
    denied, reserve, _ = make_attempt("denied", epoch=e.epoch)
    with pytest.raises(Fault, match="REPAIR_INFERENCE_FROZEN"):
        gateway.execute("a1", denied, reserve, lambda: pytest.fail("frozen call forwarded"))
    rejection = verified_rejections(e.database.connection, "job1", True)["denied"]
    assert rejection.schema_ == "strata/InferencePreDispatchRejection/2"
    assert gateway.status("denied")["state"] == "REJECTED_BEFORE_DISPATCH"
    assert gateway.execute("a1", a, r, lambda: pytest.fail("old call replayed"))["state"] == "DISPATCHING"
    gateway.settle("pre", "pre-event", s())
    completed = service.audit("tx", "owner", e.epoch)
    assert completed["tracked_dispatches_settled"]
    assert sum(c["actual"]["model_calls"] for c in completed["calls"]) == 3
    assert not completed["costs_reposted"] and not completed["complete_repair_accounting"]
    assert not completed["campaign_permission_published"]
    assert completed["closing_cursor"] == audit["closing_cursor"]
    assert gateway.budgets.status("a1")["committed_and_reserved"]["model_calls"] == 4
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None


def test_uncertain_call_retains_its_original_hold_until_real_receipt(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    a, r, s = make_attempt("unknown", epoch=e.epoch)
    gateway._begin("a1", a, r)
    gateway.mark_uncertain("unknown", "transport_or_receipt_uncertain")
    service = RepairInference(e.repairs)
    before = gateway.budgets.status("a1")
    audit = service.freeze("tx", "owner", e.epoch)
    assert not audit["tracked_dispatches_settled"] and audit["calls"][0]["uncertain"]
    assert gateway.budgets.status("a1") == before
    gateway.settle("unknown", "late-authoritative", s(35))
    assert service.audit("tx", "owner", e.epoch)["tracked_dispatches_settled"]
    assert gateway.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 35


def test_freeze_is_avatar_scoped_and_zero_calls_is_not_complete_repair(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    audit = RepairInference(e.repairs).freeze("tx", "owner", e.epoch)
    assert audit["calls"] == [] and audit["tracked_dispatches_settled"]
    assert not audit["complete_repair_accounting"]
    gateway.budgets.create_account("a2", dict.fromkeys(DIMENSIONS, 100000), "c1", "a2", category="training")
    a, r, s = make_attempt("sibling", agent_id="a2", epoch=e.epoch)
    assert gateway.execute("a2", a, r, lambda: ("sibling-event", s()))["state"] == "SETTLED"
    assert RepairInference(e.repairs).audit("tx", "owner", e.epoch) == audit


@pytest.mark.parametrize("change", ["missing_member", "changed_fingerprint", "missing_event", "missing_attempt",
                                    "window_scope", "window_opening", "window_closing"])
def test_audit_reconciles_members_against_dispatch_and_settlement_history(gateway, make_attempt, repair_env, change):
    e = repair_env
    e.begin()
    e.request()
    a, r, s = make_attempt("one", epoch=e.epoch)
    gateway.execute("a1", a, r, lambda: ("one-event", s()))
    service = RepairInference(e.repairs)
    assert service.freeze("tx", "owner", e.epoch)["tracked_dispatches_settled"]
    with e.database.transaction() as db:
        if change == "missing_member":
            db.execute("DELETE FROM repair_inference_members")
        elif change == "changed_fingerprint":
            db.execute("UPDATE repair_inference_members SET fingerprint='changed'")
        elif change == "missing_event":
            db.execute("DELETE FROM outbox WHERE kind='inference.settled'")
        elif change == "missing_attempt":
            db.execute("DELETE FROM inference_attempts")
        elif change == "window_scope":
            db.execute("UPDATE repair_inference_windows SET agent='sibling'")
        elif change == "window_opening":
            db.execute("DELETE FROM outbox WHERE kind='repair.inference_opened'")
        else:
            db.execute("DELETE FROM outbox WHERE kind='repair.inference_frozen'")
    with pytest.raises(Fault, match="REPAIR_INFERENCE_CHANGED"):
        service.audit("tx", "owner", e.epoch)


def test_legacy_missing_window_is_refused_without_inventing_zero_usage(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    with e.database.transaction() as db:
        db.execute("DELETE FROM repair_inference_windows")
    a, r, _ = make_attempt("legacy", epoch=e.epoch)
    with pytest.raises(Fault, match="REPAIR_INFERENCE_UNTRACKED"):
        gateway.execute("a1", a, r, lambda: pytest.fail("untracked repair forwarded"))
    with pytest.raises(Fault, match="REPAIR_INFERENCE_UNTRACKED"):
        RepairInference(e.repairs).freeze("tx", "owner", e.epoch)
    assert "legacy" in verified_rejections(e.database.connection, "job1", True)


def test_failed_attribution_commit_never_forwards_or_charges(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    before = gateway.budgets.status("a1")
    e.database.connection.execute("CREATE TRIGGER fail_member BEFORE INSERT ON repair_inference_members "
        "BEGIN SELECT RAISE(ABORT,'synthetic member storage failure'); END")
    a, r, _ = make_attempt("failed", epoch=e.epoch)
    with pytest.raises(Exception, match="synthetic member storage"):
        gateway.execute("a1", a, r, lambda: pytest.fail("failed attribution forwarded"))
    assert gateway.budgets.status("a1") == before
    assert e.database.connection.execute("SELECT 1 FROM inference_attempts WHERE operation='failed'").fetchone() is None


def test_dispatch_racing_freeze_is_either_included_or_durably_denied(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    a, r, s = make_attempt("racing", epoch=e.epoch)
    entered, release = threading.Event(), threading.Event()
    def dispatch():
        db = Database(e.database.path)
        try:
            gate = InferenceDispatches(db, CAS(db, e.cas.root), simulation=True)
            original = gate._validate_bound
            def validate(*args):
                original(*args)
                entered.set()
                assert release.wait(3)
            gate._validate_bound = validate
            return gate._begin("a1", a, r)
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(dispatch)
        assert entered.wait(3)  # The other connection now owns the writer lock.
        timer = threading.Timer(.05, release.set)
        timer.start()
        try:
            audit = RepairInference(e.repairs).freeze("tx", "owner", e.epoch)
        finally:
            release.set()
            timer.join()
        assert future.result(timeout=3)
    assert [c["operation_id"] for c in audit["calls"]] == ["racing"]
    assert not audit["tracked_dispatches_settled"]
    next_attempt, next_reserve, _ = make_attempt("after-freeze", epoch=e.epoch)
    with pytest.raises(Fault, match="REPAIR_INFERENCE_FROZEN"):
        gateway._begin("a1", next_attempt, next_reserve)
    gateway.settle("racing", "racing-receipt", s())
    assert RepairInference(e.repairs).audit("tx", "owner", e.epoch)["tracked_dispatches_settled"]


def test_failed_freeze_commit_does_not_claim_closed_admission(gateway, make_attempt, repair_env):
    e = repair_env
    e.begin()
    e.request()
    e.database.connection.execute("CREATE TRIGGER fail_freeze BEFORE UPDATE ON repair_inference_windows "
        "BEGIN SELECT RAISE(ABORT,'synthetic freeze write failure'); END")
    service = RepairInference(e.repairs)
    with pytest.raises(Exception, match="synthetic freeze write failure"):
        service.freeze("tx", "owner", e.epoch)
    assert not service.audit("tx", "owner", e.epoch)["admission_closed"]
    assert e.database.connection.execute("SELECT count(*) FROM outbox WHERE kind='repair.inference_frozen'").fetchone()[0] == 0
    a, r, s = make_attempt("still-open", epoch=e.epoch)
    assert gateway.execute("a1", a, r, lambda: ("open-receipt", s()))["state"] == "SETTLED"
