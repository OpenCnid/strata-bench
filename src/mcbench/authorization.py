"""Operator execution authorization, separate from runtime qualification and billing.

No account credentials or assumed OAuth-to-USD conversion are stored here.
The $ ceiling is a single parent of development, training and evaluation, not
a fresh allowance for every child, campaign, retry, epoch or restored process.
"""

import json
from typing import Annotated, Literal

from pydantic import Field

from .accounting import EstimateBasis
from .budgets import DIMENSIONS, Budgets
from .contracts import Digest, Id, Positive, Ref, Strict
from .storage import canonical, digest, require


class LegacyExecutionAuthorization(Strict):
    schema_: Literal["strata/ExecutionAuthorization/1"] = Field(alias="schema")
    authorization_id: Id
    decision_id: Id
    provider: Literal["openai"]
    auth_mode: Literal["chatgpt_oauth", "api_key"]
    models: Annotated[list[str], Field(min_length=1)]
    total_spend_microusd: Positive
    currency: Literal["USD"]
    scope: Literal["live_validation"]
    includes: list[Literal["development", "training", "evaluation"]]
    unknown_metering: Literal["block"]


class ExecutionAuthorization(LegacyExecutionAuthorization):
    schema_: Literal["strata/ExecutionAuthorization/2"] = Field(alias="schema")
    decision_id: Literal["D11"]
    original_decision_id: Literal["D04"]
    legacy_authorization_digest: Digest
    accounting_basis: EstimateBasis
    first_trial_max_microusd: Positive


class MigrationAudit(Strict):
    schema_: Literal["strata/AuthorizationMigrationAudit/1"] = Field(alias="schema")
    authorization_id: Id
    decision_id: Literal["D11"]
    source_authorization_digest: Digest
    snapshot_digest: Digest
    store_path_digest: Digest
    legacy_amount_semantics: Literal["actual_charge", "api_equivalent_estimate",
                                     "unknown_conservative"]
    external_inventory_ref: Ref
    decision_ref: Ref
    policy: Literal["preserve_all_accounts_operations_receipts_and_holds/1"]


def parse_authorization(raw):
    body = json.loads(raw) if isinstance(raw, str) else raw
    cls = (ExecutionAuthorization if body.get("schema", body.get("schema_")) ==
           "strata/ExecutionAuthorization/2" else LegacyExecutionAuthorization)
    return cls.model_validate(body)


