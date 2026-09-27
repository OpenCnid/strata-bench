"""Finite prior capacity, real SQLite holds, and private transport rejection."""

import copy
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest

from mcbench.storage import Database, Fault, canonical, digest
from strata_evaluator import telemetry_capacity as capacity
from strata_evaluator.protected_reference import parse_protected_plan
from strata_evaluator.reference_abort import abort_scope
from strata_evaluator.reference_launch import ReferenceLauncher, parse_launch_plan
from strata_evaluator.reference_pair import ReferencePair
from strata_evaluator.telemetry_pipe import TelemetryPipeBroker
from test_craft_reference import reference, pin  # noqa: F401
from test_protected_reference import plan as base_plan  # noqa: F401
from test_online_reference import online  # noqa: F401
from test_telemetry_pipe import sink  # noqa: F401


def bound(size=65536):
    return capacity.TelemetryCapacity(policy=capacity.POLICY, max_bytes=size, max_events=100)


def upgraded(profile):
    value = copy.deepcopy(profile)
    value["schema"] = "strata/ProtectedReferencePlan/3"
    value["launch"].update(schema="strata/PrivateReferenceLaunch/8",
                           telemetry_capacity=bound(128 * 1024**2).model_dump())
    return value


def test_capacity_is_a_new_prior_bound_profile_without_migrating_legacy(online):  # noqa: F811
    prior = copy.deepcopy(online)
    old = parse_protected_plan(online)
    assert capacity.limits(old.launch) == {"max_bytes": 8388608, "max_events": 2000}
    assert old.model_dump(by_alias=True) == prior
    value = upgraded(online)
    parsed = parse_protected_plan(value)
    assert parsed.model_dump(by_alias=True) == value
    assert capacity.limits(parsed.launch) == {"max_bytes": 128 * 1024**2, "max_events": 100}
    assert abort_scope(parsed.launch).launch_plan_digest == digest(value["launch"])
    assert abort_scope(parsed.launch).launch_plan_digest != abort_scope(old.launch).launch_plan_digest
    assert parse_launch_plan(value["launch"]).telemetry_capacity == parsed.launch.telemetry_capacity
    value["launch"]["telemetry_capacity"]["max_bytes"] += 1
    assert abort_scope(value["launch"]).launch_plan_digest != abort_scope(parsed.launch).launch_plan_digest
    assert online == prior


@pytest.mark.parametrize("field,value", [("max_bytes", 65535), ("max_bytes", 1024**3 + 1),
    ("max_bytes", True), ("max_bytes", "8388608"), ("max_events", 0),
    ("max_events", 1000001), ("max_events", 2.5), ("policy", "unbounded"), ("extra", 1)])
def test_invalid_or_unknown_capacity_is_rejected_before_launch(online, field, value):  # noqa: F811
    changed = upgraded(online)
    changed["launch"]["telemetry_capacity"][field] = value
    with pytest.raises(ValueError):
        parse_protected_plan(changed)


@pytest.mark.parametrize("change", ["missing", "old_launch", "old_protected", "new_protected_old_launch"])
def test_capacity_cannot_be_omitted_or_attached_to_an_old_identity(online, change):  # noqa: F811
    value = upgraded(online)
    if change == "missing":
        del value["launch"]["telemetry_capacity"]
    elif change == "old_launch":
        value["launch"]["schema"] = "strata/PrivateReferenceLaunch/5"
    elif change == "old_protected":
        value["schema"] = "strata/ProtectedReferencePlan/2"
    else:
        value["launch"] = online["launch"]
    with pytest.raises(ValueError):
        parse_protected_plan(value)


@pytest.mark.parametrize("change", [None, "max_bytes", "max_events"])
def test_pair_checks_exact_nested_capacity_before_reservation(reference, online, tmp_path, change):  # noqa: F811
    store, _, _, _, _ = reference
    value = upgraded(online)
    protected_file, launch_file = tmp_path / "protected.json", tmp_path / "launch.json"
    protected_file.write_bytes(canonical(value))
    launch = copy.deepcopy(value["launch"])
    if change is not None:
        launch["telemetry_capacity"][change] += 1
    launch_file.write_bytes(canonical(launch))

    def pinned(path):
        return {"path": str(path), **pin(path)}

    root = Path(__file__).resolve().parents[1]
    pair = {"schema": "strata/PrivateReferencePair/2", "protected_file": pinned(protected_file),
            "launch_file": pinned(launch_file), "client_driver": pinned(launch_file),
            "python": pinned(Path(sys.executable)), "bootstrap": pinned(root / "src/mcbench/process_bootstrap.py"),
            "source_root": str(root), "inputs": [pinned(launch_file)],
            "evidence_directory": str(tmp_path / "pair"), "client_window_ms": 1000, "finalize_ms": 1000}
    # Matching version/capacity reaches the next unchanged bootstrap gate. This
    # intentionally incomplete fixture cannot reserve or run a native process.
    error = "REFERENCE_PAIR_PROTECTED_BINDING" if change else "REFERENCE_PAIR_LAUNCH_BOOTSTRAP"
    with pytest.raises(Fault, match=error):
        ReferencePair(store.database).run(pair)
    assert store.database.connection.execute("SELECT COUNT(*) FROM reference_pairs").fetchone()[0] == 0
    assert not Path(pair["evidence_directory"]).exists()


