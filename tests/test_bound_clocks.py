# ruff: noqa: F401, F811
"""Synthetic setup/body sources, real MAC/ledger and optional held Windows JVM."""

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from types import SimpleNamespace

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.processes import WindowsJob
from mcbench.storage import Fault, canonical, digest
from strata_evaluator.bound_clocks import BoundClockSource
from strata_evaluator.craft_reference import parse_plan
from strata_evaluator.reference_launch import ReferenceLaunchPlan, bind_identity
from strata_evaluator.repair_clocks import RepairClockEvidence
from strata_evaluator.telemetry import LaunchIdentity
from strata_evaluator.telemetry_pipe import TelemetryPipeBroker
from test_live_clocks import sampled, fields_history, team_history, globals_history, clocked, history, native, reference
from test_setup_control import source as signed_source
from test_native_control_plan import native_env, repair_env
from test_telemetry_auth import signed, write

pytestmark = pytest.mark.parametrize("fields_history", [6], indirect=True)


@pytest.fixture
def clock_source(sampled, tmp_path, database):
    fixture, first, last = sampled
    def build(*, campaign="synthetic", roster=None, job=None, identity=None):
        setup, events = fixture[1], fixture[2]
        setup["campaign_id"] = campaign
        for event in events:
            event["campaign_id"] = campaign
        if roster is not None:
            setup["roster"] = roster
            setup["predicate"]["actors"] = list(roster.values())
            setup["native_team_ids"] = dict.fromkeys(roster, next(iter(setup["native_team_ids"].values())))
        exe, module = tmp_path / "java.exe", tmp_path / "module.jar"
        exe.write_bytes(b"synthetic executable identity")
        module.write_bytes(b"synthetic module")
        identity = identity or {"pid": 1234, "process_started_unix_ms": 1000, "executable": str(exe)}
        if job is None:
            job = SimpleNamespace(members={identity["pid"]: 123},
                kernel=SimpleNamespace(WaitForSingleObject=lambda *args: 258),
                member_identity=lambda pid: copy.deepcopy(identity))
        observed = {"policy": "native-server-launch-observation/1", **identity,
            "game_directory": setup["game_directory"], "world_directory": setup["fixture_directory"],
            "module_file": str(module), "module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
            "online_mode": True, "server_port": 25569}
        events[0]["payload"]["launch_identity"] = observed
        events[0]["payload"]["telemetry_transport"] = "windows-owned-pipe/1"
        folder, authority, path, boot = signed_source(fixture, tmp_path)
        def pin(p):
            return {"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        plan = ReferenceLaunchPlan.model_validate({"schema": "strata/PrivateReferenceLaunch/1",
            "instance_id": setup["instance_id"], "setup_digest": digest(setup), "mode": "synthetic-fixture",
            "executable": pin(Path(identity["executable"])), "module_file": pin(module),
            "immutable_files": [pin(Path(identity["executable"])), pin(module)], "immutable_trees": [],
            "evidence_directory": str(tmp_path / "launch"), "server_port": 25569,
            "max_wall_s": 30, "ready_run_s": 1, "graceful_stop_s": 2})
        broker = object.__new__(TelemetryPipeBroker)
        broker.database_path, broker.authority = database.path, authority
        broker.plan, broker.setup = plan, parse_plan(setup)
        broker.spool, broker.boot, broker.job = folder, boot, job
        broker.deadline, broker.closing = time.monotonic() + 30, threading.Event()
        broker.thread = SimpleNamespace(is_alive=lambda: True)
        body = {"records": last["seq"], "server_boot_id": boot, "peer": identity,
            "binding": bind_identity(plan, broker.setup, LaunchIdentity.model_validate(observed), identity)}
        def persist(state="DURABLE"):
            with database.transaction() as db:
                db.execute("CREATE TABLE IF NOT EXISTS telemetry_pipe_boots (authority TEXT PRIMARY KEY,state TEXT,body TEXT)")
                db.execute("INSERT OR REPLACE INTO telemetry_pipe_boots VALUES (?,?,?)",
                           (authority.fingerprint(), state, canonical(body).decode()))
        persist()
        return SimpleNamespace(source=BoundClockSource(broker), broker=broker, body=body, persist=persist,
                               first=first["seq"], last=last["seq"], path=path, identity=identity, events=events)
    return build


