"""Operator-only per-request reservations and durable at-most-once forwarding.

This is an accounting boundary, not a provider proxy, price estimator or security
sandbox. The trusted adapter must qualify the finite bound and parse authoritative
provider receipts. No OAuth qualification is supplied by this module. Synthetic
stores are permanently marked and cannot be promoted to live use.
"""

import json
import time
from typing import Literal

from pydantic import Field

from .authorization import Authorizations
from .budgets import Budgets
from .contracts import Digest, Id, Positive, Ref, Strict
from .records import BudgetLedger
from .storage import Principal, canonical, digest, require

POLICY = "reserve-intent-before-distinct-dispatch/1"


class InferenceAttempt(Strict):
    schema_: Literal["strata/InferenceAttempt/1"] = Field(alias="schema")
    runtime_job_id: Id
    profile_digest: Digest
    provider: Id
    auth_mode: Literal["chatgpt_oauth", "api_key"]
    request_digest: Digest
    bound_ref: Ref


class DispatchBound(Strict):
    schema_: Literal["strata/InferenceDispatchBound/1"] = Field(alias="schema")
    is_example: bool
    runtime_job_id: Id
    profile_digest: Digest
    provider: Id
    auth_mode: Literal["chatgpt_oauth", "api_key"]
    request_digest: Digest
    reservation_digest: Digest
    pricing_ref: Ref
    currency: Literal["USD"]
    finite_dispatch_bound_verified: bool
    pricing_semantics_verified: bool
    expires_unix_ms: Positive


