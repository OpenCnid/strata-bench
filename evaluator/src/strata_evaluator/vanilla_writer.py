"""Bounded vanilla server lifetime inside the existing protected writer custody.

This is an operator conformance path. No telemetry broker, probe admission,
scorer or game agent authority is fabricated for an uninstrumented server.
"""

from pathlib import Path
from datetime import datetime, timezone
import re
import threading
import time
import uuid
from typing import Literal

from pydantic import Field

from mcbench.contracts import Strict, RpcRequest
from mcbench.broker_stdio import WorkerTransport
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.pack_launch import RestoredPackLaunchBinding, resolve_pack_launch
from mcbench.pack_worker import HeldPackWorker, _ProcessOutput
from mcbench.server_health import inspect_server_log
from mcbench.storage import canonical, digest, require
from mcbench.vanilla_persistence import VanillaPersistence
from mcbench.worker_stop import stop_owned_worker

from .craft_reference import PrivateFile, check_file, check_tree
from .writer_preparation import WriterPreparationPlanV4, java_identity
from .telemetry_auth import private_read

POLICY = "protected-sealed-restored-vanilla-server/1"
ARGUMENTS = ["-XX:ActiveProcessorCount=2", "-Xms1G", "-Xmx2G", "-jar", "server.jar", "nogui"]


class VanillaWriterLaunch(Strict):
    schema_: Literal["strata/PrivateVanillaWriterLaunch/1"] = Field(alias="schema")
    policy: Literal["protected-sealed-restored-vanilla-server/1"]
    binding: RestoredPackLaunchBinding
    helper_class: PrivateFile
    max_wall_s: int = Field(ge=30, le=600)


