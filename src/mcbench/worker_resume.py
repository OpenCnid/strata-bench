"""Private same-worker resume transport; controller settlement/publication remain required."""

import http.client
import re
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator

from .client_discovery import bounded_read
from .contracts import Digest, Id, Observation, Positive, Strict, UInt
from .native_resume import NativeResumeDecision, NativeResumeState
from .native_settings import strict_json
from .storage import Fault, canonical, digest, require
from .worker_repair import WorkerRepairClient
from .worker_restart import WorkerRestartClient


class WorkerResumeGrant(Strict):
    schema_: Literal["strata/WorkerResumeGrant/1"] = Field(alias="schema")
    policy: Literal["operator-owned-settings-resume/1"]
    repair_binding_digest: Digest
    restart_binding_digest: Digest
    url: str = Field(max_length=128, pattern=r"^http://127\.0\.0\.1:[0-9]{1,5}/v1/resume$")
    token: SecretStr
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    lease_id: Id

    @property
    def port(self):
        return int(self.url.split(":")[2].split("/")[0])

    @model_validator(mode="after")
    def endpoint(self):
        require(0 < self.port < 65536 and bool(re.fullmatch(r"[0-9a-f]{64}", self.token.get_secret_value())),
                "RESUME_GRANT_INVALID")
        return self


class WorkerResumeState(Strict):
    schema_: Literal["strata/WorkerResumeState/1"] = Field(alias="schema")
    decision: NativeResumeDecision
    native: NativeResumeState
    observation: Observation
    primitive_events: UInt
    gameplay_resumed: bool

    @model_validator(mode="before")
    @classmethod
    def strict_flag(cls, value):
        require(isinstance(value, dict) and type(value.get("gameplay_resumed")) is bool, "RESUME_RESPONSE_INVALID")
        return value

    @model_validator(mode="after")
    def joins(self):
        plan, observation = self.decision.worker_plan, self.observation
        require(self.native.decision == self.decision
                and self.primitive_events >= self.native.health.attempted_primitive_events
                and not observation.is_example
                and all(getattr(observation, k) == getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch"))
                and observation.state is not None and observation.state.connected
                and observation.state.active_request_id is None and not observation.held_keys
                and observation.age_at_send_ms <= 2000
                and (not self.gameplay_resumed or self.native.input_resumed), "RESUME_RESPONSE_INVALID")
        return self


class WorkerResumeReply(Strict):
    schema_: Literal["strata/WorkerResumeResponse/1"] = Field(alias="schema")
    request_id: Id
    status: Literal["ok"]
    result: WorkerResumeState


class WorkerResumeUnknown(Fault):
    def __init__(self, request_id):
        super().__init__("RESUME_OUTCOME_UNKNOWN")
        self.request_id = request_id


class WorkerResumeClient:
    def __init__(self, grant):
        raw = grant.model_dump()
        raw["token"] = grant.token.get_secret_value()
        self.grant = WorkerResumeGrant.model_validate(raw)
        self.binding_digest = digest(raw)

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(WorkerResumeGrant.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            raise Fault("RESUME_GRANT_INVALID") from None

    def validate_worker(self, worker: WorkerRepairClient, restart: WorkerRestartClient, decision: NativeResumeDecision):
        require(isinstance(worker, WorkerRepairClient) and isinstance(restart, WorkerRestartClient)
                and worker.binding_digest == self.grant.repair_binding_digest
                and restart.binding_digest == self.grant.restart_binding_digest, "RESUME_WORKER_MISMATCH")
        restart.validate_worker(worker, decision.worker_plan)
        self._scope(decision)

    def _scope(self, decision):
        require(all(getattr(self.grant, k) == getattr(decision.worker_plan, k)
                    for k in ("campaign_id", "agent_id", "epoch", "lease_id")), "REPAIR_NOT_OWNED")

    def call(self, operation, decision, *, timeout_ms=2000):
        require(operation in {"resume", "status"}, "CAPABILITY_MISSING")
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 6000, "RESUME_DEADLINE_INVALID")
        decision = NativeResumeDecision.model_validate(decision.model_dump())
        self._scope(decision)
        if operation == "resume":
            require(decision.lease_until_unix_ms > time.time() * 1000, "REPAIR_RESUME_EXPIRED")
        request_id = str(uuid.uuid4())
        body = canonical({"schema": "strata/WorkerResumeRequest/1", "request_id": request_id,
            "operation": operation, "decision": decision.model_dump()})
        require(len(body) <= 16384, "RESUME_REQUEST_INVALID")
        until = time.monotonic() + timeout_ms / 1000
        connection = http.client.HTTPConnection("127.0.0.1", self.grant.port, timeout=timeout_ms / 1000)
        try:
            connection.request("POST", "/v1/resume", body, headers={"Content-Type": "application/json",
                "Authorization": "Bearer " + self.grant.token.get_secret_value(), "Connection": "close"})
            response = connection.getresponse()
            require(response.status == 200 and response.getheader("Content-Type") == "application/json", "RESUME_RESPONSE_INVALID")
            chunks, size = [], 0
            while True:
                remaining = until - time.monotonic()
                require(remaining > 0, "RESUME_DEADLINE_INVALID")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(131073 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                require(size <= 131072, "RESUME_RESPONSE_INVALID")
            require(time.monotonic() <= until, "RESUME_DEADLINE_INVALID")
            reply = WorkerResumeReply.model_validate(strict_json(b"".join(chunks)))
            require(reply.request_id == request_id and reply.result.decision == decision, "REPAIR_NOT_OWNED")
            return reply
        except (OSError, ValueError, http.client.HTTPException):
            if operation == "resume":
                raise WorkerResumeUnknown(request_id) from None
            raise Fault("RESUME_STATUS_UNAVAILABLE") from None
        finally:
            connection.close()
