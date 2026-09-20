"""Operator-owned non-input Java lifetime with an independent challenge guardian.

No authentication, GUI driving, game mutation, or campaign admission. Arguments
must already be reviewed and private. Desktop placement is not a security sandbox.
The caller must pump regularly; a blocked caller cannot renew the guardian lease.
"""

import json
import os
from pathlib import Path
import queue
import re
import threading
import time

from .desktop_process import DesktopProcess
from .process_guard import ProcessGuardGrant, inspect_process
from .processes import ManagedProcess
from .storage import Fault, canonical, digest, reject_links, require

POLICY = "noninput-java-independent-challenge-lifetime/1"


class DesktopJava:
    def __init__(self, argv, cwd, environment, private_directory, *, max_wall_ms):
        require(Path(argv[0]).name.casefold() in {"java.exe", "javaw.exe"}, "PROCESS_NOT_JAVA")
        require(type(max_wall_ms) is int and 5000 <= max_wall_ms <= 600000, "INVALID_ARGUMENT")
        root = Path(private_directory)
        require(root.is_absolute(), "UNSAFE_PATH")
        reject_links(root)
        require(root.is_dir() and not root.resolve().is_relative_to(Path(__file__).resolve().parents[2]), "FORBIDDEN")
        self.child = self.guard = None
        self.closed = False
        self.ready = False
        self.terminal = None
        self.failure = None
        self.sequence = 0
        self.events = queue.Queue(maxsize=16)
        self.reader_failed = threading.Event()
        self.journal = (root / "launch.jsonl").open("xb")
        self.written = 0
        try:
            self.record({"kind": "launch_intent", "policy": POLICY, "max_wall_ms": max_wall_ms,
                         "campaign_admission": False})
            self.child = DesktopProcess(argv, cwd, environment, max_wall_ms=max_wall_ms)
            identity = inspect_process(self.child.pid)
            grant = ProcessGuardGrant.model_validate({"schema": "strata/JavaProcessGuardGrant/1",
                "purpose": "dedicated-development-client-lifetime", "campaign_id": "desktop-development",
                "agent_id": "dedicated-client", "epoch": 1, "process": identity.model_dump(),
                "expires_unix_ms": time.time_ns() // 1_000_000 + max_wall_ms,
                "max_wall_ms": max_wall_ms})
            self.process_digest = digest(identity.model_dump())
            grant_file = root / "process-grant.json"
            with grant_file.open("xb") as target:
                target.write(canonical(grant.model_dump(by_alias=True)) + b"\n")
                target.flush()
                os.fsync(target.fileno())
            import sys
            env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            self.guard = ManagedProcess([sys.executable, "-I", "-m", "mcbench.process_guard",
                "--grant", str(grant_file)], root, env, "", interactive=True)
            threading.Thread(target=self.read, args=(self.guard.process.stdout, True), daemon=True).start()
            threading.Thread(target=self.read, args=(self.guard.process.stderr, False), daemon=True).start()
            until = time.monotonic() + 5
            while not self.ready:
                self.pump()
                require(time.monotonic() < until, "PROCESS_GUARD_START_TIMEOUT")
                time.sleep(.01)
            self.record({"kind": "launch_ready", "desktop": self.child.name,
                         "process_digest": self.process_digest, "campaign_admission": False})
        except BaseException:
            self.close()
            raise

    def read(self, stream, parse):
        try:
            total = 0
            while True:
                raw = stream.readline(4097)
                if not raw:
                    return
                total += len(raw)
                require(len(raw) <= 4096 and total <= 2 * 1024**2, "PROCESS_GUARD_OUTPUT_QUOTA")
                if parse:
                    require(raw.endswith(b"\n"), "PROCESS_GUARD_OUTPUT_INVALID")
                    self.events.put_nowait(json.loads(raw))
        except Exception:
            self.reader_failed.set()

    def record(self, value):
        data = canonical({"elapsed_monotonic_ns": time.monotonic_ns(),
                          "utc_unix_ms": time.time_ns() // 1_000_000, **value}) + b"\n"
        require(self.written + len(data) <= 65536, "PROCESS_EVIDENCE_QUOTA")
        self.journal.write(data)
        self.journal.flush()
        os.fsync(self.journal.fileno())
        self.written += len(data)

    def pump(self, *, stopping=False):
        require(not self.closed, "PROCESS_CLOSED")
        require(not self.reader_failed.is_set(), "PROCESS_GUARD_OUTPUT_INVALID")
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            require(isinstance(event, dict) and event.get("schema") == "strata/ProcessGuardEvent/1",
                    "PROCESS_GUARD_OUTPUT_INVALID")
            kind = event.get("kind")
            if kind == "ready":
                require(not self.ready and event.get("process_digest") == self.process_digest
                        and event.get("campaign_admission") is False, "PROCESS_GUARD_IDENTITY_MISMATCH")
                self.ready = True
                self.record(event)
            elif kind == "challenge":
                require(self.ready and type(event.get("seq")) is int and event["seq"] == self.sequence + 1
                        and isinstance(event.get("nonce"), str) and len(event["nonce"]) == 32,
                        "PROCESS_GUARD_OUTPUT_INVALID")
                self.sequence = event["seq"]
                if not stopping:
                    self.guard.send_input(json.dumps({"kind": "renew", "seq": event["seq"],
                                                     "nonce": event["nonce"]}) + "\n", timeout_s=.25)
            elif kind == "stopped":
                require(self.terminal is None and event.get("termination_confirmed") is True
                        and event.get("release_confirmed") is False, "PROCESS_STOP_UNCONFIRMED")
                self.terminal = event
                self.record(event)
            elif kind == "failed":
                require(set(event) == {"schema", "kind", "reason", "termination_confirmed"}
                        and event["termination_confirmed"] is False
                        and isinstance(event["reason"], str)
                        and re.fullmatch(r"[A-Z_]{1,96}", event["reason"]) is not None,
                        "PROCESS_GUARD_OUTPUT_INVALID")
                self.failure = event
                self.record(event)
                raise Fault("PROCESS_GUARD_FAILED")
            else:
                raise Fault("PROCESS_GUARD_FAILED")
        if self.guard.poll() is not None and self.terminal is None:
            # A final pipe event may still be in transit; caller retries until its
            # bounded shutdown/startup deadline. Never treat this as readiness.
            require(stopping, "PROCESS_GUARD_EXITED")
        require(self.terminal is None or stopping, "PROCESS_GUARD_STOPPED")

    def close(self):
        if self.closed:
            return
        error = None
        try:
            if self.guard:
                if self.guard.poll() is None:
                    self.guard.send_input('{"kind":"stop"}\n', timeout_s=.25)
                until = time.monotonic() + 3
                while self.terminal is None and time.monotonic() < until:
                    self.pump(stopping=True)
                    time.sleep(.01)
                require(self.terminal is not None, "PROCESS_STOP_UNCONFIRMED")
        except Exception as fault:
            error = fault
        finally:
            try:
                if self.guard:
                    self.guard.close()
            finally:
                try:
                    if self.child:
                        self.child.close()
                finally:
                    self.closed = True
                    self.journal.close()
        if error:
            raise error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
