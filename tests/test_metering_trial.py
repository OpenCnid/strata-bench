"""D12 accounting exception using synthetic rows; no OAuth or spending."""

import json
import time
from types import SimpleNamespace

import pytest

from mcbench.authorization import Authorizations
from mcbench.budgets import Budgets, DIMENSIONS
from mcbench.metering_trial import MAXIMUM, POLICY, MeteringTrials, uncertain_rows
from mcbench.native import NativeExec
from mcbench.native_conformance import PROMPT
from mcbench.storage import Database, Fault, canonical, digest
from test_authorization import install, policy
import test_native
from native_dispatch_probe import ledger, put

make_plan = test_native.make_plan

@pytest.fixture
def trial(database, cas, make_plan):
    auth = Authorizations(database)
    approved = policy()
    authority = install(auth, approved)
    NativeExec(database, cas, authorization_id=approved.authorization_id)
    budgets = auth.budgets
    limits = dict.fromkeys(DIMENSIONS, None) | {"spend_microusd": MAXIMUM, "model_calls": 1}
    budgets.create_account("old-account", limits, "c1", "a1", authority, category="development")
    old_plan, _ = make_plan("old")
    price = put(cas, approved.accounting_basis.model_dump())

    def reserve(plan, operation, parent=None):
        return ledger(plan, operation, parent=parent, calls=1, spend=MAXIMUM, pricing=price,
                      inputs=1050000, outputs=128000)

    old = reserve(old_plan, "old-envelope")
    budgets.post("old-account", old, envelope=True)
    budgets.post("old-account", reserve(old_plan, "old-request", "old-envelope"))
    for operation in ("old-envelope", "old-request"):
        budgets.hold_uncertain("old-account", operation, "synthetic missing receipt")
    job = approved.authorization_id + ":oauth-receipt-d12"
    plan, _ = make_plan("trial", job_id=job, operation_id=job+":envelope", account=job+":account", purpose="conformance",
        helper_limit=0, model="gpt-5.6-luna", provider="openai", auth_mode="chatgpt_oauth", prompt=PROMPT,
        accounting_basis_digest=approved.accounting_basis.fingerprint())
    budgets.create_account(plan.account, limits, "c1", "a1", authority, category="development")
    decision = put(cas, {"schema": "strata/MeteringTrialDecision/1", "decision_id": "D12", "policy": POLICY,
        "authorization_id": approved.authorization_id, "authorization_digest": digest(approved.model_dump()),
        "maximum_microusd": MAXIMUM, "max_requests": 1, "retained_hold_microusd": MAXIMUM,
        "combined_exposure_microusd": 2*MAXIMUM, "user_authorized": True})
    service = MeteringTrials(database)
    root = reserve(plan, plan.operation_id)

    def authorize():
        return service.install(approved.authorization_id, plan, root, decision_ref=decision,
                               cas=cas, snapshot_digest=auth.snapshot())

    def prepare():
        database.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (job, "c1", "a1", 1, "executor", None, "synthetic", canonical(plan.model_dump()).decode(), "PREPARED"))
        budgets.post(plan.account, root, envelope=True)
        database.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (job,))

    return SimpleNamespace(db=database, cas=cas, auth=auth, budgets=budgets, approved=approved, authority=authority,
        plan=plan, root=root, reserve=reserve, authorize=authorize, prepare=prepare, service=service,
        retained=uncertain_rows(database.connection, authority))


def test_one_request_preserves_original_holds_and_counts_envelope_once(trial):
    t = trial
    before = t.auth.snapshot()
    t.authorize()
    assert t.auth.snapshot() == before
    t.prepare()
    t.budgets.post(t.plan.account, t.reserve(t.plan, "new-request", t.plan.operation_id))
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == 2*MAXIMUM
    assert uncertain_rows(t.db.connection, t.authority) == t.retained
    assert t.budgets.status(t.authority)["dispatch_allowed"] is False
    t.budgets.hold_uncertain(t.plan.account, "new-request", "synthetic lost reply")
    t.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED'")
    reopened = Database(t.db.path)
    try:
        with pytest.raises(Fault, match="METERING_UNKNOWN"):
            Budgets(reopened).post(t.plan.account, t.reserve(t.plan, "retry", t.plan.operation_id))
        assert Budgets(reopened).status(t.authority)["committed_and_reserved"]["spend_microusd"] == 2*MAXIMUM
    finally:
        reopened.close()


def test_no_exception_for_other_job_or_reinstall(trial):
    t = trial
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.root, envelope=True)
    t.authorize()
    with pytest.raises(Fault, match="METERING_TRIAL_ALREADY_USED"):
        t.authorize()
    t.prepare()
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post("old-account", t.reserve(t.plan, "other-job"), envelope=True)


@pytest.mark.parametrize("case", ["expired", "old_hold_changed", "new_unknown", "wrong_model", "helper", "too_large", "second_request"])
def test_exception_fails_closed_outside_exact_single_request(trial, case):
    t = trial
    t.authorize()
    t.prepare()
    request = t.reserve(t.plan, "new-request", t.plan.operation_id)
    if case == "expired":
        body=json.loads(t.db.connection.execute("SELECT body FROM metering_trials").fetchone()[0])
        body["expires_unix"] = time.time()-1
        t.db.connection.execute("UPDATE metering_trials SET body=?", (canonical(body).decode(),))
    elif case == "old_hold_changed":
        row = dict(t.retained[1])
        value = json.loads(row["reserved"])
        value["spend_microusd"] -= 1
        t.db.connection.execute("UPDATE operations SET reserved=? WHERE id='old-request'", (canonical(value).decode(),))
    elif case == "new_unknown":
        t.budgets.hold_uncertain(t.plan.account, t.plan.operation_id, "new uncertainty")
    elif case == "wrong_model":
        request=request.model_copy(update={"model_identity":"other"})
    elif case == "helper":
        request=request.model_copy(update={"kind":"helper"})
    elif case == "too_large":
        request=request.model_copy(update={"usage":request.usage.model_copy(update={"spend_microusd":MAXIMUM+1})})
    else:
        t.budgets.post(t.plan.account, request)
        request=t.reserve(t.plan,"second-request",t.plan.operation_id)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account,request)


def test_aggregate_cap_failure_rolls_back_exception_consumption(trial):
    t = trial
    t.authorize()
    limits=json.loads(t.db.connection.execute("SELECT limits FROM accounts WHERE id=?",(t.authority,)).fetchone()[0])
    limits["spend_microusd"]=MAXIMUM*2-1
    t.db.connection.execute("UPDATE accounts SET limits=? WHERE id=?",(canonical(limits).decode(),t.authority))
    with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
        t.prepare()
    assert t.db.connection.execute("SELECT state FROM metering_trials").fetchone()[0] == "READY"
    assert t.db.connection.execute("SELECT 1 FROM operations WHERE account=?",(t.plan.account,)).fetchone() is None
    assert uncertain_rows(t.db.connection,t.authority)==t.retained
