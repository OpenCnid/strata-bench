"""Repair attribution for the existing at-most-once inference dispatch boundary.

Costs stay on their original operations. Freezing closes new inference admission
for this avatar while existing requests retain their settlement/uncertainty paths.
This supplies one accounting dependency, not complete repair or runtime approval.
"""

import json

from .records import BudgetLedger
from .storage import Database, canonical, require


def install(db):
    db.execute("CREATE TABLE IF NOT EXISTS repair_inference_windows (repair TEXT PRIMARY KEY, "
               "campaign TEXT NOT NULL, agent TEXT NOT NULL, epoch INTEGER NOT NULL, "
               "opening_cursor INTEGER NOT NULL, closing_cursor INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS repair_inference_members (repair TEXT, operation TEXT, "
               "basis TEXT NOT NULL, fingerprint TEXT NOT NULL, PRIMARY KEY(repair,operation))")


def _exists(db, table):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _member(db, window, attempt, basis):
    reserve = BudgetLedger.model_validate_json(attempt["reservation"])
    require(reserve.campaign_id == window["campaign"] and reserve.agent_id == window["agent"]
            and reserve.epoch == window["epoch"] and reserve.kind in {"model", "helper"},
            "REPAIR_INFERENCE_SCOPE")
    db.execute("INSERT INTO repair_inference_members VALUES (?,?,?,?)",
               (window["repair"], attempt["operation"], basis, attempt["fingerprint"]))


def begin(db, repair, campaign, agent, epoch):
    """Called atomically with the original repair request and input suspension."""
    cursor = Database.event(db, "repair.inference_opened", {"transaction_id": repair,
        "campaign_id": campaign, "agent_id": agent, "epoch": epoch})
    db.execute("INSERT INTO repair_inference_windows VALUES (?,?,?,?,?,NULL)",
               (repair, campaign, agent, epoch, cursor))
    window = db.execute("SELECT * FROM repair_inference_windows WHERE repair=?", (repair,)).fetchone()
    if _exists(db, "inference_attempts"):
        for row in db.execute("SELECT * FROM inference_attempts WHERE state<>'SETTLED' "
                "AND json_extract(reservation,'$.campaign_id')=? AND json_extract(reservation,'$.agent_id')=?",
                (campaign, agent)).fetchall():
            _member(db, window, row, "in_flight_at_repair_request")


def active_window(db, reserve):
    if not _exists(db, "avatar_lanes"):
        return None
    lane = db.execute("SELECT repair FROM avatar_lanes WHERE campaign=? AND agent=?",
                      (reserve.campaign_id, reserve.agent_id)).fetchone()
    if lane is None or lane["repair"] is None:
        return None
    require(_exists(db, "repair_inference_windows"), "REPAIR_INFERENCE_UNTRACKED")
    window = db.execute("SELECT * FROM repair_inference_windows WHERE repair=?", (lane["repair"],)).fetchone()
    require(window is not None and window["epoch"] == reserve.epoch, "REPAIR_INFERENCE_UNTRACKED")
    require(window["closing_cursor"] is None, "REPAIR_INFERENCE_FROZEN")
    return window


def admitted(db, window, operation):
    if window is not None:
        row = db.execute("SELECT * FROM inference_attempts WHERE operation=?", (operation,)).fetchone()
        _member(db, window, row, "admitted_during_repair")


def _window(db, repair):
    row = db.execute("SELECT * FROM repair_inference_windows WHERE repair=?", (repair["id"],)).fetchone()
    require(row is not None, "REPAIR_INFERENCE_UNTRACKED")
    require((row["campaign"], row["agent"], row["epoch"]) == (repair["campaign"], repair["agent"], repair["epoch"]),
            "REPAIR_INFERENCE_CHANGED")
    opened = db.execute("SELECT kind,body FROM outbox WHERE cursor=?", (row["opening_cursor"],)).fetchone()
    require(opened is not None and opened["kind"] == "repair.inference_opened"
            and json.loads(opened["body"]) == {"transaction_id": repair["id"], "campaign_id": repair["campaign"],
                "agent_id": repair["agent"], "epoch": repair["epoch"]}, "REPAIR_INFERENCE_CHANGED")
    if row["closing_cursor"] is not None:
        closed = db.execute("SELECT kind,body FROM outbox WHERE cursor=?", (row["closing_cursor"],)).fetchone()
        require(row["closing_cursor"] > row["opening_cursor"] and closed is not None
                and closed["kind"] == "repair.inference_frozen"
                and json.loads(closed["body"]) == {"transaction_id": repair["id"]}, "REPAIR_INFERENCE_CHANGED")
    return row


