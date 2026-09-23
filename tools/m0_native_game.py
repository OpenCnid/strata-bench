"""Run the native Dovetail/broker/helper path against an owned vanilla worker.

Usage: python tools/m0_native_game.py PRIVATE_PLAN.json
The explicit plan references an already installed official server and licensed
avatar cache. No downloads, admin gameplay tool, desktop input or paid model
requests for Smoke/Recovery plans. M0NativePilot/1 explicitly selects real model
decisions and original accounting admission; isolation remains unqualified (D14).
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
from contextlib import ExitStack
from datetime import datetime, timezone

from mcbench.broker_stdio import WorkerTransport
from mcbench.contracts import RpcRequest
from mcbench.inventory import file_hash
from mcbench.launch_integrity import safe
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault, canonical, reject_links, require
from native_dispatch_probe import BINARY_SHA256, CODEX_VERSION, DOVETAIL_COMMIT, MODEL
from native_game_probe import GameProbe
from native_mcp_identity_probe import run as run_native
from mcbench.native_game_retention import GameRetention, paired_components
from mcbench.worker_bundle import HeldWorkerBundle
from mcbench.pack_launch import RestoredPackLaunchBinding, parse_pack_binding
from mcbench.pack_worker import HeldPackWorker, WorkerInvocation
from mcbench.vanilla_persistence import PACK_POLICY
from mcbench.worker_stop import stop_owned_worker
from mcbench.runtime import native_companion_paths

ROOT = Path(__file__).resolve().parents[1]


def private(path):
    path = Path(path).absolute()
    reject_links(path)
    require(not safe(path.resolve()).is_relative_to(safe(ROOT)), "PRIVATE_PATH_REQUIRED")
    return path


def write(path, body):
    with path.open("xb") as stream:
        stream.write(canonical(body))
        stream.flush()
        os.fsync(stream.fileno())


def finish_native_worker(worker, config, output, wait, operator_stop, checks, result):
    """A completed negative gameplay result still receives the normal stop path."""
    if operator_stop:
        result["worker_stop"] = stop_owned_worker(worker, config, output, wait)
    else:
        wait(lambda: worker.poll() is not None, config["max_wall_ms"] / 1000 + 5, "WORKER_STOP_TIMEOUT")
    require(worker.poll() == 0, "WORKER_EXIT_FAILED")
    require(all(checks.values()), "NATIVE_GAME_CHECK_FAILED")


def run(plan_path):
    plan = json.loads(private(plan_path).read_bytes())
    version = plan.get("schema")
    pilot = version == "strata/M0NativePilot/1"
    if pilot:
        from native_pilot_trial import check_inputs
        check_inputs(plan.get("pilot"))
    sealed = pilot or version in {"strata/M0NativeGameSmoke/4", "strata/M0NativeGameSmoke/5", "strata/M0NativeGameRecovery/3"}
    pinned = version in {"strata/M0NativeGameSmoke/3", "strata/M0NativeGameRecovery/2"}
    if sealed:
        require(set(plan) == {"schema", "output", "pack", "worker_invocation", "worker_runtime", "codex",
                              "tool_projections", "model_catalog",
                              "recovery_source" if version == "strata/M0NativeGameRecovery/3" else "retention_source"}
                | ({"pilot"} if pilot else set()), "M0_PLAN_INVALID")
        require(file_hash(Path(plan["codex"])) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
        native_companion_paths(plan["codex"])
        with ExitStack() as resources:
            return run_plan(plan, resources)
    require(version in {"strata/M0NativeGameSmoke/1", "strata/M0NativeGameSmoke/2", "strata/M0NativeGameRecovery/1",
                        "strata/M0NativeGameSmoke/3", "strata/M0NativeGameRecovery/2"}
            and set(plan) == {"schema", "output", "server_plan", "worker_config", "codex",
                              "worker_runtime" if pinned else "node",
                              "tool_projections", "model_catalog"} |
            ({"retention_source"} if version in {"strata/M0NativeGameSmoke/2", "strata/M0NativeGameSmoke/3"} else
             {"recovery_source"} if version in {"strata/M0NativeGameRecovery/1", "strata/M0NativeGameRecovery/2"}
             else set()), "M0_PLAN_INVALID")
    require(file_hash(Path(plan["codex"])) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    native_companion_paths(plan["codex"])
    with ExitStack() as resources:
        runtime = None
        if pinned:
            private(plan["worker_runtime"]["path"])
            runtime = HeldWorkerBundle(plan["worker_runtime"])
            private(runtime.body["root"])
            resources.enter_context(runtime)
        # Process callbacks are registered after the runtime lease. They close
        # before its release even when setup, native execution or cleanup raises.
        return run_plan(plan, resources, runtime)


def run_plan(plan, resources, runtime=None):
    version = plan["schema"]
    pilot = version == "strata/M0NativePilot/1"
    if pilot:
        from native_pilot_trial import check_inputs
        pilot_admission = check_inputs(plan["pilot"])
    sealed = pilot or version in {"strata/M0NativeGameSmoke/4", "strata/M0NativeGameSmoke/5", "strata/M0NativeGameRecovery/3"}
    restored = pilot or version in {"strata/M0NativeGameSmoke/5", "strata/M0NativeGameRecovery/3"}
    sealed_recovery = version == "strata/M0NativeGameRecovery/3"
    prepared = None
    retention = recovery = None
    if pilot or version in {"strata/M0NativeGameSmoke/2", "strata/M0NativeGameSmoke/3",
                   "strata/M0NativeGameSmoke/4", "strata/M0NativeGameSmoke/5"}:
        private(plan["retention_source"]["path"])
        retention = GameRetention(plan["retention_source"])
        # Check the real provider identity before materializing output or
        # preparing Java/worker resources. MODEL is only the scripted fixture.
        retention.check_identity(model=pilot_admission["model"] if pilot else MODEL,
            dovetail_commit=DOVETAIL_COMMIT, binary_digest=BINARY_SHA256,
            binary_version=CODEX_VERSION, helper_limit=0 if pilot else 2)
    if version in {"strata/M0NativeGameRecovery/1", "strata/M0NativeGameRecovery/2", "strata/M0NativeGameRecovery/3"}:
        from native_game_recovery import GameRecovery
        private(plan["recovery_source"]["bundle"])
        if not sealed_recovery:
            private(plan["recovery_source"]["template_directory"])
        recovery = GameRecovery(plan["recovery_source"], sealed=sealed_recovery)
        retention = recovery.retention
        if runtime:
            recovery.check_worker_runtime(runtime.reference)
    output = private(plan["output"])
    require(not output.exists(), "TARGET_EXISTS")
    if sealed:
        pack = parse_pack_binding(plan["pack"])
        require(isinstance(pack, RestoredPackLaunchBinding) == restored, "M0_PACK_RESTORATION_REQUIRED")
        private(pack.store)
        private(pack.instance)
        invocation = WorkerInvocation.model_validate(plan["worker_invocation"])
        require(safe(invocation.state_directory) == safe(output / "worker")
                and safe(invocation.configuration_path) == safe(output / "worker-config.json"), "M0_PLAN_INVALID")
        require(retention.config.pack_lock == pack.lock, "M0_PACK_RETENTION_MISMATCH")
        if restored:
            from mcbench.pack_restore import archive_restoration, baseline_record
            private(pack.restoration.snapshot)
            if sealed_recovery:
                recovery.validate_sealed_binding(pack, invocation.model_dump())
            else:
                require(json.loads(retention.body["objects"][retention.config.world_baseline]) == baseline_record(pack),
                        "M0_PACK_BASELINE_MISMATCH")
        output.mkdir(parents=True)
        (output / "worker").mkdir()
        prepared = resources.enter_context(HeldPackWorker(pack, invocation.model_dump()))
        require(prepared.resolved["worker_runtime"] == plan["worker_runtime"], "M0_PACK_RUNTIME_MISMATCH")
        runtime = prepared.runtime
        if sealed_recovery:
            recovery.check_worker_runtime(runtime.reference)
        worker_config = prepared.resolved["worker_configuration"]
        server_plan = {"schema": "strata/DevelopmentServer/5" if restored else "strata/DevelopmentServer/4",
            "pack": pack.model_dump(), "target": "vanilla",
            "persistence_policy": PACK_POLICY, "evidence": str(output / "server"),
            "max_wall_s": (worker_config["max_wall_ms"] + 999) // 1000 + 80}
        server_source, worker_source = output / "server-plan.json", output / "worker-config.json"
        write(output / "pack-worker-launch.json", prepared.resolved)
        lock_path = safe(Path(pack.store) / "objects" / pack.lock[11:])
        require(file_hash(lock_path) == pack.lock[11:], "M0_PACK_CHANGED")
        lock = json.loads(lock_path.read_bytes())
        for name, ref in {"pack-lock.json": pack.lock, "pack-launch-profile.json": lock["launch_profile"],
                          "pack-inventory.json": lock["resolved_inventory"]}.items():
            source = safe(Path(pack.store) / "objects" / ref[11:])
            require(file_hash(source) == ref[11:] and source.stat().st_size <= 8 * 1024**2, "M0_PACK_CHANGED")
            with (output / name).open("xb") as stream:
                stream.write(source.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
        if restored:
            world = archive_restoration(pack, json.loads((output / "pack-inventory.json").read_bytes()),
                                        output / ("restoration-source" if sealed_recovery else "baseline"))
            from mcbench.pack_launch import WorkerProfileBaseline
            if isinstance(pack.restoration, WorkerProfileBaseline):
                from mcbench.pack_baseline import profile_documents, verify_profile_baseline
                require(not sealed_recovery and invocation.epoch == 1, "PACK_BASELINE_NEW_CAMPAIGN_REQUIRED")
                documents = profile_documents(pack)
                proof = verify_profile_baseline(pack, world, json.loads((output / "pack-inventory.json").read_bytes()),
                                                documents, output / "baseline")
                for key in ("source_lock", "source_profile"):
                    write(output / ("baseline-" + key.replace("_", "-") + ".json"), documents[key])
                write(output / "baseline-import.json", proof)
            require(sealed_recovery or not any(p.startswith("world/playerdata/") and p.endswith(".dat") for p in world["files"]),
                    "M0_BASELINE_HAS_PLAYER_STATE")
    else:
        server_source, worker_source = private(plan["server_plan"]), private(plan["worker_config"])
        server_plan, worker_config = (json.loads(p.read_bytes()) for p in (server_source, worker_source))
    if retention:
        retention.check_scope(worker_config)
        expected = "strata/DevelopmentServer/5" if restored else "strata/DevelopmentServer/4" if sealed else "strata/DevelopmentServer/2"
        require(server_plan["schema"] == expected
                and server_plan["persistence_policy"] == (PACK_POLICY if sealed else "vanilla1192-stopped-instance/1"),
                "M0_CAPTURE_REQUIRED")
    require(server_plan["target"] == "vanilla" and worker_config["schema"] == "strata/DevelopmentWorker/1"
            and worker_config["server_kind"] == "vanilla" and worker_config["host"] == "127.0.0.1",
            "M0_PROFILE_UNSUPPORTED")
    require(150000 <= worker_config["max_wall_ms"] <= 240000 and
            server_plan["max_wall_s"] >= worker_config["max_wall_ms"] / 1000 + 60,
            "M0_EXPOSURE_INCOMPLETE")
    require(file_hash(Path(plan["codex"])) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    if retention and not pilot:
        retention.check_identity(model=MODEL, dovetail_commit=DOVETAIL_COMMIT,
            binary_digest=BINARY_SHA256, binary_version=CODEX_VERSION, helper_limit=0 if pilot else 2)
    for key in ("tool_projections", "model_catalog"):
        private(plan[key])
    require(not (private(worker_config["auth_cache"]) / "auth.lock").exists(), "AUTH_CACHE_IN_USE")
    if runtime:
        for path in (output, server_source, worker_source, private(worker_config["auth_cache"])):
            require(not safe(path).is_relative_to(runtime.root) and not runtime.root.is_relative_to(safe(path)),
                    "WORKER_BUNDLE_OVERLAP")
    if not sealed:
        output.mkdir(parents=True)
        (output / "worker").mkdir()
        worker_config["state_directory"] = str(output / "worker")
    server_plan["evidence"] = str(output / "server")
    if not sealed:
        write(output / "worker-config.json", worker_config)
    write(output / "server-plan.json", server_plan)
    if runtime:
        with (output / "worker-runtime.json").open("xb") as stream:
            stream.write(runtime.raw)
            stream.flush()
            os.fsync(stream.fileno())
    if retention:
        # Preserve exactly the externally pinned preregistration bytes.
        with (output / "retention-input.json").open("xb") as stream:
            stream.write(retention.raw)
            stream.flush()
            os.fsync(stream.fileno())
    source_pins = {p.relative_to(ROOT).as_posix(): file_hash(p)
                   for directory in (ROOT / "src/mcbench", ROOT / "tools")
                   for p in directory.iterdir() if p.suffix == ".py"}
    worker_root = Path(runtime.body["root"]) if runtime else ROOT
    source_pins.update({p.relative_to(worker_root).as_posix(): file_hash(p)
                       for p in (worker_root / "backends/mineflayer/dist/src").iterdir() if p.suffix == ".js"})
    write(output / "intent.json", {"schema": "strata/M0NativeGameIntent/1", "plan": plan,
        "model_provider": "native_oauth" if pilot else "synthetic", "real_model_requests": None if pilot else 0,
        "isolation_qualified": False, "authentic_game": True,
        "shared_desktop_input": False, "started_unix": time.time(),
        "source_pins": source_pins})
    if recovery and not sealed_recovery:
        private(server_plan["launch"]["working_directory"])
        recovery.materialize(output, server_plan, worker_config)
    environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH")
                   if key in os.environ}
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["NODE_COMPILE_CACHE"] = str(output / "node-compile-cache")
    processes, readers, reader_faults, closed = {}, [], [], set()
    result = {"schema": "strata/M0NativeGameResult/1", "status": "fail", "G0": "fail",
              "model_evidence": "synthetic_provider", "game_evidence": "authentic_vanilla",
              "real_model_requests": 0, "production_qualified": False, "native_worker_journal_join": False}
    if pilot:
        result.update(schema="strata/M0NativePilotResult/1", model_evidence="actual_native_oauth",
                      isolation_qualified=False, scope_decision="D14", complete_checkpoint=False,
                      real_model_requests=None)
    started = time.monotonic()

    def close_owned(name):
        if name not in closed:
            processes[name].close()
            closed.add(name)

    def launch(name, argv):
        if prepared and name in {"worker-preflight", "worker-driver"}:
            process = prepared.start(preflight=name == "worker-preflight")
        else:
            process = ManagedProcess(argv, ROOT, environment, "",
                interactive=name == "worker-driver" and runtime is not None and runtime.operator_stop,
                **({"bootstrap_python": Path(runtime.body["python"])} if prepared else {}))
        processes[name] = process
        resources.callback(close_owned, name)

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
        def worker_command(argument):
            return runtime.command(argument) if runtime else [plan["node"],
                str(ROOT / "backends/mineflayer/dist/src/worker.js"), str(argument)]

        loader = launch("worker-preflight", worker_command("--check-vanilla-runtime"))
        wait(lambda: loader.poll() is not None, 20, "WORKER_PREFLIGHT_TIMEOUT")
        require(loader.poll() == 0, "WORKER_PREFLIGHT_FAILED")
        if sealed_recovery:
            recovery.restore_worker(prepared, output)
        server = launch("server-driver", [sys.executable, "-X", "utf8", str(ROOT / "tools/development_server.py"),
                                           str(output / "server-plan.json")])
        wait(lambda: (output / "server/ready.json").exists() or server.poll() is not None,
             80 if sealed else 60, "SERVER_START_TIMEOUT")
        require(server.poll() is None, "SERVER_EARLY_EXIT")
        worker = launch("worker-driver", worker_command(output / "worker-config.json"))
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
                if recovery:
                    from native_game_recovery import player_matches
                    if not player_matches(recovery.player, observed["result"]["state"]):
                        require(time.monotonic() < deadline, "GAME_RECOVERY_PLAYER_CHANGED")
                        time.sleep(.6)
                        continue
                write(output / "initial-observation.json", observed)
                break
            require(worker.poll() is None and time.monotonic() < deadline, "GAME_CONNECT_TIMEOUT")
            time.sleep(.6)
        print(json.dumps({"status": "native_game_ready", "elapsed_s": round(time.monotonic()-started, 3)}), flush=True)
        if recovery:
            result["recovery_start"] = recovery.verify_start(descriptor, observed)
            write(output / "recovery-start.json", result["recovery_start"])
        native = output / "native"
        if not pilot:
            native.mkdir()
        if recovery:
            recovery.copy_native(native)
        if pilot:
            from native_pilot_trial import run_trial
            native_result = run_trial(plan, native, descriptor, worker_config["lease_id"])
        else:
            native_result = run_native(Path(plan["codex"]), native, broker_mode=True, admission_mode=True,
            bootstrap_mode=True, ingress_mode=True, oauth_mode=True,
            tool_projections=json.loads(Path(plan["tool_projections"]).read_bytes()),
            no_patch_catalog=Path(plan["model_catalog"]),
            game_probe=GameProbe(descriptor, worker_config["lease_id"], recovery=recovery is not None),
            game_retention=retention, game_recovery=recovery, job_id="root-recovery" if recovery else "root")
        write(output / "native-result.json", native_result)
        result["native_checks"] = native_result["checks"]
        if pilot:
            result["native_closure"] = native_result["runtime"]
            result["real_model_requests"] = len(native_result["attempts"])
            result["model_valuations"] = native_result["valuations"]
            require(native_result["closure_error"] is None, "PILOT_NATIVE_CLOSURE")
        else:
            result["native_closure"] = native_result["closure"]
            result["fixture_model_costs"] = native_result["budget"]
        if retention and not pilot:
            result["native_retention"] = native_result["retention"]
        finish_native_worker(worker, worker_config, output, wait,
                             runtime is not None and runtime.operator_stop, native_result["checks"], result)
        result["status"] = "pass"
    except BaseException as error:
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
            try:
                if (output / "server").is_dir():
                    if "worker_stop" in result:
                        boundary = {"schema": "strata/WorkerServerStopBoundary/1",
                            "worker_stop_request_id": result["worker_stop"]["intent"]["request"]["request_id"],
                            "requested_mono_ns": time.monotonic_ns(), "requested_unix": time.time()}
                        write(output / "server/stop.request", boundary)
                        result["server_stop_intent"] = boundary
                    else:
                        (output / "server/stop.request").touch(exist_ok=True)
            except Exception as error:
                result["status"] = "fail"
                result["server_stop_intent_error"] = type(error).__name__
                result["forced_server_cleanup"] = True
                server.stop()
            try:
                wait(lambda: server.poll() is not None, 125, "SERVER_STOP_TIMEOUT")
            except Exception:
                result["status"] = "fail"
                result["forced_server_cleanup"] = True
                server.stop()
        for reader in readers:
            reader.join(2)
        result["logs_complete"] = not reader_faults and not any(t.is_alive() for t in readers)
        if prepared:
            try:
                result["sealed_worker_receipt"] = prepared.receipt()
            except Exception as error:
                result["status"] = "fail"
                result["sealed_worker_error"] = error.code if isinstance(error, Fault) else type(error).__name__
        trees = {}
        for name, process in processes.items():
            result[name] = {"returncode": process.poll()}
            if runtime:
                trees[name] = {"parent_returncode": process.poll(),
                    "active_processes": process.job.accounting()["active_processes"] if process.job else None}
            close_owned(name)
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
            db.close()
            result["worker_journal"] = {"actions": actions, "counters": counters,
                                        "sha256": file_hash(journal)}
            selected = [a for a in actions if a["batch"]["epoch"] == worker_config["epoch"]]
            action_id = "native-bounded-look" + (f"-epoch-{worker_config['epoch']}" if recovery else "")
            joined = len(selected) == 1 and selected[0]["batch"]["request_id"] == action_id and \
                selected[0]["ack"]["status"] == "completed" and counters.get("primitive_events", 0) > 0
            if pilot:
                report_path = output / "native/result.json"
                model_actions = []
                if report_path.exists():
                    model_actions = [c["body"]["action"] for c in json.loads(report_path.read_bytes())["game_calls"]
                                     if c["body"]["method"] == "act"]
                joined = (len(selected) == len(model_actions) == 2 and
                    [a["batch"] for a in selected] == model_actions and
                    all(a["ack"]["status"] == "completed" and a["ack"]["release_confirmed"] for a in selected)
                    and counters.get("primitive_events", 0) > 0)
            if recovery:
                try:
                    result["recovery_journal"] = recovery.worker_report(journal)
                except Exception as error:
                    joined = False
                    result["recovery_error"] = error.code if isinstance(error, Fault) else type(error).__name__
            result["native_worker_journal_join"] = joined
            if not joined:
                result["status"] = "fail"
        if not result["native_worker_journal_join"]:
            result["status"] = "fail"
        if retention and not pilot:
            # Both components must exist; neither alone is a joint checkpoint.
            try:
                result["joint_components"] = paired_components(output, result, retention.source["sha256"], server_plan)
                write(output / "joint-components.json", result["joint_components"])
            except Exception as error:
                result["status"] = "fail"
                result["capture_error"] = error.code if isinstance(error, Fault) else type(error).__name__
        if runtime:
            try:
                require(set(trees) == {"worker-preflight", "worker-driver", "server-driver"}
                        and all(row == {"parent_returncode": 0, "active_processes": 0} for row in trees.values()),
                        "WORKER_RUNTIME_STOP_UNCERTAIN")
                result["worker_runtime"] = runtime.receipt() | {"owned_processes": trees,
                    "held_through_owned_stop": True, "root": runtime.body["root"],
                    "preflight_argv": worker_command("--check-vanilla-runtime"),
                    "worker_argv": worker_command(output / "worker-config.json")}
            except Exception as error:
                result["status"] = "fail"
                result["worker_runtime_error"] = error.code if isinstance(error, Fault) else str(error)
        write(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    result = run(args.plan)
    print(json.dumps({key: result[key] for key in ("status", "G0", "model_evidence", "game_evidence", "elapsed_s")}), flush=True)
    raise SystemExit(0 if result["status"] == "pass" else 1)
