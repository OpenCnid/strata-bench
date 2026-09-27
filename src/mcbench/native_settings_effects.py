"""Private candidate settings/effect client. Raw observations never establish qualification."""

import http.client
import re
import time
import uuid
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, model_validator

from .client_discovery import bounded_read
from .contracts import Digest, Id, Positive, Ref, Strict, UInt
from .native_game import GameConnection, GameResponse
from .native_restart import NativeRestartCheckpoint, NativeRestartRequest, NativeRestartState
from .native_resume import NativeResumeDecision, NativeResumeState
from .native_settings import (
    MAX_REQUEST, NativePatch, NativeReceipt, NativeSettingsClient, NativeSnapshot, strict_json,
)
from .storage import Fault, canonical, require
from .worker_repair import WorkerRepairPlan

OPERATIONS = frozenset({"settings_snapshot", "settings_apply", "settings_status", "settings_rollback",
                        "settings_effect_start", "settings_effect_status", "settings_repair_bind", "settings_repair_status",
                        "settings_commit", "settings_commit_status", "settings_restart_prepare", "settings_restart_continue", "settings_restart_status",
                        "settings_resume", "settings_resume_status"})
MUTATIONS = frozenset({"settings_apply", "settings_rollback", "settings_effect_start", "settings_repair_bind", "settings_commit",
                      "settings_restart_prepare", "settings_restart_continue", "settings_resume"})
Context = Literal["IN_GAME", "GUI", "CHAT"]
ClassName = Annotated[str, Field(min_length=1, max_length=512, pattern=r"^[A-Za-z_$][A-Za-z0-9_.$]*$")]


class EffectRequest(Strict):
    id: Id
    transaction_id: Id | None
    expected_revision: Positive
    expected_digest: Digest
    plan_digest: Digest
    binding_id: Id
    context: Context
    stage: Literal["baseline", "before_restart", "after_restart"]
    hold_ms: int = Field(ge=1, le=2000)
    settle_ticks: int = Field(ge=1, le=200)

    @model_validator(mode="after")
    def transaction_scope(self):
        require((self.stage == "baseline") == (self.transaction_id is None), "SETTINGS_EFFECT_REQUEST_INVALID")
        return self


class EffectAdmission(Strict):
    wire_schema: Literal["strata/NativeSettingsEffectAdmission/2"] = Field(alias="schema")
    settings_fingerprint: Digest
    request: EffectRequest


class VisibleState(Strict):
    client_tick: UInt
    context: Context
    screen: ClassName
    window_active: bool
    menu_id: UInt
    menu_type: ClassName
    x: float = Field(ge=-30_000_000, le=30_000_000)
    y: float = Field(ge=-2048, le=2048)
    z: float = Field(ge=-30_000_000, le=30_000_000)
    sneaking: bool
    sprinting: bool
    using_item: bool

    @model_validator(mode="after")
    def context_matches(self):
        require((self.context == "IN_GAME") == (self.screen == "none"), "SETTINGS_EFFECT_RESPONSE_INVALID")
        return self


class ScreenOpening(Strict):
    client_tick: UInt
    from_screen: ClassName
    requested_screen: ClassName
    cancelled_at_observer: bool


class ActiveVisibleState(VisibleState):
    swinging: bool
    mouse_grabbed: bool
    mouse_left: bool
    mouse_right: bool


class AdmissionObservation(Strict):
    phase: Literal["admission"]
    index: int = Field(ge=0, le=255)
    value: EffectAdmission


class StateObservation(Strict):
    phase: Literal["before", "held", "released"]
    index: int = Field(ge=0, le=255)
    value: VisibleState | ActiveVisibleState


class OpeningObservation(Strict):
    phase: Literal["screen_opening"]
    index: int = Field(ge=0, le=255)
    value: ScreenOpening


