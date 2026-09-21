"""Resource admission and failed-cleanup retention, without allocating large heaps."""

import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault


@pytest.fixture
def probe():
    path = Path(__file__).resolve().parents[1] / "tools/probe_guard_memory.py"
    spec = importlib.util.spec_from_file_location("guard_memory_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("samples", [[], [True], [0], [15], [17], [3088],
                                     [16, 16], [16, 32, 48, 64]])
def test_invalid_or_repeated_load_never_admitted(probe, samples):
    with pytest.raises(Fault, match="MEMORY_PROFILE_INVALID"):
        probe.admit(samples, {"available_physical_bytes": 10**12,
                              "available_commit_bytes": 10**12})


@pytest.mark.parametrize("missing", ["available_physical_bytes", "available_commit_bytes"])
def test_both_host_memory_limits_must_preserve_desktop_margin(probe, missing):
    memory = {"available_physical_bytes": 10**12, "available_commit_bytes": 10**12}
    memory[missing] = probe.HEADROOM + 3072 * probe.MIB
    with pytest.raises(Fault, match="DESKTOP_MEMORY_HEADROOM"):
        probe.admit([256, 1536, 3072], memory)
    memory[missing] = (3072 + 512 + 2048) * probe.MIB + probe.HEADROOM
    probe.admit([256, 1536, 3072], memory)


def test_cleanup_failures_still_close_owned_job_and_retain_failed_evidence(probe, monkeypatch, tmp_path):
    events = []
    def fail(name):
        def action(*args, **kwargs):
            events.append(name)
            raise Fault(name)
        return action
    owned = SimpleNamespace(
        process=SimpleNamespace(stdout=io.BytesIO(b""), wait=fail("WAIT_FAILED")),
        job=SimpleNamespace(observe_members=fail("OBSERVATION_FAILED")),
        stop=fail("STOP_FAILED"), close=lambda: events.append("closed"))
    monkeypatch.setattr(probe, "ManagedProcess", lambda *args, **kwargs: owned)
    monkeypatch.setattr(probe, "memory_status", lambda: {
        "available_physical_bytes": 10**12, "available_commit_bytes": 10**12})
    result = probe.sample(tmp_path / "java.exe", tmp_path, tmp_path, 16)
    assert events == ["OBSERVATION_FAILED", "STOP_FAILED", "WAIT_FAILED", "closed"]
    assert result["status"] == "incomplete" and not result["cleanup_confirmed"]
    assert result["stop_result"] == "not_run"
    assert result["error_code"] == "OBSERVATION_FAILED"
    assert result["cleanup_errors"] == ["STOP_FAILED", "WAIT_FAILED"]
    assert json.loads((tmp_path / "result-16.json").read_bytes()) == result
    with pytest.raises(FileExistsError):
        probe.sample(tmp_path / "java.exe", tmp_path, tmp_path, 16)
    assert events[-1] == "closed"  # Existing intent prevents another dispatch.
