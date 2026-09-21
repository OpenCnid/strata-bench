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

from .accounting import EstimateBasis, FiniteExposure, UsageValuation
from .authorization import Authorizations
from .budgets import Budgets
from .contracts import Digest, Id, Positive, Ref, Strict
from .records import BudgetLedger
from .storage import Fault, Principal, canonical, digest, require

POLICY = "reserve-intent-before-distinct-dispatch/1"
REJECTION_POLICY = "durable-budget-denial-before-dispatch/1"
BUDGET_DENIALS = {"BUDGET_EXHAUSTED", "ENVELOPE_EXHAUSTED", "METERING_UNKNOWN"}


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


class EstimateDispatchBound(DispatchBound):
    schema_: Literal["strata/InferenceDispatchBound/2"] = Field(alias="schema")
    exposure: FiniteExposure


class PreDispatchRejection(Strict):
    schema_: Literal["strata/InferencePreDispatchRejection/1"] = Field(alias="schema")
    policy: Literal["durable-budget-denial-before-dispatch/1"]
    simulation: bool
    account: Id
    attempt: InferenceAttempt
    reservation: BudgetLedger
    reason: Literal["BUDGET_EXHAUSTED", "ENVELOPE_EXHAUSTED", "METERING_UNKNOWN"]


def rejection_event(body):
    return {"operation_id": body.reservation.operation_id, "runtime_job_id": body.attempt.runtime_job_id,
            "request_digest": body.attempt.request_digest, "reason": body.reason,
            "record_digest": digest(body.model_dump()), "policy": REJECTION_POLICY}


