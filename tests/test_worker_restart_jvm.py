"""Actual same-worker, Windows guardian and native client replacement; synthetic Minecraft body."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.native_settings_effects import EffectRequest
from mcbench.native_restart import NativeRestartRequest
import http.client
from urllib.parse import urlsplit
from mcbench.native_repair_flow import NativeRepairFlow
from mcbench.storage import canonical, digest
from mcbench.worker_repair import WorkerRepairClient
from test_native_control_plan import prepare, target_for
from test_native_settings_effects_jvm import ID, ORIGINAL, effects_jvm as _effects_jvm, terminal
from test_reconfiguration import repair_env as _repair_env

effects_jvm, repair_env = _effects_jvm, _repair_env


@pytest.mark.parametrize("repair_env", ["real-clock"], indirect=True)
@pytest.mark.parametrize("stop_mode", ["operator", "repair_expiry"])
def test_same_worker_replaces_guarded_native_client_without_rearming(effects_jvm, repair_env, tmp_path, stop_mode):
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
    with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True, capability_digest=capability, scope=("c1", "a1"), options_text=options) as (client, game, profile, game_root):
        descriptor = tmp_path / "connection-1.json"
        identity = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(game.pid)]).stdout)
        guard, config, state = tmp_path / "guard.json", tmp_path / "worker.json", tmp_path / "worker-state"
        state.mkdir()
        guard.write_bytes(canonical({"schema": "strata/ForgeProcessGuardGrant/2", "shutdown_policy": "java-tree1000-lease750/1",
            "purpose": "dedicated-development-client-lifetime", "campaign_id": "c1", "agent_id": "a1",
            "epoch": e.epoch, "process": identity, "expires_unix_ms": int(time.time() * 1000) + 60000, "max_wall_ms": 25000,
            "connection_file": str(descriptor), "connection_digest": digest(json.loads(descriptor.read_text())),
            "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64, "capability_digest": capability, "primitive_limit": 1000}))
        config.write_bytes(canonical({"schema": "strata/ForgeDevelopmentWorker/4", "restart_policy": "operator-owned-client-replacement/1", "repair_policy": "operator-owned-fixed-repair-pause/1",
            "purpose": "manual-conformance", "server_kind": "e9e", "backend": "forge_client", "pack_version": "1.27.0",
            "connection_file": str(descriptor), "native_fingerprint": "a" * 64, "body_fingerprint": "b" * 64,
            "state_directory": str(state), "max_wall_ms": 20000, "primitive_limit": 1000,
            "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease,
            "process_guard_file": str(guard), "guard_python": sys.executable}))
        parent = subprocess.Popen([node, str(worker_js), str(config), "--operator-stop"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
            e.repairs.request("c1", "owner", e.epoch, "tx", "a1", "repair-op", deadline_unix=time.time() + 9)
            target = target_for(e, client)
            receipt = e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
            plan = receipt["admission"]
            flow = NativeRepairFlow(e.repairs)
            assert flow.apply("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "verifying"
            snapshot = client.call("settings_snapshot", {})
            restart = NativeRestartRequest.model_validate({"schema": "strata/NativeSettingsRestartRequest/1",
                "transaction_id": "tx", "plan_digest": plan["worker_plan"]["plan_digest"], "restart_id": "restart-1",
                "expected_revision": snapshot["revision"], "expected_digest": snapshot["digest"]})
            checkpoint = client.call("settings_restart_prepare", restart.model_dump())["checkpoint"]
            restart_grant = json.loads((state / f"restart-grant-{e.epoch}.json").read_text())
            address = urlsplit(restart_grant["url"])
            def restart_call(operation, paths=None, expected_status=200):
                transport = http.client.HTTPConnection(address.hostname, address.port, timeout=8)
                try:
                    transport.request("POST", address.path, body=canonical({"schema": "strata/WorkerRestartRequest/1",
                        "request_id": "request", "operation": operation, "plan": plan["worker_plan"],
                        "checkpoint": checkpoint, "paths": paths}), headers={"Content-Type": "application/json",
                        "Authorization": "Bearer " + restart_grant["token"]})
                    response = transport.getresponse()
                    result = json.loads(response.read())
                    assert response.status == expected_status, result
                    return result["result"] if response.status == 200 else result
                finally:
                    transport.close()
            detached = restart_call("detach")
            assert detached["phase"] == "detached" and detached["old_terminal"]["termination_confirmed"] is True
            assert game.wait(timeout=1) is not None and parent.poll() is None
            supervisor_before = [json.loads(line) for line in (state / f"supervisor-{e.epoch}.jsonl").read_text().splitlines()]
            child_pid = next(x["value"]["pid"] for x in supervisor_before if x["kind"] == "worker_started")
            assert restart_call("status")["phase"] == "detached"
            with effects_jvm(repair_owner=True, commit_owner=True, restart_owner=True) as (replacement, second, _, _):
                descriptor2 = tmp_path / "connection-2.json"
                identity2 = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(second.pid)]).stdout)
                guard2 = tmp_path / "guard-2.json"
                old_guard = json.loads(guard.read_text())
                guard2.write_bytes(canonical(old_guard | {"schema": "strata/ForgeProcessGuardGrant/3",
                    "restart_checkpoint": checkpoint, "repair_plan": plan["worker_plan"],
                    "process": identity2, "connection_file": str(descriptor2),
                    "connection_digest": digest(json.loads(descriptor2.read_text()))}))
                attached = restart_call("attach", {"connection_file": str(descriptor2), "process_guard_file": str(guard2)})
                assert attached["phase"] == "attached" and attached["input_resumed"] is False
                assert attached["primitive_events"] >= detached["primitive_events"]
                assert attached["replacement"]["process_digest"] != detached["old_terminal"]["process_digest"]
                assert parent.poll() is None
                assert restart_call("attach", {"connection_file": str(descriptor2), "process_guard_file": str(guard2)})["phase"] == "attached"
                refused = restart_call("attach", {"connection_file": str(descriptor), "process_guard_file": str(guard2)}, 400)
                assert refused["error"]["code"] == "REPAIR_NOT_OWNED"
                head = replacement.call("settings_snapshot", {})
                effect = EffectRequest(id="after", transaction_id="tx", expected_revision=head["revision"],
                    expected_digest=head["digest"], plan_digest=plan["worker_plan"]["plan_digest"], binding_id=ID,
                    context="IN_GAME", stage="after_restart", hold_ms=50, settle_ticks=2)
                replacement.call("settings_effect_start", effect.model_dump(), timeout_ms=500)
                assert terminal(replacement, effect)["state"] == "observed"
                assert restart_call("status")["phase"] == "attached"
                assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
                assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
                assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
                if stop_mode == "operator":
                    parent.stdin.write(canonical({"schema": "strata/WorkerStop/1", "policy": "operator-stdin-stop2250/1",
                        "request_id": "stop", "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease}) + b"\n")
                    parent.stdin.flush()
                    assert parent.wait(timeout=6) == 0
                else:
                    # Guardian or worker may observe expiry first; both must stop this same chain.
                    assert parent.wait(timeout=12) in (0, 1)
                    assert int(time.time() * 1000) <= plan["worker_plan"]["expires_unix_ms"] + 4000
                assert second.wait(timeout=2) is not None
            records = [json.loads(line) for line in (state / f"supervisor-{e.epoch}.jsonl").read_text().splitlines()]
            assert [x["value"]["pid"] for x in records if x["kind"] == "worker_started"] == [child_pid]
            assert sum(x["kind"] == "guard_stopped" for x in records) == 2
            assert sum(x["kind"] == "repair_restart_old_terminal" for x in records) == 1
            assert sum(x["kind"] == "repair_restart_replacement_guarded" for x in records) == 1
            if stop_mode == "repair_expiry":
                assert any(code in json.dumps(records) for code in ("REPAIR_DEADLINE_EXPIRED", "PROCESS_REPAIR_HOLD_LOST"))
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            parent.stdout.close()
            parent.stderr.close()
            parent.stdin.close()