class InputRelease(Strict):
    wire_schema: Literal["strata/NativeInputRelease/1"] = Field(alias="schema")
    key: int = Field(ge=32, le=342)
    modifier: Literal["NONE", "SHIFT", "CONTROL", "ALT"]
    release_order: list[int] = Field(min_length=1, max_length=2)
    callbacks_confirmed: bool
    clear_confirmed: bool

    @model_validator(mode="after")
    def complete(self):
        modifier = {"NONE": None, "SHIFT": 340, "CONTROL": 341, "ALT": 342}[self.modifier]
        require((self.key < 340 or modifier is None)
                and self.release_order == [self.key] + ([] if modifier is None else [modifier])
                and self.callbacks_confirmed and self.clear_confirmed, "SETTINGS_INPUT_RELEASE_UNCONFIRMED")
        return self


class DeviceInputRelease(Strict):
    wire_schema: Literal["strata/NativeInputRelease/2"] = Field(alias="schema")
    device: Literal["keyboard", "mouse"]
    key: int = Field(ge=0, le=342)
    modifier: Literal["NONE", "SHIFT", "CONTROL", "ALT"]
    release_order: list[int] = Field(min_length=1, max_length=2)
    callbacks_confirmed: bool
    clear_confirmed: bool

    @model_validator(mode="after")
    def complete(self):
        modifier = {"NONE": None, "SHIFT": 340, "CONTROL": 341, "ALT": 342}[self.modifier]
        require((self.key in {0, 1} if self.device == "mouse" else self.key >= 32 and (self.key < 340 or modifier is None))
                and self.release_order == [self.key] + ([] if modifier is None else [modifier])
                and self.callbacks_confirmed and self.clear_confirmed, "SETTINGS_INPUT_RELEASE_UNCONFIRMED")
        return self


class PairedInputRelease(Strict):
    wire_schema: Literal["strata/NativeInputRelease/3"] = Field(alias="schema")
    device: Literal["keyboard"]
    key: int = Field(ge=32, le=342)
    modifier: Literal["NONE"]
    companion: int = Field(ge=32, le=339)
    release_order: list[int] = Field(min_length=2, max_length=2)
    callbacks_confirmed: bool
    clear_confirmed: bool

    @model_validator(mode="after")
    def complete(self):
        require(self.key != self.companion and self.release_order == [self.companion, self.key]
                and self.callbacks_confirmed and self.clear_confirmed, "SETTINGS_INPUT_RELEASE_UNCONFIRMED")
        return self


class ReleaseObservation(Strict):
    phase: Literal["input_release"]
    index: int = Field(ge=0, le=255)
    value: Annotated[InputRelease | DeviceInputRelease | PairedInputRelease, Field(discriminator="wire_schema")]


Observation = Annotated[AdmissionObservation | StateObservation | OpeningObservation | ReleaseObservation, Field(discriminator="phase")]


