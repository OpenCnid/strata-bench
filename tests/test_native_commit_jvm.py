"""Production native commit/store/journal with synthetic body and controller decision."""

import json
import time

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_settings_effects import EffectOutcomeUnknown
from mcbench.storage import Fault
from test_native_commit import decision
from test_native_repair_admission_jvm import admission
from test_native_settings_effects_jvm import effects_jvm as _effects_jvm

effects_jvm = _effects_jvm


def pending(client, lifetime=10000):
    plan = admission(client, lifetime)
    client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
    client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
    head = client.call("settings_snapshot", {})
    return decision(head["revision"], head["digest"], plan.worker_plan.plan_digest)


def commit_status(client, commit):
    return client.call("settings_commit_status", {"transaction_id": "tx"}, expected_commit=commit)


def test_commit_records_private_decision_without_effect_or_resume_claim(effects_jvm):
    with effects_jvm(repair_owner=True, commit_owner=True) as (client, _, profile, game_root):
        original = (profile / "options.txt").read_bytes()
        commit = pending(client)
        applied = (profile / "options.txt").read_bytes()
        result = client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
        assert result["committed"] is True
        assert result["effects_verified_by_native"] is result["input_resumed"] is False
        assert (profile / "options.txt").read_bytes() == applied
        assert client.call("settings_snapshot", {})["active_transaction"] is None
        assert client.call("settings_status", {"transaction_id": "tx"})["phase"] == "committed"
        game = NativeGameClient(client.connection)
        with pytest.raises(Fault):
            game.call("arm", {"epoch": 2, "lease_id": "new", "lease_until_unix_ms": 9999999999999,
                "expected_fence_token": game.call("lane_status", {})["fence_token"]})
        client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == original
        assert commit_status(client, commit)["phase"] == "rolled_back"
        assert '"kind":"repair_admitted"' in (game_root / "game-actions.jsonl").read_text()


def test_lost_commit_delivery_queries_the_durable_decision_once(effects_jvm, monkeypatch):
    with effects_jvm(repair_owner=True, commit_owner=True) as (client, _, _, _):
        commit = pending(client)
        original = client._result
        def lost(operation, *args, **kwargs):
            result = original(operation, *args, **kwargs)
            if operation == "settings_commit":
                raise TimeoutError("synthetic loss after durable response")
            return result
        monkeypatch.setattr(client, "_result", lost)
        with pytest.raises(EffectOutcomeUnknown) as error:
            client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
        assert error.value.transaction_id == "tx"
        assert commit_status(client, commit)["committed"] is True


def test_commit_survives_process_reopen_but_owned_hold_never_rearms(effects_jvm, tmp_path):
    with effects_jvm(repair_owner=True, commit_owner=True) as (client, _, profile, _):
        original = (profile / "options.txt").read_bytes()
        commit = pending(client)
        client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
    with effects_jvm() as (client, _, profile, _):
        assert commit_status(client, commit)["committed"] is True
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
        client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == original
        assert commit_status(client, commit)["phase"] == "rolled_back"
    frames = [json.loads(line)["payload"] for line in (tmp_path / "settings/settings-journal.jsonl").read_text().splitlines()]
    assert sum(frame["kind"] == "committed" for frame in frames) == 1


@pytest.mark.parametrize("change", ["plan", "revision", "reference"])
def test_refused_commit_never_changes_the_pending_patch(effects_jvm, change):
    with effects_jvm(repair_owner=True, commit_owner=True) as (client, _, profile, _):
        commit = pending(client)
        raw = commit.model_dump()
        if change == "plan":
            raw["plan_digest"] = "0" * 64
        elif change == "revision":
            raw["expected_revision"] += 1
        else:
            raw["verification_ref"] = "not-a-reference"
        before = (profile / "options.txt").read_bytes()
        with pytest.raises(ValueError):
            client.call("settings_commit", raw, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == before
        assert client.call("settings_status", {"transaction_id": "tx"})["phase"] == "applied_pending_verification"


def test_owned_repair_profile_without_commit_opt_in_cannot_commit(effects_jvm):
    with effects_jvm(repair_owner=True) as (client, _, _, _):
        commit = pending(client)
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
        assert client.call("settings_status", {"transaction_id": "tx"})["phase"] == "applied_pending_verification"


def test_expired_repair_refuses_commit_and_still_permits_rollback(effects_jvm):
    with effects_jvm(repair_owner=True, commit_owner=True) as (client, _, profile, _):
        original = (profile / "options.txt").read_bytes()
        commit = pending(client, 1500)
        time.sleep(1.55)
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_commit", commit.model_dump(), timeout_ms=1000)
        assert client.call("settings_status", {"transaction_id": "tx"})["phase"] == "applied_pending_verification"
        client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == original
