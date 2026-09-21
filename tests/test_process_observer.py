"""Independent exit waiting, incremental source tailing and durable resource failure evidence."""
# ruff: noqa: F811 -- pytest intentionally injects the imported fixture by name.

import json
import os
import threading
import time
from types import SimpleNamespace

import pytest

from mcbench import process_observer as observation
from mcbench.process_guard import AttachedJava, inspect_process
from mcbench.storage import Fault
from test_process_guard import jvm_factory  # noqa: F401


def event(seq):
    return (json.dumps({"schema": "strata/SupervisorEvent/1", "seq": seq, "kind": "fixture",
                       "source_clock_id": "fixture", "mono_ms": seq, "at": "fixture", "hash": "a" * 64}) + "\n").encode()


def test_incremental_journal_preserves_partial_line_and_rejects_truncation(tmp_path):
    observer = observation.ExitObserver.__new__(observation.ExitObserver)
    observer.journal = tmp_path / "source.jsonl"
    observer.source_offset = observer.last_seq = 0
    seen = []
    observer.sink = SimpleNamespace(emit=lambda kind, **record: seen.append(record["source_seq"]))
    first, second = event(1), event(2)
    observer.journal.write_bytes(first + second[:20])
    observer.journal_events()
    assert observer.source_offset == len(first) and seen == [1]
    with observer.journal.open("ab") as stream:
        stream.write(second[20:])
    observer.journal_events()
    observer.journal_events()
    assert observer.source_offset == len(first + second) and seen == [1, 2]
    observer.journal.write_bytes(first)
    with pytest.raises(Fault, match="SUPERVISOR_QUOTA"):
        observer.journal_events()


def test_observation_file_is_exclusive_and_quota_cannot_overwrite_prior_record(tmp_path):
    path = tmp_path / "observer.jsonl"
    journal = observation.Journal(path, byte_limit=150)
    try:
        journal.emit("first")
        original = path.read_bytes()
        with pytest.raises(Fault, match="OBSERVER_QUOTA"):
            journal.emit("too_large", value="x" * 200)
        assert path.read_bytes() == original and journal.records == 1
        with pytest.raises(FileExistsError):
            observation.Journal(path)
    finally:
        journal.close()


@pytest.mark.skipif(os.name != "nt", reason="Native owned Java guardian with blocked metadata observer")
def test_blocked_resource_thread_cannot_delay_production_guardian(jvm_factory, tmp_path, monkeypatch, record_property):
    entered, release = threading.Event(), threading.Event()
    original = observation.ResourceProcess.snapshot
    def blocked(self):
        entered.set()
        assert release.wait(10)
        return original(self)
    monkeypatch.setattr(observation.ResourceProcess, "snapshot", blocked)
    with jvm_factory() as (java, _):
        identity = inspect_process(java.pid)
        observer = observation.ExitObserver(java.pid, tmp_path / "source.jsonl", tmp_path / "exit.jsonl",
                                            expected_identity=identity)
        guardian = None
        try:
            assert entered.wait(5)
            guardian = AttachedJava(identity)
            guardian.terminate()
            record_property("guardian_timing", json.dumps(guardian.termination_timing))
            assert guardian.termination_timing["tree_result"] == "empty" and not release.is_set()
            until = time.monotonic() + 2
            while not observer.summary["exited"] and time.monotonic() < until:
                time.sleep(.01)
            assert observer.summary["exited"]  # Exit wait progresses while metadata is blocked.
            began = time.monotonic()
            pending = observer.finish()
            assert time.monotonic() - began < 2.5
            assert pending["status"] == "fail" and pending["error_code"] == "OBSERVER_JOIN_TIMEOUT"
            release.set()
            observer.resources.thread.join(3)
            final = observer.finish()
            assert final["status"] == "fail" and final["error_code"] == "OBSERVER_JOIN_TIMEOUT"
            assert final["resources"]["samples"] == 1 and final["resources"]["status"] == "pass"
            values = [json.loads(x) for x in (tmp_path / "exit-resources.jsonl").read_text().splitlines()]
            assert values[0]["observation"]["signaled_before"]
        finally:
            release.set()
            observer.finish()
            if guardian:
                guardian.close()


def test_resource_handle_failure_does_not_skip_durable_journal_close(tmp_path, monkeypatch):
    def close():
        raise OSError("synthetic close failure")
    value = {"signaled_before": True, "signaled_after": True, "regions": {"status": "not_run"},
             "within_query_budget": True, "counters": {}}
    monkeypatch.setattr(observation, "ResourceProcess", lambda _: SimpleNamespace(snapshot=lambda: value, close=close))
    collector = observation.ResourceCollector(None, tmp_path / "resources.jsonl", threading.Event(),
                                              time.perf_counter_ns() + 1_000_000_000)
    collector.start()
    collector.thread.join(2)
    assert not collector.thread.is_alive()
    assert collector.summary["status"] == "fail"
    assert collector.summary["error_code"] == "RESOURCE_HANDLE_CLOSE_FAILED"
    assert collector.summary["records"] == 1 and collector.summary["bytes"] > 0
    assert json.loads((tmp_path / "resources.jsonl").read_bytes())["observation"] == value


def test_late_wait_thread_cannot_erase_a_previous_finish_timeout():
    alive = {"value": True}
    observer = observation.ExitObserver.__new__(observation.ExitObserver)
    observer.stop, observer.finish_fault = threading.Event(), None
    observer.summary = {"status": "fail", "exited": False}
    observer.records = observer.bytes = observer.max_wait_span_ns = 0
    observer.thread = SimpleNamespace(join=lambda _: None, is_alive=lambda: alive["value"])
    observer.resources = SimpleNamespace(started=False, summary={"status": "pass"})
    assert observer.finish()["error_code"] == "OBSERVER_JOIN_TIMEOUT"
    # Model the wait thread returning after the bounded finish already failed.
    alive["value"] = False
    observer.summary.update(status="pass", exited=True)
    result = observer.finish()
    assert result["status"] == "fail" and result["error_code"] == "OBSERVER_JOIN_TIMEOUT" and result["exited"]


@pytest.mark.parametrize("mode,counters,censuses", [
    ("complete", 1, 1), ("partial", 1, 0), ("counter_error", 0, 0), ("terminal", 0, 0)])
def test_observer_lifecycle_never_conflates_partial_region_and_counter_evidence(tmp_path, mode, counters, censuses):
    value = {"signaled_before": mode == "terminal", "signaled_after": mode == "terminal",
             "regions": {"status": "partial" if mode == "partial" else "complete"},
             "counter_elapsed_ns": 1000, "within_query_budget": mode != "partial",
             "counters": {"memory_error": 5} if mode == "counter_error" else {}}
    collector = observation.ResourceCollector(None, tmp_path / "unused", threading.Event(), 0)
    reader = SimpleNamespace(snapshot=lambda: value)
    journal = SimpleNamespace(emit=lambda *args, **kwargs: None)
    assert collector.observe(reader, journal, "fixture") == (mode == "terminal")
    assert collector.summary["complete_counter_samples"] == counters
    assert collector.summary["complete_region_censuses"] == censuses
    assert collector.summary["partial_region_samples"] == 1 - censuses
    assert collector.summary["status"] == "fail"  # A sample alone cannot close the lifecycle.
