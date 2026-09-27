"""Owned native repair admission over real JVM HTTP; synthetic settings/body/input."""

import time
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.native_settings_effects import EffectOutcomeUnknown, NativeRepairAdmission
from mcbench.storage import Fault
from mcbench.storage import canonical, digest
from mcbench.worker_repair import WorkerRepairClient
from test_native_settings_effects_jvm import ID, effect, effects_jvm as _effects_jvm, terminal

effects_jvm = _effects_jvm


def admission(client, lifetime=10000):
    game = NativeGameClient(client.connection)
    health = game.call("lane_status", {})
    if health["epoch"] is None:
        game.call("arm", {"epoch": 1, "lease_id": "lease-1", "lease_until_unix_ms": int(time.time() * 1000) + 6000,
                          "expected_fence_token": health["fence_token"]})
        game.call("stop_all", {})
    snapshot = client.call("settings_snapshot", {})
    return NativeRepairAdmission.model_validate({"schema": "strata/NativeSettingsRepairAdmission/1",
        "policy": "operator-owned-native-settings-repair/1", "worker_plan": {
            "schema": "strata/WorkerRepairPlan/1", "policy": "operator-owned-fixed-repair-pause/1",
            "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease-1",
            "transaction_id": "tx", "plan_digest": "e" * 64, "expires_unix_ms": int(time.time() * 1000) + lifetime},
        "settings_fingerprint": "d" * 64, "patch": {"transaction_id": "tx", "expected_revision": snapshot["revision"],
            "expected_digest": snapshot["digest"], "changes": {ID: {"before": "key.keyboard.g", "after": "key.keyboard.f13"}}},
        "effect_bindings": [ID]})


def status(client, plan):
    return client.call("settings_repair_status", {"transaction_id": "tx"}, expected_repair=plan)


def test_owned_native_patch_effect_and_rollback_keep_the_same_plan(effects_jvm):
    with effects_jvm(repair_owner=True) as (client, _, profile, game_root):
        original = (profile / "options.txt").read_bytes()
        plan = admission(client)
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_apply", plan.patch.model_dump())
        result = client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        assert result["phase"] == "bound" and result["resume_authorized"] is False
        assert client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000) == result
        changed = plan.patch.model_dump()
        changed["changes"][ID]["after"] = "key.keyboard.e"
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_apply", changed, timeout_ms=1000)
        assert (profile / "options.txt").read_bytes() == original
        assert client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)["phase"] == "applied_pending_verification"
        request = effect(client.call("settings_snapshot", {}))
        wrong = request.model_dump() | {"plan_digest": "f" * 64}
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_effect_start", wrong, timeout_ms=1000)
        client.call("settings_effect_start", request.model_dump(), timeout_ms=1000)
        observed = terminal(client, request)
        assert observed["state"] == "observed" and observed["verified"] is False
        assert status(client, plan)["primitive_events"] > result["primitive_events"]
        assert client.call("settings_rollback", {"transaction_id": "tx"})["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == original
        assert status(client, plan)["phase"] == "recovery_required"
        game = NativeGameClient(client.connection)
        with pytest.raises(Fault):
            game.call("arm", {"epoch": 2, "lease_id": "new", "lease_until_unix_ms": int(time.time() * 1000) + 6000,
                              "expected_fence_token": game.call("lane_status", {})["fence_token"]})
        assert (game_root / "game-actions.jsonl").read_text().count('"kind":"repair_admitted"') == 1


def test_expired_native_plan_refuses_forward_work_but_allows_owned_rollback(effects_jvm):
    with effects_jvm(repair_owner=True) as (client, _, profile, _):
        original = (profile / "options.txt").read_bytes()
        plan = admission(client, 1200)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=200)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=200)
        while time.time() * 1000 <= plan.worker_plan.expires_unix_ms + 30:
            time.sleep(0.02)
        assert status(client, plan)["phase"] == "recovery_required"
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_effect_start", effect(client.call("settings_snapshot", {})).model_dump(), timeout_ms=200)
        assert client.call("settings_rollback", {"transaction_id": "tx"})["phase"] == "rolled_back"
        assert (profile / "options.txt").read_bytes() == original


