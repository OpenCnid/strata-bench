"""Strict private restart wire semantics and binding; no game or restart qualification."""

import copy

import pytest

from mcbench.native_restart import NativeRestartCheckpoint, NativeRestartRequest, NativeRestartState
from mcbench.storage import Fault
from test_native_settings_effects import client


def request():
    return NativeRestartRequest.model_validate({"schema": "strata/NativeSettingsRestartRequest/1",
        "transaction_id": "tx", "plan_digest": "d" * 64, "restart_id": "restart-1",
        "expected_revision": 3, "expected_digest": "e" * 64})


def state():
    return {"schema": "strata/NativeSettingsRestartState/1", "checkpoint": {
        "schema": "strata/NativeSettingsRestartCheckpoint/1", "request": request().model_dump(),
        "source_instance": "original"}, "phase": "continued", "current_instance": "reopened",
        "continued_instance": "reopened", "primitive_events": 5, "expires_unix_ms": 100000,
        "input_resumed": False}


@pytest.mark.parametrize("patch", [{"input_resumed": True}, {"input_resumed": 0}, {"primitive_events": -1},
    {"primitive_events": True}, {"expires_unix_ms": 0}, {"continued_instance": None},
    {"continued_instance": "original"}, {"phase": "prepared"}, {"current_instance": "foreign"}, {"extra": 1}])
def test_restart_state_cannot_claim_resume_or_a_false_continuation(patch):
    with pytest.raises(ValueError):
        NativeRestartState.model_validate(state() | patch)


def test_restart_status_joins_consumed_checkpoint_or_preparation_request():
    c, value = client(), state()
    checkpoint = NativeRestartCheckpoint.model_validate(value["checkpoint"])
    assert c._result("settings_restart_continue", checkpoint.model_dump(), value) == value
    assert c._result("settings_restart_status", {"restart_id": "restart-1"}, value, expected_restart=checkpoint) == value
    assert c._result("settings_restart_status", {"restart_id": "restart-1"}, value, expected_restart=request()) == value
    changed = copy.deepcopy(value)
    changed["checkpoint"]["source_instance"] = "foreign"
    with pytest.raises(Fault, match="IDENTITY_MISMATCH"):
        c._result("settings_restart_continue", checkpoint.model_dump(), changed)


def test_status_requires_explicit_matching_expectation_before_transport(monkeypatch):
    c = client()
    monkeypatch.setattr(c._transport, "_exchange", lambda *a: pytest.fail("invalid status must not dispatch"))
    with pytest.raises(Fault):
        c.call("settings_restart_status", {"restart_id": "restart-1"})
    with pytest.raises(Fault):
        c.call("settings_restart_status", {"restart_id": "different"}, expected_restart=request())
