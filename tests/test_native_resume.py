"""Strict private resume state; no gameplay or controller verification qualification."""
import copy

import pytest

from mcbench.native_resume import NativeResumeDecision, NativeResumeState
from mcbench.native_settings_effects import NativeSettingsEffectsClient


def decision():
    return {"schema": "strata/NativeSettingsResumeDecision/1", "policy": "operator-owned-settings-resume/1",
        "resume_id": "resume-1", "worker_plan": {"schema": "strata/WorkerRepairPlan/1",
            "policy": "operator-owned-fixed-repair-pause/1", "campaign_id": "campaign", "agent_id": "avatar",
            "epoch": 1, "lease_id": "lease-1", "transaction_id": "tx", "plan_digest": "a" * 64,
            "expires_unix_ms": 10000}, "expected_revision": 4, "expected_digest": "b" * 64,
        "completion_phase": "committed", "verification_ref": "cas:sha256:" + "c" * 64,
        "connection_generation": 1, "lease_until_unix_ms": 9000}


def state():
    return {"schema": "strata/NativeSettingsResumeState/1", "decision": decision(),
        "source_instance": "native-1", "current_instance": "native-1", "input_resumed": True,
        "effects_verified_by_native": False, "health": {"schema": "strata/NativeGameLane/1",
            "fenced": False, "fence_token": "opaque", "reason": None, "journal_healthy": True,
            "epoch": 1, "active_request_id": None, "attempted_primitive_events": 7, "primitive_limit": 100}}


@pytest.mark.parametrize("change", [{"extra": True}, {"lease_until_unix_ms": 10001},
    {"completion_phase": "applied_pending_verification"}, {"expected_revision": 0},
    {"connection_generation": -1}, {"verification_ref": "file:private"}, {"resume_id": "../foreign"}])
def test_decision_refuses_incomplete_or_unbounded_scope(change):
    with pytest.raises(ValueError):
        NativeResumeDecision.model_validate(decision() | change)


@pytest.mark.parametrize("change", [{"input_resumed": 1}, {"effects_verified_by_native": 0},
    {"effects_verified_by_native": True}, {"current_instance": "reopened"}, {"extra": True}])
def test_receipt_cannot_invent_live_or_verified_authority(change):
    with pytest.raises(ValueError):
        NativeResumeState.model_validate(state() | change)


@pytest.mark.parametrize("change", [{"fenced": True, "reason": "STOP_ALL"}, {"epoch": 2}, {"journal_healthy": False}])
def test_live_receipt_requires_matching_healthy_unfenced_lane(change):
    value = state()
    value["health"].update(change)
    with pytest.raises(ValueError):
        NativeResumeState.model_validate(value)


def test_old_receipt_is_history_after_reopen_and_request_is_not_mutated():
    value = state()
    value.update(current_instance="reopened", input_resumed=False)
    value["health"].update(fenced=True, reason="RECOVERY_REQUIRED")
    assert NativeResumeState.model_validate(value).input_resumed is False
    raw = decision()
    before = copy.deepcopy(raw)
    assert NativeSettingsEffectsClient._args("settings_resume", raw) == raw == before
