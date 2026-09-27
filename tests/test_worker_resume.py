"""Synthetic proof-substitution tests for the private worker resume consumer."""
import copy

import pytest

from mcbench.worker_resume import WorkerResumeGrant, WorkerResumeState
from test_forge_guard_resume import fixture


def state(example):
    _, native, _, _ = fixture()
    observation = example("Observation") | {"is_example": False, "campaign_id": "campaign", "agent_id": "avatar",
        "epoch": 1, "age_at_send_ms": 0, "captured_mono_ms": 100, "gateway_sent_mono_ms": 100, "held_keys": []}
    observation["state"]["connected"] = True
    observation["state"]["active_request_id"] = None
    return {"schema": "strata/WorkerResumeState/1", "decision": copy.deepcopy(native["decision"]),
        "native": native, "observation": observation, "primitive_events": 7, "gameplay_resumed": True}


@pytest.mark.parametrize("path,value", [
    ("gameplay_resumed", 1), ("native.input_resumed", False), ("decision.resume_id", "other"),
    ("native.current_instance", "reopened"), ("primitive_events", 6), ("observation.is_example", True),
    ("observation.agent_id", "sibling"), ("observation.epoch", 2), ("observation.age_at_send_ms", 2001),
    ("observation.state.connected", False), ("observation.state.active_request_id", "active"),
    ("native.effects_verified_by_native", True), ("private_path", "operator"),
])
def test_resume_proof_rejects_foreign_scope_stale_observation_and_false_authority(example, path, value):
    valid = state(example)
    assert WorkerResumeState.model_validate(valid).gameplay_resumed
    target = valid
    keys = path.split(".")
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    with pytest.raises(ValueError):
        WorkerResumeState.model_validate(valid)


@pytest.mark.parametrize("patch", [
    {"schema": "strata/WorkerResumeGrant/2"}, {"repair_binding_digest": None}, {"restart_binding_digest": None},
    {"url": "http://localhost:1234/v1/resume"}, {"url": "http://127.0.0.1:65536/v1/resume"},
    {"token": "public"}, {"epoch": True}, {"policy": "automatic-resume"}, {"extra": True},
])
def test_resume_grant_requires_both_bound_private_transports(patch):
    grant = {"schema": "strata/WorkerResumeGrant/1", "policy": "operator-owned-settings-resume/1",
        "repair_binding_digest": "a" * 64, "restart_binding_digest": "b" * 64,
        "url": "http://127.0.0.1:1234/v1/resume", "token": "c" * 64,
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease"}
    assert WorkerResumeGrant.model_validate(grant).port == 1234
    with pytest.raises(ValueError):
        WorkerResumeGrant.model_validate(grant | patch)
