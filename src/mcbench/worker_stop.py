"""One-use normal drain over an owned operator pipe, with retained stop evidence."""

import math
import os
from pathlib import Path
import time
from typing import Literal
import uuid

from pydantic import Field

from .contracts import Id, Positive, Strict
from .inference_transport import strict_json
from .storage import canonical, reject_links, require

POLICY = "operator-stdin-stop2250/1"
ARGUMENT = "--operator-stop"
DRAIN_MS = 2250
SCOPE = ("campaign_id", "agent_id", "epoch", "lease_id")


class WorkerStop(Strict):
    schema_: Literal["strata/WorkerStop/1"] = Field(alias="schema")
    policy: Literal["operator-stdin-stop2250/1"]
    request_id: Id
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    lease_id: Id


def verify_worker_stop(request, receipt):
    request = WorkerStop.model_validate(request).model_dump()
    require(isinstance(receipt, dict) and set(receipt) == {
        "schema", "policy", "scope", "request", "received_mono_ms", "child_exit_mono_ms",
        "elapsed_ms", "drain_limit_ms", "exit_code", "forced", "status",
        "complete_checkpoint", "shutdown_gate_qualified"}, "WORKER_STOP_RECEIPT")
    started, ended, elapsed = (receipt[k] for k in ("received_mono_ms", "child_exit_mono_ms", "elapsed_ms"))
    require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (started, ended, elapsed))
            and started <= ended and elapsed == ended - started and elapsed <= DRAIN_MS,
            "WORKER_STOP_CLOCK")
    require(canonical(receipt) == canonical({"schema": "strata/WorkerStopReceipt/1", "policy": POLICY,
        "scope": {k: request[k] for k in SCOPE}, "request": request,
        "received_mono_ms": started, "child_exit_mono_ms": ended, "elapsed_ms": elapsed,
        "drain_limit_ms": DRAIN_MS, "exit_code": 0, "forced": False, "status": "pass",
        "complete_checkpoint": False, "shutdown_gate_qualified": False})
        and type(receipt["exit_code"]) is int and type(receipt["drain_limit_ms"]) is int
        and receipt["forced"] is False and receipt["complete_checkpoint"] is False
        and receipt["shutdown_gate_qualified"] is False, "WORKER_STOP_RECEIPT")
    return receipt


def stop_owned_worker(process, configuration, output, wait):
    """Persist intent before sending once. Any ambiguity remains failed, never replayed."""
    output = Path(output)
    reject_links(output)
    require(process.poll() is None and process.interactive, "WORKER_STOP_PROCESS")
    request = WorkerStop.model_validate({"schema": "strata/WorkerStop/1", "policy": POLICY,
        "request_id": "worker-stop-" + uuid.uuid4().hex, **{k: configuration[k] for k in SCOPE}}).model_dump()
    receipt_path = Path(configuration["state_directory"]) / f"supervisor-stop-{configuration['epoch']}.json"
    reject_links(receipt_path)
    require(not receipt_path.exists(), "WORKER_STOP_ALREADY_RECORDED")
    started, unix = time.monotonic_ns(), time.time()
    intent = {"schema": "strata/WorkerStopIntent/1", "request": request,
              "requested_mono_ns": started, "requested_unix": unix}
    with (output / "worker-stop-intent.json").open("xb") as stream:
        stream.write(canonical(intent))
        stream.flush()
        os.fsync(stream.fileno())
    process.send_input(canonical(request).decode() + "\n", timeout_s=1)
    wait(lambda: process.poll() is not None, 5, "WORKER_STOP_TIMEOUT")
    ended = time.monotonic_ns()
    require(process.poll() == 0 and ended - started <= 5_000_000_000, "WORKER_STOP_PROCESS")
    require(receipt_path.is_file() and receipt_path.stat().st_size <= 8192, "WORKER_STOP_RECEIPT")
    reject_links(receipt_path)
    receipt = verify_worker_stop(request, strict_json(receipt_path.read_bytes()))
    require(process.job is not None, "WORKER_STOP_PROCESS")
    job = process.job.accounting()
    require(job["active_processes"] == job["terminated_processes"] == 0, "WORKER_STOP_PROCESS")
    return {"schema": "strata/OwnedWorkerStop/1", "intent": intent, "receipt": receipt,
            "exited_mono_ns": ended, "owner_elapsed_ms": (ended - started) / 1_000_000,
            "owned_processes": job, "shutdown_gate_qualified": False, "complete_checkpoint": False}
