"""Operator-only Windows Java process lifetime guard; not a gameplay command.

This foundation deliberately owns the *whole* dedicated client lifetime. Every
exit after attachment terminates that client. A forced exit is not an input
release receipt or a clean Minecraft/agent checkpoint. Worker/bridge admission
and durable controller evidence integration are separate requirements.
"""

import argparse
import ctypes
import hashlib
import json
import os
import queue
import re
import secrets
import sys
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from .contracts import Digest, Id, Strict
from .native_settings import strict_json
from .processes import WindowsJob
from .storage import Fault, canonical, digest, reject_links, require

LEASE_SECONDS = 1.5
POLL_SECONDS = .01
STOP_WAIT_MS = 500


class ProcessIdentity(Strict):
    pid: int = Field(ge=1, le=0xFFFFFFFF)
    # FILETIME does not fit losslessly in a JavaScript number.
    created_filetime: str = Field(pattern=r"^[1-9][0-9]{0,19}$")
    executable_path: str = Field(min_length=1, max_length=32767)
    executable_sha256: Digest


class ProcessGuardGrant(Strict):
    wire_schema: Literal["strata/JavaProcessGuardGrant/1"] = Field(alias="schema")
    purpose: Literal["dedicated-development-client-lifetime"]
    campaign_id: Id
    agent_id: Id
    epoch: int = Field(ge=1, le=9007199254740991)
    process: ProcessIdentity
    expires_unix_ms: int = Field(ge=1, le=9007199254740991)
    max_wall_ms: int = Field(ge=1, le=600000)


class HeldProcess:
    """Validate and act through one HANDLE, never re-open a cached PID to kill.

    No command line, environment or account credentials are inspected. The image
    hash is a check of the on-disk executable, not loaded-code attestation.
    """

    def __init__(self, pid: int, *, may_attach=False):
        require(os.name == "nt", "PROCESS_GUARD_UNSUPPORTED")
        require(type(pid) is int and 0 < pid <= 0xFFFFFFFF, "PROCESS_ID_INVALID")
        from ctypes import wintypes

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "GetProcessTimes": ([wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4,
                                wintypes.BOOL),
            "QueryFullProcessImageNameW": ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                            ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result
        # QUERY_LIMITED_INFORMATION + SYNCHRONIZE; attach additionally needs
        # PROCESS_SET_QUOTA + PROCESS_TERMINATE. Handles are not inheritable.
        rights = 0x1000 | 0x100000 | (0x100 | 1 if may_attach else 0)
        self.handle = self.kernel.OpenProcess(rights, False, pid)
        require(bool(self.handle), "PROCESS_IDENTITY_UNAVAILABLE")
        try:
            require(not self.exited(), "PROCESS_NOT_RUNNING")
            created, exited, kernel, user = [wintypes.FILETIME() for _ in range(4)]
            require(bool(self.kernel.GetProcessTimes(self.handle, ctypes.byref(created),
                    ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user))),
                    "PROCESS_IDENTITY_UNAVAILABLE")
            size = wintypes.DWORD(32768)
            path_buffer = ctypes.create_unicode_buffer(size.value)
            require(bool(self.kernel.QueryFullProcessImageNameW(self.handle, 0, path_buffer,
                                                               ctypes.byref(size))),
                    "PROCESS_IDENTITY_UNAVAILABLE")
            path = Path(path_buffer.value)
            require(path.is_absolute(), "PROCESS_IDENTITY_UNAVAILABLE")
            reject_links(path)
            with path.open("rb") as source:
                image_hash = hashlib.file_digest(source, "sha256").hexdigest()
            self.identity = ProcessIdentity(pid=pid,
                created_filetime=str((created.dwHighDateTime << 32) | created.dwLowDateTime),
                executable_path=str(path.resolve()), executable_sha256=image_hash)
            require(not self.exited(), "PROCESS_NOT_RUNNING")
        except BaseException:
            self.close()
            raise

    def exited(self, timeout_ms=0):
        result = self.kernel.WaitForSingleObject(self.handle, timeout_ms)
        require(result in (0, 258), "PROCESS_STATE_UNAVAILABLE")
        return result == 0

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def inspect_process(pid: int):
    """Read-only identity inspection. This does not authorize attachment."""
    process = HeldProcess(pid)
    try:
        return process.identity
    finally:
        process.close()