class EffectResult(Strict):
    wire_schema: Literal["strata/NativeSettingsEffects/2", "strata/NativeSettingsEffects/3", "strata/NativeSettingsEffects/4", "strata/NativeSettingsEffects/5"] = Field(alias="schema")
    request: EffectRequest
    state: Literal["prepared", "running", "observed", "unknown", "refused"]
    error_code: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    verified: bool
    committed: bool
    observations: list[Observation] = Field(max_length=256)

    @model_validator(mode="after")
    def trace(self):
        require(not self.verified and not self.committed, "SETTINGS_EFFECT_RESPONSE_INVALID")
        require((self.error_code is not None) == (self.state in {"unknown", "refused"}),
                "SETTINGS_EFFECT_RESPONSE_INVALID")
        if self.state in {"prepared", "refused"}:
            require(not self.observations, "SETTINGS_EFFECT_RESPONSE_INVALID")
        if self.state in {"running", "observed"}:
            require(len(self.observations) >= 2, "SETTINGS_EFFECT_RESPONSE_INVALID")
        released, receipts, tick, total = 0, 0, -1, 0
        for index, item in enumerate(self.observations):
            require(item.index == index, "SETTINGS_EFFECT_RESPONSE_INVALID")
            if index == 0:
                require(isinstance(item, AdmissionObservation) and item.value.request == self.request,
                        "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            elif index == 1:
                require(isinstance(item, StateObservation) and item.phase == "before"
                        and item.value.context == self.request.context, "SETTINGS_EFFECT_RESPONSE_INVALID")
            else:
                require(item.phase in {"held", "released", "screen_opening", "input_release"}, "SETTINGS_EFFECT_RESPONSE_INVALID")
            if isinstance(item, ReleaseObservation):
                require(not self.wire_schema.endswith("/2") and released == 0 and receipts == 0
                        and ((self.wire_schema.endswith("/3") and isinstance(item.value, InputRelease))
                            or (self.wire_schema.endswith("/4") and isinstance(item.value, DeviceInputRelease))
                            or (self.wire_schema.endswith("/5") and isinstance(item.value, (DeviceInputRelease, PairedInputRelease)))),
                        "SETTINGS_EFFECT_RESPONSE_INVALID")
                receipts += 1
            elif not isinstance(item, AdmissionObservation):
                if isinstance(item, StateObservation):
                    require(isinstance(item.value, ActiveVisibleState) == self.wire_schema.endswith(("/4", "/5")),
                            "SETTINGS_EFFECT_RESPONSE_INVALID")
                require(item.value.client_tick >= tick, "SETTINGS_EFFECT_RESPONSE_INVALID")
                tick = item.value.client_tick
            if item.phase == "released":
                require(self.wire_schema.endswith("/2") or receipts == 1, "SETTINGS_INPUT_RELEASE_UNCONFIRMED")
                released += 1
            if item.phase == "held":
                require(released == 0 and receipts == 0, "SETTINGS_EFFECT_RESPONSE_INVALID")
            total += len(canonical(item.model_dump(mode="json", by_alias=True)))
        require(total <= 196608 and released <= self.request.settle_ticks, "SETTINGS_EFFECT_RESPONSE_INVALID")
        if self.state == "observed":
            require(released == self.request.settle_ticks, "SETTINGS_EFFECT_RESPONSE_INVALID")
        return self


class EffectOutcomeUnknown(Fault):
    def __init__(self, request_id, operation, transaction_id, effect_id):
        super().__init__("SETTINGS_EFFECT_OUTCOME_UNKNOWN")
        self.request_id, self.operation = request_id, operation
        self.transaction_id, self.effect_id = transaction_id, effect_id


class NativeRepairAdmission(Strict):
    wire_schema: Literal["strata/NativeSettingsRepairAdmission/1"] = Field(alias="schema")
    policy: Literal["operator-owned-native-settings-repair/1"]
    worker_plan: WorkerRepairPlan
    settings_fingerprint: Digest
    patch: NativePatch
    effect_bindings: list[Id] = Field(min_length=1, max_length=2048)

    @model_validator(mode="after")
    def ownership(self):
        require(self.worker_plan.transaction_id == self.patch.transaction_id
                and len(set(self.effect_bindings)) == len(self.effect_bindings)
                and set(self.patch.changes) <= set(self.effect_bindings), "SETTINGS_REPAIR_INVALID")
        return self


class NativeRepairState(Strict):
    wire_schema: Literal["strata/NativeSettingsRepairState/1"] = Field(alias="schema")
    admission: NativeRepairAdmission
    phase: Literal["bound", "recovery_required"]
    reason: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    body_fingerprint: Digest
    connection_generation: UInt
    primitive_events: UInt
    resume_authorized: bool

    @model_validator(mode="after")
    def recovery(self):
        require(not self.resume_authorized and (self.phase == "bound") == (self.reason is None),
                "SETTINGS_REPAIR_RESPONSE_INVALID")
        return self


class NativeCommitDecision(Strict):
    wire_schema: Literal["strata/NativeSettingsCommitDecision/1"] = Field(alias="schema")
    transaction_id: Id
    plan_digest: Digest
    expected_revision: Positive
    expected_digest: Digest
    verification_ref: Ref


class NativeCommitState(Strict):
    wire_schema: Literal["strata/NativeSettingsCommitState/1"] = Field(alias="schema")
    decision: NativeCommitDecision
    phase: Literal["committed", "rollback_prepared", "rollback_conflict", "rolled_back"]
    revision: Positive
    committed: bool
    input_resumed: bool
    effects_verified_by_native: bool

    @model_validator(mode="after")
    def authority(self):
        require(self.committed == (self.phase == "committed") and not self.input_resumed
                and not self.effects_verified_by_native and self.revision > self.decision.expected_revision,
                "SETTINGS_COMMIT_RESPONSE_INVALID")
        return self


class OwnedNativeReceipt(NativeReceipt):
    phase: Literal["prepared", "applied_pending_verification", "rollback_prepared",
                   "rolled_back", "rollback_conflict", "committed"]
    committed: bool

    @model_validator(mode="after")
    def decision_state(self):
        require(self.committed == (self.phase == "committed"), "SETTINGS_COMMIT_RESPONSE_INVALID")
        return self


class NativeSettingsEffectsClient:
    """Uses a private game descriptor plus a separately pinned settings fingerprint."""

    def __init__(self, connection: GameConnection, settings_fingerprint: str):
        try:
            self.settings_fingerprint = TypeAdapter(Digest).validate_python(settings_fingerprint, strict=True)
        except ValueError:
            raise Fault("SETTINGS_EFFECT_IDENTITY_INVALID") from None
        self.connection = connection
        self._transport = NativeSettingsClient(connection)
        self._transport.response_type = GameResponse

    @classmethod
    def from_file(cls, path: Path, *, game_fingerprint: str, settings_fingerprint: str):
        try:
            raw = strict_json(bounded_read(path, 4096))
            require(isinstance(raw, dict) and raw.get("operator_development_only") is True,
                    "SETTINGS_EFFECT_IDENTITY_INVALID")
            connection = GameConnection.model_validate(raw)
            require(connection.fingerprint == game_fingerprint, "SETTINGS_EFFECT_IDENTITY_INVALID")
            return cls(connection, settings_fingerprint)
        except (OSError, ValueError):
            # Never include a descriptor or server response in an exception message.
            raise Fault("SETTINGS_EFFECT_IDENTITY_INVALID") from None

    @staticmethod
    def _args(operation, args):
        require(isinstance(args, dict), "SETTINGS_EFFECT_REQUEST_INVALID")
        if operation == "settings_apply":
            return NativePatch.model_validate(args).model_dump(mode="json")
        if operation == "settings_repair_bind":
            return NativeRepairAdmission.model_validate(args).model_dump(mode="json")
        if operation == "settings_commit":
            return NativeCommitDecision.model_validate(args).model_dump(mode="json")
        if operation == "settings_resume":
            return NativeResumeDecision.model_validate(args).model_dump(mode="json", by_alias=True)
        if operation == "settings_restart_prepare":
            return NativeRestartRequest.model_validate(args).model_dump(mode="json")
        if operation == "settings_restart_continue":
            return NativeRestartCheckpoint.model_validate(args).model_dump(mode="json")
        if operation == "settings_effect_start":
            return EffectRequest.model_validate(args).model_dump(mode="json")
        if operation in {"settings_status", "settings_rollback", "settings_effect_status", "settings_repair_status", "settings_commit_status", "settings_restart_status", "settings_resume_status"}:
            field = "restart_id" if operation == "settings_restart_status" else "id" if operation == "settings_effect_status" else "transaction_id"
            require(isinstance(args, dict) and set(args) == {field}
                    and isinstance(args[field], str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", args[field]),
                    "SETTINGS_EFFECT_REQUEST_INVALID")
            return dict(args)
        require(args == {}, "SETTINGS_EFFECT_REQUEST_INVALID")
        return {}

    def call(self, operation: str, args: dict, *, timeout_ms: int = 5000,
             effect_deadline_unix_ms: int | None = None,
             expected_effect: EffectRequest | None = None, expected_repair: NativeRepairAdmission | None = None,
             expected_commit: NativeCommitDecision | None = None,
             expected_restart: NativeRestartRequest | NativeRestartCheckpoint | None = None,
             expected_resume: NativeResumeDecision | None = None) -> dict:
        require(operation in OPERATIONS, "CAPABILITY_MISSING")
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 30000, "SETTINGS_DEADLINE_INVALID")
        now_ms = int(time.time() * 1000)
        require(effect_deadline_unix_ms is None or (operation == "settings_effect_start"
                and type(effect_deadline_unix_ms) is int
                and now_ms < effect_deadline_unix_ms <= now_ms + 30000), "SETTINGS_DEADLINE_INVALID")
        try:
            args = self._args(operation, args)
            if operation == "settings_resume_status":
                require(isinstance(expected_resume, NativeResumeDecision), "SETTINGS_RESUME_INVALID")
                expected_resume = NativeResumeDecision.model_validate(expected_resume.model_dump(by_alias=True))
                require(expected_resume.worker_plan.transaction_id == args["transaction_id"], "SETTINGS_RESUME_INVALID")
            else:
                require(expected_resume is None, "SETTINGS_RESUME_INVALID")
            if operation == "settings_effect_status":
                require(isinstance(expected_effect, EffectRequest), "SETTINGS_EFFECT_REQUEST_INVALID")
                expected_effect = EffectRequest.model_validate(expected_effect.model_dump(mode="json"))
                require(expected_effect.id == args["id"], "SETTINGS_EFFECT_REQUEST_INVALID")
            else:
                require(expected_effect is None, "SETTINGS_EFFECT_REQUEST_INVALID")
            if operation == "settings_repair_status":
                require(isinstance(expected_repair, NativeRepairAdmission), "SETTINGS_REPAIR_INVALID")
                expected_repair = NativeRepairAdmission.model_validate(expected_repair.model_dump(mode="json"))
                require(expected_repair.worker_plan.transaction_id == args["transaction_id"], "SETTINGS_REPAIR_INVALID")
            else:
                require(expected_repair is None, "SETTINGS_REPAIR_INVALID")
            if operation == "settings_commit_status":
                require(isinstance(expected_commit, NativeCommitDecision), "SETTINGS_COMMIT_INVALID")
                expected_commit = NativeCommitDecision.model_validate(expected_commit.model_dump(mode="json"))
                require(expected_commit.transaction_id == args["transaction_id"], "SETTINGS_COMMIT_INVALID")
            else:
                require(expected_commit is None, "SETTINGS_COMMIT_INVALID")
            if operation == "settings_restart_status":
                require(isinstance(expected_restart, (NativeRestartRequest, NativeRestartCheckpoint)), "SETTINGS_RESTART_INVALID")
                expected_restart = type(expected_restart).model_validate(expected_restart.model_dump())
                request = expected_restart.request if isinstance(expected_restart, NativeRestartCheckpoint) else expected_restart
                require(request.restart_id == args["restart_id"], "SETTINGS_RESTART_INVALID")
            else:
                require(expected_restart is None, "SETTINGS_RESTART_INVALID")
        except ValueError:
            raise Fault("SETTINGS_EFFECT_REQUEST_INVALID") from None
        request_id = str(uuid.uuid4())
        body = canonical({"schema": "strata/NativeGameRequest/1", "request_id": request_id,
            "session_id": self.connection.session_id, "deadline_unix_ms": (
                effect_deadline_unix_ms if effect_deadline_unix_ms is not None else int(time.time() * 1000) + timeout_ms),
            "operation": operation, "args": args})
        require(len(body) <= MAX_REQUEST, "SETTINGS_REQUEST_TOO_LARGE")
        expires = time.monotonic() + timeout_ms / 1000
        try:
            response = self._transport._exchange("POST", "/v1/game", body, timeout_ms / 1000)
            while True:
                require(response.request_id == request_id and response.session_id == self.connection.session_id,
                        "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
                if response.status == "failed":
                    raise Fault(response.error_code)
                if response.status == "completed":
                    return self._result(operation, args, response.result, expected_effect, expected_repair, expected_commit, expected_restart, expected_resume)
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                time.sleep(min(0.05, remaining))
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                response = self._transport._exchange("GET", "/v1/game/" + request_id, None, remaining)
        except (OSError, http.client.HTTPException, ValueError):
            # Even a typed server error can follow a durable write or partial input.
            if operation in MUTATIONS:
                transaction = args["worker_plan"]["transaction_id"] if operation in {"settings_repair_bind", "settings_resume"} else args.get("transaction_id")
                if operation == "settings_restart_continue":
                    transaction = args["request"]["transaction_id"]
                raise EffectOutcomeUnknown(request_id, operation, transaction, args.get("id")) from None
            raise Fault("SETTINGS_EFFECT_READ_UNAVAILABLE") from None

    def _result(self, operation, args, value, expected_effect=None, expected_repair=None, expected_commit=None, expected_restart=None, expected_resume=None):
        if operation in {"settings_resume", "settings_resume_status"}:
            result = NativeResumeState.model_validate(value)
            expected = NativeResumeDecision.model_validate(args) if operation == "settings_resume" else expected_resume
            require(result.decision == expected, "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            return result.model_dump(mode="json", by_alias=True)
        if operation.startswith("settings_restart_"):
            result = NativeRestartState.model_validate(value)
            expected = (NativeRestartRequest.model_validate(args) if operation == "settings_restart_prepare" else
                        NativeRestartCheckpoint.model_validate(args) if operation == "settings_restart_continue" else expected_restart)
            require(result.checkpoint == expected if isinstance(expected, NativeRestartCheckpoint) else
                    result.checkpoint.request == expected, "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
        elif operation in {"settings_commit", "settings_commit_status"}:
            result = NativeCommitState.model_validate(value)
            expected = NativeCommitDecision.model_validate(args) if operation == "settings_commit" else expected_commit
            require(result.decision == expected, "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
        elif operation in {"settings_repair_bind", "settings_repair_status"}:
            result = NativeRepairState.model_validate(value)
            expected = NativeRepairAdmission.model_validate(args) if operation == "settings_repair_bind" else expected_repair
            require(result.admission == expected and result.admission.settings_fingerprint == self.settings_fingerprint,
                    "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
        elif operation == "settings_snapshot":
            require(value.get("supported") is False and value.get("operator_development_only") is True,
                    "SETTINGS_EFFECT_RESPONSE_INVALID")
            result = NativeSnapshot.model_validate(value)
            require(result.fingerprint == self.settings_fingerprint, "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
        elif operation in {"settings_apply", "settings_status", "settings_rollback"}:
            result = OwnedNativeReceipt.model_validate(value)
            require(result.transaction_id == args["transaction_id"], "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            if operation == "settings_rollback":
                require(result.phase == "rolled_back", "SETTINGS_EFFECT_RESPONSE_INVALID")
        else:
            result = EffectResult.model_validate(value)
            require(result.request.id == args["id"], "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            if operation == "settings_effect_start":
                require(result.request == EffectRequest.model_validate(args), "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            else:
                require(result.request == expected_effect, "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
            for observation in result.observations:
                if isinstance(observation, AdmissionObservation):
                    require(observation.value.settings_fingerprint == self.settings_fingerprint,
                            "SETTINGS_EFFECT_RESPONSE_IDENTITY_MISMATCH")
        return result.model_dump(mode="json", by_alias=True)
