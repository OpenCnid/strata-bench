"""Private live-server identity and registered-roster joins for callback clocks.

This is a source binding, not campaign admission or a repair-time certificate.
No process is discovered or adopted here; only the launch owner's held handle
and durable authenticated pipe state can supply a source.
"""

import hashlib
import sqlite3
import time

from mcbench.inference_transport import strict_json
from mcbench.storage import digest, require
from .craft_reference import parse_plan
from .live_clocks import clock_prefix
from .reference_launch import bind_identity, parse_launch_plan
from .telemetry import LaunchIdentity
from .telemetry_pipe import TelemetryPipeBroker


class BoundClockSource:
    def __init__(self, broker):
        require(isinstance(broker, TelemetryPipeBroker), "CLOCK_SOURCE_REQUIRED")
        self.broker = broker
        self.plan = parse_launch_plan(broker.plan.model_dump())
        self.setup = parse_plan(broker.setup.model_dump())
        require(self.plan.instance_id == self.setup.instance_id == broker.authority.instance_id
                and self.plan.setup_digest == digest(self.setup.model_dump())
                and getattr(broker.authority, "setup_digest", None) == self.plan.setup_digest
                and self.setup.campaign_id == broker.authority.campaign_id
                and self.setup.epoch == broker.authority.epoch, "CLOCK_SOURCE_SETUP")
        self.source_identity = {"authority_digest": broker.authority.fingerprint(),
            "launch_plan_digest": digest(self.plan.model_dump()), "setup_digest": self.plan.setup_digest}

    def _live(self, cursor):
        b = self.broker
        require(b.job is not None and b.thread.is_alive() and not b.closing.is_set()
                and time.monotonic() < b.deadline, "CLOCK_SOURCE_NOT_LIVE")
        require(digest(b.plan.model_dump()) == self.source_identity["launch_plan_digest"]
                and digest(b.setup.model_dump()) == self.source_identity["setup_digest"]
                and b.authority.fingerprint() == self.source_identity["authority_digest"], "CLOCK_SOURCE_CHANGED")
        # The pipe commits this state only after fsync; its in-memory counters
        # alone do not certify a durable prefix. Use a WAL-aware read-only view.
        with sqlite3.connect(b.database_path.as_uri() + "?mode=ro", uri=True) as db:
            row = db.execute("SELECT state,body FROM telemetry_pipe_boots WHERE authority=?",
                             (self.source_identity["authority_digest"],)).fetchone()
        require(row is not None and row[0] == "DURABLE", "CLOCK_SOURCE_NOT_LIVE")
        require(len(row[1]) <= 65536, "CLOCK_SOURCE_RECORD_SIZE")
        body = strict_json(row[1])
        require(type(body.get("records")) is int and cursor <= body["records"]
                and body.get("server_boot_id") == b.boot, "CLOCK_SOURCE_CURSOR")
        binding = body["binding"]
        observed = LaunchIdentity.model_validate(binding["native_observation"])
        require(observed.pid in b.job.members, "CLOCK_SOURCE_PROCESS")
        require(b.job.kernel.WaitForSingleObject(b.job.members[observed.pid], 0) == 258,
                "CLOCK_SOURCE_PROCESS")
        identity = b.job.member_identity(observed.pid)
        expected = bind_identity(self.plan, self.setup, observed, identity)
        require(expected == binding and body.get("peer") == identity, "CLOCK_SOURCE_PROCESS")
        return body, binding

    def observe(self, cursor):
        require(type(cursor) is int and 1 <= cursor <= 1_000_000, "CLOCK_PREFIX_CURSOR")
        body, binding = self._live(cursor)
        b = self.broker
        prefix = clock_prefix(b.spool / (b.boot + ".authenticated.jsonl"), b.authority, cursor,
                              expected_launch=binding["native_observation"])
        after, after_binding = self._live(cursor)
        require(after_binding == binding and after["server_boot_id"] == body["server_boot_id"]
                and prefix["server_boot_id"] == body["server_boot_id"], "CLOCK_SOURCE_CHANGED")
        require(set(prefix["clock"]["avatar_tick_events"]) <= set(self.setup.roster.values()),
                "CLOCK_SOURCE_FOREIGN_AVATAR")
        # This source profile is local, numeric IPv4 loopback. Menu aliases or
        # other endpoints need their own explicit binding, never guessed ones.
        endpoint = f"127.0.0.1:{self.plan.server_port}"
        fingerprints = {agent: hashlib.sha256((endpoint + "\n" + actor).encode()).hexdigest()
                        for agent, actor in self.setup.roster.items()}
        identity = self.source_identity | {"server_boot_id": prefix["server_boot_id"]}
        return {"schema": "strata/BoundServerClock/1", "is_example": self.plan.mode == "synthetic-fixture",
            "source_binding": digest(identity), **identity, "prefix": prefix,
            "launch_binding": binding, "roster": dict(self.setup.roster),
            "body_fingerprints": fingerprints, "body_binding_policy": "numeric-loopback-player-sha256/1",
            "process_isolation_qualified": False, "complete_repair_accounting": False}
