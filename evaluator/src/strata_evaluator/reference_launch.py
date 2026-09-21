"""Owned one-use Windows server reference, not campaign/scoring qualification."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Literal

from pydantic import Field, TypeAdapter

from mcbench.contracts import Digest, Id, Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.processes import ManagedProcess
from mcbench.records import GameEvent
from mcbench.server_health import inspect_server_log
from mcbench.storage import Database, Fault, canonical, digest, require

from .craft_reference import CraftReferenceStore, PrivateFile, check_file, private_path, write_new
from .reference_participant import ParticipantPlan, ParticipantWindow, validate_paths
from .telemetry import ServerStartedV5, ServerStartedV6
from .telemetry_auth import MAX_WIRE_RECORD, SpoolVerifier, inspect_authenticated_spool, private_read

# Only this inspected official E9E 1.27.0 bootstrap profile is admitted. Its
# YAML disables autoRestart/ramDisk, uses the working directory and PATH Java,
# and fixes the existing 2G/5G, nogui launch. Do not infer those semantics from
# arbitrary YAML with regular expressions or accept a caller's replacement pin.
# A changed bootstrap needs a separately reviewed versioned profile.
E9E_BOOTSTRAP_PINS = {
    "serverstarter-2.4.0.jar": "70bec2771fd000209a8778b8457f231bf8e6244bb3d8dba6bb739c3662e099b4",
    "server-setup-config.yaml": "4759535f6bb6559dc3486a7a51ff1fbe270880f054877caba395e19c8af4d92a",
}


class ReferenceLaunchBase(Strict):
    instance_id: Id
    setup_digest: Digest
    mode: Literal["e9e-serverstarter", "synthetic-fixture"]
    executable: PrivateFile
    module_file: PrivateFile
    immutable_files: list[PrivateFile] = Field(min_length=1, max_length=11900)
    # The exact inventory is re-enumerated while its file/directory leases hold.
    immutable_trees: list[str] = Field(max_length=16)
    fixture_arguments: list[str] = Field(default_factory=list, max_length=32)
    evidence_directory: str
    server_port: int = Field(ge=1024, le=65535)
    max_wall_s: int = Field(ge=1, le=600)
    graceful_stop_s: int = Field(ge=1, le=120)


class ReferenceLaunchPlan(ReferenceLaunchBase):
    schema_: Literal["strata/PrivateReferenceLaunch/1"] = Field(alias="schema")
    ready_run_s: int = Field(ge=1, le=60)


class ReferenceLaunchPlanV2(ReferenceLaunchBase):
    schema_: Literal["strata/PrivateReferenceLaunch/2"] = Field(alias="schema")
    participant: ParticipantPlan


def parse_launch_plan(value):
    return TypeAdapter(ReferenceLaunchPlan | ReferenceLaunchPlanV2).validate_python(value)


def same_path(a, b):
    return Path(a).resolve() == Path(b).resolve()


def inventory_for(plan, extra):
    files = {str(safe(pin.path)): {"path": str(safe(pin.path)), "bytes": pin.bytes, "sha256": pin.sha256}
             for pin in plan.immutable_files}
    require(len(files) == len(plan.immutable_files), "REFERENCE_PIN_DUPLICATE")
    for pin in (plan.executable, plan.module_file):
        require(files.get(str(safe(pin.path))) == {"path": str(safe(pin.path)), "bytes": pin.bytes,
                                                "sha256": pin.sha256}, "REFERENCE_FILE_UNPINNED")
    trees = []
    for root in plan.immutable_trees:
        root = safe(root)
        expected = sorted(name for name in files if Path(name).is_relative_to(root))
        require(expected, "REFERENCE_TREE_UNPINNED")
        trees.append({"path": str(root), "files": expected})
    for entry in snapshot(extra, [])["files"]:
        previous = files.get(entry["path"])
        require(previous is None or previous == entry, "REFERENCE_PIN_CONFLICT")
        files[entry["path"]] = entry
    return {"schema": "strata/LaunchFileInventory/1", "files": list(files.values()), "trees": trees}


def bind_identity(plan, setup, observed, process_identity):
    """Native MAC fields must agree with the retained OS handle and sealed paths."""
    require(observed.pid == process_identity["pid"] and observed.process_started_unix_ms ==
            process_identity["process_started_unix_ms"], "REFERENCE_PROCESS_MISMATCH")
    require(same_path(observed.executable, process_identity["executable"])
            and same_path(observed.executable, plan.executable.path), "REFERENCE_EXECUTABLE_MISMATCH")
    require(same_path(observed.game_directory, setup.game_directory)
            and same_path(observed.world_directory, setup.fixture_directory), "REFERENCE_WORLD_MISMATCH")
    require(same_path(observed.module_file, plan.module_file.path)
            and observed.module_sha256 == plan.module_file.sha256, "REFERENCE_MODULE_MISMATCH")
    require(observed.online_mode and observed.server_port == plan.server_port, "REFERENCE_SERVER_MISMATCH")
    return {"native_observation": observed.model_dump(), "held_process": process_identity,
            "launch_binding_verified": True, "process_isolation_qualified": False}


def first_start(spool_directory, authority):
    files = list(spool_directory.glob("*.authenticated.jsonl"))
    require(len(files) <= 1, "REFERENCE_SPOOL_MULTIPLE")
    if not files:
        return None
    with files[0].open("rb") as stream:
        line = stream.readline(MAX_WIRE_RECORD + 1)
    require(len(line) <= MAX_WIRE_RECORD, "REFERENCE_START_QUOTA")
    if not line or not line.endswith(b"\n"):
        return None  # In-progress write is not terminal; the same source is polled.
    with SpoolVerifier(authority) as verifier:
        event = GameEvent.model_validate(strict_json(verifier.verify(line)))
        require(not event.is_example and event.visibility == "evaluator"
                and event.kind == "server_started" and event.payload_schema in {"strata/ServerStarted/5", "strata/ServerStarted/6"}
                and event.seq == event.server_event_seq == 1 and event.server_tick == 0
                and event.server_boot_id == verifier.boot
                and (event.campaign_id, event.epoch) == (authority.campaign_id, authority.epoch),
                "REFERENCE_START_INVALID")
        model = ServerStartedV6 if event.payload_schema == "strata/ServerStarted/6" else ServerStartedV5
        return files[0], event, model.model_validate(event.payload)


class ReferenceLauncher:
    def __init__(self, store):
        self.store = store
        self.database = store.database
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS reference_dispatches (instance TEXT PRIMARY KEY, "
                       "plan TEXT NOT NULL, state TEXT NOT NULL, body TEXT NOT NULL)")

    def _record(self, instance, state, body):
        with self.database.transaction() as db:
            db.execute("UPDATE reference_dispatches SET state=?,body=? WHERE instance=?",
                       (state, canonical(body).decode(), instance))
            self.database.event(db, "private.reference_dispatch", {"instance": instance, "state": state, **body})

    def run(self, value, *, client_binding=None):
        require(os.name == "nt", "REFERENCE_PLATFORM_UNQUALIFIED")
        plan = parse_launch_plan(value)
        row, setup, authority, authority_path = self.store._load(plan.instance_id)
        require(row["digest"] == plan.setup_digest, "REFERENCE_SETUP_CHANGED")
        require(plan.mode != "synthetic-fixture" or setup.evidence_kind == "synthetic", "REFERENCE_MODE")
        require(plan.mode != "e9e-serverstarter" or not plan.fixture_arguments, "REFERENCE_ARGUMENTS")
        evidence = private_path(plan.evidence_directory)
        game = private_path(setup.game_directory)
        require(not evidence.exists() and not evidence.is_relative_to(game)
                and not game.is_relative_to(evidence) and not evidence.is_relative_to(authority_path.parent),
                "REFERENCE_EVIDENCE_PATH")
        coordinated = isinstance(plan, ReferenceLaunchPlanV2)
        binding = None
        if coordinated:
            require(plan.participant.window_s <= plan.max_wall_s, "REFERENCE_DEADLINE")
            validate_paths(plan.participant, evidence, game, authority_path.parent)
            if plan.mode == "e9e-serverstarter":
                require(client_binding is not None, "REFERENCE_CLIENT_BINDING_REQUIRED")
                from .reference_client import ClientReferenceBinding, validate_client_binding
                binding = ClientReferenceBinding.model_validate(client_binding)
                # The -m entrypoint owns __main__ model classes; pass wire data
                # across the imported client validator boundary, not class identity.
                validate_client_binding(binding, setup, plan.model_dump(by_alias=True))
            else:
                require(client_binding is None, "REFERENCE_CLIENT_PROFILE")
        else:
            require(plan.ready_run_s <= plan.max_wall_s, "REFERENCE_DEADLINE")
            require(client_binding is None, "REFERENCE_CLIENT_PROFILE")
        pinned = {str(Path(pin.path).resolve()).casefold() for pin in plan.immutable_files}
        bootstrap = Path(__file__).resolve().parents[3] / "src/mcbench/process_bootstrap.py"
        require(all(str(path.resolve()).casefold() in pinned for path in
                    (Path(sys.executable), bootstrap)), "REFERENCE_BOOTSTRAP_UNPINNED")
        if plan.mode == "e9e-serverstarter":
            require(Path(plan.executable.path).name.lower() == "java.exe", "REFERENCE_EXECUTABLE")
            require(all(str((game / name).resolve()).casefold() in pinned for name in
                        ("serverstarter-2.4.0.jar", "server-setup-config.yaml")), "REFERENCE_BOOTSTRAP_UNPINNED")
            by_path = {str(Path(pin.path).resolve()).casefold(): pin for pin in plan.immutable_files}
            require(all(by_path[str((game / name).resolve()).casefold()].sha256 == expected
                        for name, expected in E9E_BOOTSTRAP_PINS.items()), "REFERENCE_BOOTSTRAP_UNREVIEWED")
            roots = {str(Path(path).resolve()).casefold() for path in plan.immutable_trees}
            require(all(str(path.resolve()).casefold() in roots for path in (
                Path(plan.executable.path).parent.parent, game / "mods", game / "libraries",
                game / "kubejs/server_scripts", game / "kubejs/startup_scripts")), "REFERENCE_SOFTWARE_UNPINNED")
            # File syntax and effective startup observations are both checked.
            properties = (game / "server.properties").read_text(encoding="utf-8")
            require(re.findall(r"(?m)^server-ip=(.*)\s*$", properties) == ["127.0.0.1"]
                    and re.findall(r"(?m)^online-mode=(true|false)\s*$", properties) == ["true"]
                    and re.findall(r"(?m)^server-port=(\d+)\s*$", properties) == [str(plan.server_port)],
                    "REFERENCE_SERVER_PROPERTIES")
            require(re.findall(r"(?m)^eula=(true|false)\s*$", (game / "eula.txt").read_text()) == ["true"],
                    "AWAITING_OPERATOR_EULA")
        for pin in plan.immutable_files:
            check_file(Path(pin.path), pin)
        # Preflight is the durable one-use reservation, not a status query. A
        # later failure retains it, including a crash before dispatch is recorded.
        self.store.preflight(plan.instance_id)
        with self.database.transaction() as db:
            require(db.execute("SELECT 1 FROM reference_dispatches WHERE instance=?",
                               (plan.instance_id,)).fetchone() is None, "REFERENCE_ALREADY_DISPATCHED")
            body = {"schema": "strata/PrivateReferenceDispatch/1", "plan_digest": digest(plan.model_dump(by_alias=True)),
                    "evidence_kind": setup.evidence_kind, "status": "intent", "launch_binding_verified": False,
                    "scoring_eligible": False, "started_unix": time.time()}
            if binding is not None:
                body["client_binding_digest"] = digest(binding.model_dump(by_alias=True))
            db.execute("INSERT INTO reference_dispatches VALUES (?,?,?,?)",
                       (plan.instance_id, canonical(plan.model_dump(by_alias=True)).decode(), "INTENT", canonical(body).decode()))
            self.database.event(db, "private.reference_dispatch", {"instance": plan.instance_id, **body})
        proc, lease, participant = None, None, None
        readers, reader_errors = [], []
        ready = threading.Event()
        overflow = threading.Event()
        started, stopped_at, bound_at = time.monotonic(), None, None
        body.update(stop_sent=False, forced_stop=False)
        if coordinated:
            body["participant"] = {"status": "not_ready", "participant_execution_verified": False}
        try:
            evidence.mkdir()
            spool = evidence / "telemetry"
            spool.mkdir()
            config_path = evidence / "telemetry-config.json"
            config = {"schema": "strata/ForgeTelemetryConfig/3", "campaign_id": setup.campaign_id,
                "epoch": setup.epoch, "spool_directory": str(spool), "max_bytes": 8388608, "max_events": 2000,
                "recipe_ids": list(setup.recipe_digests), "config_queries": [], "authentication": authority.producer_config()}
            write_new(config_path, config)
            write_new(evidence / "launch-plan.json", plan.model_dump(by_alias=True))
            binding_files = []
            if binding is not None:
                write_new(evidence / "client-binding.json", binding.model_dump(by_alias=True))
                binding_files = [evidence / "client-binding.json", Path(binding.fixture_declaration.path)]
            lease = FileLease(inventory_for(plan, [config_path, authority_path,
                authority_path.with_name("setup.json"), Path(authority.key_file), evidence / "launch-plan.json",
                *binding_files]))
            if binding is not None:
                # Revalidate the declared hashes while the exact module/declaration
                # handles deny writes; a preflight-to-lease change is not accepted.
                validate_client_binding(binding, setup, plan.model_dump(by_alias=True))
            environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP") if key in os.environ}
            environment.update(JAVA_HOME=str(Path(plan.executable.path).parent.parent),
                PATH=str(Path(plan.executable.path).parent) + os.pathsep + str(Path(os.environ["SystemRoot"]) / "System32"),
                STRATA_TELEMETRY_CONFIG=str(config_path))
            arguments = ["-jar", "serverstarter-2.4.0.jar"] if plan.mode == "e9e-serverstarter" else [
                arg.replace("{config}", str(config_path)).replace("{game}", str(game))
                .replace("{module}", plan.module_file.path) for arg in plan.fixture_arguments]
            lease.recheck()
            self._record(plan.instance_id, "DISPATCHING", body | {"status": "dispatching"})
            proc = ManagedProcess([plan.executable.path, *arguments], game, environment, "", interactive=True,
                                  bootstrap_python=sys.executable, bootstrap_script=bootstrap)
            body.update(status="running", supervisor_pid=proc.process.pid)
            self._record(plan.instance_id, "RUNNING", body)

            def copy(source, name):
                try:
                    with (evidence / name).open("xb") as output:
                        total = 0
                        while line := source.readline(65536):
                            total += len(line)
                            if total > 64 * 1024**2:
                                overflow.set()
                                break
                            output.write(line)
                            output.flush()
                            if re.search(rb'Done \([0-9.,]+s\)! For help, type "help"', line):
                                ready.set()
                        os.fsync(output.fileno())
                except (OSError, ValueError) as error:
                    reader_errors.append(type(error).__name__)

            for source, name in ((proc.process.stdout, "stdout.log"), (proc.process.stderr, "stderr.log")):
                thread = threading.Thread(target=copy, args=(source, name), daemon=True)
                thread.start()
                readers.append(thread)
            while proc.poll() is None:
                proc.job.observe_members()
                lease.recheck()
                require(not overflow.is_set() and not reader_errors, "REFERENCE_LOG_UNAVAILABLE")
                if bound_at is None:
                    first = first_start(spool, authority)
                    if first is not None:
                        _, event, payload = first
                        identity = proc.job.member_identity(payload.launch_identity.pid)
                        body["binding"] = bind_identity(plan, setup, payload.launch_identity, identity)
                        body["server_boot_id"] = event.server_boot_id
                        body["launch_binding_verified"] = True
                        bound_at = time.monotonic()
                        self._record(plan.instance_id, "BOUND", body)
                now = time.monotonic()
                if coordinated and stopped_at is None:
                    if participant is None:
                        require(not (evidence / "participant-completion.json").exists(),
                                "REFERENCE_PARTICIPANT_PREMATURE")
                        if bound_at is not None and ready.is_set():
                            participant = ParticipantWindow(plan.participant, evidence, plan, body["server_boot_id"],
                                                            now, time.time(), started + plan.max_wall_s)
                            body["participant"] = participant.result
                            body["participant_readiness"] = participant.ready.model_dump(by_alias=True)
                            self._record(plan.instance_id, "PARTICIPANT_READY", body)
                            participant.publish()
                    stop = participant is not None and participant.poll(time.monotonic())
                else:
                    stop = not coordinated and bound_at is not None and ready.is_set() and now - bound_at >= plan.ready_run_s
                stop = stop or now - started >= plan.max_wall_s
                if stop and stopped_at is None:
                    body["stop_sent"] = True
                    self._record(plan.instance_id, "STOPPING", body)
                    stopped_at = now
                    proc.send_input("stop\n")
                if stopped_at is not None and now - stopped_at >= plan.graceful_stop_s:
                    body["forced_stop"] = True
                    proc.stop()
                    break
                time.sleep(0.1)
            body["exit_code"] = proc.process.wait(timeout=2)
            for thread in readers:
                thread.join(2)
            require(not any(thread.is_alive() for thread in readers) and not reader_errors
                    and not overflow.is_set(), "REFERENCE_LOG_UNAVAILABLE")
            body["job_accounting"] = proc.job.accounting()
            body["held_members"] = proc.job.member_status()
            require(body["launch_binding_verified"] and ready.is_set() and body["stop_sent"]
                    and not body["forced_stop"] and body["exit_code"] == 0, "REFERENCE_LIFECYCLE_FAILED")
            require(body["job_accounting"]["active_processes"] == 0, "REFERENCE_PROCESS_STILL_ACTIVE")
            require(body["held_members"]["signaled_processes"] == body["held_members"]["held_processes"]
                    == body["job_accounting"]["total_processes"], "REFERENCE_PROCESS_HISTORY_INCOMPLETE")
            body["log_health"] = {name: inspect_server_log(evidence / name) for name in ("stdout.log", "stderr.log")}
            require(all(check["result"] == "pass" for check in body["log_health"].values()), "SERVER_RUNTIME_FAILURE")
            files = list(spool.glob("*.authenticated.jsonl"))
            require(len(files) == 1, "REFERENCE_SPOOL_MULTIPLE")
            inspection = inspect_authenticated_spool(files[0], authority_path)
            require(inspection["server_boot_id"] == body["server_boot_id"] and
                    inspection["launch_identity"] == body["binding"]["native_observation"], "REFERENCE_START_CHANGED")
            body["spool_sha256"] = inspection["file_sha256"]
            body["records"] = inspection["records"]
            body["sampled_server_ticks"] = inspection["sampled_server_ticks"]
            if coordinated:
                require(participant is not None, "REFERENCE_PARTICIPANT_MISSING")
                participant.finish()
            body["status"] = "stopped_reference"
            lease.recheck()
        except BaseException as error:
            body["status"] = "uncertain"
            body["error"] = error.code if isinstance(error, Fault) else type(error).__name__
        finally:
            if proc:
                try:
                    if proc.poll() is None:
                        body["forced_stop"] = True
                        proc.stop()
                    proc.close()
                except BaseException as error:
                    body.update(status="uncertain", cleanup_error=type(error).__name__)
            for thread in readers:
                thread.join(2)
            if lease:
                lease.close()
            if participant:
                participant.close()
            body["elapsed_s"] = time.monotonic() - started
            state = "STOPPED" if body["status"] == "stopped_reference" else "UNCERTAIN"
            self._record(plan.instance_id, state, body)
            if evidence.is_dir():
                write_new(evidence / "result.json", body)
        return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--client-binding", type=Path)
    args = parser.parse_args()
    plan = strict_json(private_read(args.plan, 8 * 1024**2))
    binding = strict_json(private_read(args.client_binding, 1024**2)) if args.client_binding else None
    database = Database(private_path(args.database))
    try:
        result = ReferenceLauncher(CraftReferenceStore(database)).run(plan, client_binding=binding)
        print(json.dumps(result))
        return 0 if result["status"] == "stopped_reference" else 1
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
