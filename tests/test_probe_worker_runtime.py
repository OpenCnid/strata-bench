"""Registered whole-pair runtime with substituted processes, network and JVM.

Actual software/config/account/source custody and stopped SQLite joins run.
"""

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator import probe_worker_runtime as module
from test_probe_pairs import EVALUATOR
from test_probe_saved_body_runtime import launches_v2, process_fixture
from test_probe_worker_inputs import (
    source, inputs, base_candidate, base_installed, sealed_installation,
    copies, custody, configs, base_pair_source, unbound_pair_source, pair_source,
    software_plans, fake_writers, candidate, installed, runtime, account, values,
)
from test_probe_worker_observation import inventory_window, journal, observation

(source, inputs, base_candidate, base_installed, sealed_installation, copies, custody,
 configs, base_pair_source, unbound_pair_source, pair_source, software_plans, fake_writers,
 candidate, installed, runtime, process_fixture) = (
    source, inputs, base_candidate, base_installed, sealed_installation, copies, custody,
    configs, base_pair_source, unbound_pair_source, pair_source, software_plans, fake_writers,
    candidate, installed, runtime, process_fixture)

pytestmark = [pytest.mark.parametrize("directory_fixture", [True]),
              pytest.mark.parametrize("source", [True], indirect=True),
              pytest.mark.parametrize("base_candidate", [True], indirect=True),
              pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
              pytest.mark.parametrize("per_arm_disk_bytes", [1024**3])]


@pytest.fixture
def worker_processes(monkeypatch, example):
    from mcbench.pack_worker import HeldPackWorker
    launched, processes, observations = [], [], {}
    failures = {"kind": None}

    def start(worker, *, preflight=False):
        config = worker.resolved["worker_configuration"]
        mode = "preflight" if preflight else "worker"
        launched.append((mode, config["campaign_id"]))
        state = {"exit": (4 if failures["kind"] == "import" and len(launched) == 2 else 0) if preflight else None,
                 "forced": False}
        job = SimpleNamespace(accounting=lambda: {"active_processes": int(state["exit"] is None),
            "terminated_processes": int(state["forced"]), "total_processes": 1})

        def stop():
            state.update(exit=125, forced=True)

        def send(raw, **kwargs):
            request = json.loads(raw)
            receipt = {"schema": "strata/WorkerStopReceipt/1", "policy": "operator-stdin-stop2250/1",
                       "scope": {k: config[k] for k in ("campaign_id", "agent_id", "epoch", "lease_id")},
                       "request": request, "received_mono_ms": 1, "child_exit_mono_ms": 2, "elapsed_ms": 1,
                       "drain_limit_ms": 2250, "exit_code": 0, "forced": False, "status": "pass",
                       "complete_checkpoint": False, "shutdown_gate_qualified": False}
            path = Path(config["state_directory"]) / f"supervisor-stop-{config['epoch']}.json"
            if failures["kind"] != "stop":
                path.write_bytes(canonical(receipt))
            state["exit"] = 0

        process = SimpleNamespace(poll=lambda: state["exit"], job=job, stop=stop, interactive=not preflight,
            send_input=send, process=SimpleNamespace(stdout=io.BytesIO(), stderr=io.BytesIO()), state=state)
        processes.append(process)
        worker.processes[mode] = process
        if not preflight:
            observed = observation(example, config)
            inventory_window(observed)
            if failures["kind"] == "example":
                observed["is_example"] = True
            if failures["kind"] == "state":
                observed["state"]["health"] = 19
            if failures["kind"] == "early_exit":
                state["exit"] = 4
            descriptor = {"url": "http://127.0.0.1:1234/v1/game", "token": "synthetic-token-value",
                          **{k: config[k] for k in ("campaign_id", "agent_id", "epoch")}}
            observations[config["campaign_id"]] = observed
            if failures["kind"] == "scope":
                descriptor["agent_id"] = "foreign"
            (Path(config["state_directory"]) / f"grant-{config['epoch']}.json").write_bytes(canonical(descriptor))
            journal(config["state_directory"], config, observed)
        return process

    class Transport:
        def __init__(self, descriptor):
            self.descriptor = descriptor
        def __call__(self, request):
            assert request.method == "observe" and request.action is None
            return {"schema": "strata/GameResponse/1", "status": "ok",
                    "result": observations[self.descriptor["campaign_id"]]}

    monkeypatch.setattr(HeldPackWorker, "start", start)
    monkeypatch.setattr(module, "WorkerTransport", Transport)
    return launched, processes, failures


