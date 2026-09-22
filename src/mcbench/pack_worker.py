"""Private vanilla PackLock launch with typed per-invocation configuration.

This connects the sealed runtime/settings to the real worker command. File
leases protect selected bytes; neither this launcher nor a fresh directory is
a general process/network sandbox or a complete checkpoint protocol.
"""

from contextlib import ExitStack
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import threading
import time
from typing import Annotated

from pydantic import Field

from .contracts import Id, Positive, Strict
from .inventory import file_hash
from .launch_integrity import FileLease, safe, snapshot
from .processes import ManagedProcess
from .provisioning import VanillaLaunchProfile, WORKER_CONFIG_ARGUMENT, validate_launch_environment
from .storage import Fault, canonical, digest, require
from .worker_bundle import HeldWorkerBundle, launch_path

ROOT = Path(__file__).resolve().parents[2]


class WorkerInvocation(Strict):
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    lease_id: Id
    state_directory: Annotated[str, Field(min_length=1)]
    configuration_path: Annotated[str, Field(min_length=1)]


def _path(value):
    require(isinstance(value, str) and "\x00" not in value and Path(value).is_absolute()
            and ".." not in Path(value).parts,
            "WORKER_LAUNCH_PATH")
    require(all(":" not in part and not part.endswith((" ", ".")) for part in Path(value).parts[1:]),
            "WORKER_LAUNCH_PATH")
    return safe(Path(value))


def _apart(first, second):
    require(not first.is_relative_to(second) and not second.is_relative_to(first), "WORKER_LAUNCH_OVERLAP")


def validate_server_settings(raw, settings):
    """Accept the inspected one-assignment-per-line properties profile.

    Keys remain literal; values support escaped separators, spaces, comment
    markers and backslashes. Unknown escapes, Unicode escapes and continuations
    reject instead of pretending to implement the entire Java properties grammar.
    """
    require(len(raw) <= 65536, "WORKER_SERVER_SETTINGS_MISMATCH")
    properties = {}
    require(raw.isascii(), "WORKER_SERVER_SETTINGS_MISMATCH")
    for line in raw.decode("ascii").splitlines():
        if not line or line.startswith(("#", "!")):
            continue
        require("=" in line and "\x00" not in line,
                "WORKER_SERVER_SETTINGS_MISMATCH")
        key, value = line.split("=", 1)
        require(re.fullmatch("[a-z0-9.-]+", key) and value == value.strip() and key not in properties,
                "WORKER_SERVER_SETTINGS_MISMATCH")
        require(re.fullmatch(r"(?:[^\\\x00-\x1f]|\\[\\:= #!])*", value) is not None,
                "WORKER_SERVER_SETTINGS_MISMATCH")
        properties[key] = re.sub(r"\\([\\:= #!])", r"\1", value)
    require(all(properties.get(key) == value for key, value in {
        "server-ip": settings.host, "server-port": str(settings.port), "online-mode": "true",
        "enable-rcon": "false", "rcon.password": "", "enable-command-block": "false"}.items()),
        "WORKER_SERVER_SETTINGS_MISMATCH")
    return properties


def check_worker_command(profile, runtime):
    _apart(runtime.root, safe(ROOT))
    _apart(runtime.path, safe(ROOT))
    command = profile.client
    require(command.arguments == [runtime.body["worker"], WORKER_CONFIG_ARGUMENT]
            and command.executable_path == runtime.body["node"]
            and command.executable.digest == file_hash(Path(runtime.body["node"]))
            and command.working_directory == ".", "WORKER_LAUNCH_COMMAND_MISMATCH")
    require("\x00" not in profile.worker_settings.username, "WORKER_LAUNCH_SETTINGS")
    validate_launch_environment(command.environment)
    cache = _path(profile.worker_settings.auth_cache)
    require(cache.is_dir(), "AWAITING_ARTIFACT")
    _apart(cache, runtime.root)
    _apart(cache, safe(ROOT))


def validate_worker_profile(profile):
    require(isinstance(profile, VanillaLaunchProfile), "WORKER_LAUNCH_PROFILE")
    profile = VanillaLaunchProfile.model_validate(profile.model_dump())
    with HeldWorkerBundle(profile.worker_runtime.model_dump()) as runtime:
        check_worker_command(profile, runtime)
        runtime.recheck()


