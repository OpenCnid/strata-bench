"""Separate response waiting from input lifetime; JVM body/input are synthetic."""
import json
import time
from types import SimpleNamespace

import pytest

from mcbench.native_repair_flow import NativeRepairFlow
from mcbench.storage import Fault
from test_native_settings_effects import client, request, exchange_result
from test_native_settings_effects_jvm import effects_jvm as _effects_jvm, apply, effect, terminal

effects_jvm = _effects_jvm


def test_absolute_effect_deadline_does_not_extend_http_wait(monkeypatch):
    c = client()
    exchange_result(c, monkeypatch)
    original = c._transport._exchange
    sent = []

    def exchange(method, path, body, timeout):
        sent.append((json.loads(body), timeout))
        return original(method, path, body, timeout)

    monkeypatch.setattr(c._transport, "_exchange", exchange)
    deadline = int(time.time() * 1000) + 4000
    c.call("settings_effect_start", request(), timeout_ms=500, effect_deadline_unix_ms=deadline)
    assert len(sent) == 1 and sent[0][0]["deadline_unix_ms"] == deadline
    assert sent[0][1] == .5


@pytest.mark.parametrize("mode", ["expired", "too_far", "boolean", "float", "read", "other_write"])
def test_effect_deadline_rejects_invalid_scope_before_transport(monkeypatch, mode):
    c = client()
    monkeypatch.setattr(c._transport, "_exchange", lambda *a: pytest.fail("unexpected dispatch"))
    now = int(time.time() * 1000)
    deadline = {"expired": now - 1, "too_far": now + 40000, "boolean": True,
                "float": float(now + 1000)}.get(mode, now + 1000)
    operation = {"read": "settings_snapshot", "other_write": "settings_rollback"}.get(mode, "settings_effect_start")
    with pytest.raises(Fault, match="SETTINGS_DEADLINE_INVALID"):
        c.call(operation, request(), effect_deadline_unix_ms=deadline)


@pytest.mark.parametrize("unix,mono,worker,expected", [
    (200., 200., 200000, 130000), (102., 200., 200000, 102000),
    (200., 103., 200000, 103000), (200., 200., 104000, 104000)])
def test_execution_bound_intersects_both_parent_clocks_and_worker(unix, mono, worker, expected):
    flow = object.__new__(NativeRepairFlow)
    flow.repairs = SimpleNamespace(clock=lambda: 100., monotonic=lambda: 100.)
    repair = {"request": {"deadline_unix": unix, "deadline_mono": mono}}
    admission = SimpleNamespace(worker_plan=SimpleNamespace(expires_unix_ms=worker))
    assert flow._effect_deadline(repair, admission) == expected
    assert flow._timeout(repair) == 1000


@pytest.mark.parametrize("clock", ["unix", "mono", "worker"])
def test_expired_parent_refuses_execution(clock):
    flow = object.__new__(NativeRepairFlow)
    flow.repairs = SimpleNamespace(clock=lambda: 100., monotonic=lambda: 100.)
    repair = {"request": {"deadline_unix": 100.01 if clock == "unix" else 200.,
                           "deadline_mono": 100.01 if clock == "mono" else 200.}}
    admission = SimpleNamespace(worker_plan=SimpleNamespace(expires_unix_ms=100010 if clock == "worker" else 200000))
    with pytest.raises(Fault, match="REPAIR_DEADLINE_EXPIRED"):
        flow._effect_deadline(repair, admission)


@pytest.mark.parametrize("separate_execution_window", [False, True])
def test_actual_jvm_long_hold_uses_execution_deadline(effects_jvm, separate_execution_window):
    with effects_jvm() as (c, process, profile, game_root):
        planned = effect(apply(c), hold=1250, ticks=2)
        kwargs = {"effect_deadline_unix_ms": int(time.time() * 1000) + 4000} if separate_execution_window else {}
        c.call("settings_effect_start", planned.model_dump(), timeout_ms=500, **kwargs)
        result = terminal(c, planned)
        assert result["state"] == ("observed" if separate_execution_window else "unknown")
        if not separate_execution_window:
            assert result["error_code"] == "SETTINGS_VERIFICATION_EXPIRED"
        else:
            release = next(o["value"] for o in result["observations"] if o["phase"] == "input_release")
            assert release["callbacks_confirmed"] and release["clear_confirmed"]
        assert process.poll() is None
