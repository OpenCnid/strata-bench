"""Fixed installed E9E boot observation; private operator tool, no gameplay agent.

Run against an independently verified fresh copy or its normally stopped world.
This profile does not seal an installation, award a score or qualify isolation.
"""

import argparse
import os
from pathlib import Path
import re
import socket
import sys
import threading
import time
from types import SimpleNamespace

from mcbench.inventory import file_hash
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.pack_modes import inspect_e9e_mode
from mcbench.processes import ManagedProcess
from mcbench.runtime_data import AGENT_PATH, validate_snapshot
from mcbench.server_health import inspect_server_log
from mcbench.storage import canonical, require
from strata_evaluator.reference_launch import bind_identity, first_start
from strata_evaluator.telemetry_auth import inspect_authenticated_spool, issue_authority

PROFILE = "e9e1270-installed-forge-cold-start/1"
ARGS = "libraries/net/minecraftforge/forge/1.19.2-43.4.23/win_args.txt"
MODULE = "mods/strata-forge1192-telemetry-0.3.13.jar"
PINS = {
    ARGS: "083c60331e7cdd9c76f73a3131f86e1f8b5454fa1a531f59e2d9748c27923c30",
    MODULE: "0067aba399598ed6d9482398ea051aff24fcaa1fb1499fe7d546d915d5df6625",
    "java/bin/java.exe": "1977f302375adbb920d41dac65c7e22eb9c2ed8e1e8d6258964154ff16f14406",
}
QUERIES = [
    {
        "file_name": "create-server.toml",
        "paths": [
            ["logistics", "defaultExtractionTimer"],
            ["schematics", "schematicannon", "schematicannonShotsPerGunpowder"],
            ["schematics", "schematicannon", "schematicannonDelay"],
        ],
    },
    {"file_name": "sophisticatedcore-common.toml", "paths": [["common", "enabledItems"]]},
]
RECIPE = "enigmatica:expert/minecraft/shaped/furnace"


