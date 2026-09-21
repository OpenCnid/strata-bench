"""Synthetic billing proofs/receipts; no provider or OAuth qualification."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from mcbench.budgets import DIMENSIONS, Budgets
from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest


@pytest.fixture
def gateway(database, cas):
    gate = InferenceDispatches(database, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 10000) | {"spend_microusd": 100}
    gate.budgets.create_account("root", limits, "*")
    gate.budgets.create_account("a1", limits, "c1", "a1", "root", category="training")
    return gate


@pytest.fixture
def make_attempt(gateway, example):
    def put(value, visibility="operator"):
        return gateway.cas.put(Principal("operator", "operator"), "operator", visibility,
                               canonical(value))
    price = put({"schema": "synthetic-pricing-fixture", "is_example": True})
    raw = put({"schema": "synthetic-reported-usage-fixture", "is_example": True})

    def make(op, *, spend=60, request_digest="a" * 64, bound_updates=None, **updates):
        body = example("BudgetLedger")
        reserve = BudgetLedger.model_validate(body | {
            "is_example": False, "operation_id": op, "parent_operation_id": None,
            "source_event_id": op + ":reserve", "ledger_id": op + ":reservation",
            "posting": "reserve", "kind": "model", "model_identity": "synthetic-no-model",
            "pricing_ref": price, "raw_usage_ref": None, "metering": "estimated",
            "usage": body["usage"] | {"input_tokens": 100, "cached_input_tokens": 0,
                "output_tokens": 20, "reasoning_tokens": None, "spend_microusd": spend,
                "model_calls": 1, "primitive_events": 0, "avatar_ticks": 0, "wall_ms": 0},
            **updates})
        fields = {"runtime_job_id": "job1", "profile_digest": "b" * 64,
                  "provider": "openai", "auth_mode": "chatgpt_oauth",
                  "request_digest": request_digest}
        bound = {"schema": "strata/InferenceDispatchBound/1", "is_example": True,
            **fields, "reservation_digest": digest(reserve.model_dump()), "pricing_ref": price,
            "currency": "USD", "finite_dispatch_bound_verified": True,
            "pricing_semantics_verified": True, "expires_unix_ms": time.time_ns() // 1000000 + 60000,
            **(bound_updates or {})}
        attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1",
                                                  **fields, "bound_ref": put(bound)})

        def settlement(cost=20, **changes):
            return BudgetLedger.model_validate(reserve.model_dump() | {
                "posting": "settle", "ledger_id": op + ":receipt",
                "source_event_id": op + ":settle", "metering": "reported", "raw_usage_ref": raw,
                "usage": reserve.usage.model_dump() | {"input_tokens": 5, "output_tokens": 2,
                                                       "spend_microusd": cost, "wall_ms": 7},
                **changes})
        return attempt, reserve, settlement
    return make


def test_reserve_commits_before_forward_and_duplicates_never_resend(gateway, make_attempt):
    attempt, reserve, settle = make_attempt("one")
    sent = []
    def forward():
        assert gateway.status("one")["state"] == "DISPATCHING"
        assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 60
        other = Database(gateway.db.path)
        try:
            assert other.connection.execute(
                "SELECT state FROM inference_attempts").fetchone()[0] == "DISPATCHING"
        finally:
            other.close()
        sent.append(True)
        return "provider-one", settle()
    assert gateway.execute("a1", attempt, reserve, forward)["state"] == "SETTLED"
    assert gateway.execute("a1", attempt, reserve, forward)["state"] == "SETTLED"
    assert sent == [True]
    assert not gateway.settle("one", "provider-one", settle())
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 20
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        gateway.execute("a1", attempt.model_copy(update={"request_digest": "c" * 64}), reserve, forward)


def test_identical_retry_bodies_reserve_and_charge_distinct_attempts(gateway, make_attempt):
    for op in ("one", "retry"):
        a, r, s = make_attempt(op)
        gateway.execute("a1", a, r, lambda: ("provider-" + op, s(30)))
    totals = gateway.budgets.status("root")["committed_and_reserved"]
    assert (totals["model_calls"], totals["spend_microusd"]) == (2, 60)
    a, r, s = make_attempt("over-limit")
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        gateway.execute("a1", a, r, lambda: pytest.fail("must reject before transport"))
    assert gateway.db.connection.execute("SELECT COUNT(*) FROM inference_attempts").fetchone()[0] == 2


def test_budget_denial_is_durable_nonreplayable_and_not_a_receipt(gateway, make_attempt):
    first, hold, settlement = make_attempt("in-flight")
    gateway._begin("a1", first, hold)
    attempt, reserve, _ = make_attempt("denied")
    before = gateway.budgets.status("root")
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        gateway.execute("a1", attempt, reserve, lambda: pytest.fail("denied request forwarded"))
    status = gateway.status("denied")
    assert status["state"] == "REJECTED_BEFORE_DISPATCH" and not status["usage_receipt"]
    assert gateway.budgets.status("root") == before
    gateway.settle("in-flight", "first-receipt", settlement(20))  # Room now exists, but this ID is terminal.
    second = Database(gateway.db.path)
    try:
        restored = InferenceDispatches(second, CAS(second, gateway.cas.root), simulation=True)
        assert restored.status("denied") == status
        with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
            restored.execute("a1", attempt, reserve, lambda: pytest.fail("restart replayed denial"))
        with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
            restored._begin("a1", attempt.model_copy(update={"request_digest": "f" * 64}), reserve)
        from mcbench.inference_dispatch import verified_rejections
        assert set(verified_rejections(second.connection, "job1", True)) == {"denied"}
    finally:
        second.close()
    new_attempt, new_reserve, new_settlement = make_attempt("distinct")
    gateway.execute("a1", new_attempt, new_reserve, lambda: ("second-receipt", new_settlement(20)))
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 40
    assert gateway.db.connection.execute("SELECT count(*) FROM inference_rejections").fetchone()[0] == 1


def test_failed_denial_commit_never_becomes_a_rejection_or_dispatch(gateway, make_attempt):
    attempt, reserve, _ = make_attempt("denied", spend=101)
    gateway.db.connection.execute("CREATE TRIGGER fail_rejection BEFORE INSERT ON inference_rejections "
        "BEGIN SELECT RAISE(ABORT,'synthetic rejection write failure'); END")
    with pytest.raises(Exception, match="synthetic rejection write failure"):
        gateway.execute("a1", attempt, reserve, lambda: pytest.fail("failed commit forwarded"))
    for table in ("inference_attempts", "inference_rejections", "operations", "ledger"):
        assert gateway.db.connection.execute("SELECT count(*) FROM " + table).fetchone()[0] == 0
    assert gateway.db.connection.execute("SELECT count(*) FROM outbox WHERE kind LIKE 'inference.%'").fetchone()[0] == 0


def test_denial_due_to_unknown_usage_does_not_clear_the_unknown_hold(gateway, make_attempt):
    attempt, reserve, _ = make_attempt("ambiguous")
    gateway._begin("a1", attempt, reserve)
    gateway.mark_uncertain("ambiguous", "transport_or_receipt_uncertain")
    before = gateway.budgets.status("root")
    attempt, reserve, _ = make_attempt("denied", spend=1)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        gateway._begin("a1", attempt, reserve)
    assert gateway.status("ambiguous")["state"] == "UNSETTLED"
    assert gateway.budgets.status("root") == before and before["uncertain"]
    assert gateway.status("denied")["state"] == "REJECTED_BEFORE_DISPATCH"


@pytest.mark.parametrize("updates", [
    {"expires_unix_ms": 1}, {"is_example": False}, {"request_digest": "f" * 64},
    {"reservation_digest": "f" * 64}, {"pricing_semantics_verified": False},
    {"finite_dispatch_bound_verified": False}, {"profile_digest": "f" * 64},
])
def test_unknown_expired_wrong_or_live_bound_never_dispatches(gateway, make_attempt, updates):
    a, r, _ = make_attempt("one", bound_updates=updates)
    with pytest.raises(Fault, match="DISPATCH_BOUND_UNVERIFIED"):
        gateway.execute("a1", a, r, lambda: pytest.fail("no dispatch"))
    assert gateway.db.connection.execute("SELECT COUNT(*) FROM operations").fetchone()[0] == 0


def test_transport_failure_holds_reserve_until_authoritative_reconciliation(gateway, make_attempt):
    a, r, s = make_attempt("one")
    def fail():
        raise ConnectionError("synthetic lost response after possible billing")
    with pytest.raises(ConnectionError):
        gateway.execute("a1", a, r, fail)
    assert gateway.status("one")["state"] == "UNSETTLED"
    assert gateway.budgets.status("root")["uncertain"]
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 60
    a2, r2, _ = make_attempt("retry", spend=1)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        gateway.execute("a1", a2, r2, lambda: pytest.fail("no unknown-cost retry"))
    assert gateway.execute("a1", a, r, fail)["state"] == "UNSETTLED"
    gateway.settle("one", "late-authoritative-receipt", s(35))
    assert not gateway.budgets.status("root")["uncertain"]
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 35


def test_crash_boundary_recovery_never_replays_and_profile_cannot_promote(gateway, make_attempt):
    a, r, _ = make_attempt("one")
    assert gateway._begin("a1", a, r)  # Synthetic crash immediately after durable intent.
    second = Database(gateway.db.path)
    try:
        cas = CAS(second, gateway.cas.root)
        restored = InferenceDispatches(second, cas, simulation=True)
        assert restored.recover() == ["one"]
        assert restored.recover() == []
        assert restored.execute("a1", a, r, lambda: pytest.fail("no replay"))["state"] == "UNSETTLED"
        assert restored.budgets.status("root")["uncertain"]
        with pytest.raises(Fault, match="DISPATCH_PROFILE_MISMATCH"):
            InferenceDispatches(second, cas, simulation=False)
    finally:
        second.close()


def test_failed_intent_insert_rolls_back_budget_and_journal(gateway, make_attempt):
    a, r, _ = make_attempt("one")
    gateway.db.connection.execute("CREATE TRIGGER fail_intent BEFORE INSERT ON inference_attempts "
                                  "BEGIN SELECT RAISE(ABORT,'synthetic write failure'); END")
    with pytest.raises(Exception, match="synthetic write failure"):
        gateway.execute("a1", a, r, lambda: pytest.fail("no dispatch after partial commit"))
    for table in ("inference_attempts", "operations", "ledger"):
        assert gateway.db.connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
    events = gateway.db.connection.execute("SELECT kind FROM outbox").fetchall()
    assert not any(e[0].startswith(("budget.", "inference.")) for e in events)


@pytest.mark.parametrize("change", [{"epoch": 2}, {"model_identity": "another-model"},
                                  {"metering": "estimated"}, {"raw_usage_ref": None}])
def test_invalid_settlement_retains_full_reservation(gateway, make_attempt, change):
    a, r, s = make_attempt("one")
    with pytest.raises(Fault):
        gateway.execute("a1", a, r, lambda: ("provider-one", s(**change)))
    assert gateway.status("one")["state"] == "UNSETTLED"
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 60


def test_overrun_retained_and_provider_event_reuse_does_not_double_settle(gateway, make_attempt):
    a, r, s = make_attempt("one")
    gateway.execute("a1", a, r, lambda: ("provider-one", s(1)))
    a2, r2, s2 = make_attempt("retry")
    with pytest.raises(Fault, match="PROVIDER_EVENT_REUSED"):
        gateway.execute("a1", a2, r2, lambda: ("provider-one", s2(1)))
    gateway.settle("retry", "provider-retry", s2(110))
    result = gateway.budgets.status("root")
    assert result["committed_and_reserved"]["spend_microusd"] == 111
    assert not result["dispatch_allowed"]


def test_concurrent_new_attempts_cannot_multiply_parent_cap(gateway, make_attempt):
    one, two = make_attempt("one"), make_attempt("two")
    barrier = threading.Barrier(2)
    def send(values):
        db = Database(gateway.db.path)
        try:
            g = InferenceDispatches(db, CAS(db, gateway.cas.root), simulation=True)
            a, r, _ = values
            barrier.wait(timeout=3)
            try:
                return g._begin("a1", a, r)
            except Fault as error:
                return error.code
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, (one, two)))
    assert results.count(True) == results.count("BUDGET_EXHAUSTED") == 1
    assert gateway.budgets.status("root")["committed_and_reserved"]["spend_microusd"] == 60


def test_ledger_transaction_composition_requires_own_active_transaction(gateway, make_attempt):
    _, r, _ = make_attempt("one")
    with pytest.raises(Fault, match="TRANSACTION_REQUIRED"):
        gateway.budgets.post_in_transaction(gateway.db.connection, "a1", r)
    with gateway.db.transaction() as db:
        assert gateway.budgets.post_in_transaction(db, "a1", r)
    assert Budgets(gateway.db).status("root")["committed_and_reserved"]["spend_microusd"] == 60


def test_native_and_dispatch_stores_cannot_mix_simulation_modes(gateway):
    from mcbench.native import NativeExec
    with pytest.raises(Fault, match="DISPATCH_PROFILE_MISMATCH"):
        NativeExec(gateway.db, gateway.cas, simulation=False)
    NativeExec(gateway.db, gateway.cas, simulation=True)


def test_existing_native_store_rejects_mismatched_dispatch_profile(database, cas):
    from mcbench.native import NativeExec
    NativeExec(database, cas, simulation=True)
    with pytest.raises(Fault, match="DISPATCH_PROFILE_MISMATCH"):
        InferenceDispatches(database, cas, simulation=False)
