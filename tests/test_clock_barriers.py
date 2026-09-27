# ruff: noqa: F401, F811
"""Causal receipt boundaries with synthetic game data and real durable stores."""

import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import threading
import time

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault, canonical, digest
from strata_evaluator.repair_clocks import RepairClockEvidence
from test_bound_clocks import (clock_source, sampled, fields_history, team_history, globals_history,
    clocked, history, native, reference, native_env, repair_env)
from test_telemetry_auth import signed, write

pytestmark = pytest.mark.parametrize("fields_history", [6], indirect=True)


def initial(e):
    e.body["records"] = 1
    e.persist()


def later(e, acknowledged):
    health = e.events[e.last - 2]
    assert health["kind"] == "server_health"
    health["payload"]["durable_event_seq_before_sample"] = acknowledged
    from pathlib import Path
    write(e.path, signed(e.broker.authority, Path(e.broker.authority.key_file).read_bytes(), e.events))
    e.body.update(records=e.last, clock_sample_cursor=e.last)
    e.persist()


def test_after_request_needs_strictly_newer_producer_receipt_and_preserves_deadline(clock_source):
    e = clock_source()
    initial(e)
    request = e.source.begin_barrier("a" * 64, {"owned": "repair-1"}, 10)
    assert request["receipt_cursor_after"] == 1
    for acknowledged in (0, 1):
        later(e, acknowledged)
        with pytest.raises(Fault, match="CLOCK_BARRIER_NOT_REACHED"):
            e.source.barrier_sample(request)
    # A later retry must retain the first threshold and deadline, even though
    # the durable stream and requested remaining window have both increased.
    assert e.source.begin_barrier("a" * 64, {"owned": "repair-1"}, 20) == request
    later(e, 2)
    observed = e.source.barrier_sample(request)
    assert observed["prefix"]["producer_receipt_cursor"] == 2
    assert observed["prefix"]["receipt_cursor_after"] == 1
    assert not observed["complete_repair_accounting"]
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        e.source.begin_barrier("a" * 64, {"owned": "other-repair"}, 10)
    with pytest.raises(Fault, match="CLOCK_BARRIER_CHANGED"):
        e.source.barrier_sample(request | {"receipt_cursor_after": 0})


def test_expired_request_cannot_be_rearmed_or_completed(clock_source, monkeypatch):
    e = clock_source()
    initial(e)
    request = e.source.begin_barrier("a" * 64, {}, 1)
    later(e, 2)
    monkeypatch.setattr(time, "monotonic", lambda: request["deadline_mono"] + 0.1)
    for operation in (lambda: e.source.begin_barrier("a" * 64, {}, 10),
                      lambda: e.source.barrier_sample(request)):
        with pytest.raises(Fault, match="CLOCK_BARRIER_EXPIRED"):
            operation()


@pytest.mark.parametrize("change", ["file_transport", "future_receipt", "deadline_during_read"])
def test_receipt_barrier_rejects_wrong_transport_future_ack_and_expired_read(clock_source, monkeypatch, change):
    e = clock_source()
    initial(e)
    request = e.source.begin_barrier("a" * 64, {}, 10)
    if change == "file_transport":
        e.events[0]["payload"]["telemetry_transport"] = "private-file/1"
    later(e, e.last if change == "future_receipt" else 2)
    if change == "deadline_during_read":
        original = e.source.observe
        def delayed(*args, **kwargs):
            result = original(*args, **kwargs)
            monkeypatch.setattr(time, "monotonic", lambda: request["deadline_mono"] + 0.1)
            return result
        monkeypatch.setattr(e.source, "observe", delayed)
    with pytest.raises(Fault, match="CLOCK_BARRIER_TRANSPORT|TELEMETRY_CLOCK_MISMATCH|CLOCK_BARRIER_EXPIRED"):
        e.source.barrier_sample(request)


def test_checkpoint_waiting_for_writer_does_not_extend_original_remaining_time(clock_source, monkeypatch):
    e = clock_source()
    initial(e)
    original = e.source._live
    now = time.monotonic()
    times = iter([now, now + 2])
    monkeypatch.setattr(time, "monotonic", lambda: next(times))
    monkeypatch.setattr(e.source, "_live", lambda cursor: (e.body, e.body["binding"]))
    with pytest.raises(Fault, match="CLOCK_BARRIER_EXPIRED"):
        e.source.begin_barrier("a" * 64, {}, 1)
    monkeypatch.setattr(e.source, "_live", original)