def test_owned_source_joins_exact_launch_roster_and_keeps_qualification_separate(clock_source):
    e = clock_source()
    first, last = e.source.observe(e.first), e.source.observe(e.last)
    assert first["source_binding"] == last["source_binding"]
    assert last["launch_binding"]["held_process"] == e.identity
    assert last["is_example"] and not last["process_isolation_qualified"]
    assert not last["complete_repair_accounting"]
    assert set(last["body_fingerprints"]) == set(e.broker.setup.roster)
    assert e.source.observe(e.first) == first


@pytest.mark.parametrize("change", ["terminal", "uncertain", "not_durable", "pid_reused", "exited", "unheld",
    "closed", "deadline", "thread", "launch", "world", "roster", "signed_launch", "boot"])
def test_changed_or_unowned_source_cannot_supply_repair_clock(clock_source, change):
    e = clock_source()
    if change in {"terminal", "uncertain"}:
        e.persist("STOPPED" if change == "terminal" else "UNCERTAIN")
    elif change == "not_durable":
        e.body["records"] = e.first - 1
        e.persist()
    elif change == "pid_reused":
        e.broker.job.member_identity = lambda pid: e.identity | {"process_started_unix_ms": 9999}
    elif change == "exited":
        e.broker.job.kernel.WaitForSingleObject = lambda *args: 0
    elif change == "unheld":
        e.broker.job.members.clear()
    elif change == "closed":
        e.broker.closing.set()
    elif change == "deadline":
        e.broker.deadline = 0
    elif change == "thread":
        e.broker.thread.is_alive = lambda: False
    elif change == "launch":
        e.broker.plan.server_port += 1
    elif change in {"world", "signed_launch"}:
        key = "world_directory" if change == "world" else "module_sha256"
        e.body["binding"]["native_observation"][key] = "wrong" if change == "world" else "0" * 64
        e.persist()
    elif change == "roster":
        e.broker.setup.roster["foreign"] = "22222222-2222-2222-2222-222222222222"
    elif change == "boot":
        e.broker.boot = "other-boot"
    with pytest.raises(ValueError):
        e.source.observe(e.first)


@pytest.mark.parametrize("change", ["native_pid", "foreign_avatar"])
def test_even_a_valid_mac_must_match_retained_launch_and_registered_roster(clock_source, change):
    e = clock_source()
    if change == "native_pid":
        e.events[0]["payload"]["launch_identity"]["pid"] += 1
    else:
        e.events[e.last - 1]["payload"]["avatar_tick_events"] = {"99999999-9999-9999-9999-999999999999": 1}
    write(e.path, signed(e.broker.authority, Path(e.broker.authority.key_file).read_bytes(), e.events))
    with pytest.raises(Fault, match="CLOCK_PREFIX_LAUNCH|CLOCK_SOURCE_FOREIGN_AVATAR"):
        e.source.observe(e.last)


