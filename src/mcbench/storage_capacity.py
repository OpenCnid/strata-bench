"""Finite private receipt capacity, reserved before a provider dispatch.

Reservations survive crashes. Only the owning operator transport consumes or
releases them; there is no expiry or implicit reclamation of unknown work.
"""

import shutil

from .storage import require

AGENT_QUOTA = 20 * 1024**2
OPERATOR_QUOTA = 128 * 1024**2
DISK_MARGIN = 64 * 1024**2
POLICY = "operator-receipt-capacity/1"


def quota(principal, namespace, visibility):
    return (OPERATOR_QUOTA if principal.role == "operator" and namespace == "operator" and
            visibility == "operator" else AGENT_QUOTA)


def held(db, namespace, excluding=None):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='artifact_reservations'").fetchone():
        return 0
    return db.execute("SELECT COALESCE(SUM(bytes),0) FROM artifact_reservations "
        "WHERE namespace=? AND state='RESERVED' AND token!=?", (namespace, excluding or "")).fetchone()[0]


def available(db, root, namespace, required, limit):
    require(type(required) is int and 0 < required <= limit, "INVALID_QUOTA")
    used = db.execute("SELECT COALESCE(SUM(bytes),0) FROM objects WHERE namespace=?", (namespace,)).fetchone()[0]
    pending = held(db, namespace)
    require(used + pending + required <= limit, "ARTIFACT_CAPACITY")
    # Logical reservation protects cooperating CAS writers; unexpected external
    # disk exhaustion remains a typed failed write, never proof of durability.
    total_held = (db.execute("SELECT COALESCE(SUM(bytes),0) FROM artifact_reservations "
        "WHERE state='RESERVED'").fetchone()[0] if
        db.execute("SELECT 1 FROM sqlite_master WHERE name='artifact_reservations'").fetchone() else 0)
    require(shutil.disk_usage(root).free >= total_held + required + DISK_MARGIN, "ARTIFACT_DISK_CAPACITY")
    return {"policy": POLICY, "namespace": namespace, "quota_bytes": limit,
            "used_bytes": used, "reserved_bytes": pending, "required_bytes": required}


def reserve(cas, principal, namespace, token, size):
    require(principal.role == "operator" and isinstance(token, str) and 0 < len(token) <= 128, "FORBIDDEN")
    with cas.database.transaction() as db:
        db.execute("CREATE TABLE IF NOT EXISTS artifact_reservations (namespace TEXT, token TEXT, "
            "bytes INTEGER NOT NULL, state TEXT NOT NULL, ref TEXT, PRIMARY KEY(namespace,token))")
        require(db.execute("SELECT 1 FROM artifact_reservations WHERE namespace=? AND token=?",
                           (namespace, token)).fetchone() is None, "ARTIFACT_RESERVATION_USED")
        proof = available(db, cas.root, namespace, size, quota(principal, namespace, "operator"))
        db.execute("INSERT INTO artifact_reservations VALUES(?,?,?,'RESERVED',NULL)", (namespace, token, size))
        cas.database.event(db, "artifact.capacity_reserved", proof | {"token": token})


def release(cas, namespace, token):
    with cas.database.transaction() as db:
        changed = db.execute("UPDATE artifact_reservations SET state='RELEASED' "
            "WHERE namespace=? AND token=? AND state='RESERVED'", (namespace, token)).rowcount
        if changed:
            cas.database.event(db, "artifact.capacity_released", {"namespace": namespace, "token": token})


def consume(db, principal, namespace, token, size, ref):
    require(principal.role == "operator", "FORBIDDEN")
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='artifact_reservations'").fetchone(),
            "ARTIFACT_RESERVATION_INVALID")
    row = db.execute("SELECT * FROM artifact_reservations WHERE namespace=? AND token=?",
                     (namespace, token)).fetchone()
    require(row is not None and row["state"] == "RESERVED" and size <= row["bytes"],
            "ARTIFACT_RESERVATION_INVALID")
    db.execute("UPDATE artifact_reservations SET state='CONSUMED',ref=? WHERE namespace=? AND token=?",
               (ref, namespace, token))
