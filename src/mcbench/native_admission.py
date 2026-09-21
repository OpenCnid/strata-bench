"""Native request/participant admission for a protected inference ingress.

Only the trusted ingress calls this service. Request metadata alone is not
authentication on a public socket. The selected runtime must already enforce
its tool/transport boundary; native stdout independently binds the root identity.
"""

import base64
import json
import re
import time
from pathlib import Path
from xml.etree import ElementTree

from .broker import BrokerGrant, NativeBroker, POLICY
from .budgets import Budgets
from .inference_transport import strict_json
from .native import NativeLaunch
from .native_broker_policy import validate_broker_settings
from .runtime import CODEX_VERSION, DOVETAIL_COMMIT
from .storage import Fault, Principal, canonical, digest, require


def context_metadata(body):
    require(isinstance(body, dict) and isinstance(body.get("client_metadata"), dict),
            "NATIVE_METADATA_REQUIRED")
    raw = body["client_metadata"].get("x-codex-turn-metadata")
    require(isinstance(raw, str) and len(raw) <= 16384, "NATIVE_METADATA_REQUIRED")
    meta = strict_json(raw)
    require(isinstance(meta, dict) and all(isinstance(meta.get(k), str) and
        re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", meta[k]) for k in (
            "session_id", "thread_id", "turn_id")), "NATIVE_METADATA_REQUIRED")
    require(isinstance(meta.get("agent_name"), str) and re.fullmatch(
        r"/root(?:/[a-z0-9_]{1,64}){0,2}", meta["agent_name"]), "NATIVE_LINEAGE")
    return meta


def require_clean_child(body, meta, workspace, parent_name):
    """Pinned initial native request shape; fail closed on inherited conversation."""
    require(not body.get("previous_response_id") and not body.get("conversation"),
            "HELPER_CONTEXT_INHERITED")
    items = body.get("input")
    require(isinstance(items, list) and len(items) <= 64, "HELPER_CONTEXT_INHERITED")
    users, tasks = [], []
    for item in items:
        require(isinstance(item, dict), "HELPER_CONTEXT_INHERITED")
        if item.get("role") == "developer" and item.get("type") in {"message", "additional_tools"}:
            continue  # Native instruction/tool projection is a separately pinned profile.
        if item.get("type") == "message" and item.get("role") == "user":
            users.append(item)
        elif item.get("type") == "agent_message":
            tasks.append(item)
        else:
            require(False, "HELPER_CONTEXT_INHERITED")
    require(len(users) == 1 and len(tasks) == 1, "HELPER_CONTEXT_INHERITED")
    content = users[0].get("content")
    require(isinstance(content, list) and len(content) == 1 and isinstance(content[0], dict) and
            content[0].get("type") == "input_text", "HELPER_CONTEXT_INHERITED")
    text = content[0].get("text")
    require(isinstance(text, str) and len(text) <= 16384 and "<!" not in text,
            "HELPER_CONTEXT_INHERITED")
    try:
        environment = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        require(False, "HELPER_CONTEXT_INHERITED")
    require(environment.tag == "environment_context" and not environment.attrib and
            not (environment.text or "").strip() and
            [e.tag for e in environment] == ["cwd", "shell", "current_date", "timezone", "filesystem"]
            and environment.findtext("cwd") == str(Path(workspace)) and
            all(not (e.tail or "").strip() for e in environment), "HELPER_CONTEXT_INHERITED")
    leaves = list(environment)[:4]
    require(all(not e.attrib and len(e) == 0 for e in leaves) and
            environment.findtext("shell") == "powershell" and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", environment.findtext("current_date") or "") and
            re.fullmatch(r"[A-Za-z_]+(?:/[A-Za-z_+-]+){0,2}",
                         environment.findtext("timezone") or ""), "HELPER_CONTEXT_INHERITED")
    def shape(element):
        return (element.tag, element.attrib, (element.text or "").strip(),
                tuple(shape(child) for child in element), (element.tail or "").strip())
    expected = ElementTree.fromstring('<filesystem><workspace_roots><root /></workspace_roots>'
        '<permission_profile type="managed"><file_system type="restricted">'
        '<entry access="read"><special>:root</special></entry></file_system>'
        '</permission_profile></filesystem>')
    expected.find("workspace_roots/root").text = str(Path(workspace))
    require(shape(environment.find("filesystem")) == shape(expected), "HELPER_CONTEXT_INHERITED")
    task = tasks[0]
    require(task.get("author") == parent_name and task.get("recipient") == meta["agent_name"],
            "HELPER_CONTEXT_INHERITED")
    parts = task.get("content")
    require(isinstance(parts, list) and len(parts) == 2 and parts[0] == {
        "type": "input_text", "text": "Message Type: NEW_TASK\nTask name: " + meta["agent_name"] +
        "\nSender: " + parent_name + "\nPayload:\n"}, "HELPER_CONTEXT_INHERITED")
    payload = parts[1]
    require(isinstance(payload, dict), "HELPER_CONTEXT_INHERITED")
    key = "encrypted_content" if payload.get("type") == "encrypted_content" else "text"
    require(payload.get("type") in {"encrypted_content", "input_text"} and
            set(payload) == {"type", key} and isinstance(payload[key], str) and
            0 < len(payload[key].encode("utf-8")) <= 32000, "HELPER_CONTEXT_INHERITED")