class AttachedJava:
    def __init__(self, identity: ProcessIdentity, *, deadline=None):
        self.process = HeldProcess(identity.pid, may_attach=True)
        self.job = None
        self.ownership = None
        self.termination_timing = None
        try:
            require(self.process.identity == identity, "PROCESS_IDENTITY_MISMATCH")
            require(Path(identity.executable_path).name.casefold() in {"java.exe", "javaw.exe"},
                    "PROCESS_NOT_JAVA")
            from ctypes import wintypes

            create = self.process.kernel.CreateMutexW
            create.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            create.restype = wintypes.HANDLE
            name = "Local\\StrataJavaGuard-" + digest({"pid": identity.pid,
                                                       "created": identity.created_filetime})
            ctypes.set_last_error(0)
            self.ownership = create(None, False, name)
            require(bool(self.ownership), "PROCESS_FENCING_UNAVAILABLE")
            require(ctypes.get_last_error() != 183, "PROCESS_GUARD_OWNED")
            require(deadline is None or time.monotonic() < deadline, "PROCESS_GRANT_EXPIRED")
            self.job = WindowsJob()
            self.job.attach_handle(self.process.handle)
            require(not self.process.exited(), "PROCESS_NOT_RUNNING")
            self.job.observe_members()
        except BaseException:
            self.close()
            raise

    def terminate(self):
        # Always terminate the job, even if the root already exited, to reap
        # descendants created *after* attachment. Pre-existing children are not
        # enrolled by AssignProcessToJobObject and require launch integration.
        tracking_failed = False
        try:
            self.job.observe_members()
        except Exception:
            # An inventory failure must never postpone the termination request.
            tracking_failed = True
        started = time.perf_counter_ns()
        timing = self.termination_timing = {
            "policy": "job-call-wait-tree-qpc/2", "started_qpc_ns": str(started),
            "clock_resolution_ns": round(time.get_clock_info("perf_counter").resolution * 1e9),
            "wait_bound_ms": STOP_WAIT_MS, "job_succeeded": False,
            "job_returned_after_ns": None, "wait_started_after_ns": None,
            "wait_returned_after_ns": None, "wait_result": "not_started",
            "tree_checked_after_ns": None, "active_processes": None,
            "tree_result": "not_started",
            "total_processes": None, "held_processes": None, "signaled_processes": None,
        }
        try:
            self.job.terminate()
            timing["job_succeeded"] = True
        finally:
            timing["job_returned_after_ns"] = time.perf_counter_ns() - started
        timing["wait_started_after_ns"] = time.perf_counter_ns() - started
        try:
            signaled = self.process.exited(STOP_WAIT_MS)
            timing["wait_result"] = "signaled" if signaled else "timeout"
        except BaseException:
            timing["wait_result"] = "error"
            raise
        finally:
            timing["wait_returned_after_ns"] = time.perf_counter_ns() - started
        require(signaled, "PROCESS_STOP_UNCONFIRMED")
        # A signaled root does not establish that its descendants have stopped.
        # Spend only the remainder of the same 500 ms wait, never a new allowance.
        timing["tree_result"] = "error"
        checked = timing["wait_returned_after_ns"]
        if tracking_failed:
            timing["tree_checked_after_ns"] = checked
            raise Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
        while True:
            remaining = STOP_WAIT_MS * 1_000_000 - (checked - timing["wait_started_after_ns"])
            if remaining <= 0:
                timing["tree_checked_after_ns"] = checked
                timing["tree_result"] = "timeout"
                raise Fault("PROCESS_STOP_UNCONFIRMED")
            timing.update(active_processes=None, total_processes=None,
                          held_processes=None, signaled_processes=None)
            try:
                accounting, members = self.job.accounting(), self.job.member_status()
                count, total = accounting["active_processes"], accounting["total_processes"]
                held, signaled = members["held_processes"], members["signaled_processes"]
                require(all(type(x) is int and x >= 0 for x in (count, total, held, signaled))
                        and count <= total and signaled <= held <= total, "PROCESS_STATE_UNAVAILABLE")
                timing["active_processes"] = count
                timing.update(total_processes=total, held_processes=held, signaled_processes=signaled)
            finally:
                checked = timing["tree_checked_after_ns"] = time.perf_counter_ns() - started
            remaining = STOP_WAIT_MS * 1_000_000 - (checked - timing["wait_started_after_ns"])
            if remaining < 0:
                timing["tree_result"] = "timeout"
                raise Fault("PROCESS_STOP_UNCONFIRMED")
            if count == 0:
                if total != held or held == 0:
                    timing["tree_result"] = "incomplete"
                    raise Fault("PROCESS_STOP_UNCONFIRMED")
                if signaled == held:
                    timing["tree_result"] = "empty"
                    return
            time.sleep(min(POLL_SECONDS, remaining / 1_000_000_000))
            checked = time.perf_counter_ns() - started

    def close(self):
        if self.job:
            self.job.close()
        if self.ownership:
            self.process.kernel.CloseHandle(self.ownership)
            self.ownership = None
        self.process.close()