class Authorizations:
    def __init__(self, database):
        self.db = database
        self.budgets = Budgets(database)
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS execution_authorizations "
                       "(id TEXT PRIMARY KEY, digest TEXT NOT NULL, body TEXT NOT NULL, "
                       "account TEXT NOT NULL UNIQUE)")
            db.execute("CREATE TABLE IF NOT EXISTS authorization_migrations "
                       "(id TEXT PRIMARY KEY, source_digest TEXT NOT NULL, "
                       "snapshot_digest TEXT NOT NULL, evidence_ref TEXT NOT NULL, "
                       "legacy_amount_semantics TEXT NOT NULL, target_digest TEXT NOT NULL)")

    def require_store_mode(self, simulation):
        if simulation:
            require(self.db.connection.execute(
                "SELECT 1 FROM authorization_migrations LIMIT 1").fetchone() is None,
                "SIMULATION_AUTHORITY_MIX")

    def install(self, authorization: ExecutionAuthorization):
        require(set(authorization.includes) == {"development", "training", "evaluation"} and
                len(authorization.includes) == 3, "INCOMPLETE_BUDGET_SCOPE")
        require(len(set(authorization.models)) == len(authorization.models), "MODEL_POLICY")
        account = "authorization:" + authorization.authorization_id
        body = authorization.model_dump()
        # Same transaction for cap and authorization: no partially uncapped allowance.
        with self.db.transaction() as db:
            prior = db.execute("SELECT * FROM execution_authorizations WHERE id=?",
                               (authorization.authorization_id,)).fetchone()
            if prior:
                require(prior["digest"] == digest(body), "AUTHORIZATION_CONFLICT")
                return prior["account"]
            require(isinstance(authorization, LegacyExecutionAuthorization) and
                    not isinstance(authorization, ExecutionAuthorization),
                    "EXPLICIT_AUTHORIZATION_MIGRATION_REQUIRED")
            require(db.execute("SELECT id FROM accounts WHERE id=?", (account,)).fetchone() is None,
                    "BUDGET_ACCOUNT_CONFLICT")
            limits = dict.fromkeys(DIMENSIONS, None)
            limits["spend_microusd"] = authorization.total_spend_microusd
            db.execute("INSERT INTO accounts VALUES(?,NULL,'*',NULL,?,NULL)",
                       (account, canonical(limits).decode()))
            db.execute("INSERT INTO execution_authorizations VALUES(?,?,?,?)",
                       (authorization.authorization_id, digest(body), canonical(body).decode(), account))
            self.db.event(db, "execution.authorized", {"authorization": body, "account": account})
        return account

    def snapshot(self):
        """Fingerprint every accounting row, including unknowns and orphaned holds.

        Taking a snapshot is read-only. Migration rechecks it under the writer
        lock so concurrent consumption cannot be lost or relabeled unnoticed.
        """
        db = self.db.connection
        tables = ("accounts", "operations", "ledger", "budget_envelopes")
        return digest({t: sorted((dict(r) for r in db.execute("SELECT * FROM " + t)),
                                key=lambda r: canonical(r)) for t in tables})

    def migrate(self, authorization: ExecutionAuthorization, *, snapshot_digest,
                evidence_ref, legacy_amount_semantics, cas):
        require(isinstance(authorization, ExecutionAuthorization), "MIGRATION_TARGET_REQUIRED")
        require(legacy_amount_semantics in {"actual_charge", "api_equivalent_estimate",
                                           "unknown_conservative"}, "MIGRATION_SEMANTICS")
        # Evidence is an operator audit, not a qualification or an invoice.
        require(cas.database is self.db, "DISPATCH_STORE_MISMATCH")
        row = self.db.connection.execute(
            "SELECT visibility FROM objects WHERE namespace='operator' AND ref=?",
            (evidence_ref,)).fetchone()
        require(row is not None and row[0] == "operator", "MIGRATION_EVIDENCE_REQUIRED")
        from .storage import Principal
        audit = MigrationAudit.model_validate_json(cas.read(
            Principal("operator", "operator"), "operator", evidence_ref, max_bytes=256*1024))
        require(audit.authorization_id == authorization.authorization_id and
                audit.source_authorization_digest == authorization.legacy_authorization_digest and
                audit.snapshot_digest == snapshot_digest and
                audit.store_path_digest == digest(str(self.db.path)) and
                audit.legacy_amount_semantics == legacy_amount_semantics,
                "MIGRATION_AUDIT_MISMATCH")
        for ref in (audit.external_inventory_ref, audit.decision_ref):
            row = self.db.connection.execute(
                "SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (ref,)
            ).fetchone()
            require(row is not None and row[0] == "operator", "MIGRATION_EVIDENCE_REQUIRED")
            cas.read(Principal("operator", "operator"), "operator", ref, max_bytes=256*1024)
        with self.db.transaction() as db:
            target = digest(authorization.model_dump())
            old_migration = db.execute("SELECT * FROM authorization_migrations WHERE id=?",
                                      (authorization.authorization_id,)).fetchone()
            if old_migration:
                require(old_migration["target_digest"] == target and
                        old_migration["snapshot_digest"] == snapshot_digest and
                        old_migration["evidence_ref"] == evidence_ref and
                        old_migration["legacy_amount_semantics"] == legacy_amount_semantics,
                        "MIGRATION_CONFLICT")
                return "authorization:" + authorization.authorization_id
            for table in ("native_profile", "inference_dispatch_profile", "controller_profile",
                          "provisioning_profile"):
                if db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                    row = db.execute("SELECT simulation FROM " + table).fetchone()
                    require(row is None or not row[0], "SIMULATION_STORE")
            prior = db.execute("SELECT * FROM execution_authorizations WHERE id=?",
                               (authorization.authorization_id,)).fetchone()
            require(prior is not None, "LEGACY_AUTHORIZATION_REQUIRED")
            legacy = LegacyExecutionAuthorization.model_validate_json(prior["body"])
            require(prior["digest"] == authorization.legacy_authorization_digest ==
                    digest(legacy.model_dump()), "MIGRATION_SOURCE_MISMATCH")
            # D11 changes meaning, never amount, model, scope, provider or lineage.
            for name in LegacyExecutionAuthorization.model_fields:
                if name not in {"schema_", "decision_id"}:
                    require(getattr(authorization, name) == getattr(legacy, name),
                            "MIGRATION_AUTHORITY_MISMATCH")
            require(legacy.decision_id == authorization.original_decision_id and
                    authorization.auth_mode == "chatgpt_oauth" and
                    authorization.models == [authorization.accounting_basis.model] and
                    0 < authorization.first_trial_max_microusd <= min(
                        1_000_000, authorization.total_spend_microusd), "MIGRATION_AUTHORITY_MISMATCH")
            require(self.snapshot() == snapshot_digest, "MIGRATION_SNAPSHOT_CHANGED")
            limits = json.loads(db.execute("SELECT limits FROM accounts WHERE id=?",
                                           (prior["account"],)).fetchone()[0])
            require(limits["spend_microusd"] == legacy.total_spend_microusd,
                    "MIGRATION_AUTHORITY_MISMATCH")
            db.execute("INSERT INTO authorization_migrations VALUES(?,?,?,?,?,?)",
                       (authorization.authorization_id, prior["digest"], snapshot_digest,
                        evidence_ref, legacy_amount_semantics, target))
            body = authorization.model_dump()
            db.execute("UPDATE execution_authorizations SET digest=?,body=? WHERE id=?",
                       (target, canonical(body).decode(), authorization.authorization_id))
            self.db.event(db, "execution.authorization_migrated", {
                "schema": "strata/AuthorizationMigration/1", "authorization": body,
                "legacy_authorization": legacy.model_dump(), "snapshot_digest": snapshot_digest,
                "evidence_ref": evidence_ref, "legacy_amount_semantics": legacy_amount_semantics,
                "policy": "preserve_all_accounts_operations_receipts_and_holds/1"})
            require(self.snapshot() == snapshot_digest, "MIGRATION_ACCOUNTING_CHANGED")
        return prior["account"]

    def check(self, authorization_id, account, provider, auth_mode, model):
        row = self.db.connection.execute("SELECT * FROM execution_authorizations WHERE id=?",
                                         (authorization_id,)).fetchone()
        require(row is not None, "EXECUTION_AUTHORIZATION_REQUIRED")
        policy = parse_authorization(row["body"])
        require(isinstance(policy, ExecutionAuthorization), "LEGACY_ACCOUNTING_UNMIGRATED")
        require(policy.provider == provider and policy.auth_mode == auth_mode and model in policy.models,
                "UNAUTHORIZED_MODEL_OR_PROVIDER")
        ancestors = self.budgets.ancestors(self.db.connection, account)
        require(row["account"] in {r["id"] for r in ancestors} and
                ancestors[0]["category"] in policy.includes, "UNAUTHORIZED_BUDGET_ACCOUNT")
        return policy

    def status(self, authorization_id):
        row = self.db.connection.execute("SELECT * FROM execution_authorizations WHERE id=?",
                                         (authorization_id,)).fetchone()
        require(row is not None, "EXECUTION_AUTHORIZATION_REQUIRED")
        policy = parse_authorization(row["body"])
        return {"authorization": policy.model_dump(by_alias=True), "account": row["account"],
                "budget": self.budgets.status(row["account"]),
                "accounting_kind": (policy.accounting_basis.kind if isinstance(
                    policy, ExecutionAuthorization) else "legacy_unclassified"),
                "legacy_migration": (dict(r) if (r := self.db.connection.execute(
                    "SELECT * FROM authorization_migrations WHERE id=?",
                    (authorization_id,)).fetchone()) else None),
                "qualification_implied": False, "actual_charge_implied": False,
                "pricing_conversion_implied": False}
