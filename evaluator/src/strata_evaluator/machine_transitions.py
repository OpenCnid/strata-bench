"""Private native process-start carry and stop-refund witnesses."""

from typing import Literal

from pydantic import Field

from mcbench.storage import digest, require

from .machine_capture import NativeFurnaceBase, FurnaceRegistration, ResolvedFurnaceRecipe
from .machine_energy import ProcessState

POLICY = "thermal1192-native-furnace-transitions/1"
KINDS = {"machine_process_transition": "strata/NativeFurnaceProcessTransition/1",
         "machine_process_transition_refused": "strata/NativeFurnaceProcessTransitionRefusal/1"}


class TransitionState(ProcessState):
    # The first processStart may follow an idle machine with no prior progress.
    process_max: int = Field(ge=0, le=2**31 - 1)
    process_tick: int = Field(ge=0, le=2**31 - 1)


class TransitionBase(NativeFurnaceBase):
    policy: Literal["thermal1192-native-furnace-transitions/1"]
    operation: Literal["start", "refund"]


class ProcessStart(TransitionBase):
    operation: Literal["start"]
    registration: FurnaceRegistration
    resolved_recipe: ResolvedFurnaceRecipe
    states: list[TransitionState] = Field(min_length=2, max_length=2)
    base_process_tick: int = Field(ge=1, le=2**31 - 1)


class ProcessRefund(TransitionBase):
    operation: Literal["refund"]
    states: list[TransitionState] = Field(min_length=2, max_length=2)


class TransitionRefusal(TransitionBase):
    reason: Literal["native_profile_unsupported", "native_registration_unobserved",
                    "native_registration_changed"]


def parse_transition(event, supported):
    require(supported and event.kind in KINDS and event.payload_schema == KINDS[event.kind]
            and not event.is_example and not event.actor_ids and not event.evidence_refs,
            "MACHINE_TRANSITION_SCOPE")
    if event.kind.endswith("_refused"):
        return TransitionRefusal.model_validate(event.payload)
    require(event.payload.get("operation") in {"start", "refund"}, "MACHINE_TRANSITION_OPERATION")
    model = ProcessStart if event.payload["operation"] == "start" else ProcessRefund
    return model.model_validate(event.payload)


def qualify_transition(event, captured):
    """Verify only the native bracket; do not infer a continuous/net energy bill."""
    before, after = captured.states
    changed = ({"process", "process_max", "process_tick"} if captured.operation == "start"
               else {"energy_rf"})
    require(all(getattr(before, key) == getattr(after, key)
                for key in set(TransitionState.model_fields) - changed),
            "MACHINE_TRANSITION_UNRELATED_CHANGE")
    if captured.operation == "start":
        # Reject overflow instead of mistaking wrapped Java progress for useful work.
        amount = captured.resolved_recipe.recipe_energy_rf + before.process
        require(before.process <= 0 and 0 < amount <= 2**31 - 1
                and after.process == after.process_max == amount
                and after.process_tick == captured.base_process_tick,
                "MACHINE_START_CARRY_UNPROVEN")
        facts = {"progress_carried": before.process, "progress_started": amount,
                 "registration": captured.registration.model_dump(),
                 "resolved_recipe_digest": digest(captured.resolved_recipe.model_dump())}
    else:
        # tickServer passes -process directly to EnergyStorageCoFH.modify.
        # Java negation/addition can overflow; unsupported arithmetic cannot pass.
        refund = -before.process
        total = before.energy_rf + refund
        require(before.process <= 0 and 0 <= refund <= 2**31 - 1 and total <= 2**31 - 1
                and after.energy_rf == min(before.energy_capacity, total),
                "MACHINE_REFUND_UNPROVEN")
        facts = {"requested_refund_rf": refund,
                 "energy_refunded_rf": after.energy_rf - before.energy_rf}
    return {"policy": POLICY, "transaction_id": captured.transaction_id,
            "source_event_digest": digest(event.model_dump()), "source_seq": event.seq,
            "server_tick": event.server_tick, "server_boot_id": event.server_boot_id,
            "campaign_id": event.campaign_id, "epoch": event.epoch,
            "dimension": captured.dimension, "position": captured.position,
            "operation": captured.operation, **facts,
            "producer_authenticated": False, "sustained_operation_verified": False,
            "setup_team_qualified": False, "scoring_eligible": False}
