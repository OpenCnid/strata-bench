"""Independent Windows Forge development process guard. Operator-only pipes.

The loopback listener must belong to the explicitly granted held Java identity.
Authenticated reads run on the native client thread, independent of Node health.
No arming, gameplay mutation or settings command is issued by this guardian.
"""

import argparse
import ctypes
import hashlib
import json
import os
import queue
import socket
import struct
import sys
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import Field

from .contracts import Digest
from .native_game import GameConnection, NativeGameClient
from .native_settings import strict_json
from .native_restart import NativeRestartCheckpoint
from .native_resume import NativeResumeState
from .worker_repair import WorkerRepairPlan
from .process_guard import (
    D13_STOP_POLICY, LEGACY_STOP_POLICY, GuardPipes, ProcessGuardGrant, failure_event, guard, read_grant,
)
from .storage import Fault, digest, reject_links, require

GUARD_SOURCES = ("forge_guard.py", "process_guard.py", "processes.py", "native_game.py", "native_restart.py", "native_resume.py", "worker_repair.py",
                 "native_settings.py", "contracts.py", "storage.py", "client_discovery.py")


def implementation_digest():
    root = Path(__file__).parent
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                   for name in GUARD_SOURCES})


class ForgeGuardGrant(ProcessGuardGrant):
    wire_schema: Literal["strata/ForgeProcessGuardGrant/1"] = Field(alias="schema")
    connection_file: str = Field(min_length=1, max_length=32767)
    connection_digest: Digest
    native_fingerprint: Digest
    body_fingerprint: Digest
    capability_digest: Digest
    primitive_limit: int = Field(ge=2, le=100000)


class ForgeGuardGrantV2(ForgeGuardGrant):
    wire_schema: Literal["strata/ForgeProcessGuardGrant/2"] = Field(alias="schema")
    shutdown_policy: Literal["java-tree1000-lease750/1"]


class ForgeGuardGrantV3(ForgeGuardGrantV2):
    wire_schema: Literal["strata/ForgeProcessGuardGrant/3"] = Field(alias="schema")
    restart_checkpoint: NativeRestartCheckpoint
    repair_plan: WorkerRepairPlan


class ForgeGuardGrantV4(ForgeGuardGrantV3):
    wire_schema: Literal["strata/ForgeProcessGuardGrant/4"] = Field(alias="schema")
    resume_policy: Literal["operator-owned-settings-resume/1"]


