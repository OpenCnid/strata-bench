"""D15 synthetic accounting: bounded sequential requests, no real dispatch."""

import json
import time

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.native_piloting import MAX_SPEND, MAX_REQUESTS, PURPOSE
from mcbench.pilot_budget import DECISIONS, JOB, decision_body, install
from mcbench.storage import Fault, canonical
from test_metering_trial import uncertain_rows
import test_metering_trial as metering_tests

trial = metering_tests.trial
make_plan = metering_tests.make_plan


@pytest.fixture
def pilot_trial(trial):
    t = trial
    # Synthetic already-settled D12 analogue, distinct from the old unknowns.
    amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 1458, "model_calls": 1}
    t.db.connection.execute("INSERT INTO operations VALUES('settled-d12','old-account',NULL,'model',?,?,0)",
                           (canonical(amount).decode(), canonical(amount).decode()))
    t.plan = t.plan.model_copy(update={"job_id": JOB, "account": JOB+":account", "operation_id": JOB+":envelope",
        "purpose": PURPOSE, "hard_timeout_s": 90, "budget_mode": "per_dispatch"})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": MAX_SPEND, "model_calls": MAX_REQUESTS}, "c1", "a1", t.authority, category="development")
    t.root = t.reserve(t.plan, t.plan.operation_id).model_copy(update={"usage": t.root.usage.model_copy(update={
        "spend_microusd": MAX_SPEND, "model_calls": MAX_REQUESTS,
        "input_tokens": 6300000, "output_tokens": 768000})})
    t.decision = decision_body(t.db.connection)
    def authorize():
        return install(t.db, t.cas, t.plan, t.root, t.decision)
    def prepare():
        t.db.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (JOB, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "PREPARED"))
        t.budgets.post(t.plan.account, t.root, envelope=True)
        t.db.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (JOB,))
    t.authorize, t.prepare = authorize, prepare
    return t


def settle(t, record, spend=1000):
    actual = record.model_copy(update={"posting": "settle", "source_event_id": record.source_event_id+":actual",
        "usage": record.usage.model_copy(update={"spend_microusd": spend})})
    t.budgets.post(t.plan.account, actual)


def test_six_sequential_receipts_preserve_holds_and_single_envelope(pilot_trial):
    t = pilot_trial
    t.authorize()
    t.prepare()
    for i in range(6):
        r = t.reserve(t.plan, f"new-{i}", t.plan.operation_id)
        t.budgets.post(t.plan.account, r)
        assert not t.budgets.post(t.plan.account, r)  # identical posting consumes no second request
        settle(t, r)
    assert uncertain_rows(t.db.connection, t.authority) == t.retained
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == 1756858
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.reserve(t.plan, "seventh", t.plan.operation_id))
    assert t.db.connection.execute("SELECT requests FROM pilot_trials").fetchone()[0] == 6


@pytest.mark.parametrize("case", ["new_unknown", "concurrent", "old_changed", "expired", "wrong_model", "helper", "overspend"])
def test_no_expansion_or_unknown_replay(pilot_trial, case):
    t = pilot_trial
    t.authorize()
    t.prepare()
    r = t.reserve(t.plan, "first", t.plan.operation_id)
    if case in {"concurrent", "new_unknown", "overspend"}:
        t.budgets.post(t.plan.account, r)
        if case == "new_unknown":
            t.budgets.hold_uncertain(t.plan.account, "first", "missing receipt")
        elif case == "overspend":
            settle(t, r, spend=300000)
        r = t.reserve(t.plan, "second", t.plan.operation_id)
    elif case == "old_changed":
        t.db.connection.execute("UPDATE operations SET uncertain=0 WHERE id='old-request'")
    elif case == "expired":
        body = json.loads(t.db.connection.execute("SELECT body FROM pilot_trials").fetchone()[0])
        body["expires_unix"] = time.time()-1
        t.db.connection.execute("UPDATE pilot_trials SET body=?", (canonical(body).decode(),))
    elif case == "wrong_model":
        r = r.model_copy(update={"model_identity": "other"})
    elif case == "helper":
        r = r.model_copy(update={"kind": "helper"})
    with pytest.raises(Fault, match="METERING_UNKNOWN|ENVELOPE_EXHAUSTED"):
        t.budgets.post(t.plan.account, r)
    assert t.db.connection.execute("SELECT requests FROM pilot_trials").fetchone()[0] == int(case in {"concurrent", "new_unknown", "overspend"})


def test_reinstall_and_general_dispatch_remain_denied(pilot_trial):
    t = pilot_trial
    t.authorize()
    with pytest.raises(Fault, match="PILOT_ALREADY_ATTEMPTED"):
        t.authorize()
    t.prepare()
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post("old-account", t.reserve(t.plan, "unrelated"), envelope=True)
    assert not t.budgets.status(t.authority)["dispatch_allowed"]


@pytest.fixture
def corrected_trial(pilot_trial):
    """Synthetic closed D15 history; no provider or game execution."""
    t = pilot_trial
    db = t.db.connection
    amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 6422, "model_calls": 6}
    db.execute("INSERT INTO operations VALUES('settled-d15','old-account',NULL,'model',?,?,0)",
               (canonical(amount).decode(), canonical(amount).decode()))
    db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (JOB, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "FINALIZED"))
    db.execute("CREATE TABLE inference_attempts (request TEXT, state TEXT)")
    db.executemany("INSERT INTO inference_attempts VALUES(?,'SETTLED')",
                   [(canonical({"runtime_job_id": JOB}).decode(),)] * 6)
    job = DECISIONS["D16"][0]
    t.plan = t.plan.model_copy(update={"job_id": job, "account": job+":account", "operation_id": job+":envelope"})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": MAX_SPEND, "model_calls": MAX_REQUESTS}, "c1", "a1", t.authority, category="development")
    t.root = t.root.model_copy(update={"operation_id": t.plan.operation_id})
    t.decision = decision_body(db, "D16")
    return t


def test_d16_preserves_closed_prior_run_and_is_single_use(corrected_trial):
    t = corrected_trial
    before = list(t.db.connection.execute("SELECT * FROM native_jobs"))
    assert t.decision["combined_exposure_microusd"] == 1763280
    t.authorize()
    assert list(t.db.connection.execute("SELECT * FROM native_jobs")) == before
    assert uncertain_rows(t.db.connection, t.authority) == t.retained
    with pytest.raises(Fault, match="PILOT_ALREADY_ATTEMPTED"):
        t.authorize()


@pytest.mark.parametrize("case", ["running", "unsettled", "wrong_job", "new_cost"])
def test_d16_requires_exact_approved_history(corrected_trial, case):
    t = corrected_trial
    if case == "running":
        t.db.connection.execute("UPDATE native_jobs SET state='RUNNING'")
    elif case == "unsettled":
        t.db.connection.execute("UPDATE inference_attempts SET state='UNKNOWN' WHERE rowid=1")
    elif case == "wrong_job":
        t.plan = t.plan.model_copy(update={"job_id": JOB})
    else:
        t.db.connection.execute("DELETE FROM operations WHERE id='settled-d15'")
    with pytest.raises(Fault, match="PILOT_PRIOR_RUN_UNSETTLED|PILOT_BUDGET_SCOPE|PILOT_RETAINED_HOLDS_CHANGED"):
        t.authorize()
