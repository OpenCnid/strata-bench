"""Transactional hierarchical reservations and immutable usage receipts.

The caller must bound uncancellable work before dispatch. Unknown costs block
further dispatch; observed overruns are retained, never rejected or truncated.
Campaign active time is measured separately, never summed from model latencies.
"""

import json

from .records import BudgetLedger
from .storage import Database, canonical, digest, require

DIMENSIONS = ("input_tokens", "output_tokens", "model_calls", "primitive_events", "avatar_ticks",
              "spend_microusd", "practice_world_ms")


def vector(record):
    usage = record.usage.model_dump()
    return {k: usage.get(k, usage["wall_ms"] if record.kind == "practice" else 0)
            for k in DIMENSIONS}


class Budgets:
    def __init__(self, database: Database):
        self.database = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, parent TEXT "
                       "REFERENCES accounts(id), campaign TEXT, agent TEXT, limits TEXT NOT NULL, "
                       "category TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, account TEXT "
                       "REFERENCES accounts(id), parent TEXT REFERENCES operations(id), kind TEXT, "
                       "reserved TEXT NOT NULL, actual TEXT, uncertain INTEGER NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS ledger (campaign TEXT, source TEXT, digest TEXT, "
                       "body TEXT, PRIMARY KEY(campaign,source))")
            db.execute("CREATE TABLE IF NOT EXISTS budget_envelopes (operation TEXT PRIMARY KEY "
                       "REFERENCES operations(id))")

    def create_account(self, name, limits, campaign, agent=None, parent=None, *, category=None):
        require(set(limits) == set(DIMENSIONS), "BUDGET_DIMENSIONS")
        require(all(v is None or type(v) is int and 0 <= v <= 2**53 - 1
                    for v in limits.values()), "BUDGET_RANGE")
        with self.database.transaction() as db:
            require(category in {None, "training", "evaluation", "development"}, "BUDGET_ACCOUNT")
            if parent:
                row = db.execute("SELECT * FROM accounts WHERE id=?", (parent,)).fetchone()
                require(row is not None, "BUDGET_PARENT_MISSING")
                require(row["campaign"] in (campaign, "*"), "FORBIDDEN")
                require(row["category"] is None or category in (None, row["category"]), "FORBIDDEN")
                category = category or row["category"]
            db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?)",
                       (name, parent, campaign, agent, canonical(limits).decode(), category))

    @staticmethod
    def ancestors(db, account):
        result = []
        while account:
            row = db.execute("SELECT * FROM accounts WHERE id=?", (account,)).fetchone()
            require(row is not None and account not in [r["id"] for r in result], "BUDGET_ACCOUNT")
            result.append(row)
            account = row["parent"]
        return result

    @classmethod
    def totals(cls, db, account):
        amounts = cls.exposures(db)
        totals = {k: 0 for k in DIMENSIONS}
        uncertain = False
        for row in db.execute("SELECT * FROM operations"):
            if account not in [a["id"] for a in cls.ancestors(db, row["account"])]:
                continue
            uncertain |= bool(row["uncertain"])
            if row["parent"] is not None:
                continue  # Included by its parent's recursive exposure, exactly once.
            amount = amounts[row["id"]]
            for key in DIMENSIONS:
                if amount[key] is None or totals[key] is None:
                    totals[key] = None
                else:
                    totals[key] += amount[key]
        return totals, uncertain

    @staticmethod
    def exposures(db):
        """Open envelopes hold max(bound, descendants); closed ones count descendants.

        Ordinary operations still add their own usage to their descendants. An
        envelope is explicitly registered at reservation, never inferred from a
        parent ID. Provider overruns remain visible even above an envelope bound.
        """
        rows = {r["id"]: r for r in db.execute("SELECT * FROM operations")}
        envelopes = {r[0] for r in db.execute("SELECT operation FROM budget_envelopes")}
        children = {op: [] for op in rows}
        for op, row in rows.items():
            if row["parent"] is not None:
                children[row["parent"]].append(op)
        result = {}

        def visit(op):
            row = rows[op]
            own = json.loads(row["actual"] or row["reserved"])
            nested = [visit(child) for child in children[op]]
            amount = {}
            for key in DIMENSIONS:
                values = [v[key] for v in nested]
                subtotal = None if None in values else sum(values)
                if own[key] is None or subtotal is None:
                    amount[key] = None
                elif op in envelopes:
                    amount[key] = max(own[key], subtotal)
                else:
                    amount[key] = own[key] + subtotal
            result[op] = amount
            return amount

        for op, row in rows.items():
            if row["parent"] is None:
                visit(op)
        require(len(result) == len(rows), "OPERATION_LINEAGE")
        return result

    def post(self, account: str, record: BudgetLedger, *, envelope=False):
        with self.database.transaction() as db:
            return self.post_in_transaction(db, account, record, envelope=envelope)

    def post_in_transaction(self, db, account: str, record: BudgetLedger, *, envelope=False,
                            close_envelope=False):
        """Compose a posting with its operator dispatch intent in the same commit."""
        require(db is self.database.connection and db.in_transaction, "TRANSACTION_REQUIRED")
        require(not record.is_example, "EXAMPLE_NOT_EXECUTABLE")
        body = record.model_dump()
        previous = db.execute("SELECT digest FROM ledger WHERE campaign=? AND source=?",
                              (record.campaign_id, record.source_event_id)).fetchone()
        if previous:
            require(previous["digest"] == digest({"account": account, "body": body}),
                    "IDEMPOTENCY_CONFLICT")
            if record.posting == "reserve":
                registered = db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?",
                                        (record.operation_id,)).fetchone() is not None
                require(registered == envelope, "IDEMPOTENCY_CONFLICT")
            return False
        chain = self.ancestors(db, account)
        require(chain[0]["campaign"] == record.campaign_id and
                chain[0]["agent"] == record.agent_id and
                chain[0]["category"] == record.campaign_account, "FORBIDDEN")
        op = db.execute("SELECT * FROM operations WHERE id=?", (record.operation_id,)).fetchone()
        amount = vector(record)
        if record.posting == "reserve":
            require(not close_envelope, "ENVELOPE_POSTING")
            require(op is None, "OPERATION_EXISTS")
            if record.parent_operation_id:
                parent = db.execute("SELECT * FROM operations WHERE id=?",
                                    (record.parent_operation_id,)).fetchone()
                require(parent is not None and parent["account"] == account, "FORBIDDEN")
                parent_id = record.parent_operation_id
                while parent_id:
                    ancestor_op = db.execute("SELECT * FROM operations WHERE id=?",
                                             (parent_id,)).fetchone()
                    if db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?",
                                  (parent_id,)).fetchone():
                        require(ancestor_op["actual"] is None, "ENVELOPE_CLOSED")
                    parent_id = ancestor_op["parent"]
            if any(self.totals(db, ancestor["id"])[1] for ancestor in chain):
                from .metering_trial import admit_retained_unknowns
                admit_retained_unknowns(db, account, record, envelope=envelope)
            require(all(amount[k] is not None for k in DIMENSIONS), "METERING_UNKNOWN")
            db.execute("INSERT INTO operations(id,account,parent,kind,reserved) VALUES (?,?,?,?,?)",
                       (record.operation_id, account, record.parent_operation_id, record.kind,
                        canonical(amount).decode()))
            if envelope:
                db.execute("INSERT INTO budget_envelopes VALUES(?)", (record.operation_id,))
                self.database.event(db, "budget.envelope_opened", {
                    "operation_id": record.operation_id, "policy": "nested-envelope/1"})
            # Validate the post-insert exposure, including consumption within every
            # enclosing job. Transaction rollback removes a rejected reservation.
            exposures = self.exposures(db)
            parent_id = record.parent_operation_id
            while parent_id:
                parent = db.execute("SELECT * FROM operations WHERE id=?", (parent_id,)).fetchone()
                if db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?",
                              (parent_id,)).fetchone():
                    bound = json.loads(parent["reserved"])
                    require(all(exposures[parent_id][k] is not None and bound[k] is not None and
                                exposures[parent_id][k] <= bound[k] for k in DIMENSIONS),
                            "ENVELOPE_EXHAUSTED")
                parent_id = parent["parent"]
            for ancestor in chain:
                total, _ = self.totals(db, ancestor["id"])
                limits = json.loads(ancestor["limits"])
                for key in DIMENSIONS:
                    require(total[key] is not None and amount[key] is not None,
                            "METERING_UNKNOWN")
                    if limits[key] is not None:
                        require(total[key] <= limits[key], "BUDGET_EXHAUSTED")
        else:
            require(not envelope, "ENVELOPE_POSTING")
            require(op is not None and op["account"] == account and
                    op["parent"] == record.parent_operation_id and op["kind"] == record.kind,
                    "OPERATION_LINEAGE")
            registered = db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?",
                                    (record.operation_id,)).fetchone() is not None
            require(registered == close_envelope, "ENVELOPE_POSTING")
            if close_envelope:
                require(record.posting == "settle" and record.metering == "reported" and
                        record.raw_usage_ref is not None and
                        all(v == 0 for v in amount.values()), "ENVELOPE_POSTING")
                pending = db.execute("SELECT 1 FROM operations WHERE parent=? AND "
                                     "(actual IS NULL OR uncertain=1)",
                                     (record.operation_id,)).fetchone()
                require(pending is None, "DESCENDANT_UNSETTLED")
                self.database.event(db, "budget.envelope_closed", {
                    "operation_id": record.operation_id, "seal_ref": record.raw_usage_ref,
                    "policy": "nested-envelope/1"})
            if record.posting == "settle":
                require(op["actual"] is None, "ALREADY_SETTLED")
            else:
                require(op["actual"] is not None and record.raw_usage_ref is not None
                        and record.reason.startswith("reconcile:"), "INVALID_ADJUSTMENT")
                old = json.loads(op["actual"])
                require(all(old[k] is not None and amount[k] is not None for k in DIMENSIONS),
                        "UNKNOWN_RECONCILIATION_REQUIRES_RECEIPT")
                amount = {k: old[k] + amount[k] for k in DIMENSIONS}
                require(all(v >= 0 for v in amount.values()), "NEGATIVE_TOTAL")
            db.execute("UPDATE operations SET actual=?,uncertain=? WHERE id=?",
                       (canonical(amount).decode(), int(record.metering == "unknown" or
                        any(v is None for v in amount.values())), record.operation_id))
        db.execute("INSERT INTO ledger VALUES (?,?,?,?)", (record.campaign_id,
                   record.source_event_id, digest({"account": account, "body": body}),
                   canonical(body).decode()))
        self.database.event(db, "budget." + record.posting, body)
        return True

    def status(self, account):
        db = self.database.connection
        chain = self.ancestors(db, account)
        amount, uncertain = self.totals(db, account)
        exceeded = []
        for ancestor in chain:
            totals, unknown = self.totals(db, ancestor["id"])
            uncertain |= unknown
            for key, limit in json.loads(ancestor["limits"]).items():
                if limit is not None and totals[key] is not None and totals[key] >= limit:
                    exceeded.append(f"{ancestor['id']}:{key}")
        return {"committed_and_reserved": amount, "uncertain": uncertain,
                "exhausted": sorted(exceeded), "dispatch_allowed": not uncertain and not exceeded}

    def hold_uncertain(self, account: str, operation: str, reason: str):
        """Retain a dispatched reservation until the provider reconciles actual calls.

        This is not a fabricated zero-usage settlement. Native turn summaries are
        insufficient to settle a job containing retries/helpers. The hold blocks
        further dispatch throughout the ancestor chain, including after a crash.
        """
        require(bool(reason) and len(reason) <= 256, "INVALID_REASON")
        with self.database.transaction() as db:
            row = db.execute("SELECT * FROM operations WHERE id=?", (operation,)).fetchone()
            require(row is not None and row["account"] == account, "OPERATION_LINEAGE")
            if row["actual"] is None and not row["uncertain"]:
                db.execute("UPDATE operations SET uncertain=1 WHERE id=?", (operation,))
                self.database.event(db, "budget.unsettled_dispatch", {
                    "account": account, "operation_id": operation, "reason": reason})