def resolve_worker_invocation(profile, value, binding):
    """Resolve the single declared argument slot, with no caller setting overrides."""
    require(value is not None, "WORKER_INVOCATION_REQUIRED")
    invocation = WorkerInvocation.model_validate(value)
    state, config = _path(invocation.state_directory), _path(invocation.configuration_path)
    require(state.is_dir() and not any(state.iterdir()) and config.parent.is_dir()
            and not config.exists(), "WORKER_INVOCATION_NOT_FRESH")
    cache = _path(profile.worker_settings.auth_cache)
    manifest = _path(profile.worker_runtime.path)
    for first in (state, config):
        for second in (_path(binding.store), _path(binding.instance), cache, safe(ROOT), manifest):
            _apart(first, second)
    _apart(state, config)
    with HeldWorkerBundle(profile.worker_runtime.model_dump()) as runtime:
        check_worker_command(profile, runtime)
        for first in (state, config):
            _apart(first, runtime.root)
        validate_server_settings((_path(binding.instance) / "server/server.properties").read_bytes(),
                                 profile.worker_settings)
        configuration = {"schema": "strata/DevelopmentWorker/1", "purpose": "manual-conformance",
            "server_kind": "vanilla", **profile.worker_settings.model_dump(),
            **invocation.model_dump(exclude={"configuration_path"})}
        configuration["state_directory"] = launch_path(state)
        configuration["auth_cache"] = launch_path(cache)
        raw = canonical(configuration)
        require(len(raw) <= 8192, "WORKER_LAUNCH_CONFIG_QUOTA")
        command = profile.client.model_dump() | {
            "arguments": [runtime.body["worker"], launch_path(config)],
            "working_directory": launch_path(_path(binding.instance) / "client")}
        return {"schema": "strata/ResolvedPackLaunch/2", "launch": command,
            "worker_runtime": profile.worker_runtime.model_dump(), "worker_configuration": configuration,
            "worker_configuration_path": launch_path(config),
            "worker_configuration_sha256": hashlib.sha256(raw).hexdigest(), "update_policy": profile.update_policy}


class HeldPackWorker:
    """Own the actual worker and its fixed import preflight under retained leases.

    The caller drains output, enforces its outer deadline and requests normal
    worker stop. Exceptional context exit closes owned processes before leases.
    Nothing dispatches inference or accepts account terms here.
    """

    def __init__(self, binding, invocation, *, simulation=False):
        self.binding, self.invocation, self.simulation = deepcopy(binding), deepcopy(invocation), simulation
        self._resources = None
        self._resolved = None
        self.processes = {}

    @property
    def resolved(self):
        require(self._resolved is not None, "WORKER_LAUNCH_NOT_HELD")
        return deepcopy(self._resolved)

    def __enter__(self):
        from .pack_launch import resolve_pack_launch
        require(self._resources is None, "WORKER_LAUNCH_ALREADY_HELD")
        resolved = resolve_pack_launch(self.binding, "client", simulation=self.simulation,
                                       worker_invocation=self.invocation)
        resources = ExitStack()
        try:
            self.runtime = resources.enter_context(HeldWorkerBundle(resolved["worker_runtime"]))
            config = _path(resolved["worker_configuration_path"])
            raw = canonical(resolved["worker_configuration"])
            require(hashlib.sha256(raw).hexdigest() == resolved["worker_configuration_sha256"],
                    "WORKER_LAUNCH_CONFIG_CHANGED")
            with config.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            self.config_lease = resources.enter_context(FileLease(snapshot([config], [])))
            require(file_hash(config) == resolved["worker_configuration_sha256"], "WORKER_LAUNCH_CONFIG_CHANGED")
            self._resolved, self._resources = resolved, resources
        except BaseException:
            resources.close()
            raise
        return self

    def start(self, *, preflight=False):
        require(self._resources is not None and type(preflight) is bool, "WORKER_LAUNCH_NOT_HELD")
        mode = "preflight" if preflight else "worker"
        require(mode not in self.processes, "WORKER_LAUNCH_ALREADY_STARTED")
        if not preflight and "preflight" in self.processes:
            previous = self.processes["preflight"]
            require(previous.poll() == 0 and previous.job.accounting()["active_processes"] == 0,
                    "WORKER_PREFLIGHT_INCOMPLETE")
        require(not preflight or "worker" not in self.processes, "WORKER_LAUNCH_ALREADY_STARTED")
        require(not any(_path(self._resolved["worker_configuration"]["state_directory"]).iterdir()),
                "WORKER_INVOCATION_NOT_FRESH")
        self.runtime.recheck()
        self.config_lease.recheck()
        command = self._resolved["launch"]
        argv = ([command["executable_path"], command["arguments"][0], "--check-vanilla-runtime"]
                if preflight else [command["executable_path"], *command["arguments"]])
        process = ManagedProcess(argv, Path(command["working_directory"]), command["environment"], "")
        self.processes[mode] = process
        self._resources.callback(process.close)
        return process

    def receipt(self):
        require(self._resources is not None and self.processes, "WORKER_LAUNCH_NOT_HELD")
        owned = {}
        for name, process in self.processes.items():
            require(process.poll() == 0 and process.job is not None, "WORKER_LAUNCH_STOP_UNPROVEN")
            job = process.job.accounting()
            require(job["active_processes"] == job["terminated_processes"] == 0, "WORKER_LAUNCH_STOP_UNPROVEN")
            owned[name] = {"returncode": 0, "job": job}
        self.config_lease.recheck()
        return {"schema": "strata/HeldPackWorker/1", "lock": self._resolved["lock"],
            "launch_profile": self._resolved["launch_profile"],
            "configuration_sha256": self._resolved["worker_configuration_sha256"],
            "runtime": self.runtime.receipt(), "owned_processes": owned,
            "held_through_owned_stop": True, "campaign_admission": False, "isolation_qualified": False}

    def __exit__(self, *_):
        if self._resources:
            try:
                self._resources.close()
            finally:
                self._resources = None


