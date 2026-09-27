"""Actual Python controller -> Node worker -> guarded JVM; synthetic body/settings."""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.native_game import NativeGameClient
from mcbench.storage import canonical, digest
from mcbench.worker_repair import POLICY, WorkerRepairClient, WorkerRepairUnknown
from test_reconfiguration import repair_env as _repair_env

repair_env = _repair_env


@pytest.mark.parametrize("repair_env", ["real-clock"], indirect=True)
@pytest.mark.parametrize("lost_reply", [False, True])
def test_controller_handoff_cancels_actual_guarded_worker_without_replay(repair_env, tmp_path, monkeypatch, lost_reply):
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    classpath_file = os.environ.get("STRATA_CLIENT_TEST_CLASSPATH")
    node = os.environ.get("STRATA_CLIENT_TEST_NODE")
    if os.name != "nt" or not java or not classpath_file or not node:
        pytest.skip("explicit pinned Node/Java/classpath and Windows guardian required")
    root = Path(__file__).resolve().parents[1]
    worker_js = root / "backends/mineflayer/dist/src/worker.js"
    cli = root / "backends/mineflayer/dist/src/cli.js"
    e = repair_env
    fingerprint = "a" * 64
    def run(args, **kwargs):
        kwargs.setdefault("check", True)
        return subprocess.run(args, capture_output=True, timeout=20,
                              creationflags=subprocess.CREATE_NO_WINDOW, **kwargs)
    capability = json.loads(run([node, str(worker_js), "--forge-capabilities", fingerprint]).stdout)["digest"]
    native, worker_root = tmp_path / "native", tmp_path / "worker"
    native.mkdir()
    worker_root.mkdir()
    (native / "game-authority.json").write_bytes(canonical({"schema": "strata/NativeGameAuthority/1",
        "campaign_id": "c1", "agent_id": "a1", "capability_digest": capability,
        "body_fingerprint": fingerprint, "expires_unix_ms": int(time.time() * 1000) + 120000,
        "primitive_limit": 1000}))
    descriptor, argfile = tmp_path / "connection.json", tmp_path / "java-args.txt"
    args = ["-cp", Path(classpath_file).read_text().strip(),
            "io.github.opencnid.strata.client.GameBridgeFixture", descriptor, native, "hold", tmp_path / "freeze"]
    argfile.write_text("\n".join('"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'
                               for value in args), encoding="utf-8")
    game = subprocess.Popen([java, "@" + str(argfile)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    parent = None
    try:
        until = time.monotonic() + 15
        while not descriptor.exists() and time.monotonic() < until:
            assert game.poll() is None
            time.sleep(0.02)
        assert descriptor.exists()
        connection = json.loads(descriptor.read_text())
        native_client = NativeGameClient.from_file(descriptor)
        process = json.loads(run([sys.executable, "-I", "-m", "mcbench.process_guard", "--inspect", str(game.pid)]).stdout)
        e.begin()
        scope = e.controller.input_authority("c1", "owner", e.epoch, "a1")
        guard = tmp_path / "guard.json"
        guard.write_bytes(canonical({"schema": "strata/ForgeProcessGuardGrant/2",
            "shutdown_policy": "java-tree1000-lease750/1", "purpose": "dedicated-development-client-lifetime",
            "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "process": process,
            "expires_unix_ms": int(time.time() * 1000) + 120000, "max_wall_ms": 20000,
            "connection_file": str(descriptor), "connection_digest": digest(connection),
            "native_fingerprint": fingerprint, "body_fingerprint": fingerprint,
            "capability_digest": capability, "primitive_limit": 1000}))
        config = tmp_path / "worker.json"
        config.write_bytes(canonical({"schema": "strata/ForgeDevelopmentWorker/3", "repair_policy": POLICY,
            "purpose": "manual-conformance", "server_kind": "e9e", "backend": "forge_client", "pack_version": "1.27.0",
            "connection_file": str(descriptor), "native_fingerprint": fingerprint, "body_fingerprint": fingerprint,
            "state_directory": str(worker_root), "max_wall_ms": 15000, "primitive_limit": 1000,
            "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": scope["lease_id"],
            "process_guard_file": str(guard), "guard_python": sys.executable}))
        parent = subprocess.Popen([node, str(worker_js), str(config)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        grant = worker_root / "grant-1.json"
        until = time.monotonic() + 8
        while not grant.exists() and time.monotonic() < until:
            assert parent.poll() is None
            e.controller.heartbeat("c1", "owner", e.epoch)
            time.sleep(0.02)
        assert grant.exists()
        result = run([node, str(cli), "look-at", "--x", "1", "--y", "65", "--z", "2", "--json"],
                     env=os.environ | {"STRATA_GAME_GRANT": str(grant)}, check=False)
        assert result.returncode in {0, 2}
        accepted = json.loads(result.stdout)
        assert accepted["result"]["status"] == "accepted"
        until = time.monotonic() + 1
        while native_client.call("lane_status", {})["active_request_id"] is None and time.monotonic() < until:
            time.sleep(0.01)
        assert native_client.call("lane_status", {})["active_request_id"] is not None
        e.controller.heartbeat("c1", "owner", e.epoch)
        e.repairs.request("c1", "owner", e.epoch, "tx", "a1", "repair-op", deadline_unix=time.time() + 4)
        client = WorkerRepairClient.from_file(worker_root / "repair-grant-1.json")
        operations, original = [], client.call

        def exchange(operation, plan, **kwargs):
            operations.append(operation)
            result = original(operation, plan, **kwargs)
            if lost_reply and operation == "pause":
                raise WorkerRepairUnknown(result.request_id)  # lost controller delivery after actual worker reply
            return result

        monkeypatch.setattr(client, "call", exchange)
        if lost_reply:
            with pytest.raises(WorkerRepairUnknown):
                e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
        receipt = e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
        assert receipt["phase"] == "RECONFIGURING"
        assert operations == (["pause", "status"] if lost_reply else ["pause"])
        assert native_client.call("lane_status", {})["fenced"] is True
        assert native_client.call("lane_status", {})["active_request_id"] is None
        assert not e.adapter.requests
        assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
        with sqlite3.connect((worker_root / "actions.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            ack = json.loads(db.execute("SELECT ack FROM actions").fetchone()[0])
            assert ack["status"] == "cancelled" and ack["release_confirmed"] is True
            assert db.execute("SELECT count(*) FROM repair_holds").fetchone()[0] == 1
        assert parent.wait(timeout=8) == 0
        assert game.wait(timeout=2) is not None
        assert e.repairs.expire() == ["tx"]
        assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"
        assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
    finally:
        for process in (parent, game):
            if process is not None:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
