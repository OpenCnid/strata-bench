"""Synthetic records and real owned Node processes; no game, auth or inference."""

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
import time

import pytest

from mcbench.processes import ManagedProcess
from mcbench.storage import Fault, canonical
from mcbench.worker_stop import POLICY, stop_owned_worker, verify_worker_stop
from strata_evaluator.native_game_stop import inspect_normal_boundary, inspect_worker_stop

SCOPE = {"campaign_id": "fixture", "agent_id": "avatar", "epoch": 2, "lease_id": "new-lease"}
REQUEST = {"schema": "strata/WorkerStop/1", "policy": POLICY, "request_id": "stop-1", **SCOPE}


def receipt():
    return {"schema": "strata/WorkerStopReceipt/1", "policy": POLICY, "scope": SCOPE.copy(),
        "request": deepcopy(REQUEST), "received_mono_ms": 100, "child_exit_mono_ms": 240,
        "elapsed_ms": 140, "drain_limit_ms": 2250, "exit_code": 0, "forced": False,
        "status": "pass", "complete_checkpoint": False, "shutdown_gate_qualified": False}


def test_receipt_validates_measured_drain_without_qualifying_emergency_stop_or_save():
    assert verify_worker_stop(REQUEST, receipt()) == receipt()


@pytest.mark.parametrize("change", ["scope", "lease", "request", "policy", "forced", "failed", "exit",
    "extra", "time", "nan", "bound", "late", "bool-epoch", "bool-exit", "checkpoint", "shutdown"])
def test_invalid_or_ambiguous_receipt_cannot_be_reported_as_normal_stop(change):
    r = receipt()
    if change == "scope":
        r["scope"]["epoch"] = 1
    elif change == "lease":
        r["request"]["lease_id"] = "old"
    elif change == "request":
        r["request"]["request_id"] = "different"
    elif change == "bool-epoch":
        r["scope"]["epoch"] = True
    elif change == "late":
        r.update(child_exit_mono_ms=2351, elapsed_ms=2251)
    else:
        key, value = {"policy": ("policy", "unknown"), "forced": ("forced", True),
            "failed": ("status", "fail"), "exit": ("exit_code", 1), "extra": ("extra", 0),
            "time": ("elapsed_ms", 1), "nan": ("received_mono_ms", float("nan")),
            "bound": ("drain_limit_ms", 3000), "bool-exit": ("exit_code", False),
            "checkpoint": ("complete_checkpoint", True), "shutdown": ("shutdown_gate_qualified", True)}[change]
        r[key] = value
    with pytest.raises(Fault):
        verify_worker_stop(REQUEST, r)


def wait(predicate, seconds, code):
    end = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() >= end:
            raise Fault(code)
        time.sleep(.02)


@pytest.mark.parametrize("hang", [False, True])
def test_owned_operator_pipe_drains_real_synthetic_child_or_retains_deadline_failure(tmp_path, hang):
    node = Path(shutil.which("node") or "C:/Program Files/nodejs/node.exe").resolve()
    assert node.is_file(), "pinned Node required for owned-process test"
    root = Path(__file__).resolve().parents[1]
    module = root / "backends/mineflayer/dist/src/worker_control.js"
    assert module.is_file(), "build worker before running this selection"
    state = tmp_path / "state"
    state.mkdir()
    child = tmp_path / "child.cjs"
    child.write_text("const timer=setInterval(()=>{},100);process.on('message',m=>{"
                     + ("" if hang else "if(m==='stop'){clearInterval(timer);process.disconnect();}")
                     + "});process.send('ready');", encoding="utf-8")
    script = tmp_path / "owner.mjs"
    script.write_text("import {fork} from 'node:child_process';import {writeFileSync} from 'node:fs';"
        "import {WorkerControl} from " + json.dumps(module.as_uri()) + ";"
        "const child=fork(" + json.dumps(str(child)) + ",[],{stdio:['ignore','ignore','ignore','ipc'],windowsHide:true});"
        "let forced=false;const control=new WorkerControl(process.stdin," + json.dumps(SCOPE)
        + ",()=>child.send('stop'),()=>{forced=true;child.kill();});"
        "const timer=setInterval(()=>{if(control.expired()){forced=true;child.kill();}},10);"
        "child.once('message',()=>writeFileSync(" + json.dumps(str(tmp_path / "ready")) + ",'ready'));"
        "child.once('exit',code=>{clearInterval(timer);const r=control.receipt(code??1,forced);control.close();"
        "writeFileSync(" + json.dumps(str(state / "supervisor-stop-2.json")) + ",JSON.stringify(r));"
        "process.exitCode=r.status==='pass'?0:1;});", encoding="utf-8")
    process = ManagedProcess([str(node), str(script)], tmp_path,
        {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}, "",
        interactive=True, bootstrap_python=Path(sys._base_executable))
    try:
        wait(lambda: (tmp_path / "ready").exists() or process.poll() is not None, 5, "FIXTURE_START")
        assert process.poll() is None
        config = SCOPE | {"state_directory": str(state)}
        if hang:
            with pytest.raises(Fault, match="WORKER_STOP_PROCESS"):
                stop_owned_worker(process, config, tmp_path, wait)
            failure = json.loads((state / "supervisor-stop-2.json").read_bytes())
            assert failure["forced"] and failure["status"] == "fail" and process.poll() != 0
        else:
            report = stop_owned_worker(process, config, tmp_path, wait)
            assert report["receipt"]["status"] == "pass" and report["owner_elapsed_ms"] < 5000
            assert report["owned_processes"]["active_processes"] == 0 and process.poll() == 0
        before = (tmp_path / "worker-stop-intent.json").read_bytes()
        with pytest.raises(Fault, match="WORKER_STOP_PROCESS"):
            stop_owned_worker(process, config, tmp_path, wait)
        assert (tmp_path / "worker-stop-intent.json").read_bytes() == before
    finally:
        process.close()


