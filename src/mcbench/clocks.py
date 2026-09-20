"""Durable consumed exposure; supervisor interval IDs survive rollback.

Inputs are measured telemetry intervals, not inferred 20 Hz game time. Missing
intervals must be classified by the supervisor; this service cannot invent them.
"""

import json

from .storage import Database, canonical, digest, require


class Clocks:
    def __init__(self, database: Database):
        self.database = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS clock_intervals (campaign TEXT, id TEXT, "
                       "digest TEXT, body TEXT, PRIMARY KEY(campaign,id))")
            db.execute("CREATE TABLE IF NOT EXISTS clock_repairs (campaign TEXT, interval_id TEXT, "
                       "agent TEXT, repair TEXT, PRIMARY KEY(campaign,interval_id,agent))")

    def record(self, campaign, interval_id, *, elapsed_ms, n, server_stopped, inference_suspended,
               server_ticks, avatar_ticks, disconnected_body_ms, boot_id, uncertainty_ms=0):
        for count in (elapsed_ms, n, server_ticks, avatar_ticks, disconnected_body_ms, uncertainty_ms):
            require(type(count) is int and 0 <= count <= 2**53 - 1, "CLOCK_RANGE")
        require(n > 0 and disconnected_body_ms <= n * elapsed_ms, "CLOCK_RANGE")
        require(type(server_stopped) is bool and type(inference_suspended) is bool, "CLOCK_RANGE")
        require(not server_stopped or server_ticks == avatar_ticks == 0, "CLOCK_INCONSISTENT")
        body = {"elapsed_ms": elapsed_ms,
                "active_ms": 0 if server_stopped and inference_suspended else elapsed_ms,
                "reserved_body_ms": n * (0 if server_stopped and inference_suspended else elapsed_ms),
                "server_ticks": server_ticks, "avatar_ticks": avatar_ticks,
                "disconnected_body_ms": disconnected_body_ms, "boot_id": boot_id,
                "uncertainty_ms": uncertainty_ms}
        with self.database.transaction() as db:
            old = db.execute("SELECT digest FROM clock_intervals WHERE campaign=? AND id=?",
                             (campaign, interval_id)).fetchone()
            if old:
                require(old[0] == digest(body), "IDEMPOTENCY_CONFLICT")
                return
            repairs = []
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='avatar_lanes'").fetchone():
                campaign_row = db.execute("SELECT state,config FROM campaigns WHERE id=?", (campaign,)).fetchone()
                if campaign_row:
                    require(json.loads(campaign_row["config"])["n"] == n, "CLOCK_ROSTER_MISMATCH")
                    repairs = db.execute("SELECT agent,repair FROM avatar_lanes WHERE campaign=? "
                                         "AND repair IS NOT NULL", (campaign,)).fetchall()
                    if repairs and campaign_row["state"] == "RUNNING":
                        require(not (server_stopped and inference_suspended), "REPAIR_EXPOSURE_REQUIRED")
            db.execute("INSERT INTO clock_intervals VALUES (?,?,?,?)",
                       (campaign, interval_id, digest(body), canonical(body).decode()))
            db.executemany("INSERT INTO clock_repairs VALUES (?,?,?,?)",
                           [(campaign, interval_id, item["agent"], item["repair"]) for item in repairs])
            self.database.event(db, "clock.interval", {"campaign": campaign, "id": interval_id, **body})
            if repairs:
                self.database.event(db, "clock.repair_attribution", {"campaign": campaign, "id": interval_id,
                    "repairs": [dict(item) for item in repairs], "basis": "hold_active_at_interval_ingestion"})

    def totals(self, campaign):
        keys = ("elapsed_ms", "active_ms", "reserved_body_ms", "server_ticks", "avatar_ticks",
                "disconnected_body_ms", "uncertainty_ms")
        totals = dict.fromkeys(keys, 0)
        for row in self.database.connection.execute("SELECT body FROM clock_intervals WHERE campaign=?",
                                                    (campaign,)):
            body = json.loads(row[0])
            for key in keys:
                totals[key] += body[key]
        return totals
