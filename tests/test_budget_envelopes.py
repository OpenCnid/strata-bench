"""Synthetic job/subjob budgets, including failures and immutable receipts."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from mcbench.budgets import DIMENSIONS, Budgets
from mcbench.records import BudgetLedger
from mcbench.storage import Database, Fault


@pytest.fixture
def envelopes(database, example):
    budgets = Budgets(database)
    limits = dict.fromkeys(DIMENSIONS, 10000) | {"spend_microusd": 100}
    budgets.create_account("root", limits, "*")
    budgets.create_account("a1", limits, "c1", "a1", "root", category="training")

    def record(op, spend, parent=None, posting="reserve", **updates):
        base = example("BudgetLedger")
        return BudgetLedger.model_validate(base | {"is_example": False,
            "operation_id": op, "parent_operation_id": parent, "posting": posting,
            "source_event_id": op + ":" + posting, "ledger_id": op + ":" + posting,
            "metering": "reported", "usage": dict.fromkeys(base["usage"], 0) |
                {"spend_microusd": spend}, **updates})
    return budgets, record


def total(budgets):
    return budgets.status("root")["committed_and_reserved"]["spend_microusd"]


def test_nested_envelope_consumption_close_and_no_double_count(envelopes):
    b, r = envelopes
    b.post("a1", r("job", 100), envelope=True)
    b.post("a1", r("call", 40, "job"))
    b.post("a1", r("helper", 60, "job"), envelope=True)
    b.post("a1", r("helper-call", 50, "helper"))
    assert total(b) == 100
    with pytest.raises(Fault, match="ENVELOPE_EXHAUSTED"):
        b.post("a1", r("extra", 1, "job"))
    b.post("a1", r("call", 10, "job", "settle"))
    b.post("a1", r("helper-call", 20, "helper", "settle"))
    assert total(b) == 100
    with b.database.transaction() as db:
        b.post_in_transaction(db, "a1", r("helper", 0, "job", "settle"), close_envelope=True)
    assert total(b) == 100
    with b.database.transaction() as db:
        b.post_in_transaction(db, "a1", r("job", 0, posting="settle"), close_envelope=True)
    assert total(b) == 30
    with pytest.raises(Fault, match="ENVELOPE_CLOSED"):
        b.post("a1", r("late", 1, "job"))
    assert not b.post("a1", r("job", 100), envelope=True)
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        b.post("a1", r("job", 100))


def test_unknown_children_cannot_be_refunded_by_parent_closure(envelopes):
    b, r = envelopes
    b.post("a1", r("job", 100), envelope=True)
    b.post("a1", r("call", 40, "job"))
    b.hold_uncertain("a1", "call", "lost stream")
    assert total(b) == 100 and b.status("root")["uncertain"]
    with pytest.raises(Fault, match="DESCENDANT_UNSETTLED"), b.database.transaction() as db:
        b.post_in_transaction(db, "a1", r("job", 0, posting="settle"), close_envelope=True)
    with pytest.raises(Fault, match="ENVELOPE_POSTING"):
        b.post("a1", r("job", 0, posting="settle"))
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        b.post("a1", r("retry", 1, "job"))
    b.post("a1", r("call", 40, "job", "settle"))
    assert not b.status("root")["uncertain"] and total(b) == 100


def test_actual_overrun_is_retained_above_job_and_root_limits(envelopes):
    b, r = envelopes
    b.post("a1", r("job", 100), envelope=True)
    b.post("a1", r("call", 40, "job"))
    b.post("a1", r("call", 120, "job", "settle"))
    assert total(b) == 120
    with b.database.transaction() as db:
        b.post_in_transaction(db, "a1", r("job", 0, posting="settle"), close_envelope=True)
    assert total(b) == 120 and not b.status("root")["dispatch_allowed"]
    row = b.database.connection.execute("SELECT actual FROM operations WHERE id='call'").fetchone()
    assert json.loads(row[0])["spend_microusd"] == 120


def test_envelope_rollback_and_ordinary_parent_remains_additive(envelopes):
    b, r = envelopes
    b.post("a1", r("ordinary", 40))
    b.post("a1", r("nested", 60, "ordinary"), envelope=True)
    b.post("a1", r("call", 30, "nested"))
    assert total(b) == 100
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        b.post("a1", r("extra", 1), envelope=True)
    assert b.database.connection.execute(
        "SELECT 1 FROM budget_envelopes WHERE operation='extra'").fetchone() is None


def test_concurrent_descendants_cannot_multiply_preallocated_capacity(envelopes):
    b, r = envelopes
    b.post("a1", r("job", 100), envelope=True)
    def reserve(op):
        db = Database(b.database.path)
        try:
            Budgets(db).post("a1", r(op, 60, "job"))
            return "admitted"
        except Fault as error:
            return error.code
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reserve, ("child1", "child2")))
    assert sorted(outcomes) == ["ENVELOPE_EXHAUSTED", "admitted"]
    assert total(b) == 100
