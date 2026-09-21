"""Revocation races and uncertain tool work retain native helper capacity."""

import json
import threading

import pytest

from mcbench.broker import NativeBroker
from mcbench.broker_lifecycle import require_drained
from mcbench.storage import CAS, Database, Fault
from test_native_admission import admitted as _admitted, broker_meta
from test_native_broker import broker as _broker, meta, request
from test_native_retirement import scenario

admitted = _admitted
broker = _broker


def states(db):
    return [dict(r) for r in db.execute("SELECT * FROM broker_call_lifecycle ORDER BY event")]


def test_each_call_has_own_durable_lifetime_even_when_call_id_repeated(broker):
    b, _, _ = broker
    for _ in range(2):
        assert b.call("artifact_list", {}, meta("child"))["files"]
    rows = states(b.db.connection)
    assert len(rows) == 2 and len({r["event"] for r in rows}) == 2
    assert all(r["state"] == "RETURNED" and r["elapsed_ns"] >= 0 and
               r["result_digest"] and r["fault"] is None for r in rows)
    require_drained(b.db.connection, "runtime", "child")
    with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
        b.call("artifact_read", {"path": "docs/root-only"}, meta("child"))
    assert states(b.db.connection)[-1]["state"] == "REJECTED"
    require_drained(b.db.connection, "runtime", "child")


def test_unexpected_exception_and_lost_game_result_are_not_inferred_drained(broker, monkeypatch):
    b, _, _ = broker
    def lost(_):
        raise TimeoutError("private credentials must not appear in durable error")
    with pytest.raises(Fault, match="BROKER_GAME_OUTCOME_UNKNOWN"):
        b.call("game", {"request": request()}, meta(), game_transport=lost)
    assert states(b.db.connection)[0]["state"] == "UNKNOWN"
    with pytest.raises(Fault, match="BROKER_DRAIN_UNCERTAIN"):
        require_drained(b.db.connection, "runtime", "root")
    def unexpected(*args):
        raise RuntimeError("private path must not appear in durable error")
    monkeypatch.setattr(b, "_execute", unexpected)
    with pytest.raises(RuntimeError):
        b.call("artifact_list", {}, meta("child"))
    assert states(b.db.connection)[-1]["fault"] == "BROKER_CALL_UNKNOWN"
    assert "private" not in json.dumps(states(b.db.connection))
    with pytest.raises(Fault, match="BROKER_DRAIN_UNCERTAIN"):
        require_drained(b.db.connection, "runtime", "child")


def test_crash_does_not_erase_pending_work_on_restart(broker, monkeypatch):
    b, _, _ = broker
    def crash(*args):
        raise SystemExit("owned synthetic crash")
    monkeypatch.setattr(b, "_execute", crash)
    with pytest.raises(SystemExit):
        b.call("artifact_list", {}, meta("child"))
    restored = Database(b.db.path)
    try:
        NativeBroker(restored, CAS(restored, b.cas.root), "runtime", "a" * 64, clock=lambda: 100)
        with pytest.raises(Fault, match="BROKER_DRAIN_PENDING"):
            require_drained(restored.connection, "runtime", "child")
        assert len(states(restored.connection)) == 1
    finally:
        restored.close()


@pytest.mark.parametrize("gap", ["legacy_event", "missing_table", "missing_end", "unknown_state"])
def test_legacy_or_incomplete_inventory_cannot_claim_drain(broker, gap):
    b, _, _ = broker
    b.call("artifact_list", {}, meta("child"))
    db = b.db.connection
    if gap == "legacy_event":
        with b.db.transaction() as transaction:
            b.db.event(transaction, "broker.call", {"runtime": "runtime", "thread": "child"})
    elif gap == "missing_table":
        db.execute("DROP TABLE broker_call_lifecycle")
    elif gap == "missing_end":
        db.execute("UPDATE broker_call_lifecycle SET ended_unix_ms=NULL")
    else:
        db.execute("UPDATE broker_call_lifecycle SET state='OTHER'")
    with pytest.raises(Fault, match="BROKER_DRAIN_UNTRACKED|BROKER_DRAIN_UNCERTAIN"):
        require_drained(db, "runtime", "child")
    require_drained(db, "other-runtime", "child")
    require_drained(db, "runtime", "other-child")


def test_retirement_waits_for_started_call_then_denies_post_fence_read_result(admitted):
    admission, gate, broker, plan, _, _, _ = admitted
    entered, release = threading.Event(), threading.Event()
    outcomes = []
    thread = None
    def start_read():
        nonlocal thread
        broker.project("child", "supplied/work.md", "own allowed bytes")
        namespace = gate.db.connection.execute("SELECT namespace FROM broker_grants WHERE thread='child'").fetchone()[0]
        def worker():
            db = Database(gate.db.path)
            class HeldRead(CAS):
                def read(self, principal, ns, ref, **kwargs):
                    if ns == namespace:
                        entered.set()
                        assert release.wait(5), "owned test gate timed out"
                    return super().read(principal, ns, ref, **kwargs)
            try:
                b = NativeBroker(db, HeldRead(db, gate.cas.root), "job", plan.profile_digest())
                outcomes.append(b.call("artifact_read", {"path": "supplied/work.md"}, broker_meta("child", "root")))
            except BaseException as error:
                outcomes.append(error)
            finally:
                db.close()
        thread = threading.Thread(target=worker)
        thread.start()
        assert entered.wait(5), "owned read did not enter"
    try:
        _, ref, _, _ = scenario(admitted, before_revoke=start_read)
        before = gate.budgets.status("a1")["committed_and_reserved"]
        with pytest.raises(Fault, match="BROKER_DRAIN_PENDING"):
            admission.retire("job", "child", ref)
        assert gate.budgets.status("a1")["committed_and_reserved"] == before
        assert not outcomes
    finally:
        release.set()
        if thread:
            thread.join(5)
    assert not thread.is_alive()
    assert len(outcomes) == 1 and isinstance(outcomes[0], Fault) and outcomes[0].code == "BROKER_RUNTIME_REVOKED"
    rows = states(gate.db.connection)
    assert len(rows) == 1 and rows[0]["state"] == "REJECTED" and rows[0]["result_digest"] is None
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"


def test_unknown_broker_work_blocks_retirement_with_usage_settled(admitted):
    admission, gate, broker, _, _, _, _ = admitted
    def legacy_work():
        with gate.db.transaction() as db:
            gate.db.event(db, "broker.call", {"runtime": "job", "thread": "child"})
    _, ref, _, _ = scenario(admitted, before_revoke=legacy_work)
    with pytest.raises(Fault, match="BROKER_DRAIN_UNTRACKED"):
        admission.retire("job", "child", ref)
