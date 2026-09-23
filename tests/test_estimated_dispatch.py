"""Versioned estimate admission through the existing durable dispatch machinery."""

import json
import time
from pathlib import Path

import pytest

from mcbench.accounting import FiniteExposure, UsageValuation
from mcbench.authorization import ExecutionAuthorization
from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest


@pytest.fixture
def estimated(database, cas, example):
    policy = ExecutionAuthorization.model_validate_json(
        (Path(__file__).resolve().parents[1] / "configs/operator/legacy/live-validation-d11.json").read_text(
            encoding="utf-8"
        )
    )
    basis = policy.accounting_basis
    gate = InferenceDispatches(database, cas, simulation=True)
    gate.budgets.create_account(
        "a1",
        dict.fromkeys(DIMENSIONS, 100000000) | {"spend_microusd": 1000000},
        "c1",
        "a1",
        category="training",
    )

    def put(value):
        return cas.put(Principal("operator", "operator"), "operator", "operator", canonical(value))

    price = put(basis.model_dump(by_alias=True))
    proof = {
        "schema": "strata/InferenceExposureEvidence/1",
        "is_example": True,
        "profile_digest": "b" * 64,
        "basis_digest": basis.fingerprint(),
        "input_bound_method": "provider_context_limit",
        "output_bound_method": "provider_model_limit",
        "max_input_tokens": 1050000,
        "max_output_tokens": 128000,
        "result": "pass",
    }
    exposure = FiniteExposure.model_validate(
        {
            "schema": "strata/FiniteInferenceExposure/1",
            **{
                k: proof[k]
                for k in (
                    "basis_digest",
                    "input_bound_method",
                    "output_bound_method",
                    "max_input_tokens",
                    "max_output_tokens",
                )
            },
            "max_requests": 1,
            "enforcement_ref": put(proof),
        }
    )
    base = example("BudgetLedger")
    envelope = BudgetLedger.model_validate(
        base
        | {
            "is_example": False,
            "operation_id": "job",
            "parent_operation_id": None,
            "posting": "reserve",
            "source_event_id": "job:reserve",
            "metering": "estimated",
            "pricing_ref": price,
            "model_identity": basis.model,
            "usage": dict.fromkeys(base["usage"], 0)
            | {
                "input_tokens": 100000000,
                "output_tokens": 100000000,
                "model_calls": 100,
                "spend_microusd": 1000000,
            },
        }
    )
    gate.budgets.post("a1", envelope, envelope=True)

    def make(op, *, spend=None, bound_updates=None, kind="model"):
        reserve = BudgetLedger.model_validate(
            envelope.model_dump()
            | {
                "operation_id": op,
                "parent_operation_id": "job",
                "source_event_id": op + ":reserve",
                "kind": kind,
                "usage": dict.fromkeys(base["usage"], 0)
                | {
                    "input_tokens": 1050000,
                    "output_tokens": 128000,
                    "model_calls": 1,
                    "spend_microusd": exposure.amount(basis) if spend is None else spend,
                },
            }
        )
        scope = {
            "runtime_job_id": "job",
            "profile_digest": "b" * 64,
            "provider": "openai",
            "auth_mode": "chatgpt_oauth",
            "request_digest": "a" * 64,
        }
        bound = {
            "schema": "strata/InferenceDispatchBound/2",
            "is_example": True,
            **scope,
            "reservation_digest": digest(reserve.model_dump()),
            "pricing_ref": price,
            "currency": "USD",
            "finite_dispatch_bound_verified": True,
            "pricing_semantics_verified": True,
            "expires_unix_ms": time.time_ns() // 1000000 + 60000,
            "exposure": exposure.model_dump(),
            **(bound_updates or {}),
        }
        attempt = InferenceAttempt.model_validate(
            {"schema": "strata/InferenceAttempt/1", **scope, "bound_ref": put(bound)}
        )
        usage = {
            "model": basis.model,
            "input_tokens": 1000,
            "cached_input_tokens": 200,
            "cache_write_tokens": 100,
            "output_tokens": 100,
            "reasoning_tokens": 20,
        }
        raw = put({"is_example": True, "op": op, "usage": usage})
        valuation = UsageValuation.model_validate(
            {
                "schema": "strata/UsageValuation/1",
                "kind": "api_equivalent_estimate",
                "basis_digest": basis.fingerprint(),
                "raw_usage_ref": raw,
                "usage": usage,
                "amount_microusd": basis.estimate(usage),
                "token_evidence": "synthetic_fixture",
            }
        )
        receipt = BudgetLedger.model_validate(
            reserve.model_dump()
            | {
                "posting": "settle",
                "source_event_id": op + ":settle",
                "raw_usage_ref": raw,
                "usage": reserve.usage.model_dump()
                | {
                    k: usage[k]
                    for k in (
                        "input_tokens",
                        "cached_input_tokens",
                        "output_tokens",
                        "reasoning_tokens",
                    )
                }
                | {"spend_microusd": valuation.amount_microusd},
            }
        )
        return attempt, reserve, receipt, valuation

    return gate, make, envelope, put, exposure


