"""Private publication transport and measured worker charge intervals.

These receipts do not certify complete campaign settlement or infer game ticks.
"""

import http.client
import re
import time
import uuid
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, StringConstraints, model_validator

from .client_discovery import bounded_read
from .contracts import Digest, Id, Observation, Positive, Ref, Strict, UInt
from .native_resume import NativeResumeDecision
from .native_settings import strict_json
from .storage import Fault, canonical, digest, require
from .worker_repair import WorkerRepairPlan
from .worker_resume import WorkerResumeClient

POLICY = "verified-controls-after-settlement/1"
Source = Annotated[str, StringConstraints(pattern=r"^native:[a-f0-9]{64}:[a-f0-9]{64}$")]


class WorkerControlPublication(Strict):
    schema_: Literal["strata/WorkerControlPublication/1"] = Field(alias="schema")
    policy: Literal[POLICY]
    publication_id: Id
    worker_plan: WorkerRepairPlan
    resume_digest: Digest
    control_revision: Positive
    keymap_digest: Digest
    verification_ref: Ref
    settlement_ref: Ref
    primitive_events: UInt


class WorkerControlPublicationGrant(Strict):
    schema_: Literal["strata/WorkerControlPublicationGrant/1"] = Field(alias="schema")
    policy: Literal[POLICY]
    resume_binding_digest: Digest
    url: str = Field(max_length=128, pattern=r"^http://127\.0\.0\.1:[0-9]{1,5}/v1/publication$")
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
                "CONTROL_PUBLICATION_GRANT_INVALID")
        return self


class WorkerControlPublicationState(Strict):
    schema_: Literal["strata/WorkerControlPublicationState/1"] = Field(alias="schema")
    decision: WorkerControlPublication
    observation: Observation
    primitive_events: UInt
    published: bool

    @model_validator(mode="after")
    def joins(self):
        d, o = self.decision, self.observation
        require(not o.is_example and all(getattr(o, k) == getattr(d.worker_plan, k)
                for k in ("campaign_id", "agent_id", "epoch"))
                and o.control_revision == d.control_revision and o.keymap_digest == d.keymap_digest
                and not o.held_keys and o.age_at_send_ms <= 2000
                and o.state is not None and o.state.connected and o.state.active_request_id is None
                and self.primitive_events >= d.primitive_events, "CONTROL_PUBLICATION_RESPONSE_INVALID")
        return self


class WorkerChargeBoundary(Strict):
    cursor: Positive
    mono_ms: UInt
    unix_ms: Positive
    primitive_events: UInt
    sources: Annotated[dict[Source, UInt], Field(max_length=64)]

    @model_validator(mode="after")
    def total(self):
        require(sum(self.sources.values()) == self.primitive_events, "REPAIR_ACCOUNTING_MISMATCH")
        return self


class WorkerRepairAccounting(Strict):
    schema_: Literal["strata/WorkerRepairAccounting/1"] = Field(alias="schema")
    policy: Literal["durable-worker-charge-interval/1"]
    worker_plan: WorkerRepairPlan
    clock_id: Id
    resume_digest: Digest
    opening: WorkerChargeBoundary
    closing: WorkerChargeBoundary
    charged_primitive_events: UInt
    elapsed_ms: UInt
    complete_repair_accounting: Literal[False]
    avatar_ticks: None
    model_usage: None
    publication_tail_included: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def exact_limits(cls, value):
        require(isinstance(value, dict) and value.get("complete_repair_accounting") is False
                and value.get("publication_tail_included") is False, "REPAIR_ACCOUNTING_INVALID")
        return value

    @model_validator(mode="after")
    def interval(self):
        a, b = self.opening, self.closing
        require(b.cursor > a.cursor and b.mono_ms >= a.mono_ms
                and self.elapsed_ms == b.mono_ms - a.mono_ms
                and self.charged_primitive_events == b.primitive_events - a.primitive_events
                and all(b.sources.get(k, -1) >= v for k, v in a.sources.items()), "REPAIR_ACCOUNTING_MISMATCH")
        return self


class WorkerControlPublicationCommit(Strict):
    schema_: Literal["strata/WorkerControlPublicationCommit/1"] = Field(alias="schema")
    decision: WorkerControlPublication
    observation: Observation
    clock_id: Id
    measurement_digest: Digest
    boundary: WorkerChargeBoundary
    complete_repair_accounting: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def historical_only(cls, value):
        require(isinstance(value, dict) and value.get("complete_repair_accounting") is False,
                "REPAIR_ACCOUNTING_INVALID")
        return value

    @model_validator(mode="after")
    def observation_join(self):
        WorkerControlPublicationState.model_validate({"schema": "strata/WorkerControlPublicationState/1",
            "decision": self.decision.model_dump(), "observation": self.observation.model_dump(),
            "primitive_events": self.boundary.primitive_events, "published": False})
        return self


class WorkerPublicationAccounting(Strict):
    schema_: Literal["strata/WorkerPublicationAccounting/1"] = Field(alias="schema")
    measurement: WorkerRepairAccounting
    commit: WorkerControlPublicationCommit

    @model_validator(mode="after")
    def joins(self):
        m, c = self.measurement, self.commit
        require(c.measurement_digest == digest(m.model_dump()) and c.clock_id == m.clock_id
                and c.decision.worker_plan == m.worker_plan and c.decision.resume_digest == m.resume_digest
                and c.boundary.primitive_events == c.decision.primitive_events == m.closing.primitive_events
                and c.boundary.sources == m.closing.sources and c.boundary.cursor >= m.closing.cursor
                and c.boundary.mono_ms >= m.closing.mono_ms, "REPAIR_ACCOUNTING_CHANGED")
        return self


