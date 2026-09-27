"""Private worker-owned repair handoff. No native settings or gameplay authority."""

import http.client
import re
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator

from .client_discovery import bounded_read
from .contracts import Digest, Id, Positive, Strict, UInt
from .native_settings import strict_json
from .storage import Fault, canonical, digest, require

POLICY = "operator-owned-fixed-repair-pause/1"


class WorkerRepairPlan(Strict):
    schema_: Literal["strata/WorkerRepairPlan/1"] = Field(alias="schema")
    policy: Literal[POLICY]
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    lease_id: Id
    transaction_id: Id
    plan_digest: Digest
    expires_unix_ms: Positive


class WorkerRepairGrant(Strict):
    schema_: Literal["strata/WorkerRepairGrant/1"] = Field(alias="schema")
    policy: Literal[POLICY]
    url: str = Field(max_length=128, pattern=r"^http://127\.0\.0\.1:[0-9]{1,5}/v1/repair$")
    token: SecretStr
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    lease_id: Id

    @model_validator(mode="after")
    def endpoint(self):
        require(0 < self.port < 65536 and bool(re.fullmatch(r"[0-9a-f]{64}", self.token.get_secret_value())),
                "REPAIR_GRANT_INVALID")
        return self

    @property
    def port(self):
        return int(self.url.split(":")[2].split("/")[0])


class WorkerRepairState(Strict):
    schema_: Literal["strata/WorkerRepairState/1"] = Field(alias="schema")
    policy: Literal[POLICY]
    plan: WorkerRepairPlan
    phase: Literal["quiescing", "paused", "failed"]
    reason: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    inputs_released: bool
    primitive_events: UInt
    gameplay_suspended: Literal[True]
    resume_authorized: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def exact_authority_flags(cls, value):
        require(isinstance(value, dict) and value.get("gameplay_suspended") is True
                and value.get("resume_authorized") is False, "REPAIR_RESPONSE_INVALID")
        return value

    @model_validator(mode="after")
    def terminal(self):
        require((self.phase == "failed") == (self.reason is not None)
                and (self.phase != "paused" or self.inputs_released), "REPAIR_RESPONSE_INVALID")
        return self


class WorkerRepairReply(Strict):
    schema_: Literal["strata/WorkerRepairResponse/1"] = Field(alias="schema")
    request_id: Id
    status: Literal["ok"]
    result: WorkerRepairState


class WorkerRepairUnknown(Fault):
    def __init__(self, request_id):
        super().__init__("REPAIR_OUTCOME_UNKNOWN")
        self.request_id = request_id


class WorkerRepairClient:
    def __init__(self, grant: WorkerRepairGrant):
        try:
            raw = grant.model_dump(mode="python")
            raw["token"] = grant.token.get_secret_value()
            self.grant = WorkerRepairGrant.model_validate(raw)
            # Bind the actual private capability without storing it in evidence.
            self.binding_digest = digest(raw)
        except (ValueError, AttributeError, TypeError):
            raise Fault("REPAIR_GRANT_INVALID") from None

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(WorkerRepairGrant.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            raise Fault("REPAIR_GRANT_INVALID") from None

    def validate_scope(self, plan: WorkerRepairPlan):
        for key in ("campaign_id", "agent_id", "epoch", "lease_id"):
            require(getattr(self.grant, key) == getattr(plan, key), "REPAIR_NOT_OWNED")

    def call(self, operation: Literal["pause", "status"], plan: WorkerRepairPlan, *, timeout_ms=1000):
        require(operation in {"pause", "status"}, "CAPABILITY_MISSING")
        require(type(timeout_ms) is int and 1 <= timeout_ms <= 2000, "REPAIR_DEADLINE_INVALID")
        try:
            plan = WorkerRepairPlan.model_validate(plan.model_dump())
        except (ValueError, AttributeError):
            raise Fault("REPAIR_PLAN_INVALID") from None
        self.validate_scope(plan)
        if operation == "pause":
            require(plan.expires_unix_ms > time.time() * 1000, "REPAIR_DEADLINE_EXPIRED")
        request_id = str(uuid.uuid4())
        body = canonical({"schema": "strata/WorkerRepairRequest/1", "request_id": request_id,
                          "operation": operation, "plan": plan.model_dump()})
        require(len(body) <= 4096, "REPAIR_REQUEST_INVALID")
        until = time.monotonic() + timeout_ms / 1000
        connection = http.client.HTTPConnection("127.0.0.1", self.grant.port, timeout=timeout_ms / 1000)
        try:
            # One POST only. A missing or rejected reply never causes mutation replay.
            connection.request("POST", "/v1/repair", body, headers={"Content-Type": "application/json",
                "Authorization": "Bearer " + self.grant.token.get_secret_value(), "Connection": "close"})
            response = connection.getresponse()
            require(response.status == 200 and response.getheader("Content-Type") == "application/json",
                    "REPAIR_RESPONSE_INVALID")
            chunks, size = [], 0
            while True:
                remaining = until - time.monotonic()
                require(remaining > 0, "REPAIR_DEADLINE_EXPIRED")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(4097 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                require(size <= 4096, "REPAIR_RESPONSE_INVALID")
            require(time.monotonic() <= until, "REPAIR_DEADLINE_EXPIRED")
            reply = WorkerRepairReply.model_validate(strict_json(b"".join(chunks)))
            require(reply.request_id == request_id and reply.result.plan == plan, "REPAIR_NOT_OWNED")
            return reply
        except (OSError, ValueError, http.client.HTTPException):
            if operation == "pause":
                raise WorkerRepairUnknown(request_id) from None
            raise Fault("REPAIR_STATUS_UNAVAILABLE") from None
        finally:
            connection.close()
