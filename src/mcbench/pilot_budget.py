"""Distinct one-run decisions, retaining all original costs and holds.

D18 carries continuing user approval within the original allowance. Each run
still requires its own bounded durable admission; consumed jobs cannot rearm.
The D18 entry below records the first approved run, m0-pilot-03.
"""

import json
import time

from .budgets import Budgets, vector
from .metering_trial import uncertain_rows
from .native_piloting import MAX_REQUESTS, MAX_SPEND, PURPOSE
from .storage import Principal, canonical, digest, require

AUTHORIZATION = "validation-2026-09-18"
JOB = AUTHORIZATION + ":m0-pilot-01"
POLICY = "one-pilot-retain-unknown-holds/1"
DECISIONS = {"D15": (JOB, 756858), "D16": (AUTHORIZATION + ":m0-pilot-02", 763280),
             "D18": (AUTHORIZATION + ":m0-pilot-03", 773794),
             "D18.1": (AUTHORIZATION + ":m0-pilot-04", 778471),
             "D18.2": (AUTHORIZATION + ":m0-pilot-05", 784341)}


def decision_body(db, decision_id="D15"):
    require(isinstance(decision_id, str) and decision_id in DECISIONS, "PILOT_DECISION_REQUIRED")
    job, prior = DECISIONS[decision_id]
    row = db.execute("SELECT * FROM execution_authorizations WHERE id=?", (AUTHORIZATION,)).fetchone()
    require(row is not None, "PILOT_DECISION_REQUIRED")
    totals, unknown = Budgets.totals(db, row["account"])
    require(unknown and totals["spend_microusd"] == prior, "PILOT_RETAINED_HOLDS_CHANGED")
    predecessors = {"D15": [], "D16": [JOB], "D18": [JOB, DECISIONS["D16"][0]],
                    "D18.1": [JOB, DECISIONS["D16"][0], DECISIONS["D18"][0]],
                    "D18.2": [JOB, DECISIONS["D16"][0], DECISIONS["D18"][0], DECISIONS["D18.1"][0]]}[decision_id]
    for predecessor in predecessors:
        previous = db.execute("SELECT state FROM native_jobs WHERE id=?", (predecessor,)).fetchone()
        require(previous is not None and previous[0] == "FINALIZED" and
                db.execute("SELECT count(*) FROM inference_attempts WHERE "
                    "json_extract(request,'$.runtime_job_id')=? AND state='SETTLED'", (predecessor,)).fetchone()[0] == 6,
                "PILOT_PRIOR_RUN_UNSETTLED")
    if decision_id in {"D18", "D18.1", "D18.2"}:
        from .authorization import ModelExecutionAuthorization, parse_authorization
        policy = parse_authorization(row["body"])
        require(isinstance(policy, ModelExecutionAuthorization) and policy.models == ["gpt-6-luna"] and
                policy.accounting_basis.model == "gpt-6-luna", "PILOT_MODEL_AUTHORITY")
    return {"schema": "strata/PilotBudgetDecision/1", "decision_id": decision_id, "policy": POLICY,
        "authorization_id": AUTHORIZATION, "authorization_digest": row["digest"], "job_id": job,
        "maximum_microusd": MAX_SPEND, "max_requests": MAX_REQUESTS, "hard_timeout_s": 90,
        "helper_limit": 0, "prior_exposure_microusd": prior, "combined_exposure_microusd": prior + MAX_SPEND,
        "retained_digest": digest(uncertain_rows(db, row["account"])), "user_authorized": True}


def check_decision(db, decision):
    require(isinstance(decision, dict) and decision == decision_body(db, decision.get("decision_id")),
            "PILOT_DECISION_REQUIRED")
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='pilot_trials'").fetchone():
        require(db.execute("SELECT 1 FROM pilot_trials WHERE job=?", (decision["job_id"],)).fetchone() is None,
                "PILOT_ALREADY_ATTEMPTED")


