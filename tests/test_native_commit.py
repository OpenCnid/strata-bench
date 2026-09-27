"""Strict commit decision/result contracts. Synthetic controller decisions only."""

import copy

import pytest

from mcbench.native_settings_effects import NativeCommitDecision, NativeCommitState
from mcbench.storage import Fault
from test_native_settings_effects import client


def decision(revision=3, head="d" * 64, plan="e" * 64):
    return NativeCommitDecision.model_validate({"schema": "strata/NativeSettingsCommitDecision/1",
        "transaction_id": "tx", "plan_digest": plan, "expected_revision": revision, "expected_digest": head,
        "verification_ref": "cas:sha256:" + "f" * 64})


def state():
    return {"schema": "strata/NativeSettingsCommitState/1", "decision": decision().model_dump(),
        "phase": "committed", "revision": 4, "committed": True, "input_resumed": False,
        "effects_verified_by_native": False}


@pytest.mark.parametrize("patch", [{"input_resumed": True}, {"effects_verified_by_native": True},
    {"committed": 1}, {"input_resumed": 0}, {"effects_verified_by_native": 0}, {"committed": False},
    {"phase": "applied_pending_verification"}, {"phase": "rolled_back"}, {"revision": 3}, {"extra": 1}])
def test_commit_state_cannot_invent_effects_resume_or_a_matching_revision(patch):
    with pytest.raises(ValueError):
        NativeCommitState.model_validate(state() | patch)


def test_commit_result_joins_the_whole_consumed_decision():
    c = client()
    assert c._result("settings_commit", decision().model_dump(), state())["committed"] is True
    changed = copy.deepcopy(state())
    changed["decision"]["verification_ref"] = "cas:sha256:" + "0" * 64
    with pytest.raises(Fault, match="SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH"):
        c._result("settings_commit", decision().model_dump(), changed)
    assert c._result("settings_commit_status", {"transaction_id": "tx"}, state(), expected_commit=decision())["input_resumed"] is False


def test_native_status_only_accepts_matching_commit_boolean():
    c = client()
    value = {"transaction_id": "tx", "phase": "committed", "revision": 4, "committed": True}
    assert c._result("settings_status", {"transaction_id": "tx"}, value) == value
    with pytest.raises(ValueError, match="SETTINGS_COMMIT_RESPONSE_INVALID"):
        c._result("settings_status", {"transaction_id": "tx"}, value | {"committed": False})
