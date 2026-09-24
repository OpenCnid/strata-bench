"""Bounded D18 admissions with synthetic continuing approval; no real dispatch."""
import pytest
import time

from mcbench.budgets import DIMENSIONS
from mcbench.pilot_budget import DECISIONS, decision_body, decision_job, install
from mcbench.storage import Fault, canonical
from native_dispatch_probe import ledger, put
import test_pilot_budget as prior
import test_model_selection as selection

trial, make_plan, pilot_trial, corrected_trial = prior.trial, prior.make_plan, prior.pilot_trial, prior.corrected_trial


@pytest.fixture(params=["D18", "D18.1", "D18.2", "D18.3", "D18.4"])
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
    for predecessor, cost in [("D18", 4677), ("D18.1", 5870), ("D18.2", 5567), ("D18.3", 5651)]:
        if predecessor == request.param:
            break
        amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": cost, "model_calls": 6}
        db.execute("INSERT INTO operations VALUES(?,'old-account',NULL,'model',?,?,0)",
                   ("settled-"+predecessor.lower(), canonical(amount).decode(), canonical(amount).decode()))
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (DECISIONS[predecessor][0], "c1", "a1", 1, "executor", None, "synthetic", "{}", "FINALIZED"))
        db.executemany("INSERT INTO inference_attempts VALUES(?,'SETTLED')",
                      [(canonical({"runtime_job_id": DECISIONS[predecessor][0]}).decode(),)] * 6)
    job = DECISIONS[request.param][0]
    calls = 12 if request.param == "D18.4" else 6
    t.plan = t.plan.model_copy(update={"job_id": job, "account": job+":account", "operation_id": job+":envelope",
        "model": "gpt-6-luna", "accounting_basis_digest": policy.accounting_basis.fingerprint()})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": 1000000, "model_calls": calls}, "c1", "a1", t.authority, category="development")
    price = put(t.cas, policy.accounting_basis.model_dump())
    t.root = t.root.model_copy(update={"operation_id": t.plan.operation_id, "model_identity": t.plan.model,
        "pricing_ref": price, "usage": t.root.usage.model_copy(update={"model_calls": calls,
            "input_tokens": 1050000*calls, "output_tokens": 128000*calls})})
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


def test_luna6_settled_calls_preserve_all_prior_costs_and_unknowns(luna6):
    t = luna6
    expected = {"D18": 1773794, "D18.1": 1778471, "D18.2": 1784341,
                "D18.3": 1789908, "D18.4": 1795559}[t.decision["decision_id"]]
    assert t.decision["combined_exposure_microusd"] == expected
    t.authorize()
    t.db.connection.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (t.plan.job_id, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "PREPARED"))
    t.budgets.post(t.plan.account, t.root, envelope=True)
    t.db.connection.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (t.plan.job_id,))
    for i in range(t.decision["max_requests"]):
        r = t.reserve(f"luna6-{i}")
        t.budgets.post(t.plan.account, r)
        prior.settle(t, r)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.reserve("over-limit"))
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
@pytest.mark.parametrize("luna6", ["D18.1", "D18.2", "D18.3", "D18.4"], indirect=True)
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


