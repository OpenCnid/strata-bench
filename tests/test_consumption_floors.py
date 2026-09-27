# ruff: noqa: F811
"""Confirmed partial consumption must preserve both charges and unresolved holds."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mcbench.budgets import Budgets
from mcbench.native_repair_resume import NativeRepairResume
from mcbench.native_resume import NativeResumeDecision
from mcbench.storage import Fault, canonical, digest
from mcbench.worker_publication import WorkerPublicationClient, WorkerRepairAccounting
from test_budget_clocks import accounts, receipt
from test_native_control_plan import native_env, repair_env  # noqa: F401
from test_worker_publication import measured
from test_worker_resume import state


def floor(budgets, amount, source="measured", dimension="input_tokens", operation="root"):
    with budgets.database.transaction() as db:
        return budgets.retain_consumption_floor(db, "a1", operation, source, dimension, amount,
                                                {"is_example": True, "fixture": "synthetic cumulative minimum"})


def test_observed_floor_keeps_full_reserve_and_deduplicates_notifications(database, example):
    budgets = Budgets(database)
    accounts(budgets)
    budgets.post("a1", receipt(example, "root", "reserve", tokens=100))
    before = budgets.status("a1")
    assert floor(budgets, 70)
    assert not floor(budgets, 70)
    assert budgets.status("a1") == before
    assert database.connection.execute("SELECT actual FROM operations WHERE id='root'").fetchone()[0] is None
    assert budgets.consumption_floors(database.connection) == {"root": {"input_tokens": 70}}
    # Distinct observations are cumulative lower bounds, not extra calls.
    floor(budgets, 80, source="later")
    assert budgets.status("a1") == before
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        floor(budgets, 71)
    with pytest.raises(Fault, match="CONFIRMED_CONSUMPTION_REFUND"):
        budgets.post("a1", receipt(example, "root", "settle", tokens=79))
    budgets.post("a1", receipt(example, "root", "settle", tokens=80))
    assert budgets.status("a1")["committed_and_reserved"]["input_tokens"] == 80
    adjustment = receipt(example, "root", "adjust", tokens=-1).model_copy(update={"reason": "reconcile:synthetic"})
    with pytest.raises(Fault, match="CONFIRMED_CONSUMPTION_REFUND"):
        budgets.post("a1", adjustment)
    assert not floor(budgets, 70)  # Same observation never posts a new charge.


def test_overrun_propagates_once_through_nested_envelope_without_closing_it(database, example):
    budgets = Budgets(database)
    accounts(budgets, tokens=300)
    budgets.post("a1", receipt(example, "job", "reserve", tokens=200), envelope=True)
    budgets.post("a1", receipt(example, "root", "reserve", tokens=100, parent="job"))
    floor(budgets, 350)
    status = budgets.status("operator")
    assert status["committed_and_reserved"]["input_tokens"] == 350
    assert not status["dispatch_allowed"]
    assert database.connection.execute("SELECT actual FROM operations WHERE id='job'").fetchone()[0] is None
    with pytest.raises(Fault, match="CONSUMPTION_FLOOR_ENVELOPE"):
        floor(budgets, 350, operation="job")
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        budgets.post("a1", receipt(example, "other", "reserve", tokens=1))
    budgets.post("a1", receipt(example, "root", "settle", tokens=350, parent="job"))
    assert budgets.status("operator")["committed_and_reserved"]["input_tokens"] == 350


def test_unknown_hold_is_not_cleared_by_a_confirmed_partial_dimension(database, example):
    budgets = Budgets(database)
    accounts(budgets)
    budgets.post("a1", receipt(example, "root", "reserve", tokens=100))
    budgets.hold_uncertain("a1", "root", "synthetic missing source")
    floor(budgets, 120)
    assert budgets.status("a1")["uncertain"]
    assert budgets.status("a1")["committed_and_reserved"]["input_tokens"] == 120
    budgets.post("a1", receipt(example, "root", "settle", tokens=120, spend=None))
    assert budgets.status("a1")["uncertain"]
    assert budgets.status("a1")["committed_and_reserved"]["spend_microusd"] is None


@pytest.mark.parametrize("amount", [True, -1, 1.5, 2**53])
def test_invalid_floor_does_not_change_reservation(database, example, amount):
    budgets = Budgets(database)
    accounts(budgets)
    budgets.post("a1", receipt(example, "root", "reserve"))
    before = budgets.status("a1")
    with pytest.raises(Fault, match="CONSUMPTION_FLOOR_INVALID"):
        floor(budgets, amount)
    assert budgets.status("a1") == before


@pytest.mark.parametrize("overrun", [False, True])
def test_actual_repair_ledger_retains_native_measurement_before_cas_failure(native_env, example, monkeypatch, overrun):
    """Real repair/budget stores; synthetic native evidence and transport replies."""
    e, worker, native, target, _, _, _, _ = native_env
    admitted = e.repairs.admit_native("tx", "owner", e.epoch, worker, native, target)
    from mcbench.native_settings_effects import NativeRepairAdmission
    admission = NativeRepairAdmission.model_validate(admitted["admission"])
    joined = NativeRepairResume(e.repairs)
    context = joined.flow._context
    def committed_context(*args, **kwargs):
        repair, control, admitted = context(*args, **kwargs)
        return repair, control | {"phase": "committed"}, admitted
    monkeypatch.setattr(joined.flow, "_context", committed_context)
    decision = NativeResumeDecision.model_validate(state(example)["decision"] | {
        "worker_plan": admission.worker_plan.model_dump(), "lease_until_unix_ms": 149000})
    resume = SimpleNamespace(binding_digest="a" * 64)
    monkeypatch.setattr(joined, "_evidence", lambda *args: (
        SimpleNamespace(verification_ref=decision.verification_ref), "native-1", 1, None))
    resume_ref = e.put({"fixture": "resume"})
    inference_ref = e.put(joined.inference.freeze("tx", "owner", e.epoch))
    with e.database.transaction() as db:
        db.execute("INSERT INTO repair_resume_inference VALUES (?,?)", ("tx", inference_ref))
        e.database.event(db, "repair.resume_intent", {"transaction_id": "tx",
            "decision": decision.model_dump(), "inference_ref": inference_ref})
        db.execute("INSERT INTO repair_worker_resumes VALUES (?,?,?,?,'CONFIRMED',?)",
            ("tx", resume.binding_digest, canonical(decision.model_dump()).decode(), "native-1", resume_ref))
    raw = measured(example)
    raw.update(worker_plan=admission.worker_plan.model_dump(), resume_digest=digest(decision.model_dump()))
    if overrun:
        raw["charged_primitive_events"] = 25
        raw["closing"]["primitive_events"] = raw["opening"]["primitive_events"] + 25
        raw["closing"]["sources"] = {next(iter(raw["closing"]["sources"])): raw["closing"]["primitive_events"]}
    publisher = Mock(spec=WorkerPublicationClient)
    publisher.binding_digest = "b" * 64
    publisher.measure.return_value = WorkerRepairAccounting.model_validate(raw)
    def unavailable(value):
        raise OSError("synthetic CAS unavailable")
    monkeypatch.setattr(joined.flow, "_put", unavailable)
    with pytest.raises(Fault if overrun else OSError, match="REPAIR_BUDGET_EXHAUSTED" if overrun else "synthetic CAS"):
        joined.measure_prepared("tx", "owner", e.epoch, worker, Mock(), resume, publisher, native)
    minimum = 25 if overrun else 5
    stored = e.database.connection.execute("SELECT * FROM budget_consumption_floors").fetchone()
    assert stored["minimum"] == minimum
    assert json.loads(stored["body"])["evidence"]["worker_receipt"] == raw
    assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == max(20, minimum)
    assert e.database.connection.execute("SELECT actual FROM operations WHERE id='repair-op'").fetchone()[0] is None
    assert e.database.connection.execute("SELECT count(*) FROM repair_worker_measurements").fetchone()[0] == 0
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    if overrun:
        with e.database.transaction() as db, pytest.raises(Fault, match="REPAIR_BUDGET_EXHAUSTED"):
            e.repairs._budget(db, e.repairs.status("tx")["request"])
