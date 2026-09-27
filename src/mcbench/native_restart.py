"""Private native pending-repair continuation. No process-death or gameplay-resume claim."""

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Digest, Id, Positive, Strict, UInt
from .storage import require


class NativeRestartRequest(Strict):
    schema_: Literal["strata/NativeSettingsRestartRequest/1"] = Field(alias="schema")
    transaction_id: Id
    plan_digest: Digest
    restart_id: Id
    expected_revision: Positive
    expected_digest: Digest


class NativeRestartCheckpoint(Strict):
    schema_: Literal["strata/NativeSettingsRestartCheckpoint/1"] = Field(alias="schema")
    request: NativeRestartRequest
    source_instance: Id


class NativeRestartState(Strict):
    schema_: Literal["strata/NativeSettingsRestartState/1"] = Field(alias="schema")
    checkpoint: NativeRestartCheckpoint
    phase: Literal["prepared", "continued", "recovery_required"]
    current_instance: Id
    continued_instance: Id | None
    primitive_events: UInt
    expires_unix_ms: Positive
    input_resumed: bool

    @model_validator(mode="after")
    def no_resume(self):
        require(not self.input_resumed, "SETTINGS_RESTART_RESPONSE_INVALID")
        require(self.phase != "prepared" or self.continued_instance is None, "SETTINGS_RESTART_RESPONSE_INVALID")
        require(self.continued_instance != self.checkpoint.source_instance, "SETTINGS_RESTART_RESPONSE_INVALID")
        require(self.phase != "continued" or self.current_instance == self.continued_instance,
                "SETTINGS_RESTART_RESPONSE_INVALID")
        return self
