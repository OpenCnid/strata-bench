"""Private native resource qualification; never converts raw records into a score.

This proves only a bounded ordinary shaped craft in a paired server click record.
Authenticated ingestion, fixture/setup validity, team assignment and deployment
isolation must be established separately before a scorer can grant credit.
"""

import hashlib
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from mcbench.contracts import Digest, Id, Name, Strict, UInt
from mcbench.records import GameEvent
from mcbench.storage import require

EMPTY_COMPONENTS = hashlib.sha256(b"{}").hexdigest()


class WitnessStack(Strict):
    item_id: Name
    count: int = Field(ge=0, le=64)
    components_sha256: Digest
    components_empty: bool

    @model_validator(mode="after")
    def consistent(self):
        require((self.count == 0) == (self.item_id == "minecraft:air"), "CRAFT_STACK_INVALID")
        require(
            self.components_empty == (self.components_sha256 == EMPTY_COMPONENTS),
            "CRAFT_COMPONENTS_INVALID",
        )
        require(self.count > 0 or self.components_empty, "CRAFT_STACK_INVALID")
        return self


class WitnessState(Strict):
    slots: list[WitnessStack] = Field(min_length=46, max_length=46)
    cursor: WitnessStack


class CraftBoundary(Strict):
    transaction_id: Id
    policy: Literal["server-result-pickup-bracket/1", "server-result-pickup-fastbench-bound/2"]
    container_id: int = Field(ge=0, le=100)
    score_eligible: Literal[False]
    state: WitnessState


class CraftBegin(CraftBoundary):
    recipe_id: Name
    recipe_output: WitnessStack
    grid_size: Literal[4, 9]


class CraftCallback(Strict):
    output: WitnessStack
    grid: list[WitnessStack] = Field(min_length=4, max_length=9)


class CraftEnd(CraftBoundary):
    same_menu: bool
    nested: bool
    callback_count: UInt
    callback: CraftCallback | None