def install(database, cas, plan, reserve, decision):
    """Install once, before native intent; all ordinary budget caps still apply."""
    from .authorization import Authorizations
    auth = Authorizations(database)
    require(cas.database is database, "PILOT_DECISION_REQUIRED")
    check_decision(database.connection, decision)
    ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(decision))
    job = decision["job_id"]
    with database.transaction() as db:
        check_decision(db, decision)
        policy = auth.check(AUTHORIZATION, plan.account, plan.provider, plan.auth_mode, plan.model)
        require(plan.job_id == job and plan.account == job + ":account" and
                plan.operation_id == job + ":envelope" and plan.purpose == PURPOSE and
                plan.role == "executor" and plan.parent_job_id is None and plan.helper_limit == 0 and
                plan.hard_timeout_s <= 90 and plan.budget_mode == "per_dispatch" and
                plan.model == ("gpt-6-luna" if decision["decision_id"] in {"D18", "D18.1", "D18.2"} else "gpt-5.6-luna") and
                plan.auth_mode == "chatgpt_oauth" and
                plan.provider == "openai" and reserve.operation_id == plan.operation_id and
                reserve.parent_operation_id is None and reserve.kind == "model" and
                reserve.usage.model_calls == MAX_REQUESTS and reserve.usage.spend_microusd == MAX_SPEND and
                MAX_SPEND <= policy.first_trial_max_microusd and
                decision["combined_exposure_microusd"] <= policy.total_spend_microusd,
                "PILOT_BUDGET_SCOPE")
        require(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (job,)).fetchone() is None,
                "PILOT_ALREADY_ATTEMPTED")
        chain = Budgets.ancestors(db, plan.account)
        authority = db.execute("SELECT account FROM execution_authorizations WHERE id=?", (AUTHORIZATION,)).fetchone()[0]
        limits = json.loads(chain[0]["limits"])
        require(len(chain) == 2 and chain[1]["id"] == authority and
                limits["spend_microusd"] == MAX_SPEND and limits["model_calls"] == MAX_REQUESTS,
                "PILOT_BUDGET_SCOPE")
        body = {"decision_ref": ref, "authorization_digest": decision["authorization_digest"],
            "authority": authority, "retained_digest": decision["retained_digest"],
            "profile_digest": plan.profile_digest(), "envelope": plan.operation_id,
            "reserve_digest": digest(reserve.model_dump()), "maximum": vector(reserve),
            "basis_digest": plan.accounting_basis_digest, "expires_unix": time.time() + 600}
        db.execute("CREATE TABLE IF NOT EXISTS pilot_trials (job TEXT PRIMARY KEY, account TEXT UNIQUE NOT NULL, "
                   "body TEXT NOT NULL, state TEXT NOT NULL, requests INTEGER NOT NULL)")
        db.execute("INSERT INTO pilot_trials VALUES(?,?,?,'READY',0)", (job, plan.account, canonical(body).decode()))
        database.event(db, "pilot.budget_authorized", body)
        return body


def admit(db, account, record, *, envelope):
    """Reservation-transaction check; any additional unknown fails closed."""
    from .native import NativeLaunch
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='pilot_trials'").fetchone(), "METERING_UNKNOWN")
    row = db.execute("SELECT * FROM pilot_trials WHERE account=?", (account,)).fetchone()
    require(row is not None, "METERING_UNKNOWN")
    body = json.loads(row["body"])
    auth = db.execute("SELECT digest FROM execution_authorizations WHERE id=?", (AUTHORIZATION,)).fetchone()
    require(auth is not None and auth[0] == body["authorization_digest"] and
            time.time() < body["expires_unix"] and
            digest(uncertain_rows(db, body["authority"])) == body["retained_digest"], "METERING_UNKNOWN")
    job = db.execute("SELECT plan,state FROM native_jobs WHERE id=?", (row["job"],)).fetchone()
    require(job is not None, "METERING_UNKNOWN")
    plan = NativeLaunch.model_validate_json(job["plan"])
    require(plan.profile_digest() == body["profile_digest"] and plan.account == account and
            plan.accounting_basis_digest == body["basis_digest"] and record.kind == "model" and
            record.model_identity == plan.model, "METERING_UNKNOWN")
    amount = vector(record)
    require(all(amount[k] is not None and 0 <= amount[k] <= bound for k, bound in body["maximum"].items()),
            "METERING_UNKNOWN")
    if envelope:
        require(row["state"] == "READY" and job["state"] == "PREPARED" and
                record.operation_id == body["envelope"] and record.parent_operation_id is None and
                digest(record.model_dump()) == body["reserve_digest"], "METERING_UNKNOWN")
        db.execute("UPDATE pilot_trials SET state='ENVELOPE_RESERVED' WHERE account=?", (account,))
    else:
        children = list(db.execute("SELECT actual FROM operations WHERE parent=?", (body["envelope"],)))
        require(row["state"] == "ENVELOPE_RESERVED" and job["state"] == "RUNNING" and
                record.parent_operation_id == body["envelope"] and record.usage.model_calls == 1 and
                len(children) == row["requests"] < MAX_REQUESTS and all(c[0] is not None for c in children),
                "METERING_UNKNOWN")
        db.execute("UPDATE pilot_trials SET requests=requests+1 WHERE account=?", (account,))
