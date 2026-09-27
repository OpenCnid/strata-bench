"""Private identity contract checks; authentic worker provenance is separate."""

import pytest
from pydantic import ValidationError

from mcbench.pack_worker import WorkerPlayerIdentity
from mcbench.storage import Fault


def values(tmp_path):
    uuid = "00000000-0000-4000-8000-000000000001"
    scope = {"campaign_id": "copy", "agent_id": "body", "epoch": 1, "lease_id": "fresh",
             "expected_player_uuid": uuid}
    invocation = scope | {"state_directory": str(tmp_path / "state"),
                          "configuration_path": str(tmp_path / "config.json")}
    record = scope | {"schema": "strata/WorkerPlayerIdentity/1",
        "policy": "authenticated-saved-player-binding/1", "authenticated_player_uuid": uuid,
        "connected_player_uuid": uuid, "spawn_seq": 1, "recorded_at": "2026-09-25T00:00:00Z", "mono_ms": 1.0}
    return invocation, record


def test_identity_receipt_requires_same_configured_scope_and_player(tmp_path):
    invocation, record = values(tmp_path)
    assert WorkerPlayerIdentity.for_invocation(record, invocation).model_dump() == record
    for name, value in {"campaign_id": "other", "agent_id": "other", "epoch": 2, "lease_id": "other",
                        "expected_player_uuid": None}.items():
        with pytest.raises(Fault, match="WORKER_IDENTITY_SCOPE"):
            WorkerPlayerIdentity.for_invocation(record, invocation | {name: value})
    for name in ("authenticated_player_uuid", "connected_player_uuid"):
        with pytest.raises(ValidationError, match="AUTH_PLAYER_MISMATCH"):
            WorkerPlayerIdentity.for_invocation(record | {name: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}, invocation)


def test_identity_record_is_strict_and_rejects_bad_versions_and_measurements(tmp_path):
    invocation, record = values(tmp_path)
    for name, value in {"schema": "strata/WorkerPlayerIdentity/2", "policy": "unbound",
                        "spawn_seq": 0, "mono_ms": float("nan"), "extra": True,
                        "recorded_at": "invalid", "epoch": True}.items():
        with pytest.raises(ValidationError):
            WorkerPlayerIdentity.for_invocation(record | {name: value}, invocation)

