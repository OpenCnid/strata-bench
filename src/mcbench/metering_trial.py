"""D12: one bounded receipt trial alongside unchanged, explicitly retained holds.

This operator-installed exception never changes the original authorization,
settles unknown usage or permits general dispatch. Reservation consumption and
the ordinary aggregate/envelope checks share the caller's SQLite transaction.
"""

import json
import time

from .storage import Principal, canonical, digest, require

POLICY = "one-receipt-trial-retain-unknown-holds/1"
MAXIMUM = 755400


def uncertain_rows(db, authority):
    from .budgets import Budgets
    return [dict(row) for row in db.execute("SELECT * FROM operations WHERE uncertain=1 ORDER BY id")
            if authority in {r["id"] for r in Budgets.ancestors(db, row["account"])}]


class MeteringTrials:
    def __init__(self, database):
        self.db = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS metering_trials (authorization TEXT PRIMARY KEY, "
                       "job TEXT UNIQUE NOT NULL, account TEXT UNIQUE NOT NULL, body TEXT NOT NULL, "
                       "state TEXT NOT NULL, request TEXT)")

    def install(self, authorization_id, plan, reserve, *, decision_ref, cas, snapshot_digest):
        from .authorization import Authorizations
        from .budgets import Budgets, vector
        from .native_conformance import PROMPT
        auth = Authorizations(self.db)
        with self.db.transaction() as db:
            require(cas.database is self.db and db.execute(
                "SELECT 1 FROM objects WHERE namespace='operator' AND ref=? AND visibility='operator'",
                (decision_ref,)).fetchone() is not None, "METERING_TRIAL_DECISION_REQUIRED")
            policy = auth.check(authorization_id, plan.account, plan.provider, plan.auth_mode, plan.model)
            row = db.execute("SELECT * FROM execution_authorizations WHERE id=?", (authorization_id,)).fetchone()
            require(auth.snapshot() == snapshot_digest, "METERING_TRIAL_SNAPSHOT_CHANGED")
            decision = cas.json(Principal("operator", "operator"), "operator", decision_ref)
            require(decision == {"schema": "strata/MeteringTrialDecision/1", "decision_id": "D12",
                "policy": POLICY, "authorization_id": authorization_id, "authorization_digest": row["digest"],
                "maximum_microusd": MAXIMUM, "max_requests": 1,
                "retained_hold_microusd": MAXIMUM, "combined_exposure_microusd": 2 * MAXIMUM,
                "user_authorized": True}, "METERING_TRIAL_DECISION_REQUIRED")
            require(plan.job_id == authorization_id + ":oauth-receipt-d12" and
                    plan.account == plan.job_id + ":account" and plan.operation_id == plan.job_id + ":envelope" and
                    plan.purpose == "conformance" and plan.role == "executor" and plan.parent_job_id is None and
                    plan.helper_limit == 0 and plan.prompt == PROMPT and plan.auth_mode == "chatgpt_oauth" and
                    plan.model == "gpt-5.6-luna" and plan.provider == "openai" and
                    reserve.operation_id == plan.operation_id and reserve.parent_operation_id is None and
                    reserve.kind == "model" and reserve.usage.model_calls == 1 and
                    reserve.usage.spend_microusd == MAXIMUM <= policy.first_trial_max_microusd,
                    "METERING_TRIAL_SCOPE")
            require(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone() is None,
                    "METERING_TRIAL_ALREADY_USED")
            chain = Budgets.ancestors(db, plan.account)
            require(len(chain) == 2 and chain[1]["id"] == row["account"] and
                    json.loads(chain[0]["limits"])["spend_microusd"] == MAXIMUM and
                    json.loads(chain[0]["limits"])["model_calls"] == 1,
                    "METERING_TRIAL_SCOPE")
            totals, unknown = Budgets.totals(db, row["account"])
            retained = uncertain_rows(db, row["account"])
            require(unknown and retained and totals["spend_microusd"] == MAXIMUM and
                    all(v is not None for v in totals.values()) and
                    totals["spend_microusd"] + MAXIMUM <= policy.total_spend_microusd,
                    "METERING_TRIAL_RETAINED_HOLDS")
            body = {"policy": POLICY, "decision_ref": decision_ref, "authorization_digest": row["digest"],
                "authority": row["account"], "job": plan.job_id, "account": plan.account,
                "envelope": plan.operation_id, "profile_digest": plan.profile_digest(),
                "model": plan.model, "basis_digest": plan.accounting_basis_digest,
                "reserve_digest": digest(reserve.model_dump()), "maximum": vector(reserve),
                "retained_operations": retained, "retained_digest": digest(retained),
                "snapshot_digest": snapshot_digest, "expires_unix": time.time() + 600}
            require(db.execute("SELECT 1 FROM metering_trials WHERE authorization=?",
                               (authorization_id,)).fetchone() is None, "METERING_TRIAL_ALREADY_USED")
            db.execute("INSERT INTO metering_trials VALUES(?,?,?,?,'READY',NULL)",
                       (authorization_id, plan.job_id, plan.account, canonical(body).decode()))
            self.db.event(db, "metering.trial_authorized", body)
        return body


def admit_retained_unknowns(db, account, record, *, envelope):
    """Called only inside the reservation transaction. Default remains block."""
    from .budgets import vector
    from .native import NativeLaunch
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='pilot_trials'").fetchone() and db.execute(
            "SELECT 1 FROM pilot_trials WHERE account=?", (account,)).fetchone():
        from .pilot_budget import admit
        return admit(db, account, record, envelope=envelope)
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='metering_trials'").fetchone(),
            "METERING_UNKNOWN")
    row = db.execute("SELECT * FROM metering_trials WHERE account=?", (account,)).fetchone()
    require(row is not None, "METERING_UNKNOWN")
    body = json.loads(row["body"])
    authority = db.execute("SELECT * FROM execution_authorizations WHERE id=?", (row["authorization"],)).fetchone()
    require(authority is not None and authority["digest"] == body["authorization_digest"] and
            time.time() < body["expires_unix"] and
            digest(uncertain_rows(db, body["authority"])) == body["retained_digest"], "METERING_UNKNOWN")
    job = db.execute("SELECT plan,state FROM native_jobs WHERE id=?", (row["job"],)).fetchone()
    require(job is not None, "METERING_UNKNOWN")
    plan = NativeLaunch.model_validate_json(job["plan"])
    require(plan.profile_digest() == body["profile_digest"] and plan.account == account and
            plan.operation_id == body["envelope"] and record.model_identity == body["model"] and
            record.kind == "model" and record.usage.model_calls == 1 and
            plan.accounting_basis_digest == body["basis_digest"], "METERING_UNKNOWN")
    amount = vector(record)
    require(all(amount[k] is not None and 0 <= amount[k] <= bound for k, bound in body["maximum"].items()),
            "METERING_UNKNOWN")
    if envelope:
        require(row["state"] == "READY" and job["state"] == "PREPARED" and
                record.operation_id == body["envelope"] and record.parent_operation_id is None and
                digest(record.model_dump()) == body["reserve_digest"], "METERING_UNKNOWN")
        db.execute("UPDATE metering_trials SET state='ENVELOPE_RESERVED' WHERE account=?", (account,))
    else:
        require(row["state"] == "ENVELOPE_RESERVED" and job["state"] == "RUNNING" and
                record.parent_operation_id == body["envelope"], "METERING_UNKNOWN")
        db.execute("UPDATE metering_trials SET state='REQUEST_RESERVED',request=? WHERE account=?",
                   (record.operation_id, account))