def verified_rejections(db, job, simulation):
    """Only explicit trusted pre-forward records prove rejection; absence does not."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='inference_rejections'").fetchone():
        return {}
    result = {}
    for row in db.execute("SELECT * FROM inference_rejections WHERE "
                          "json_extract(body,'$.attempt.runtime_job_id')=? ORDER BY operation", (job,)):
        body = PreDispatchRejection.model_validate_json(row["body"])
        op = body.reservation.operation_id
        require(body.simulation is simulation and row["operation"] == op and row["fingerprint"] == digest({
            "account": body.account, "attempt": body.attempt.model_dump(), "reserve": body.reservation.model_dump()})
            and body.reservation.posting == "reserve", "DISPATCH_REJECTION_INVALID")
        require(db.execute("SELECT 1 FROM inference_attempts WHERE operation=?", (op,)).fetchone() is None and
            db.execute("SELECT 1 FROM operations WHERE id=?", (op,)).fetchone() is None and
            db.execute("SELECT 1 FROM ledger WHERE json_extract(body,'$.operation_id')=?", (op,)).fetchone() is None,
            "DISPATCH_REJECTION_INVALID")
        events = db.execute("SELECT body FROM outbox WHERE kind='inference.rejected_before_dispatch' "
                           "AND json_extract(body,'$.operation_id')=?", (op,)).fetchall()
        require(len(events) == 1 and json.loads(events[0][0]) == rejection_event(body), "DISPATCH_REJECTION_INVALID")
        result[op] = body
    return result


def require_admission_outcomes(db, plan, simulation):
    """Every native admission must have dispatch history or a proved denial."""
    rejected = verified_rejections(db, plan.job_id, simulation)
    admissions = {r["operation"]: r for r in db.execute(
        "SELECT * FROM native_request_admissions WHERE job=?", (plan.job_id,))}
    attempts = {r[0] for r in db.execute("SELECT operation FROM inference_attempts WHERE "
        "json_extract(request,'$.runtime_job_id')=?", (plan.job_id,))}
    require(set(admissions) == attempts | set(rejected) and not attempts & set(rejected), "METERING_UNKNOWN")
    for op, body in rejected.items():
        admission, request, reserve = admissions[op], body.attempt, body.reservation
        require(body.account == plan.account and request.profile_digest == plan.profile_digest() and
            request.provider == plan.provider and request.auth_mode == plan.auth_mode and
            request.request_digest == admission["request_digest"] and
            reserve.parent_operation_id == admission["envelope"] and reserve.campaign_id == plan.campaign_id and
            reserve.agent_id == plan.agent_id and reserve.epoch == plan.epoch and reserve.model_identity == plan.model,
            "DISPATCH_REJECTION_INVALID")
    return rejected


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
            self.authorizations.require_store_mode(simulation)
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
            db.execute("CREATE TABLE IF NOT EXISTS inference_valuations "
                       "(operation TEXT PRIMARY KEY REFERENCES inference_attempts(operation), "
                       "body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS inference_exposure_faults "
                       "(operation TEXT PRIMARY KEY REFERENCES inference_attempts(operation), "
                       "profile_digest TEXT NOT NULL)")
            # Additive migration. Never backfill legacy missing attempts as zero usage.
            db.execute("CREATE TABLE IF NOT EXISTS inference_rejections "
                       "(operation TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, body TEXT NOT NULL)")

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
        bound = self._bound(attempt)
        expected = attempt.model_dump(exclude={"schema_", "bound_ref"})
        require(all(getattr(bound, k) == v for k, v in expected.items()) and
                bound.reservation_digest == digest(reserve.model_dump()) and
                bound.pricing_ref == reserve.pricing_ref and
                bound.is_example == self.simulation and
                bound.finite_dispatch_bound_verified and bound.pricing_semantics_verified and
                bound.expires_unix_ms > time.time_ns() // 1000000, "DISPATCH_BOUND_UNVERIFIED")
        price_raw = self._private_ref(bound.pricing_ref, 65536)
        if isinstance(bound, EstimateDispatchBound):
            basis = EstimateBasis.model_validate_json(price_raw)
            require(reserve.model_identity == basis.model and
                    reserve.usage.input_tokens == bound.exposure.max_input_tokens and
                    reserve.usage.output_tokens == bound.exposure.max_output_tokens and
                    reserve.usage.spend_microusd == bound.exposure.amount(basis),
                    "DISPATCH_ESTIMATE_MISMATCH")
            proof = json.loads(self._private_ref(bound.exposure.enforcement_ref, 65536))
            require(proof.get("schema") == "strata/InferenceExposureEvidence/1" and
                    proof.get("is_example") is self.simulation and
                    proof.get("profile_digest") == attempt.profile_digest and
                    proof.get("basis_digest") == basis.fingerprint() and
                    proof.get("input_bound_method") == bound.exposure.input_bound_method and
                    proof.get("output_bound_method") == bound.exposure.output_bound_method and
                    proof.get("max_input_tokens") == bound.exposure.max_input_tokens and
                    proof.get("max_output_tokens") == bound.exposure.max_output_tokens and
                    proof.get("result") == "pass", "EXPOSURE_UNQUALIFIED")
            # Smaller bounds require request-specific enforcement evidence.
            if (bound.exposure.input_bound_method != "provider_context_limit" or
                    bound.exposure.output_bound_method != "provider_model_limit"):
                require(proof.get("request_digest") == attempt.request_digest,
                        "EXPOSURE_UNQUALIFIED")
        if not self.simulation:
            policy = self.authorizations.check(self.authorization_id, account, attempt.provider,
                                              attempt.auth_mode, reserve.model_identity)
            require(isinstance(bound, EstimateDispatchBound), "VERSIONED_ESTIMATE_REQUIRED")
            require(basis == policy.accounting_basis, "ACCOUNTING_BASIS_MISMATCH")
        exists = self.db.connection.execute("SELECT name FROM sqlite_master "
                                            "WHERE name='native_jobs'").fetchone()
        job = self.db.connection.execute("SELECT plan,state,started FROM native_jobs WHERE id=?",
            (attempt.runtime_job_id,)).fetchone() if exists else None
        from .native import NativeLaunch
        plan = NativeLaunch.model_validate_json(job["plan"]) if job else None
        if not self.simulation or plan is not None and (
                plan.broker_policy is not None or plan.ingress_policy is not None):
            require(job is not None and job["state"] == "RUNNING", "RUNTIME_NOT_RUNNING")
            require(plan.profile_digest() == attempt.profile_digest and plan.account == account and
                    plan.budget_mode == "per_dispatch" and
                    plan.campaign_id == reserve.campaign_id and plan.agent_id == reserve.agent_id and
                    plan.epoch == reserve.epoch and plan.model == reserve.model_identity and
                    plan.provider == attempt.provider and plan.auth_mode == attempt.auth_mode,
                    "DISPATCH_SCOPE_MISMATCH")
            if plan.broker_policy is not None:
                require(job["started"] + plan.hard_timeout_s > time.time(), "RUNTIME_EXPIRED")
                from .native_admission import require_request_admission
                require_request_admission(self.db.connection, plan, attempt, reserve, account,
                                          cas=self.cas, simulation=self.simulation)
            else:
                require(plan.operation_id == reserve.parent_operation_id, "DISPATCH_SCOPE_MISMATCH")
            if plan.ingress_policy is not None:
                from .native_ingress import require_ingress_request
                require_ingress_request(self.db.connection, plan, reserve.operation_id, attempt.request_digest)
            if plan.gateway_config_digest is not None:
                from .native_gateway import require_gateway
                require_gateway(self.db.connection, plan, "OPEN")

    def _bound(self, attempt):
        raw = json.loads(self._private_ref(attempt.bound_ref, 16384))
        cls = (EstimateDispatchBound if raw.get("schema", raw.get("schema_")) ==
               "strata/InferenceDispatchBound/2" else DispatchBound)
        return cls.model_validate(raw)

    def _begin(self, account, attempt, reserve):
        fingerprint = digest({"account": account, "attempt": attempt.model_dump(),
                              "reserve": reserve.model_dump()})
        rejected = None
        with self.db.transaction() as db:
            old = db.execute("SELECT fingerprint FROM inference_attempts WHERE operation=?",
                             (reserve.operation_id,)).fetchone()
            if old:
                require(old[0] == fingerprint, "IDEMPOTENCY_CONFLICT")
                return False
            old = db.execute("SELECT fingerprint,body FROM inference_rejections WHERE operation=?",
                             (reserve.operation_id,)).fetchone()
            if old:
                require(old[0] == fingerprint, "IDEMPOTENCY_CONFLICT")
                raise Fault(PreDispatchRejection.model_validate_json(old[1]).reason)
            require(db.execute("SELECT 1 FROM inference_exposure_faults LIMIT 1").fetchone() is None,
                    "INFERENCE_EXPOSURE_QUARANTINED")
            self._validate_bound(account, attempt, reserve)
            db.execute("SAVEPOINT dispatch_reservation")
            try:
                require(self.budgets.post_in_transaction(db, account, reserve),
                        "DISPATCH_RESERVATION_REUSED")
            except Fault as exc:
                if exc.code not in BUDGET_DENIALS:
                    raise
                db.execute("ROLLBACK TO dispatch_reservation")
                require(db.execute("SELECT 1 FROM operations WHERE id=?", (reserve.operation_id,)).fetchone() is None,
                        "DISPATCH_REJECTION_INVALID")
                rejected = PreDispatchRejection.model_validate({"schema": "strata/InferencePreDispatchRejection/1",
                    "policy": REJECTION_POLICY, "simulation": self.simulation, "account": account,
                    "attempt": attempt, "reservation": reserve, "reason": exc.code})
                db.execute("INSERT INTO inference_rejections VALUES(?,?,?)", (
                    reserve.operation_id, fingerprint, canonical(rejected.model_dump()).decode()))
                self.db.event(db, "inference.rejected_before_dispatch", rejection_event(rejected))
            finally:
                db.execute("RELEASE dispatch_reservation")
            if rejected is None:
                db.execute("INSERT INTO inference_attempts VALUES(?,?,?,?,?,'DISPATCHING',NULL,NULL,NULL)",
                       (reserve.operation_id, account, fingerprint,
                        canonical(attempt.model_dump()).decode(),
                        canonical(reserve.model_dump()).decode()))
                self.db.event(db, "inference.dispatch_intent", {
                    "operation_id": reserve.operation_id, "runtime_job_id": attempt.runtime_job_id,
                    "request_digest": attempt.request_digest, "bound_ref": attempt.bound_ref,
                    "policy": POLICY, "simulation": self.simulation})
        if rejected is not None:
            raise Fault(rejected.reason)  # Committed denial; this operation can never forward.
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
            result = forward()
            require(isinstance(result, tuple) and len(result) in (2, 3),
                    "AUTHORITATIVE_USAGE_REQUIRED")
            provider_event_id, receipt = result[:2]
            self.settle(reserve.operation_id, provider_event_id, receipt,
                        valuation=result[2] if len(result) == 3 else None)
        except BaseException:
            self.mark_uncertain(reserve.operation_id, "transport_or_receipt_uncertain")
            raise
        return self.status(reserve.operation_id)

    def settle(self, operation, provider_event_id, receipt: BudgetLedger, *, valuation=None):
        require(isinstance(provider_event_id, str) and 0 < len(provider_event_id) <= 256 and
                not any(ord(c) < 33 for c in provider_event_id), "PROVIDER_EVENT_INVALID")
        require(isinstance(receipt, BudgetLedger) and receipt.posting == "settle" and
                receipt.metering in {"reported", "estimated"} and receipt.raw_usage_ref is not None and
                receipt.usage.spend_microusd is not None and
                receipt.usage.model_calls in (0, 1), "AUTHORITATIVE_USAGE_REQUIRED")
        self._private_ref(receipt.raw_usage_ref, 256 * 1024)
        fingerprint_body = {"provider_event_id": provider_event_id, "receipt": receipt.model_dump()}
        if valuation is not None:
            valuation = UsageValuation.model_validate(valuation)
            fingerprint_body["valuation"] = valuation.model_dump()
        fingerprint = digest(fingerprint_body)
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM inference_attempts WHERE operation=?",
                             (operation,)).fetchone()
            require(row is not None, "DISPATCH_NOT_FOUND")
            reserved = BudgetLedger.model_validate_json(row["reservation"])
            attempt = InferenceAttempt.model_validate_json(row["request"])
            bound = self._bound(attempt)
            if isinstance(bound, EstimateDispatchBound):
                basis = EstimateBasis.model_validate_json(self._private_ref(bound.pricing_ref, 65536))
                require(valuation is not None and
                        valuation.kind == "api_equivalent_estimate" and
                        valuation.basis_digest == basis.fingerprint() and
                        valuation.raw_usage_ref == receipt.raw_usage_ref and
                        valuation.token_evidence == ("synthetic_fixture" if self.simulation else
                                                      "provider_reported") and
                        valuation.amount_microusd == basis.estimate(valuation.usage) ==
                        receipt.usage.spend_microusd and receipt.metering == "estimated" and
                        receipt.usage.model_calls == 1, "USAGE_VALUATION_MISMATCH")
                require(valuation.usage.model == receipt.model_identity and all(
                    getattr(valuation.usage, k) == getattr(receipt.usage, k) for k in
                    ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")),
                    "USAGE_VALUATION_MISMATCH")
            else:
                require(valuation is None and receipt.metering == "reported" and self.simulation,
                        "VERSIONED_ESTIMATE_REQUIRED")
            fields = ("campaign_id", "agent_id", "campaign_account", "epoch", "operation_id",
                      "parent_operation_id", "kind", "pricing_ref", "model_identity")
            require(all(getattr(receipt, k) == getattr(reserved, k) for k in fields),
                    "DISPATCH_RECEIPT_SCOPE")
            if row["state"] == "SETTLED":
                require(row["receipt_digest"] == fingerprint, "IDEMPOTENCY_CONFLICT")
                return False
            event_key = digest({"provider": attempt.provider, "event": provider_event_id})
            conflict = db.execute("SELECT operation FROM inference_attempts WHERE provider_event=?",
                                  (event_key,)).fetchone()
            require(conflict is None, "PROVIDER_EVENT_REUSED")
            self.budgets.post_in_transaction(db, row["account"], receipt)
            if valuation is not None:
                db.execute("INSERT INTO inference_valuations VALUES(?,?)",
                           (operation, canonical(valuation.model_dump()).decode()))
                if (receipt.usage.input_tokens > bound.exposure.max_input_tokens or
                        receipt.usage.output_tokens > bound.exposure.max_output_tokens or
                        receipt.usage.spend_microusd > reserved.usage.spend_microusd):
                    # Preserve the full observed consumption, then revoke trust in
                    # the bound. An inexpensive overrun still invalidates exposure.
                    db.execute("INSERT INTO inference_exposure_faults VALUES(?,?)",
                               (operation, attempt.profile_digest))
                    self.db.event(db, "inference.exposure_quarantined", {
                        "operation_id": operation, "profile_digest": attempt.profile_digest})
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
        if row is None:
            row = self.db.connection.execute("SELECT body FROM inference_rejections WHERE operation=?",
                                             (operation,)).fetchone()
            require(row is not None, "DISPATCH_NOT_FOUND")
            rejected = PreDispatchRejection.model_validate_json(row[0])
            return {"operation_id": operation, "state": "REJECTED_BEFORE_DISPATCH", "reason": rejected.reason,
                    "simulation": self.simulation, "policy": REJECTION_POLICY,
                    "request_digest": rejected.attempt.request_digest, "usage_receipt": False}
        return {"operation_id": operation, "state": row["state"], "reason": row["reason"],
                "simulation": self.simulation, "policy": POLICY,
                "accounting_kind": ("synthetic_fixture_units" if self.simulation else
                                    "api_equivalent_estimate"),
                "exposure_quarantined": self.db.connection.execute(
                    "SELECT 1 FROM inference_exposure_faults LIMIT 1").fetchone() is not None,
                "request_digest": json.loads(row["request"])["request_digest"]}
