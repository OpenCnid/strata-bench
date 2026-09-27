"""Synthetic receipt substitutions; Windows/JVM supervision is covered separately."""
import copy
import time
from types import SimpleNamespace

import pytest

from mcbench.forge_guard import ForgeGuardGrantV4, NativeHealth
from mcbench.native_resume import NativeResumeDecision
from mcbench.storage import Fault


def fixture():
    decision = NativeResumeDecision.model_validate({"schema": "strata/NativeSettingsResumeDecision/1",
        "policy": "operator-owned-settings-resume/1", "resume_id": "resume", "worker_plan": {
            "schema": "strata/WorkerRepairPlan/1", "policy": "operator-owned-fixed-repair-pause/1",
            "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease",
            "transaction_id": "tx", "plan_digest": "a" * 64, "expires_unix_ms": int(time.time() * 1000) + 5000},
        "expected_revision": 4, "expected_digest": "b" * 64, "completion_phase": "committed",
        "verification_ref": "cas:sha256:" + "c" * 64, "connection_generation": 2,
        "lease_until_unix_ms": int(time.time() * 1000) + 4000})
    health = {"schema": "strata/NativeGameLane/1", "fenced": False, "fence_token": "token", "reason": None,
        "journal_healthy": True, "epoch": 1, "active_request_id": None, "attempted_primitive_events": 7, "primitive_limit": 100}
    state = {"schema": "strata/NativeSettingsResumeState/1", "decision": decision.model_dump(),
        "source_instance": "replacement", "current_instance": "replacement", "health": health,
        "input_resumed": True, "effects_verified_by_native": False}
    monitor = NativeHealth.__new__(NativeHealth)
    monitor.grant = ForgeGuardGrantV4.model_construct(repair_plan=decision.worker_plan, primitive_limit=100)
    monitor.replacement_instance, monitor.resume_receipt = "replacement", None
    monitor.client = SimpleNamespace(call=lambda op, args, timeout_ms: copy.deepcopy(state))
    return monitor, state, health, {"connection_generation": 2}


@pytest.mark.parametrize("fault", ["instance", "plan", "generation", "epoch", "limit", "fenced", "inactive", "changed_receipt"])
def test_replacement_resume_refuses_foreign_or_inactive_receipts(fault):
    monitor, state, health, identity = fixture()
    if fault == "instance":
        state["source_instance"] = state["current_instance"] = "different"
    elif fault == "plan":
        state["decision"]["worker_plan"]["lease_id"] = "different"
    elif fault == "generation":
        state["decision"]["connection_generation"] += 1
    elif fault == "epoch":
        health["epoch"] += 1
    elif fault == "limit":
        health["primitive_limit"] += 1
    elif fault == "fenced":
        state["health"] = health | {"fenced": True}
    elif fault == "inactive":
        state["input_resumed"] = False
    else:
        monitor._repair_resume_health(identity, health)
        state["decision"]["resume_id"] = "second"
    with pytest.raises((Fault, ValueError)):
        monitor._repair_resume_health(identity, health)


def test_resume_authority_is_exact_and_status_does_not_issue_mutation():
    monitor, state, health, identity = fixture()
    calls = []
    def read(op, args, timeout_ms):
        calls.append((op, args, timeout_ms))
        return state
    monitor.client.call = read
    monitor._repair_resume_health(identity, health)
    monitor._repair_resume_health(identity, health)
    assert calls == [("settings_resume_status", {"transaction_id": "tx"}, 500)] * 2
    assert monitor.resume_receipt.model_dump() == state["decision"]


def test_pending_repair_still_requires_live_fixed_expiry_and_no_input():
    monitor, _, health, identity = fixture()
    held = health | {"fenced": True}
    monitor._repair_resume_health(identity, held)
    assert monitor.resume_receipt is None
    with pytest.raises(Fault, match="PROCESS_REPAIR_HOLD_LOST"):
        monitor._repair_resume_health(identity, held | {"active_request_id": "action"})
    monitor.grant.repair_plan.expires_unix_ms = 1
    with pytest.raises(Fault, match="PROCESS_REPAIR_HOLD_LOST"):
        monitor._repair_resume_health(identity, held)
