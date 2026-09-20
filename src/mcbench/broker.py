"""Private capability broker for a restricted native MCP profile.

Native transport metadata is trusted only over the owned stdio connection in a
qualified tool-restricted runtime. Nothing here makes an arbitrary HTTP caller,
metadata dictionary, or unqualified native profile trustworthy. Admission and
projection methods are operator-only and are never exposed as tools.
"""

import json
import time
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from .contracts import Digest, Id, Positive, Ref, RpcRequest, Strict, UInt
from .budgets import Budgets
from .runtime import CODEX_VERSION
from .storage import Fault, Principal, canonical, digest, require, safe_relative

POLICY = "native-stdio-projected-artifacts-executor-game/1"
NATIVE_METADATA_VERSION = CODEX_VERSION.removeprefix("codex-cli ")
MAX_TEXT = 256 * 1024


class BrokerGrant(Strict):
    schema_: Literal["strata/NativeBrokerGrant/1"] = Field(alias="schema")
    runtime_id: Id
    session_id: Id
    thread_id: Id
    parent_thread_id: Id | None
    profile_digest: Digest
    model: str
    role: Literal["executor", "helper"]
    namespace: Id
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    depth: UInt = Field(le=2)
    expires_unix_ms: Positive
    tool_calls: Positive = Field(le=10000)
    # The enrollment caller must first admit the model job/child reservation.
    admission_ref: Ref


class ArtifactRead(Strict):
    path: Annotated[str, Field(min_length=1, max_length=256)]


class ArtifactWrite(ArtifactRead):
    text: Annotated[str, Field(max_length=MAX_TEXT)]
    expected_ref: Ref | None


class Empty(Strict):
    pass


class GameCall(Strict):
    request: RpcRequest


ARGUMENTS = {"artifact_read": ArtifactRead, "artifact_write": ArtifactWrite,
             "artifact_list": Empty, "game": GameCall}