@pytest.fixture
def retained_pilot(luna6):
    t = luna6
    db = t.db.connection
    t.authorize()
    db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (t.plan.job_id, "c1", "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "PREPARED"))
    t.budgets.post(t.plan.account, t.root, envelope=True)
    db.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (t.plan.job_id,))
    for i in range(4):
        r = t.reserve(f"before-failure-{i}")
        t.budgets.post(t.plan.account, r)
        prior.settle(t, r)
    r = t.reserve("unknown-fifth")
    t.budgets.post(t.plan.account, r)
    t.budgets.hold_uncertain(t.plan.account, r.operation_id, "fixture truncated response")
    t.budgets.hold_uncertain(t.plan.account, t.plan.operation_id, "fixture incomplete job")
    db.execute("UPDATE native_jobs SET state='UNSETTLED' WHERE id=?", (t.plan.job_id,))
    db.execute("UPDATE native_jobs SET ended=?", (time.time(),))
    db.execute("CREATE TABLE native_gateways (job TEXT PRIMARY KEY,state TEXT,fence_ref TEXT)")
    db.execute("INSERT INTO native_gateways SELECT id,'CLOSED','fixture-fence' FROM native_jobs")
    t.retained_all = prior.uncertain_rows(db, t.authority)
    t.decision = decision_body(db, "D19.1")
    job = decision_job("D19.1")
    t.plan = t.plan.model_copy(update={"job_id": job, "account": job+":account", "operation_id": job+":envelope",
                                     "campaign_id": "fresh-d19-campaign"})
    t.budgets.create_account(t.plan.account, dict.fromkeys(DIMENSIONS, None) |
        {"spend_microusd": 1000000, "model_calls": 12}, t.plan.campaign_id, "a1", t.authority, category="development")
    t.root = t.root.model_copy(update={"operation_id": t.plan.operation_id,
        "source_event_id": job+":reserve", "ledger_id": job+":ledger", "campaign_id": t.plan.campaign_id})
    return t


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
def test_d19_retains_full_failed_envelope_and_stops_new_unknown(retained_pilot):
    t = retained_pilot
    assert t.decision["prior_exposure_microusd"] == 1795559
    assert t.decision["combined_exposure_microusd"] == 2795559
    t.authorize()
    db = t.db.connection
    db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
        (t.plan.job_id, t.plan.campaign_id, "a1", 1, "executor", None, "synthetic", canonical(t.plan.model_dump()).decode(), "PREPARED"))
    t.budgets.post(t.plan.account, t.root, envelope=True)
    db.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (t.plan.job_id,))
    r = t.reserve("new-d19-first")
    t.budgets.post(t.plan.account, r)
    assert prior.uncertain_rows(db, t.authority) == t.retained_all
    assert t.budgets.status(t.authority)["committed_and_reserved"]["spend_microusd"] == 2795559
    t.budgets.hold_uncertain(t.plan.account, r.operation_id, "fixture second truncation")
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        t.budgets.post(t.plan.account, t.reserve("new-d19-second"))
    with pytest.raises(Fault, match="PILOT_PRIOR_RUN_UNSETTLED"):
        decision_body(db, "D19.2")


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
@pytest.mark.parametrize("change", ["running", "unfenced", "changed-hold", "overspend", "replay", "skip"])
def test_d19_rejects_unfenced_stale_overbudget_and_reused_admission(retained_pilot, change):
    t = retained_pilot
    db = t.db.connection
    if change == "running":
        db.execute("UPDATE native_jobs SET state='RUNNING' WHERE id=?", (DECISIONS["D18.4"][0],))
    elif change == "unfenced":
        db.execute("UPDATE native_gateways SET state='OPEN' WHERE job=?", (DECISIONS["D18.4"][0],))
    elif change == "changed-hold":
        db.execute("UPDATE operations SET uncertain=0 WHERE id='old-request'")
    elif change == "overspend":
        amount = dict.fromkeys(DIMENSIONS, 0) | {"spend_microusd": 9000000}
        db.execute("INSERT INTO operations VALUES('outside-cost','old-account',NULL,'model',?,?,0)",
                   (canonical(amount).decode(), canonical(amount).decode()))
    elif change == "replay":
        t.authorize()
    else:
        t.decision = t.decision | {"decision_id": "D19.2"}
    with pytest.raises(Fault, match="PILOT_PRIOR_RUN_UNSETTLED|PILOT_PRIOR_RUN_UNFENCED|PILOT_DECISION_REQUIRED|ALLOWANCE_UNAVAILABLE|PILOT_ALREADY_ATTEMPTED"):
        t.authorize()
    if change != "changed-hold":
        assert prior.uncertain_rows(db, t.authority) == t.retained_all


@pytest.mark.parametrize("luna6", ["D18.4"], indirect=True)
def test_longer_successor_keeps_legacy_bounds_and_requires_own_decision(retained_pilot):
    t = retained_pilot
    assert t.decision["hard_timeout_s"] == 90
    t.plan = t.plan.model_copy(update={"hard_timeout_s": 180})
    with pytest.raises(Fault, match="PILOT_BUDGET_SCOPE"):
        t.authorize()
    db = t.db.connection
    for decision_id in ("D19.1", "D19.2"):
        assert decision_body(db, decision_id)["hard_timeout_s"] == 90
        job = decision_job(decision_id)
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,?,NULL,NULL)",
            (job, "fixture", "a1", 1, "executor", None, "synthetic", "{}", "FINALIZED", time.time()))
        db.execute("INSERT INTO native_gateways VALUES(?,'CLOSED','fixture-fence')", (job,))
    decision = decision_body(db, "D19.3")
    assert decision["hard_timeout_s"] == 180 and decision["max_requests"] == 12
    assert decision["prior_exposure_microusd"] == t.decision["prior_exposure_microusd"]
    assert prior.uncertain_rows(db, t.authority) == t.retained_all
