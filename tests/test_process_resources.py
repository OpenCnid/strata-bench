"""Bounded metadata walks, identity failure, and actual owned JVM resource queries."""
# ruff: noqa: F811 -- pytest intentionally injects the imported fixture by name.

import ctypes
from ctypes import wintypes
import json
import os
from types import SimpleNamespace

import pytest

from mcbench import process_resources as resources
from mcbench.process_guard import ProcessIdentity, inspect_process
from mcbench.storage import Fault
from test_process_guard import jvm_factory  # noqa: F401


def region(base, size, state=0x1000, kind=0x20000, allocation=None):
    return {"base": base, "size": size, "state": state, "kind": kind,
            "allocation": base if allocation is None else allocation}


def test_nonatomic_walk_clips_coalesced_regions_without_exporting_addresses():
    values = {0: region(0, 4096, 0x10000, 123, -1), 4096: region(4096, 4096, 0x2000),
        8192: region(8192, 8192, allocation=4096),
        16384: region(12288, 8192, kind=0x40000),
        20480: region(20480, 4096, kind=0x1000000),
        24576: region(24576, 8192, 0x10000)}
    result = resources.walk_regions(values.__getitem__, 28672, 100, clock=lambda: 0)
    assert result == {"status": "complete", "regions_observed": 6, "allocation_bases_observed": 3,
        "committed_bytes": {"private": 8192, "mapped": 4096, "image": 4096},
        "committed_regions": {"private": 1, "mapped": 1, "image": 1},
        "reserved_bytes": 4096, "free_bytes": 8192, "non_atomic": True}


@pytest.mark.parametrize("mode", ["quota", "deadline", "api", "short_api", "late_complete"])
def test_partial_walk_never_becomes_complete_or_retries(mode):
    calls = []
    def query(address):
        calls.append(address)
        if mode in {"api", "short_api"}:
            raise resources.RegionQueryFault(0 if mode == "api" else 24, 5 if mode == "api" else None)
        return region(address, 4096)
    times = iter([0, 101])
    def clock():
        return next(times) if mode == "late_complete" else (101 if mode == "deadline" else 0)
    result = resources.walk_regions(query, 4096 if mode == "late_complete" else 8192,
                                    100, quota=1, clock=clock)
    assert result["status"] == "partial"
    assert len(calls) == (0 if mode == "deadline" else 1)
    if mode in {"api", "short_api"}:
        assert result["error_code"] == "RESOURCE_REGION_QUERY_FAILED"
        assert result["win32_error"] == (5 if mode == "api" else None)
    else:
        assert result["error_code"] == ("RESOURCE_REGION_QUOTA" if mode == "quota" else "RESOURCE_QUERY_BUDGET")


@pytest.mark.parametrize("change", [{"base": 4096}, {"size": 0}, {"size": 2**64 + 1},
    {"allocation": 4096}, {"state": 123}, {"kind": 123}, {"base": True}])
def test_invalid_regions_do_not_invent_aggregate_bytes(change):
    result = resources.walk_regions(lambda _: {**region(0, 4096), **change}, 4096, 100, clock=lambda: 0)
    assert result["status"] == "partial" and result["regions_observed"] == 0
    assert not any(result["committed_bytes"].values()) and result["reserved_bytes"] == result["free_bytes"] == 0


def test_identity_mismatch_closes_readonly_handle_before_resource_api_setup(monkeypatch, tmp_path):
    expected = ProcessIdentity(pid=123, created_filetime="1", executable_path=str(tmp_path / "owned.exe"),
                               executable_sha256="a" * 64)
    events = []
    def held(pid, **kwargs):
        assert pid == 123 and kwargs == {"query_information": True}
        return SimpleNamespace(identity=expected.model_copy(update={"created_filetime": "2"}),
                               close=lambda: events.append("closed"))
    monkeypatch.setattr(resources, "HeldProcess", held)
    with pytest.raises(Fault, match="PROCESS_IDENTITY_MISMATCH"):
        resources.ResourceProcess(expected)
    assert events == ["closed"]


