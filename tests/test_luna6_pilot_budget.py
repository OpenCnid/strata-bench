"""Bounded D18 admissions with synthetic continuing approval; no real dispatch."""
import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.pilot_budget import DECISIONS, decision_body, install
from mcbench.storage import Fault, canonical
from native_dispatch_probe import ledger, put
import test_pilot_budget as prior
import test_model_selection as selection

trial, make_plan, pilot_trial, corrected_trial = prior.trial, prior.make_plan, prior.pilot_trial, prior.corrected_trial


@pytest.fixture(params=["D18", "D18.1", "D18.2"])
def luna6(corrected_trial, request):
    t = corrected_trial
    db = t.db.connection
    amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 10514, "model_calls": 6}
    db.execute("INSERT INTO operations VALUES('settled-d16','old-account',NULL,'model',?,?,0)",
               (canonical(amount).decode(), canonical(amount).decode()))
    db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (t.plan.job_id, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "FINALIZED"))
    db.executemany("INSERT INTO inference_attempts VALUES(?,'SETTLED')",
                  [(canonical({"runtime_job_id": t.plan.job_id}).decode(),)] * 6)
    policy = selection.selection()
    selection.apply(t, policy)
    if request.param in {"D18.1", "D18.2"}:
        amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 4677, "model_calls": 6}
        db.execute("INSERT INTO operations VALUES('settled-d18','old-account',NULL,'model',?,?,0)",
                   (canonical(amount).decode(), canonical(amount).decode()))
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (DECISIONS["D18"][0], "c1", "a1", 1, "executor", None, "synthetic", "{}", "FINALIZED"))
        db.executemany("INSERT INTO inference_attempts VALUES(?,'SETTLED')",
                      [(canonical({"runtime_job_id": DECISIONS["D18"][0]}).decode(),)] * 6)
    if request.param == "D18.2":
        amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 5870, "model_calls": 6}
        db.execute("INSERT INTO operations VALUES('settled-d18.1','old-account',NULL,'model',?,?,0)",
                   (canonical(amount).decode(), canonical(amount).decode()))
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (DECISIONS["D18.1"][0], "c1", "a1", 1, "executor", None, "synthetic", "{}", "FINALIZED"))
        db.executemany("INSERT INTO inference_attempts VALUES(?,'SETTLED')",
                      [(canonical({"runtime_job_id": DECISIONS["D18.1"][0]}).decode(),)] * 6)
    job = DECISIONS[request.param][0]
    t.plan = t.plan.model_copy(update={"job_id": job, "account": job+":account", "operation_id": job+":envelope",
        "model": "gpt-6-luna", "accounting_basis_digest": policy.accounting_basis.fingerprint()})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": 1000000, "model_calls": 6}, "c1", "a1", t.authority, category="development")
    price = put(t.cas, policy.accounting_basis.model_dump())
    t.root = t.root.model_copy(update={"operation_id": t.plan.operation_id, "model_identity": t.plan.model,
                                     "pricing_ref": price})
    t.decision = decision_body(db, request.param)
    t.reserve = lambda operation: ledger(t.plan, operation, parent=t.plan.operation_id, calls=1,
        spend=358500, pricing=price, inputs=1050000, outputs=128000)
    return t


def test_proposal_cannot_admit_without_explicit_approval(luna6):
    t = luna6
    before = t.auth.snapshot()
    with pytest.raises(Fault, match="PILOT_DECISION_REQUIRED"):
        install(t.db, t.cas, t.plan, t.root, t.decision | {"user_authorized": False})
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.root, envelope=True)
    assert t.auth.snapshot() == before


def test_luna6_six_settled_calls_preserve_all_prior_costs_and_unknowns(luna6):
    t = luna6
    expected = {"D18": 1773794, "D18.1": 1778471, "D18.2": 1784341}[t.decision["decision_id"]]
    assert t.decision["combined_exposure_microusd"] == expected
    t.authorize()
    t.db.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (t.plan.job_id, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "PREPARED"))
    t.budgets.post(t.plan.account, t.root, envelope=True)
    t.db.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (t.plan.job_id,))
    for i in range(6):
        r = t.reserve(f"luna6-{i}")
        t.budgets.post(t.plan.account, r)
        prior.settle(t, r)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.reserve("seventh"))
    assert prior.uncertain_rows(t.db.connection, t.authority) == t.retained
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == expected
    with pytest.raises(Fault, match="PILOT_RETAINED_HOLDS_CHANGED"):
        t.authorize()


@pytest.mark.parametrize("change", ["prior-running", "prior-unsettled", "wrong-model", "wrong-job", "new-cost", "helpers"])
def test_luna6_proposal_cannot_expand_or_forget_history(luna6, change):
    t = luna6
    if change == "prior-running":
        t.db.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (DECISIONS["D16"][0],))
    elif change == "prior-unsettled":
        t.db.connection.execute("UPDATE inference_attempts SET state='UNKNOWN' WHERE rowid=7")
    elif change == "new-cost":
        t.db.connection.execute("DELETE FROM operations WHERE id='settled-d16'")
    elif change == "wrong-model":
        t.plan = t.plan.model_copy(update={"model": "gpt-5.6-luna"})
    elif change == "wrong-job":
        t.plan = t.plan.model_copy(update={"job_id": DECISIONS["D16"][0]})
    else:
        t.plan = t.plan.model_copy(update={"helper_limit": 1})
    with pytest.raises(Fault, match="PILOT_PRIOR_RUN_UNSETTLED|PILOT_RETAINED_HOLDS_CHANGED|PILOT_BUDGET_SCOPE|UNAUTHORIZED_MODEL_OR_PROVIDER"):
        t.authorize()
    assert prior.uncertain_rows(t.db.connection, t.authority) == t.retained


@pytest.mark.parametrize("change", ["running", "unsettled", "cost-removed"])
@pytest.mark.parametrize("luna6", ["D18.1", "D18.2"], indirect=True)
def test_continuing_approval_cannot_forget_first_luna_run(luna6, change):
    t = luna6
    if change == "running":
        t.db.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (DECISIONS["D18"][0],))
    elif change == "unsettled":
        t.db.connection.execute("UPDATE inference_attempts SET state='UNKNOWN' WHERE json_extract(request,'$.runtime_job_id')=?",
                                (DECISIONS["D18"][0],))
    else:
        t.db.connection.execute("DELETE FROM operations WHERE id='settled-d18'")
    with pytest.raises(Fault, match="PILOT_PRIOR_RUN_UNSETTLED|PILOT_RETAINED_HOLDS_CHANGED"):
        t.authorize()