def test_root_helper_retry_summary_each_charge_once_and_envelope_does_not(estimated):
    gate, make, envelope, _, _ = estimated
    for op in ("root", "helper", "retry", "summary"):
        a, r, s, v = make(op, kind="helper" if op == "helper" else "model")
        assert gate.execute("a1", a, r, lambda: ("event-" + op, s, v))["state"] == "SETTLED"
        assert not gate.settle(op, "event-" + op, s, valuation=v)
        gate.execute("a1", a, r, lambda: pytest.fail("duplicate dispatch"))
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000000
    closed = BudgetLedger.model_validate(
        envelope.model_dump()
        | {
            "posting": "settle",
            "source_event_id": "job:close",
            "metering": "reported",
            "raw_usage_ref": s.raw_usage_ref,
            "usage": dict.fromkeys(envelope.usage.model_dump(), 0),
        }
    )
    with gate.db.transaction() as db:
        gate.budgets.post_in_transaction(db, "a1", closed, close_envelope=True)
    amount = gate.budgets.status("a1")["committed_and_reserved"]
    # 700*.2 + 200*.02 + 100*.25 + 100*1.2 = 289 microUSD per request.
    assert amount["spend_microusd"] == 4 * 289 and amount["model_calls"] == 4
    assert (
        gate.db.connection.execute("SELECT count(*) FROM inference_valuations").fetchone()[0] == 4
    )


def test_full_verified_bound_blocks_second_unsettled_request_before_forward(estimated):
    gate, make, _, _, _ = estimated
    a, r, _, _ = make("first")
    assert gate._begin("a1", a, r)
    a2, r2, _, _ = make("second")
    with pytest.raises(Fault, match="ENVELOPE_EXHAUSTED"):
        gate.execute("a1", a2, r2, lambda: pytest.fail("admission must reject"))
    db = Database(gate.db.path)
    try:
        restored = InferenceDispatches(db, CAS(db, gate.cas.root), simulation=True)
        assert restored.recover() == ["first"]
        assert (
            restored.execute("a1", a, r, lambda: pytest.fail("no replay"))["state"] == "UNSETTLED"
        )
        assert restored.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000000
    finally:
        db.close()


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "actual_charge",
        "wrong_amount",
        "wrong_counters",
        "reported_money",
        "live_tokens",
        "wrong_basis",
    ],
)
def test_bad_valuation_retains_reservation(change, estimated):
    gate, make, _, _, _ = estimated
    a, r, s, v = make("bad")
    if change == "missing":
        v = None
    if change == "actual_charge":
        v = v.model_copy(update={"kind": "actual_charge"})
    if change == "wrong_amount":
        v = v.model_copy(update={"amount_microusd": 0})
    if change == "wrong_counters":
        s = s.model_copy(update={"usage": s.usage.model_copy(update={"input_tokens": 999})})
    if change == "reported_money":
        s = s.model_copy(update={"metering": "reported"})
    if change == "live_tokens":
        v = v.model_copy(update={"token_evidence": "provider_reported"})
    if change == "wrong_basis":
        v = v.model_copy(update={"basis_digest": "f" * 64})
    with pytest.raises(Fault, match="USAGE_VALUATION_MISMATCH"):
        gate.execute("a1", a, r, lambda: ("event-bad", s, v))
    assert gate.status("bad")["state"] == "UNSETTLED"
    assert gate.budgets.status("a1")["uncertain"]
    assert (
        gate.db.connection.execute("SELECT count(*) FROM inference_valuations").fetchone()[0] == 0
    )


