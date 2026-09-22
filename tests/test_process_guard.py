"""Windows guard faults against disposable JVMs; no Minecraft/desktop launch."""

import contextlib
import io
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from mcbench.process_guard import (
    AttachedJava, GuardPipes, HeldProcess, ProcessGuardGrant, inspect_process, read_grant,
)
from mcbench.storage import Fault

REPOSITORY = Path(__file__).resolve().parents[1]


def lines(stream):
    output = queue.Queue()

    def read():
        for line in stream:
            output.put(line)
    threading.Thread(target=read, daemon=True).start()
    return output


@pytest.fixture
def jvm_factory(tmp_path):
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    classpath = os.environ.get("STRATA_CLIENT_TEST_CLASSPATH")
    if os.name != "nt" or not java or not classpath:
        pytest.skip("explicit pinned Java/classpath and Windows required")
    count = 0

    @contextlib.contextmanager
    def launch():
        nonlocal count
        count += 1
        argfile = tmp_path / f"args-{count}.txt"
        arguments = ["-cp", Path(classpath).read_text().strip(),
                     "io.github.opencnid.strata.client.ProcessGuardFixture"]
        argfile.write_text("\n".join('"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
                                     for x in arguments), encoding="utf-8")
        proc = subprocess.Popen([java, "@" + str(argfile)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        output = lines(proc.stdout)
        try:
            assert output.get(timeout=15).strip() == b"ready"
            yield proc, output
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                stream.close()
    return launch


def grant_for(proc, **changes):
    return ProcessGuardGrant.model_validate({"schema": "strata/JavaProcessGuardGrant/1",
        "purpose": "dedicated-development-client-lifetime", "campaign_id": "synthetic-campaign",
        "agent_id": "synthetic-avatar", "epoch": 1,
        "process": inspect_process(proc.pid).model_dump(),
        "expires_unix_ms": time.time_ns() // 1000000 + 60000, "max_wall_ms": 10000, **changes})


@contextlib.contextmanager
def guardian(tmp_path, grant, module="mcbench.process_guard"):
    path = tmp_path / "private-process-grant.json"
    path.write_text(grant.model_dump_json(by_alias=True), encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-I", "-m", module, "--grant", str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW)
    output = lines(proc.stdout)
    try:
        ready = json.loads(output.get(timeout=10))
        assert ready["kind"] == "ready", ready
        assert ready["campaign_admission"] is False
        yield proc, output
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            stream.close()


def send(proc, value):
    proc.stdin.write(json.dumps(value).encode() + b"\n")
    proc.stdin.flush()


def event(output, kind):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        item = json.loads(output.get(timeout=max(.01, until - time.monotonic())))
        if item["kind"] == kind:
            return item
    pytest.fail("missing guard event")


def reply(proc, challenge):
    send(proc, {"kind": "renew", "seq": challenge["seq"], "nonce": challenge["nonce"]})


def test_inspection_and_wrong_identity_cannot_terminate_java(jvm_factory):
    with jvm_factory() as (proc, _):
        identity = inspect_process(proc.pid)
        assert int(identity.created_filetime) > 2**53
        assert set(identity.model_dump()) == {"pid", "created_filetime", "executable_path", "executable_sha256"}
        for patch in [{"created_filetime": str(int(identity.created_filetime) + 1)},
                      {"executable_sha256": "0" * 64}, {"executable_path": "C:\\wrong\\java.exe"}]:
            with pytest.raises(Fault, match="PROCESS_IDENTITY_MISMATCH"):
                AttachedJava(identity.model_copy(update=patch))
            assert proc.poll() is None


@pytest.mark.skipif(os.name != "nt", reason="Windows handles required")
def test_non_java_process_cannot_be_attached():
    with pytest.raises(Fault, match="PROCESS_NOT_JAVA"):
        AttachedJava(inspect_process(os.getpid()))


def test_stale_grant_after_exit_does_not_attach_replacement(jvm_factory):
    with jvm_factory() as (old, _):
        identity = inspect_process(old.pid)
        held = HeldProcess(old.pid)
        try:
            old.kill()
            old.wait(timeout=5)
            assert held.exited()
            with pytest.raises(Fault, match="PROCESS_NOT_RUNNING|PROCESS_IDENTITY_UNAVAILABLE"):
                AttachedJava(identity)
            with jvm_factory() as (new, _):
                with pytest.raises(Fault, match="PROCESS_IDENTITY_MISMATCH"):
                    AttachedJava(identity.model_copy(update={"pid": new.pid}))
                assert new.poll() is None
                assert held.exited()  # Held identity stays the old process, never the replacement.
        finally:
            held.close()


def test_second_guard_and_expired_attachment_do_not_disturb_existing_owner(jvm_factory):
    with jvm_factory() as (java, _):
        identity = inspect_process(java.pid)
        with pytest.raises(Fault, match="PROCESS_GRANT_EXPIRED"):
            AttachedJava(identity, deadline=time.monotonic() - 1)
        assert java.poll() is None
        owner = AttachedJava(identity)
        try:
            with pytest.raises(Fault, match="PROCESS_GUARD_OWNED"):
                AttachedJava(identity)
            assert java.poll() is None
        finally:
            owner.close()
            java.wait(timeout=2)


def test_guard_notices_normal_process_exit_without_claiming_input_release(jvm_factory, tmp_path):
    with jvm_factory() as (java, _):
        with guardian(tmp_path, grant_for(java)) as (guard, events):
            reply(guard, event(events, "challenge"))
            java.stdin.write(b"stop\n")
            java.stdin.flush()
            assert java.wait(timeout=2) == 0
            stopped = event(events, "stopped")
            assert stopped["reason"] == "PROCESS_EXITED"
            assert stopped["termination_confirmed"] and not stopped["release_confirmed"]
            assert guard.wait(timeout=5) == 0


def test_strict_private_grant_expiry_bounds_and_repository_exclusion(jvm_factory, tmp_path):
    with jvm_factory() as (proc, _):
        grant = grant_for(proc)
        path = tmp_path / "grant.json"
        raw = grant.model_dump(by_alias=True)
        path.write_text(json.dumps(raw))
        assert read_grant(path, REPOSITORY) == grant
        for patch, code in [({"expires_unix_ms": 1}, "PROCESS_GRANT_EXPIRED"),
                            ({"expires_unix_ms": time.time_ns() // 1000000 + 700000}, "PROCESS_GRANT_EXPIRED"),
                            ({"max_wall_ms": 600001}, "PROCESS_GRANT_INVALID"),
                            ({"epoch": True}, "PROCESS_GRANT_INVALID"),
                            ({"purpose": "attach-personal-game"}, "PROCESS_GRANT_INVALID"),
                            ({"extra": "hidden"}, "PROCESS_GRANT_INVALID")]:
            path.write_text(json.dumps({**raw, **patch}))
            with pytest.raises(Fault, match=code):
                read_grant(path, REPOSITORY)
        path.write_text(json.dumps(raw)[:-1] + ',"epoch":1}')
        with pytest.raises(Fault, match="PROCESS_GRANT_INVALID"):
            read_grant(path, REPOSITORY)
        path.write_bytes(b" " * 8193)
        with pytest.raises(Fault, match="PROCESS_GRANT_QUOTA"):
            read_grant(path, REPOSITORY)
        with pytest.raises(Fault, match="FORBIDDEN"):
            read_grant(path, tmp_path)
        assert proc.poll() is None


def test_hung_java_and_silent_supervisor_terminate_within_watchdog_bound(jvm_factory, tmp_path,
                                                                     record_property):
    with jvm_factory() as (java, output):
        java.stdin.write(b"hang\n")
        java.stdin.flush()
        assert output.get(timeout=5).strip() == b"hung"
        with guardian(tmp_path, grant_for(java)) as (guard, events):
            event(events, "challenge")
            started = time.monotonic()
            java.wait(timeout=2.25)
            elapsed = time.monotonic() - started
            record_property("challenge_to_process_exit_ms", round(elapsed * 1000, 3))
            assert elapsed < 2.25
            stopped = event(events, "stopped")
            assert stopped["reason"] == "PROCESS_LEASE_EXPIRED"
            assert stopped["termination_confirmed"] and not stopped["release_confirmed"]
            assert stopped["requires_resync"]
            record_property("termination_wait_ms", stopped["termination_wait_ms"])
            assert guard.wait(timeout=5) == 1


@pytest.mark.parametrize("failure", ["eof", "crash", "invalid", "replay", "oversize"])
def test_guard_pipe_faults_or_guard_crash_terminate_only_owned_client(jvm_factory, tmp_path, failure,
                                                                   record_property):
    with jvm_factory() as (java, _), jvm_factory() as (sibling, _):
        with guardian(tmp_path, grant_for(java)) as (guard, events):
            challenge = event(events, "challenge")
            if failure == "replay":
                reply(guard, challenge)
                event(events, "challenge")
            started = time.monotonic()
            if failure == "eof":
                guard.stdin.close()
            elif failure == "crash":
                guard.kill()
            elif failure == "oversize":
                guard.stdin.write(b"x" * 1025 + b"\n")
                guard.stdin.flush()
            elif failure == "replay":
                reply(guard, challenge)
            else:
                send(guard, {"kind": "renew", "seq": True, "nonce": challenge["nonce"]})
            # Kernel kill-on-job-close may report exit code zero. Process exit
            # proves termination only, never clean game/input shutdown.
            java.wait(timeout=2.25)
            elapsed = time.monotonic() - started
            record_property("fault_to_process_exit_ms", round(elapsed * 1000, 3))
            assert elapsed < 2.25
            assert sibling.poll() is None
            assert guard.wait(timeout=5) != 0


def test_fresh_challenges_keep_client_alive_then_explicit_stop_terminates(jvm_factory, tmp_path):
    with jvm_factory() as (java, _):
        with guardian(tmp_path, grant_for(java)) as (guard, events):
            nonces = set()
            for _ in range(9):
                challenge = event(events, "challenge")
                assert challenge["nonce"] not in nonces
                nonces.add(challenge["nonce"])
                reply(guard, challenge)
                assert java.poll() is None
            send(guard, {"kind": "stop"})
            stopped = event(events, "stopped")
            assert stopped["reason"] == "PROCESS_STOP_REQUESTED"
            assert stopped["termination_confirmed"] and not stopped["release_confirmed"]
            assert guard.wait(timeout=5) == 0
            java.wait(timeout=2)


@pytest.mark.parametrize("limit", ["wall", "grant"])
def test_renewal_cannot_extend_immutable_wall_or_authority_limit(jvm_factory, tmp_path, limit):
    with jvm_factory() as (java, _):
        change = {"max_wall_ms": 1200} if limit == "wall" else {
            "expires_unix_ms": time.time_ns() // 1000000 + 2000}
        with guardian(tmp_path, grant_for(java, **change)) as (guard, events):
            while True:
                item = json.loads(events.get(timeout=5))
                if item["kind"] == "challenge":
                    reply(guard, item)
                else:
                    assert item["kind"] == "stopped"
                    assert item["reason"] == "PROCESS_WALL_LIMIT"
                    break
            assert guard.wait(timeout=5) == 1
            java.wait(timeout=2)


def test_post_attachment_descendant_is_reaped_without_late_effect(jvm_factory, tmp_path):
    marker = tmp_path / "late-effect"
    with jvm_factory() as (java, output):
        with guardian(tmp_path, grant_for(java)) as (guard, events):
            reply(guard, event(events, "challenge"))
            java.stdin.write(("spawn " + str(marker) + "\n").encode())
            java.stdin.flush()
            pid = int(output.get(timeout=5))
            child = HeldProcess(pid)
            try:
                until = time.monotonic() + 1
                while not Path(str(marker) + ".ready").exists() and time.monotonic() < until:
                    time.sleep(.01)
                assert Path(str(marker) + ".ready").exists()
                guard.kill()
                guard.wait(timeout=5)
                java.wait(timeout=2)
                assert child.exited(2000)
                time.sleep(2.1)
                assert not marker.exists()
            finally:
                child.close()


@pytest.mark.parametrize("root_exits_first", [False, True])
def test_confirmed_stop_observes_empty_owned_job(jvm_factory, tmp_path, record_property,
                                                root_exits_first):
    marker = tmp_path / "late-effect"
    with jvm_factory() as (java, output):
        target = AttachedJava(inspect_process(java.pid))
        child = None
        try:
            java.stdin.write(("spawn " + str(marker) + "\n").encode())
            java.stdin.flush()
            child = HeldProcess(int(output.get(timeout=5)))
            until = time.monotonic() + 1
            while not Path(str(marker) + ".ready").exists() and time.monotonic() < until:
                time.sleep(.01)
            assert Path(str(marker) + ".ready").exists()
            before = target.job.accounting()
            record_property("job_before_stop", json.dumps(before))
            # The owned job can include OS/runtime descendants besides both JVMs.
            assert before["active_processes"] >= 2
            if root_exits_first:
                java.stdin.write(b"stop\n")
                java.stdin.flush()
                assert java.wait(timeout=2) == 0
                assert not child.exited()
                remaining = target.job.accounting()
                record_property("job_after_root_exit", json.dumps(remaining))
                assert remaining["active_processes"] >= 1
            target.terminate()
            timing = target.termination_timing
            record_property("termination_timing", json.dumps(timing))
            assert timing["wait_result"] == "signaled" and timing["tree_result"] == "empty"
            assert timing["active_processes"] == target.job.accounting()["active_processes"] == 0
            assert timing["total_processes"] == timing["held_processes"] == timing["signaled_processes"]
            assert timing["held_processes"] == before["total_processes"]
            assert timing["tree_checked_after_ns"] - timing["wait_started_after_ns"] <= 500_000_000
            assert child.exited(0) and target.process.exited(0)
            time.sleep(2.1)
            assert not marker.exists()
        finally:
            target.close()
            if child:
                child.close()


def test_pipe_output_backpressure_cannot_block_guard_control_loop():
    blocked = threading.Event()

    class BlockedOutput:
        def write(self, value):
            blocked.wait(10)
        def flush(self):
            pass

    pipes = GuardPipes(io.BytesIO(b""), BlockedOutput())
    try:
        before = time.monotonic()
        with pytest.raises(Fault, match="PROCESS_GUARD_PIPE_FAILED"):
            for _ in range(20):
                pipes.emit({"kind": "synthetic"})
        assert time.monotonic() - before < .25
    finally:
        blocked.set()


def test_guard_failure_preserves_typed_fault_without_exception_text():
    from mcbench.process_guard import failure_event
    assert failure_event(Fault("PROCESS_STOP_UNCONFIRMED"))["reason"] == "PROCESS_STOP_UNCONFIRMED"
    for error in (RuntimeError("private token or path"), Fault("private token or path")):
        event = failure_event(error)
        assert event == {"schema": "strata/ProcessGuardEvent/1", "kind": "failed",
                         "reason": "PROCESS_GUARD_FAILURE", "termination_confirmed": False}


@pytest.mark.parametrize("stop_policy", ["java-tree500-lease1500/1", "java-tree1000-lease750/1"])
@pytest.mark.parametrize("outcome", ["signaled", "timeout", "error", "job_error"])
def test_stop_timing_preserves_faults_one_attempt_and_existing_wait(monkeypatch, outcome, stop_policy):
    import mcbench.process_guard as module
    wait_ms, _, policy = module.stop_settings(stop_policy)
    calls = []

    class Job:
        def observe_members(self):
            pass

        def member_status(self):
            return {"held_processes": 1, "signaled_processes": 1}

        def terminate(self):
            calls.append("terminate")
            if outcome == "job_error":
                raise Fault("PROCESS_STOP_FAILED")

        def accounting(self):
            calls.append("accounting")
            return {"active_processes": 0, "total_processes": 1}

    class Process:
        def exited(self, timeout):
            calls.append(("wait", timeout))
            if outcome == "error":
                raise Fault("PROCESS_STATE_UNAVAILABLE")
            return outcome == "signaled"

    target = AttachedJava.__new__(AttachedJava)
    target.job, target.process = Job(), Process()
    stamps = iter([100000000000, 100000000007, 100000000011, 100400000019, 100400000023])
    monkeypatch.setattr(module.time, "perf_counter_ns", lambda: next(stamps))
    errors = {"timeout": "PROCESS_STOP_UNCONFIRMED", "error": "PROCESS_STATE_UNAVAILABLE",
              "job_error": "PROCESS_STOP_FAILED"}
    if outcome == "signaled":
        target.terminate(stop_policy=stop_policy)
    else:
        with pytest.raises(Fault, match=errors[outcome]):
            target.terminate(stop_policy=stop_policy)
    timing = target.termination_timing
    assert timing["started_qpc_ns"] == "100000000000"
    assert timing["wait_bound_ms"] == wait_ms
    assert timing["job_returned_after_ns"] == 7
    assert timing["job_succeeded"] is (outcome != "job_error")
    expected = ["terminate"] if outcome == "job_error" else ["terminate", ("wait", wait_ms)]
    assert calls == expected + (["accounting"] if outcome == "signaled" else [])
    assert timing["policy"] == policy
    assert timing["wait_result"] == ("not_started" if outcome == "job_error" else outcome)
    assert timing["wait_started_after_ns"] == (None if outcome == "job_error" else 11)
    assert timing["wait_returned_after_ns"] == (None if outcome == "job_error" else 400000019)
    assert timing["tree_result"] == ("empty" if outcome == "signaled" else "not_started")
    assert timing["active_processes"] == (0 if outcome == "signaled" else None)
    assert timing["tree_checked_after_ns"] == (400000023 if outcome == "signaled" else None)


@pytest.mark.parametrize("stop_policy", ["java-tree500-lease1500/1", "java-tree1000-lease750/1"])
@pytest.mark.parametrize("case", ["drained", "lingering", "query_error", "invalid_count",
                                  "late_zero", "late_root", "unsignaled", "inventory_gap",
                                  "inventory_error", "member_error"])
def test_root_exit_requires_empty_owned_job_within_same_bound(monkeypatch, case, stop_policy):
    import mcbench.process_guard as module
    wait_ms, _, _ = module.stop_settings(stop_policy)
    limit_ns = wait_ms * 1_000_000
    elapsed = 0
    counts, calls, sleeps = [], [], []

    class Process:
        def exited(self, timeout):
            nonlocal elapsed
            calls.append(("wait", timeout))
            elapsed += limit_ns + 10_000_000 if case == "late_root" else limit_ns - 20_000_000
            return True

    class Job:
        def observe_members(self):
            if case == "inventory_error":
                raise Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")

        def member_status(self):
            if case == "member_error":
                raise Fault("PROCESS_STATE_UNAVAILABLE")
            return {"held_processes": 1, "signaled_processes": 0 if case == "unsignaled" else 1}

        def terminate(self):
            calls.append("terminate")

        def accounting(self):
            nonlocal elapsed
            calls.append("accounting")
            elapsed += 25_000_000 if case == "late_zero" else 1_000_000
            if case == "query_error":
                raise Fault("PROCESS_STATE_UNAVAILABLE")
            count = True if case == "invalid_count" else (
                0 if case in {"late_zero", "unsignaled", "inventory_gap"} or (case == "drained" and counts) else 1)
            counts.append(count)
            return {"active_processes": count, "total_processes": 2 if case == "inventory_gap" else 1}

    def sleep(seconds):
        nonlocal elapsed
        sleeps.append(seconds)
        elapsed += round(seconds * 1e9)

    monkeypatch.setattr(module.time, "perf_counter_ns", lambda: 100_000_000_000 + elapsed)
    monkeypatch.setattr(module.time, "sleep", sleep)
    target = AttachedJava.__new__(AttachedJava)
    target.job, target.process = Job(), Process()
    if case == "drained":
        target.terminate(stop_policy=stop_policy)
        assert counts == [1, 0]
    else:
        error = "PROCESS_STATE_UNAVAILABLE" if case in {"query_error", "invalid_count", "member_error"} else (
            "PROCESS_MEMBER_INVENTORY_UNAVAILABLE" if case == "inventory_error" else "PROCESS_STOP_UNCONFIRMED")
        with pytest.raises(Fault, match=error):
            target.terminate(stop_policy=stop_policy)
    timing = target.termination_timing
    assert calls.count("terminate") == 1 and calls.count(("wait", wait_ms)) == 1
    assert timing["wait_result"] == "signaled"
    expected = "empty" if case == "drained" else (
        "error" if case in {"query_error", "invalid_count", "inventory_error", "member_error"} else (
            "incomplete" if case == "inventory_gap" else "timeout"))
    assert timing["tree_result"] == expected
    if case == "lingering":
        assert elapsed == limit_ns and sum(sleeps) < .020
        assert timing["active_processes"] == 1
    if case == "late_root":
        assert "accounting" not in calls
    if case == "late_zero":
        assert timing["active_processes"] == 0  # Empty too late cannot pass.
    if case == "unsignaled":
        assert timing["active_processes"] == 0 and timing["signaled_processes"] == 0
        assert elapsed == limit_ns


@pytest.mark.parametrize("emit_fails", [False, True])
def test_timing_output_occurs_after_cleanup_even_when_wait_failed(monkeypatch, emit_fails):
    import mcbench.process_guard as module
    from types import SimpleNamespace
    calls = []

    class Target:
        termination_timing = {"wait_result": "timeout"}
        process = SimpleNamespace(exited=lambda: True)
        job = SimpleNamespace(observe_members=lambda: None)

        def __init__(self, *args, **kwargs):
            pass

        def terminate(self, **kwargs):
            calls.append("terminate")
            raise Fault("PROCESS_STOP_UNCONFIRMED")

        def close(self):
            calls.append("close")

    class Pipes:
        def emit(self, value):
            calls.append(value["kind"])
            if value["kind"] == "termination_timing" and emit_fails:
                raise Fault("PROCESS_GUARD_PIPE_FAILED")

    grant = SimpleNamespace(expires_unix_ms=time.time_ns() // 1000000 + 30000,
        max_wall_ms=10000, process=SimpleNamespace(model_dump=lambda: {}),
        campaign_id="synthetic", agent_id="avatar", epoch=1)
    monkeypatch.setattr(module, "AttachedJava", Target)
    expected = "PROCESS_GUARD_PIPE_FAILED" if emit_fails else "PROCESS_STOP_UNCONFIRMED"
    with pytest.raises(Fault, match=expected):
        module.guard(grant, Pipes(), termination_evidence=True)
    assert calls == ["ready", "terminate", "close", "termination_timing"]