class VanillaWriterSession:
    def __init__(self, writer, value):
        writer.check()
        require(not writer.launched, "WRITER_CUSTODY_ALREADY_LAUNCHED")
        writer.launched = True  # Failed preflight is consumed too.
        self.writer = writer
        self.plan = plan = VanillaWriterLaunch.model_validate(value)
        require(
            isinstance(writer.plan, WriterPreparationPlanV4)
            and writer.plan.evidence_kind == "authentic_operator_reference",
            "VANILLA_WRITER_PROFILE",
        )
        require(
            Path(plan.helper_class.path).name == "StrataWriterLaunch.class", "WRITER_LAUNCH_HELPER"
        )
        check_file(Path(plan.helper_class.path), plan.helper_class)
        binding = plan.binding
        resolved = resolve_pack_launch(binding, "server")
        require(
            resolved["target"] == "vanilla"
            and resolved["launch"]["arguments"] == ARGUMENTS
            and safe(resolved["launch"]["working_directory"])
            == safe(Path(binding.instance) / "server")
            and safe(writer.plan.source_root) == safe(Path(binding.instance) / "server")
            and safe(writer.plan.java.path) == safe(resolved["launch"]["executable_path"])
            and writer.plan.java.sha256 == resolved["launch"]["executable"]["digest"],
            "VANILLA_WRITER_PROFILE",
        )
        source = safe(writer.plan.source_root)
        inventory = snapshot([], [source])
        expected = {safe(p["path"]).relative_to(source).as_posix(): p for p in inventory["files"]}
        actual = {
            name: pin.model_dump() | {"path": str(safe(pin.path))}
            for name, pin in writer.plan.sources.items()
        }
        require(
            actual == expected
            and set(writer.plan.directories)
            == {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_dir()},
            "VANILLA_WRITER_SOURCE",
        )
        check_tree(writer.tree.path, writer.plan.sources)
        require(
            {
                p.relative_to(writer.tree.path).as_posix()
                for p in writer.tree.path.rglob("*")
                if p.is_dir()
            }
            == set(writer.plan.directories),
            "VANILLA_WRITER_SOURCE",
        )
        properties = (writer.tree.path / "server.properties").read_text(encoding="utf-8")
        for key, expected_value in {
            "server-ip": "127.0.0.1",
            "online-mode": "true",
            "level-name": "world",
            "enable-rcon": "false",
            "rcon.password": "",
            "enable-command-block": "false",
        }.items():
            require(
                re.findall(r"(?m)^" + re.escape(key) + r"=(.*)$", properties) == [expected_value],
                "VANILLA_WRITER_SETTINGS",
            )
        require(
            re.findall(r"(?m)^eula=(true|false)\s*$", (writer.tree.path / "eula.txt").read_text())
            == ["true"],
            "AWAITING_OPERATOR_EULA",
        )
        inputs = snapshot(
            [plan.helper_class.path], [Path(binding.instance), Path(binding.restoration.snapshot)]
        )
        writer.leases.append(FileLease(inputs))
        require(resolve_pack_launch(binding, "server") == resolved, "VANILLA_WRITER_SOURCE")
        # The source remains the resolved materialization. Record the protected
        # working-directory translation explicitly as this separate profile.
        translated = resolved | {
            "launch": resolved["launch"] | {"working_directory": str(writer.tree.path)}
        }
        self.persistence = VanillaPersistence(writer.tree.path, pack=binding, resolved=translated)
        writer.leases.append(self.persistence.lease)
        self.ready = threading.Event()
        self.evidence = Path(writer.plan.evidence_directory) / "launch"
        self.result = {
            "policy": POLICY,
            "source_resolution": resolved,
            "protected_working_directory": str(writer.tree.path),
            "ready": False,
            "stop_requested": False,
            "authoritative_ticks": False,
            "probe_admission": False,
        }
        writer.result.update(capability="native-private-vanilla-custody/1", vanilla=self.result)
        arguments = [
            "-XX:-UsePerfData",
            "-Djava.io.tmpdir=" + str(writer.workspace.path / "tmp"),
            *ARGUMENTS,
        ]
        self.result["arguments"] = arguments
        writer.body["game_launch_attempted"] = True
        self.native = writer._dispatch(plan, inputs, arguments, self.ready, self.evidence)

    def verify_ready(self):
        writer = self.writer
        writer.check()
        require(self.native.observe() is None and self.ready.is_set(), "VANILLA_WRITER_NOT_READY")
        child = java_identity(
            strict_json(
                private_read(writer.workspace.path / "control/launch-child-identity.json", 8192)
            ),
            writer.result["challenge"],
            writer.tree.path,
            writer.plan.java.path,
            self.native.process.job,
        )
        require(child["pid"] != writer.result["gate_identity"]["pid"], "VANILLA_WRITER_JVM")
        token = writer.tree.security.bind_process(
            self.native.process.job.members[child["pid"]],
            writer.plan.writer_sid,
            writer.tree.group_sid,
            writer.tree.scope_sid,
        )
        self.result.update(
            ready=True, owned_jvm=child, jvm_token=token, ready_mono_ns=time.monotonic_ns()
        )
        writer.body["game_launched"] = True
        writer._record("RUNNING")
        return dict(self.result)

    def stop(self):
        self.writer.check()
        require(
            self.result["ready"] and not self.result["stop_requested"], "VANILLA_WRITER_STOP_SCOPE"
        )
        self.result.update(stop_requested=True, stop_mono_ns=time.monotonic_ns())
        self.native.process.send_input("stop\n")
        self.writer._record("STOPPING")

    def finish(self):
        writer = self.writer
        writer.check()
        require(
            self.result["ready"]
            and self.result["stop_requested"]
            and self.native.observe() is not None,
            "VANILLA_WRITER_UNFINISHED",
        )
        self.result["snapshot"] = self.persistence.capture(
            self.evidence / "stopped-instance",
            self.native.process,
            plan_digest=digest(self.plan.model_dump(by_alias=True)),
        )
        terminal = self.native.finish()
        writer.native = None
        writer.result["terminal"] = terminal
        require(
            terminal["terminal_verified"]
            and terminal["logs_complete"]
            and terminal["exit_code"] == 0
            and not terminal["forced"],
            "WRITER_CUSTODY_TERMINAL_UNCERTAIN",
        )
        self.result["log_health"] = {
            name: inspect_server_log(self.evidence / name)
            for name in ("server.stdout.log", "server.stderr.log")
        }
        require(
            all(v["result"] != "fail" for v in self.result["log_health"].values()),
            "SERVER_RUNTIME_FAILURE",
        )
        writer.check()
        writer._record("STOPPED")
        writer.completed = True
        return dict(writer.result)