def test_barrier_request_orders_against_the_actual_sqlite_durable_writer(clock_source):
    e = clock_source()
    initial(e)
    locked, release, result = threading.Event(), threading.Event(), []
    def writer():
        with sqlite3.connect(e.broker.database_path) as db:
            db.execute("BEGIN IMMEDIATE")
            body = e.body | {"records": 2}
            db.execute("UPDATE telemetry_pipe_boots SET body=? WHERE authority=?",
                       (canonical(body).decode(), e.broker.authority.fingerprint()))
            locked.set()
            assert release.wait(2)
    thread = threading.Thread(target=writer)
    thread.start()
    assert locked.wait(2)
    def checkpoint():
        try:
            result.append(e.source.begin_barrier("b" * 64, {}, 10))
        except BaseException as error:
            result.append(error)
    reader = threading.Thread(target=checkpoint)
    reader.start()
    try:
        # Request is blocked by an already held actual database writer lock.
        assert reader.is_alive()
    finally:
        release.set()
        thread.join(2)
        reader.join(2)
    assert not thread.is_alive() and not reader.is_alive()
    assert len(result) == 1 and isinstance(result[0], dict), result
    assert result[0]["receipt_cursor_after"] == 2


def test_controller_barrier_binds_original_repair_and_never_grants_completion(clock_source, native_env, monkeypatch):
    from test_craft_reference import ACTOR
    e, worker, client, target, _, _, _, _ = native_env
    source = clock_source(campaign="c1", roster={"a1": ACTOR, "a2": "22222222-2222-2222-2222-222222222222"})
    initial(source)
    body = hashlib.sha256(("127.0.0.1:25569\n" + ACTOR).encode()).hexdigest()
    original = client.call
    def native_call(*args, **kwargs):
        result = original(*args, **kwargs)
        if "body_fingerprint" in result:
            result["body_fingerprint"] = body
        return result
    monkeypatch.setattr(client, "call", native_call)
    monkeypatch.setattr(NativeGameClient, "call", lambda *args, **kwargs: {
        "schema": "strata/NativeGameIdentity/1", "body_fingerprint": body, "connection_generation": 1})
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target.model_copy(update={"body_fingerprint": body}))
    service = RepairClockEvidence(e.repairs)
    budget = e.budgets.status("a1")
    put = service.flow._put
    def unavailable(value):
        raise OSError("synthetic CAS unavailable after durable source request")
    monkeypatch.setattr(service.flow, "_put", unavailable)
    with pytest.raises(OSError, match="synthetic CAS"):
        service.request_barrier("tx", "closed", "owner", e.epoch, worker, client, source.source)
    assert e.database.connection.execute("SELECT count(*) FROM repair_clock_barriers").fetchone()[0] == 0
    persisted = source.broker.database_path
    with sqlite3.connect(persisted) as db:
        durable = json.loads(db.execute("SELECT body FROM telemetry_clock_barriers").fetchone()[0])
    source.body["records"] = 2
    source.persist()
    monkeypatch.setattr(service.flow, "_put", put)
    request = service.request_barrier("tx", "closed", "owner", e.epoch, worker, client, source.source)
    assert e.controller.evidence(request["request_ref"]) == durable
    assert service.request_barrier("tx", "closed", "owner", e.epoch, worker, client, source.source) == request
    later(source, 1)
    with pytest.raises(Fault, match="CLOCK_BARRIER_NOT_REACHED"):
        service.capture("tx", "closed", "owner", e.epoch, worker, client, source.source)
    assert e.database.connection.execute("SELECT count(*) FROM repair_clock_marks").fetchone()[0] == 0
    later(source, 2)
    result = service.capture("tx", "closed", "owner", e.epoch, worker, client, source.source)
    receipt = e.controller.evidence(result["source_ref"])
    assert receipt["barrier_request_ref"] == request["request_ref"]
    assert receipt["sample_generation_after_request_proven"]
    assert not receipt["sample_generation_after_read_start_proven"]
    assert not receipt["consumption_settled"] and not receipt["campaign_permission_published"]
    assert service.capture("tx", "closed", "owner", e.epoch, worker, client, source.source) == result
    assert e.budgets.status("a1") == budget
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    assert e.repairs.status("tx")["phase"] == "RECONFIGURING"
    other = service.request_barrier("tx", "other-mark", "owner", e.epoch, worker, client, source.source)
    # A valid CAS reference and valid source request for a different mark must
    # not certify this repair boundary if a persisted join is corrupted.
    with e.database.transaction() as db:
        db.execute("UPDATE repair_clock_barriers SET request_ref=? WHERE repair=? AND mark=?",
                   (other["request_ref"], "tx", "closed"))
    with pytest.raises(Fault, match="REPAIR_CLOCK_SCOPE"):
        service.capture("tx", "closed", "owner", e.epoch, worker, client, source.source)