def test_census_resumes_without_requery_and_resets_after_completion(monkeypatch):
    now, calls = [0], []
    monkeypatch.setattr(resources.time, "perf_counter_ns", lambda: now[0])
    reader = resources.ResourceProcess.__new__(resources.ResourceProcess)
    reader.census, reader.limit = None, 5 * 4096
    def query(address):
        calls.append(address)
        now[0] += 10_000_000  # A native call cannot be preempted at the 25-ms boundary.
        return region(address, 4096, allocation=0)
    reader.region = query
    first = reader.census_step(0, False)
    assert first["error_code"] == "RESOURCE_QUERY_BUDGET" and first["regions_observed"] == 3
    now[0] = 1_000_000_000
    second = reader.census_step(now[0], False)
    assert second["status"] == "complete" and second["segments"] == 2
    assert second["census_elapsed_ns"] == 1_020_000_000 and second["non_atomic"]
    assert second["committed_bytes"]["private"] == 5 * 4096
    assert second["allocation_bases_observed"] == 1
    assert calls == [i * 4096 for i in range(5)] and reader.census is None
    assert first["regions_observed"] == 3  # Published prefixes cannot mutate later.
    reader.census_step(now[0], False)
    assert calls[5] == 0  # A new census has a separate interval.


def test_region_quota_is_shared_across_segments():
    progress, calls = {}, []
    def query(address):
        calls.append(address)
        return region(address, 4096)
    ticks = iter([0, 101])
    first = resources.walk_regions(query, 12288, 100, quota=2,
                                   clock=lambda: next(ticks), _progress=progress)
    assert first["regions_observed"] == 1 and first["error_code"] == "RESOURCE_QUERY_BUDGET"
    second = resources.walk_regions(query, 12288, 100, quota=2, clock=lambda: 0, _progress=progress)
    assert second["regions_observed"] == 2 and second["error_code"] == "RESOURCE_REGION_QUOTA"
    assert calls == [0, 4096]


@pytest.mark.parametrize("end", ["time", "segments", "exit"])
def test_incomplete_census_expiry_and_exit_preserve_prefix_without_queries(monkeypatch, end):
    now = 8_000_000_000 if end == "time" else 2_000_000_000
    monkeypatch.setattr(resources.time, "perf_counter_ns", lambda: now)
    reader = resources.ResourceProcess.__new__(resources.ResourceProcess)
    prefix = {"status": "partial", "regions_observed": 42, "error_code": "RESOURCE_QUERY_BUDGET"}
    reader.census = {"started": 0, "segments": 8 if end == "segments" else 1,
                     "progress": {"result": prefix}}
    reader.region = lambda _: pytest.fail("Expired/terminal census must not query")
    value = reader.census_step(now, end == "exit")
    assert value["status"] == "partial" and value["regions_observed"] == 42
    assert value["error_code"] == ("RESOURCE_PROCESS_SIGNALED" if end == "exit" else "RESOURCE_CENSUS_DEADLINE")
    assert reader.census is None and prefix["error_code"] == "RESOURCE_QUERY_BUDGET"


def test_region_api_failure_cannot_resume_as_success(monkeypatch):
    monkeypatch.setattr(resources.time, "perf_counter_ns", lambda: 0)
    reader = resources.ResourceProcess.__new__(resources.ResourceProcess)
    reader.census, reader.limit = None, 4096
    def denied(_):
        raise resources.RegionQueryFault(0, 5)
    reader.region = denied
    value = reader.census_step(0, False)
    assert value["error_code"] == "RESOURCE_REGION_QUERY_FAILED" and value["win32_error"] == 5
    assert reader.census is None


@pytest.mark.skipif(os.name != "nt", reason="Actual Windows metadata handle")
def test_actual_owned_jvm_metadata_handle_cannot_terminate_and_survives_exit(jvm_factory, record_property):
    with jvm_factory() as (java, _):
        reader = resources.ResourceProcess(inspect_process(java.pid))
        try:
            snapshot = reader.snapshot()
            record_property("live_snapshot", json.dumps(snapshot))
            assert snapshot["regions"]["status"] == "complete" and snapshot["within_query_budget"]
            assert snapshot["counters"]["handles"] > 0
            assert snapshot["counters"]["memory"]["private"] > 0
            assert snapshot["regions"]["committed_bytes"]["private"] > 0
            assert not snapshot["signaled_after"]
            terminate = reader.kernel.TerminateProcess
            terminate.argtypes, terminate.restype = [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL
            ctypes.set_last_error(0)
            assert not terminate(reader.held.handle, 125) and ctypes.get_last_error() == 5
            assert java.poll() is None  # The metadata handle has no termination right.
            java.stdin.write(b"stop\n")
            java.stdin.flush()
            assert java.wait(timeout=5) == 0
            final = reader.snapshot()
            record_property("terminal_snapshot", json.dumps(final))
            assert final["signaled_before"] and final["signaled_after"]
            assert final["regions"] == {"status": "not_run", "reason": "process_signaled"}
            assert int(final["counters"]["cpu_100ns"]["kernel"]) >= int(snapshot["counters"]["cpu_100ns"]["kernel"])
        finally:
            reader.close()
        with pytest.raises(Fault, match="RESOURCE_OBSERVER_CLOSED"):
            reader.snapshot()
