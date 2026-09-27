"""Real temporary SQLite upgrades; no operator database or live authority."""
import hashlib
import sqlite3

import pytest

from mcbench.controller import Controller
from mcbench.controls import Controls
from mcbench.storage import Database, Fault


def logical_state(connection):
    schema = list(connection.execute("SELECT type,name,sql FROM sqlite_master ORDER BY type,name"))
    tables = [row[1] for row in schema if row[0] == "table"]
    return ([tuple(row) for row in schema],
            {name: [tuple(row) for row in connection.execute('SELECT * FROM "' + name + '"')]
             for name in tables})


def test_populated_version_zero_upgrade_and_reopen_preserve_journal_and_objects(tmp_path):
    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as old:
        old.execute("CREATE TABLE outbox (cursor INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL)")
        old.execute("CREATE TABLE objects (namespace TEXT, ref TEXT, visibility TEXT NOT NULL, "
                    "media_type TEXT NOT NULL, bytes INTEGER NOT NULL, PRIMARY KEY(namespace,ref))")
        old.execute("INSERT INTO outbox VALUES (42,'consumed','{\"hold\":123}')")
        old.execute("INSERT INTO objects VALUES ('private','opaque','evaluator','application/json',17)")
    for _ in range(2):
        db = Database(path)
        try:
            assert db.connection.execute("PRAGMA user_version").fetchone()[0] == 1
            assert tuple(db.connection.execute("SELECT * FROM outbox").fetchone()) == (42, "consumed", '{"hold":123}')
            assert tuple(db.connection.execute("SELECT * FROM objects").fetchone()) == (
                "private", "opaque", "evaluator", "application/json", 17)
        finally:
            db.close()
    db = Database(path)
    try:
        with db.transaction() as transaction:
            assert db.event(transaction, "next", {"held": True}) == 43
    finally:
        db.close()


def test_future_version_refusal_preserves_existing_state(tmp_path):
    path = tmp_path / "future.sqlite"
    with sqlite3.connect(path) as old:
        old.execute("CREATE TABLE future (value TEXT)")
        old.execute("INSERT INTO future VALUES ('do not reinterpret')")
        old.execute("PRAGMA user_version=100")
        before = logical_state(old)
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        Database(path)
    with sqlite3.connect(path) as current:
        assert current.execute("PRAGMA user_version").fetchone()[0] == 100
        assert logical_state(current) == before


def legacy_grants(db):
    db.execute("CREATE TABLE grants (hash TEXT PRIMARY KEY, campaign TEXT, agent TEXT, role TEXT, "
               "namespace TEXT, epoch INTEGER, methods TEXT, expires REAL, remaining INTEGER, "
               "revoked INTEGER DEFAULT 0)")
    db.execute("INSERT INTO grants VALUES (?,'c1','a1','executor','campaign:c1:agent:a1',1,"
               "'[\"act\"]',1000,3,0)", (hashlib.sha256(b"legacy-token").hexdigest(),))


def legacy_controls(db):
    db.execute("CREATE TABLE control_transactions (id TEXT PRIMARY KEY, agent TEXT, fingerprint TEXT, "
               "phase TEXT, plan TEXT, receipt TEXT)")
    db.execute("INSERT INTO control_transactions VALUES ('legacy','a1','old','verifying','{}',NULL)")


@pytest.mark.parametrize("kind", ["grants", "controls"])
def test_denied_column_upgrade_rolls_back_data_and_schema_then_reopens(database, kind):
    with database.transaction() as db:
        (legacy_grants if kind == "grants" else legacy_controls)(db)
    before = logical_state(database.connection)
    database.connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_DENY
                                      if action == sqlite3.SQLITE_ALTER_TABLE else sqlite3.SQLITE_OK)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            if kind == "grants":
                Controller(database, simulation=True)
            else:
                Controls(database, None, simulation=True)
    finally:
        database.connection.set_authorizer(None)
    assert logical_state(database.connection) == before
    for _ in range(2):
        if kind == "grants":
            Controller(database, simulation=True)
            row = tuple(database.connection.execute("SELECT * FROM grants").fetchone())
            assert row[:-1] == before[1]["grants"][0] and row[-1] is None
        else:
            Controls(database, None, simulation=True)
            row = tuple(database.connection.execute("SELECT * FROM control_transactions").fetchone())
            assert row[:-1] == before[1]["control_transactions"][0] and row[-1] is None
            with pytest.raises(Fault, match="SETTINGS_LEGACY_RECOVERY_REQUIRED"):
                Controls._idle(database.connection, "new-profile", "new-transaction", "a2")


def test_migrated_grant_cannot_invent_input_generation_or_restore_consumed_quota(database, configs):
    with database.transaction() as db:
        legacy_grants(db)
    controller = Controller(database, simulation=True, clock=lambda: 100)
    config, agents = configs()
    controller.create(config, agents)
    with database.transaction() as db:
        db.execute("UPDATE campaigns SET state='RUNNING',epoch=1,lease_until=1000")
        db.execute("UPDATE avatar_lanes SET epoch=1,generation=7,state='READY',lease_id='lease'")
    with pytest.raises(Fault, match="INPUT_SUSPENDED"):
        controller.authorize("legacy-token", "c1", "a1", 1, "act", 101)
    assert database.connection.execute("SELECT remaining FROM grants").fetchone()[0] == 3
    token = controller.grant("c1", None, 1, "a1", "campaign:c1:agent:a1", ["act"], quota=2)
    controller.authorize(token, "c1", "a1", 1, "act", 101)
    for _ in range(2):
        Controller(database, simulation=True, clock=lambda: 100)
        rows = {row[0]: (row[1], row[2]) for row in database.connection.execute(
            "SELECT hash,generation,remaining FROM grants")}
        assert rows[hashlib.sha256(b"legacy-token").hexdigest()] == (None, 3)
        assert rows[hashlib.sha256(token.encode()).hexdigest()] == (7, 1)