def test_capture_binds_original_controller_repair_without_granting_completion(clock_source, native_env, monkeypatch):
    e, worker, client, target, _, _, _, _ = native_env
    # Match the existing signed fixture actor, preserving its actual raw events.
    from test_craft_reference import ACTOR
    s = clock_source(campaign="c1", roster={"a1": ACTOR, "a2": "22222222-2222-2222-2222-222222222222"})
    body = hashlib.sha256(("127.0.0.1:25569\n" + ACTOR).encode()).hexdigest()
    target = target.model_copy(update={"body_fingerprint": body})
    original = client.call
    def native_call(*args, **kwargs):
        result = original(*args, **kwargs)
        if "body_fingerprint" in result:
            result["body_fingerprint"] = body
        return result
    monkeypatch.setattr(client, "call", native_call)
    monkeypatch.setattr(NativeGameClient, "call", lambda *args, **kwargs: {
        "schema": "strata/NativeGameIdentity/1", "body_fingerprint": body, "connection_generation": 1})
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    service = RepairClockEvidence(e.repairs)
    before = e.budgets.status("a1")
    original_observe = s.source.observe
    for change, code in [("profile", "PROFILE_MISMATCH"), ("campaign", "REPAIR_CLOCK_SCOPE"),
                         ("epoch", "REPAIR_CLOCK_SCOPE"), ("roster", "REPAIR_CLOCK_SCOPE"),
                         ("body", "REPAIR_CLOCK_BODY")]:
        def altered(cursor):
            value = copy.deepcopy(original_observe(cursor))
            if change == "profile":
                value["is_example"] = False
            elif change == "campaign":
                value["prefix"]["campaign_id"] = "foreign"
            elif change == "epoch":
                value["prefix"]["epoch"] += 1
            elif change == "roster":
                del value["roster"]["a2"]
            else:
                value["body_fingerprints"]["a1"] = "0" * 64
            return value
        monkeypatch.setattr(s.source, "observe", altered)
        with pytest.raises(Fault, match=code):
            service.capture("tx", change, "owner", e.epoch, worker, client, s.source, s.first)
        assert e.database.connection.execute("SELECT count(*) FROM repair_clock_marks").fetchone()[0] == 0
    monkeypatch.setattr(s.source, "observe", original_observe)
    result = service.capture("tx", "first", "owner", e.epoch, worker, client, s.source, s.first)
    proof = e.controller.evidence(result["source_ref"])
    assert proof["worker_plan"]["lease_id"] == e.repairs.status("tx")["request"]["old_lease_id"]
    assert proof["native_identity"]["body_fingerprint"] == body
    assert not proof["sample_generation_after_read_start_proven"]
    assert not proof["campaign_permission_published"] and not proof["consumption_settled"]
    assert service.capture("tx", "first", "owner", e.epoch, worker, client, s.source, s.first) == result
    with pytest.raises(Fault, match="REPAIR_CLOCK_DISCONTINUITY"):
        service.capture("tx", "stale", "owner", e.epoch, worker, client, s.source, s.first)
    service.capture("tx", "next", "owner", e.epoch, worker, client, s.source, s.last)
    read = s.source.observe
    def changed_receipt(cursor):
        value = read(cursor)
        value["prefix"]["clock"]["elapsed_wall_ns"] += 1
        return value
    monkeypatch.setattr(s.source, "observe", changed_receipt)
    with pytest.raises(Fault, match="REPAIR_CLOCK_CHANGED"):
        service.capture("tx", "first", "owner", e.epoch, worker, client, s.source, s.first)
    monkeypatch.setattr(s.source, "observe", read)
    assert e.budgets.status("a1") == before
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    assert e.repairs.status("tx")["phase"] == "RECONFIGURING"
    monkeypatch.setattr(NativeGameClient, "call", lambda *args, **kwargs: {
        "schema": "strata/NativeGameIdentity/1", "body_fingerprint": "0" * 64, "connection_generation": 1})
    # Changed cursors do not bypass the native body join: remove only synthetic
    # stored marks to exercise this independent pre-publication refusal.
    with e.database.transaction() as db:
        db.execute("DELETE FROM repair_clock_marks")
    with pytest.raises(Fault, match="REPAIR_CLOCK_BODY"):
        service.capture("tx", "wrong-native", "owner", e.epoch, worker, client, s.source, s.last)
    assert e.database.connection.execute("SELECT count(*) FROM repair_clock_marks").fetchone()[0] == 0


def test_real_held_jvm_identity_is_required_until_prefix_read_finishes(clock_source):
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if os.name != "nt" or not java or not classpath:
        pytest.skip("Explicit Windows Java/classpath required")
    process = subprocess.Popen([java, "-cp", Path(classpath).read_text(encoding="utf-8"),
        "io.github.opencnid.strata.telemetry.LiveClockFixture"], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    job = WindowsJob()
    try:
        job.attach(process)
        job.observe_members()
        identity = job.member_identity(process.pid)
        e = clock_source(job=job, identity=identity)
        proof = e.source.observe(e.first)
        assert proof["launch_binding"]["held_process"] == identity
        assert process.poll() is None
        process.stdin.write(b"stop\n")
        process.stdin.flush()
        assert process.wait(timeout=5) == 0
        # The same retained handle is now signaled. A perfectly valid old MAC
        # cannot turn a terminal process into current server authority.
        with pytest.raises(Fault, match="CLOCK_SOURCE_PROCESS") as stopped:
            e.source.observe(e.first)
        (e.path.parent / "held-jvm-clock-proof.json").write_text(json.dumps({
            "proof": proof, "exit_code": process.returncode, "post_stop_refusal": stopped.value.code,
            "scope": "Actual retained Windows JVM handle; synthetic telemetry, setup and pipe lifecycle."}, indent=2),
            encoding="utf-8")
    finally:
        if process.poll() is None:
            job.terminate()
            process.wait(timeout=5)
        job.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
