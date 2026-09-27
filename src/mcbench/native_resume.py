"""Private resume receipt contracts; referenced controller verification remains external."""

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Digest, Id, Positive, Ref, Strict, UInt
from .native_game import GameLane
from .storage import require
from .worker_repair import WorkerRepairPlan


class NativeResumeDecision(Strict):
    schema_: Literal["strata/NativeSettingsResumeDecision/1"] = Field(alias="schema")
    policy: Literal["operator-owned-settings-resume/1"]
    resume_id: Id
    worker_plan: WorkerRepairPlan
    expected_revision: Positive
    expected_digest: Digest
    completion_phase: Literal["committed", "rolled_back"]
    verification_ref: Ref
    connection_generation: UInt
    lease_until_unix_ms: Positive

    @model_validator(mode="after")
    def bounded_lease(self):
        require(self.lease_until_unix_ms <= self.worker_plan.expires_unix_ms, "SETTINGS_RESUME_INVALID")
        return self


class NativeResumeState(Strict):
    schema_: Literal["strata/NativeSettingsResumeState/1"] = Field(alias="schema")
    decision: NativeResumeDecision
    source_instance: Id
    current_instance: Id
    health: GameLane
    input_resumed: bool
    effects_verified_by_native: Literal[False]

    @model_validator(mode="before")
    @classmethod
    def authority_flags(cls, value):
        require(isinstance(value, dict) and type(value.get("input_resumed")) is bool
                and value.get("effects_verified_by_native") is False, "SETTINGS_RESUME_RESPONSE_INVALID")
        return value

    @model_validator(mode="after")
    def active_scope(self):
        if self.input_resumed:
            require(self.source_instance == self.current_instance and not self.health.fenced
                    and self.health.journal_healthy and self.health.epoch == self.decision.worker_plan.epoch,
                    "SETTINGS_RESUME_RESPONSE_INVALID")
        return self