def test_reopened_native_plan_stays_held_even_without_mode_flag(effects_jvm):
    with effects_jvm(repair_owner=True) as (client, _, profile, _):
        original = (profile / "options.txt").read_bytes()
        plan = admission(client)
        client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
    with effects_jvm() as (client, _, profile, _):
        assert status(client, plan)["phase"] == "recovery_required"
        with pytest.raises(EffectOutcomeUnknown):
            client.call("settings_apply", plan.patch.model_dump(), timeout_ms=1000)
        client.call("settings_rollback", {"transaction_id": "tx"})
        assert (profile / "options.txt").read_bytes() == original


def test_preplay_mode_does_not_claim_owned_repair_support(effects_jvm):
    with effects_jvm() as (client, _, _, _):
        plan = admission(client)
        with pytest.raises(EffectOutcomeUnknown) as error:
            client.call("settings_repair_bind", plan.model_dump(), timeout_ms=1000)
        assert error.value.transaction_id == "tx"


def test_actual_worker_pause_owns_native_settings_mutation_and_expiry(effects_jvm, tmp_path):
    node = os.environ.get("STRATA_CLIENT_TEST_NODE")
    if os.name != "nt" or not node:
        pytest.skip("explicit pinned Node and Windows guardian required")
    worker_js = Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/worker.js"
    def run(args):
        return subprocess.run(args, check=True, capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    capability = json.loads(run([node, str(worker_js), "--forge-capabilities", "a" * 64]).stdout)["digest"]
    with effects_jvm(repair_owner=True, capability_digest=capability) as (client, game, profile, _):
        original = (profile / "options.txt").read_bytes()
        descriptor = tmp_path / "connection-1.json"
        identity = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(game.pid)]).stdout)
        guard, config, state = tmp_path / "guard.json", tmp_path / "worker.json", tmp_path / "worker-state"
        state.mkdir()
        guard.write_bytes(canonical({"schema": "strata/ForgeProcessGuardGrant/2", "shutdown_policy": "java-tree1000-lease750/1",
            "purpose": "dedicated-development-client-lifetime", "campaign_id": "campaign", "agent_id": "avatar",
            "epoch": 1, "process": identity, "expires_unix_ms": int(time.time() * 1000) + 60000, "max_wall_ms": 20000,
            "connection_file": str(descriptor), "connection_digest": digest(json.loads(descriptor.read_text())),
            "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64, "capability_digest": capability, "primitive_limit": 1000}))
        config.write_bytes(canonical({"schema": "strata/ForgeDevelopmentWorker/3", "repair_policy": "operator-owned-fixed-repair-pause/1",
            "purpose": "manual-conformance", "server_kind": "e9e", "backend": "forge_client", "pack_version": "1.27.0",
            "connection_file": str(descriptor), "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64,
            "state_directory": str(state), "max_wall_ms": 15000, "primitive_limit": 1000,
            "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease-1",
            "process_guard_file": str(guard), "guard_python": sys.executable}))
        parent = subprocess.Popen([node, str(worker_js), str(config)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            grant = state / "repair-grant-1.json"
            until = time.monotonic() + 8
            while not grant.exists() and time.monotonic() < until:
                assert parent.poll() is None
                time.sleep(0.02)
            assert grant.exists()
            worker = WorkerRepairClient.from_file(grant)
            plan = admission(client, 3000)
            assert worker.call("pause", plan.worker_plan).result.phase == "paused"
            bound = client.call("settings_repair_bind", plan.model_dump(), timeout_ms=500)
            assert bound["admission"]["worker_plan"] == plan.worker_plan.model_dump()
            client.call("settings_apply", plan.patch.model_dump(), timeout_ms=500)
            request = effect(client.call("settings_snapshot", {}))
            client.call("settings_effect_start", request.model_dump(), timeout_ms=500)
            assert terminal(client, request)["state"] == "observed"
            client.call("settings_rollback", {"transaction_id": "tx"}, timeout_ms=500)
            assert (profile / "options.txt").read_bytes() == original
            assert status(client, plan)["phase"] == "recovery_required"
            assert parent.wait(timeout=8) == 0
            assert game.wait(timeout=2) is not None
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            parent.stdout.close()
            parent.stderr.close()