@pytest.fixture
def archive():
    r = receipt()
    intent = {"schema": "strata/WorkerStopIntent/1", "request": REQUEST,
              "requested_mono_ns": 100_000_000, "requested_unix": 1000}
    job = {"active_processes": 0, "terminated_processes": 0}
    result = {"worker_stop": {"schema": "strata/OwnedWorkerStop/1", "intent": intent, "receipt": r,
        "exited_mono_ns": 500_000_000, "owner_elapsed_ms": 400, "owned_processes": job,
        "shutdown_gate_qualified": False, "complete_checkpoint": False},
        "sealed_worker_receipt": {"owned_processes": {"worker": {"job": job}}}}
    values = {"run/worker-config.json": SCOPE, "run/worker-stop-intent.json": intent,
              "run/worker/supervisor-stop-2.json": r}
    class Bundle:
        def json(self, name):
            return json.loads(canonical(values[name]))
    return Bundle(), values, result


def test_offline_stop_join_uses_exact_intent_receipt_and_owned_process_evidence(archive):
    bundle, _, result = archive
    assert inspect_worker_stop(bundle, result)["worker_drain_ms"] == 140


@pytest.mark.parametrize("change", ["scope", "intent", "receipt", "elapsed", "job", "late", "claim", "bool-job"])
def test_tampered_operator_stop_join_rejects(archive, change):
    bundle, values, result = archive
    if change == "scope":
        values["run/worker-config.json"] = SCOPE | {"epoch": 1}
    elif change == "intent":
        result["worker_stop"]["intent"] = result["worker_stop"]["intent"] | {"requested_unix": 1001}
    elif change == "receipt":
        result["worker_stop"]["receipt"] = receipt() | {"elapsed_ms": 1}
    elif change == "elapsed":
        result["worker_stop"]["owner_elapsed_ms"] = 1
    elif change == "job":
        result["worker_stop"]["owned_processes"] = {"active_processes": 1, "terminated_processes": 0}
    elif change == "late":
        result["worker_stop"].update(exited_mono_ns=6_100_000_000, owner_elapsed_ms=6000)
    elif change == "bool-job":
        result["worker_stop"]["owned_processes"] = {"active_processes": False, "terminated_processes": 0}
    else:
        result["worker_stop"]["complete_checkpoint"] = True
    with pytest.raises((Fault, KeyError)):
        inspect_worker_stop(bundle, result)


@pytest.mark.parametrize("change", [None, "missing", "order", "trigger", "boundary", "reference", "late", "claim"])
def test_server_stop_and_capture_join_keeps_order_bound_and_qualification_limits(archive, change):
    bundle, values, result = archive
    kinds = ["spawn_requested", "spawned", "ready", "stop_command_attempted", "stop_command_written",
             "process_exited", "snapshot_started", "snapshot_captured"]
    events = [{"seq": i, "kind": kind, "mono_ns": i * 1_000_000_000, "unix": 1000 + i}
              for i, kind in enumerate(kinds, 1)]
    events[3]["trigger"] = "operator_file"
    boundary = {"schema": "strata/WorkerServerStopBoundary/1", "worker_stop_request_id": "stop-1",
                "requested_mono_ns": 3_500_000_000, "requested_unix": 1003.5}
    result["server_stop_intent"] = boundary
    values["run/server/stop.request"] = boundary
    server = {"lifecycle": {"schema": "strata/ServerLifecycle/1", "clock": "python-monotonic-ns/same-host-boot",
                            "events": events, "authoritative_ticks": False, "clean_save_proven": False}}
    if change == "missing":
        events.pop()
    elif change == "order":
        events[4]["mono_ns"] = 1
    elif change == "trigger":
        events[3]["trigger"] = "wall_deadline"
    elif change == "boundary":
        boundary["requested_mono_ns"] = 1
    elif change == "reference":
        boundary["worker_stop_request_id"] = "other"
    elif change == "late":
        for event in events[5:]:
            event["mono_ns"] += 121_000_000_000
    elif change == "claim":
        server["lifecycle"]["clean_save_proven"] = True
    bundle.read = lambda _: b"\n".join(canonical(e) for e in events)
    if change:
        with pytest.raises(Fault):
            inspect_normal_boundary(bundle, result, server)
    else:
        r = inspect_normal_boundary(bundle, result, server)
        assert r["server_stop_through_exit_ms"] == 2000 and r["capture_ms"] == 1000
        assert r["observed_lifecycle_only"] and not r["clean_save_proven"] and not r["authoritative_ticks"]