def run_pack_worker(binding, invocation, evidence, *, import_only=False):
    """Bounded operator command, using the same held launcher as native integration.

    Import-only checks load the pinned worker without authentication or a game
    connection. Full mode starts the worker against the already owned server;
    its grant stays in the declared private state directory for the scoped CLI.
    """
    started, started_unix = time.monotonic(), time.time()
    evidence = _path(str(evidence))
    require(type(import_only) is bool and not evidence.exists(), "WORKER_EVIDENCE_TARGET")
    invocation = WorkerInvocation.model_validate(invocation).model_dump()
    for path in (binding.store, binding.instance, invocation["state_directory"],
                 invocation["configuration_path"], str(ROOT)):
        _apart(evidence, _path(path))
    result = {"schema": "strata/PackWorkerRun/1", "mode": "import-only" if import_only else "worker",
              "status": "fail", "campaign_admission": False, "isolation_qualified": False,
              "started_unix": started_unix, "process_elapsed_s": {}}
    with HeldPackWorker(binding, invocation) as worker:
        _apart(evidence, worker.runtime.root)
        _apart(evidence, worker.runtime.path)
        _apart(evidence, _path(worker.resolved["worker_configuration"]["auth_cache"]))
        evidence.mkdir(parents=True)
        (evidence / "launch.json").write_bytes(canonical(worker.resolved))
        result["launch_digest"] = digest(worker.resolved)
        result["preparation_elapsed_s"] = time.monotonic() - started
        try:
            for preflight in ([True] if import_only else [True, False]):
                process_started = time.monotonic()
                process = worker.start(preflight=preflight)
                mode = "preflight" if preflight else "worker"
                failures, threads = [], []

                def drain(stream, path):
                    try:
                        with path.open("xb") as destination:
                            total = 0
                            while data := stream.read1(65536):
                                total += len(data)
                                require(total <= 64 * 1024**2, "WORKER_LOG_QUOTA")
                                destination.write(data)
                            destination.flush()
                            os.fsync(destination.fileno())
                    except Exception:
                        failures.append(True)

                for stream, name in ((process.process.stdout, "stdout"), (process.process.stderr, "stderr")):
                    thread = threading.Thread(target=drain, args=(stream, evidence / f"{mode}.{name}.log"), daemon=True)
                    thread.start()
                    threads.append(thread)
                bound = 20 if preflight else worker.resolved["worker_configuration"]["max_wall_ms"] / 1000 + 5
                deadline = time.monotonic() + bound
                try:
                    while process.poll() is None:
                        require(time.monotonic() < deadline, "WORKER_PROCESS_TIMEOUT")
                        require(not failures, "WORKER_LOG_UNAVAILABLE")
                        time.sleep(.05)
                    require(process.poll() == 0, "WORKER_PROCESS_FAILED")
                finally:
                    if process.poll() is None:
                        process.stop()
                    for thread in threads:
                        thread.join(2)
                    result["process_elapsed_s"][mode] = time.monotonic() - process_started
                require(not failures and not any(thread.is_alive() for thread in threads), "WORKER_LOG_UNAVAILABLE")
            result["receipt"] = worker.receipt()
            result["status"] = "stopped_unqualified"
        except Exception as error:
            result["error"] = error.code if isinstance(error, Fault) else type(error).__name__
            raise
        finally:
            result["elapsed_s"] = time.monotonic() - started
            (evidence / "result.json").write_bytes(canonical(result))
    return result
