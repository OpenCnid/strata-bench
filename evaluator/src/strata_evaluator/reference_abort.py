"""Private cooperative abort; cleanup never converts uncertain evidence to a pass."""

import re
import os
import hashlib
import threading
from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Id, Strict
from mcbench.inference_transport import strict_json
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault, digest, require

from .craft_reference import private_path
from .reference_participant import publish
from .telemetry_auth import private_read

Phase = Literal[
    "server_monitor",
    "client_monitor",
    "client_deadline",
    "server_deadline",
    "client_driver",
    "outer_cleanup",
]
ABORT_FILE = "outer-abort.json"


class MonitorFailure(Strict):
    phase: Phase
    error_type: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,79}$")
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,127}$")


def failure_record(phase, error):
    """Keep typed codes, never exception messages/arguments that may hold secrets."""
    name = type(error).__name__
    code = error.code if isinstance(error, Fault) else "REFERENCE_MONITOR_EXCEPTION"
    return MonitorFailure(
        phase=phase,
        error_type=name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", name) else "Exception",
        code=code
        if isinstance(code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", code)
        else "REFERENCE_UNCLASSIFIED_FAULT",
    )


class AbortScope(Strict):
    instance_id: Id
    participant_id: Id
    launch_plan_digest: Digest
    challenge: Digest


class AbortRequest(AbortScope):
    schema_: Literal["strata/ReferenceOuterAbort/1"] = Field(alias="schema")
    failure: MonitorFailure


def abort_scope(launch):
    value = launch.model_dump(by_alias=True) if hasattr(launch, "model_dump") else launch
    require(value.get("schema") == "strata/PrivateReferenceLaunch/3", "REFERENCE_ABORT_PROFILE")
    return AbortScope(
        instance_id=value["instance_id"],
        participant_id=value["participant"]["participant_id"],
        launch_plan_digest=digest(value),
        challenge=value["outer_challenge"],
    )


def request_abort(evidence, launch, phase, error):
    """Call once after durably recording the outer failure; never replace a request."""
    value = AbortRequest.model_validate(
        {
            "schema": "strata/ReferenceOuterAbort/1",
            **abort_scope(launch).model_dump(),
            "failure": failure_record(phase, error).model_dump(),
        }
    )
    publish(private_path(evidence) / ABORT_FILE, value.model_dump(by_alias=True))
    return value


class AbortSignal:
    """Sticky bounded reader. Foreign/malformed control is itself an abort fault."""

    def __init__(self, launch, evidence):
        self.scope = abort_scope(launch)
        self.path = private_path(evidence) / ABORT_FILE
        self.result = None

    def poll(self):
        if self.result is not None:
            return True
        try:
            if not os.path.lexists(self.path):
                return False
            raw = private_read(self.path, 8192)
            request = AbortRequest.model_validate(strict_json(raw))
            require(
                AbortScope.model_validate(request.model_dump(exclude={"schema_", "failure"}))
                == self.scope,
                "REFERENCE_ABORT_SCOPE",
            )
            self.result = {
                "status": "requested",
                "request": request.model_dump(by_alias=True),
                "request_sha256": hashlib.sha256(raw).hexdigest(),
                "request_bytes": len(raw),
                "scoring_eligible": False,
            }
        except Exception as error:
            self.result = {
                "status": "invalid",
                "failure": failure_record("outer_cleanup", error).model_dump(),
                "scoring_eligible": False,
            }
        return True


class ParticipantAbortGuard:
    """Trusted operator driver guard for its retained, owned process objects.

    Start children through start(), check() before public command admission, and
    close() before writing the terminal report. An independent thread stops only
    these owned objects on abort even when the driver is blocked in a command.
    The driver still owns normal cleanup/handle close and its hard watchdog.
    This is not the 500-ms guardian and cannot qualify isolation or execution.
    """

    def __init__(self, launch, evidence):
        self.signal = AbortSignal(launch, evidence)
        value = launch.model_dump(by_alias=True) if hasattr(launch, "model_dump") else launch
        self.cleanup_ms = value["abort_cleanup_ms"]
        require(
            type(self.cleanup_ms) is int and 500 <= self.cleanup_ms <= 15000,
            "REFERENCE_ABORT_EXPOSURE",
        )
        self.lock = threading.RLock()
        self.stop_lock = threading.Lock()
        self.done = threading.Event()
        self.resources = []
        self.stopped = False
        self.errors = []
        self.closed = False
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()

    def _stop_owned(self):
        with self.stop_lock:
            if self.stopped:
                return
            with self.lock:
                resources = list(reversed(self.resources))
            for process in resources:
                try:
                    process.stop()  # Retained Job/process handle, never PID rediscovery.
                except Exception as error:
                    self.errors.append(failure_record("outer_cleanup", error).model_dump())
            self.stopped = True

    def _watch(self):
        while not self.done.wait(0.05):
            with self.lock:
                requested = self.signal.poll()
            if requested:
                self._stop_owned()
                return

    def check(self):
        with self.lock:
            require(not self.closed, "REFERENCE_ABORT_GUARD_CLOSED")
            requested = self.signal.poll()
        if requested:
            raise Fault("REFERENCE_OUTER_ABORT_REQUESTED")

    def start(self, factory):
        # Only short, already authorized owned-process creation belongs here.
        # Holding the gate across creation lets the watcher see the retained
        # object even if the signal arrives while the OS is creating the child.
        from mcbench.desktop_process import DesktopProcess

        with self.lock:
            require(not self.closed, "REFERENCE_ABORT_GUARD_CLOSED")
            require(not self.signal.poll(), "REFERENCE_OUTER_ABORT_REQUESTED")
            require(len(self.resources) < 2, "REFERENCE_ABORT_OWNER_QUOTA")
            process = factory()
            require(isinstance(process, (ManagedProcess, DesktopProcess)), "REFERENCE_ABORT_OWNER")
            self.resources.append(process)
        self.check()
        return process

    def close(self):
        # Closing the guard is not evidence of normal child termination. A final
        # poll catches an already published abort before the terminal report.
        with self.lock:
            requested = self.signal.poll()
            self.closed = True
        if not requested:
            self.done.set()
        self.thread.join(self.cleanup_ms / 1000)
        require(not self.thread.is_alive(), "REFERENCE_ABORT_GUARD_UNCONFIRMED")
        # The watcher never closes handles underneath the driver. Handle close
        # happens only after its bounded stop attempt has actually returned.
        for process in reversed(self.resources):
            try:
                process.close()
            except Exception as error:
                self.errors.append(failure_record("outer_cleanup", error).model_dump())
        return self.report()

    def report(self):
        return {
            "schema": "strata/ReferenceParticipantAbortObservation/1",
            "abort": self.signal.result,
            "stop_attempted": self.stopped,
            "cleanup_errors": list(self.errors),
            "watcher_terminal": not self.thread.is_alive(),
            "participant_execution_verified": False,
            "guardian_qualified": False,
            "scoring_eligible": False,
        }
