# ruff: noqa: F401, F811
"""Signed synthetic clocks; no authentic game or settlement qualification."""

import copy
import json
import os
import queue
import subprocess
import threading
from pathlib import Path

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator.live_clocks import clock_prefix
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_transitions import module18
from test_script_field_history import fields_history, team_history, globals_history, clocked, history, native, reference
from test_setup_control import source
from test_setup_facts import renumber
from test_telemetry_pipe import sink
from test_telemetry_auth import signed, write
from strata_evaluator.telemetry_clocks import ServerClock, ServerClockSample

pytestmark = pytest.mark.parametrize("fields_history", [6], indirect=True)


@pytest.fixture
def sampled(fields_history):
    events = fields_history[2]
    module18(events)
    events[0]["payload_schema"] = "strata/ServerStarted/20"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.19",
        machine_interval_policy="thermal1192-native-furnace-server-tick/1",
        clock_sample_policy="server-event-monotonic-samples/1")
    terminal = next(e for e in events if e["kind"] == "server_clock")
    index = next(i for i, e in enumerate(events) if e["kind"] == "server_health")
    health = events[index]
    first = copy.deepcopy(health) | {"kind": "server_clock_sample", "payload_schema": "strata/ServerClockSample/1",
        "payload": {**copy.deepcopy(terminal["payload"]), "boundary": "server_tick_end_sample",
            "completed_server_ticks": health["server_tick"],
            "elapsed_wall_ns": health["payload"]["interval_wall_ns"] + 100_000,
            "observed_tick_work_ns": health["payload"]["observed_tick_work_ns"],
            "avatar_tick_events": {}}}
    events.insert(index + 1, first)
    # A second sample records real callback deltas in the fixture. The health
    # roster counts intentionally differ and cannot substitute for callbacks.
    second_health = copy.deepcopy(health)
    second_health["server_tick"] += 1
    second_health["payload"].update(interval_server_ticks=1, interval_wall_ns=100_000,
                                    observed_tick_work_ns=100)
    second = copy.deepcopy(first)
    second["server_tick"] = second_health["server_tick"]
    second["payload"].update(completed_server_ticks=second["server_tick"],
        elapsed_wall_ns=first["payload"]["elapsed_wall_ns"] + 100_000,
        observed_tick_work_ns=first["payload"]["observed_tick_work_ns"] + 100,
        avatar_tick_events={next(iter(terminal["payload"]["avatar_tick_events"])): 1})
    # Keep earlier craft events in their original order, before the new sample.
    terminal_index = events.index(terminal)
    events[terminal_index:terminal_index] = [second_health, second]
    renumber(events)
    return fields_history, first, second


def test_authenticated_prefix_needs_no_stop_and_does_not_promote_roster_counts(sampled, tmp_path):
    fixture, first, second = sampled
    _, authority, path, _ = source(fixture, tmp_path)
    complete = path.read_bytes()
    lines = complete.splitlines(keepends=True)
    path.write_bytes(b"".join(lines[:first["seq"]]))
    initial = clock_prefix(path, authority, first["seq"])
    assert initial["clock"]["avatar_tick_events"] == {}
    assert not initial["clean_stop"] and not initial["complete_repair_accounting"]
    with pytest.raises(Fault, match="TELEMETRY_CLEAN_STOP_MISSING"):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    path.write_bytes(b"".join(lines[:second["seq"]]))
    later = clock_prefix(path, authority, second["seq"])
    assert later["clock"]["completed_server_ticks"] - initial["clock"]["completed_server_ticks"] == 1
    assert sum(later["clock"]["avatar_tick_events"].values()) == 1
    assert not later["avatar_roster_mapping_qualified"] and not later["active_time_qualified"]
    assert clock_prefix(path, authority, first["seq"]) == initial
    path.write_bytes(complete)
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert report["clean_stop"] and report["kind_counts"]["server_clock_sample"] == 2


@pytest.mark.parametrize("change", ["legacy", "missing", "reordered", "ticks", "actor", "avatar_rollback",
    "work_rollback", "wall_rollback", "duplicate", "signature", "partial", "cursor"])
