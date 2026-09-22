"""Bounded operator-owned, localhost-only server preparation check.

Not a campaign supervisor or telemetry producer. Uses an explicit reviewed launch
plan, protected external evidence and a Job Object. Never accepts an EULA.
"""

import argparse
import json
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

from mcbench.inventory import file_hash
from mcbench.processes import ManagedProcess
from mcbench.launch_integrity import IntegrityError
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.provisioning import LaunchCommand, validate_launch_environment
from mcbench.server_health import inspect_server_log
from mcbench.storage import Fault, digest, reject_links, require
from mcbench.vanilla_persistence import POLICY, PACK_POLICY, VanillaPersistence


def outside(path):
    path = Path(path)
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(not path.is_relative_to(Path(__file__).resolve().parents[1]), "FORBIDDEN")
    return path


def validate_persistence_profile(plan, launch, text):
    sealed = plan.get("schema") == "strata/DevelopmentServer/4"
    arguments = ["-Xms1G", "-Xmx2G", "-jar", "server.jar", "nogui"]
    require(os.name == "nt" and plan["target"] == "vanilla"
            and plan["persistence_policy"] == (PACK_POLICY if sealed else POLICY)
            and launch.arguments == (["-XX:ActiveProcessorCount=2", *arguments] if sealed else arguments),
            "VANILLA_PERSISTENCE_PROFILE_UNSUPPORTED")
    require(re.findall(r"(?m)^level-name=(.*)$", text) == ["world"]
            and re.findall(r"(?m)^enable-rcon=(true|false)$", text) == ["false"]
            and re.findall(r"(?m)^rcon\.password=(.*)$", text) == [""]
            and re.findall(r"(?m)^enable-command-block=(true|false)$", text) == ["false"],
            "VANILLA_PERSISTENCE_PROFILE_UNSUPPORTED")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    options = parser.parse_args(argv)
    plan = json.loads(outside(options.plan).read_text(encoding="utf-8"))
    capture = plan.get("schema") in {"strata/DevelopmentServer/2", "strata/DevelopmentServer/4"}
    sealed = plan.get("schema") in {"strata/DevelopmentServer/3", "strata/DevelopmentServer/4"}
    require(set(plan) == {"schema", "pack" if sealed else "launch", "evidence", "max_wall_s", "target"} | ({"persistence_policy"} if capture else set()),
            "SCHEMA_UNSUPPORTED")
    require(plan["schema"] in {"strata/DevelopmentServer/1", "strata/DevelopmentServer/2",
                               "strata/DevelopmentServer/3", "strata/DevelopmentServer/4"}
            and plan["target"] in {"vanilla", "e9e"}, "SCHEMA_UNSUPPORTED")
    require(type(plan["max_wall_s"]) is int and 1 <= plan["max_wall_s"] <= 600, "CONFIG_RANGE")
    binding = None
    if sealed:
        pack = PackLaunchBinding.model_validate(plan["pack"])
        outside(pack.store)
        outside(pack.instance)
        binding = resolve_pack_launch(pack, "server")
        require(binding["target"] == plan["target"], "RELEASE_MISMATCH")
    launch = LaunchCommand.model_validate(binding["launch"] if sealed else plan["launch"])
    validate_launch_environment(launch.environment)
    root = outside(launch.working_directory)
    require(root.is_dir(), "AWAITING_ARTIFACT")
    exe = Path(launch.executable_path)
    require(file_hash(exe) == launch.executable.digest, "HASH_MISMATCH")
    eula = root / "eula.txt"
    reject_links(eula)
    require(eula.stat().st_size < 65536
            and re.findall(r"(?m)^eula=(true|false)\s*$", eula.read_text()) == ["true"],
            "AWAITING_OPERATOR_EULA")
    properties = root / "server.properties"
    reject_links(properties)
    text = properties.read_text(encoding="utf-8")
    require(re.findall(r"(?m)^server-ip=(.*)\s*$", text) == ["127.0.0.1"], "LOOPBACK_REQUIRED")
    require(re.findall(r"(?m)^online-mode=(true|false)\s*$", text) == ["true"], "ONLINE_AUTH_REQUIRED")
    if capture:
        validate_persistence_profile(plan, launch, text)
    evidence = outside(plan["evidence"])
    if sealed:
        require(all(not evidence.is_relative_to(path) and not path.is_relative_to(evidence)
                    for path in (outside(pack.store), outside(pack.instance))), "UNSAFE_PATH")
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    if binding:
        (evidence / "pack-launch.json").write_text(json.dumps(binding, indent=2), encoding="utf-8")
    require(shutil.disk_usage(root).free >= 5 * 1024**3, "DISK_RESERVE_LOW")
    started = time.monotonic()
    ready = threading.Event()
    overflow = threading.Event()
    reader_failed = threading.Event()
    threads = []
    persistence = (VanillaPersistence(root, pack=pack if sealed else None,
                                     resolved=binding if sealed else None) if capture else None)
    try:
        # Bypass the venv executable redirector for this explicitly tracked
        # profile: the base bootstrap waits for Job assignment before children.
        proc = ManagedProcess([str(exe), *launch.arguments], root, launch.environment, "",
                              interactive=True, bootstrap_python=Path(sys._base_executable) if capture else None)
    except BaseException:
        if persistence:
            persistence.close()
        raise
    result = {"schema": "strata/DevelopmentServerResult/1", "plan_digest": digest(plan),
              "target": plan["target"], "started_unix": time.time(), "ready": False,
              "stop_sent": False, "forced_stop": False, "exit_code": None,
              "gate_result": "not_run", "campaign_admission": False,
              "status": "fail", "clean_save_proven": False}
    if binding:
        result["pack_launch_digest"] = digest(binding)

    def copy(source, name):
        try:
            with (evidence / name).open("xb") as destination:
                total = 0
                for line in iter(lambda: source.readline(65536), b""):
                    total += len(line)
                    if total > 256 * 1024**2:
                        overflow.set()
                        break
                    destination.write(line)
                    destination.flush()
                    if re.search(rb'Done \([0-9.,]+s\)! For help, type "help"', line):
                        ready.set()
                destination.flush()
                os.fsync(destination.fileno())
        except (OSError, ValueError):
            reader_failed.set()

    try:
        for source, name in ((proc.process.stdout, "stdout.log"), (proc.process.stderr, "stderr.log")):
            thread = threading.Thread(target=copy, args=(source, name), daemon=True)
            thread.start()
            threads.append(thread)
        stopping = None
        while proc.poll() is None:
            if capture:
                proc.job.observe_members()
            now = time.monotonic()
            if ready.is_set() and not result["ready"]:
                result["ready"] = True
                (evidence / "ready.json").write_text(json.dumps({"plan_digest": digest(plan),
                    "ready_unix": time.time(), "campaign_admission": False}), encoding="utf-8")
                print(json.dumps({"status": "server_ready", "evidence": str(evidence),
                                  "campaign_admission": False}), flush=True)
            if overflow.is_set() or reader_failed.is_set():
                result["forced_stop"] = True
                result["error"] = "EVIDENCE_UNAVAILABLE"
                proc.stop()
                break
            stop_file = evidence / "stop.request"
            reject_links(stop_file)
            should_stop = now - started >= plan["max_wall_s"] or stop_file.exists()
            if should_stop and stopping is None:
                result["stop_sent"] = True
                stopping = now
                proc.send_input("stop\n")
                print(json.dumps({"status": "server_stop_requested"}), flush=True)
            if stopping is not None and now - stopping >= 120:
                result["forced_stop"] = True
                proc.stop()
                break
            time.sleep(0.1)
        result["exit_code"] = proc.process.wait(timeout=2)
    except (OSError, Fault, IntegrityError) as error:
        result["error"] = error.code if isinstance(error, Fault) else (
            str(error) if isinstance(error, IntegrityError) else "SERVER_PROCESS_UNAVAILABLE")
    finally:
        if proc.poll() is None:
            result["forced_stop"] = True
            proc.stop()
        for thread in threads:
            thread.join(2)
        result["elapsed_s"] = time.monotonic() - started
        result["logs_complete"] = (not reader_failed.is_set() and not overflow.is_set()
                                   and not any(thread.is_alive() for thread in threads))
        try:
            require(result["logs_complete"], "SERVER_LOG_INCOMPLETE")
            result["log_health"] = {name: inspect_server_log(evidence / name)
                                    for name in ("stdout.log", "stderr.log")}
            if any(value["result"] == "fail" for value in result["log_health"].values()):
                result["error"] = "SERVER_RUNTIME_FAILURE"
            elif (result["ready"] and result["stop_sent"] and not result["forced_stop"]
                  and result["exit_code"] == 0 and "error" not in result):
                # Controlled launcher lifecycle only; a full save/checkpoint
                # needs independent server and persisted-state evidence.
                result["status"] = "stopped_unqualified"
                if persistence:
                    capture_started = time.monotonic()
                    result["stopped_snapshot"] = persistence.capture(evidence / "stopped-instance", proc,
                                                                     plan_digest=digest(plan))
                    result["snapshot_elapsed_s"] = time.monotonic() - capture_started
        except (OSError, Fault, IntegrityError) as error:
            result["status"] = "fail"
            result["error"] = error.code if isinstance(error, Fault) else (
                str(error) if isinstance(error, IntegrityError) else "SERVER_LOG_UNAVAILABLE")
        finally:
            if persistence:
                persistence.close()
            proc.close()
        if capture:
            result["total_elapsed_s"] = time.monotonic() - started
        (evidence / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"status": "server_stopped", **result}), flush=True)
    return 0 if result["status"] == "stopped_unqualified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