class RepairInference:
    def __init__(self, repairs):
        self.repairs, self.database = repairs, repairs.database

    def freeze(self, transaction, owner, epoch):
        """Close admission once; do not cancel, settle, replay or refund calls."""
        with self.database.transaction() as db:
            repair = self.repairs.status(transaction)
            self.repairs._owned(db, repair, owner, epoch)
            row = _window(db, repair)
            if row["closing_cursor"] is None:
                cursor = self.database.event(db, "repair.inference_frozen", {"transaction_id": transaction})
                db.execute("UPDATE repair_inference_windows SET closing_cursor=? WHERE repair=?", (cursor, transaction))
        return self.audit(transaction, owner, epoch)

    def audit(self, transaction, owner, epoch):
        with self.database.transaction() as db:
            return self.audit_in_transaction(db, transaction, owner, epoch)

    def audit_in_transaction(self, db, transaction, owner, epoch):
        require(db is self.database.connection and db.in_transaction, "TRANSACTION_REQUIRED")
        repair = self.repairs.status(transaction)
        self.repairs._owned(db, repair, owner, epoch, unexpired=False)
        window = _window(db, repair)
        members = db.execute("SELECT * FROM repair_inference_members WHERE repair=? ORDER BY operation",
                             (transaction,)).fetchall()
        expected = set()
        if _exists(db, "inference_attempts"):
            for attempt in db.execute("SELECT * FROM inference_attempts WHERE "
                    "json_extract(reservation,'$.campaign_id')=? AND json_extract(reservation,'$.agent_id')=?",
                    (window["campaign"], window["agent"])).fetchall():
                intents = db.execute("SELECT cursor FROM outbox WHERE kind='inference.dispatch_intent' "
                                     "AND json_extract(body,'$.operation_id')=?", (attempt["operation"],)).fetchall()
                settled = db.execute("SELECT cursor FROM outbox WHERE kind='inference.settled' "
                                     "AND json_extract(body,'$.operation_id')=?", (attempt["operation"],)).fetchall()
                require(len(intents) == 1 and len(settled) == int(attempt["state"] == "SETTLED"),
                        "REPAIR_INFERENCE_CHANGED")
                if window["closing_cursor"] is not None:
                    require(intents[0][0] < window["closing_cursor"], "REPAIR_INFERENCE_CHANGED")
                if not settled or settled[0][0] > window["opening_cursor"]:
                    expected.add(attempt["operation"])
        require(expected == {m["operation"] for m in members}, "REPAIR_INFERENCE_CHANGED")
        calls = []
        for member in members:
            attempt = db.execute("SELECT * FROM inference_attempts WHERE operation=?", (member["operation"],)).fetchone()
            op = db.execute("SELECT * FROM operations WHERE id=?", (member["operation"],)).fetchone()
            require(attempt is not None and op is not None and attempt["fingerprint"] == member["fingerprint"]
                    and attempt["account"] == op["account"], "REPAIR_INFERENCE_CHANGED")
            reserve = BudgetLedger.model_validate_json(attempt["reservation"])
            require(reserve.campaign_id == window["campaign"] and reserve.agent_id == window["agent"]
                    and reserve.epoch == window["epoch"] and reserve.parent_operation_id == op["parent"]
                    and reserve.kind == op["kind"], "REPAIR_INFERENCE_CHANGED")
            settled = (attempt["state"] == "SETTLED" and op["actual"] is not None and not op["uncertain"]
                       and attempt["receipt_digest"] is not None and attempt["provider_event"] is not None)
            calls.append({"operation_id": op["id"], "account": op["account"], "parent_operation_id": op["parent"],
                "kind": op["kind"], "attribution": member["basis"], "state": attempt["state"],
                "settled": bool(settled), "receipt_digest": attempt["receipt_digest"],
                "provider_event_digest": attempt["provider_event"],
                "actual": json.loads(op["actual"]) if op["actual"] is not None else None,
                "reserved": json.loads(op["reserved"]), "uncertain": bool(op["uncertain"])})
        result = {"schema": "strata/RepairInferenceAudit/1", "is_example": self.repairs.controller.simulation,
            "transaction_id": transaction, "campaign_id": window["campaign"], "agent_id": window["agent"],
            "epoch": window["epoch"], "opening_cursor": window["opening_cursor"],
            "closing_cursor": window["closing_cursor"], "admission_closed": window["closing_cursor"] is not None,
            "calls": calls, "tracked_dispatches_settled": window["closing_cursor"] is not None
                and all(c["settled"] for c in calls), "costs_reposted": False,
            "complete_repair_accounting": False, "campaign_permission_published": False}
        require(len(canonical(result)) <= 1024 * 1024, "REPAIR_INFERENCE_AUDIT_QUOTA")
        return result
