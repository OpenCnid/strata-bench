"""Run the native Dovetail/broker/helper path against an owned vanilla worker.

Usage: python tools/m0_native_game.py PRIVATE_PLAN.json
The explicit plan references an already installed official server and licensed
avatar cache. No downloads, admin gameplay tool, desktop input or paid model
requests. Model replies are scripted; Minecraft and the native CLI are real.
"""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

from mcbench.broker_stdio import WorkerTransport
from mcbench.contracts import RpcRequest
from mcbench.inventory import file_hash
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault, canonical, reject_links, require
from native_dispatch_probe import BINARY_SHA256, CODEX_VERSION, DOVETAIL_COMMIT, MODEL
from native_game_probe import GameProbe
from native_mcp_identity_probe import run as run_native
from mcbench.native_game_retention import GameRetention, paired_components

ROOT = Path(__file__).resolve().parents[1]


def private(path):
    path = Path(path).absolute()
    reject_links(path)
    require(not path.resolve().is_relative_to(ROOT), "PRIVATE_PATH_REQUIRED")
    return path


def write(path, body):
    with path.open("xb") as stream:
        stream.write(canonical(body))
        stream.flush()
        os.fsync(stream.fileno())


def run(plan_path):
    plan = json.loads(private(plan_path).read_bytes())
    version = plan.get("schema")
    require(version in {"strata/M0NativeGameSmoke/1", "strata/M0NativeGameSmoke/2"}
            and set(plan) == {"schema", "output", "server_plan", "worker_config", "codex", "node",
                              "tool_projections", "model_catalog"} |
            ({"retention_source"} if version == "strata/M0NativeGameSmoke/2" else set()), "M0_PLAN_INVALID")
    retention = None
    if version == "strata/M0NativeGameSmoke/2":
        private(plan["retention_source"]["path"])
        retention = GameRetention(plan["retention_source"])
    output = private(plan["output"])
    require(not output.exists(), "TARGET_EXISTS")
    server_source, worker_source = private(plan["server_plan"]), private(plan["worker_config"])
    server_plan, worker_config = (json.loads(p.read_bytes()) for p in (server_source, worker_source))
    if retention:
        retention.check_scope(worker_config)
        require(server_plan["schema"] == "strata/DevelopmentServer/2" and
                server_plan["persistence_policy"] == "vanilla1192-stopped-instance/1", "M0_CAPTURE_REQUIRED")
    require(server_plan["target"] == "vanilla" and worker_config["schema"] == "strata/DevelopmentWorker/1"
            and worker_config["server_kind"] == "vanilla" and worker_config["host"] == "127.0.0.1",
            "M0_PROFILE_UNSUPPORTED")
    require(150000 <= worker_config["max_wall_ms"] <= 240000 and
            server_plan["max_wall_s"] >= worker_config["max_wall_ms"] / 1000 + 60,
            "M0_EXPOSURE_INCOMPLETE")
    require(file_hash(Path(plan["codex"])) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    if retention:
        retention.check_identity(model=MODEL, dovetail_commit=DOVETAIL_COMMIT,
            binary_digest=BINARY_SHA256, binary_version=CODEX_VERSION, helper_limit=2)
    for key in ("tool_projections", "model_catalog"):
        private(plan[key])
    require(not (private(worker_config["auth_cache"]) / "auth.lock").exists(), "AUTH_CACHE_IN_USE")
    output.mkdir(parents=True)
    (output / "worker").mkdir()
    worker_config["state_directory"] = str(output / "worker")
    server_plan["evidence"] = str(output / "server")
    write(output / "worker-config.json", worker_config)
    write(output / "server-plan.json", server_plan)
    if retention:
        # Preserve exactly the externally pinned preregistration bytes.
        with (output / "retention-input.json").open("xb") as stream:
            stream.write(retention.raw)
            stream.flush()
            os.fsync(stream.fileno())
    write(output / "intent.json", {"schema": "strata/M0NativeGameIntent/1", "plan": plan,
        "model_provider": "synthetic", "real_model_requests": 0, "authentic_game": True,
        "shared_desktop_input": False, "started_unix": time.time(),
        "source_pins": {p.relative_to(ROOT).as_posix(): file_hash(p)
                        for directory in (ROOT / "src/mcbench", ROOT / "tools", ROOT / "backends/mineflayer/dist/src")
                        for p in directory.iterdir() if p.suffix in {".py", ".js"}}})
    environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH")
                   if key in os.environ}
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["NODE_COMPILE_CACHE"] = str(output / "node-compile-cache")
    processes, readers, reader_faults = {}, [], []
    result = {"schema": "strata/M0NativeGameResult/1", "status": "fail", "G0": "fail",
              "model_evidence": "synthetic_provider", "game_evidence": "authentic_vanilla",
              "real_model_requests": 0, "production_qualified": False, "native_worker_journal_join": False}
    started = time.monotonic()

    def launch(name, argv):
        process = ManagedProcess(argv, ROOT, environment, "")
        processes[name] = process

        def drain(stream, destination):
            try:
                total = 0
                with destination.open("xb") as output_stream:
                    while data := stream.read1(65536):
                        total += len(data)
                        require(total <= 64 * 1024**2, "M0_LOG_QUOTA")
                        output_stream.write(data)
                        output_stream.flush()
            except Exception:
                reader_faults.append(name)

        for stream, suffix in ((process.process.stdout, "stdout"), (process.process.stderr, "stderr")):
            thread = threading.Thread(target=drain, args=(stream, output / f"{name}.{suffix}.log"), daemon=True)
            thread.start()
            readers.append(thread)
        return process

    def wait(predicate, seconds, code):
        deadline = time.monotonic() + seconds
        while not predicate():
            require(time.monotonic() < deadline, code)
            require(not reader_faults, "M0_LOG_UNAVAILABLE")
            for process in processes.values():
                if process.job:
                    process.job.observe_members()
            time.sleep(.1)

    try:
        loader = launch("worker-preflight", [plan["node"], str(ROOT / "backends/mineflayer/dist/src/worker.js"),
                                             "--check-vanilla-runtime"])
        wait(lambda: loader.poll() is not None, 20, "WORKER_PREFLIGHT_TIMEOUT")
        require(loader.poll() == 0, "WORKER_PREFLIGHT_FAILED")
        server = launch("server-driver", [sys.executable, "-X", "utf8", str(ROOT / "tools/development_server.py"),
                                           str(output / "server-plan.json")])
        wait(lambda: (output / "server/ready.json").exists() or server.poll() is not None, 60, "SERVER_START_TIMEOUT")
        require(server.poll() is None, "SERVER_EARLY_EXIT")
        worker = launch("worker-driver", [plan["node"], str(ROOT / "backends/mineflayer/dist/src/worker.js"),
                                           str(output / "worker-config.json")])
        grant_path = output / "worker" / f"grant-{worker_config['epoch']}.json"
        wait(lambda: grant_path.exists() or worker.poll() is not None, 30, "WORKER_START_TIMEOUT")
        require(worker.poll() is None and grant_path.exists(), "WORKER_EARLY_EXIT")
        descriptor = json.loads(grant_path.read_bytes())
        transport = WorkerTransport(descriptor)
        scope = {key: descriptor[key] for key in ("campaign_id", "agent_id", "epoch")}
        deadline = time.monotonic() + 30
        while True:
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1", **scope,
                "request_id": "ready-" + uuid.uuid4().hex, "method": "observe", "action": None,
                "deadline_at": datetime.fromtimestamp(time.time()+5, timezone.utc).isoformat(
                    timespec="milliseconds").replace("+00:00", "Z"), "target_request_id": None, "after": None})
            observed = transport(request)
            if observed.get("status") == "ok" and observed["result"]["state"]["connected"]:
                write(output / "initial-observation.json", observed)
                break
            require(worker.poll() is None and time.monotonic() < deadline, "GAME_CONNECT_TIMEOUT")
            time.sleep(.6)
        print(json.dumps({"status": "native_game_ready", "elapsed_s": round(time.monotonic()-started, 3)}), flush=True)
        native = output / "native"
        native.mkdir()
        native_result = run_native(Path(plan["codex"]), native, broker_mode=True, admission_mode=True,
            bootstrap_mode=True, ingress_mode=True, oauth_mode=True,
            tool_projections=json.loads(Path(plan["tool_projections"]).read_bytes()),
            no_patch_catalog=Path(plan["model_catalog"]), game_probe=GameProbe(descriptor, worker_config["lease_id"]),
            game_retention=retention)
        write(output / "native-result.json", native_result)
        result["native_checks"] = native_result["checks"]
        result["native_closure"] = native_result["closure"]
        result["fixture_model_costs"] = native_result["budget"]
        if retention:
            result["native_retention"] = native_result["retention"]
        require(all(native_result["checks"].values()), "NATIVE_GAME_CHECK_FAILED")
        wait(lambda: worker.poll() is not None, worker_config["max_wall_ms"] / 1000 + 5, "WORKER_STOP_TIMEOUT")
        require(worker.poll() == 0, "WORKER_EXIT_FAILED")
        result["status"] = "pass"
    except Exception as error:
        result["error"] = error.code if isinstance(error, Fault) else type(error).__name__
    finally:
        # Revoke via the native binding first. Forced outer cleanup is a failure,
        # never substituted for a successful scoped stop or clean world save.
        worker = processes.get("worker-driver")
        if worker and worker.poll() is None:
            result["forced_worker_cleanup"] = True
            worker.stop()
        server = processes.get("server-driver")
        if server and server.poll() is None:
            if (output / "server").is_dir():
                (output / "server/stop.request").touch(exist_ok=True)
            try:
                wait(lambda: server.poll() is not None, 125, "SERVER_STOP_TIMEOUT")
            except Exception:
                result["status"] = "fail"
                result["forced_server_cleanup"] = True
                server.stop()
        for reader in readers:
            reader.join(2)
        result["logs_complete"] = not reader_faults and not any(t.is_alive() for t in readers)
        for name, process in processes.items():
            result[name] = {"returncode": process.poll()}
            process.close()
        result["elapsed_s"] = time.monotonic() - started
        if not result["logs_complete"] or any(process.poll() != 0 for process in processes.values()):
            result["status"] = "fail"
        saved = output / "server/result.json"
        result["server_result"] = json.loads(saved.read_bytes()) if saved.exists() else None
        if not result["server_result"] or result["server_result"]["status"] != "stopped_unqualified":
            result["status"] = "fail"
        journal = output / "worker/actions.sqlite"
        if journal.exists() and worker and worker.poll() == 0:
            with sqlite3.connect(journal.as_uri()+"?mode=ro", uri=True) as db:
                actions = [{"batch": json.loads(r[0]), "ack": json.loads(r[1])}
                           for r in db.execute("SELECT request,ack FROM actions ORDER BY seq")]
                counters = dict(db.execute("SELECT name,value FROM counters"))
            result["worker_journal"] = {"actions": actions, "counters": counters,
                                        "sha256": file_hash(journal)}
            joined = len(actions) == 1 and actions[0]["batch"]["request_id"] == "native-bounded-look" and \
                actions[0]["ack"]["status"] == "completed" and counters.get("primitive_events", 0) > 0
            result["native_worker_journal_join"] = joined
            if not joined:
                result["status"] = "fail"
        if not result["native_worker_journal_join"]:
            result["status"] = "fail"
        if retention:
            # Both components must exist; neither alone is a joint checkpoint.
            try:
                result["joint_components"] = paired_components(output, result, retention.source["sha256"], server_plan)
                write(output / "joint-components.json", result["joint_components"])
            except Exception as error:
                result["status"] = "fail"
                result["capture_error"] = error.code if isinstance(error, Fault) else type(error).__name__
        write(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    result = run(args.plan)
    print(json.dumps({key: result[key] for key in ("status", "G0", "model_evidence", "game_evidence", "elapsed_s")}), flush=True)
    raise SystemExit(0 if result["status"] == "pass" else 1)
