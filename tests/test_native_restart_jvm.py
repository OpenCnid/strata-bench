"""Actual JVM termination/reopen and native handoff; synthetic body, no worker restart claim."""

import json
import time

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_restart import NativeRestartCheckpoint, NativeRestartRequest
from mcbench.native_settings_effects import EffectOutcomeUnknown
from mcbench.storage import Fault
from test_native_commit_jvm import pending
from test_native_settings_effects_jvm import effect, terminal, effects_jvm as _effects_jvm

effects_jvm = _effects_jvm


def request(client, lifetime=10000):
    decision = pending(client, lifetime)
    return NativeRestartRequest.model_validate({"schema": "strata/NativeSettingsRestartRequest/1",
        "transaction_id": "tx", "plan_digest": decision.plan_digest, "restart_id": "restart-1",
        "expected_revision": decision.expected_revision, "expected_digest": decision.expected_digest})


def status(client, expected):
    return client.call("settings_restart_status", {"restart_id": "restart-1"}, expected_restart=expected)


@pytest.mark.parametrize("lost_operation", [None, "settings_restart_prepare", "settings_restart_continue"])
def test_pending_handoff_survives_actual_jvm_exit_and_continues_once(effects_jvm, monkeypatch, lost_operation):
    def lose_reply(client):
        original = client._result
        def result(operation, *args, **kwargs):
            value = original(operation, *args, **kwargs)
            if operation == lost_operation:
                raise TimeoutError("synthetic lost reply after native write")
            return value
        monkeypatch.setattr(client, "_result", result)
    with effects_jvm(repair_owner=True, restart_owner=True) as (client, first, profile, _):
        original_options = (profile / "options.txt").read_bytes()
        req = request(client)
        lose_reply(client)
        if lost_operation == "settings_restart_prepare":
            with pytest.raises(EffectOutcomeUnknown) as error:
                client.call("settings_restart_prepare", req.model_dump())
            assert error.value.transaction_id == "tx"
        else:
            client.call("settings_restart_prepare", req.model_dump())
        prepared = status(client, req)
        checkpoint = NativeRestartCheckpoint.model_validate(prepared["checkpoint"])
        first_session = client.connection.session_id
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_restart_continue", checkpoint.model_dump())
    assert first.poll() == 0
    with effects_jvm(repair_owner=True, restart_owner=True) as (client, second, profile, game_root):
        assert client.connection.session_id != first_session
        assert status(client, checkpoint)["phase"] == "prepared"
        lose_reply(client)
        if lost_operation == "settings_restart_continue":
            with pytest.raises(EffectOutcomeUnknown) as error:
                client.call("settings_restart_continue", checkpoint.model_dump())
            assert error.value.transaction_id == "tx"
        else:
            client.call("settings_restart_continue", checkpoint.model_dump())
        continued = status(client, checkpoint)
        assert continued["phase"] == "continued" and continued["input_resumed"] is False
        assert continued["expires_unix_ms"] == prepared["expires_unix_ms"]
        assert continued["primitive_events"] >= prepared["primitive_events"]
        head = client.call("settings_snapshot", {})
        run = effect(head).model_copy(update={"stage": "after_restart", "plan_digest": req.plan_digest})
        client.call("settings_effect_start", run.model_dump(), timeout_ms=1000)
        assert terminal(client, run)["state"] == "observed"
        game = NativeGameClient(client.connection)
        with pytest.raises(Fault):
            game.call("arm", {"epoch": 2, "lease_id": "new", "lease_until_unix_ms": int(time.time()*1000)+1000,
                "expected_fence_token": game.call("lane_status", {})["fence_token"]})
    assert second.poll() == 0
    with effects_jvm(repair_owner=True, restart_owner=True) as (client, _, profile, _):
        assert status(client, checkpoint)["phase"] == "recovery_required"
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_restart_continue", checkpoint.model_dump())
        client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == original_options
    frames = [json.loads(line)["payload"] for line in (game_root / "game-actions.jsonl").read_text().splitlines()]
    for kind in ("repair_restart_prepared", "repair_restart_continued"):
        assert sum(f["kind"] == kind for f in frames) == 1


@pytest.mark.parametrize("failure", ["disabled", "changed-head", "expired"])
def test_reopened_native_continuation_refuses_missing_authority_or_state(effects_jvm, failure):
    with effects_jvm(repair_owner=True, restart_owner=True) as (client, _, profile, _):
        req = request(client, 1500 if failure == "expired" else 10000)
        prepared = client.call("settings_restart_prepare", req.model_dump())
        checkpoint = NativeRestartCheckpoint.model_validate(prepared["checkpoint"])
    if failure == "changed-head":
        options = profile / "options.txt"
        options.write_bytes(options.read_bytes().replace(b"renderDistance:12", b"renderDistance:13"))
    if failure == "expired":
        time.sleep(1.55)
    with effects_jvm(repair_owner=True, restart_owner=failure != "disabled") as (client, _, _, _):
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_restart_continue", checkpoint.model_dump())
        assert status(client, checkpoint)["phase"] != "continued"
        assert client.call("settings_snapshot", {})["active_transaction"] == "tx"