def test_complete_pair_imports_before_servers_then_workers_drain_before_save(
    runtime, candidate, process_fixture, worker_processes, tmp_path, directory_fixture, per_arm_disk_bytes,
    monkeypatch,
):
    service, plans, launches, binding, capacity = runtime
    account(candidate[1].worker_settings.auth_cache)
    invocations = values(service, tmp_path)
    order, processes, _ = worker_processes
    original = module.PairedWorkerReference.event
    events = []
    from strata_evaluator.probe_vanilla_inputs import VanillaProbeInputs
    software_check = VanillaProbeInputs.check
    coordinator_check = module.PairedWorkerReference.check
    software_calls = []
    standalone_calls = []
    member_check = module.PairedWorkerReference.check_workers

    def checked_members(self):
        standalone_calls.append(self)
        return member_check(self)

    def checked_software(self):
        software_calls.append(self)
        return software_check(self)

    def checked_pair(self):
        before = len(software_calls)
        result = coordinator_check(self)
        assert len(software_calls) == before + 1
        return result

    monkeypatch.setattr(VanillaProbeInputs, "check", checked_software)
    monkeypatch.setattr(module.PairedWorkerReference, "check", checked_pair)
    monkeypatch.setattr(module.PairedWorkerReference, "check_workers", checked_members)

    def event(self, arm, phase):
        events.append((arm, phase))
        if phase == "launch_intent":
            assert len([v for v in order if v[0] == "preflight"]) == 2
            for group in invocations.values():
                receipt = Path(group["a1"]["configuration_path"] + ".evidence/preflight-receipt.json")
                proof = json.loads(receipt.read_bytes())
                assert proof["owned_processes"]["preflight"]["returncode"] == 0
                assert proof["owned_processes"]["preflight"]["job"]["active_processes"] == 0
                assert proof["held_through_owned_stop"] and proof["runtime"]["manifest_held"]
            if arm == "experienced":
                state = Path(invocations["initial"]["a1"]["state_directory"])
                with pytest.raises(PermissionError):
                    (state / "actions.sqlite").write_bytes(b"changed")
                output = Path(invocations["initial"]["a1"]["configuration_path"] + ".evidence")
                stopped = json.loads((output / "worker-stop.json").read_bytes())
                custody = json.loads((output / "worker-custody.json").read_bytes())
                delivered = json.loads((output / "initial-observation.json").read_bytes())
                assert stopped["receipt"]["status"] == "pass"
                assert custody["owned_processes"]["worker"]["returncode"] == 0
                assert "machine" not in delivered["state"]["window"]
        if phase == "stop_requested":
            assert all(p.poll() == 0 for p in processes)
        original(self, arm, phase)

    monkeypatch.setattr(module.PairedWorkerReference, "event", event)
    result = service.run_vanilla_worker_reference(EVALUATOR, plans, launches_v2(launches), invocations,
                                                 pack_binding=binding.model_dump())
    assert result["policy"] == module.POLICY
    assert process_fixture[0] == ["initial", "experienced"]
    assert len(standalone_calls) == 2  # One live-body barrier per arm.
    assert [v[0] for v in order] == ["preflight", "preflight", "worker", "worker"]
    assert not result["native_launch_authorized"] and not result["live_initial_state_verified"]
    for group in result["runtime"]["workers"].values():
        assert group["complete_roster_observed_connected"] and not group["live_initial_state_verified"]
        assert group["members"]["a1"]["own_state_projection_verified"]
    assert service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0] == "STOPPED_REFERENCE"
    from mcbench.controller import reserved_resources
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200