def reserve(database, root, instance="i"):
    with database.transaction() as db:
        return capacity.reserve(database, db, instance, "a" * 64, bound(), root)


def test_insufficient_space_is_not_a_reservation_or_dispatch(tmp_path, monkeypatch):
    database = Database(tmp_path / "ledger.sqlite")
    monkeypatch.setattr(capacity.shutil, "disk_usage", lambda _: SimpleNamespace(free=capacity.DISK_MARGIN + 65535))
    try:
        with pytest.raises(Fault, match="TELEMETRY_STORAGE_DISK_LOW"):
            reserve(database, tmp_path)
        assert not database.connection.execute("SELECT * FROM outbox").fetchall()
        assert not database.connection.execute("SELECT name FROM sqlite_master WHERE name='reference_telemetry_capacity'").fetchall()
    finally:
        database.close()


def test_competing_connections_cannot_both_spend_the_same_logical_capacity(tmp_path, monkeypatch):
    path = tmp_path / "ledger.sqlite"
    database = Database(path)
    database.close()
    monkeypatch.setattr(capacity.shutil, "disk_usage", lambda _: SimpleNamespace(free=capacity.DISK_MARGIN + 2 * 65536 - 1))
    barrier = Barrier(2)

    def attempt(instance):
        database = Database(path)
        try:
            barrier.wait(timeout=10)
            try:
                reserve(database, tmp_path, instance)
                return "reserved"
            except Fault as error:
                return error.code
        finally:
            database.close()

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(attempt, ["a", "b"]))
    assert sorted(results) == ["TELEMETRY_STORAGE_DISK_LOW", "reserved"]
    database = Database(path)
    try:
        assert database.connection.execute("SELECT SUM(bytes) FROM reference_telemetry_capacity WHERE state='RESERVED'").fetchone()[0] == 65536
    finally:
        database.close()


@pytest.fixture
def held_capacity(reference, tmp_path):  # noqa: F811
    store, _, _, _, _ = reference
    launcher = ReferenceLauncher(store)
    proof = reserve(store.database, tmp_path)
    body = {"status": "stopped_reference", "plan_digest": "a" * 64, "telemetry_capacity": proof,
            "launch_binding_verified": True, "stop_sent": True, "forced_stop": False, "exit_code": 0,
            "records": 4, "broker": {"status": "stopped", "records": 4, "bytes": 4096},
            "job_accounting": {"active_processes": 0, "total_processes": 2},
            "held_members": {"held_processes": 2, "signaled_processes": 2}}
    with store.database.transaction() as db:
        db.execute("INSERT INTO reference_dispatches VALUES('i','{}','INTENT','{}')")
    return launcher, body, tmp_path


def test_uncertainty_and_restart_keep_hold_and_used_identity(held_capacity):
    launcher, body, root = held_capacity
    body["status"] = "uncertain"
    launcher._record("i", "UNCERTAIN", body)
    reopened = Database(launcher.database.path)
    try:
        assert reopened.connection.execute("SELECT state FROM reference_telemetry_capacity").fetchone()[0] == "RESERVED"
        with pytest.raises(Fault, match="TELEMETRY_STORAGE_ALREADY_RESERVED"):
            reserve(reopened, root)
    finally:
        reopened.close()


