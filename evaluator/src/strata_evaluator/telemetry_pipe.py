"""Private OS-peer-bound telemetry ingress; signing keys never enter the writer."""

import base64
import ctypes as c
from ctypes import wintypes as w
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time

from mcbench.inference_transport import strict_json
from mcbench.records import GameEvent
from mcbench.processes import ProcessInventoryFault
from mcbench.storage import canonical, require, safe_relative
from .craft_reference import private_path, write_new
from .private_pipe import PrivatePipe
from .telemetry import KINDS, PAYLOADS, LAUNCH_STARTUP_MODELS
from .telemetry_auth import MAX_RECORD, MAX_WIRE_RECORD, POLICY, private_read
from .windows_writer import WindowsSecurity


def controller_start_ms(security):
    function = security.kernel.GetProcessTimes
    function.argtypes = [w.HANDLE, *([c.POINTER(w.FILETIME)] * 4)]
    function.restype = w.BOOL
    created, exited, kernel, user = (w.FILETIME() for _ in range(4))
    require(function(security.kernel.GetCurrentProcess(), c.byref(created), c.byref(exited),
                     c.byref(kernel), c.byref(user)), "TELEMETRY_PIPE_CONTROLLER")
    return ((created.dwHighDateTime << 32 | created.dwLowDateTime) // 10000) - 11644473600000


class TelemetryPipeBroker:
    """One connection/boot, durable-before-ACK, no retry or resume endpoint.

    The caller must retain the writer tree and launch input leases for this
    complete lifecycle. This component alone grants no setup/scoring authority.
    """

    def __init__(self, database, authority, spool, launch_plan, setup, *,
                 writer_sid, group_sid, scope_sid, deadline, settings):
        self.database_path, self.authority = database.path, authority
        self.plan, self.setup = launch_plan, setup
        self.writer_sid, self.group_sid, self.scope_sid = writer_sid, group_sid, scope_sid
        self.spool, self.deadline = private_path(spool), deadline
        game = private_path(setup.game_directory)
        require(not self.spool.exists() and all(not private_path(path).is_relative_to(game)
                for path in (self.spool, self.database_path, authority.key_file)),
                "TELEMETRY_PIPE_SPOOL")
        require(settings == {"schema": "strata/ForgeTelemetryBrokerSettings/1",
            "campaign_id": authority.campaign_id, "epoch": authority.epoch,
            "max_bytes": settings.get("max_bytes"), "max_events": settings.get("max_events"),
            "recipe_ids": list(setup.recipe_digests), "config_queries": []}
            and type(settings["max_bytes"]) is int and 65536 <= settings["max_bytes"] <= 1024**3
            and type(settings["max_events"]) is int and 1 <= settings["max_events"] <= 1000000,
            "TELEMETRY_PIPE_SETTINGS")
        self.settings, self.pipe, self.job = settings, None, None
        self.armed = threading.Event()
        self.closing = threading.Event()
        self.count, self.bytes, self.previous = 0, 0, "0" * 64
        self.boot, self.last_tick, self.stopped = None, -1, False
        self.output = None
        self.body = {"schema": "strata/PrivateTelemetryPipeResult/1", "status": "intent",
                     "authority_digest": authority.fingerprint(), "scoring_eligible": False,
                     "credential_disclosed": False, "configuration_sent": False, "records": 0}
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS telemetry_pipe_boots (authority TEXT PRIMARY KEY, "
                       "state TEXT NOT NULL, body TEXT NOT NULL)")
            require(db.execute("SELECT 1 FROM telemetry_pipe_boots WHERE authority=?",
                    (authority.fingerprint(),)).fetchone() is None, "TELEMETRY_PIPE_ALREADY_RESERVED")
            require(not Path(authority.key_file + ".claimed").exists(), "TELEMETRY_PIPE_ALREADY_CLAIMED")
            db.execute("INSERT INTO telemetry_pipe_boots VALUES(?,?,?)",
                       (authority.fingerprint(), "INTENT", canonical(self.body).decode()))
            database.event(db, "private.telemetry_pipe", self.body)
        try:
            self.spool.mkdir()
            self.pipe = PrivatePipe(group_sid, scope_sid, deadline)
            self.descriptor = {"schema": "strata/ForgeTelemetryConfig/4", "pipe_name": self.pipe.name,
                "controller_pid": os.getpid(), "controller_started_unix_ms": controller_start_ms(self.pipe.security),
                "challenge": secrets.token_hex(32)}
            self.thread = threading.Thread(target=self._serve, name="strata-private-telemetry", daemon=True)
            self.thread.start()
        except BaseException:
            if self.pipe is not None:
                self.pipe.close()
            self._record("UNCERTAIN", error="TELEMETRY_PIPE_START_FAILED")
            raise

    def _record(self, state, **changes):
        self.body.update(status=state.lower(), **changes)
        db = sqlite3.connect(self.database_path, timeout=5, isolation_level=None)
        try:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE telemetry_pipe_boots SET state=?,body=? WHERE authority=?",
                (state, canonical(self.body).decode(), self.authority.fingerprint()))
            db.execute("INSERT INTO outbox(kind,body) VALUES(?,?)",
                       ("private.telemetry_pipe", canonical(self.body).decode()))
            db.commit()
        finally:
            db.close()

    def bind(self, job):
        require(not self.closing.is_set() and not self.armed.is_set()
                and self.job is None and time.monotonic() < self.deadline,
                "TELEMETRY_PIPE_BIND_ONCE")
        self.job = job
        self.armed.set()

    def _peer(self, pid):
        require(self.armed.wait(max(0, self.deadline - time.monotonic())), "TELEMETRY_PIPE_UNBOUND")
        require(not self.closing.is_set() and self.job is not None, "TELEMETRY_PIPE_UNBOUND")
        # Only the lifecycle owner observes/adds Job members. A second observer
        # could race its handle insertion and leak/replace a retained handle.
        # Give that owner a bounded chance to observe a just-connected child;
        # never look up/adopt the caller's PID outside the held member map.
        observed_until = min(self.deadline, time.monotonic() + 0.5)
        while pid not in self.job.members and time.monotonic() < observed_until:
            require(not self.closing.wait(0.01), "TELEMETRY_PIPE_UNBOUND")
        identity = self.job.member_identity(pid)
        require(Path(identity["executable"]).resolve() == Path(self.plan.executable.path).resolve(),
                "TELEMETRY_PIPE_EXECUTABLE")
        security = WindowsSecurity()
        token = security.bind_process(self.job.members[pid], self.writer_sid, self.group_sid, self.scope_sid)
        security.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        security.kernel.WaitForSingleObject.restype = w.DWORD
        require(security.kernel.WaitForSingleObject(self.job.members[pid], 0) == 258, "TELEMETRY_PIPE_PEER_EXITED")
        self._record("BOUND", peer=identity, token=token)
        return identity

    def _event(self, raw, identity, key):
        require(0 < len(raw) <= MAX_RECORD and raw.endswith(b"\n"), "TELEMETRY_PIPE_EVENT_FRAMING")
        event = GameEvent.model_validate(strict_json(raw))
        require(not self.stopped and not event.is_example and event.visibility == "evaluator"
                and event.seq == event.server_event_seq == self.count + 1
                and event.campaign_id == self.authority.campaign_id and event.epoch == self.authority.epoch
                and event.server_tick >= self.last_tick and not event.evidence_refs,
                "TELEMETRY_PIPE_EVENT_SCOPE")
        if self.count:
            require(event.kind != "server_started" and KINDS.get(event.kind) == event.payload_schema,
                    "TELEMETRY_PIPE_EVENT_SCOPE")
            PAYLOADS[event.kind].model_validate(event.payload)
        if self.count == 0:
            require(event.kind == "server_started" and event.server_tick == 0
                    and event.payload_schema in LAUNCH_STARTUP_MODELS,
                    "TELEMETRY_PIPE_FIRST_EVENT")
            model = LAUNCH_STARTUP_MODELS[event.payload_schema]
            payload = model.model_validate(event.payload)
            require(event.payload_schema not in {"strata/ServerStarted/7", "strata/ServerStarted/8"}
                    or payload.telemetry_transport == "windows-owned-pipe/1", "TELEMETRY_PIPE_TRANSPORT")
            from .reference_launch import bind_identity
            binding = bind_identity(self.plan, self.setup, payload.launch_identity, identity)
            self.boot = event.server_boot_id
            safe_relative(self.boot)
            claim = f"{POLICY}\nclaim\n{self.authority.fingerprint()}\n{self.authority.challenge}\n{self.boot}\n"
            write_new(Path(self.authority.key_file + ".claimed"), {
                "schema": "strata/TelemetryBootClaim/1", "challenge": self.authority.challenge,
                "authority_digest": self.authority.fingerprint(), "server_boot_id": self.boot,
                "mac": hmac.digest(key, claim.encode("ascii"), "sha256").hex()})
            self._record("CLAIMED", server_boot_id=self.boot, binding=binding)
            self.output = (self.spool / (self.boot + ".authenticated.jsonl")).open("xb")
        require(event.server_boot_id == self.boot, "TELEMETRY_PIPE_BOOT")
        event_hash = hashlib.sha256(raw).hexdigest()
        text = f"{POLICY}\n{self.authority.fingerprint()}\n{self.authority.challenge}\n{event.seq}\n{self.previous}\n{event_hash}\n"
        mac = hmac.digest(key, text.encode("ascii"), "sha256").hex()
        wire = canonical({"schema": "strata/AuthenticatedTelemetry/1", "policy": POLICY,
            "authority_digest": self.authority.fingerprint(), "challenge": self.authority.challenge,
            "sequence": event.seq, "previous_mac": self.previous,
            "event_base64": base64.b64encode(raw).decode(), "mac": mac}) + b"\n"
        require(len(wire) <= MAX_WIRE_RECORD and self.count < self.settings["max_events"]
                and self.bytes + len(wire) <= self.settings["max_bytes"], "TELEMETRY_PIPE_QUOTA")
        self.output.write(wire)
        self.output.flush()
        os.fsync(self.output.fileno())
        self.count, self.previous, self.bytes, self.last_tick = event.seq, mac, self.bytes + len(wire), event.server_tick
        self.stopped = event.kind == "server_stopped" and event.payload_schema == "strata/ServerStopped/1"
        self._record("DURABLE", records=self.count, bytes=self.bytes, last_event_sha256=event_hash)
        self.pipe.send(canonical({"schema": "strata/TelemetryPipeReceipt/1", "sequence": self.count,
                                  "event_sha256": event_hash}))

    def _serve(self):
        key = b""
        try:
            identity = self._peer(self.pipe.accept())
            request = strict_json(self.pipe.receive(4096))
            require(request == {"schema": "strata/TelemetryPipeOpen/1", "challenge": self.descriptor["challenge"]},
                    "TELEMETRY_PIPE_OPEN")
            self.pipe.send(canonical(self.settings))
            self._record("CONFIGURED", configuration_sent=True)
            key = private_read(self.authority.key_file, 32)
            require(len(key) == 32 and hashlib.sha256(key).hexdigest() == self.authority.key_sha256,
                    "TELEMETRY_AUTH_KEY_CHANGED")
            while True:
                raw = self.pipe.receive(MAX_RECORD)
                value = strict_json(raw)
                if isinstance(value, dict) and value.get("schema") == "strata/TelemetryPipeFinish/1":
                    require(value == {"schema": "strata/TelemetryPipeFinish/1", "sequence": self.count}
                            and type(value.get("sequence")) is int
                            and self.stopped and self.output is not None, "TELEMETRY_PIPE_INCOMPLETE")
                    self._record("STOPPED")
                    self.pipe.send(canonical({"schema": "strata/TelemetryPipeClosed/1", "sequence": self.count}))
                    break
                self._event(raw, identity, key)
        except BaseException as error:
            observation = ({"process_observation": error.observation()}
                           if isinstance(error, ProcessInventoryFault) else {})
            self._record("UNCERTAIN", error=getattr(error, "code", type(error).__name__), **observation)
        finally:
            if self.output is not None:
                self.output.close()
            key = b""  # Python cannot promise memory zeroization.
            self.pipe.close()

    def close(self):
        self.thread.join(2)
        if self.thread.is_alive():
            self.closing.set()
            self.armed.set()  # Wake a connected peer awaiting ownership, never authorize it.
            self.pipe.close()
            self.thread.join(2)
        require(not self.thread.is_alive(), "TELEMETRY_PIPE_CLOSE_UNCONFIRMED")
        return dict(self.body)
