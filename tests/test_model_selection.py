"""D17 model migration, using synthetic authority/history only."""

from pathlib import Path

import pytest

from mcbench.authorization import ModelExecutionAuthorization, parse_authorization
from mcbench.storage import Fault, Principal, canonical, digest
import test_pilot_budget as pilot_tests

trial = pilot_tests.trial
make_plan = pilot_tests.make_plan
pilot_trial = pilot_tests.pilot_trial


def selection():
    return ModelExecutionAuthorization.model_validate_json(
        (Path(__file__).resolve().parents[1] / "configs/operator/live-validation.json").read_bytes())


def decision(t, policy, snapshot):
    return {"schema": "strata/ModelSelectionDecision/1", "decision_id": "D17",
        "authorization_id": policy.authorization_id, "user_authorized": True,
        "source_digest": policy.previous_authorization_digest, "target_digest": digest(policy.model_dump()),
        "snapshot_digest": snapshot, "store_path_digest": digest(str(t.db.path)), "model": "gpt-6-luna",
        "new_allowance": False, "clears_unknown_usage": False, "rearms_consumed_trials": False}


def apply(t, policy, snapshot=None, changed_decision=None):
    snapshot = snapshot or t.auth.snapshot()
    body = decision(t, policy, snapshot) | (changed_decision or {})
    ref = t.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(body))
    return t.auth.switch_model(policy, snapshot_digest=snapshot, decision_ref=ref, cas=t.cas)


def test_new_model_keeps_same_budget_history_and_unknown_holds(pilot_trial):
    t = pilot_trial
    policy = selection()
    before = t.auth.snapshot()
    old = dict(t.db.connection.execute("SELECT * FROM execution_authorizations").fetchone())
    assert apply(t, policy) == t.authority
    assert t.auth.snapshot() == before
    row = dict(t.db.connection.execute("SELECT * FROM authorization_model_changes").fetchone())
    assert (row["source_body"], row["source_digest"]) == (old["body"], old["digest"])
    assert t.auth.check(policy.authorization_id, t.plan.account, "openai", "chatgpt_oauth", "gpt-6-luna") == policy
    with pytest.raises(Fault, match="UNAUTHORIZED_MODEL_OR_PROVIDER"):
        t.auth.check(policy.authorization_id, t.plan.account, "openai", "chatgpt_oauth", "gpt-5.6-luna")
    assert t.auth.status(policy.authorization_id)["budget"]["dispatch_allowed"] is False
    assert apply(t, policy) == t.authority
    assert t.db.connection.execute("SELECT count(*) FROM authorization_model_changes").fetchone()[0] == 1
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.root, envelope=True)
    assert t.auth.snapshot() == before
    assert pilot_tests.uncertain_rows(t.db.connection, t.authority) == t.retained


@pytest.mark.parametrize("change", [{"total_spend_microusd": 11000000}, {"first_trial_max_microusd": 2000000},
    {"includes": ["development"]}, {"models": ["gpt-6-astra"]}, {"auth_mode": "api_key"},
    {"previous_authorization_digest": "0" * 64}])
def test_model_selection_cannot_expand_other_authority(pilot_trial, change):
    t = pilot_trial
    before = t.auth.snapshot()
    with pytest.raises(Fault, match="MODEL_CHANGE_SCOPE|MODEL_CHANGE_SOURCE_CHANGED"):
        apply(t, selection().model_copy(update=change))
    assert t.auth.snapshot() == before
    assert t.auth.status(t.approved.authorization_id)["authorization"]["decision_id"] == "D11"


def test_model_selection_requires_current_snapshot_and_explicit_exact_decision(pilot_trial):
    t = pilot_trial
    with pytest.raises(Fault, match="MODEL_CHANGE_DECISION_REQUIRED"):
        apply(t, selection(), changed_decision={"user_authorized": False})
    with pytest.raises(Fault, match="MODEL_CHANGE_SNAPSHOT_CHANGED"):
        apply(t, selection(), snapshot="0" * 64)


@pytest.mark.parametrize("state,ended,code", [("RUNNING", None, None), ("UNSETTLED", None, None)])
def test_model_selection_refuses_unclosed_native_process(pilot_trial, state, ended, code):
    t = pilot_trial
    t.db.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,?,?,NULL)",
        ("active", "c1", "a1", 1, "executor", None, "fixture", canonical(t.plan.model_dump()).decode(), state, ended, code))
    with pytest.raises(Fault, match="MODEL_CHANGE_ACTIVE_JOB"):
        apply(t, selection())


def test_luna6_pricing_and_legacy_basis_are_distinct():
    policy = selection()
    assert parse_authorization(policy.model_dump()) == policy
    basis = policy.accounting_basis
    assert basis.maximum_request(max_input_tokens=1050000, max_output_tokens=128000) == 358500
    usage = {"model": "gpt-6-luna", "input_tokens": 10000, "cached_input_tokens": 0,
             "cache_write_tokens": 0, "output_tokens": 1000, "reasoning_tokens": 0}
    assert basis.estimate(usage) == 1500
    old = pilot_tests.metering_tests.policy().accounting_basis
    assert old.estimate(usage | {"model": old.model}) == 3200
    with pytest.raises(Fault, match="PRICE_MODEL_MISMATCH"):
        old.estimate(usage)
