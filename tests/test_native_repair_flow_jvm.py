"""Controller apply/commit/rollback through real worker/JVM; synthetic body and verification."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.native_settings_effects import EffectOutcomeUnknown, EffectRequest
from mcbench.native_repair_flow import NativeRepairFlow
from test_native_repair_flow import verification
from mcbench.storage import canonical, digest
from mcbench.worker_repair import WorkerRepairClient
from test_native_control_plan import prepare, target_for
from test_native_settings_effects_jvm import ID, ORIGINAL, effects_jvm as _effects_jvm, terminal
from test_reconfiguration import repair_env as _repair_env

effects_jvm, repair_env = _effects_jvm, _repair_env


@pytest.mark.parametrize("repair_env", ["real-clock"], indirect=True)
@pytest.mark.parametrize("lost_operation", [None, "settings_apply", "settings_commit", "settings_rollback"])
def test_controller_native_write_flow_with_actual_worker(effects_jvm, repair_env, tmp_path, monkeypatch, lost_operation):
    node = os.environ.get("STRATA_CLIENT_TEST_NODE")
    if os.name != "nt" or not node:
        pytest.skip("explicit pinned Node and Windows guardian required")
    worker_js = Path(__file__).resolve().parents[1] / "backends/mineflayer/dist/src/worker.js"
    def run(args):
        return subprocess.run(args, check=True, capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    capability = json.loads(run([node, str(worker_js), "--forge-capabilities", "a" * 64]).stdout)["digest"]
    e = repair_env
    prepare(e, ids=(ID, "minecraft:key.inventory:0"), initial=(71, "g"), replacement=(302, "f13"))
    lease = e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"]
    # Declare a G/G conflict before creating the fixture's first native store.
    options = ORIGINAL.replace("key_key.inventory:key.keyboard.e", "key_key.inventory:key.keyboard.g")
    with effects_jvm(repair_owner=True, commit_owner=True, capability_digest=capability, scope=("c1", "a1"), options_text=options) as (client, game, profile, game_root):
        original = (profile / "options.txt").read_bytes()
        descriptor = tmp_path / "connection-1.json"
        identity = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(game.pid)]).stdout)
        guard, config, state = tmp_path / "guard.json", tmp_path / "worker.json", tmp_path / "worker-state"
        state.mkdir()
        guard.write_bytes(canonical({"schema": "strata/ForgeProcessGuardGrant/2", "shutdown_policy": "java-tree1000-lease750/1",
            "purpose": "dedicated-development-client-lifetime", "campaign_id": "c1", "agent_id": "a1",
            "epoch": e.epoch, "process": identity, "expires_unix_ms": int(time.time() * 1000) + 60000, "max_wall_ms": 20000,
            "connection_file": str(descriptor), "connection_digest": digest(json.loads(descriptor.read_text())),
            "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64, "capability_digest": capability, "primitive_limit": 1000}))
        config.write_bytes(canonical({"schema": "strata/ForgeDevelopmentWorker/3", "repair_policy": "operator-owned-fixed-repair-pause/1",
            "purpose": "manual-conformance", "server_kind": "e9e", "backend": "forge_client", "pack_version": "1.27.0",
            "connection_file": str(descriptor), "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64,
            "state_directory": str(state), "max_wall_ms": 15000, "primitive_limit": 1000,
            "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease,
            "process_guard_file": str(guard), "guard_python": sys.executable}))
        parent = subprocess.Popen([node, str(worker_js), str(config)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            grant = state / f"repair-grant-{e.epoch}.json"
            until = time.monotonic() + 8
            while not grant.exists() and time.monotonic() < until:
                assert parent.poll() is None
                e.controller.heartbeat("c1", "owner", e.epoch)
                time.sleep(0.02)
            assert grant.exists()
            worker = WorkerRepairClient.from_file(grant)
            e.controller.heartbeat("c1", "owner", e.epoch)
            e.repairs.request("c1", "owner", e.epoch, "tx", "a1", "repair-op", deadline_unix=time.time() + 5)
            operations, original_call = [], client.call
            def call(operation, args, **kwargs):
                operations.append(operation)
                result = original_call(operation, args, **kwargs)
                if operation == lost_operation:
                    raise EffectOutcomeUnknown("lost", operation, "tx", None)
                return result
            monkeypatch.setattr(client, "call", call)
            target = target_for(e, client)
            receipt = e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
            plan = receipt["admission"]
            flow = NativeRepairFlow(e.repairs)
            if lost_operation == "settings_apply":
                with pytest.raises(EffectOutcomeUnknown):
                    flow.apply("tx", "owner", e.epoch, worker, client)
            assert flow.apply("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "verifying"
            snapshot = client.call("settings_snapshot", {})
            request = EffectRequest(id="effect", transaction_id="tx", expected_revision=snapshot["revision"],
                expected_digest=snapshot["digest"], plan_digest=plan["worker_plan"]["plan_digest"], binding_id=ID,
                context="IN_GAME", stage="before_restart", hold_ms=50, settle_ticks=2)
            client.call("settings_effect_start", request.model_dump(), timeout_ms=500)
            assert terminal(client, request)["state"] == "observed"
            proofs = verification(e)  # Explicit synthetic producer; does not claim actual restart.
            if lost_operation == "settings_commit":
                with pytest.raises(EffectOutcomeUnknown):
                    flow.commit("tx", "owner", e.epoch, worker, client, proofs)
            assert flow.commit("tx", "owner", e.epoch, worker, client, proofs)["control"]["phase"] == "committed"
            if lost_operation == "settings_rollback":
                with pytest.raises(EffectOutcomeUnknown):
                    flow.rollback("tx", "owner", e.epoch, worker, client)
            assert flow.rollback("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "rolled_back"
            assert operations.count("settings_apply") == operations.count("settings_commit") == operations.count("settings_rollback") == 1
            assert e.repairs.status("tx")["phase"] == "AWAITING_OBSERVATION"
            assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
            assert (profile / "options.txt").read_bytes() == original
            assert (game_root / "game-actions.jsonl").read_text().count('"kind":"repair_admitted"') == 1
            assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
            assert parent.wait(timeout=8) == 0
            assert game.wait(timeout=2) is not None
            assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            parent.stdout.close()
            parent.stderr.close()