@pytest.mark.parametrize("charge_repair", [False, True, "body"])
def test_actual_jvm_pipe_receipt_precedes_causal_sample(sampled, tmp_path, monkeypatch, native_env, charge_repair):
    """Actual Java/Python pipe and held job; fixture bypasses token qualification."""
    from mcbench.processes import WindowsJob
    from strata_evaluator.bound_clocks import BoundClockSource
    from strata_evaluator.craft_reference import parse_plan
    from strata_evaluator.reference_launch import ReferenceLaunchPlan
    from strata_evaluator.telemetry_auth import parse_authority
    from strata_evaluator.telemetry_pipe import TelemetryPipeBroker
    from test_private_pipe import SCOPE
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    group = os.environ.get("STRATA_WRITER_TEST_GROUP")
    if os.name != "nt" or not java or not classpath or not group:
        pytest.skip("Explicit Windows Java/classpath and existing local group required")
    fixture, _, _ = sampled
    store, setup, events, directory, _ = fixture
    if charge_repair:
        from test_craft_reference import ACTOR
        e, worker, client, target, *_ = native_env
        setup["campaign_id"] = "c1"
        setup["roster"] = {"a1": ACTOR, "a2": "22222222-2222-2222-2222-222222222222"}
        setup["predicate"]["actors"] = list(setup["roster"].values())
        setup["native_team_ids"] = dict.fromkeys(setup["roster"], next(iter(setup["native_team_ids"].values())))
        for event in events:
            event["campaign_id"] = "c1"
        body = hashlib.sha256(("127.0.0.1:25569\n" + ACTOR).encode()).hexdigest()
        original = client.call
        def native_call(*args, **kwargs):
            result = original(*args, **kwargs)
            if "body_fingerprint" in result:
                result["body_fingerprint"] = body
            return result
        monkeypatch.setattr(client, "call", native_call)
        monkeypatch.setattr(NativeGameClient, "call", lambda *args, **kwargs: {
            "schema": "strata/NativeGameIdentity/1", "body_fingerprint": body, "connection_generation": 1})
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target.model_copy(update={"body_fingerprint": body}))
        service = RepairClockEvidence(e.repairs)
    store.seal(setup, directory)  # Fresh authority, not the shared signed fixture claim.
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    module = tmp_path / "synthetic-module.jar"
    module.write_bytes(b"Synthetic launch identity; no Minecraft module")
    def pin(p):
        return {"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    plan = ReferenceLaunchPlan.model_validate({"schema": "strata/PrivateReferenceLaunch/1",
        "instance_id": setup["instance_id"], "setup_digest": digest(setup), "mode": "synthetic-fixture",
        "executable": pin(Path(java)), "module_file": pin(module),
        "immutable_files": [pin(Path(java)), pin(module)], "immutable_trees": [],
        "evidence_directory": str(tmp_path / "launch"), "server_port": 25569,
        "max_wall_s": 30, "ready_run_s": 1, "graceful_stop_s": 2})
    settings = {"schema": "strata/ForgeTelemetryBrokerSettings/1", "campaign_id": authority.campaign_id,
        "epoch": authority.epoch, "max_bytes": 1024**2, "max_events": 100,
        "recipe_ids": list(setup["recipe_digests"]), "config_queries": []}
    # _serve resolves its peer method before blocking in accept; install this
    # explicit fixture seam before the broker thread starts.
    monkeypatch.setattr(TelemetryPipeBroker, "_peer", lambda self, pid: fixture_peer(pid))
    broker = TelemetryPipeBroker(store.database, authority, tmp_path / "actual-pipe-spool", plan, parse_plan(setup),
        writer_sid="fixture-token-unqualified", group_sid=group, scope_sid=SCOPE,
        deadline=time.monotonic() + 30, settings=settings)
    descriptor = tmp_path / "pipe-config.json"
    descriptor.write_bytes(canonical(broker.descriptor))
    start = copy.deepcopy(events[0]["payload"])
    start["telemetry_transport"] = "windows-owned-pipe/1"
    start["launch_identity"].update(game_directory=setup["game_directory"],
        world_directory=setup["fixture_directory"], module_file=str(module))
    startup = tmp_path / "start.json"
    startup.write_bytes(canonical(start))
    job, process, reader = WindowsJob(), None, None
    output = queue.Queue()
    try:
        process = subprocess.Popen([java, "-cp", Path(classpath).read_text(encoding="utf-8"),
            "io.github.opencnid.strata.telemetry.CausalClockFixture", str(descriptor), str(startup)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        job.attach(process)
        job.observe_members()
        identity = job.member_identity(process.pid)
        def fixture_peer(pid):
            assert pid == process.pid
            assert job.member_identity(pid) == identity
            broker._record("BOUND", peer=identity, token={"fixture_token_qualification": False})
            return identity
        monkeypatch.setattr(broker, "_peer", fixture_peer)
        broker.bind(job)
        reader = threading.Thread(target=lambda: [output.put(line.strip()) for line in process.stdout], daemon=True)
        reader.start()
        def command(value):
            process.stdin.write(value + "\n")
            process.stdin.flush()
        command("start")
        assert output.get(timeout=10) == "ready"
        source = BoundClockSource(broker)
        request = source.begin_barrier("d" * 64, {"fixture": "causal-pipe"}, 10)
        if charge_repair:
            service.request_barrier("tx", "opening", "owner", e.epoch, worker, client, source)
        assert request["receipt_cursor_after"] == 1
        sample_command = "sample " + ACTOR if charge_repair else "sample"
        command(sample_command)
        assert output.get(timeout=5) == "3"
        with pytest.raises(Fault, match="CLOCK_BARRIER_NOT_REACHED"):
            source.barrier_sample(request)
        command(sample_command)
        assert output.get(timeout=5) == "5"
        proof = source.barrier_sample(request)
        assert proof["prefix"]["producer_receipt_cursor"] == 3
        assert proof["prefix"]["receipt_cursor_after"] == 1
        assert proof["prefix"]["clock"]["completed_server_ticks"] == 2
        assert proof["is_example"] and not proof["process_isolation_qualified"]
        assert process.poll() is None
        if charge_repair == "body":
            from strata_evaluator.body_ticks import BodyTicks
            from test_body_ticks import allocations
            body_ticks = BodyTicks(e.controller)
            body_ticks.open("body", "c1", "owner", e.epoch, source, 5, allocations(e, bound=1))
            command(sample_command)
            assert output.get(timeout=5) == "7"
            first_ticks = body_ticks.advance("body", "owner", e.epoch, source, 7)
            assert first_ticks["avatar_ticks"] == {"a1": 1, "a2": 0}
            assert body_ticks.advance("body", "owner", e.epoch, source, 7) == first_ticks
            command(sample_command)
            assert output.get(timeout=5) == "9"
            for _ in range(2):
                with pytest.raises(Fault, match="BUDGET_EXHAUSTED"):
                    body_ticks.advance("body", "owner", e.epoch, source, 9)
            floors = e.budgets.consumption_floors(e.database.connection)
            assert floors["body-a1"]["avatar_ticks"] == 2 and floors["body-a2"]["avatar_ticks"] == 0
            assert floors.get("repair-op", {}).get("avatar_ticks", 0) == 0
            assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
            (tmp_path / "actual-continuous-body-ticks.json").write_bytes(canonical({"first": first_ticks,
                "floors": floors, "repair_coverage_claimed": False, "complete_repair_accounting": False}))
        elif charge_repair:
            service.capture("tx", "opening", "owner", e.epoch, worker, client, source)
            service.request_barrier("tx", "closing", "owner", e.epoch, worker, client, source)
            for cursor in (7, 9):
                command(sample_command)
                assert output.get(timeout=5) == str(cursor)
            service.capture("tx", "closing", "owner", e.epoch, worker, client, source)
            with pytest.raises(Fault, match="REPAIR_BUDGET_EXHAUSTED"):
                service.retain_consumption("tx", "opening", "closing", "owner", e.epoch, worker, client, source)
            assert e.budgets.status("a1")["committed_and_reserved"]["avatar_ticks"] == 2
            assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
            observed = json.loads(e.database.connection.execute("SELECT body FROM repair_clock_consumption").fetchone()[0])
            assert observed["avatar_ticks"] == observed["server_ticks"] == 2
            (tmp_path / "actual-tick-consumption.json").write_bytes(canonical(observed))
        command("stop")
        assert process.wait(timeout=5) == 0
        assert broker.close()["status"] == "stopped"
        (tmp_path / "actual-causal-pipe-proof.json").write_bytes(canonical({"request": request, "proof": proof,
            "terminal": broker.body, "exit_code": 0,
            "scope": "Actual pipe, production spool/clock, held JVM; synthetic game/setup and token qualification."}))
    finally:
        if process is not None and process.poll() is None:
            job.terminate()
            process.wait(timeout=5)
        broker.close()
        job.close()
        if reader is not None:
            reader.join(2)
        if process is not None:
            error = process.stderr.read()
            if error:
                print(error)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