def run_vanilla_worker(writer, value, invocation, output):
    """Bounded operator readiness/observation check, without model dispatch.

    Resolve and import the complete held worker before starting the finite
    server lifetime. The original source installation remains pristine; the
    worker connects to the protected copy at its exact sealed loopback port.
    """
    writer.check()
    plan = VanillaWriterLaunch.model_validate(value)
    output = safe(output)
    require(output.is_dir(), "VANILLA_WRITER_EVIDENCE")
    require(
        all(
            not output.is_relative_to(safe(path)) and not safe(path).is_relative_to(output)
            for path in (
                writer.workspace.path,
                writer.plan.source_root,
                plan.binding.instance,
                plan.binding.store,
                plan.binding.restoration.snapshot,
            )
        ),
        "VANILLA_WRITER_EVIDENCE",
    )
    result = {"policy": POLICY, "model_calls": 0, "probe_admission": False, "phases": {}}
    session = None
    started = time.monotonic()

    def record(name, body):
        with (output / name).open("xb") as file:
            file.write(canonical(body))

    def phase(name):
        result["phases"][name] = time.monotonic() - started

    def wait(predicate, seconds, code):
        until = min(writer.deadline, time.monotonic() + seconds)
        while not predicate():
            if session is not None:
                session.native.observe()
            require(time.monotonic() < until, code)
            time.sleep(0.05)

    with HeldPackWorker(plan.binding, invocation) as held:
        phase("worker_inputs_held")
        record("worker-resolution.json", held.resolved)
        process = held.start(preflight=True)
        logs = _ProcessOutput(process, output, "preflight")
        wait(lambda: process.poll() is not None, 20, "WORKER_PREFLIGHT_TIMEOUT")
        logs.finish()
        require(process.poll() == 0, "WORKER_PREFLIGHT_FAILED")
        phase("worker_import_verified")
        session = VanillaWriterSession(writer, value)
        phase("server_dispatched")
        wait(lambda: session.ready.is_set(), 80, "SERVER_READY_TIMEOUT")
        result["server_ready"] = session.verify_ready()
        phase("server_ready")
        record("server-ready.json", result)
        worker = held.start()
        logs = _ProcessOutput(worker, output, "worker")
        config = held.resolved["worker_configuration"]
        grant = Path(config["state_directory"]) / f"grant-{config['epoch']}.json"
        wait(lambda: grant.exists() or worker.poll() is not None, 30, "WORKER_GRANT_TIMEOUT")
        require(worker.poll() is None, "WORKER_EARLY_EXIT")
        descriptor = strict_json(private_read(grant, 8192))
        transport = WorkerTransport(descriptor)
        scope = {k: descriptor[k] for k in ("campaign_id", "agent_id", "epoch")}
        until = min(writer.deadline, time.monotonic() + 30)
        while True:
            request = RpcRequest.model_validate(
                {
                    "schema": "strata/GameRequest/1",
                    **scope,
                    "request_id": "observe-" + uuid.uuid4().hex,
                    "method": "observe",
                    "action": None,
                    "deadline_at": datetime.fromtimestamp(time.time() + 5, timezone.utc)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "target_request_id": None,
                    "after": None,
                }
            )
            observed = transport(request)
            if observed.get("status") == "ok" and observed["result"]["state"]["connected"]:
                break
            require(time.monotonic() < until and worker.poll() is None, "WORKER_CONNECT_TIMEOUT")
            session.native.observe()
            time.sleep(0.25)
        record("connected-observation.json", observed)
        phase("worker_connected")
        result["worker_stop"] = stop_owned_worker(worker, config, output, wait)
        logs.finish()
        result["worker_custody"] = held.receipt()
        phase("worker_stopped")
    session.stop()
    phase("server_stop_requested")
    wait(lambda: session.native.observe() is not None, 30, "SERVER_STOP_TIMEOUT")
    result["server_stop"] = session.finish()
    phase("server_stopped")
    record("vanilla-worker-result.json", result)
    return result