def test_prefix_rejects_unusable_clock_evidence(sampled, tmp_path, change):
    fixture, first, second = sampled
    events = fixture[2]
    if change == "legacy":
        events[0]["payload_schema"] = "strata/ServerStarted/19"
        events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.18")
        del events[0]["payload"]["clock_sample_policy"]
    elif change == "missing":
        events.remove(first)
    elif change == "reordered":
        index = events.index(second)
        events[index - 1], events[index] = events[index], events[index - 1]
    elif change == "ticks":
        second["payload"]["completed_server_ticks"] += 1
    elif change == "actor":
        second["actor_ids"] = ["unexpected"]
    elif change == "avatar_rollback":
        actor = next(iter(second["payload"]["avatar_tick_events"]))
        first["payload"]["avatar_tick_events"] = {actor: 2}
    elif change == "work_rollback":
        second["payload"]["observed_tick_work_ns"] = 0
    elif change == "wall_rollback":
        second["payload"]["elapsed_wall_ns"] = first["payload"]["elapsed_wall_ns"] - 1
    elif change == "duplicate":
        events.insert(events.index(first) + 1, copy.deepcopy(first))
    renumber(events)
    _, authority, path, _ = source(fixture, tmp_path)
    if change == "signature":
        raw = path.read_bytes().replace(b'"mac":"', b'"mac":"0', 1)
        path.write_bytes(raw)
    elif change == "partial":
        path.write_bytes(b"".join(path.read_bytes().splitlines(keepends=True)[:second["seq"]])[:-1])
    cursor = first["seq"] - 1 if change == "cursor" else second["seq"]
    with pytest.raises(ValueError):
        clock_prefix(path, authority, cursor)
    if change != "cursor":
        with pytest.raises(ValueError):
            inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_live_pipe_signs_samples_under_declared_profile_only(sink, sampled):
    fixture, first, _ = sampled
    broker, old_start, identity, key, replies, _ = sink
    start = copy.deepcopy(fixture[2][0])
    start["payload"]["launch_identity"] = old_start["payload"]["launch_identity"]
    start["payload"]["telemetry_transport"] = "windows-owned-pipe/1"
    broker._event(canonical(start) + b"\n", identity, key)
    health = copy.deepcopy(next(e for e in fixture[2] if e["kind"] == "server_health"))
    sample = copy.deepcopy(first)
    for seq, event in enumerate([health, sample], 2):
        event.update(seq=seq, server_event_seq=seq)
        broker._event(canonical(event) + b"\n", identity, key)
    assert broker.count == 3 and len(replies) == 3 and not broker.stopped
    with pytest.raises(Fault, match="TELEMETRY_CLOCK_SAMPLE_SCOPE"):
        sample.update(seq=4, server_event_seq=4)
        broker._event(canonical(sample) + b"\n", identity, key)


def test_actual_java_clock_prefix_is_readable_while_same_process_continues(sampled, tmp_path):
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if not java or not classpath:
        pytest.skip("Explicit pinned Java/classpath required")
    fixture, _, _ = sampled
    _, authority, path, _ = source(fixture, tmp_path)
    start = copy.deepcopy(fixture[2][0])
    events, previous, output = [start], None, queue.Queue()
    process = subprocess.Popen([java, "-cp", Path(classpath).read_text(encoding="utf-8"),
        "io.github.opencnid.strata.telemetry.LiveClockFixture"], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    reader = threading.Thread(target=lambda: [output.put(line) for line in process.stdout], daemon=True)
    reader.start()
    try:
        prefixes = []
        for command in ("connected", "disconnected", "connected"):
            process.stdin.write(command + "\n")
            process.stdin.flush()
            value = ServerClockSample.model_validate_json(output.get(timeout=5))
            assert process.poll() is None
            wall = value.elapsed_wall_ns - (previous.elapsed_wall_ns if previous else 0)
            work = value.observed_tick_work_ns - (previous.observed_tick_work_ns if previous else 0)
            health = copy.deepcopy(next(e for e in fixture[2] if e["kind"] == "server_health"))
            health.update(server_tick=value.completed_server_ticks)
            health["payload"].update(interval_server_ticks=1, interval_wall_ns=wall,
                observed_tick_work_ns=work, durable_event_seq_before_sample=len(events), avatar_ticks_since_boot={})
            sample = copy.deepcopy(health) | {"kind": "server_clock_sample",
                "payload_schema": "strata/ServerClockSample/1", "payload": value.model_dump()}
            events.extend([health, sample])
            renumber(events)
            write(path, signed(authority, Path(authority.key_file).read_bytes(), events))
            prefixes.append(clock_prefix(path, authority, len(events)))
            assert process.poll() is None
            previous = value
        assert [sum(p["clock"]["avatar_tick_events"].values()) for p in prefixes] == [1, 1, 2]
        assert [p["clock"]["completed_server_ticks"] for p in prefixes] == [1, 2, 3]
        assert all(not p["complete_repair_accounting"] and not p["clean_stop"] for p in prefixes)
        (tmp_path / "live-clock-prefixes.json").write_text(json.dumps(prefixes, indent=2), encoding="utf-8")
        process.stdin.write("stop\n")
        process.stdin.flush()
        terminal = ServerClock.model_validate_json(output.get(timeout=5))
        assert terminal.completed_server_ticks == 3
        assert process.wait(timeout=5) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=2)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