class WorkerPublicationUnknown(Fault):
    def __init__(self, request_id):
        super().__init__("CONTROL_PUBLICATION_OUTCOME_UNKNOWN")
        self.request_id = request_id


class WorkerPublicationClient:
    def __init__(self, grant):
        raw = grant.model_dump()
        raw["token"] = grant.token.get_secret_value()
        self.grant = WorkerControlPublicationGrant.model_validate(raw)
        self.binding_digest = digest(raw)

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(WorkerControlPublicationGrant.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            raise Fault("CONTROL_PUBLICATION_GRANT_INVALID") from None

    def validate_resume(self, resume):
        require(isinstance(resume, WorkerResumeClient) and self.grant.resume_binding_digest == resume.binding_digest
                and all(getattr(self.grant, k) == getattr(resume.grant, k)
                        for k in ("campaign_id", "agent_id", "epoch", "lease_id")), "RESUME_WORKER_MISMATCH")

    def _scope(self, plan):
        require(all(getattr(self.grant, k) == getattr(plan, k)
                    for k in ("campaign_id", "agent_id", "epoch", "lease_id")), "REPAIR_NOT_OWNED")

    def measure(self, decision: NativeResumeDecision, *, timeout_ms=1000):
        decision = NativeResumeDecision.model_validate(decision.model_dump())
        self._scope(decision.worker_plan)
        result = WorkerRepairAccounting.model_validate(self._call("accounting", {"plan": decision.worker_plan.model_dump()}, timeout_ms))
        require(result.worker_plan == decision.worker_plan and result.resume_digest == digest(decision.model_dump()), "REPAIR_NOT_OWNED")
        return result

    def publish(self, operation, decision: WorkerControlPublication, *, timeout_ms=2000):
        require(operation in {"publish", "status"}, "CAPABILITY_MISSING")
        decision = WorkerControlPublication.model_validate(decision.model_dump())
        self._scope(decision.worker_plan)
        try:
            result = WorkerControlPublicationState.model_validate(self._call(operation,
                {"operation": operation, "decision": decision.model_dump()}, timeout_ms))
            require(result.decision == decision, "REPAIR_NOT_OWNED")
            return result
        except WorkerPublicationUnknown:
            raise
        except ValueError:
            if operation == "publish":
                raise WorkerPublicationUnknown("unusable-publication-reply") from None
            raise Fault("CONTROL_PUBLICATION_STATUS_UNAVAILABLE") from None

    def publication_accounting(self, decision: WorkerControlPublication, *, timeout_ms=1000):
        """Read the immutable commit, with no current input-authority claim."""
        decision = WorkerControlPublication.model_validate(decision.model_dump())
        self._scope(decision.worker_plan)
        result = WorkerPublicationAccounting.model_validate(self._call("publication_accounting",
            {"decision": decision.model_dump()}, timeout_ms))
        require(result.commit.decision == decision, "REPAIR_NOT_OWNED")
        return result

    def _call(self, operation, fields, timeout_ms):
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 6000, "CONTROL_PUBLICATION_DEADLINE_INVALID")
        accounting = operation == "accounting"
        request_id = str(uuid.uuid4())
        kind = ("WorkerRepairAccounting" if accounting else "WorkerPublicationAccounting"
                if operation == "publication_accounting" else "WorkerControlPublication")
        body = canonical({"schema": "strata/" + kind + "Request/1", "request_id": request_id, **fields})
        require(len(body) <= 16384, "CONTROL_PUBLICATION_REQUEST_INVALID")
        until = time.monotonic() + timeout_ms / 1000
        connection = http.client.HTTPConnection("127.0.0.1", self.grant.port, timeout=timeout_ms / 1000)
        try:
            connection.request("POST", "/v1/publication", body, headers={"Content-Type": "application/json",
                "Authorization": "Bearer " + self.grant.token.get_secret_value(), "Connection": "close"})
            response = connection.getresponse()
            require(response.status == 200 and response.getheader("Content-Type") == "application/json", "CONTROL_PUBLICATION_RESPONSE_INVALID")
            chunks, size = [], 0
            while True:
                remaining = until - time.monotonic()
                require(remaining > 0, "CONTROL_PUBLICATION_DEADLINE_INVALID")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(131073 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                require(size <= 131072, "CONTROL_PUBLICATION_RESPONSE_INVALID")
            require(time.monotonic() <= until, "CONTROL_PUBLICATION_DEADLINE_INVALID")
            reply = strict_json(b"".join(chunks))
            require(isinstance(reply, dict) and set(reply) == {"schema", "request_id", "status", "result"}
                    and reply["schema"] == "strata/" + kind + "Response/1" and reply["request_id"] == request_id
                    and reply["status"] == "ok", "CONTROL_PUBLICATION_RESPONSE_INVALID")
            return reply["result"]
        except (OSError, ValueError, http.client.HTTPException):
            if operation == "publish":
                raise WorkerPublicationUnknown(request_id) from None
            raise Fault("REPAIR_ACCOUNTING_UNAVAILABLE" if accounting or operation == "publication_accounting"
                        else "CONTROL_PUBLICATION_STATUS_UNAVAILABLE") from None
        finally:
            connection.close()