def read_grant(path: Path, repository: Path, model=ProcessGuardGrant):
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(not path.resolve().is_relative_to(repository.resolve()), "FORBIDDEN")
    with path.open("rb") as source:
        raw = source.read(8193)
    require(len(raw) <= 8192, "PROCESS_GRANT_QUOTA")
    try:
        grant = model.model_validate(strict_json(raw))
    except (ValidationError, UnicodeError, ValueError):
        raise Fault("PROCESS_GRANT_INVALID") from None
    remaining = grant.expires_unix_ms - time.time_ns() // 1000000
    require(0 < remaining <= 600000, "PROCESS_GRANT_EXPIRED")
    require(Path(grant.process.executable_path).is_absolute(), "PROCESS_GRANT_INVALID")
    return grant


class GuardPipes:
    """Bounded pipe IO on daemon threads; neither pipe can block the watchdog."""

    def __init__(self, source, sink):
        self.received = queue.Queue(maxsize=2)
        self.outgoing = queue.Queue(maxsize=8)
        self.failed = threading.Event()

        def read():
            try:
                while True:
                    raw = source.readline(1025)
                    if not raw:
                        self.failed.set()
                        return
                    require(len(raw) <= 1024 and raw.endswith(b"\n"), "PROCESS_LEASE_INVALID")
                    self.received.put_nowait(strict_json(raw))
            except Exception:
                self.failed.set()

        def write():
            try:
                while True:
                    payload = self.outgoing.get()
                    try:
                        sink.write(canonical(payload) + b"\n")
                        sink.flush()
                    finally:
                        self.outgoing.task_done()
            except Exception:
                self.failed.set()

        threading.Thread(target=read, daemon=True).start()
        threading.Thread(target=write, daemon=True).start()

    def emit(self, payload):
        try:
            self.outgoing.put_nowait(payload)
        except queue.Full:
            self.failed.set()
            raise Fault("PROCESS_GUARD_PIPE_FAILED") from None