class NativeAdmission:
    def __init__(self, database, cas, *, clock=time.time):
        self.db, self.cas, self.clock = database, cas, clock
        self.budgets = Budgets(database)
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_participants (job TEXT, thread TEXT, "
                "name TEXT, parent TEXT, depth INTEGER, envelope TEXT, initial_context TEXT, "
                "state TEXT, PRIMARY KEY(job,thread), UNIQUE(job,name))")
            db.execute("CREATE TABLE IF NOT EXISTS native_request_admissions (operation TEXT PRIMARY KEY, "
                "job TEXT, thread TEXT, request_digest TEXT, raw_ref TEXT, envelope TEXT, account TEXT, "
                "reservation_digest TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS native_participant_retirements (job TEXT, thread TEXT, "
                "fence_ordinal INTEGER NOT NULL, proof_ref TEXT, PRIMARY KEY(job,thread))")
            db.execute("CREATE TABLE IF NOT EXISTS native_tool_call_ids (job TEXT, thread TEXT, call_id TEXT, "
                "first_ordinal INTEGER NOT NULL, PRIMARY KEY(job,thread,call_id))")
            db.execute("CREATE TABLE IF NOT EXISTS native_tool_call_indexed_requests "
                "(operation TEXT PRIMARY KEY,raw_ref TEXT NOT NULL)")

    @staticmethod
    def child_envelope_id(job, thread):
        return "child:" + digest({"job": job, "thread": thread})

    def _plan(self, db, job):
        row = db.execute("SELECT plan,state,started FROM native_jobs WHERE id=?", (job,)).fetchone()
        require(row is not None and row["state"] == "RUNNING", "RUNTIME_NOT_RUNNING")
        plan = NativeLaunch.model_validate_json(row["plan"])
        mode = db.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()
        require(mode is not None and mode[0] in (0, 1), "NATIVE_ADMISSION_PROFILE")
        if mode[0] == 0:
            # Also fence a legacy job already running when the controller was
            # upgraded; live startup/dispatch checks alone are too late for its
            # first new helper envelope.
            require(plan.tool_projection_ref is not None, "NATIVE_TOOL_PROJECTION_REQUIRED")
            require(plan.tool_catalog_policy is not None, "NATIVE_TOOL_CATALOG_REQUIRED")
        require(row["started"] + plan.hard_timeout_s > self.clock(), "RUNTIME_EXPIRED")
        require(plan.broker_policy == POLICY and plan.binary_version == CODEX_VERSION and
                plan.dovetail_commit == DOVETAIL_COMMIT and plan.role == "executor" and
                plan.budget_mode == "per_dispatch", "NATIVE_ADMISSION_PROFILE")
        validate_broker_settings(plan.config_overrides)
        if plan.bootstrap_digest is not None:
            from .native_bootstrap import verify_native_inventory
            verify_native_inventory(plan)
        if plan.tool_catalog_policy is not None:
            from .native_catalog import require_no_patch_catalog
            require_no_patch_catalog(plan)
        return plan

    @staticmethod
    def _root_thread(db, job):
        found = []
        for row in db.execute("SELECT body FROM native_events WHERE job=? AND channel='stdout' "
                              "ORDER BY cursor LIMIT 128", (job,)):
            event = strict_json(base64.b64decode(json.loads(row[0])["raw_base64"]))
            if event.get("type") == "thread.started":
                found.append(event.get("thread_id"))
        require(len(found) == 1 and isinstance(found[0], str), "NATIVE_ROOT_EVENT_REQUIRED")
        return found[0]

    def wait_for_root(self, job, *, timeout_s=2):
        """Bounded ingress wait for independently journaled native stdout identity."""
        require(0 < timeout_s <= 3, "NATIVE_IDENTITY_WAIT_BOUND")
        deadline = time.monotonic() + timeout_s
        while True:
            row = self.db.connection.execute("SELECT state FROM native_jobs WHERE id=?", (job,)).fetchone()
            require(row is not None and row[0] == "RUNNING", "RUNTIME_NOT_RUNNING")
            try:
                return self._root_thread(self.db.connection, job)
            except Fault as error:
                if error.code != "NATIVE_ROOT_EVENT_REQUIRED" or time.monotonic() >= deadline:
                    raise
            time.sleep(min(0.01, max(0, deadline - time.monotonic())))

    def prepare(self, account, attempt, reserve, raw, *, child_envelope=None):
        """Before dispatch: validate caller/context and reserve a child sub-envelope.

        No provider call is made here. The normal dispatch gate still atomically
        reserves each distinct request. Failed/ambiguous requests keep their holds.
        """
        import hashlib
        require(isinstance(raw, bytes) and len(raw) <= 1024 * 1024 and
                hashlib.sha256(raw).hexdigest() == attempt.request_digest, "REQUEST_DIGEST_MISMATCH")
        body = strict_json(raw)
        meta = context_metadata(body)
        raw_ref = self.cas.put(Principal("operator", "operator"), "operator", "operator", raw,
                               max_object_bytes=1024 * 1024)
        with self.db.transaction() as db:
            plan = self._plan(db, attempt.runtime_job_id)
            if plan.ingress_policy is not None:
                from .native_ingress import require_ingress_request
                require_ingress_request(db, plan, reserve.operation_id, attempt.request_digest)
            require(plan.profile_digest() == attempt.profile_digest and plan.account == account and
                    plan.campaign_id == reserve.campaign_id and plan.agent_id == reserve.agent_id and
                    plan.epoch == reserve.epoch and body.get("model") == plan.model == reserve.model_identity,
                    "NATIVE_ADMISSION_SCOPE")
            root = self._root_thread(db, plan.job_id)
            require(meta["session_id"] == root, "NATIVE_LINEAGE")
            thread, name = meta["thread_id"], meta["agent_name"]
            if plan.skill_activation_ref is not None:
                from .native_skill_activation import require_catalog
                require_catalog(db, self.cas, plan, body, "executor" if name == "/root" else "helper")
            # No helper envelope or participant is created until the complete
            # request tool projection matches the pre-existing operator pin.
            # Lineage checks below independently authenticate the claimed role.
            projection_digest = None
            if plan.tool_projection_ref is not None:
                from .native_tool_projection import require_tool_projection
                projection_digest = require_tool_projection(self.cas, plan, body,
                    "executor" if name == "/root" else "helper")
            participant = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?",
                (plan.job_id, thread)).fetchone()
            if participant is None:
                if name == "/root":
                    require(thread == root and meta.get("parent_thread_id") is None and
                            meta.get("thread_source") == "user" and child_envelope is None,
                            "NATIVE_LINEAGE")
                    parent, depth, envelope = None, 0, plan.operation_id
                else:
                    require(db.execute("SELECT 1 FROM native_participants WHERE job=? AND name=?",
                                       (plan.job_id, name)).fetchone() is None, "NATIVE_PARTICIPANT_NAME_REUSED")
                    parent = meta.get("parent_thread_id")
                    p = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?",
                        (plan.job_id, parent)).fetchone()
                    require(p is not None and p["state"] == "ACTIVE" and
                            name.rsplit("/", 1)[0] == p["name"] and meta.get("thread_source") == "subagent"
                            and meta.get("subagent_kind") == "thread_spawn", "NATIVE_LINEAGE")
                    depth = p["depth"] + 1
                    require(depth <= 2, "HELPER_DEPTH")
                    require_clean_child(body, meta, plan.workspace, p["name"])
                    count = db.execute("SELECT count(*) FROM native_participants WHERE job=? "
                        "AND depth>0 AND state IS NOT 'CLOSED'", (plan.job_id,)).fetchone()[0]
                    require(count < plan.helper_limit, "HELPER_CAPACITY")
                    envelope = self.child_envelope_id(plan.job_id, thread)
                    require(child_envelope is not None and child_envelope.posting == "reserve" and
                            child_envelope.operation_id == envelope and child_envelope.kind == "helper"
                            and child_envelope.parent_operation_id == p["envelope"] and all(
                                getattr(child_envelope, k) == getattr(reserve, k) for k in (
                                    "campaign_id", "agent_id", "campaign_account", "epoch", "model_identity")),
                            "CHILD_BUDGET_REQUIRED")
                    self.budgets.post_in_transaction(db, account, child_envelope, envelope=True)
                op = db.execute("SELECT actual,uncertain FROM operations WHERE id=? AND account=?",
                    (envelope, account)).fetchone()
                require(op is not None and op["actual"] is None and not op["uncertain"], "ENVELOPE_CLOSED")
                db.execute("INSERT INTO native_participants VALUES(?,?,?,?,?,?,?,'ACTIVE')", (
                    plan.job_id, thread, name, parent, depth, envelope, attempt.request_digest))
                participant = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?",
                    (plan.job_id, thread)).fetchone()
            require(participant["state"] == "ACTIVE" and participant["name"] == name and
                    participant["parent"] == meta.get("parent_thread_id") and
                    reserve.parent_operation_id == participant["envelope"] and reserve.kind == (
                        "model" if participant["depth"] == 0 else "helper"), "NATIVE_ADMISSION_SCOPE")
            require(meta.get("thread_source") == ("user" if participant["depth"] == 0 else "subagent")
                    and (participant["depth"] == 0 or meta.get("subagent_kind") == "thread_spawn"),
                    "NATIVE_LINEAGE")
            require_active_participant(db, plan.job_id, thread)
            old = db.execute("SELECT * FROM native_request_admissions WHERE operation=?",
                             (reserve.operation_id,)).fetchone()
            values = (reserve.operation_id, plan.job_id, thread, attempt.request_digest, raw_ref,
                      participant["envelope"], account, digest(reserve.model_dump()))
            require(old is None or tuple(old) == values, "IDEMPOTENCY_CONFLICT")
            db.execute("INSERT OR IGNORE INTO native_request_admissions VALUES(?,?,?,?,?,?,?,?)", values)
            from .native_retirement import index_native_tool_calls
            indexed = db.execute("SELECT rowid ordinal,* FROM native_request_admissions WHERE operation=?",
                                 (reserve.operation_id,)).fetchone()
            index_native_tool_calls(db, self.cas, indexed, body=body)
            self.db.event(db, "native.request_admitted", {"operation": reserve.operation_id,
                "job": plan.job_id, "thread": thread, "depth": participant["depth"],
                "initial_context_digest": participant["initial_context"], "raw_ref": raw_ref,
                "tool_projection_ref": plan.tool_projection_ref,
                "tool_projection_digest": projection_digest})
        return dict(participant)

    def enroll(self, operation, *, tool_calls=100):
        """After durable per-call admission, before returning tool-capable output."""
        db = self.db.connection
        row = db.execute("SELECT * FROM native_request_admissions WHERE operation=?", (operation,)).fetchone()
        require(row is not None, "NATIVE_REQUEST_NOT_ADMITTED")
        plan = self._plan(db, row["job"])
        dispatch = db.execute("SELECT state,request FROM inference_attempts WHERE operation=?",
                              (operation,)).fetchone()
        require(dispatch is not None and dispatch["state"] == "DISPATCHING" and
                json.loads(dispatch["request"])["request_digest"] == row["request_digest"],
                "NATIVE_DISPATCH_NOT_ADMITTED")
        p = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?",
                       (row["job"], row["thread"])).fetchone()
        existing = db.execute("SELECT body FROM broker_grants WHERE runtime=? AND thread=?",
            (row["job"], row["thread"])).fetchone() if db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='broker_grants'").fetchone() else None
        if existing:
            broker = NativeBroker(self.db, self.cas, plan.job_id, plan.profile_digest(), clock=self.clock)
            grant = broker._grant(db, row["thread"])[0]
            self._project_skills(plan, grant, broker)
            return grant
        root = self._root_thread(db, row["job"])
        evidence = self.cas.put(Principal("operator", "operator"), "operator", "operator", canonical({
            "schema": "strata/NativeBrokerAdmission/1", "operation_id": operation, "job": row["job"],
            "thread": row["thread"], "envelope": row["envelope"],
            "request_digest": row["request_digest"], "profile_digest": plan.profile_digest()}))
        grant = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1",
            "runtime_id": plan.job_id, "session_id": root, "thread_id": row["thread"],
            "parent_thread_id": p["parent"], "profile_digest": plan.profile_digest(), "model": plan.model,
            "role": "executor" if p["depth"] == 0 else "helper", "namespace": "native:" +
                digest({"job": row["job"], "thread": row["thread"]}),
            "campaign_id": plan.campaign_id, "agent_id": plan.agent_id, "epoch": plan.epoch,
            "depth": p["depth"], "expires_unix_ms": int((db.execute(
                "SELECT started FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone()[0]
                + plan.hard_timeout_s)*1000),
            "tool_calls": tool_calls, "admission_ref": evidence})
        # Descendant grant lifetime must not outlive its parent.
        if p["parent"]:
            parent = db.execute("SELECT body FROM broker_grants WHERE runtime=? AND thread=?",
                (row["job"], p["parent"])).fetchone()
            require(parent is not None, "BROKER_LINEAGE")
            grant = grant.model_copy(update={"expires_unix_ms": min(grant.expires_unix_ms,
                BrokerGrant.model_validate_json(parent[0]).expires_unix_ms)})
        broker = NativeBroker(self.db, self.cas, plan.job_id, plan.profile_digest(), clock=self.clock)
        broker.admit(grant)
        self._project_skills(plan, grant, broker)
        return grant

    def _project_skills(self, plan, grant, broker):
        if plan.skill_activation_ref is not None:
            from .native import NativeExec
            from .native_skill_activation import NativeSkillSets
            mode = self.db.connection.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()[0]
            NativeSkillSets(NativeExec(self.db, self.cas, simulation=bool(mode))).project(plan, grant, broker)

    def revoke(self, job, thread):
        """Fence a subtree immediately; retain its slots and every usage hold."""
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM native_participants WHERE job=? AND thread=?",
                               (job, thread)).fetchone(), "NATIVE_PARTICIPANT_UNKNOWN")
            pending = [thread]
            ordinal = db.execute("SELECT coalesce(max(rowid),0) FROM native_request_admissions WHERE job=?",
                                 (job,)).fetchone()[0]
            while pending:
                current = pending.pop()
                pending.extend(r[0] for r in db.execute("SELECT thread FROM native_participants "
                    "WHERE job=? AND parent=?", (job, current)))
                db.execute("UPDATE native_participants SET state='REVOKED' WHERE job=? AND thread=? "
                           "AND state IS NOT 'CLOSED'",
                           (job, current))
                db.execute("INSERT OR IGNORE INTO native_participant_retirements VALUES(?,?,?,NULL)",
                           (job, current, ordinal))
            self.db.event(db, "native.participant_revoked", {"job": job, "thread": thread})

    def retire(self, job, thread, proof_ref):
        from .native_retirement import retire_participant
        return retire_participant(self, job, thread, proof_ref)