@pytest.mark.parametrize("failure", ["import", "scope", "state", "early_exit", "stop", "between_arms", "example",
                                     "import_receipt", "member_binding", "runtime_recheck", "software_scope",
                                     "stop_receipt", "custody_receipt", "ready_binding"])
def test_worker_failure_fences_pair_without_second_server_or_refund(
    runtime, candidate, process_fixture, worker_processes, tmp_path, directory_fixture, per_arm_disk_bytes, failure, monkeypatch,
):
    service, plans, launches, binding, capacity = runtime
    account(candidate[1].worker_settings.auth_cache)
    _, processes, failures = worker_processes
    failures["kind"] = failure
    invocations = values(service, tmp_path)
    if failure in {"import_receipt", "stop_receipt", "custody_receipt"}:
        original_write = module.PairedWorkerReference._write
        def write(self, output, name, value):
            if failure == "import_receipt" and name == "preflight-receipt.json" and "experienced" in output.name:
                raise Fault("WORKER_RECEIPT_WRITE_FAILED")
            if name == {"stop_receipt": "worker-stop.json", "custody_receipt": "worker-custody.json"}.get(failure):
                raise Fault("WORKER_RECEIPT_WRITE_FAILED")
            return original_write(self, output, name, value)
        monkeypatch.setattr(module.PairedWorkerReference, "_write", write)
    if failure in {"member_binding", "runtime_recheck", "software_scope", "ready_binding"}:
        original = module.PairedWorkerReference.event
        def changed(self, arm, phase):
            if ((failure == "ready_binding" and arm == "initial" and phase == "server_ready")
                    or (failure != "ready_binding" and arm == "experienced" and phase == "initial_state_held")):
                if failure == "software_scope":
                    self.inputs.software = object()
                elif failure in {"member_binding", "ready_binding"}:
                    self.inputs._binding_refs[arm, "a1"] = "cas:sha256:" + "a" * 64
                else:
                    def invalid():
                        raise Fault("WORKER_RUNTIME_CHANGED")
                    monkeypatch.setattr(self.workers[arm]["a1"].runtime, "recheck", invalid)
            original(self, arm, phase)
        monkeypatch.setattr(module.PairedWorkerReference, "event", changed)
    if failure == "between_arms":
        original = module.PairedWorkerReference.event
        def changed(self, arm, phase):
            if arm == "experienced" and phase == "launch_intent":
                service.db.connection.execute("UPDATE accounts SET category='training' WHERE id='initial-account'")
            original(self, arm, phase)
        monkeypatch.setattr(module.PairedWorkerReference, "event", changed)
    with pytest.raises(Fault, match="PROBE_|WORKER_"):
        service.run_vanilla_worker_reference(EVALUATOR, plans, launches_v2(launches), invocations,
                                              pack_binding=binding.model_dump())
    assert process_fixture[0] == ([] if failure in {"import", "import_receipt", "member_binding", "runtime_recheck", "software_scope"}
                                  else ["initial"])
    if failure == "import_receipt":
        assert Path(invocations["initial"]["a1"]["configuration_path"] + ".evidence/preflight-receipt.json").is_file()
        assert not Path(invocations["experienced"]["a1"]["configuration_path"] + ".evidence/preflight-receipt.json").exists()
    if failure in {"state", "stop_receipt", "custody_receipt"}:
        output = Path(invocations["initial"]["a1"]["configuration_path"] + ".evidence")
        assert (output / "worker-stop.json").is_file() == (failure != "stop_receipt")
        assert (output / "worker-custody.json").is_file() == (failure == "state")
        assert not (output / "worker-result.json").exists()
    if failure == "ready_binding":
        assert len(processes) == 2 and all(not p.interactive for p in processes)
    assert all(p.poll() is not None for p in processes)
    assert service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0] == "FAILED"
    assert service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0] == "FENCED"
    from mcbench.controller import reserved_resources
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
