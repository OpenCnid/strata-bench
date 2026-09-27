"""Synthetic replacement-health failures; actual process replacement is tested separately."""

import time
from types import SimpleNamespace

import pytest

from mcbench import forge_guard as module
from mcbench.native_restart import NativeRestartCheckpoint
from mcbench.worker_repair import WorkerRepairPlan
from mcbench.storage import Fault


@pytest.mark.parametrize("case,expected", [
    ("valid", None), ("foreign_plan", "PROCESS_RESTART_MISMATCH"),
    ("foreign_checkpoint", "PROCESS_RESTART_MISMATCH"), ("same_instance", "PROCESS_RESTART_MISMATCH"),
    ("already_continued", "PROCESS_RESTART_MISMATCH"), ("changed_expiry", "PROCESS_RESTART_MISMATCH"),
    ("expired", "PROCESS_REPAIR_HOLD_LOST"), ("unfenced", "PROCESS_REPAIR_HOLD_LOST"),
    ("active", "PROCESS_REPAIR_HOLD_LOST"), ("wrong_epoch", "PROCESS_NATIVE_ALREADY_ARMED"),
    ("later_unfenced", "PROCESS_REPAIR_HOLD_LOST"), ("legacy", "PROCESS_NATIVE_ALREADY_ARMED"),
])
def test_replacement_profile_requires_exact_prepared_repair_and_keeps_input_fenced(monkeypatch, case, expected):
    expiry = time.time_ns() // 1000000 + (-1 if case == "expired" else 10000)
    plan = WorkerRepairPlan.model_validate({"schema": "strata/WorkerRepairPlan/1",
        "policy": "operator-owned-fixed-repair-pause/1", "campaign_id": "foreign" if case == "foreign_plan" else "campaign",
        "agent_id": "avatar", "epoch": 1, "lease_id": "lease", "transaction_id": "repair",
        "plan_digest": "a" * 64, "expires_unix_ms": expiry})
    checkpoint = NativeRestartCheckpoint.model_validate({"schema": "strata/NativeSettingsRestartCheckpoint/1",
        "source_instance": "old", "request": {"schema": "strata/NativeSettingsRestartRequest/1",
            "transaction_id": "repair", "restart_id": "restart", "plan_digest": "a" * 64,
            "expected_revision": 1, "expected_digest": "b" * 64}})
    # No OS process access in these health-state tests; only the consumed fields are constructed.
    model = module.ForgeGuardGrantV2 if case == "legacy" else module.ForgeGuardGrantV3
    grant = model.model_construct(campaign_id="campaign", agent_id="avatar", epoch=1,
        body_fingerprint="b" * 64, capability_digest="c" * 64, primitive_limit=100,
        process=SimpleNamespace(pid=123), repair_plan=plan, restart_checkpoint=checkpoint)
    calls, cycles = [], 0

    def call(operation, args, *, timeout_ms):
        nonlocal cycles
        calls.append(operation)
        assert timeout_ms == 500
        if operation == "authority":
            return {"campaign_id": "campaign", "agent_id": "avatar", "capability_digest": "c" * 64,
                "body_fingerprint": "b" * 64, "primitive_limit": 100, "expires_unix_ms": expiry + 30000}
        if operation == "identity":
            return {"body_fingerprint": "b" * 64, "connection_generation": 1}
        if operation == "lane_status":
            cycles += 1
            return {"journal_healthy": True, "fenced": case != "unfenced" and not (case == "later_unfenced" and cycles > 1),
                "active_request_id": "active" if case == "active" else None, "epoch": 2 if case == "wrong_epoch" else 1}
        assert operation == "settings_restart_status" and args == {"restart_id": "restart"}
        return {"checkpoint": {} if case == "foreign_checkpoint" else checkpoint.model_dump(),
            "phase": "continued" if case == "already_continued" else "prepared",
            "current_instance": "old" if case == "same_instance" else "new",
            "expires_unix_ms": expiry + (1 if case == "changed_expiry" else 0)}

    monkeypatch.setattr(module, "listener_owned_by", lambda *_: None)
    monitor = module.NativeHealth(grant, SimpleNamespace(call=call, connection=SimpleNamespace(port=123)))
    try:
        if expected is None or case == "later_unfenced":
            assert monitor.prepare()["body_fingerprint"] == "b" * 64
        if expected:
            until = time.monotonic() + 2
            while monitor.error is None and time.monotonic() < until:
                time.sleep(.005)
            assert monitor.error == expected
            with pytest.raises(Fault, match=expected):
                monitor.prepare()
            assert monitor.failure_diagnostic()["initialized"] == (case == "later_unfenced")
        assert calls.count("settings_restart_status") <= 1
    finally:
        monitor.stop.set()
