"""Bind one native executor's lifetime to its existing scoped game worker.

The descriptor remains operator-side. A missing stop acknowledgement is durable
uncertainty, never permission to replay an action or claim a clean checkpoint.
"""

import json
import time
import uuid
from datetime import datetime, timezone

from .broker_stdio import WorkerTransport
from .contracts import RpcRequest
from .storage import canonical, digest, require


class NativeWorker:
    def __init__(self, database, descriptor):
        self.db = database
        self.descriptor = dict(descriptor)
        self.transport = WorkerTransport(dict(descriptor))
        self.job = None
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_worker_bindings (job TEXT PRIMARY KEY, "
                       "scope TEXT NOT NULL, grant_digest TEXT NOT NULL, state TEXT NOT NULL, "
                       "stop_request TEXT, stop_result TEXT)")

    def bind(self, plan):
        scope = {key: getattr(plan, key) for key in ("campaign_id", "agent_id", "epoch")}
        require(plan.role == "executor" and plan.parent_job_id is None and
                all(self.descriptor[key] == value for key, value in scope.items()), "BROKER_SCOPE")
        require(self.job is None, "NATIVE_WORKER_ALREADY_BOUND")
        with self.db.transaction() as db:
            require(db.execute("SELECT 1 FROM native_worker_bindings WHERE job=?",
                               (plan.job_id,)).fetchone() is None, "NATIVE_WORKER_ALREADY_BOUND")
            db.execute("INSERT INTO native_worker_bindings VALUES(?,?,?,'BOUND',NULL,NULL)",
                       (plan.job_id, canonical(scope).decode(), digest(self.descriptor)))
            self.db.event(db, "native.worker_bound", {"job": plan.job_id, **scope,
                "grant_digest": digest(self.descriptor)})
        self.job = plan.job_id

    def revoke(self, campaign_id, agent_id, epoch):
        require(self.job is not None, "NATIVE_WORKER_UNBOUND")
        scope = {"campaign_id": campaign_id, "agent_id": agent_id, "epoch": epoch}
        with self.db.transaction() as db:
            row = db.execute("SELECT * FROM native_worker_bindings WHERE job=?", (self.job,)).fetchone()
            require(json.loads(row["scope"]) == scope, "BROKER_SCOPE")
            if row["state"] == "STOPPED":
                return json.loads(row["stop_result"])
            require(row["state"] == "BOUND", "NATIVE_WORKER_STOP_UNKNOWN")
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1", **scope,
                "request_id": "native-stop-" + uuid.uuid4().hex,
                "deadline_at": datetime.fromtimestamp(time.time() + 5, timezone.utc).isoformat(
                    timespec="milliseconds").replace("+00:00", "Z"),
                "method": "stop_all", "action": None, "target_request_id": None, "after": None})
            db.execute("UPDATE native_worker_bindings SET state='STOPPING',stop_request=? WHERE job=?",
                       (canonical(request.model_dump()).decode(), self.job))
            self.db.event(db, "native.worker_stop_intent", {"job": self.job, **scope,
                "request_id": request.request_id})
        result = self.transport(request)
        require(result.get("request_id") == request.request_id and result.get("status") == "ok"
                and result.get("result") == {"status": "stopped"}, "NATIVE_WORKER_STOP_UNKNOWN")
        with self.db.transaction() as db:
            db.execute("UPDATE native_worker_bindings SET state='STOPPED',stop_result=? WHERE job=?",
                       (canonical(result).decode(), self.job))
            self.db.event(db, "native.worker_stopped", {"job": self.job, **scope,
                "request_id": request.request_id})
        return result
