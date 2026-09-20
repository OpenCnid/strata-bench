"""Bounded operator-owned, localhost-only server preparation check.

Not a campaign supervisor or telemetry producer. Uses an explicit reviewed launch
plan, protected external evidence and a Job Object. Never accepts an EULA.
"""

import argparse
import json
import os
import re
import shutil
import threading
import time
from pathlib import Path

from mcbench.inventory import file_hash
from mcbench.processes import ManagedProcess
from mcbench.provisioning import LaunchCommand
from mcbench.storage import digest, reject_links, require


def outside(path):
    path = Path(path)
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(not path.is_relative_to(Path(__file__).resolve().parents[1]), "FORBIDDEN")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    options = parser.parse_args()
    plan = json.loads(outside(options.plan).read_text(encoding="utf-8"))
    require(set(plan) == {"schema", "launch", "evidence", "max_wall_s", "target"},
            "SCHEMA_UNSUPPORTED")
    require(plan["schema"] == "strata/DevelopmentServer/1"
            and plan["target"] in {"vanilla", "e9e"}, "SCHEMA_UNSUPPORTED")
    require(type(plan["max_wall_s"]) is int and 1 <= plan["max_wall_s"] <= 600, "CONFIG_RANGE")
    launch = LaunchCommand.model_validate(plan["launch"])
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
    evidence = outside(plan["evidence"])
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    require(shutil.disk_usage(root).free >= 5 * 1024**3, "DISK_RESERVE_LOW")
    started = time.monotonic()
    ready = threading.Event()
    overflow = threading.Event()
    reader_failed = threading.Event()
    threads = []
    proc = ManagedProcess([str(exe), *launch.arguments], root, launch.environment, "",
                          interactive=True)
    result = {"schema": "strata/DevelopmentServerResult/1", "plan_digest": digest(plan),
              "target": plan["target"], "started_unix": time.time(), "ready": False,
              "stop_sent": False, "forced_stop": False, "exit_code": None,
              "gate_result": "not_run", "campaign_admission": False}

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
    finally:
        if proc.poll() is None:
            result["forced_stop"] = True
            proc.stop()
        for thread in threads:
            thread.join(2)
        proc.close()
        result["elapsed_s"] = time.monotonic() - started
        result["logs_complete"] = not reader_failed.is_set() and not overflow.is_set()
        (evidence / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"status": "server_stopped", **result}), flush=True)


if __name__ == "__main__":
    main()