class InferenceDispatches:
    def __init__(self, database, cas, *, simulation=False, namespace="operator",
                 authorization_id=None):
        require(type(simulation) is bool, "DISPATCH_PROFILE_MISMATCH")
        require(cas.database is database, "DISPATCH_STORE_MISMATCH")
        self.db, self.cas = database, cas
        self.simulation, self.namespace = simulation, namespace
        self.authorization_id = authorization_id
        self.budgets = Budgets(database)
        self.authorizations = Authorizations(database)
        with database.transaction() as db:
            if db.execute("SELECT name FROM sqlite_master WHERE name='native_profile'").fetchone():
                native = db.execute("SELECT simulation FROM native_profile").fetchone()
                require(native is not None and bool(native[0]) == simulation,
                        "DISPATCH_PROFILE_MISMATCH")
            db.execute("CREATE TABLE IF NOT EXISTS inference_dispatch_profile "
                       "(singleton INTEGER PRIMARY KEY CHECK(singleton=1), simulation INTEGER, "
                       "policy TEXT NOT NULL)")
            row = db.execute("SELECT * FROM inference_dispatch_profile").fetchone()
            if row:
                require(bool(row["simulation"]) == simulation and row["policy"] == POLICY,
                        "DISPATCH_PROFILE_MISMATCH")
            else:
                db.execute("INSERT INTO inference_dispatch_profile VALUES(1,?,?)",
                           (int(simulation), POLICY))
            db.execute("CREATE TABLE IF NOT EXISTS inference_attempts ("
                       "operation TEXT PRIMARY KEY REFERENCES operations(id), account TEXT, "
                       "fingerprint TEXT NOT NULL, request TEXT NOT NULL, reservation TEXT NOT NULL, "
                       "state TEXT NOT NULL, receipt_digest TEXT, provider_event TEXT, reason TEXT)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS inference_provider_event "
                       "ON inference_attempts(provider_event) WHERE provider_event IS NOT NULL")

    def _private_ref(self, ref, max_bytes):
        row = self.db.connection.execute(
            "SELECT visibility FROM objects WHERE namespace=? AND ref=?",
            (self.namespace, ref)).fetchone()
        require(row is not None and row[0] == "operator", "DISPATCH_EVIDENCE_PRIVATE")
        return self.cas.read(Principal(self.namespace, "operator"), self.namespace, ref,
                             max_bytes=max_bytes)

    def _validate_bound(self, account, attempt, reserve):
        require(not reserve.is_example and reserve.posting == "reserve" and
                reserve.kind in {"model", "helper"} and reserve.usage.model_calls == 1 and
                reserve.metering != "unknown" and reserve.pricing_ref is not None and
                reserve.model_identity is not None and reserve.usage.spend_microusd is not None,
                "DISPATCH_BOUND_REQUIRED")
        bound = DispatchBound.model_validate_json(self._private_ref(attempt.bound_ref, 16384))
        expected = attempt.model_dump(exclude={"schema_", "bound_ref"})
        require(all(getattr(bound, k) == v for k, v in expected.items()) and
                bound.reservation_digest == digest(reserve.model_dump()) and
                bound.pricing_ref == reserve.pricing_ref and
                bound.is_example == self.simulation and
                bound.finite_dispatch_bound_verified and bound.pricing_semantics_verified and
                bound.expires_unix_ms > time.time_ns() // 1000000, "DISPATCH_BOUND_UNVERIFIED")
        self._private_ref(bound.pricing_ref, 65536)
        if not self.simulation:
            self.authorizations.check(self.authorization_id, account, attempt.provider,
                                      attempt.auth_mode, reserve.model_identity)
            exists = self.db.connection.execute("SELECT name FROM sqlite_master "
                                                "WHERE name='native_jobs'").fetchone()
            require(exists is not None, "RUNTIME_UNQUALIFIED")
            job = self.db.connection.execute("SELECT plan,state FROM native_jobs WHERE id=?",
                                             (attempt.runtime_job_id,)).fetchone()
            require(job is not None and job["state"] == "RUNNING", "RUNTIME_NOT_RUNNING")
            from .native import NativeLaunch
            plan = NativeLaunch.model_validate_json(job["plan"])
            require(plan.profile_digest() == attempt.profile_digest and plan.account == account and
                    plan.campaign_id == reserve.campaign_id and plan.agent_id == reserve.agent_id and
                    plan.epoch == reserve.epoch and plan.model == reserve.model_identity and
                    plan.provider == attempt.provider and plan.auth_mode == attempt.auth_mode and
                    plan.operation_id == reserve.parent_operation_id, "DISPATCH_SCOPE_MISMATCH")

    def _begin(self, account, attempt, reserve):
        fingerprint = digest({"account": account, "attempt": attempt.model_dump(),
                              "reserve": reserve.model_dump()})
        with self.db.transaction() as db:
            old = db.execute("SELECT fingerprint FROM inference_attempts WHERE operation=?",
                             (reserve.operation_id,)).fetchone()
            if old:
                require(old[0] == fingerprint, "IDEMPOTENCY_CONFLICT")
                return False
            self._validate_bound(account, attempt, reserve)
            require(self.budgets.post_in_transaction(db, account, reserve),
                    "DISPATCH_RESERVATION_REUSED")
            db.execute("INSERT INTO inference_attempts VALUES(?,?,?,?,?,'DISPATCHING',NULL,NULL,NULL)",
                       (reserve.operation_id, account, fingerprint,
                        canonical(attempt.model_dump()).decode(),
                        canonical(reserve.model_dump()).decode()))
            self.db.event(db, "inference.dispatch_intent", {
                "operation_id": reserve.operation_id, "runtime_job_id": attempt.runtime_job_id,
                "request_digest": attempt.request_digest, "bound_ref": attempt.bound_ref,
                "policy": POLICY, "simulation": self.simulation})
        return True  # Only this first caller may forward, after the durable commit.

    def execute(self, account, attempt: InferenceAttempt, reserve: BudgetLedger, forward):
        """The callback forwards once and returns (provider event ID, settlement).

        It must not retry internally: every actual retry requires a new operation
        and reservation. Streaming adapters return only after authoritative usage.
        Any exception retains the full reservation and blocks further dispatch.
        """
        require(callable(forward), "DISPATCH_TRANSPORT_REQUIRED")
        if not self._begin(account, attempt, reserve):
            return self.status(reserve.operation_id)
        try:
            provider_event_id, receipt = forward()
            self.settle(reserve.operation_id, provider_event_id, receipt)
        except BaseException:
            self.mark_uncertain(reserve.operation_id, "transport_or_receipt_uncertain")
            raise
        return self.status(reserve.operation_id)

    def settle(self, operation, provider_event_id, receipt: BudgetLedger):
        require(isinstance(provider_event_id, str) and 0 < len(provider_event_id) <= 256 and
                not any(ord(c) < 33 for c in provider_event_id), "PROVIDER_EVENT_INVALID")
        require(isinstance(receipt, BudgetLedger) and receipt.posting == "settle" and
                receipt.metering == "reported" and receipt.raw_usage_ref is not None and
                receipt.usage.spend_microusd is not None and
                receipt.usage.model_calls in (0, 1), "AUTHORITATIVE_USAGE_REQUIRED")
        self._private_ref(receipt.raw_usage_ref, 256 * 1024)
        fingerprint = digest({"provider_event_id": provider_event_id,
                              "receipt": receipt.model_dump()})
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM inference_attempts WHERE operation=?",
                             (operation,)).fetchone()
            require(row is not None, "DISPATCH_NOT_FOUND")
            reserved = BudgetLedger.model_validate_json(row["reservation"])
            fields = ("campaign_id", "agent_id", "campaign_account", "epoch", "operation_id",
                      "parent_operation_id", "kind", "pricing_ref", "model_identity")
            require(all(getattr(receipt, k) == getattr(reserved, k) for k in fields),
                    "DISPATCH_RECEIPT_SCOPE")
            if row["state"] == "SETTLED":
                require(row["receipt_digest"] == fingerprint, "IDEMPOTENCY_CONFLICT")
                return False
            attempt = InferenceAttempt.model_validate_json(row["request"])
            event_key = digest({"provider": attempt.provider, "event": provider_event_id})
            conflict = db.execute("SELECT operation FROM inference_attempts WHERE provider_event=?",
                                  (event_key,)).fetchone()
            require(conflict is None, "PROVIDER_EVENT_REUSED")
            self.budgets.post_in_transaction(db, row["account"], receipt)
            db.execute("UPDATE inference_attempts SET state='SETTLED',receipt_digest=?,"
                       "provider_event=?,reason=NULL WHERE operation=?",
                       (fingerprint, event_key, operation))
            self.db.event(db, "inference.settled", {"operation_id": operation,
                "provider_event_digest": event_key, "receipt_digest": fingerprint})
        return True

    def mark_uncertain(self, operation, reason):
        require(reason in {"transport_or_receipt_uncertain", "supervisor_state_loss"},
                "INVALID_REASON")
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM inference_attempts WHERE operation=?",
                             (operation,)).fetchone()
            require(row is not None, "DISPATCH_NOT_FOUND")
            if row["state"] != "DISPATCHING":
                return False
            db.execute("UPDATE operations SET uncertain=1 WHERE id=? AND actual IS NULL", (operation,))
            db.execute("UPDATE inference_attempts SET state='UNSETTLED',reason=? WHERE operation=?",
                       (reason, operation))
            self.db.event(db, "inference.unsettled", {"operation_id": operation, "reason": reason})
        return True

    def recover(self):
        """Use only after the supervisor has fenced/stopped the prior transports."""
        pending = [r[0] for r in self.db.connection.execute(
            "SELECT operation FROM inference_attempts WHERE state='DISPATCHING'")]
        for operation in pending:
            self.mark_uncertain(operation, "supervisor_state_loss")
        return pending

    def status(self, operation):
        row = self.db.connection.execute("SELECT * FROM inference_attempts WHERE operation=?",
                                         (operation,)).fetchone()
        require(row is not None, "DISPATCH_NOT_FOUND")
        return {"operation_id": operation, "state": row["state"], "reason": row["reason"],
                "simulation": self.simulation, "policy": POLICY,
                "request_digest": json.loads(row["request"])["request_digest"]}
