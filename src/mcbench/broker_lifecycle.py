"""Durable broker work inventory; process death is not inferred from a timeout."""

import time

from .storage import digest, require

POLICY = "native-broker-call-drain/1"


def install(db):
    db.execute("CREATE TABLE IF NOT EXISTS broker_call_lifecycle (event INTEGER PRIMARY KEY "
        "REFERENCES outbox(cursor), state TEXT NOT NULL, started_unix_ms INTEGER NOT NULL, "
        "ended_unix_ms INTEGER, elapsed_ns INTEGER, result_digest TEXT, fault TEXT)")


def started(db, event):
    db.execute("INSERT INTO broker_call_lifecycle VALUES(?,'STARTED',?,NULL,NULL,NULL,NULL)",
               (event, time.time_ns() // 1000000))


def finished(database, db, event, state, elapsed_ns, *, result=None, fault=None):
    require(state in {"RETURNED", "REJECTED", "UNKNOWN"} and elapsed_ns >= 0, "BROKER_DRAIN_STATE")
    row = db.execute("SELECT state FROM broker_call_lifecycle WHERE event=?", (event,)).fetchone()
    require(row is not None and row[0] == "STARTED", "BROKER_DRAIN_STATE")
    db.execute("UPDATE broker_call_lifecycle SET state=?,ended_unix_ms=?,elapsed_ns=?,result_digest=?,fault=? "
        "WHERE event=?", (state, time.time_ns() // 1000000, elapsed_ns,
                          digest(result) if state == "RETURNED" else None, fault, event))
    database.event(db, "broker.call_finished", {"policy": POLICY, "call_event": event,
        "state": state, "elapsed_ns": elapsed_ns, "fault": fault})


def require_drained(db, runtime, thread):
    """Join every admitted call to its terminal work record, including legacy gaps."""
    scope = "o.kind='broker.call' AND json_extract(o.body,'$.runtime')=? AND json_extract(o.body,'$.thread')=?"
    table = db.execute("SELECT 1 FROM sqlite_master WHERE name='broker_call_lifecycle'").fetchone()
    if table is None:
        require(db.execute("SELECT 1 FROM outbox o WHERE " + scope + " LIMIT 1",
                           (runtime, thread)).fetchone() is None, "BROKER_DRAIN_UNTRACKED")
        return
    rows = db.execute("SELECT l.* FROM outbox o LEFT JOIN broker_call_lifecycle l ON o.cursor=l.event WHERE " +
                      scope, (runtime, thread)).fetchall()
    require(all(row["event"] is not None for row in rows), "BROKER_DRAIN_UNTRACKED")
    require(all(row["state"] != "STARTED" for row in rows), "BROKER_DRAIN_PENDING")
    require(all(row["state"] in {"RETURNED", "REJECTED"} and row["ended_unix_ms"] is not None and
                row["elapsed_ns"] is not None for row in rows), "BROKER_DRAIN_UNCERTAIN")
