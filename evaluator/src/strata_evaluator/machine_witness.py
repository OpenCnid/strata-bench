"""Private Thermal completion deltas, not authenticated machine scoring.

The pinned MachineBlockEntity.processFinish validates inputs, resolves outputs,
then resolves inputs. Capture begins after successful validation, with intermediate
and final boundaries at those ordinary calls. RF is spent in processTick, outside
this bracket. No snapshot delta is relabelled sustained operation or energy use.
"""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from mcbench.contracts import Digest, Id, Name, Strict
from mcbench.records import GameEvent
from mcbench.storage import digest, require

from .craft_witness import WitnessStack

POLICY = "thermal1192-furnace-resolve-bracket/1"


class FurnaceState(Strict):
    # Exact native base order: input, output, charge; augment slots are separate.
    slots: list[WitnessStack] = Field(min_length=3, max_length=3)
    augments: list[WitnessStack] = Field(max_length=16)
    energy_rf: int = Field(ge=0, le=2**31 - 1)
    process: int = Field(ge=-(2**31), le=2**31 - 1)
    process_max: int = Field(ge=1, le=2**31 - 1)
    process_tick: int = Field(ge=1, le=2**31 - 1)
    active: Literal[True]

    @field_validator("active", mode="before")
    @classmethod
    def actual_boolean(cls, value):
        require(type(value) is bool, "MACHINE_STATE_INVALID")
        return value


class FurnaceBoundary(Strict):
    policy: Literal["thermal1192-furnace-resolve-bracket/1"]
    transaction_id: Id
    dimension: Name
    position: list[int] = Field(min_length=3, max_length=3)
    block_id: Literal["thermal:machine_furnace"]
    recipe_digest: Digest
    state: FurnaceState
    score_eligible: Literal[False]

    @field_validator("score_eligible", mode="before")
    @classmethod
    def actual_boolean(cls, value):
        require(type(value) is bool, "MACHINE_SCORE_FLAG_INVALID")
        return value

    @model_validator(mode="after")
    def bounded_position(self):
        require(all(-(2**31) <= v < 2**31 for v in self.position), "MACHINE_POSITION_INVALID")
        return self


class FurnaceRecipe(Strict):
    """Registered concrete plain one-input/output recipe, after native resolution.

    Its bytes and selected native recipe still need independent authentication.
    This is an evaluator contract, not an invented Thermal API response.
    """

    policy: Literal["thermal1192-furnace-plain-recipe/1"]
    recipe_id: Name
    input: WitnessStack
    output: WitnessStack
    output_chance: int = Field(ge=1, le=1)
    recipe_energy_rf: int = Field(ge=1, le=2**31 - 1)

    @model_validator(mode="after")
    def plain_nonempty(self):
        require(self.input.count > 0 and self.output.count > 0
                and self.input.components_empty and self.output.components_empty,
                "MACHINE_RECIPE_UNSUPPORTED")
        return self


def _quantity(stack, expected):
    if stack.count == 0:
        return 0
    require(stack.item_id == expected.item_id
            and stack.components_sha256 == expected.components_sha256
            and stack.components_empty == expected.components_empty,
            "MACHINE_RESOURCE_IDENTITY")
    return stack.count


def require_furnace_deltas(states: tuple[FurnaceState, FurnaceState, FurnaceState],
                           plan: FurnaceRecipe):
    """Shared arithmetic only; callers retain their original evidence framing."""
    a, b, c = states
    require(all(not any(s.count for s in state.augments) for state in states),
            "MACHINE_AUGMENTS_UNSUPPORTED")
    unchanged = a.model_dump(exclude={"slots"})
    require(all(state.model_dump(exclude={"slots"}) == unchanged for state in states)
            and a.process <= 0 and a.slots[2] == b.slots[2] == c.slots[2],
            "MACHINE_OTHER_RESOURCES_CHANGED")
    require(a.slots[0] == b.slots[0] and b.slots[1] == c.slots[1],
            "MACHINE_RESOLUTION_ORDER")
    input_before, input_after = (_quantity(s.slots[0], plan.input) for s in (a, c))
    output_before, output_after = (_quantity(s.slots[1], plan.output) for s in (a, b))
    require(input_before - input_after == plan.input.count, "MACHINE_CONSUMPTION_UNPROVEN")
    require(output_after - output_before == plan.output.count, "MACHINE_OUTPUT_UNPROVEN")


def qualify_furnace_completion(begin: GameEvent, outputs: GameEvent, end: GameEvent,
                               recipe: dict):
    """Verify all three supplied boundaries; retain every failed witness upstream.

    Caller must authenticate complete ordered records, loaded producer/callback,
    server thread, machine lifetime, recipe and configuration. This function
    cannot prove those properties or establish fixture/team/setup authority.
    """
    events = (begin, outputs, end)
    kinds = ("machine_resolve_begin", "machine_outputs_resolved", "machine_inputs_resolved")
    schemas = ("strata/MachineResolveBegin/1", "strata/MachineOutputsResolved/1",
               "strata/MachineInputsResolved/1")
    require(all(e.kind == k and e.payload_schema == s
                for e, k, s in zip(events, kinds, schemas, strict=True)), "MACHINE_BOUNDARY_SCHEMA")
    require(all(not e.is_example and e.visibility == "evaluator" for e in events),
            "MACHINE_PRIVATE_EVIDENCE_REQUIRED")
    # Autonomous machine work has no guessed player attribution. The registered
    # fixture/team mapping is a separate admission requirement.
    require(all(not e.actor_ids for e in events), "MACHINE_ACTOR_UNPROVEN")
    scope = (begin.campaign_id, begin.epoch, begin.server_boot_id, begin.server_tick)
    require(all((e.campaign_id, e.epoch, e.server_boot_id, e.server_tick) == scope
                and e.server_event_seq == begin.server_event_seq + i
                for i, e in enumerate(events)), "MACHINE_BOUNDARY_SCOPE")
    a, b, c = (FurnaceBoundary.model_validate(e.payload) for e in events)
    plan = FurnaceRecipe.model_validate(recipe)
    expected = digest(plan.model_dump())
    identity = a.model_dump(exclude={"state"})
    require(b.model_dump(exclude={"state"}) == c.model_dump(exclude={"state"}) == identity
            and a.recipe_digest == expected, "MACHINE_BOUNDARY_IDENTITY")
    require_furnace_deltas((a.state, b.state, c.state), plan)
    return {"policy": POLICY, "resource_witness": "pass", "transaction_id": a.transaction_id,
        "campaign_id": begin.campaign_id, "epoch": begin.epoch,
        "server_boot_id": begin.server_boot_id, "server_tick": begin.server_tick,
        "dimension": a.dimension, "position": list(a.position), "block_id": a.block_id,
        "recipe_id": plan.recipe_id, "recipe_digest": expected,
        "consumed": {plan.input.item_id: plan.input.count},
        "produced": {plan.output.item_id: plan.output.count},
        "source_event_digests": [digest(e.model_dump()) for e in events],
        "producer_authenticated": False, "setup_team_qualified": False,
        "sustained_operation_verified": False, "energy_consumption_verified": False,
        "fluid_consumption_verified": False, "scoring_eligible": False}
