"""Reconcile operator stop intent and child/owner exit clocks in sealed evidence."""

import math

from mcbench.storage import canonical, require
from mcbench.inference_transport import strict_json
from mcbench.worker_stop import SCOPE, verify_worker_stop


def inspect_worker_stop(bundle, result):
    intent = bundle.json("run/worker-stop-intent.json")
    config = bundle.json("run/worker-config.json")
    receipt = bundle.json(f"run/worker/supervisor-stop-{config['epoch']}.json")
    require(set(intent) == {"schema", "request", "requested_mono_ns", "requested_unix"}
            and intent["schema"] == "strata/WorkerStopIntent/1", "NATIVE_GAME_WORKER_STOP_INTENT")
    require(canonical({k: intent["request"][k] for k in SCOPE}) == canonical({k: config[k] for k in SCOPE}),
            "NATIVE_GAME_WORKER_STOP_SCOPE")
    verify_worker_stop(intent["request"], receipt)
    owned = result["worker_stop"]
    require(set(owned) == {"schema", "intent", "receipt", "exited_mono_ns", "owner_elapsed_ms",
                          "owned_processes", "shutdown_gate_qualified", "complete_checkpoint"},
            "NATIVE_GAME_WORKER_STOP_RECEIPT")
    start, end, elapsed, unix = intent["requested_mono_ns"], owned["exited_mono_ns"], owned["owner_elapsed_ms"], intent["requested_unix"]
    require(type(start) is int and type(end) is int and 0 < start <= end
            and all(type(v) in (int, float) and math.isfinite(v) for v in (elapsed, unix))
            and elapsed == (end - start) / 1_000_000 and 0 <= elapsed <= 5000 and unix > 0,
            "NATIVE_GAME_WORKER_STOP_CLOCK")
    require(owned["schema"] == "strata/OwnedWorkerStop/1"
            and canonical(owned["intent"]) == canonical(intent) and canonical(owned["receipt"]) == canonical(receipt)
            and owned["shutdown_gate_qualified"] is False and owned["complete_checkpoint"] is False,
            "NATIVE_GAME_WORKER_STOP_RECEIPT")
    job = owned["owned_processes"]
    require(all(type(job[k]) is int and job[k] == 0 for k in ("active_processes", "terminated_processes")),
            "NATIVE_GAME_WORKER_STOP_PROCESS")
    if "sealed_worker_receipt" in result:
        require(canonical(job) == canonical(result["sealed_worker_receipt"]["owned_processes"]["worker"]["job"]),
                "NATIVE_GAME_WORKER_STOP_PROCESS")
    return {"operator_request_verified": True, "worker_drain_ms": receipt["elapsed_ms"],
            "owner_stop_ms": elapsed, "shutdown_gate_qualified": False, "complete_checkpoint": False}


def inspect_normal_boundary(bundle, result, server):
    """Observed owned-process intervals only; simulation ticks and save custody remain open."""
    boundary = bundle.json("run/server/stop.request")
    require(set(boundary) == {"schema", "worker_stop_request_id", "requested_mono_ns", "requested_unix"}
            and boundary["schema"] == "strata/WorkerServerStopBoundary/1"
            and boundary["worker_stop_request_id"] == result["worker_stop"]["intent"]["request"]["request_id"]
            and canonical(boundary) == canonical(result["server_stop_intent"]), "NATIVE_GAME_STOP_BOUNDARY")
    events = [strict_json(line) for line in bundle.read("run/server/lifecycle.jsonl").splitlines()]
    kinds = ["spawn_requested", "spawned", "ready", "stop_command_attempted", "stop_command_written",
             "process_exited", "snapshot_started", "snapshot_captured"]
    require([v["kind"] for v in events] == kinds, "NATIVE_GAME_SERVER_LIFECYCLE")
    for i, value in enumerate(events, 1):
        require(set(value) == {"seq", "kind", "mono_ns", "unix"}
                | ({"trigger"} if value["kind"] == "stop_command_attempted" else set())
                and type(value["seq"]) is int and value["seq"] == i
                and type(value["mono_ns"]) is int and value["mono_ns"] > 0
                and type(value["unix"]) in (int, float) and math.isfinite(value["unix"]) and value["unix"] > 0,
                "NATIVE_GAME_SERVER_LIFECYCLE")
    require(canonical(server["lifecycle"]) == canonical({"schema": "strata/ServerLifecycle/1",
        "clock": "python-monotonic-ns/same-host-boot", "events": events,
        "authoritative_ticks": False, "clean_save_proven": False}), "NATIVE_GAME_SERVER_LIFECYCLE")
    by_kind = {value["kind"]: value for value in events}
    require(all(a["mono_ns"] <= b["mono_ns"] for a, b in zip(events, events[1:]))
            and by_kind["stop_command_attempted"]["trigger"] == "operator_file"
            and type(boundary["requested_mono_ns"]) is int
            and result["worker_stop"]["exited_mono_ns"] <= boundary["requested_mono_ns"]
            <= by_kind["stop_command_attempted"]["mono_ns"]
            and type(boundary["requested_unix"]) in (int, float) and math.isfinite(boundary["requested_unix"])
            and result["worker_stop"]["intent"]["requested_unix"] <= boundary["requested_unix"]
            <= by_kind["stop_command_attempted"]["unix"], "NATIVE_GAME_STOP_ORDER")
    save_ms = (by_kind["process_exited"]["mono_ns"] - by_kind["stop_command_attempted"]["mono_ns"]) / 1_000_000
    require(save_ms <= 120_000, "NATIVE_GAME_SERVER_STOP_DEADLINE")
    return {"worker_to_server_request_ms": (boundary["requested_mono_ns"] - result["worker_stop"]["exited_mono_ns"]) / 1_000_000,
        "server_stop_through_exit_ms": save_ms,
        "capture_ms": (by_kind["snapshot_captured"]["mono_ns"] - by_kind["snapshot_started"]["mono_ns"]) / 1_000_000,
        "observed_lifecycle_only": True, "authoritative_ticks": False, "clean_save_proven": False}