def test_understated_bound_and_unqualified_proof_reject(estimated):
    gate, make, _, put, exposure = estimated
    a, r, _, _ = make("cheap", spend=1)
    with pytest.raises(Fault, match="DISPATCH_ESTIMATE_MISMATCH"):
        gate.execute("a1", a, r, lambda: pytest.fail("understated bound"))
    bad = exposure.model_dump() | {"enforcement_ref": put({"result": "pass"})}
    a, r, _, _ = make("unsupported", bound_updates={"exposure": bad})
    with pytest.raises(Fault, match="EXPOSURE_UNQUALIFIED"):
        gate.execute("a1", a, r, lambda: pytest.fail("mere flag is insufficient"))
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_valuation_conflict_does_not_replace_settlement(estimated):
    gate, make, _, _, _ = estimated
    a, r, s, v = make("one")
    gate.execute("a1", a, r, lambda: ("event-one", s, v))
    old = json.loads(
        gate.db.connection.execute("SELECT body FROM inference_valuations").fetchone()[0]
    )
    v2 = v.model_copy(update={"usage": v.usage.model_copy(update={"cache_write_tokens": 101})})
    # Different cache information can round to the same amount; it is still a conflict.
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT|USAGE_VALUATION_MISMATCH"):
        gate.settle("one", "event-one", s, valuation=v2)
    assert (
        json.loads(
            gate.db.connection.execute("SELECT body FROM inference_valuations").fetchone()[0]
        )
        == old
    )


def test_receipted_overrun_is_retained_and_quarantines_admission_after_restart(estimated):
    from mcbench.accounting import EstimateBasis

    gate, make, _, put, _ = estimated
    a, r, s, v = make("overrun")
    usage = v.usage.model_copy(update={"output_tokens": 128001})
    basis = EstimateBasis.model_validate_json(gate._private_ref(r.pricing_ref, 65536))
    amount = basis.estimate(usage)
    raw = put({"is_example": True, "usage": usage.model_dump()})
    v = v.model_copy(update={"usage": usage, "amount_microusd": amount, "raw_usage_ref": raw})
    s = s.model_copy(
        update={
            "raw_usage_ref": raw,
            "usage": s.usage.model_copy(update={"output_tokens": 128001, "spend_microusd": amount}),
        }
    )
    status = gate.execute("a1", a, r, lambda: ("overrun-event", s, v))
    assert status["state"] == "SETTLED" and status["exposure_quarantined"]
    actual = json.loads(
        gate.db.connection.execute("SELECT actual FROM operations WHERE id='overrun'").fetchone()[0]
    )
    assert actual["output_tokens"] == 128001 and actual["spend_microusd"] == amount
    a2, r2, _, _ = make("next")
    db = Database(gate.db.path)
    try:
        restored = InferenceDispatches(db, CAS(db, gate.cas.root), simulation=True)
        with pytest.raises(Fault, match="INFERENCE_EXPOSURE_QUARANTINED"):
            restored.execute("a1", a2, r2, lambda: pytest.fail("invalid bound must stop admission"))
    finally:
        db.close()
