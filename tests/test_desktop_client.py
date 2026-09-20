"""Independent guardian attached to a fresh non-input desktop's disposable JVM."""
import json
import os
from pathlib import Path
import time
import queue
import threading

import pytest

from mcbench.desktop_client import DesktopJava
from mcbench.desktop_process import DesktopApi
from mcbench.process_guard import HeldProcess
from mcbench.storage import Fault


@pytest.fixture
def launch(tmp_path):
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    if os.name != "nt" or not java:
        pytest.skip("explicit Windows Java required")
    fixture = Path(__file__).parent / "fixtures/DesktopLifetimeFixture.java"
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    count = 0

    def start():
        nonlocal count
        count += 1
        root = tmp_path / str(count)
        root.mkdir()
        ready = root / "fixture.ready"
        process = DesktopJava([java, str(fixture), str(ready)], root, env, root, max_wall_ms=20000)
        until = time.monotonic() + 10
        try:
            while not ready.exists():
                process.pump()
                assert time.monotonic() < until
                time.sleep(.02)
        except BaseException:
            process.close()
            raise
        return process, root
    return start


def test_guarded_java_start_and_stop_leave_input_desktop_unchanged(launch):
    before = DesktopApi().input_name()
    process, root = launch()
    assert process.ready and process.sequence >= 1
    held = HeldProcess(process.child.pid)
    try:
        process.pump()
        process.close()
        assert held.exited(2000)
        assert process.terminal["reason"] == "PROCESS_STOP_REQUESTED"
        assert not process.terminal["release_confirmed"]
        assert DesktopApi().input_name() == before
        events = [json.loads(line) for line in (root / "launch.jsonl").read_text().splitlines()]
        assert [e["kind"] for e in events] == ["launch_intent", "ready", "launch_ready", "stopped"]
        assert not any("nonce" in e for e in events)
        process.close()
    finally:
        held.close()
        if not process.closed:
            process.close()


def test_stalled_caller_cannot_renew_independent_guardian(launch):
    process, _ = launch()
    held = HeldProcess(process.child.pid)
    try:
        # No pumping during a blocked caller: independent process must stop Java.
        assert held.exited(4000)
        process.pump(stopping=True)
        process.close()
        assert process.terminal["reason"] == "PROCESS_LEASE_EXPIRED"
    finally:
        held.close()
        if not process.closed:
            process.close()


def test_guardian_crash_stops_java_and_is_not_success(launch):
    process, _ = launch()
    held = HeldProcess(process.child.pid)
    try:
        process.guard.stop()
        assert held.exited(2000)
        with pytest.raises(Fault, match="PROCESS_GUARD_EXITED"):
            process.pump()
        with pytest.raises(Fault, match="PROCESS_STOP_UNCONFIRMED"):
            process.close()
        assert process.closed and process.terminal is None
    finally:
        held.close()
        if not process.closed:
            process.close()


def test_private_startup_failure_leaves_no_child(tmp_path):
    with pytest.raises(Fault, match="PROCESS_NOT_JAVA"):
        DesktopJava(["not-a-java.exe"], tmp_path, {}, tmp_path, max_wall_ms=10000)
    with pytest.raises(Fault, match="INVALID_ARGUMENT"):
        DesktopJava(["java.exe"], tmp_path, {}, tmp_path, max_wall_ms=True)


def test_guard_failure_is_retained_without_claiming_confirmed_stop():
    from mcbench.process_guard import failure_event
    process = DesktopJava.__new__(DesktopJava)
    process.closed = False
    process.reader_failed = threading.Event()
    process.events = queue.Queue()
    process.terminal = process.failure = None
    records = []
    process.record = records.append
    failure = failure_event(Fault("PROCESS_STOP_UNCONFIRMED"))
    process.events.put(failure)
    with pytest.raises(Fault, match="PROCESS_GUARD_FAILED"):
        process.pump(stopping=True)
    assert records == [failure] and process.failure == failure
    assert process.terminal is None


def test_untrusted_failure_fields_are_not_copied_to_evidence():
    process = DesktopJava.__new__(DesktopJava)
    process.closed = False
    process.reader_failed = threading.Event()
    process.events = queue.Queue()
    records = []
    process.record = records.append
    process.events.put({"schema": "strata/ProcessGuardEvent/1", "kind": "failed",
                        "reason": "PROCESS_STOP_UNCONFIRMED", "termination_confirmed": False,
                        "private_data": "not authorized for journal"})
    with pytest.raises(Fault, match="PROCESS_GUARD_OUTPUT_INVALID"):
        process.pump(stopping=True)
    assert records == []
