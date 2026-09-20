from concurrent.futures import ThreadPoolExecutor

import pytest

from mcbench.budgets import DIMENSIONS, Budgets
from mcbench.clocks import Clocks
from mcbench.records import BudgetLedger
from mcbench.storage import Database, Fault


def receipt(example, op, posting, *, tokens=100, spend=10, parent=None, kind="model", source=None):
    body = example("BudgetLedger")
    return BudgetLedger.model_validate(body | {"is_example": False, "operation_id": op,
        "parent_operation_id": parent, "posting": posting, "source_event_id": source or f"{op}:{posting}",
        "kind": kind, "usage": body["usage"] | {"input_tokens": tokens, "cached_input_tokens": 0,
            "output_tokens": 10, "reasoning_tokens": None, "spend_microusd": spend}})


def accounts(budget, tokens=1000):
    limits = dict.fromkeys(DIMENSIONS, 10000) | {"input_tokens": tokens}
    budget.create_account("operator", limits, "*")
    budget.create_account("training", limits, "c1", parent="operator", category="training")
    budget.create_account("a1", limits, "c1", "a1", "training")
    budget.create_account("evaluation", limits, "c2", "a1", "operator", category="evaluation")


def test_reserve_settle_nested_retry_idempotency_overrun(database, example):
    budget = Budgets(database)
    accounts(budget)
    reserve = receipt(example, "root", "reserve", tokens=500)
    budget.post("a1", reserve)
    assert not budget.post("a1", reserve)
    budget.post("a1", receipt(example, "helper", "reserve", parent="root", kind="helper"))
    budget.post("a1", receipt(example, "grandchild", "reserve", parent="helper", kind="helper"))
    budget.post("a1", receipt(example, "root", "settle", tokens=200))
    assert budget.status("operator")["committed_and_reserved"]["input_tokens"] == 400
    budget.post("a1", receipt(example, "retry", "reserve"))
    budget.post("a1", receipt(example, "retry", "settle"))
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        budget.post("a1", receipt(example, "root", "reserve", tokens=499))
    with pytest.raises(Fault, match="ALREADY_SETTLED"):
        budget.post("a1", receipt(example, "retry", "settle", source="new-notification"))
    budget.post("a1", receipt(example, "helper", "settle", tokens=1000, parent="root", kind="helper"))
    assert budget.status("operator")["committed_and_reserved"]["input_tokens"] == 1400
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        budget.post("a1", receipt(example, "after-overrun", "reserve"))


def test_unknown_cost_and_negative_rollback_never_free_capacity(database, example):
    budget = Budgets(database)
    accounts(budget)
    budget.post("a1", receipt(example, "root", "reserve"))
    budget.post("a1", receipt(example, "root", "settle", spend=None))
    assert budget.status("a1")["committed_and_reserved"]["spend_microusd"] is None
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        budget.post("a1", receipt(example, "new", "reserve"))
    adjustment = receipt(example, "root", "adjust", tokens=-100).model_dump()
    adjustment["reason"] = "world-rollback"
    with pytest.raises(Fault, match="INVALID_ADJUSTMENT"):
        budget.post("a1", BudgetLedger.model_validate(adjustment))


def test_concurrent_accounts_cannot_overspend_parent(database, example, tmp_path):
    budget = Budgets(database)
    accounts(budget, tokens=100)
    path = tmp_path / "operator.sqlite"
    def attempt(op):
        db = Database(path)
        try:
            Budgets(db).post("a1", receipt(example, op, "reserve", tokens=100))
            return "reserved"
        except Fault as error:
            return error.code
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, ["first", "second"])) == ["BUDGET_EXHAUSTED", "reserved"]
    assert budget.status("operator")["committed_and_reserved"]["input_tokens"] == 100


def test_actual_clocks_pause_thinking_disconnect_rollback(database):
    clock = Clocks(database)
    args = dict(elapsed_ms=1000, n=2, server_stopped=False, inference_suspended=False,
                server_ticks=17, avatar_ticks=29, disconnected_body_ms=200, boot_id="boot1")
    clock.record("c1", "one", **args)
    clock.record("c1", "one", **args)
    clock.record("c1", "thinking-server-stopped", **(args | {"server_stopped": True,
                 "server_ticks": 0, "avatar_ticks": 0}))
    clock.record("c1", "true-pause", **(args | {"server_stopped": True,
                 "server_ticks": 0, "avatar_ticks": 0, "inference_suspended": True}))
    clock.record("c1", "after-rollback", **(args | {"boot_id": "boot2"}))
    total = clock.totals("c1")
    assert (total["elapsed_ms"], total["active_ms"], total["reserved_body_ms"]) == (4000, 3000, 6000)
    assert (total["server_ticks"], total["avatar_ticks"]) == (34, 58)
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        clock.record("c1", "one", **(args | {"server_ticks": 20}))
