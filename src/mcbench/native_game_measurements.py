"""Private joins for the explicitly instrumented native vanilla pilot.

These are observed callback/resource intervals, not a capacity certificate or
an active-campaign clock. The caller supplies stopped-file custody (and, for
offline use, a verified evidence bundle); archived absolute paths are data.
"""

import hashlib
import math
from pathlib import Path, PureWindowsPath
import re
import zipfile

from .inference_transport import strict_json
from .inventory import file_hash
from .storage import digest, reject_links, require
from .vanilla_clock import inspect_vanilla_clock
from .vanilla_persistence import verify_snapshot
from .worker_health import health_required, inspect_worker_health

SCOPE = ("campaign_id", "agent_id", "epoch")
POLICY = "native-vanilla-callback-resource-join/1"
TIMING_KINDS = ("run_started", "server_launch_requested", "worker_launch_requested", "avatar_ready",
                "native_started", "native_finished", "worker_close_requested", "worker_closed",
                "server_stop_requested", "server_closed", "run_finished")


def inspect_timing(path, clock, health):
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= 65536, "NATIVE_TIMING_INCOMPLETE")
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    require(len(lines) == len(TIMING_KINDS) and all(line.endswith(b"\n") for line in lines),
            "NATIVE_TIMING_INCOMPLETE")
    events = [strict_json(line) for line in lines]
    previous = 0
    for seq, (event, kind) in enumerate(zip(events, TIMING_KINDS), 1):
        require(set(event) == {"seq", "kind", "mono_ns", "unix"}
                and type(event["seq"]) is int and event["seq"] == seq and event["kind"] == kind
                and type(event["mono_ns"]) is int and event["mono_ns"] > previous
                and type(event["unix"]) in (int, float) and math.isfinite(event["unix"]) and event["unix"] > 0,
                "NATIVE_TIMING_ORDER")
        previous = event["mono_ns"]
    stamps = {e["kind"]: e["mono_ns"] for e in events}
    native_ns = stamps["native_finished"] - stamps["native_started"]
    worker_ns = stamps["worker_closed"] - stamps["worker_launch_requested"]
    server_ns = stamps["server_closed"] - stamps["server_launch_requested"]
    require(0 < health["elapsed_ns"] <= worker_ns and 0 < clock["run_elapsed_ns"] <= server_ns,
            "NATIVE_TIMING_EXPOSURE")
    return {"schema": "strata/NativePilotTiming/1", "clock": "python-monotonic-ns/same-host-boot",
        "source_sha256": hashlib.sha256(raw).hexdigest(), "events": events,
        "native_harness_including_thinking_ns": native_ns,
        "worker_launch_through_close_ns": worker_ns, "server_launch_through_close_ns": server_ns,
        "wrapper_ns": stamps["run_finished"] - stamps["run_started"],
        "segments": [{"from": a["kind"], "to": b["kind"], "elapsed_ns": b["mono_ns"] - a["mono_ns"]}
                     for a, b in zip(events, events[1:])],
        "segments_partition_wrapper": True, "nested_intervals_are_not_additive": True,
        "unix_clock_used_for_durations": False, "active_campaign_clock_qualified": False}


def bind_clock_overlay(base, clock, worker, job_id, runtime_files):
    require(isinstance(clock, dict) and set(clock) ==
            {"agent_path", "agent_sha256", *SCOPE, "run_id"}, "NATIVE_MEASUREMENT_PROFILE")
    require(base.get("schema") == "strata/DevelopmentServer/5" and base.get("target") == "vanilla"
            and worker.get("server_kind") == "vanilla"
            and all(clock[k] == worker[k] and type(clock[k]) is type(worker[k]) for k in SCOPE)
            and clock["run_id"] == job_id, "NATIVE_MEASUREMENT_SCOPE")
    require(all(isinstance(clock[k], str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", clock[k])
                for k in ("campaign_id", "agent_id", "run_id"))
            and type(clock["epoch"]) is int and 1 <= clock["epoch"] <= 999999999
            and isinstance(clock["agent_sha256"], str) and re.fullmatch("[0-9a-f]{64}", clock["agent_sha256"])
            and isinstance(clock["agent_path"], str) and PureWindowsPath(clock["agent_path"]).is_absolute(),
            "NATIVE_MEASUREMENT_PROFILE")
    require(health_required(e["path"] for e in runtime_files), "WORKER_HEALTH_REQUIRED")
    return {"schema": "strata/DevelopmentServer/6", "base": base, "clock": dict(clock)}


def read_json(path):
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= 8 * 1024**2, "NATIVE_MEASUREMENT_INPUT")
    return strict_json(path.read_bytes())


