"""Native processTick RF deltas, not continuous operation or score authority."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from mcbench.storage import digest, require

from .machine_capture import NativeFurnaceBase, FurnaceRegistration, ResolvedFurnaceRecipe
from .machine_witness import FurnaceState

POLICY = "thermal1192-native-furnace-process-tick/1"
KINDS = {"machine_process_tick": "strata/NativeFurnaceProcessTick/1",
         "machine_process_tick_refused": "strata/NativeFurnaceProcessTickRefusal/1"}


class ProcessState(FurnaceState):
    active: bool
    energy_capacity: int = Field(ge=1, le=2**31 - 1)
    energy_creative: Literal[False]

    @field_validator("energy_creative", mode="before")
    @classmethod
    def real_false(cls, value):
        require(value is False, "MACHINE_TICK_PROFILE")
        return value

    @model_validator(mode="after")
    def profile(self):
        require(self.energy_rf <= self.energy_capacity and not any(v.count for v in self.augments)
                and all(v.components_empty for v in self.slots + self.augments), "MACHINE_TICK_PROFILE")
        return self


class ProcessTick(NativeFurnaceBase):
    policy: Literal["thermal1192-native-furnace-process-tick/1"]
    registration: FurnaceRegistration
    resolved_recipe: ResolvedFurnaceRecipe
    states: list[ProcessState] = Field(min_length=2, max_length=2)
    returned: int = Field(ge=0, le=2**31 - 1)


class ProcessTickRefusal(NativeFurnaceBase):
    policy: Literal["thermal1192-native-furnace-process-tick/1"]
    reason: Literal["native_profile_unsupported", "native_registration_unobserved",
                    "native_registration_changed"]


def parse_tick(event, supported):
    require(supported and event.kind in KINDS and event.payload_schema == KINDS[event.kind]
            and not event.is_example and not event.actor_ids and not event.evidence_refs,
            "MACHINE_TICK_SCOPE")
    model = ProcessTick if event.kind == "machine_process_tick" else ProcessTickRefusal
    return model.model_validate(event.payload)


def qualify_tick(event, captured):
    """Require the pinned processTick arithmetic, including its zero-work return.

    EnergyStorageCoFH.modify clamps below zero. The returned progress decrement
    therefore cannot be treated as the RF actually spent on an underfunded tick.
    The caller authenticates the stream and supplies its already-parsed capture.
    """
    before, after = captured.states
    unchanged = set(ProcessState.model_fields) - {"energy_rf", "process"}
    require(all(getattr(before, k) == getattr(after, k) for k in unchanged),
            "MACHINE_TICK_UNRELATED_CHANGE")
    step = before.process_tick if before.process > 0 else 0
    spent = min(before.energy_rf, step)
    require(captured.returned == step and after.process == before.process - step
            and after.energy_rf == before.energy_rf - spent, "MACHINE_TICK_DEBIT_UNPROVEN")
    return {"policy": POLICY, "transaction_id": captured.transaction_id,
        "source_event_digest": digest(event.model_dump()), "source_seq": event.seq,
        "server_tick": event.server_tick, "server_boot_id": event.server_boot_id,
        "campaign_id": event.campaign_id, "epoch": event.epoch,
        "dimension": captured.dimension, "position": captured.position,
        "registration": captured.registration.model_dump(),
        "resolved_recipe_digest": digest(captured.resolved_recipe.model_dump()),
        "energy_debited_rf": spent, "progress_decrement": step,
        "fully_funded": spent == step, "did_work": step > 0,
        "producer_authenticated": False, "sustained_operation_verified": False,
        "setup_team_qualified": False, "scoring_eligible": False}
