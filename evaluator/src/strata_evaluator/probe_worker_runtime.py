"""Complete registered worker rosters inside the protected paired server reference.

An operator reference, with no model, mutation, native admission or scientific
probe claim. Workers drain before their server saves; failures fence the pair.
"""

from datetime import datetime, timezone
from pathlib import Path
import os
import time
import uuid

from mcbench.broker_stdio import WorkerTransport
from mcbench.contracts import Observation, RpcRequest
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, safe, snapshot, tree_files
from mcbench.native_export import OPERATOR
from mcbench.pack_worker import _ProcessOutput
from mcbench.storage import Fault, canonical, require
from mcbench.worker_stop import stop_owned_worker

from .probe_saved_bodies import MAX_COMPRESSED
from .probe_vanilla_runtime import BODY_POLICY, PairedVanillaRuntime
from .probe_worker_observation import verify_initial_worker
from .telemetry_auth import private_read

POLICY = "held-pair-protected-vanilla-worker-reference/1"
STATE_LIMIT = 64 * 1024**2
# Four existing 64MiB private logs, bounded worker state, config and receipts.
MEMBER_STORAGE = 328 * 1024**2


class PairedWorkerReference(PairedVanillaRuntime):
    def __init__(self, pair, launches, inputs):
        super().__init__(pair, launches)
        require(self.policy == BODY_POLICY, "PROBE_BODY_POLICY_REQUIRED")
        self.input_record = inputs.check()
        self.inputs = inputs
        self.policy = POLICY
        self.record.update(policy=POLICY, server_policy=BODY_POLICY, worker_inputs=self.input_record)
        self.result.update(policy=POLICY, saved_bodies=inputs.software.record["saved_bodies"], workers={})
        self.workers = inputs._workers
        self.phases = {(arm, agent): "HELD" for arm, group in self.workers.items() for agent in group}
        self.outputs, self.logs, self.exports = {}, [], []
        self.session = None
        self.consumed = False
        runtime_files = {}
        for group in self.workers.values():
            for worker in group.values():
                for item in worker.runtime.inventory["files"]:
                    runtime_files[item["path"]] = item["bytes"]
                runtime_files[str(worker.runtime.path)] = len(worker.runtime.raw)
        self.storage_bound += len(self.phases) * MEMBER_STORAGE + sum(runtime_files.values())

    def check_workers(self):
        self.inputs._check_custody()
        self._check_worker_phases()

    def _check_worker_phases(self):
        for (arm, agent), phase in self.phases.items():
            worker = self.workers[arm][agent]
            expected = set() if phase == "HELD" else {"preflight"} if phase == "IMPORTED" else {"preflight", "worker"}
            require(set(worker.processes) == expected, "PROBE_WORKER_PHASE")
            if phase in {"IMPORTED", "STOPPED"}:
                worker.receipt()
            elif phase == "RUNNING":
                require(worker.processes["worker"].poll() is None, "PROBE_WORKER_EARLY_EXIT")
            paths = tree_files(worker.invocation["state_directory"])
            require(sum(Path(p).stat().st_size for p in paths) <= STATE_LIMIT, "PROBE_WORKER_STORAGE_LIMIT")
        for lease in self.exports:
            lease.recheck()

    def check(self):
        require(self._scope().software is self.inputs.software, "PROBE_WORKER_SOFTWARE_SCOPE")
        super().check()
        # The base check includes the complete shared software/parent check.
        # Compose the remaining member custody and phases without repeating it.
        self.inputs._check_bindings_and_files()
        self._check_worker_phases()

    def _write(self, output, name, value):
        with (output / name).open("xb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())

    def _wait(self, predicate, seconds, code):
        until = min(self.held.preparation.deadline, *(w.deadline for w in self.held.writers.values()),
                    time.monotonic() + seconds)
        while not predicate():
            require(time.monotonic() < until, code)
            for log in self.logs:
                log.check()
            if self.session is not None:
                require(self.session.native.observe() is None, "PROBE_SERVER_EARLY_EXIT")
            time.sleep(.05)

    def _prepare(self, held):
        # Validate all destinations before creating any evidence output directory.
        paths = [safe(p) for writer in held.writers.values() for p in
                 (writer.plan.workspace_directory, writer.plan.evidence_directory)]
        paths += [safe(p) for group in self.workers.values() for worker in group.values()
                  for p in (worker.invocation["state_directory"], worker.invocation["configuration_path"])]
        for arm, group in self.workers.items():
            for agent, worker in group.items():
                config = safe(worker.invocation["configuration_path"])
                output = config.with_name(config.name + ".evidence")
                require(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
                                                    for p in paths), "PROBE_WORKER_NAMESPACE")
                paths.append(output)
                self.outputs[arm, agent] = output
        self.inputs.check()
        for (arm, agent), output in self.outputs.items():
            output.mkdir()
            worker = self.workers[arm][agent]
            self._write(output, "resolution.json", worker.resolved)
            process = worker.start(preflight=True)
            log = _ProcessOutput(process, output, "preflight")
            self.logs.append(log)
            self._wait(lambda: process.poll() is not None, 20, "WORKER_PREFLIGHT_TIMEOUT")
            log.finish()
            self._write(output, "preflight-receipt.json", worker.receipt())
            self.phases[arm, agent] = "IMPORTED"
        # Base run constructs the held initial states, then performs the full
        # composed check before any server dispatch. Each import's owned stop
        # has already been checked and persisted above; custody stays held.

    def _observe(self, worker, transport):
        config = worker.resolved["worker_configuration"]
        until = min(self.held.preparation.deadline, self.session.writer.deadline, time.monotonic() + 30)
        for _ in range(120):
            require(time.monotonic() + 5.5 < until, "PROBE_WORKER_CONNECT_TIMEOUT")
            require(worker.processes["worker"].poll() is None, "PROBE_WORKER_EARLY_EXIT")
            require(self.session.native.observe() is None, "PROBE_SERVER_EARLY_EXIT")
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1",
                **{k: config[k] for k in ("campaign_id", "agent_id", "epoch")},
                "request_id": "probe-observe-" + uuid.uuid4().hex, "method": "observe", "action": None,
                "deadline_at": datetime.fromtimestamp(time.time() + 5, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "target_request_id": None, "after": None})
            response = transport(request)
            if response["status"] == "ok":
                observation = Observation.model_validate(response["result"])
                require(not observation.is_example
                        and all(getattr(observation, k) == config[k] for k in ("campaign_id", "agent_id", "epoch")),
                        "PROBE_INITIAL_OBSERVATION")
                if observation.state is not None and observation.state.connected:
                    # Validate without rewriting the delivered journal identity.
                    return response["result"]
            else:
                require(response.get("error", {}).get("code") == "PRECONDITION_FAILED", "PROBE_WORKER_OBSERVE_REFUSED")
            time.sleep(.25)
        require(False, "PROBE_WORKER_CONNECT_TIMEOUT")

    def _arm(self, arm, session):
        self.session = session
        # Base run just performed the complete composed check after readiness,
        # immediately before calling this private continuation. Recheck after
        # observations so every body is still live at the arm barrier.
        group = self.workers[arm]
        observed, logs = {}, {}
        require(all(self.phases[arm, agent] == "IMPORTED" for agent in group), "PROBE_WORKER_PHASE")
        # Start the complete requested arm, then gather readiness from all bodies.
        for agent, worker in group.items():
            process = worker.start()
            self.phases[arm, agent] = "RUNNING"
            logs[agent] = _ProcessOutput(process, self.outputs[arm, agent], "worker")
            self.logs.append(logs[agent])
        for agent, worker in group.items():
            config = worker.resolved["worker_configuration"]
            grant = Path(config["state_directory"]) / f"grant-{config['epoch']}.json"
            process = worker.processes["worker"]
            self._wait(lambda: grant.exists() or process.poll() is not None, 30, "WORKER_GRANT_TIMEOUT")
            require(process.poll() is None, "PROBE_WORKER_EARLY_EXIT")
            descriptor = strict_json(private_read(grant, 8192))
            require(all(descriptor.get(k) == config[k] for k in ("campaign_id", "agent_id", "epoch")), "PROBE_WORKER_GRANT_SCOPE")
            observed[agent] = self._observe(worker, WorkerTransport(descriptor))
            self._write(self.outputs[arm, agent], "initial-observation.json", observed[agent])
        self.check_workers()  # Every body must still be live at the arm barrier.
        result = {"complete_roster_observed_connected": True, "members": {}, "live_initial_state_verified": False,
                  "native_probe_admission": False}
        self.result["workers"][arm] = result
        for agent, worker in group.items():
            output = self.outputs[arm, agent]
            stop = stop_owned_worker(worker.processes["worker"], worker.resolved["worker_configuration"], output, self._wait)
            self._write(output, "worker-stop.json", stop)
            logs[agent].finish()
            self._write(output, "worker-custody.json", worker.receipt())
            self.phases[arm, agent] = "STOPPED"
            body = self.inputs.software.record["saved_bodies"]["bodies"][agent]["state"]
            prep = self.held.preparation
            raw = prep.cas.read(OPERATOR, prep.views.namespace, body["player_file"], max_bytes=MAX_COMPRESSED)
            joined = verify_initial_worker(worker, observed[agent], raw)
            result["members"][agent] = joined | {"stop": stop}
            self._write(output, "worker-result.json", result["members"][agent])
            self.exports.append(FileLease(snapshot([], [Path(worker.invocation["state_directory"]), output])))
        self.session = None
        return result

    def run(self, held, continuation):
        require(not self.consumed and self.held is None, "PROBE_WORKER_REFERENCE_CONSUMED")
        self.consumed = True
        # Preflight wait uses the original parent's finite bounds before servers.
        self.held = held
        try:
            self._prepare(held)
            self.held = None  # Base coordinator consumes this same held pair once.
            result = super().run(held, self._arm)
            require(all(p == "STOPPED" for p in self.phases.values()), "PROBE_WORKER_STOP_UNPROVEN")
            return result
        finally:
            # Stop all worker processes before outer writer cleanup can save/exit.
            errors = []
            for group in self.workers.values():
                for worker in group.values():
                    for process in worker.processes.values():
                        try:
                            if process.poll() is None:
                                process.stop()
                        except Exception as error:
                            errors.append(error)
            for log in self.logs:
                try:
                    log.finish()
                except Exception as error:
                    errors.append(error)
            for lease in reversed(self.exports):
                try:
                    lease.close()
                except Exception as error:
                    errors.append(error)
            if errors:
                self.result["cleanup_failures"] = [getattr(e, "code", type(e).__name__) for e in errors]
                raise Fault("PROBE_WORKER_CLEANUP_UNCERTAIN") from errors[0]