def listener_owned_by(port: int, pid: int):
    """Read only matching IPv4/IPv4-mapped loopback TCP listener ownership.

    No process table, other listener, credentials or command line is exported.
    Wildcard/public bindings are deliberately not equivalent to loopback.
    """
    require(os.name == "nt", "PROCESS_GUARD_UNSUPPORTED")
    from ctypes import wintypes

    api = ctypes.WinDLL("iphlpapi", use_last_error=True).GetExtendedTcpTable
    api.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), wintypes.BOOL,
                   wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
    api.restype = wintypes.DWORD
    owners = set()
    for family in (2, 23):  # Windows AF_INET / AF_INET6; OWNER_PID_LISTENER=3.
        size = wintypes.DWORD(0)
        require(api(None, ctypes.byref(size), False, family, 3, 0) == 122,
                "PROCESS_LISTENER_UNAVAILABLE")
        for _ in range(3):
            require(4 <= size.value <= 4 * 1024 * 1024, "PROCESS_LISTENER_UNAVAILABLE")
            data = ctypes.create_string_buffer(size.value)
            result = api(data, ctypes.byref(size), False, family, 3, 0)
            if result != 122:
                break
        require(result == 0, "PROCESS_LISTENER_UNAVAILABLE")
        raw = data.raw
        count, = struct.unpack_from("<I", raw)
        stride = 24 if family == 2 else 56
        require(count <= (len(raw) - 4) // stride, "PROCESS_LISTENER_UNAVAILABLE")
        for index in range(count):
            offset = 4 + index * stride
            if family == 2:
                state, address, local_port, _, _, owner = struct.unpack_from("<6I", raw, offset)
                matches = struct.pack("<I", address) == socket.inet_aton("127.0.0.1")
            else:
                address, scope, local_port, _, _, _, state, owner = struct.unpack_from(
                    "<16sII16sIIII", raw, offset)
                matches = scope == 0 and address == socket.inet_pton(socket.AF_INET6, "::ffff:127.0.0.1")
            if state == 2 and matches and socket.ntohs(local_port & 0xFFFF) == port:
                owners.add(owner)
    require(owners == {pid}, "PROCESS_LISTENER_MISMATCH")


def connection_for(grant: ForgeGuardGrant):
    path = Path(grant.connection_file)
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(not path.resolve().is_relative_to(Path(__file__).resolve().parents[2]), "FORBIDDEN")
    with path.open("rb") as source:
        raw = source.read(4097)
    require(len(raw) <= 4096, "GAME_CONNECTION_INVALID")
    value = strict_json(raw)
    require(digest(value) == grant.connection_digest, "PROCESS_CONNECTION_MISMATCH")
    connection = GameConnection.model_validate(value)
    require(connection.fingerprint == grant.native_fingerprint, "PROCESS_CONNECTION_MISMATCH")
    listener_owned_by(connection.port, grant.process.pid)
    return NativeGameClient(connection)


class NativeHealth:
    def __init__(self, grant: ForgeGuardGrant, client: NativeGameClient):
        self.grant, self.client = grant, client
        self.period_s = .25 if isinstance(grant, ForgeGuardGrantV2) else 1.0
        self.stale_s = .75 if isinstance(grant, ForgeGuardGrantV2) else 1.5
        self.latest = time.monotonic()
        self.error = None
        self.initial = queue.Queue(maxsize=1)
        self.stop = threading.Event()
        self.identity = None
        self.initial_epoch = None
        self.armed = False
        self.replacement_instance = None
        self.resume_receipt = None
        self._phase = ("authority", time.monotonic_ns())
        self._failure_diagnostic = None
        threading.Thread(target=self._run, daemon=True).start()

    def _enter(self, phase):
        self._phase = (phase, time.monotonic_ns())

    def _run(self):
        try:
            self._enter("authority")
            authority = self.client.call("authority", {}, timeout_ms=500)
            self._enter("authority_scope")
            require(authority["campaign_id"] == self.grant.campaign_id
                    and authority["agent_id"] == self.grant.agent_id
                    and authority["capability_digest"] == self.grant.capability_digest
                    and authority["body_fingerprint"] == self.grant.body_fingerprint
                    and authority["primitive_limit"] == self.grant.primitive_limit
                    and authority["expires_unix_ms"] >= time.time_ns() // 1000000,
                    "PROCESS_NATIVE_AUTHORITY_MISMATCH")
            while not self.stop.is_set():
                self._enter("listener")
                listener_owned_by(self.client.connection.port, self.grant.process.pid)
                self._enter("identity")
                identity = self.client.call("identity", {}, timeout_ms=500)
                self._enter("lane_status")
                health = self.client.call("lane_status", {}, timeout_ms=500)
                self._enter("state")
                require(identity["body_fingerprint"] == self.grant.body_fingerprint,
                        "PROCESS_NATIVE_IDENTITY_MISMATCH")
                require(health["journal_healthy"], "PROCESS_NATIVE_HEALTH_FAILED")
                if isinstance(self.grant, ForgeGuardGrantV4) and self.identity is not None:
                    self._repair_resume_health(identity, health)
                elif isinstance(self.grant, ForgeGuardGrantV3):
                    require(health["fenced"] and health["active_request_id"] is None
                            and time.time_ns() // 1000000 < self.grant.repair_plan.expires_unix_ms,
                            "PROCESS_REPAIR_HOLD_LOST")
                if self.identity is None:
                    replacement = isinstance(self.grant, ForgeGuardGrantV3)
                    if replacement:
                        plan, checkpoint = self.grant.repair_plan, self.grant.restart_checkpoint
                        require(all(getattr(plan, k) == getattr(self.grant, k) for k in ("campaign_id", "agent_id", "epoch"))
                                and plan.transaction_id == checkpoint.request.transaction_id
                                and plan.plan_digest == checkpoint.request.plan_digest, "PROCESS_RESTART_MISMATCH")
                        self._enter("restart_status")
                        state = self.client.call("settings_restart_status", {"restart_id": checkpoint.request.restart_id}, timeout_ms=500)
                        require(state["checkpoint"] == checkpoint.model_dump() and state["phase"] == "prepared"
                                and state["current_instance"] != checkpoint.source_instance
                                and state["expires_unix_ms"] == plan.expires_unix_ms, "PROCESS_RESTART_MISMATCH")
                        self.replacement_instance = state["current_instance"]
                        self._enter("state")
                    require(health["fenced"] and health["active_request_id"] is None
                            and (health["epoch"] == self.grant.epoch if replacement else
                                 health["epoch"] is None or health["epoch"] < self.grant.epoch),
                            "PROCESS_NATIVE_ALREADY_ARMED")
                    self.identity, self.initial_epoch = identity, health["epoch"]
                    self.initial.put_nowait(identity)
                else:
                    require(identity == self.identity, "PROCESS_NATIVE_IDENTITY_MISMATCH")
                    self.armed |= health["epoch"] == self.grant.epoch
                    require(health["epoch"] == self.grant.epoch or not self.armed
                            and health["fenced"] and health["epoch"] == self.initial_epoch,
                            "PROCESS_NATIVE_EPOCH_MISMATCH")
                self.latest = time.monotonic()
                self.stop.wait(self.period_s)
        except Exception as error:
            phase, started = self._phase
            # Memory only on the health path. Publish after guard cleanup, never
            # block native health checks or termination on diagnostic output.
            self._failure_diagnostic = {
                "schema": "strata/ProcessGuardEvent/1", "kind": "native_health_failure",
                "policy": "forge-native-health-phase/1", "phase": phase,
                "elapsed_ms": (time.monotonic_ns() - started) // 1_000_000,
                "read_timeout_ms": 500 if phase in {"authority", "identity", "lane_status", "restart_status", "resume_status"} else None,
                "initialized": self.identity is not None,
                "reason": failure_event(error)["reason"],
            }
            self.error = error.code if isinstance(error, Fault) else "PROCESS_NATIVE_HEALTH_FAILED"

    def _repair_resume_health(self, identity, health):
        plan = self.grant.repair_plan
        if self.resume_receipt is None and health["fenced"]:
            require(health["active_request_id"] is None and time.time_ns() // 1000000 < plan.expires_unix_ms,
                    "PROCESS_REPAIR_HOLD_LOST")
            return
        self._enter("resume_status")
        state = NativeResumeState.model_validate(self.client.call("settings_resume_status",
            {"transaction_id": plan.transaction_id}, timeout_ms=500))
        self._enter("state")
        require(state.input_resumed and state.source_instance == self.replacement_instance
                and state.current_instance == self.replacement_instance
                and state.decision.worker_plan == plan
                and state.decision.connection_generation == identity["connection_generation"]
                and state.health.primitive_limit == self.grant.primitive_limit
                and health["epoch"] == plan.epoch and not health["fenced"], "PROCESS_RESUME_MISMATCH")
        if self.resume_receipt is not None:
            require(state.decision == self.resume_receipt, "PROCESS_RESUME_MISMATCH")
        self.resume_receipt = state.decision

    def failure_diagnostic(self):
        value = self._failure_diagnostic
        return None if value is None else dict(value)

    def prepare(self):
        # No Job Object attachment or worker arming while startup reads are
        # unavailable. Slow trickle responses cannot hold the caller indefinitely.
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            require(self.error is None, self.error or "PROCESS_NATIVE_HEALTH_FAILED")
            try:
                return self.initial.get(timeout=.02)
            except queue.Empty:
                pass
        raise Fault("PROCESS_NATIVE_START_TIMEOUT")

    def failure(self, now):
        return self.error or ("PROCESS_NATIVE_HEALTH_TIMEOUT" if now - self.latest > self.stale_s else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", required=True, type=Path)
    args = parser.parse_args()
    monitor = None
    pipes = None
    try:
        require(sys.version_info[:3] == (3, 12, 14), "PROCESS_GUARD_RUNTIME_MISMATCH")
        grant = read_grant(args.grant, Path(__file__).resolve().parents[2], ForgeGuardGrant | ForgeGuardGrantV2 | ForgeGuardGrantV3 | ForgeGuardGrantV4)
        version2 = isinstance(grant, ForgeGuardGrantV2)
        client = connection_for(grant)
        monitor = NativeHealth(grant, client)
        identity = monitor.prepare()
        pipes = GuardPipes(sys.stdin.buffer, sys.stdout.buffer)
        result = guard(grant, pipes, health_check=monitor.failure, termination_evidence=True,
            stop_policy=D13_STOP_POLICY if version2 else LEGACY_STOP_POLICY,
            ready_extra={"policy": f"forge-process-listener-client-thread/{4 if isinstance(grant, ForgeGuardGrantV4) else 3 if isinstance(grant, ForgeGuardGrantV3) else 2 if version2 else 1}",
                         "connection_digest": grant.connection_digest,
                         "body_fingerprint": identity["body_fingerprint"],
                         "connection_generation": identity["connection_generation"],
                         "implementation_digest": implementation_digest(), "python": "3.12.14"})
        code = 0 if result["reason"] in {"PROCESS_EXITED", "PROCESS_STOP_REQUESTED"} else 1
    except Exception as error:
        body = failure_event(error)
        if pipes:
            try:
                pipes.emit(body)
            except Fault:
                pass
        else:
            print(json.dumps(body), flush=True)
        code = 1
    finally:
        if monitor:
            monitor.stop.set()
            diagnostic = monitor.failure_diagnostic()
            if diagnostic is not None:
                # Startup has not attached a Job, or guard() has returned from
                # its cleanup. Missing output cannot change the failure verdict.
                try:
                    if pipes:
                        pipes.emit(diagnostic)
                    else:
                        print(json.dumps(diagnostic), flush=True)
                except (Fault, OSError):
                    pass
    if pipes:
        until = time.monotonic() + .1
        while pipes.outgoing.unfinished_tasks and time.monotonic() < until:
            time.sleep(.005)
        os._exit(code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