def inspect_measurements(output, server_plan, worker, server, stored_health, job_id, worker_db):
    """Recompute both streams and join one saved body; never follow plan paths."""
    output = Path(output)
    require(set(server_plan) == {"schema", "base", "clock"}
            and server_plan["schema"] == "strata/DevelopmentServer/6", "NATIVE_MEASUREMENT_PROFILE")
    runtime = read_json(output / "worker-runtime.json")
    # The held runtime receipt is the membership authority, not an installed
    # checkout or a plausible module name from a caller's environment.
    runtime_files = runtime["inventory"]["files"]
    require(bind_clock_overlay(server_plan["base"], server_plan["clock"], worker, job_id, runtime_files)
            == server_plan and read_json(output / "server/plan.json") == server_plan
            and read_json(output / "worker-config.json") == worker, "NATIVE_MEASUREMENT_PROFILE")
    require(server == read_json(output / "server/result.json")
            and server["status"] == "stopped_unqualified" and server["plan_digest"] == digest(server_plan)
            and server["ready"] is True and server["stop_sent"] is True
            and server["forced_stop"] is False and server["exit_code"] == 0,
            "NATIVE_MEASUREMENT_STOP")
    selected = server_plan["clock"]
    module = output / "vanilla-clock-agent.jar"
    reject_links(module)
    require(module.stat().st_size <= 1024**2 and file_hash(module) == selected["agent_sha256"],
            "VANILLA_CLOCK_AGENT_PIN")
    launch = read_json(output / "server/clock-launch.json")
    require(launch == server["vanilla_clock"]["launch_binding"]
            and launch["composite_launch_digest"] == digest({k: v for k, v in launch.items()
                                                           if k != "composite_launch_digest"})
            and launch["agent_sha256"] == selected["agent_sha256"]
            and all(launch[k] == selected[k] for k in (*SCOPE, "run_id"))
            and launch["original_pack_profile_unchanged_claim"] is False
            and launch["campaign_admission"] is False, "NATIVE_MEASUREMENT_LAUNCH")
    base_launch = read_json(output / "server/pack-launch.json")["launch"]
    def dos(value):
        value = str(PureWindowsPath(value))
        return "\\\\" + value[8:] if value.startswith("\\\\?\\UNC\\") else value.removeprefix("\\\\?\\")

    server_directory = PureWindowsPath(server_plan["base"]["evidence"])
    expected_config = "".join(f"{k}={v}\n" for k, v in {
        **{k: selected[k] for k in (*SCOPE, "run_id")},
        "output": dos(server_directory / "vanilla-clock.jsonl")}.items()).encode()
    require((output / "server/vanilla-clock.config").read_bytes() == expected_config,
            "NATIVE_MEASUREMENT_LAUNCH")
    require(launch["base_launch_digest"] == digest(base_launch)
            and launch["arguments"] == [f"-javaagent:{dos(selected['agent_path'])}="
                f"{dos(server_directory / 'vanilla-clock.config')}", *base_launch["arguments"]],
            "NATIVE_MEASUREMENT_LAUNCH")
    for name, key in (("vanilla-clock.config", "configuration_sha256"),
                      ("vanilla-clock-callbacks.jar", "callbacks_sha256")):
        path = output / "server" / name
        reject_links(path)
        require(file_hash(path) == launch[key], "NATIVE_MEASUREMENT_LAUNCH")
    with zipfile.ZipFile(module) as jar:
        require(jar.getinfo("strata-clock-callbacks.jar").file_size <= 262144
                and hashlib.sha256(jar.read("strata-clock-callbacks.jar")).hexdigest() == launch["callbacks_sha256"],
                "VANILLA_CLOCK_AGENT_PIN")
    stored = server["vanilla_clock"]
    require(PureWindowsPath(dos(stored["owned_jvm"]["executable"])) ==
            PureWindowsPath(dos(base_launch["executable_path"])), "NATIVE_MEASUREMENT_LAUNCH")
    scope = {k: selected[k] for k in (*SCOPE, "run_id")}
    clock = inspect_vanilla_clock(output / "server/vanilla-clock.jsonl", scope=scope,
        module_sha256=selected["agent_sha256"], pid=stored["owned_jvm"]["pid"],
        expected_sha256=stored["source_sha256"])
    require(stored == clock | {k: stored[k] for k in ("owned_jvm", "owned_processes", "launch_binding")},
            "NATIVE_MEASUREMENT_CHANGED")
    snapshot_sha = server["stopped_snapshot"]["manifest_sha256"]
    snapshot = verify_snapshot(output / "server/stopped-instance", snapshot_sha)
    require(snapshot["server_plan_digest"] == digest(server_plan)
            and snapshot["pack"]["lock"] == server_plan["base"]["pack"]["lock"]
            and stored["owned_processes"] == {k: snapshot["owned_processes"][k] for k in ("job", "held")},
            "NATIVE_MEASUREMENT_SNAPSHOT")
    players = [p for p in snapshot["files"] if p.startswith("world/playerdata/") and p.endswith(".dat")]
    require(len(players) == 1 and snapshot["files"][players[0]]["disposition"] == "state",
            "NATIVE_MEASUREMENT_ROSTER")
    player = Path(players[0]).stem
    require(set(clock["avatar_tick_events"]) == {player} and clock["avatar_tick_events"][player] > 0,
            "NATIVE_MEASUREMENT_ROSTER")
    health = inspect_worker_health(worker_db, **{k: worker[k] for k in SCOPE}, required=True)
    require(health == stored_health, "NATIVE_MEASUREMENT_CHANGED")
    timing = inspect_timing(output / "pilot-timing.jsonl", clock, health)
    return {"schema": "strata/NativeGameMeasurements/1", "policy": POLICY, "visibility": "evaluator",
        **scope, "server_plan_digest": digest(server_plan), "composite_launch_digest": launch["composite_launch_digest"],
        "snapshot_sha256": snapshot_sha, "saved_player_uuid": player,
        "saved_player_sha256": snapshot["files"][players[0]]["sha256"],
        "clock": clock, "worker_health": health, "timing": timing, "intervals_are_not_additive": True,
        "active_wall_s": None, "capacity_qualified": False, "isolation_qualified": False,
        "complete_checkpoint": False,
        "gaps": ["native_cost_and_active_time_join", "worker_process_identity_join",
                 "telemetry_overhead_control", "rolling_capacity_qualification"]}
