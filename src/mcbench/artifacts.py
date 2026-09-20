"""Learned revision activation and explicit episode artifact policies."""

import json

from .records import SkillRevision
from .storage import CAS, Database, Principal, canonical, digest, require


class Artifacts:
    def __init__(self, database: Database, cas: CAS):
        self.database, self.cas = database, cas
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS revisions (id TEXT PRIMARY KEY, namespace TEXT, "
                       "agent TEXT, kind TEXT, body TEXT, digest TEXT, active INTEGER)")

    def publish(self, principal: Principal, revision: SkillRevision, *, at_boundary: bool):
        require(principal.role == "executor", "FORBIDDEN")
        require(principal.namespace.endswith(":agent:" + revision.agent_id), "FORBIDDEN")
        require(not revision.is_example and revision.status == "active" and at_boundary,
                "ACTIVATION_BOUNDARY_REQUIRED")
        require(revision.kind != "initial" and revision.origin != "initial", "INITIAL_IMMUTABLE")
        require(not revision.origin == "probe" or principal.namespace.startswith("probe:"),
                "PROBE_IMPORT_FORBIDDEN")
        require(not principal.namespace.startswith("probe:") or revision.origin == "probe",
                "PROBE_ORIGIN_REQUIRED")
        data = self.cas.read(principal, principal.namespace, revision.content)
        require(len(data) <= (8000 if revision.kind == "handoff" else 256 * 1024), "ARTIFACT_QUOTA")
        for ref in revision.provenance_refs:
            self.cas.read(principal, principal.namespace, ref)
        require(revision.provenance_refs and revision.generating_call_ids, "PROVENANCE_REQUIRED")
        body = revision.model_dump()
        with self.database.transaction() as db:
            old = db.execute("SELECT * FROM revisions WHERE id=?", (revision.revision_id,)).fetchone()
            if old:
                require(old["namespace"] == principal.namespace and old["digest"] == digest(body),
                        "IDEMPOTENCY_CONFLICT")
                return
            active = db.execute("SELECT id FROM revisions WHERE namespace=? AND agent=? AND kind=? "
                                "AND active=1", (principal.namespace, revision.agent_id, revision.kind))
            active = active.fetchone()
            require(revision.parent_revision_id == (active[0] if active else None), "REVISION_CONFLICT")
            db.execute("UPDATE revisions SET active=0 WHERE namespace=? AND agent=? AND kind=?",
                       (principal.namespace, revision.agent_id, revision.kind))
            db.execute("INSERT INTO revisions VALUES (?,?,?,?,?,?,1)", (revision.revision_id,
                       principal.namespace, revision.agent_id, revision.kind, canonical(body).decode(),
                       digest(body)))
            self.database.event(db, "skill.activated", {"namespace": principal.namespace, "record": body})

    def active(self, principal):
        require(principal.role in {"executor", "helper"}, "FORBIDDEN")
        return [json.loads(row[0]) for row in self.database.connection.execute(
            "SELECT body FROM revisions WHERE namespace=? AND active=1 ORDER BY id",
            (principal.namespace,))]


def episode_projection(arm: str, initial: dict, current: dict):
    """Return exact next-episode state; initial artifacts are immutable CAS refs.

    A session never survives an episode boundary. The backend cache persists with
    the training world and is reset separately for matched probes.
    """
    fields = {"notes", "procedures", "executables", "handoff", "session", "runtime_cache"}
    require(set(initial) == fields and set(current) == fields, "ARTIFACT_FIELDS")
    require(arm in {"full", "frozen-persistence", "frozen-skills", "no-self-play"}, "ARM_UNKNOWN")
    if arm == "frozen-persistence":
        result = dict(initial)
    elif arm == "frozen-skills":
        result = dict(initial) | {"notes": current["notes"], "handoff": current["handoff"]}
    else:
        result = dict(current)
    result["session"] = None
    result["runtime_cache"] = None
    return result