def require_active_participant(db, job, thread):
    row = db.execute("SELECT * FROM native_participants WHERE job=? AND thread=?", (job, thread)).fetchone()
    require(row is not None and row["state"] == "ACTIVE", "NATIVE_PARTICIPANT_REVOKED")
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='broker_grants'").fetchone():
        grant = db.execute("SELECT revoked FROM broker_grants WHERE runtime=? AND thread=?",
                           (job, thread)).fetchone()
        require(grant is None or not grant[0], "NATIVE_PARTICIPANT_REVOKED")
    if row["parent"] is not None:
        require_active_participant(db, job, row["parent"])


def require_request_admission(db, plan, attempt, reserve, account, *, cas, simulation):
    if plan.bootstrap_digest is not None:
        from .native_bootstrap import verify_native_inventory
        verify_native_inventory(plan)
    if plan.tool_catalog_policy is not None:
        from .native_catalog import require_no_patch_catalog
        require_no_patch_catalog(plan)
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_request_admissions'").fetchone(),
            "NATIVE_REQUEST_NOT_ADMITTED")
    row = db.execute("SELECT a.*,p.state FROM native_request_admissions a JOIN native_participants p "
        "ON a.job=p.job AND a.thread=p.thread WHERE operation=?", (reserve.operation_id,)).fetchone()
    require(row is not None and row["job"] == plan.job_id and row["state"] == "ACTIVE" and
            row["request_digest"] == attempt.request_digest and row["account"] == account and
            row["envelope"] == reserve.parent_operation_id and
            row["reservation_digest"] == digest(reserve.model_dump()), "NATIVE_REQUEST_NOT_ADMITTED")
    require_active_participant(db, plan.job_id, row["thread"])
    if not simulation:
        require(plan.tool_projection_ref is not None, "NATIVE_TOOL_PROJECTION_REQUIRED")
        require(plan.tool_catalog_policy is not None, "NATIVE_TOOL_CATALOG_REQUIRED")
    if plan.tool_projection_ref is not None:
        from .native_tool_projection import require_tool_projection
        # Re-read immutable private raw bytes at the durable dispatch boundary;
        # an old admission row is not a substitute for the current capability pin.
        raw = cas.read(Principal("operator", "operator"), "operator", row["raw_ref"],
                       max_bytes=1024 * 1024)
        require(row["raw_ref"] == "cas:sha256:" + attempt.request_digest,
                "REQUEST_DIGEST_MISMATCH")
        participant = db.execute("SELECT depth FROM native_participants WHERE job=? AND thread=?",
                                (plan.job_id, row["thread"])).fetchone()
        require_tool_projection(cas, plan, strict_json(raw),
                                "executor" if participant[0] == 0 else "helper")


