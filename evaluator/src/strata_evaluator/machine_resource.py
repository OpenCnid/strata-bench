"""One native completion's resource proof, without fabricated boundary events."""

from mcbench.records import GameEvent
from mcbench.storage import digest, require

from .machine_capture import POLICY_V2, NativeFurnaceCompletionV2, require_capture_scope
from .machine_witness import FurnaceRecipe, require_furnace_deltas

POLICY = "thermal1192-native-furnace-resource/1"


def qualify_native_furnace_completion(event: GameEvent, recipe: dict):
    """Compare a V2 capture with independently supplied expected recipe facts.

    The caller must authenticate the complete stream/startup and register the
    expected scope/recipe separately. This pure verifier neither authenticates
    a producer nor deduplicates imports, binds a fixture/team or grants credit.
    Recipe energy is a recipe fact, never measured RF consumption.
    """
    require(event.visibility == "evaluator", "MACHINE_PRIVATE_EVIDENCE_REQUIRED")
    capture = require_capture_scope(event, True, POLICY_V2)
    require(isinstance(capture, NativeFurnaceCompletionV2), "MACHINE_COMPLETION_REQUIRED")
    plan = FurnaceRecipe.model_validate(recipe)
    resolved = capture.resolved_recipe
    require(capture.registration.source_recipe_id == plan.recipe_id
            and resolved.input == plan.input and resolved.output == plan.output
            and resolved.resolved_input_count == plan.input.count
            and resolved.output_chance == plan.output_chance
            and resolved.recipe_energy_rf == plan.recipe_energy_rf,
            "MACHINE_REGISTERED_RECIPE_MISMATCH")
    require_furnace_deltas(tuple(capture.states), plan)
    return {"policy": POLICY, "resource_witness": "pass",
        "transaction_id": capture.transaction_id,
        "campaign_id": event.campaign_id, "epoch": event.epoch,
        "server_boot_id": event.server_boot_id, "server_tick": event.server_tick,
        "server_event_seq": event.server_event_seq,
        "dimension": capture.dimension, "position": list(capture.position),
        "block_id": capture.block_id, "recipe_id": plan.recipe_id,
        "recipe_digest": digest(plan.model_dump()),
        "registration": capture.registration.model_dump(),
        "consumed": {plan.input.item_id: plan.input.count},
        "produced": {plan.output.item_id: plan.output.count},
        "source_event_digests": [digest(event.model_dump())],
        "producer_authenticated": False, "recipe_registration_bound": False,
        "setup_team_qualified": False, "sustained_operation_verified": False,
        "energy_consumption_verified": False, "fluid_consumption_verified": False,
        "scoring_eligible": False}