def guard(grant: ProcessGuardGrant, pipes: GuardPipes, *, ready_extra=None, health_check=None,
          termination_evidence=False):
    """Independent challenge lease. Stale queued heartbeats cannot renew it.

    Parent must answer each fresh nonce with {"kind":"renew", "seq":N,
    "nonce":"..."}; {"kind":"stop"} ends this dedicated client lifetime.
    There is intentionally no detach/disarm command.
    """
    started = time.monotonic()
    remaining = (grant.expires_unix_ms - time.time_ns() // 1000000) / 1000
    require(0 < remaining <= 600, "PROCESS_GRANT_EXPIRED")
    deadline = started + min(remaining, grant.max_wall_ms / 1000)
    target = AttachedJava(grant.process, deadline=deadline)
    reason = "PROCESS_GUARD_FAILURE"
    confirmed = False
    detected = time.monotonic()
    try:
        pipes.emit({"schema": "strata/ProcessGuardEvent/1", "kind": "ready",
                    "process_digest": digest(grant.process.model_dump()),
                    "campaign_id": grant.campaign_id, "agent_id": grant.agent_id,
                    "epoch": grant.epoch, "whole_client_lifetime": True,
                    "campaign_admission": False,
                    "remaining_wall_ms": max(0, int((deadline - time.monotonic()) * 1000)),
                    **(ready_extra or {})})
        sequence, nonce, lease_until, next_challenge = 0, None, started, started
        while True:
            target.job.observe_members()
            now = time.monotonic()
            if target.process.exited():
                reason = "PROCESS_EXITED"
                break
            health_failure = health_check(now) if health_check else None
            if health_failure:
                reason = health_failure
                break
            if pipes.failed.is_set():
                reason = "PROCESS_GUARD_PIPE_FAILED"
                break
            if now >= deadline:
                reason = "PROCESS_WALL_LIMIT"
                break
            if nonce is not None and now >= lease_until:
                reason = "PROCESS_LEASE_EXPIRED"
                break
            if nonce is None and now >= next_challenge:
                sequence += 1
                nonce = secrets.token_hex(16)
                lease_until = now + LEASE_SECONDS
                next_challenge = now + .25
                pipes.emit({"schema": "strata/ProcessGuardEvent/1", "kind": "challenge",
                            "seq": sequence, "nonce": nonce, "lease_ms": 1500})
            try:
                message = pipes.received.get_nowait()
            except queue.Empty:
                time.sleep(POLL_SECONDS)
                continue
            if message == {"kind": "stop"}:
                reason = "PROCESS_STOP_REQUESTED"
                break
            if (not isinstance(message, dict) or set(message) != {"kind", "seq", "nonce"}
                    or message.get("kind") != "renew" or type(message.get("seq")) is not int
                    or message["seq"] != sequence or nonce is None or message.get("nonce") != nonce):
                reason = "PROCESS_LEASE_INVALID"
                break
            nonce = None
        detected = time.monotonic()
        target.terminate()
        confirmed = True
    finally:
        # Kernel kill-on-close also covers guard crash/SIGKILL after attachment.
        target.close()
        # Evidence queues only after closing guardian handles; backpressure must never
        # postpone termination. The base guardian's wire contract stays unchanged.
        if termination_evidence and target.termination_timing is not None:
            pipes.emit({"schema": "strata/ProcessGuardEvent/1", "kind": "termination_timing",
                        **target.termination_timing})
    result = {"schema": "strata/ProcessGuardEvent/1", "kind": "stopped", "reason": reason,
              "termination_confirmed": confirmed, "release_confirmed": False,
              "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
              "termination_wait_ms": round((time.monotonic() - detected) * 1000, 3),
              "requires_resync": True, "campaign_admission": False}
    pipes.emit(result)
    return result


def failure_event(error):
    code = error.code if isinstance(error, Fault) else "PROCESS_GUARD_FAILURE"
    if not isinstance(code, str) or re.fullmatch(r"[A-Z_]{1,96}", code) is None:
        code = "PROCESS_GUARD_FAILURE"
    return {"schema": "strata/ProcessGuardEvent/1", "kind": "failed",
            "reason": code, "termination_confirmed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--inspect", type=int, metavar="PID")
    commands.add_argument("--grant", type=Path)
    args = parser.parse_args()
    try:
        if args.inspect is not None:
            print(inspect_process(args.inspect).model_dump_json())
            return 0
        grant = read_grant(args.grant, Path(__file__).resolve().parents[2])
        pipes = GuardPipes(sys.stdin.buffer, sys.stdout.buffer)
        try:
            result = guard(grant, pipes)
            code = 0 if result["reason"] in {"PROCESS_EXITED", "PROCESS_STOP_REQUESTED"} else 1
        except Exception as error:
            pipes.emit(failure_event(error))
            code = 1
        # Output is best effort, never a reason to keep the Java client alive.
        until = time.monotonic() + .1
        while pipes.outgoing.unfinished_tasks and time.monotonic() < until:
            time.sleep(.005)
        # The daemon reader may still own buffered stdin; do not deadlock Python
        # interpreter finalization on that lock after the process has been stopped.
        os._exit(code)
    except Exception as error:
        print(json.dumps({"kind": "failed", "reason": error.code if isinstance(error, Fault)
                          else "PROCESS_GUARD_FAILURE"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