def close_participant_envelopes(database, budgets, db, plan, proof, seal_ref):
    """Called only inside NativeExec's terminal process/ingress-seal transaction."""
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_participants'").fetchone(),
            "DISPATCH_SEAL_UNVERIFIED")
    rows = list(db.execute("SELECT * FROM native_participants WHERE job=? ORDER BY depth DESC,thread",
                           (plan.job_id,)))
    require(sorted(r["thread"] for r in rows) == proof.get("participant_threads"),
            "DISPATCH_SEAL_UNVERIFIED")
    for row in rows:
        if row["depth"] == 0:
            continue  # NativeExec closes the root after all descendant envelopes.
        if row["state"] == "CLOSED":
            operation = db.execute("SELECT actual,uncertain FROM operations WHERE id=?", (row["envelope"],)).fetchone()
            require(operation is not None and operation["actual"] is not None and not operation["uncertain"],
                    "DESCENDANT_UNSETTLED")
            continue
        from .native_retirement import close_helper_envelope
        close_helper_envelope(budgets, db, plan, row, seal_ref)
    db.execute("UPDATE native_participants SET state='CLOSED' WHERE job=?", (plan.job_id,))
    database.event(db, "native.participants_closed", {"job": plan.job_id,
                   "threads": sorted(r["thread"] for r in rows), "seal_ref": seal_ref})
