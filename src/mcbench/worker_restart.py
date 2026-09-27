"""Private same-worker restart transport. No launch, gameplay input or resume authority."""

import http.client
import re
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator

from .client_discovery import bounded_read
from .contracts import Digest, Id, Positive, Strict, UInt
from .native_restart import NativeRestartCheckpoint
from .native_settings import strict_json
from .storage import Fault, canonical, digest, require
from .worker_repair import WorkerRepairPlan, WorkerRepairClient


class WorkerRestartGrant(Strict):
    schema_: Literal["strata/WorkerRestartGrant/2"] = Field(alias="schema")
    policy: Literal["operator-owned-client-replacement/1"]
    repair_binding_digest: Digest
    url: str = Field(max_length=128, pattern=r"^http://127\.0\.0\.1:[0-9]{1,5}/v1/restart$")
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
                "RESTART_GRANT_INVALID")
        return self


class ReplacementPaths(Strict):
    connection_file: str = Field(min_length=1, max_length=4096)
    process_guard_file: str = Field(min_length=1, max_length=4096)


class RestartOldTerminal(Strict):
    schema_: Literal["strata/WorkerRestartOldTerminal/1"] = Field(alias="schema")
    checkpoint_digest: Digest
    process_digest: Digest
    connection_digest: Digest
    termination_confirmed: bool

    @model_validator(mode="after")
    def terminal(self):
        require(self.termination_confirmed, "RESTART_OLD_TERMINAL_REQUIRED")
        return self


class RestartGuardReady(Strict):
    schema_: Literal["strata/ProcessGuardEvent/1"] = Field(alias="schema")
    kind: Literal["ready"]
    process_digest: Digest
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    whole_client_lifetime: bool
    campaign_admission: bool
    remaining_wall_ms: Positive
    policy: Literal["forge-process-listener-client-thread/3", "forge-process-listener-client-thread/4"]
    connection_digest: Digest
    body_fingerprint: Digest
    connection_generation: UInt
    implementation_digest: Digest
    python: Literal["3.12.14"]

    @model_validator(mode="after")
    def authority(self):
        require(self.whole_client_lifetime and not self.campaign_admission, "RESTART_RESPONSE_INVALID")
        return self


class WorkerRestartState(Strict):
    schema_: Literal["strata/WorkerRestartState/1"] = Field(alias="schema")
    plan: WorkerRepairPlan
    checkpoint: NativeRestartCheckpoint
    phase: Literal["detaching", "detached", "attaching", "attached", "recovery_required"]
    old_connection_digest: Digest
    old_terminal: RestartOldTerminal | None
    replacement: RestartGuardReady | None
    primitive_events: UInt
    gameplay_suspended: bool
    input_resumed: bool

    @model_validator(mode="after")
    def joins(self):
        require(self.gameplay_suspended and not self.input_resumed
                and self.checkpoint.request.transaction_id == self.plan.transaction_id
                and self.checkpoint.request.plan_digest == self.plan.plan_digest, "RESTART_RESPONSE_INVALID")
        if self.phase in {"detached", "attaching", "attached"}:
            require(self.old_terminal is not None, "RESTART_OLD_TERMINAL_REQUIRED")
        if self.old_terminal:
            require(self.old_terminal.checkpoint_digest == digest(self.checkpoint.model_dump())
                    and self.old_terminal.connection_digest == self.old_connection_digest, "RESTART_RESPONSE_INVALID")
        if self.phase == "attached":
            require(self.replacement is not None, "RESTART_RESPONSE_INVALID")
        if self.replacement:
            require(self.old_terminal is not None
                    and self.replacement.process_digest != self.old_terminal.process_digest
                    and self.replacement.connection_digest != self.old_connection_digest
                    and all(getattr(self.replacement, k) == getattr(self.plan, k)
                            for k in ("campaign_id", "agent_id", "epoch")), "RESTART_RESPONSE_INVALID")
        return self


class WorkerRestartReply(Strict):
    schema_: Literal["strata/WorkerRestartResponse/1"] = Field(alias="schema")
    request_id: Id
    status: Literal["ok"]
    result: WorkerRestartState


class WorkerRestartUnknown(Fault):
    def __init__(self, request_id):
        super().__init__("RESTART_OUTCOME_UNKNOWN")
        self.request_id = request_id


class WorkerRestartClient:
    def __init__(self, grant):
        raw = grant.model_dump()
        raw["token"] = grant.token.get_secret_value()
        self.grant = WorkerRestartGrant.model_validate(raw)
        self.binding_digest = digest(raw)

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(WorkerRestartGrant.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            raise Fault("RESTART_GRANT_INVALID") from None

    def validate_worker(self, worker: WorkerRepairClient, plan: WorkerRepairPlan):
        require(isinstance(worker, WorkerRepairClient) and worker.binding_digest == self.grant.repair_binding_digest,
                "RESTART_WORKER_MISMATCH")
        worker.validate_scope(plan)
        require(all(getattr(self.grant, k) == getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch", "lease_id")),
                "REPAIR_NOT_OWNED")

    def call(self, operation, plan, checkpoint, *, paths=None, timeout_ms=6000):
        require(operation in {"detach", "attach", "status"}, "CAPABILITY_MISSING")
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 7000, "RESTART_DEADLINE_INVALID")
        plan = WorkerRepairPlan.model_validate(plan.model_dump())
        checkpoint = NativeRestartCheckpoint.model_validate(checkpoint.model_dump())
        require(all(getattr(self.grant, k) == getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch", "lease_id"))
                and checkpoint.request.transaction_id == plan.transaction_id
                and checkpoint.request.plan_digest == plan.plan_digest, "REPAIR_NOT_OWNED")
        paths = ReplacementPaths.model_validate(paths) if operation == "attach" else paths
        require(operation == "attach" or paths is None, "RESTART_REQUEST_INVALID")
        if operation != "status":
            require(plan.expires_unix_ms > time.time() * 1000, "REPAIR_DEADLINE_EXPIRED")
        request_id = str(uuid.uuid4())
        body = canonical({"schema": "strata/WorkerRestartRequest/1", "request_id": request_id,
            "operation": operation, "plan": plan.model_dump(), "checkpoint": checkpoint.model_dump(),
            "paths": paths.model_dump() if paths else None})
        require(len(body) <= 16384, "RESTART_REQUEST_INVALID")
        until = time.monotonic() + timeout_ms / 1000
        connection = http.client.HTTPConnection("127.0.0.1", self.grant.port, timeout=timeout_ms / 1000)
        try:
            connection.request("POST", "/v1/restart", body, headers={"Content-Type": "application/json",
                "Authorization": "Bearer " + self.grant.token.get_secret_value(), "Connection": "close"})
            response = connection.getresponse()
            require(response.status == 200 and response.getheader("Content-Type") == "application/json", "RESTART_RESPONSE_INVALID")
            chunks, size = [], 0
            while True:
                remaining = until - time.monotonic()
                require(remaining > 0, "RESTART_DEADLINE_INVALID")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(16385 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                require(size <= 16384, "RESTART_RESPONSE_INVALID")
            require(time.monotonic() <= until, "RESTART_DEADLINE_INVALID")
            reply = WorkerRestartReply.model_validate(strict_json(b"".join(chunks)))
            require(reply.request_id == request_id and reply.result.plan == plan
                    and reply.result.checkpoint == checkpoint, "REPAIR_NOT_OWNED")
            return reply
        except (OSError, ValueError, http.client.HTTPException):
            if operation != "status":
                raise WorkerRestartUnknown(request_id) from None
            raise Fault("RESTART_STATUS_UNAVAILABLE") from None
        finally:
            connection.close()