@pytest.mark.parametrize("change", ["partial", "forced", "active", "missing_parent", "wrong_count", "overspend", "changed_plan", "changed_capacity"])
def test_unproven_terminal_or_changed_scope_cannot_release_hold(held_capacity, change):
    launcher, body, _ = held_capacity
    if change == "partial":
        body["broker"]["status"] = "uncertain"
    elif change == "forced":
        body["forced_stop"] = True
    elif change == "active":
        body["job_accounting"]["active_processes"] = 1
    elif change == "missing_parent":
        body["held_members"]["signaled_processes"] = 1
    elif change == "wrong_count":
        body["broker"]["records"] = 3
    elif change == "overspend":
        body["broker"]["bytes"] = 65537
    elif change == "changed_plan":
        body["plan_digest"] = "b" * 64
    else:
        body["telemetry_capacity"]["capacity_digest"] = "b" * 64
    with pytest.raises(Fault):
        launcher._record("i", "STOPPED", body)
    assert launcher.database.connection.execute("SELECT state FROM reference_telemetry_capacity").fetchone()[0] == "RESERVED"
    assert launcher.database.connection.execute("SELECT state FROM reference_dispatches").fetchone()[0] == "INTENT"
    assert "telemetry_capacity_settlement" not in body


def test_stop_and_capacity_consumption_commit_together_and_never_rearm(held_capacity, monkeypatch):
    launcher, body, root = held_capacity
    original = launcher.database.event

    def fail(db, kind, value):
        if kind == "private.reference_dispatch":
            raise OSError("synthetic journal failure")
        return original(db, kind, value)

    monkeypatch.setattr(launcher.database, "event", fail)
    with pytest.raises(OSError):
        launcher._record("i", "STOPPED", body)
    assert launcher.database.connection.execute("SELECT state FROM reference_telemetry_capacity").fetchone()[0] == "RESERVED"
    assert "telemetry_capacity_settlement" not in body
    monkeypatch.setattr(launcher.database, "event", original)
    launcher._record("i", "STOPPED", body)
    row = launcher.database.connection.execute("SELECT * FROM reference_telemetry_capacity").fetchone()
    assert row["state"] == "CONSUMED" and row["actual_bytes"] == 4096
    row = launcher.database.connection.execute("SELECT * FROM reference_dispatches").fetchone()
    assert row["state"] == "STOPPED" and json.loads(row["body"]) == body
    assert body["telemetry_capacity_settlement"] == {"state": "CONSUMED", "actual_bytes": 4096, "unused_bytes": 61440}
    with pytest.raises(Fault, match="TELEMETRY_STORAGE_ALREADY_RESERVED"):
        reserve(launcher.database, root)


def test_missing_dispatch_rolls_back_capacity_settlement(held_capacity):
    launcher, body, _ = held_capacity
    with launcher.database.transaction() as db:
        db.execute("DELETE FROM reference_dispatches WHERE instance='i'")
    with pytest.raises(Fault, match="TELEMETRY_STORAGE_DISPATCH_MISSING"):
        launcher._record("i", "STOPPED", body)
    assert launcher.database.connection.execute("SELECT state FROM reference_telemetry_capacity").fetchone()[0] == "RESERVED"
    assert "telemetry_capacity_settlement" not in body


@pytest.mark.parametrize("field", ["max_bytes", "max_events"])
def test_broker_cannot_use_capacity_different_from_prior_plan(reference, sink, tmp_path, field):  # noqa: F811
    store, _, _, _, _ = reference
    existing, _, _, _, _, _ = sink
    existing.plan.telemetry_capacity = bound()
    settings = {"schema": "strata/ForgeTelemetryBrokerSettings/1", "campaign_id": existing.authority.campaign_id,
                "epoch": existing.authority.epoch, **capacity.limits(existing.plan),
                "recipe_ids": list(existing.setup.recipe_digests), "config_queries": []}
    settings[field] += 1
    spool = tmp_path / "different-spool"
    with pytest.raises(Fault, match="TELEMETRY_PIPE_CAPACITY_BINDING"):
        TelemetryPipeBroker(store.database, existing.authority, spool, existing.plan, existing.setup,
                            writer_sid="unused", group_sid="unused", scope_sid="unused", deadline=0, settings=settings)
    assert not spool.exists()


@pytest.mark.parametrize("limit", ["max_bytes", "max_events"])
def test_bound_exhaustion_cannot_ack_or_append_another_record(sink, limit):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    broker._event(canonical(first) + b"\n", identity, key)
    path = next(broker.spool.glob("*.authenticated.jsonl"))
    before = path.read_bytes()
    broker.settings[limit] = broker.bytes if limit == "max_bytes" else broker.count
    stop = first | {"seq": 2, "server_event_seq": 2, "kind": "server_stopped",
                    "payload_schema": "strata/ServerStopped/1", "payload": {}}
    with pytest.raises(Fault, match="TELEMETRY_PIPE_QUOTA"):
        broker._event(canonical(stop) + b"\n", identity, key)
    assert path.read_bytes() == before and len(receipts) == broker.count == 1
    assert not broker.stopped
