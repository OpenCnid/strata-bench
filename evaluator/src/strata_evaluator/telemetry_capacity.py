"""Prior finite spool capacity; logical reservations cover this private database.

This does not reserve OS disk extents or unrelated logs/database/fixture storage.
External disk exhaustion remains a failed write. Unknown work retains its hold.
"""

import os
from pathlib import Path
import shutil
from typing import Literal

from pydantic import Field

from mcbench.contracts import Strict
from mcbench.storage import digest, require

POLICY = "private-reference-telemetry-capacity/1"
DISK_MARGIN = 64 * 1024**2
LEGACY_LIMITS = {"max_bytes": 8388608, "max_events": 2000}


class TelemetryCapacity(Strict):
    policy: Literal["private-reference-telemetry-capacity/1"]
    # Bytes count complete authenticated wire records, including base64/MAC.
    max_bytes: int = Field(ge=65536, le=1024**3)
    max_events: int = Field(ge=1, le=1000000)


def limits(plan):
    capacity = getattr(plan, "telemetry_capacity", None)
    return capacity.model_dump(exclude={"policy"}) if capacity is not None else dict(LEGACY_LIMITS)


def reserve(database, db, instance, launch_digest, capacity, root):
    """Called in the same transaction as dispatch intent, before native launch."""
    root = Path(root).resolve(strict=True)
    require(root.is_dir(), "TELEMETRY_STORAGE_ROOT")
    volume = str(os.stat(root).st_dev)
    db.execute("CREATE TABLE IF NOT EXISTS reference_telemetry_capacity ("
               "instance TEXT PRIMARY KEY, launch_digest TEXT NOT NULL, capacity_digest TEXT NOT NULL, "
               "volume TEXT NOT NULL, bytes INTEGER NOT NULL, state TEXT NOT NULL, actual_bytes INTEGER)")
    require(db.execute("SELECT 1 FROM reference_telemetry_capacity WHERE instance=?", (instance,)).fetchone()
            is None, "TELEMETRY_STORAGE_ALREADY_RESERVED")
    pending = db.execute("SELECT COALESCE(SUM(bytes),0) FROM reference_telemetry_capacity "
                         "WHERE volume=? AND state='RESERVED'", (volume,)).fetchone()[0]
    require(shutil.disk_usage(root).free >= pending + capacity.max_bytes + DISK_MARGIN,
            "TELEMETRY_STORAGE_DISK_LOW")
    capacity_digest = digest(capacity.model_dump())
    db.execute("INSERT INTO reference_telemetry_capacity VALUES(?,?,?,?,?,'RESERVED',NULL)",
               (instance, launch_digest, capacity_digest, volume, capacity.max_bytes))
    proof = {"policy": POLICY, "launch_digest": launch_digest, "capacity_digest": capacity_digest,
             "volume": volume, "reserved_bytes": capacity.max_bytes,
             "other_held_bytes": pending, "state": "RESERVED", "os_extent_reservation": False}
    database.event(db, "private.reference_telemetry_reserved", {"instance": instance, **proof})
    return proof


def consume(database, db, instance, body):
    """Atomic with STOPPED, after complete stream and retained process closure."""
    proof, broker = body["telemetry_capacity"], body.get("broker", {})
    job, held = body.get("job_accounting", {}), body.get("held_members", {})
    require(body.get("status") == "stopped_reference" and broker.get("status") == "stopped"
            and body.get("launch_binding_verified") is True and body.get("stop_sent") is True
            and body.get("forced_stop") is False and body.get("exit_code") == 0
            and job.get("active_processes") == 0 and type(job.get("total_processes")) is int
            and job["total_processes"] > 0
            and held.get("held_processes") == held.get("signaled_processes") == job["total_processes"]
            and type(body.get("records")) is int and body["records"] > 0
            and broker.get("records") == body.get("records")
            and type(broker.get("bytes")) is int, "TELEMETRY_STORAGE_TERMINAL_REQUIRED")
    row = db.execute("SELECT * FROM reference_telemetry_capacity WHERE instance=?", (instance,)).fetchone()
    require(row is not None and row["state"] == "RESERVED"
            and row["launch_digest"] == body["plan_digest"] == proof["launch_digest"]
            and row["capacity_digest"] == proof["capacity_digest"]
            and row["bytes"] == proof["reserved_bytes"]
            and 0 < broker["bytes"] <= row["bytes"], "TELEMETRY_STORAGE_RESERVATION_MISMATCH")
    db.execute("UPDATE reference_telemetry_capacity SET state='CONSUMED',actual_bytes=? WHERE instance=?",
               (broker["bytes"], instance))
    database.event(db, "private.reference_telemetry_consumed", {
        "instance": instance, "launch_digest": body["plan_digest"],
        "actual_bytes": broker["bytes"], "unused_bytes": row["bytes"] - broker["bytes"]})
    return {"state": "CONSUMED", "actual_bytes": broker["bytes"],
            "unused_bytes": row["bytes"] - broker["bytes"]}
