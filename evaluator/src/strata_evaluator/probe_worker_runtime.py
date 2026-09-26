"""Complete registered worker rosters inside the protected paired server reference.

An operator reference, with no model, mutation, native admission or scientific
probe claim. Workers drain before their server saves; failures fence the pair.
"""

from contextlib import contextmanager
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
from mcbench.storage import Fault, canonical, digest, require
from mcbench.worker_stop import stop_owned_worker

from .probe_saved_bodies import MAX_COMPRESSED
from .probe_vanilla_runtime import BODY_POLICY, CAPTURE_POLICY, PairedVanillaRuntime
from .player_body_match import MAX_COMPARISON_BYTES, compare_player_bodies
from .player_body_evidence import MAX_NBT, sha
from .probe_worker_observation import verify_initial_worker
from .telemetry_auth import private_read

POLICY = "held-pair-protected-vanilla-worker-reference/1"
CAPTURE_WORKER_POLICY = "held-pair-protected-vanilla-worker-reference/2"
STATE_LIMIT = 64 * 1024**2
# Four existing 64MiB private logs, bounded worker state, config and receipts.
MEMBER_STORAGE = 328 * 1024**2


class PairedWorkerReference(PairedVanillaRuntime):
    def __init__(self, pair, launches, inputs):
        super().__init__(pair, launches)
        require(self.policy in {BODY_POLICY, CAPTURE_POLICY}, "PROBE_BODY_POLICY_REQUIRED")
        server_policy = self.policy
        self.input_record = inputs.check()
        self.inputs = inputs
        if self.capture_bodies:
            bodies = inputs.software.record["saved_bodies"]["bodies"]
            roster = [bodies[a]["state"]["player_uuid"] for a in sorted(bodies)]
            require(len(roster) == pair["common"]["n"]
                    and all(p.body_observer.roster == roster for p in self.plans.values()),
                    "PROBE_BODY_CAPTURE_ROSTER")
        self.policy = CAPTURE_WORKER_POLICY if self.capture_bodies else POLICY
        self.record.update(policy=self.policy, server_policy=server_policy, worker_inputs=self.input_record)
        self.result.update(policy=self.policy, saved_bodies=inputs.software.record["saved_bodies"], workers={})
        self.workers = inputs._workers
        self.phases = {(arm, agent): "HELD" for arm, group in self.workers.items() for agent in group}
        self.outputs, self.logs, self.exports = {}, [], []
        self.session = None
        self.consumed = False
        self.prepared, self.run_started = False, False
        self.preflight_preparation = None
        runtime_files = {}
        for group in self.workers.values():
            for worker in group.values():
                for item in worker.runtime.inventory["files"]:
                    runtime_files[item["path"]] = item["bytes"]
                runtime_files[str(worker.runtime.path)] = len(worker.runtime.raw)
        self.storage_bound += len(self.phases) * MEMBER_STORAGE + sum(runtime_files.values())
        if self.capture_bodies:
            self.storage_bound += MAX_COMPARISON_BYTES

    def check_workers(self):
        require(self._scope().software is self.inputs.software, "PROBE_WORKER_SOFTWARE_SCOPE")
        self.inputs.software.check()
        self.inputs._check_bindings_and_configuration()
        self._check_worker_phases()

    def _check_worker_phases(self):
        for (arm, agent), phase in self.phases.items():
            require(phase in {"HELD", "IMPORTED", "RUNNING", "STOPPED"}, "PROBE_WORKER_PHASE")
            worker = self.workers[arm][agent]
            expected = set() if phase == "HELD" else {"preflight"} if phase == "IMPORTED" else {"preflight", "worker"}
            require(set(worker.processes) == expected, "PROBE_WORKER_PHASE")
            if phase in {"IMPORTED", "STOPPED"}:
                # Receipt validates this runtime plus the retained process job.
                worker.receipt()
            else:
                worker.runtime.recheck()
                if phase == "RUNNING":
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
        self.inputs._check_bindings_and_configuration()
        self._check_worker_phases()

    def _write(self, output, name, value):
        with (output / name).open("xb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())

    def _wait(self, predicate, seconds, code, *, preparation=None):
        until = (min(preparation.deadline, time.monotonic() + seconds) if preparation is not None
                 else min(self.held.preparation.deadline, *(w.deadline for w in self.held.writers.values()),
                          time.monotonic() + seconds))
        require(time.monotonic() < until, code)
        while not predicate():
            require(time.monotonic() < until, code)
            for log in self.logs:
                log.check()
            if self.session is not None:
                require(self.session.native.observe() is None, "PROBE_SERVER_EARLY_EXIT")
            time.sleep(.05)
        require(time.monotonic() < until, code)

    def _prepare(self, preparation, plans):
        # Validate all destinations before creating any evidence output directory.
        paths = [safe(p) for plan in plans.values() for p in
                 (plan.workspace_directory, plan.evidence_directory)]
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
            process = worker.start(preflight=True, _deadline=preparation.deadline)
            log = _ProcessOutput(process, output, "preflight")
            self.logs.append(log)
            self._wait(lambda: process.poll() is not None, 20, "WORKER_PREFLIGHT_TIMEOUT", preparation=preparation)
            log.finish()
            self._write(output, "preflight-receipt.json", worker.receipt())
            self.phases[arm, agent] = "IMPORTED"
        self.inputs.software.check()
        self.inputs._check_bindings_and_configuration()
        self._check_worker_phases()

    @contextmanager
    def before_writers(self, preparation, plans):
        require(not self.consumed and self.held is None, "PROBE_WORKER_REFERENCE_CONSUMED")
        require(preparation is self.inputs.software.preparation, "PROBE_WORKER_SOFTWARE_SCOPE")
        self.consumed = True
        self.preflight_preparation = preparation
        self.preflight_plan_digest = digest({arm: p.model_dump(by_alias=True) for arm, p in plans.items()})
        try:
            self._prepare(preparation, plans)
            self.prepared = True
            self.result["import_preparation"] = {"stage": "before_writers", "complete": True,
                                                  "writer_plans_digest": self.preflight_plan_digest}
            yield
        finally:
            # run() must clean workers before unwinding any server writer. If
            # copy/import preparation fails earlier, this context owns cleanup.
            if not self.run_started:
                self._cleanup_workers()

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
        if self.capture_bodies:
            self._wait(lambda: session.observer.capture_ready(session.native.process), 10, "BODY_CAPTURE_TIMEOUT")
            self.check_workers()
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

    def verify_stopped(self):
        super().verify_stopped()
        if not self.capture_bodies:
            return
        reports = {}
        for arm, session in self.sessions.items():
            observer = session.observer
            report = session.writer.result["vanilla"].get("body_observer")
            require(observer is not None and observer.captured and report is not None
                    and report["owned_producer_verified"] is True and report["content_verified"] is True
                    and report["launch_binding"] == observer.binding, "PROBE_BODY_CAPTURE_UNPROVEN")
            reports[arm] = report
        roster = self.plans["initial"].body_observer.roster

        def read(arm, identity):
            raw = private_read(self.sessions[arm].observer.output / (identity + ".nbt"), MAX_NBT)
            require(sha(raw) == reports[arm]["bodies"][identity]["nbt_sha256"], "BODY_OUTPUT_CHANGED")
            return raw

        comparison = compare_player_bodies(lambda identity: read("initial", identity),
            lambda identity: read("experienced", identity), roster)
        comparison.update(owned_producers_verified=True, pair_plan_digest=self.pair_digest,
                          capture_reports_sha256={arm: digest(v) for arm, v in reports.items()})
        self.result["body_comparison"] = comparison
        require(len(canonical(comparison)) <= MAX_COMPARISON_BYTES, "BODY_COMPARISON_QUOTA")
        self._write(self.sessions["initial"].evidence, "body-comparison.json", comparison)
        self.check()  # Retain both exports and all source/authority custody.
        require(comparison["save_format_state_equal"], "PROBE_BODY_SAVE_STATE_MISMATCH")

    def run(self, held, continuation):
        require(self.consumed and self.prepared and not self.run_started and self.held is None,
                "PROBE_WORKER_REFERENCE_CONSUMED")
        require(held.preparation is self.preflight_preparation and held.software is self.inputs.software
                and digest({arm: w.plan.model_dump(by_alias=True) for arm, w in held.writers.items()})
                == self.preflight_plan_digest, "PROBE_WORKER_SOFTWARE_SCOPE")
        self.run_started = True
        try:
            result = super().run(held, self._arm)
            require(all(p == "STOPPED" for p in self.phases.values()), "PROBE_WORKER_STOP_UNPROVEN")
            return result
        finally:
            self._cleanup_workers()

    def _cleanup_workers(self):
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
