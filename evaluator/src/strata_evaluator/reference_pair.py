"""One-use private reference pair; owned deadlines do not certify a game result."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Literal

from pydantic import Field

from mcbench.contracts import Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease
from mcbench.processes import ManagedProcess, ProcessInventoryFault
from mcbench.storage import Database, Fault, canonical, digest, reject_links, require

from .craft_reference import CraftReferenceStore, PrivateFile, check_file, private_path
from .reference_abort import AbortSignal, failure_record, request_abort
from .reference_launch import ReferenceLaunchPlanV3, parse_launch_plan
from .reference_participant import ParticipantReady, publish, REPORT_LIMIT
from .telemetry_auth import private_read

LOG_LIMIT = 16 * 1024**2


def read_pinned(pin, limit):
    raw = private_read(pin.path, limit)
    require(
        len(raw) == pin.bytes and hashlib.sha256(raw).hexdigest() == pin.sha256,
        "CRAFT_FILE_CHANGED",
    )
    return strict_json(raw)


class ReferencePairPlan(Strict):
    schema_: Literal["strata/PrivateReferencePair/1"] = Field(alias="schema")
    launch_file: PrivateFile
    client_binding: PrivateFile | None = None
    client_driver: PrivateFile
    python: PrivateFile
    bootstrap: PrivateFile
    source_root: str
    # Explicit source/config/helper inputs, held through the complete pair.
    inputs: list[PrivateFile] = Field(min_length=1, max_length=2000)
    evidence_directory: str
    client_window_ms: int = Field(ge=1000, le=420000)
    finalize_ms: int = Field(ge=1000, le=15000)


class OwnedCli:
    """An independent finite watchdog, retained Job and bounded private logs."""

    def __init__(self, process, role, evidence, deadline):
        self.process, self.role, self.evidence = process, role, evidence
        self.deadline = deadline
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.fired = False
        self.errors = []
        self.readers = []
        # Install the deadline before process observation or log reads can fail.
        self.watcher = threading.Thread(target=self._watch, daemon=True)
        self.watcher.start()
        for stream, suffix in (
            (process.process.stdout, "stdout"),
            (process.process.stderr, "stderr"),
        ):
            reader = threading.Thread(target=self._drain, args=(stream, suffix), daemon=True)
            reader.start()
            self.readers.append(reader)

    def _drain(self, stream, suffix):
        try:
            with (self.evidence / f"{self.role}.{suffix}.log").open("xb") as out:
                count = 0
                while block := stream.read(4096):
                    count += len(block)
                    require(count <= LOG_LIMIT, "REFERENCE_PAIR_LOG_QUOTA")
                    out.write(block)
                    out.flush()
                os.fsync(out.fileno())
        except Exception as error:
            self.errors.append(failure_record("outer_cleanup", error).model_dump())

    def shorten(self, deadline):
        with self.lock:
            self.deadline = min(self.deadline, deadline)

    def _watch(self):
        while not self.done.wait(0.025):
            with self.lock:
                due = time.monotonic() >= self.deadline
            if not due:
                continue
            try:
                if (
                    self.process.poll() is not None
                    and self.process.job.accounting()["active_processes"] == 0
                ):
                    return  # The owned tree is already empty; retained history is checked separately.
            except Exception as error:
                self.errors.append(failure_record("outer_cleanup", error).model_dump())
            self.fired = True
            fault = failure_record(self.role + "_deadline", Fault("REFERENCE_PAIR_HARD_DEADLINE"))
            try:
                publish(self.evidence / f"{self.role}-watchdog.json", fault.model_dump())
            except Exception as error:
                self.errors.append(failure_record("outer_cleanup", error).model_dump())
            try:
                # No PID discovery; this terminates the retained complete outer Job.
                self.process.job.terminate()
            except Exception as error:
                self.errors.append(failure_record("outer_cleanup", error).model_dump())
            return

    def observe(self):
        require(not self.fired, "REFERENCE_PAIR_HARD_DEADLINE")
        require(not self.errors, "REFERENCE_PAIR_LOG_UNAVAILABLE")
        self.process.job.observe_members()
        return self.process.poll()

    def finish(self):
        result = {"forced": self.fired, "errors": []}
        try:
            # A root exit can precede its descendants' kernel signaling. Reconcile
            # within the original deadline; never turn incomplete history into proof.
            until = min(self.deadline, time.monotonic() + 2)
            while True:
                accounting = self.process.job.accounting()
                held = self.process.job.member_status()
                if (
                    self.process.poll() is not None
                    and accounting["active_processes"] == 0
                    and held["signaled_processes"] == held["held_processes"]
                ):
                    break
                if time.monotonic() >= until:
                    break
                time.sleep(0.01)
            if self.process.poll() is None or self.process.job.accounting()["active_processes"]:
                result["forced"] = True
                self.process.stop()
                # TerminateJobObject/root wait can precede signaling of other
                # retained handles even after active_processes reaches zero.
                # Bound cleanup reconciliation; incomplete history still fails.
                stopped_until = time.monotonic() + 2
                while True:
                    accounting = self.process.job.accounting()
                    held = self.process.job.member_status()
                    if (accounting["active_processes"] == 0
                            and held["held_processes"] == held["signaled_processes"]):
                        break
                    if time.monotonic() >= stopped_until:
                        break
                    time.sleep(0.01)
            result["exit_code"] = self.process.poll()
            result["job"] = self.process.job.accounting()
            result["held"] = self.process.job.member_status()
            result["terminal_verified"] = (
                result["exit_code"] is not None
                and result["job"]["active_processes"] == 0
                and result["held"]["held_processes"]
                == result["held"]["signaled_processes"]
                == result["job"]["total_processes"]
            )
        except Exception as error:
            result["errors"].append(failure_record("outer_cleanup", error).model_dump())
            result["terminal_verified"] = False
            result["forced"] = True
            try:
                self.process.stop()
            except Exception as stop_error:
                result["errors"].append(failure_record("outer_cleanup", stop_error).model_dump())
        finally:
            self.done.set()
            self.watcher.join(2)
            if self.watcher.is_alive():
                # Never let missing watcher confirmation bypass the retained
                # Job's kill-on-close backstop or release an apparently clean
                # reference. Preserve uncertainty without escaping cleanup.
                result["terminal_verified"] = False
                result["forced"] = True
                result["errors"].append(failure_record("outer_cleanup",
                    Fault("REFERENCE_PAIR_WATCHDOG_UNCONFIRMED")).model_dump())
            result["forced"] = result["forced"] or self.fired
            for reader in self.readers:
                reader.join(2)
            result["logs_complete"] = (
                not any(t.is_alive() for t in self.readers) and not self.errors
            )
            result["errors"].extend(self.errors)
            # Never close a buffered pipe underneath an in-flight read. The Job
            # close is still a kernel backstop; missing drains remain unconfirmed.
            self.process.job.close()
            if not any(t.is_alive() for t in self.readers):
                self.process.close()
        return result


class ReferencePair:
    def __init__(self, database):
        self.database = database
        self.store = CraftReferenceStore(database)
        with database.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS reference_pairs (instance TEXT PRIMARY KEY, "
                "plan TEXT NOT NULL, state TEXT NOT NULL, body TEXT NOT NULL)"
            )

    def _record(self, instance, state, body):
        with self.database.transaction() as db:
            db.execute(
                "UPDATE reference_pairs SET state=?,body=? WHERE instance=?",
                (state, canonical(body).decode(), instance),
            )
            self.database.event(
                db, "private.reference_pair", {"instance": instance, "state": state, **body}
            )

    def run(self, value):
        require(os.name == "nt", "REFERENCE_PLATFORM_UNQUALIFIED")
        plan = ReferencePairPlan.model_validate(value)
        launch = parse_launch_plan(read_pinned(plan.launch_file, 8 * 1024**2))
        require(isinstance(launch, ReferenceLaunchPlanV3), "REFERENCE_PAIR_PROFILE")
        row, setup, _, authority = self.store._load(launch.instance_id)
        require(row["digest"] == launch.setup_digest, "REFERENCE_SETUP_CHANGED")
        evidence = private_path(plan.evidence_directory)
        server_evidence = private_path(launch.evidence_directory)
        report = private_path(launch.participant.report_path)
        require(
            not evidence.exists()
            and evidence.parent.is_dir()
            and not server_evidence.exists()
            and not report.exists(),
            "REFERENCE_PAIR_PATH",
        )
        roots = [evidence, server_evidence, private_path(setup.game_directory), authority.parent]
        require(
            all(
                not a.is_relative_to(b) and not b.is_relative_to(a)
                for i, a in enumerate(roots)
                for b in roots[i + 1 :]
            ),
            "REFERENCE_PAIR_PATH",
        )
        require(not any(report.is_relative_to(root) for root in roots), "REFERENCE_PAIR_PATH")
        source = Path(plan.source_root).resolve()
        reject_links(source)
        require(source == Path(__file__).resolve().parents[3], "REFERENCE_PAIR_SOURCE")
        require(
            Path(plan.python.path).resolve() == Path(sys.executable).resolve()
            and Path(plan.bootstrap.path).resolve() == source / "src/mcbench/process_bootstrap.py",
            "REFERENCE_PAIR_BOOTSTRAP",
        )
        private_path(plan.client_driver.path)
        pins = [plan.launch_file, plan.client_driver, plan.python, plan.bootstrap, *plan.inputs]
        if launch.mode == "e9e-serverstarter":
            from .reference_client import ClientReferenceBinding, validate_client_binding

            require(plan.client_binding is not None, "REFERENCE_CLIENT_BINDING_REQUIRED")
            binding = ClientReferenceBinding.model_validate(
                read_pinned(plan.client_binding, 1024**2)
            )
            validate_client_binding(binding, setup, launch.model_dump(by_alias=True))
            require(
                plan.client_window_ms == binding.client_wall_ms + binding.terminal_reserve_ms,
                "REFERENCE_PAIR_EXPOSURE",
            )
            pins.append(plan.client_binding)
        else:
            require(plan.client_binding is None, "REFERENCE_CLIENT_PROFILE")
        require(
            plan.client_window_ms <= launch.participant.window_s * 1000, "REFERENCE_PAIR_EXPOSURE"
        )
        inventory = {}
        for pin in pins:
            check_file(Path(pin.path), pin)
            key = str(Path(pin.path).resolve())
            require(
                key not in inventory or inventory[key] == pin.model_dump(),
                "REFERENCE_PAIR_PIN_CONFLICT",
            )
            inventory[key] = pin.model_dump()
        # At least the code providing pair/abort/launch behavior must be declared.
        for name in (
            "reference_pair.py",
            "reference_abort.py",
            "reference_launch.py",
            "reference_participant.py",
        ):
            require(
                str(Path(__file__).with_name(name).resolve()) in inventory,
                "REFERENCE_PAIR_SOURCE_UNPINNED",
            )
        body = {
            "schema": "strata/PrivateReferencePairResult/1",
            "status": "uncertain",
            "launch_plan_digest": digest(launch.model_dump(by_alias=True)),
            "pair_plan_digest": digest(plan.model_dump(by_alias=True)),
            "failures": [],
            "process_observations": [],
            "scoring_eligible": False,
            "participant_execution_verified": False,
            "guardian_qualified": False,
            "gameplay_or_inference_admission": False,
            "shared_desktop_input_verified": False,
        }
        lease = FileLease(
            {
                "schema": "strata/LaunchFileInventory/1",
                "trees": [],
                "files": list(inventory.values()),
            }
        )
        processes = {}
        started = time.monotonic()
        ready = None
        aborted_at = None
        published = False
        claimed = False
        signal = AbortSignal(launch, server_evidence)
        try:
            with self.database.transaction() as db:
                require(
                    db.execute(
                        "SELECT 1 FROM reference_pairs WHERE instance=?", (launch.instance_id,)
                    ).fetchone()
                    is None,
                    "REFERENCE_PAIR_ALREADY_DISPATCHED",
                )
                db.execute(
                    "INSERT INTO reference_pairs VALUES (?,?,?,?)",
                    (
                        launch.instance_id,
                        canonical(plan.model_dump(by_alias=True)).decode(),
                        "INTENT",
                        canonical(body).decode(),
                    ),
                )
                self.database.event(
                    db,
                    "private.reference_pair",
                    {"instance": launch.instance_id, "state": "INTENT", **body},
                )
            claimed = True
            evidence.mkdir()
            publish(evidence / "intent.json", body)
            environment = {
                k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ
            }
            environment["PYTHONPATH"] = os.pathsep.join(
                [str(source / "src"), str(source / "evaluator/src")]
            )

            def start(role, arguments, deadline):
                require(aborted_at is None and not signal.poll(), "REFERENCE_OUTER_ABORT_REQUESTED")
                lease.recheck()
                self._record(launch.instance_id, role.upper() + "_DISPATCHING", body)
                process = ManagedProcess(
                    [plan.python.path, "-X", "utf8", *arguments],
                    source,
                    environment,
                    "",
                    bootstrap_python=plan.python.path,
                    bootstrap_script=plan.bootstrap.path,
                )
                try:
                    owned = OwnedCli(process, role, evidence, deadline)
                except BaseException:
                    process.stop()
                    process.close()
                    raise
                processes[role] = owned  # Retained before observation/recording can fail.
                owned.process.job.observe_members()
                publish(
                    evidence / f"{role}-process.json",
                    {"pid": process.process.pid, "elapsed_s": time.monotonic() - started},
                )
                return owned

            arguments = [
                "-m",
                "strata_evaluator.reference_launch",
                "--database",
                str(self.database.path),
                "--plan",
                plan.launch_file.path,
            ]
            if plan.client_binding:
                arguments += ["--client-binding", plan.client_binding.path]
            phase = "server_monitor"
            server = start(
                "server",
                arguments,
                started + launch.max_wall_s + launch.graceful_stop_s + plan.finalize_ms / 1000,
            )
            while True:
                try:
                    for role, owned in processes.items():
                        phase = role + ("_deadline" if owned.fired else "_monitor")
                        owned.observe()
                    if signal.poll():
                        raise Fault("REFERENCE_OUTER_ABORT_REQUESTED")
                    if aborted_at is None and "client" not in processes:
                        phase = "client_monitor"
                        path = server_evidence / "participant-ready.json"
                        if os.path.lexists(path):
                            ready = ParticipantReady.model_validate(
                                strict_json(private_read(path, 8192))
                            )
                            require(
                                (
                                    ready.instance_id,
                                    ready.setup_digest,
                                    ready.launch_plan_digest,
                                    ready.participant_id,
                                    ready.window_ms,
                                )
                                == (
                                    launch.instance_id,
                                    launch.setup_digest,
                                    body["launch_plan_digest"],
                                    launch.participant.participant_id,
                                    launch.participant.window_s * 1000,
                                ),
                                "REFERENCE_PAIR_READINESS",
                            )
                            dispatch = self.database.connection.execute(
                                "SELECT state,body FROM reference_dispatches WHERE instance=?",
                                (launch.instance_id,),
                            ).fetchone()
                            recorded = strict_json(dispatch["body"]) if dispatch else {}
                            require(
                                dispatch is not None
                                and dispatch["state"] == "PARTICIPANT_READY"
                                and recorded.get("launch_binding_verified") is True
                                and recorded.get("participant_readiness")
                                == ready.model_dump(by_alias=True),
                                "REFERENCE_PAIR_READINESS_UNRECORDED",
                            )
                            require(
                                ready.expires_unix_ms - time.time_ns() // 1000000
                                > plan.client_window_ms,
                                "REFERENCE_PAIR_EXPOSURE",
                            )
                            require(
                                server.process.poll() is None
                                and not (server_evidence / "result.json").exists(),
                                "REFERENCE_PAIR_SERVER_TERMINAL",
                            )
                            body["readiness_digest"] = digest(ready.model_dump(by_alias=True))
                            publish(
                                evidence / "client-intent.json",
                                {"readiness_digest": body["readiness_digest"]},
                            )
                            start(
                                "client",
                                [plan.client_driver.path],
                                time.monotonic() + plan.client_window_ms / 1000,
                            )
                    if "client" in processes and processes["client"].process.poll() is not None:
                        phase = "client_monitor"
                        require(
                            processes["client"].process.poll() == 0, "REFERENCE_PAIR_CLIENT_FAILED"
                        )
                        require(
                            report.exists()
                            and (server_evidence / "participant-completion.json").exists(),
                            "REFERENCE_PAIR_CLIENT_REPORT_MISSING",
                        )
                    if server.process.poll() is not None:
                        require(
                            "client" in processes
                            and processes["client"].process.poll() is not None,
                            "REFERENCE_PAIR_SERVER_EARLY_EXIT",
                        )
                        break
                except Exception as error:
                    failure = failure_record(phase, error).model_dump()
                    changed = False
                    if isinstance(error, ProcessInventoryFault):
                        observation = {"phase": phase, **error.observation()}
                        if observation not in body["process_observations"]:
                            require(len(body["process_observations"]) < 64,
                                    "REFERENCE_PAIR_FAILURE_QUOTA")
                            body["process_observations"].append(observation)
                            changed = True
                    if failure not in body["failures"]:
                        require(len(body["failures"]) < 64, "REFERENCE_PAIR_FAILURE_QUOTA")
                        body["failures"].append(failure)
                        changed = True
                    if changed:
                        self._record(launch.instance_id, "ABORT_REQUESTED", body)
                    if aborted_at is None:
                        aborted_at = time.monotonic()
                        for role, owned in processes.items():
                            cleanup = launch.abort_cleanup_ms / 1000
                            if role == "server":
                                cleanup += launch.graceful_stop_s + plan.finalize_ms / 1000
                            owned.shorten(aborted_at + cleanup)
                    # The server owns creation of its evidence directory. An early
                    # failure remains durable while waiting for it; no client starts.
                    if not published and server_evidence.is_dir() and not signal.poll():
                        request_abort(server_evidence, launch, phase, error)
                        published = True
                    if all(owned.process.poll() is not None for owned in processes.values()):
                        break
                time.sleep(0.025)
            if not body["failures"]:
                body["status"] = "stopped_pair"
        except BaseException as error:
            if not claimed:
                raise
            failure = failure_record(locals().get("phase", "outer_cleanup"), error).model_dump()
            body["failures"].append(failure)
            if isinstance(error, ProcessInventoryFault):
                body["process_observations"].append(
                    {"phase": failure["phase"], **error.observation()})
            self._record(launch.instance_id, "ABORT_REQUESTED", body)
        finally:
            if not claimed:
                lease.close()
            else:
                for role, owned in reversed(list(processes.items())):
                    try:
                        body[role + "_process"] = owned.finish()
                    except Exception as error:
                        body[role + "_process"] = {
                            "terminal_verified": False,
                            "failure": failure_record("outer_cleanup", error).model_dump(),
                        }
                    state = body[role + "_process"]
                    if (
                        not state.get("terminal_verified")
                        or state.get("forced")
                        or not state.get("logs_complete")
                        or state.get("errors")
                        or state.get("exit_code") != 0
                    ):
                        body["status"] = "uncertain"
                for name, path in (
                    ("server_result", server_evidence / "result.json"),
                    ("client_result", report),
                ):
                    try:
                        raw = private_read(path, REPORT_LIMIT)
                        value = strict_json(raw)
                        require(isinstance(value, dict), "REFERENCE_PAIR_REPORT_INVALID")
                        with (evidence / (name + ".json")).open("xb") as preserved:
                            preserved.write(raw)
                            preserved.flush()
                            os.fsync(preserved.fileno())
                        body[name] = {
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "bytes": len(raw),
                            "value": value,
                        }
                    except Exception as error:
                        body[name] = {
                            "missing_or_invalid": True,
                            "failure": failure_record("outer_cleanup", error).model_dump(),
                        }
                        body["status"] = "uncertain"
                if (
                    body["failures"]
                    or signal.poll()
                    or body["server_result"].get("value", {}).get("status") != "stopped_reference"
                    or body["client_result"].get("value", {}).get("status") != "pass"
                ):
                    body["status"] = "uncertain"
                if body["status"] == "stopped_pair":
                    dispatch = self.database.connection.execute(
                        "SELECT state,body FROM reference_dispatches WHERE instance=?",
                        (launch.instance_id,),
                    ).fetchone()
                    if (
                        dispatch is None
                        or dispatch["state"] != "STOPPED"
                        or strict_json(dispatch["body"]) != body["server_result"]["value"]
                    ):
                        body["status"] = "uncertain"
                        body["failures"].append(
                            failure_record(
                                "server_monitor", Fault("REFERENCE_PAIR_RESULT_UNRECORDED")
                            ).model_dump()
                        )
                body["outer_abort"] = signal.result
                body["elapsed_s"] = time.monotonic() - started
                lease.close()
                # Never repair/restart the child dispatch or fabricate a terminal receipt.
                self._record(
                    launch.instance_id,
                    "STOPPED" if body["status"] == "stopped_pair" else "UNCERTAIN",
                    body,
                )
                if evidence.is_dir():
                    publish(evidence / "result.json", body)
        return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    value = strict_json(private_read(args.plan, 8 * 1024**2))
    database = Database(private_path(args.database))
    try:
        result = ReferencePair(database).run(value)
        print(json.dumps({k: result[k] for k in ("status", "elapsed_s", "scoring_eligible")}))
        return 0 if result["status"] == "stopped_pair" else 1
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
