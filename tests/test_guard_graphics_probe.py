"""Reject unbound, incomplete or resource-starved native graphics fixture reports."""

import importlib.util
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault


@pytest.fixture
def probe(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "tools/probe_guard_graphics.py"
    monkeypatch.syspath_prepend(str(path.parent))
    spec = importlib.util.spec_from_file_location("guard_graphics_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report():
    return {"schema": "strata/GuardianRenderFixture/2", "scope": "a" * 32, "audio": False,
            "pid": 123, "minecraft": False, "visible": False, "heap_mib": 3072,
            "texture_mib": 256, "status": "ready", "resources_held": True,
            "frames": 20, "red_samples": [64, 191] * 10, "gl_version": "fixture",
            "gl_vendor": "fixture", "gl_renderer": "fixture",
            "gpu_free_kib_before": 3000 * 1024, "gpu_free_kib_loaded": 2500 * 1024}


def test_only_explicit_distinct_bounded_profiles_can_dispatch(probe):
    assert probe.selected_profiles(["combined-large"]) == [("combined-large", 3072, 1024, False)]
    for names in [[], ["context", "context"], ["unbounded"], list(probe.PROFILES)]:
        with pytest.raises(Fault, match="GRAPHICS_PROFILE_INVALID"):
            probe.selected_profiles(names)


@pytest.mark.parametrize("field,value", [("scope", "b" * 32), ("pid", 124),
    ("pid", True), ("minecraft", True), ("visible", True), ("heap_mib", 0),
    ("texture_mib", 0), ("status", "pass"), ("resources_held", False),
    ("frames", 19), ("red_samples", [64] * 20), ("gl_renderer", None),
    ("gpu_free_kib_before", 2048 * 1024), ("gpu_free_kib_loaded", 2048 * 1024 - 1)])
def test_rejects_unbound_or_incomplete_graphics_fixture(probe, field, value):
    valid = report()
    probe.validate(valid, scope="a" * 32, pid=123, heap=3072, texture=256, ready=True)
    valid[field] = value
    with pytest.raises(Fault):
        probe.validate(valid, scope="a" * 32, pid=123, heap=3072, texture=256, ready=True)


def test_boot_record_never_substitutes_for_live_resource_evidence(probe):
    boot = {k: v for k, v in report().items() if k in (
        "schema", "scope", "pid", "minecraft", "visible", "heap_mib", "texture_mib", "audio")}
    probe.validate(boot, scope="a" * 32, pid=123, heap=3072, texture=256, ready=False)
    with pytest.raises(Fault, match="GRAPHICS_FIXTURE_NOT_READY"):
        probe.validate(boot, scope="a" * 32, pid=123, heap=3072, texture=256, ready=True)


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_late_stop_stays_failed_after_cleanup_and_always_closes(probe, monkeypatch, tmp_path, cleanup_fails):
    events = []
    timing = {"wait_bound_ms": 500, "tree_result": "timeout"}
    def late():
        raise Fault("PROCESS_STOP_UNCONFIRMED")
    def stop():
        events.append("stop")
        if cleanup_fails:
            raise Fault("STOP_FAILED")
    child = SimpleNamespace(pid=123, deadline=time.monotonic() + 45, reason=None,
        poll=lambda: None, stop=stop, close=lambda: events.append("outer-close"),
        job=SimpleNamespace(accounting=lambda: {"active_processes": 0, "total_processes": 1},
            member_status=lambda: {"held_processes": 1, "signaled_processes": 1}))
    guard = SimpleNamespace(terminate=late, termination_timing=timing,
        process=SimpleNamespace(exited=lambda _: True), close=lambda: events.append("guard-close"))
    monkeypatch.setattr(probe, "DesktopApi", lambda: SimpleNamespace(input_name=lambda: "Default"))
    monkeypatch.setattr(probe, "DesktopProcess", lambda *a, **kw: child)
    monkeypatch.setattr(probe, "AttachedJava", lambda *a, **kw: guard)
    monkeypatch.setattr(probe, "inspect_process", lambda pid: pid)
    monkeypatch.setattr(probe.secrets, "token_hex", lambda _: "a" * 32)
    monkeypatch.setattr(probe.memory, "memory_status", lambda: {
        "available_physical_bytes": 10**12, "available_commit_bytes": 10**12})
    monkeypatch.setattr(probe.memory, "process_memory", lambda _: {"private_bytes": 4 * 1024**3})
    monkeypatch.setattr(probe, "wait_report", lambda *a: report())
    root = tmp_path / "case"
    result = probe.sample(tmp_path / "java.exe", "fixture", root, "combined", 3072, 256)
    assert result["stop_result"] == "fail" and result["stop_error_code"] == "PROCESS_STOP_UNCONFIRMED"
    assert result["termination_timing"] == timing and result["cleanup_confirmed"]
    assert events == ["stop", "guard-close", "outer-close"]
    assert result["status"] == ("incomplete" if cleanup_fails else "measured")
    assert json.loads((root / "result.json").read_bytes()) == result


@pytest.mark.parametrize("field,value", [("audio", False), ("audio", 1),
    ("audio_state", "stopped"), ("silent_pcm", False), ("source_gain", 1),
    ("source_gain", False), ("al_version", None), ("al_renderer", ""), ("al_device", None)])
def test_silent_audio_requires_live_bound_evidence(probe, field, value):
    current = {**report(), "audio": True, "audio_state": "playing", "silent_pcm": True,
               "source_gain": 0, "al_version": "fixture", "al_renderer": "fixture", "al_device": "fixture"}
    probe.validate(current, scope="a" * 32, pid=123, heap=3072, texture=256, audio=True, ready=True)
    current[field] = value
    with pytest.raises(Fault):
        probe.validate(current, scope="a" * 32, pid=123, heap=3072, texture=256, audio=True, ready=True)