def write(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def validate(root, output, *, initial):
    root, output = Path(root), Path(output)
    for path in (root, output):
        safe(path)
        require(path == Path(os.path.abspath(path)), "INITIALIZATION_PATH")
    require(
        root.is_dir()
        and not output.exists()
        and output.parent.is_dir()
        and not output.is_relative_to(root)
        and not root.is_relative_to(output),
        "INITIALIZATION_PATH",
    )
    for name, sha in PINS.items():
        require(file_hash(root / name) == sha, "INITIALIZATION_PIN")
    require((root / "world").exists() is (not initial), "INITIALIZATION_WORLD")
    require(inspect_e9e_mode(root, "server")["file_result"] == "pass", "INITIALIZATION_MODE")
    properties = (root / "server.properties").read_text(encoding="utf-8")
    for key, value in {
        "server-ip": "127.0.0.1",
        "server-port": "25603",
        "online-mode": "true",
        "level-name": "world",
        "enable-rcon": "false",
        "rcon.password": "",
        "enable-query": "false",
        "enable-command-block": "false",
    }.items():
        require(
            re.findall(r"(?m)^" + re.escape(key) + r"=(.*)$", properties) == [value],
            "INITIALIZATION_PROPERTIES",
        )
    require(
        re.findall(r"(?m)^eula=(true|false)\s*$", (root / "eula.txt").read_text()) == ["true"],
        "AWAITING_OPERATOR_EULA",
    )
    with socket.socket() as listener:
        if os.name == "nt":
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        listener.bind(("127.0.0.1", 25603))
    return root, output


def run(root, output, *, campaign, epoch, initial, runtime_data=None):
    root, output = validate(root, output, initial=initial)
    data_report = None
    if runtime_data is not None:
        safe(runtime_data)
        data_report = validate_snapshot(Path(runtime_data).read_bytes(), (root / AGENT_PATH).read_bytes())
    profile = "e9e1270-installed-forge-cold-start/2" if data_report else PROFILE
    output.mkdir()
    authority = issue_authority(
        output / "authority", root, instance_id=campaign, campaign_id=campaign, epoch=epoch
    )
    spool, temp = output / "spool", output / "temp"
    spool.mkdir()
    temp.mkdir()
    config = output / "telemetry.json"
    write(
        config,
        {
            "schema": "strata/ForgeTelemetryConfig/3",
            "campaign_id": campaign,
            "epoch": epoch,
            "spool_directory": str(spool),
            "max_bytes": 16 * 1024**2,
            "max_events": 10000,
            "recipe_ids": [RECIPE],
            "config_queries": QUERIES,
            "authentication": authority.producer_config(),
        },
    )
    exe = root / "java/bin/java.exe"
    argv = [str(exe), "-XX:ActiveProcessorCount=4", "-Xms2G", "-Xmx5G", "@" + ARGS, "nogui"]
    if data_report:
        argv.insert(1, "-javaagent:" + str(root / AGENT_PATH))
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    environment.update(
        JAVA_HOME=str(root / "java"),
        PATH=str(exe.parent),
        TEMP=str(temp),
        TMP=str(temp),
        STRATA_TELEMETRY_CONFIG=str(config),
    )
    trees = [
        root / name
        for name in ("java", "libraries", "mods", "kubejs/server_scripts", "kubejs/startup_scripts")
    ]
    held = snapshot(
        [
            config,
            Path(authority.key_file),
            Path(sys._base_executable),
            Path(__file__).resolve().parents[1] / "src/mcbench/process_bootstrap.py",
            *([Path(runtime_data), root / AGENT_PATH] if data_report else []),
        ],
        trees,
    )
    write(
        output / "launch.json",
        {
            "profile": profile,
            "argv": argv,
            "cwd": str(root),
            "environment": environment,
            "initial": initial,
            "max_wall_s": 300,
            "ready_run_s": 10,
            "graceful_stop_s": 120,
            "outer_watchdog_s": 425,
            "immutable_inventory": held,
        },
    )
    result = {
        "schema": "strata/E9EColdStartResult/1",
        "profile": profile,
        "status": "fail",
        "initial": initial,
        "campaign_admission": False,
        "isolation_qualified": False,
        "clean_save_proven": False,
        "ready": False,
        "forced_stop": False,
    }
    ready, bad_log, deadline = threading.Event(), threading.Event(), threading.Event()
    readers = []

    def copy(source, path):
        try:
            with path.open("xb") as stream:
                count = 0
                for line in iter(lambda: source.readline(65536), b""):
                    count += len(line)
                    require(count <= 16 * 1024**2, "INITIALIZATION_LOG_QUOTA")
                    stream.write(line)
                    stream.flush()
                    if re.search(rb'Done \([0-9.,]+s\)! For help, type "help"', line):
                        ready.set()
        except BaseException:
            bad_log.set()

    with FileLease(held) as lease:
        started, bound_at, stopping, proc = time.monotonic(), None, None, None
        watchdog = None
        try:
            proc = ManagedProcess(
                argv,
                root,
                environment,
                "",
                interactive=True,
                bootstrap_python=Path(sys._base_executable),
            )

            def force():
                deadline.set()
                result["forced_stop"] = True
                proc.stop()

            watchdog = threading.Timer(425, force)
            watchdog.daemon = True
            watchdog.start()
            for source, name in (
                (proc.process.stdout, "stdout.log"),
                (proc.process.stderr, "stderr.log"),
            ):
                thread = threading.Thread(target=copy, args=(source, output / name), daemon=True)
                thread.start()
                readers.append(thread)
            while proc.poll() is None:
                proc.job.observe_members()
                require(not bad_log.is_set() and not deadline.is_set(), "INITIALIZATION_EVIDENCE")
                if bound_at is None:
                    first = first_start(spool, authority)
                    if first is not None:
                        _, event, payload = first
                        plan = SimpleNamespace(
                            executable=SimpleNamespace(path=str(exe)),
                            module_file=SimpleNamespace(
                                path=str(root / MODULE), sha256=PINS[MODULE]
                            ),
                            server_port=25603,
                        )
                        setup = SimpleNamespace(
                            game_directory=str(root), fixture_directory=str(root / "world")
                        )
                        result["binding"] = bind_identity(
                            plan,
                            setup,
                            payload.launch_identity,
                            proc.job.member_identity(payload.launch_identity.pid),
                        )
                        result["server_boot_id"] = event.server_boot_id
                        bound_at = time.monotonic()
                now = time.monotonic()
                result["ready"] = ready.is_set()
                if stopping is None and (
                    now - started >= 300
                    or ready.is_set()
                    and bound_at is not None
                    and now - bound_at >= 10
                ):
                    stopping = now
                    proc.send_input("stop\n")
                    result["stop_sent"] = True
                if stopping is not None and now - stopping >= 120:
                    result["forced_stop"] = True
                    proc.stop()
                    break
                time.sleep(0.05)
            result["exit_code"] = proc.process.wait(timeout=2)
            result["job"] = proc.job.accounting()
            result["held"] = proc.job.member_status()
            require(
                result["job"]["active_processes"] == result["job"]["terminated_processes"] == 0
                and 0
                < result["job"]["total_processes"]
                == result["held"]["held_processes"]
                == result["held"]["signaled_processes"],
                "INITIALIZATION_STOP",
            )
            for reader in readers:
                reader.join(2)
            require(
                not any(r.is_alive() for r in readers) and not bad_log.is_set(),
                "INITIALIZATION_EVIDENCE",
            )
            result["log_health"] = {
                name: inspect_server_log(output / name) for name in ("stdout.log", "stderr.log")
            }
            require(
                all(r["result"] == "pass" for r in result["log_health"].values()),
                "INITIALIZATION_RUNTIME",
            )
            require(
                result["ready"]
                and result.get("stop_sent")
                and bound_at is not None
                and result["exit_code"] == 0
                and not result["forced_stop"]
                and not deadline.is_set(),
                "INITIALIZATION_LIFECYCLE",
            )
            if data_report:
                result["runtime_data"] = inspect_runtime_data_log((output / "stderr.log").read_bytes(), data_report)
            lease.recheck()
            files = list(spool.glob("*.authenticated.jsonl"))
            require(len(files) == 1, "INITIALIZATION_SPOOL")
            inspection = inspect_authenticated_spool(files[0], output / "authority/authority.json")
            write(output / "inspection.json", inspection)
            write(
                output / "effective-files.json",
                inspect_e9e_mode(root, "server", effective=True, world="world"),
            )
            result["status"] = "pass"
        except BaseException as error:
            result["error_code"] = getattr(error, "code", type(error).__name__)
            raise
        finally:
            if watchdog:
                watchdog.cancel()
                watchdog.join(3)
            if proc:
                if proc.poll() is None:
                    result["forced_stop"] = True
                    proc.stop()
                result["terminal_job"] = proc.job.accounting()
                result["terminal_held"] = proc.job.member_status()
                for reader in readers:
                    reader.join(2)
                proc.close()
            result["elapsed_s"] = time.monotonic() - started
            write(output / "result.json", result)
    return result


def inspect_runtime_data_log(raw, report):
    """Require both transformed classes and actual reads, not agent startup alone."""
    require(len(raw) <= 16 * 1024**2 and b"STRATA_FIXED_DATA_REFUSED/1" not in raw, "RUNTIME_DATA_EXECUTION")
    lines = [line[line.index("STRATA_FIXED_DATA_"):] for line in raw.decode("utf-8", errors="strict").splitlines()
             if "STRATA_FIXED_DATA_" in line]
    require("STRATA_FIXED_DATA_READY/1 " + report["index_sha256"] in lines, "RUNTIME_DATA_EXECUTION")
    classes = {
        "com/portingdeadmods/cable_facades/CFConfig": "601b70c83a14debbb5e4679196a319c1a31eab4d4b008cd33b1feca2551bda0d",
        "blusunrize/immersiveengineering/ImmersiveEngineering$ThreadContributorSpecialsDownloader":
            "b47bfd98a885800760e9e7d7c24d60ec2d4e89da6cbc1ed9ad1e82a46283e2fb",
    }
    required = {"STRATA_FIXED_DATA_BOUND/1 " + name + " " + sha for name, sha in classes.items()}
    required.update("STRATA_FIXED_DATA_READ/1 " + r["name"] + " " + r["sha256"] for r in report["inputs"])
    require(required <= set(lines), "RUNTIME_DATA_EXECUTION")
    return {"policy": report["policy"], "jar_sha256": report["jar_sha256"],
            "index_sha256": report["index_sha256"], "bound_classes": sorted(classes),
            "read_inputs": [{"name": r["name"], "sha256": r["sha256"]} for r in report["inputs"]],
            "all_runtime_downloads_qualified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--initial", action="store_true")
    parser.add_argument("--runtime-data", type=Path)
    args = parser.parse_args()
    print(
        run(args.root, args.output, campaign=args.campaign, epoch=args.epoch, initial=args.initial, runtime_data=args.runtime_data)
    )