def qualify_click(begin: GameEvent, callback: GameEvent, end: GameEvent, recipe: dict,
                  *, end_observation: GameEvent | None = None, end_history: GameEvent | None = None):
    """Fail closed on changed resources, partial/foreign boundaries or fake callbacks."""
    require(
        begin.kind == "craft_begin"
        and begin.payload_schema == "strata/CraftBegin/1"
        and end.kind == "craft_end"
        and end.payload_schema == "strata/CraftEnd/1"
        and callback.kind == "craft_callback"
        and callback.payload_schema == "strata/RawCraftCallback/1",
        "CRAFT_BOUNDARY_SCHEMA",
    )
    require(not any(e.is_example for e in (begin, callback, end)), "EXAMPLE_NOT_EXECUTABLE")
    require(
        begin.visibility == callback.visibility == end.visibility == "evaluator", "CRAFT_VISIBILITY"
    )
    require(
        (begin.campaign_id, begin.epoch, begin.server_boot_id, begin.server_tick, begin.actor_ids)
        == (end.campaign_id, end.epoch, end.server_boot_id, end.server_tick, end.actor_ids)
        and len(begin.actor_ids) == 1
        and end.server_event_seq == begin.server_event_seq + 2
            + int(end_observation is not None) + int(end_history is not None),
        "CRAFT_BOUNDARY_SCOPE",
    )
    require(
        (
            callback.campaign_id,
            callback.epoch,
            callback.server_boot_id,
            callback.server_tick,
            callback.actor_ids,
            callback.server_event_seq,
        )
        == (
            begin.campaign_id,
            begin.epoch,
            begin.server_boot_id,
            begin.server_tick,
            begin.actor_ids,
            begin.server_event_seq + 1,
        ),
        "CRAFT_CALLBACK_SCOPE",
    )
    a, b = CraftBegin.model_validate(begin.payload), CraftEnd.model_validate(end.payload)
    if end_history is not None:
        from .setup_history import HISTORY_SCHEMAS, parse_history
        history = parse_history(end_history.payload)
        require(end_observation is not None and not end_history.is_example
                and end_history.visibility == "evaluator" and end_history.kind == "setup_history"
                and end_history.payload_schema == HISTORY_SCHEMAS[history.policy]
                and history.phase == "craft_end" and history.transaction_id == a.transaction_id
                and (end_history.campaign_id, end_history.epoch, end_history.server_boot_id,
                     end_history.server_tick, end_history.actor_ids, end_history.server_event_seq)
                == (begin.campaign_id, begin.epoch, begin.server_boot_id, begin.server_tick,
                    begin.actor_ids, begin.server_event_seq + 2), "CRAFT_SETUP_HISTORY_SCOPE")
    if end_observation is not None:
        from .setup_facts import SetupSnapshot
        point = SetupSnapshot.model_validate(end_observation.payload)
        require(not end_observation.is_example and end_observation.visibility == "evaluator"
                and end_observation.kind == "setup_snapshot"
                and end_observation.payload_schema == "strata/NativeSetupSnapshot/1"
                and point.phase == "craft_end" and point.transaction_id == a.transaction_id
                and point.actor.uuid == begin.actor_ids[0]
                and (end_observation.campaign_id, end_observation.epoch, end_observation.server_boot_id,
                     end_observation.server_tick, end_observation.actor_ids, end_observation.server_event_seq)
                == (begin.campaign_id, begin.epoch, begin.server_boot_id, begin.server_tick,
                    begin.actor_ids, begin.server_event_seq + 2 + int(end_history is not None)),
                "CRAFT_SETUP_POINT_SCOPE")
    require(
        a.transaction_id == b.transaction_id
        and a.container_id == b.container_id
        and a.policy == b.policy,
        "CRAFT_BOUNDARY_IDENTITY",
    )
    require(
        b.same_menu and not b.nested and b.callback_count == 1 and b.callback is not None,
        "CRAFT_CALLBACK_UNPROVEN",
    )
    before, after = a.state, b.state
    require(
        before.cursor.count == 0
        and before.slots[0] == a.recipe_output
        and a.recipe_output.count > 0
        and a.recipe_output.components_empty,
        "CRAFT_OUTPUT_UNPROVEN",
    )
    require(after.cursor == a.recipe_output and after.slots[0].count == 0, "CRAFT_OUTPUT_UNPROVEN")
    grid = before.slots[1 : a.grid_size + 1]
    require(
        b.callback.output == a.recipe_output and b.callback.grid == grid, "CRAFT_CALLBACK_UNPROVEN"
    )

    def plain(stack):
        return {"item_id": stack.item_id, "count": stack.count, "has_nbt": False}

    require(
        callback.payload
        == {
            "score_eligible": False,
            "reason": "consumption_team_recipe_and_setup_provenance_unverified",
            "output_at_callback": plain(a.recipe_output),
            "matrix_at_callback": [plain(s) for s in grid],
        },
        "CRAFT_CALLBACK_UNPROVEN",
    )
    require(
        any(s.count for s in grid) and all(s.count <= 1 and s.components_empty for s in grid),
        "CRAFT_GRID_UNSUPPORTED",
    )
    require(
        all(s.count == 0 for s in after.slots[1 : a.grid_size + 1]), "CRAFT_CONSUMPTION_UNPROVEN"
    )
    # Includes armor/offhand and every full component hash, not just item totals.
    require(
        before.slots[a.grid_size + 1 :] == after.slots[a.grid_size + 1 :],
        "CRAFT_OTHER_RESOURCES_CHANGED",
    )
    require(
        recipe.get("present") is True
        and recipe.get("recipe_id") == a.recipe_id
        and recipe.get("serializer") == "minecraft:crafting_shaped"
        and recipe.get("output") == plain(a.recipe_output),
        "CRAFT_RECIPE_UNPROVEN",
    )
    width, height = recipe.get("width", 0), recipe.get("height", 0)
    side = 3 if a.grid_size == 9 else 2
    ingredients = recipe.get("ingredients", [])
    require(
        type(width) is int
        and type(height) is int
        and 0 < width <= side
        and 0 < height <= side
        and len(ingredients) == width * height,
        "CRAFT_RECIPE_UNPROVEN",
    )

    def matches(ox, oy, mirror):
        for y in range(side):
            for x in range(side):
                item = grid[y * side + x]
                rx, ry = x - ox, y - oy
                allowed = (
                    ingredients[ry * width + (width - 1 - rx if mirror else rx)]
                    if 0 <= rx < width and 0 <= ry < height
                    else []
                )
                matches_item = plain(item) in allowed if allowed else item.count == 0
                if not matches_item:
                    return False
        return True

    require(
        any(
            matches(x, y, mirror)
            for y in range(side - height + 1)
            for x in range(side - width + 1)
            for mirror in (False, True)
        ),
        "CRAFT_RECIPE_UNPROVEN",
    )
    consumed = Counter()
    for item in grid:
        if item.count:
            consumed[item.item_id] += item.count
    return {
        "transaction_id": a.transaction_id,
        "actor_id": begin.actor_ids[0],
        "recipe_id": a.recipe_id,
        "item_id": a.recipe_output.item_id,
        "count": a.recipe_output.count,
        "consumed": dict(consumed),
        "server_tick": begin.server_tick,
        "resource_witness": "pass",
        "score_eligible": False,
    }