class NativeBroker:
    def __init__(self, database, cas, runtime_id, profile_digest, *, clock=time.time):
        self.db, self.cas = database, cas
        self.runtime_id, self.profile_digest, self.clock = runtime_id, profile_digest, clock
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS broker_grants (runtime TEXT, thread TEXT, "
                "namespace TEXT UNIQUE, parent TEXT, body TEXT, fingerprint TEXT, "
                "remaining INTEGER, revoked INTEGER DEFAULT 0, PRIMARY KEY(runtime,thread))")
            db.execute("CREATE TABLE IF NOT EXISTS broker_files (namespace TEXT, path TEXT, "
                "ref TEXT, immutable INTEGER, PRIMARY KEY(namespace,path))")
            db.execute("CREATE TABLE IF NOT EXISTS broker_game_calls (runtime TEXT, thread TEXT, "
                "request TEXT, fingerprint TEXT, state TEXT, result TEXT, "
                "PRIMARY KEY(runtime,thread,request))")

    def admit(self, grant: BrokerGrant):
        """Operator enrollment, after job/budget admission; never model-callable."""
        require(grant.runtime_id == self.runtime_id and grant.profile_digest == self.profile_digest,
                "BROKER_SCOPE")
        visibility = self.db.connection.execute("SELECT visibility FROM objects WHERE namespace=? "
            "AND ref=?", ("operator", grant.admission_ref)).fetchone()
        require(visibility is not None and visibility[0] == "operator", "BROKER_ADMISSION_PRIVATE")
        self._admission(self.db.connection, grant, enrolling=True)
        body = grant.model_dump()
        with self.db.transaction() as db:
            old = db.execute("SELECT fingerprint FROM broker_grants WHERE runtime=? AND thread=?",
                (self.runtime_id, grant.thread_id)).fetchone()
            if old:
                require(old[0] == digest(body), "IDEMPOTENCY_CONFLICT")
                return  # Never renew a consumed/revoked grant by replaying admission.
            require(grant.expires_unix_ms > self.clock() * 1000, "BROKER_EXPIRED")
            if grant.role == "executor":
                require(grant.depth == 0 and grant.parent_thread_id is None and
                        grant.thread_id == grant.session_id, "BROKER_LINEAGE")
                require(db.execute("SELECT 1 FROM broker_grants WHERE runtime=? AND parent IS NULL",
                    (self.runtime_id,)).fetchone() is None, "BROKER_EXECUTOR_EXISTS")
            else:
                parent = db.execute("SELECT body,revoked FROM broker_grants WHERE runtime=? "
                    "AND thread=?", (self.runtime_id, grant.parent_thread_id)).fetchone()
                require(parent is not None and not parent["revoked"], "BROKER_LINEAGE")
                p = BrokerGrant.model_validate_json(parent["body"])
                require(grant.depth == p.depth + 1 and grant.expires_unix_ms <= p.expires_unix_ms
                        and all(getattr(grant, k) == getattr(p, k) for k in (
                            "session_id", "campaign_id", "agent_id", "epoch", "model")),
                        "BROKER_LINEAGE")
            require(db.execute("SELECT 1 FROM broker_grants WHERE namespace=?",
                (grant.namespace,)).fetchone() is None, "BROKER_NAMESPACE_REUSED")
            db.execute("INSERT INTO broker_grants VALUES(?,?,?,?,?,?,?,0)", (
                self.runtime_id, grant.thread_id, grant.namespace, grant.parent_thread_id,
                canonical(body).decode(), digest(body), grant.tool_calls))
            self.db.event(db, "broker.admitted", {"policy": POLICY, "grant": body})

    def _grant(self, db, thread):
        row = db.execute("SELECT * FROM broker_grants WHERE runtime=? AND thread=?",
            (self.runtime_id, thread)).fetchone()
        require(row is not None and not row["revoked"], "BROKER_FORBIDDEN")
        g = BrokerGrant.model_validate_json(row["body"])
        require(g.profile_digest == self.profile_digest and
                g.expires_unix_ms > self.clock() * 1000, "BROKER_EXPIRED")
        self._admission(db, g)
        if g.parent_thread_id is not None:
            self._grant(db, g.parent_thread_id)  # Revocation/expiry flows to descendants.
        return g, row

    def _admission(self, db, grant, *, enrolling=False):
        evidence = json.loads(self.cas.read(Principal("operator", "operator"), "operator",
                                           grant.admission_ref, max_bytes=65536))
        if evidence.get("schema") != "strata/NativeBrokerAdmission/1":
            table = db.execute("SELECT 1 FROM sqlite_master WHERE name='native_profile'").fetchone()
            require(evidence.get("is_example") is True and table is not None and
                    db.execute("SELECT simulation FROM native_profile").fetchone()[0] == 1,
                    "BROKER_RUNTIME_ADMISSION_REQUIRED")
            return  # Historical fixture enrollment is explicitly simulation-only.
        require(evidence.get("job") == grant.runtime_id and evidence.get("thread") == grant.thread_id
                and evidence.get("profile_digest") == grant.profile_digest, "BROKER_ADMISSION_MISMATCH")
        require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_request_admissions'").fetchone(),
                "BROKER_RUNTIME_ADMISSION_REQUIRED")
        row = db.execute("SELECT a.*,p.parent,p.depth,p.state participant_state,j.state job_state,j.plan,j.started "
            "FROM native_request_admissions a JOIN native_participants p ON a.job=p.job AND a.thread=p.thread "
            "JOIN native_jobs j ON a.job=j.id WHERE a.operation=?", (evidence.get("operation_id"),)).fetchone()
        require(row is not None and row["job"] == grant.runtime_id and row["thread"] == grant.thread_id
                and row["job_state"] == "RUNNING" and row["participant_state"] == "ACTIVE" and
                row["parent"] == grant.parent_thread_id and row["depth"] == grant.depth and
                row["envelope"] == evidence.get("envelope") and
                row["request_digest"] == evidence.get("request_digest"), "BROKER_RUNTIME_REVOKED")
        from .native import NativeLaunch
        plan = NativeLaunch.model_validate_json(row["plan"])
        require(plan.profile_digest() == grant.profile_digest and plan.broker_policy == POLICY and
                all(getattr(plan, k) == getattr(grant, k)
                for k in ("campaign_id", "agent_id", "epoch", "model")) and
                grant.role == ("executor" if row["depth"] == 0 else "helper"), "BROKER_ADMISSION_MISMATCH")
        require(grant.expires_unix_ms <= int((row["started"] + plan.hard_timeout_s) * 1000),
                "BROKER_ADMISSION_MISMATCH")
        root = db.execute("SELECT thread FROM native_participants WHERE job=? AND parent IS NULL",
                          (grant.runtime_id,)).fetchone()
        require(root is not None and root[0] == grant.session_id, "BROKER_ADMISSION_MISMATCH")
        operation = db.execute("SELECT actual,uncertain FROM operations WHERE id=? AND account=?",
                               (row["envelope"], row["account"])).fetchone()
        require(operation is not None and operation["actual"] is None and not operation["uncertain"],
                "BROKER_RUNTIME_REVOKED")
        _, uncertain = Budgets.totals(db, row["account"])
        require(not uncertain, "BROKER_BUDGET_UNCERTAIN")
        require(db.execute("SELECT 1 FROM inference_exposure_faults LIMIT 1").fetchone() is None,
                "BROKER_EXPOSURE_QUARANTINED")
        if enrolling:
            dispatch = db.execute("SELECT state FROM inference_attempts WHERE operation=?",
                                  (row["operation"],)).fetchone()
            require(dispatch is not None and dispatch[0] == "DISPATCHING", "BROKER_DISPATCH_NOT_ADMITTED")

    def _authenticate(self, db, meta):
        require(isinstance(meta, dict), "BROKER_FORBIDDEN")
        native = meta.get("x-codex-turn-metadata")
        require(isinstance(native, dict) and isinstance(meta.get("threadId"), str),
                "BROKER_FORBIDDEN")
        g, row = self._grant(db, meta["threadId"])
        require(native.get("thread_id") == g.thread_id and
                native.get("session_id") == g.session_id and
                native.get("parent_thread_id") == g.parent_thread_id and
                native.get("codex_version") == NATIVE_METADATA_VERSION and native.get("model") == g.model and
                native.get("thread_source") == ("user" if g.role == "executor" else "subagent"),
                "BROKER_IDENTITY_MISMATCH")
        if g.role == "helper":
            require(native.get("subagent_kind") == "thread_spawn", "BROKER_IDENTITY_MISMATCH")
        require(isinstance(meta.get("callId"), str) and 0 < len(meta["callId"]) <= 256,
                "BROKER_IDENTITY_MISMATCH")
        require(row["remaining"] > 0, "BROKER_QUOTA")
        db.execute("UPDATE broker_grants SET remaining=remaining-1 WHERE runtime=? AND thread=?",
                   (self.runtime_id, g.thread_id))
        return g

    @staticmethod
    def _path(path):
        safe_relative(path)
        require(len(path) <= 256 and path.isascii(), "UNSAFE_PATH")
        return path

    def project(self, thread, path, text):
        """Copy explicitly admitted public/agent bytes; never resolve a caller path."""
        path = self._path(path)
        g, _ = self._grant(self.db.connection, thread)
        require(path.split("/", 1)[0] in {"initial", "docs", "supplied"}, "BROKER_PROJECTION")
        require(isinstance(text, str), "BROKER_PROJECTION")
        ref = self.cas.put(Principal(g.namespace, "executor"), g.namespace, "agent",
                           text.encode("utf-8"), media_type="text/plain")
        with self.db.transaction() as db:
            row = db.execute("SELECT ref FROM broker_files WHERE namespace=? AND path=?",
                (g.namespace, path)).fetchone()
            require(row is None or row[0] == ref, "INITIAL_IMMUTABLE")
            require(row is not None or db.execute("SELECT count(*) FROM broker_files WHERE namespace=?",
                (g.namespace,)).fetchone()[0] < 1024, "ARTIFACT_QUOTA")
            db.execute("INSERT OR IGNORE INTO broker_files VALUES(?,?,?,1)",
                       (g.namespace, path, ref))

    def revoke(self, thread):
        with self.db.transaction() as db:
            db.execute("UPDATE broker_grants SET revoked=1 WHERE runtime=? AND thread=?",
                       (self.runtime_id, thread))
            self.db.event(db, "broker.revoked", {"runtime": self.runtime_id, "thread": thread})

    def call(self, name, arguments, meta, *, game_transport=None):
        require(name in ARGUMENTS, "BROKER_TOOL_FORBIDDEN")
        value = ARGUMENTS[name].model_validate(arguments)
        # Authenticate before resolving any artifact name or forwarding game data.
        with self.db.transaction() as db:
            g = self._authenticate(db, meta)
            self.db.event(db, "broker.call", {"runtime": self.runtime_id, "thread": g.thread_id,
                "tool": name, "call_id": meta["callId"], "arguments_digest": digest(arguments)})
        if name == "artifact_list":
            return {"files": [dict(r) for r in self.db.connection.execute(
                "SELECT path,ref,immutable FROM broker_files WHERE namespace=? ORDER BY path LIMIT 1024",
                (g.namespace,))]}
        if name in {"artifact_read", "artifact_write"}:
            path = self._path(value.path)
            row = self.db.connection.execute("SELECT ref,immutable FROM broker_files "
                "WHERE namespace=? AND path=?", (g.namespace, path)).fetchone()
            if name == "artifact_read":
                require(row is not None, "BROKER_FORBIDDEN")
                text = self.cas.read(Principal(g.namespace, g.role), g.namespace, row["ref"],
                                     max_bytes=MAX_TEXT).decode("utf-8")
                return {"path": path, "ref": row["ref"], "text": text}
            prefix = path.split("/", 1)[0]
            require(prefix in ({"results"} if g.role == "helper" else {"notes", "skills", "handoff"})
                    and "/" in path and (row is None or not row["immutable"]), "BROKER_WRITE_FORBIDDEN")
            require(len(value.text.encode("utf-8")) <= (8000 if prefix == "handoff" else MAX_TEXT),
                    "ARTIFACT_QUOTA")
            # Service writes only the caller's permitted result/draft namespace.
            # This does not activate a learned revision or mutate initial skills.
            ref = self.cas.put(Principal(g.namespace, "executor"), g.namespace, "agent",
                               value.text.encode("utf-8"), media_type="text/plain")
            with self.db.transaction() as db:
                self._grant(db, g.thread_id)
                old = db.execute("SELECT ref FROM broker_files WHERE namespace=? AND path=?",
                    (g.namespace, path)).fetchone()
                if old is not None and old[0] == ref:
                    return {"path": path, "ref": ref}
                require(value.expected_ref == (old[0] if old else None), "REVISION_CONFLICT")
                require(old is not None or db.execute("SELECT count(*) FROM broker_files "
                    "WHERE namespace=?", (g.namespace,)).fetchone()[0] < 1024, "ARTIFACT_QUOTA")
                db.execute("INSERT INTO broker_files VALUES(?,?,?,0) ON CONFLICT(namespace,path) "
                    "DO UPDATE SET ref=excluded.ref", (g.namespace, path, ref))
            return {"path": path, "ref": ref}
        require(g.role == "executor" and game_transport is not None, "BROKER_GAME_FORBIDDEN")
        r = value.request
        deadline = datetime.fromisoformat(r.deadline_at.replace("Z", "+00:00")).timestamp()
        require(self.clock() < deadline <= self.clock() + 5.25, "DEADLINE_EXCEEDED")
        require(r.campaign_id == g.campaign_id and r.agent_id == g.agent_id and r.epoch == g.epoch,
                "BROKER_SCOPE")
        if r.action:
            require(r.action.campaign_id == g.campaign_id and r.action.agent_id == g.agent_id
                    and r.action.epoch == g.epoch, "BROKER_SCOPE")
        # Durable single forwarding; caller-controlled repeated request IDs cannot
        # replay an ambiguous mutation after a server or native-process restart.
        request = r.model_dump()
        key = (self.runtime_id, g.thread_id, r.request_id)
        with self.db.transaction() as db:
            self._grant(db, g.thread_id)
            old = db.execute("SELECT * FROM broker_game_calls WHERE runtime=? AND thread=? "
                "AND request=?", key).fetchone()
            if old:
                require(old["fingerprint"] == digest(request), "IDEMPOTENCY_CONFLICT")
                return json.loads(old["result"]) if old["result"] is not None else {
                    "status": "unknown", "request_id": r.request_id, "replayed": False}
            db.execute("INSERT INTO broker_game_calls VALUES(?,?,?,?,'DISPATCHING',NULL)",
                       (*key, digest(request)))
        try:
            result = game_transport(r)
            require(len(canonical(result)) <= 131072, "BROKER_RESPONSE_LIMIT")
        except Exception:
            # No raw exception/path/credential text and no transport retry.
            raise Fault("BROKER_GAME_OUTCOME_UNKNOWN") from None
        with self.db.transaction() as db:
            db.execute("UPDATE broker_game_calls SET state='SETTLED',result=? WHERE runtime=? "
                       "AND thread=? AND request=?", (canonical(result).decode(), *key))
        return result
