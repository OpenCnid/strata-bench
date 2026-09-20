"""Operator execution authorization, separate from runtime qualification and billing.

No account credentials or assumed OAuth-to-USD conversion are stored here.
The $ ceiling is a single parent of development, training and evaluation, not
a fresh allowance for every child, campaign, retry, epoch or restored process.
"""

import json
from typing import Annotated, Literal

from pydantic import Field

from .budgets import DIMENSIONS, Budgets
from .contracts import Id, Positive, Strict
from .storage import canonical, digest, require


class ExecutionAuthorization(Strict):
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


class Authorizations:
    def __init__(self, database):
        self.db = database
        self.budgets = Budgets(database)
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS execution_authorizations "
                       "(id TEXT PRIMARY KEY, digest TEXT NOT NULL, body TEXT NOT NULL, "
                       "account TEXT NOT NULL UNIQUE)")

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

    def check(self, authorization_id, account, provider, auth_mode, model):
        row = self.db.connection.execute("SELECT * FROM execution_authorizations WHERE id=?",
                                         (authorization_id,)).fetchone()
        require(row is not None, "EXECUTION_AUTHORIZATION_REQUIRED")
        policy = ExecutionAuthorization.model_validate_json(row["body"])
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
        return {"authorization": json.loads(row["body"]), "account": row["account"],
                "budget": self.budgets.status(row["account"]),
                "qualification_implied": False, "pricing_conversion_implied": False}
