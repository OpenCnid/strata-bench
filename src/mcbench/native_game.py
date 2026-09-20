"""Private Forge development client. Not an admitted gameplay backend.

Run with python -m mcbench.native_game --connection <private file> observe.
The bridge descriptor is a credential; never copy it into gameplay or evidence exports.
"""

import argparse
import http.client
import json
import re
import time
import uuid
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, model_validator

from .client_discovery import bounded_read
from .contracts import ActionBatch, Digest, DiscoveryQuery, Id, QuestComponentsQuery, QuestMenuQuery, QuestQuery, QuestTextQuery, Strict, StructuredState, UInt
from .native_settings import (
    MAX_REQUEST, Connection, NativeSettingsClient, Response, strict_json,
)
from .storage import Fault, canonical, require

READ_OPERATIONS = ["capabilities", "observe", "identity", "observe_bound", "recipes", "recipe_query", "quests", "quest_text", "quest_components", "quest_menu", "quest_screen", "recipe_page"]
QUEST_POLICY = "ftb-visible-chapters-quests-own-team-pages32/1"
RECIPE_QUERY_POLICY = "jei-thermal-emi-crafting-visible-focus-pages32/3"
LANE_OPERATIONS = ["arm", "renew", "deliver", "act", "action_status", "cancel", "stop_all", "lane_status", "authority"]
MUTATIONS = {"arm", "renew", "deliver", "act", "cancel", "stop_all"}
ACTIONS = ["attack", "chat", "click_slot", "close_window", "craft", "dig", "equip", "interact_block", "interact_entity", "look_at", "move_to", "place", "quest_menu", "quest_navigate", "quest_reward", "quest_task", "quest_ui", "recipe_navigate", "use_item"]


class GameConnection(Connection):
    wire_schema: Literal["strata/NativeGameConnection/1"] = Field(alias="schema")


class GameResponse(Response):
    wire_schema: Literal["strata/NativeGameResponse/1"] = Field(alias="schema")


class GameCapabilities(Strict):
    wire_schema: Literal["strata/NativeGameCapabilities/1"] = Field(alias="schema")
    profile: Literal["forge1192-structured-development/1"]
    backend: Literal["forge_client"]
    track: Literal["structured-actions/v1"]
    observation_policy: Literal["opaque-voxel-fixed305-radius16/2"]
    campaign_admission: Literal[False]
    conformance: Literal["unverified"]
    operator_development_only: Literal[True]
    operations: list[str] = Field(max_length=21)
    actions: list[Literal["attack", "chat", "click_slot", "close_window", "craft", "dig", "equip", "interact_block", "interact_entity", "look_at", "move_to", "place", "quest_menu", "quest_navigate", "quest_reward", "quest_task", "quest_ui", "recipe_navigate", "use_item"]] = Field(max_length=19)
    native_action_policy: Literal["durable-intent-client-thread-nineteen-actions/2"]
    block_target_policy: Literal["observed-outline-centers64-local16/1"]
    menu_close_policy: Literal["explicit-close-own-inventory-feedback-conservation/1"]
    recipe_policy: Literal["player-book-exact-shaped-shapeless-pages32/1"]
    recipe_query_policy: Literal["jei-thermal-emi-crafting-visible-focus-pages32/3"]
    recipe_page_policy: Literal["jei-task-drawn-slot-header-controls-empty-loop/4"]
    recipe_navigation_policy: Literal["jei-current-page-controls-history-fresh-frame200/2"]
    quest_policy: Literal["ftb-visible-chapters-quests-own-team-pages32/1"]
    quest_text_policy: Literal["ftb-visible-own-quest-plain-text-pages32/1"]
    quest_components_policy: Literal["ftb-visible-own-quest-task-reward-tooltips-pages32/1"]
    quest_navigation_policy: Literal["ftb-own-team-book-and-task-recipes-state/2"]
    quest_menu_action_policy: Literal["ftb-current-item-choice-menu-back-wheel/2"]
    quest_reward_policy: Literal["ftb-visible-choice-reward-menu-open/1"]
    quest_task_policy: Literal["ftb-visible-item-task-menu-or-jei-open/2"]
    quest_open_policy: Literal["ftb-own-team-open-screen-cas/1"]
    quest_menu_policy: Literal["ftb-current-item-choice-clipped-pages32/4"]
    crafting_policy: Literal["known-recipe-fill-output-exact-metadata-reacquire/3"]
    manual_crafting_policy: Literal["visible-recipe-manual-grid-feedback-search4096/1"]
    machine_observation_policy: Literal["thermal-current-gui-energy-fluid-base-slots/1"]
    machine_inventory_policy: Literal["thermal-visible-slot-owned-transfer-feedback/2"]
    machine_input_policy: Literal["thermal-display-independent-slot-cursor-fence/1"]
    navigation_policy: Literal["delivered-shapes-level-bfs512-radius16/1"]
    collision_policy: Literal["delivered-static-vanilla-shapes-age30s/1"]
    movement_policy: Literal["level-forward-coast-neutral8-charged-ticks/1"]
    keybindings: Literal[False]
    screenshots: Literal[False]

    @model_validator(mode="after")
    def exact_operations(self):
        require(self.actions in [[], ACTIONS] and self.operations
                == READ_OPERATIONS + (LANE_OPERATIONS if self.actions else []), "GAME_RESPONSE_INVALID")
        return self


class GameSnapshot(Strict):
    wire_schema: Literal["strata/NativeGameSnapshot/1"] = Field(alias="schema")
    snapshot_id: Id
    state_revision: UInt
    source_clock_id: Id
    captured_elapsed_ms: UInt
    age_ms: UInt
    state: StructuredState

    @model_validator(mode="after")
    def observation_shape(self):
        require(self.state.connected and self.state.truncated == (self.state.next_cursor is not None),
                "GAME_RESPONSE_INVALID")
        return self


class GameAuthority(Strict):
    wire_schema: Literal["strata/NativeGameAuthority/1"] = Field(alias="schema")
    campaign_id: Id
    agent_id: Id
    capability_digest: Digest
    body_fingerprint: Digest
    expires_unix_ms: UInt
    primitive_limit: UInt = Field(ge=2)


class GameBoundSnapshot(Strict):
    wire_schema: Literal["strata/NativeBoundSnapshot/1"] = Field(alias="schema")
    snapshot: GameSnapshot
    body_fingerprint: Digest
    connection_generation: UInt


class GameIdentity(Strict):
    wire_schema: Literal["strata/NativeGameIdentity/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt


RecipeId = Annotated[str, Field(min_length=1, max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]


class GameRecipeUnknown(Strict):
    recipe_id: RecipeId
    supported: Literal[False]


class GameRecipeResult(Strict):
    item_id: RecipeId
    count: int = Field(strict=True, ge=1, le=64)


class GameRecipe(Strict):
    recipe_id: RecipeId
    supported: Literal[True]
    serializer: Literal["minecraft:crafting_shaped", "minecraft:crafting_shapeless"]
    width: int = Field(strict=True, ge=0, le=3)
    height: int = Field(strict=True, ge=0, le=3)
    ingredients: list[Annotated[list[RecipeId], Field(max_length=64)]] = Field(min_length=1, max_length=9)
    result: GameRecipeResult

    @model_validator(mode="after")
    def recipe_shape(self):
        shaped = self.serializer == "minecraft:crafting_shaped"
        require((self.width >= 1 and self.height >= 1 and len(self.ingredients) == self.width * self.height
                 if shaped else self.width == self.height == 0 and all(self.ingredients))
                and any(self.ingredients)
                and all(row == sorted(set(row)) for row in self.ingredients), "GAME_RESPONSE_INVALID")
        return self


class GameRecipeList(Strict):
    wire_schema: Literal["strata/NativeRecipeList/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    revision: UInt
    recipes: list[Annotated[GameRecipe | GameRecipeUnknown, Field(discriminator="supported")]] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=10000)] | None

    @model_validator(mode="before")
    @classmethod
    def strict_recipe_booleans(cls, value):
        # Pydantic Literal[True/False] otherwise treats integer 1/0 as equal.
        if isinstance(value, dict) and isinstance(value.get("recipes"), list):
            for entry in value["recipes"]:
                if isinstance(entry, dict):
                    require(type(entry.get("supported")) is bool, "GAME_RESPONSE_INVALID")
        return value

    @model_validator(mode="after")
    def page_shape(self):
        ids = [recipe.recipe_id for recipe in self.recipes]
        require(ids == sorted(set(ids)), "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", include={"revision", "recipes", "next_cursor"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameQueryRecipe(GameRecipe):
    craft_authority: Literal["recipe_book", "discovery_only"]


class GameQueryUnknown(GameRecipeUnknown):
    craft_authority: Literal["recipe_book", "discovery_only"]


class MachineItemChoice(GameRecipeResult):
    kind: Literal["item"]


class MachineFluidChoice(Strict):
    kind: Literal["fluid"]
    fluid_id: RecipeId
    amount_mb: int = Field(strict=True, ge=1, le=2147483647)


class MachineRecipeSlot(Strict):
    role: Literal["input", "output"]
    ingredients: list[Annotated[MachineItemChoice | MachineFluidChoice, Field(discriminator="kind")]] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def sorted_choices(self):
        ids = [row.item_id if row.kind == "item" else row.fluid_id for row in self.ingredients]
        require(ids == sorted(set(ids)), "GAME_RESPONSE_INVALID")
        return self


class MachineOutputTooltip(Strict):
    kind: Literal["chance", "additional_chance"]
    percent: int = Field(strict=True, ge=0, le=99)


class GameMachineRecipe(Strict):
    recipe_id: RecipeId
    supported: Literal[True]
    category: Literal["thermal:furnace", "thermal:crucible"]
    energy_rf: Annotated[int, Field(strict=True, ge=1, le=2147483647)] | None
    slots: list[MachineRecipeSlot] = Field(min_length=2, max_length=2)
    output_tooltip: MachineOutputTooltip | None
    craft_authority: Literal["discovery_only"]

    @model_validator(mode="after")
    def displayed_layout(self):
        inputs, outputs = self.slots
        require(inputs.role == "input" and outputs.role == "output"
                and all(choice.kind == "item" for choice in inputs.ingredients)
                and len(outputs.ingredients) == 1
                and outputs.ingredients[0].kind == ("item" if self.category == "thermal:furnace" else "fluid")
                and (self.category == "thermal:furnace" or self.output_tooltip is None), "GAME_RESPONSE_INVALID")
        return self


class GameRecipeQuery(GameRecipeList):
    wire_schema: Literal["strata/NativeRecipeQuery/1"] = Field(alias="schema")
    query: DiscoveryQuery
    source_generation: UInt
    policy: Literal["jei-thermal-emi-crafting-visible-focus-pages32/3"]
    recipes: list[GameQueryRecipe | GameMachineRecipe | GameQueryUnknown] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=512)] | None

    @model_validator(mode="after")
    def query_page_shape(self):
        for recipe in self.recipes:
            machine = self.query.category != "minecraft:crafting"
            require(not machine or recipe.craft_authority == "discovery_only", "GAME_RESPONSE_INVALID")
            if recipe.supported:
                require(isinstance(recipe, GameMachineRecipe) == machine, "GAME_RESPONSE_INVALID")
                if machine:
                    require(recipe.category == self.query.category, "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameQuestEntry(Strict):
    kind: Literal["chapter", "quest"]
    entry_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    title: Annotated[str, Field(max_length=1024)]
    progress_percent: int = Field(strict=True, ge=0, le=100)
    completed: bool = Field(strict=True)
    startable: Annotated[bool, Field(strict=True)] | None
    details_visible: Annotated[bool, Field(strict=True)] | None

    @model_validator(mode="after")
    def catalog_shape(self):
        require(len(self.title.encode("utf-8")) <= 4096
                and (not self.completed or self.progress_percent == 100), "GAME_RESPONSE_INVALID")
        if self.kind == "chapter":
            require(self.startable is None and self.details_visible is None, "GAME_RESPONSE_INVALID")
        else:
            require(self.startable is not None and self.details_visible is not None
                    and (not self.startable or self.details_visible), "GAME_RESPONSE_INVALID")
        return self


class GameQuestPage(Strict):
    wire_schema: Literal["strata/NativeQuestPage/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    query: QuestQuery
    source_generation: UInt
    policy: Literal["ftb-visible-chapters-quests-own-team-pages32/1"]
    revision: UInt
    entries: list[GameQuestEntry] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=4096)] | None

    @model_validator(mode="after")
    def page_shape(self):
        ids = [entry.entry_id for entry in self.entries]
        require(ids == sorted(set(ids)) and all(entry.kind == ("chapter" if self.query.chapter_id is None else "quest")
                for entry in self.entries), "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameQuestTextLine(Strict):
    kind: Literal["text", "page_break", "unsupported"]
    text: Annotated[str, Field(max_length=4096)] | None

    @model_validator(mode="after")
    def line_shape(self):
        require((self.kind == "text") == (self.text is not None), "GAME_RESPONSE_INVALID")
        if self.text is not None:
            require(len(self.text.encode("utf-8")) <= 16384, "GAME_RESPONSE_INVALID")
        return self


class GameQuestText(Strict):
    wire_schema: Literal["strata/NativeQuestText/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    query: QuestTextQuery
    source_generation: UInt
    policy: Literal["ftb-visible-own-quest-plain-text-pages32/1"]
    revision: UInt
    title: Annotated[str, Field(max_length=1024)]
    subtitle: Annotated[str, Field(max_length=1024)]
    description_visible: bool = Field(strict=True)
    lines: list[GameQuestTextLine] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=512)] | None

    @model_validator(mode="after")
    def text_shape(self):
        require(len(self.title.encode("utf-8")) <= 4096 and len(self.subtitle.encode("utf-8")) <= 4096,
                "GAME_RESPONSE_INVALID")
        require(self.description_visible or not self.lines and self.next_cursor is None and self.query.after == 0,
                "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameQuestTask(Strict):
    completed: bool = Field(strict=True)
    optional: bool = Field(strict=True)
    progress_label: Annotated[str, Field(max_length=256)] | None

    @model_validator(mode="after")
    def progress_text(self):
        require(self.progress_label is None or len(self.progress_label.encode("utf-8")) <= 1024, "GAME_RESPONSE_INVALID")
        return self


class GameQuestReward(Strict):
    claim_state: Literal["can_claim", "cannot_claim", "claimed"]
    team_reward: bool = Field(strict=True)


class GameQuestComponent(Strict):
    entry_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    kind: Literal["task", "reward"]
    title: Annotated[str, Field(max_length=1024)]
    tooltip: list[GameQuestTextLine] = Field(max_length=64)
    task: GameQuestTask | None
    reward: GameQuestReward | None

    @model_validator(mode="after")
    def display_shape(self):
        require(len(self.title.encode("utf-8")) <= 4096 and all(line.kind != "page_break" for line in self.tooltip)
                and (self.task is not None) == (self.kind == "task")
                and (self.reward is not None) == (self.kind == "reward"), "GAME_RESPONSE_INVALID")
        require(len(canonical(self.model_dump(mode="json"))) <= 16384, "GAME_RESPONSE_INVALID")
        return self


class GameQuestComponents(Strict):
    wire_schema: Literal["strata/NativeQuestComponents/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    query: QuestComponentsQuery
    source_generation: UInt
    policy: Literal["ftb-visible-own-quest-task-reward-tooltips-pages32/1"]
    revision: UInt
    entries: list[GameQuestComponent] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=512)] | None

    @model_validator(mode="after")
    def page_shape(self):
        ids = [entry.entry_id for entry in self.entries]
        require(ids == sorted(set(ids)) and all(entry.kind == ("task" if self.query.part == "tasks" else "reward")
                for entry in self.entries), "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameRecipeEmptyDisplay(Strict):
    kind: Literal["empty", "unsupported"]


class GameRecipeValueDisplay(Strict):
    kind: Literal["item", "fluid"]
    id: Annotated[str, Field(max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    amount: Annotated[int, Field(strict=True, ge=1, le=2147483647)]

    @model_validator(mode="after")
    def registry_name(self):
        require(re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", self.id) is not None, "GAME_RESPONSE_INVALID")
        return self


class GameRecipePageSlot(Strict):
    index: Annotated[int, Field(strict=True, ge=0, le=127)]
    role: Literal["input", "output", "catalyst", "render_only"]
    display: Annotated[GameRecipeEmptyDisplay | GameRecipeValueDisplay, Field(discriminator="kind")]


class GameRecipePageLayout(Strict):
    category_id: Annotated[str, Field(max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    clipped: bool
    slots: list[GameRecipePageSlot] = Field(max_length=128)

    @model_validator(mode="after")
    def native_order(self):
        indices = [slot.index for slot in self.slots]
        require(indices == sorted(set(indices)) and (self.clipped or indices == list(range(len(indices))))
                and re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", self.category_id) is not None, "GAME_RESPONSE_INVALID")
        return self


class GameRecipeHeader(Strict):
    kind: Literal["category", "page"]
    state: Literal["text", "clipped", "unsupported"]
    text: Annotated[str, Field(max_length=1024)] | None

    @model_validator(mode="after")
    def displayed_text(self):
        require((self.state == "text") == (self.text is not None), "GAME_RESPONSE_INVALID")
        if self.text is not None:
            require(not any(0xD800 <= ord(char) <= 0xDFFF for char in self.text)
                    and len(self.text.encode("utf-8")) <= 4096, "GAME_RESPONSE_INVALID")
        return self


class GameRecipeControl(Strict):
    kind: Literal["category_next", "category_previous", "page_next", "page_previous"]
    state: Literal["enabled", "disabled", "clipped"]


class GameRecipePage(Strict):
    wire_schema: Literal["strata/NativeRecipePage/4"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    policy: Literal["jei-task-drawn-slot-header-controls-empty-loop/4"]
    source: Literal["jei"]
    coverage: Literal["slot_header_control_draw_operands"]
    complete: Literal[False]
    source_generation: UInt
    screen_generation: UInt
    screen_revision: UInt
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    quest_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    revision: Digest
    layouts: list[GameRecipePageLayout] = Field(max_length=32)
    headers: list[GameRecipeHeader] = Field(min_length=2, max_length=2)
    controls: list[GameRecipeControl] = Field(min_length=4, max_length=4)

    @model_validator(mode="before")
    @classmethod
    def incomplete_only(cls, value):
        require(isinstance(value, dict) and value.get("complete") is False, "GAME_RESPONSE_INVALID")
        return value

    @model_validator(mode="after")
    def page_shape(self):
        import hashlib
        require([header.kind for header in self.headers] == ["category", "page"], "GAME_RESPONSE_INVALID")
        require([control.kind for control in self.controls] == ["category_next", "category_previous", "page_next", "page_previous"], "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        revision = value.pop("revision")
        require(hashlib.sha256(canonical(value)).hexdigest() == revision, "GAME_RESPONSE_INVALID")
        return self


class GameQuestScreen(Strict):
    wire_schema: Literal["strata/NativeQuestScreen/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    policy: Literal["ftb-own-team-book-and-task-recipes-state/2"]
    source_generation: UInt
    screen_generation: UInt
    revision: UInt
    kind: Literal["closed", "quest_book", "task_recipes"]
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")] | None
    quest_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")] | None

    @model_validator(mode="after")
    def screen_shape(self):
        require(self.kind != "closed" or self.chapter_id is None and self.quest_id is None, "GAME_RESPONSE_INVALID")
        require(self.quest_id is None or self.chapter_id is not None, "GAME_RESPONSE_INVALID")
        require(self.kind != "task_recipes" or self.quest_id is not None, "GAME_RESPONSE_INVALID")
        return self


class GameQuestMenuContext(Strict):
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    quest_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    task_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    title: Annotated[str, Field(max_length=1024)]


class GameQuestChoiceContext(Strict):
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    quest_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    reward_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    title: Annotated[str, Field(max_length=1024)]


class GameQuestChoiceItem(Strict):
    index: Annotated[int, Field(strict=True, ge=0, le=511)]
    title: Annotated[str, Field(max_length=1024)]
    enabled: bool = Field(strict=True)
    tooltip: list[GameQuestTextLine] = Field(max_length=64)

    @model_validator(mode="after")
    def display_shape(self):
        require(len(self.title.encode("utf-8")) <= 4096 and all(line.kind != "page_break" for line in self.tooltip)
                and len(canonical(self.model_dump(mode="json"))) <= 16384, "GAME_RESPONSE_INVALID")
        return self


class GameQuestMenuItem(Strict):
    index: Annotated[int, Field(strict=True, ge=0, le=511)]
    item_id: Annotated[str, Field(max_length=256)]
    count: Annotated[int, Field(strict=True, ge=1, le=2147483647)]
    name: Annotated[str, Field(max_length=1024)]
    tooltip: list[GameQuestTextLine] = Field(max_length=64)

    @model_validator(mode="after")
    def display_shape(self):
        require(re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", self.item_id) is not None
                and len(self.name.encode("utf-8")) <= 4096
                and all(line.kind != "page_break" for line in self.tooltip), "GAME_RESPONSE_INVALID")
        require(len(canonical(self.model_dump(mode="json"))) <= 16384, "GAME_RESPONSE_INVALID")
        return self


class GameQuestMenuControl(Strict):
    control: Literal["back", "submit"]
    title: Annotated[str, Field(max_length=1024)]
    enabled: bool = Field(strict=True)
    tooltip: list[GameQuestTextLine] = Field(max_length=64)

    @model_validator(mode="after")
    def display_shape(self):
        require(len(self.title.encode("utf-8")) <= 4096 and all(line.kind != "page_break" for line in self.tooltip)
                and len(canonical(self.model_dump(mode="json"))) <= 16384, "GAME_RESPONSE_INVALID")
        return self


class GameQuestMenu(Strict):
    wire_schema: Literal["strata/NativeQuestMenu/1"] = Field(alias="schema")
    body_fingerprint: Digest
    connection_generation: UInt
    query: QuestMenuQuery
    source_generation: UInt
    menu_generation: Annotated[int, Field(strict=True, ge=1, le=9007199254740991)]
    policy: Literal["ftb-current-item-choice-clipped-pages32/4"]
    revision: UInt
    menu_kind: Literal["item_alternatives", "reward_choices"]
    context: GameQuestMenuContext | GameQuestChoiceContext
    controls: list[GameQuestMenuControl] = Field(max_length=2)
    entries: list[GameQuestMenuItem | GameQuestChoiceItem] = Field(max_length=32)
    next_cursor: Annotated[int, Field(strict=True, ge=0, le=512)] | None

    @model_validator(mode="after")
    def page_shape(self):
        choice = self.menu_kind == "reward_choices"
        require(isinstance(self.context, GameQuestChoiceContext if choice else GameQuestMenuContext)
                and all(isinstance(row, GameQuestChoiceItem if choice else GameQuestMenuItem) for row in self.entries)
                and (not choice or not self.controls), "GAME_RESPONSE_INVALID")
        require(len(self.context.title.encode("utf-8")) <= 4096, "GAME_RESPONSE_INVALID")
        roles = [control.control for control in self.controls]
        require(len(roles) == len(set(roles)) and len(canonical([c.model_dump(mode="json") for c in self.controls])) <= 8192,
                "GAME_RESPONSE_INVALID")
        require([entry.index for entry in self.entries] == list(range(self.query.after, self.query.after + len(self.entries))),
                "GAME_RESPONSE_INVALID")
        value = self.model_dump(mode="json", exclude={"wire_schema", "body_fingerprint", "connection_generation"})
        require(len(canonical(value)) <= 32768, "GAME_RESPONSE_INVALID")
        return self


class GameLease(Strict):
    epoch: UInt
    lease_id: Id
    lease_until_unix_ms: UInt


class GameArm(GameLease):
    expected_fence_token: Id


class GameDelivery(Strict):
    observation_id: Id
    snapshot_id: Id
    state_revision: UInt


class GameRequestRef(Strict):
    request_id: Id


class GameLane(Strict):
    wire_schema: Literal["strata/NativeGameLane/1"] = Field(alias="schema")
    fenced: bool
    fence_token: Id
    reason: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    journal_healthy: bool
    epoch: UInt | None
    active_request_id: Id | None
    attempted_primitive_events: UInt
    primitive_limit: UInt

    @model_validator(mode="after")
    def fenced_state(self):
        require(self.fenced == (self.reason is not None)
                and (self.journal_healthy or self.fenced), "GAME_RESPONSE_INVALID")
        return self


class GameActionReceipt(Strict):
    wire_schema: Literal["strata/NativeGameActionReceipt/1"] = Field(alias="schema")
    request_id: Id
    epoch: UInt
    action_seq: UInt
    status: Literal["accepted", "executing", "emitted", "cancelled", "unknown", "failed"]
    attempted_events: UInt
    emitted_events: UInt | None
    release_confirmed: bool
    error_code: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")
    requires_resync: bool

    @model_validator(mode="after")
    def receipt_state(self):
        terminal = self.status not in {"accepted", "executing"}
        require(self.requires_resync == terminal
                and (self.emitted_events is None or self.emitted_events <= self.attempted_events)
                and (terminal or not self.release_confirmed and self.error_code is None)
                and (self.status not in {"failed", "cancelled", "unknown"} or self.error_code is not None)
                and (self.status != "emitted" or self.release_confirmed and self.error_code is None
                     and self.emitted_events == self.attempted_events),
                "GAME_RESPONSE_INVALID")
        return self


class GameOutcomeUnknown(Fault):
    def __init__(self, request_id: str, operation: str, action_id: str | None):
        super().__init__("GAME_OUTCOME_UNKNOWN")
        self.request_id, self.operation, self.action_id = request_id, operation, action_id


class NativeGameClient:
    """Operator client with typed payloads and session-fenced polling.

    Native elapsed time is a separate clock domain, never gateway captured_mono_ms.
    Mapping transport uncertainty and public delivery receipts is future worker work.
    """

    def __init__(self, connection: GameConnection):
        self.connection = connection
        # Share bounded HTTP/auth/strict JSON parsing; expose no settings operations.
        self._transport = NativeSettingsClient(connection)
        self._transport.response_type = GameResponse

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(GameConnection.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            raise Fault("GAME_CONNECTION_INVALID") from None

    def call(self, operation: str, args: dict, *, timeout_ms: int = 5000) -> dict:
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 30000, "GAME_DEADLINE_INVALID")
        require(operation in READ_OPERATIONS + LANE_OPERATIONS, "CAPABILITY_MISSING")
        if operation in {"observe", "observe_bound"}:
            require(set(args) == {"cursor"} and (args["cursor"] is None
                    or isinstance(args["cursor"], str)
                    and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", args["cursor"])),
                    "GAME_ARGUMENTS_INVALID")
        elif operation == "recipes":
            require(set(args) == {"after"} and type(args["after"]) is int and 0 <= args["after"] <= 10000,
                    "GAME_ARGUMENTS_INVALID")
        elif operation == "recipe_query":
            args = TypeAdapter(DiscoveryQuery).validate_python(args).model_dump(mode="json")
        elif operation == "quests":
            args = QuestQuery.model_validate(args).model_dump(mode="json")
        elif operation == "quest_text":
            args = QuestTextQuery.model_validate(args).model_dump(mode="json")
        elif operation == "quest_components":
            args = QuestComponentsQuery.model_validate(args).model_dump(mode="json")
        elif operation == "quest_menu":
            args = QuestMenuQuery.model_validate(args).model_dump(mode="json")
        elif operation in {"arm", "renew"}:
            model = GameArm if operation == "arm" else GameLease
            args = model.model_validate(args).model_dump(mode="json")
        elif operation == "deliver":
            args = GameDelivery.model_validate(args).model_dump(mode="json")
        elif operation in {"action_status", "cancel"}:
            args = GameRequestRef.model_validate(args).model_dump(mode="json")
        elif operation == "act":
            require(set(args) == {"batch"}, "GAME_ARGUMENTS_INVALID")
            batch = ActionBatch.model_validate(args["batch"])
            require(not batch.is_example and batch.mode == "structured" and batch.action.kind in ACTIONS
                    and batch.keymap_digest is None, "MECHANIC_UNSUPPORTED")
            args = {"batch": batch.model_dump(mode="json", by_alias=True)}
        else:
            require(args == {}, "GAME_ARGUMENTS_INVALID")
        request_id = str(uuid.uuid4())
        body = canonical({"schema": "strata/NativeGameRequest/1", "request_id": request_id,
            "session_id": self.connection.session_id,
            "deadline_unix_ms": int(time.time() * 1000) + timeout_ms,
            "operation": operation, "args": args})
        require(len(body) <= MAX_REQUEST, "GAME_REQUEST_TOO_LARGE")
        expires = time.monotonic() + timeout_ms / 1000
        try:
            response = self._transport._exchange("POST", "/v1/game", body, timeout_ms / 1000)
            while True:
                require(response.request_id == request_id
                        and response.session_id == self.connection.session_id,
                        "GAME_RESPONSE_IDENTITY_MISMATCH")
                if response.status == "failed":
                    raise Fault(response.error_code)
                if response.status == "completed":
                    return self._result(operation, args, response.result)
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                time.sleep(min(0.05, remaining))
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                response = self._transport._exchange("GET", "/v1/game/" + request_id, None, remaining)
        except (OSError, http.client.HTTPException, ValueError) as error:
            # No retry, no raw parser/server text (which may include private state).
            if operation in MUTATIONS:
                action_id = args.get("batch", {}).get("request_id") if operation == "act" else args.get("request_id")
                raise GameOutcomeUnknown(request_id, operation, action_id) from None
            if isinstance(error, Fault):
                raise
            raise Fault("GAME_OBSERVATION_UNAVAILABLE") from None

    def _result(self, operation: str, args: dict, value: dict) -> dict:
        model = {"observe": GameSnapshot, "capabilities": GameCapabilities, "identity": GameIdentity,
            "observe_bound": GameBoundSnapshot, "recipes": GameRecipeList, "recipe_query": GameRecipeQuery,
            "authority": GameAuthority, "quests": GameQuestPage, "quest_text": GameQuestText, "quest_components": GameQuestComponents, "quest_menu": GameQuestMenu, "quest_screen": GameQuestScreen, "recipe_page": GameRecipePage,
            "arm": GameLane, "renew": GameLane, "stop_all": GameLane, "lane_status": GameLane,
            "deliver": GameDelivery, "act": GameActionReceipt, "action_status": GameActionReceipt,
            "cancel": GameActionReceipt}[operation]
        result = model.model_validate(value).model_dump(mode="json", by_alias=True)
        if operation == "deliver":
            require(result == args, "GAME_RESPONSE_IDENTITY_MISMATCH")
        if operation in {"recipes", "recipe_query"}:
            require(result["next_cursor"] is None or len(result["recipes"]) > 0
                    and result["next_cursor"] == args["after"] + len(result["recipes"]), "GAME_RESPONSE_INVALID")
        if operation == "recipe_query":
            require(result["query"] == args, "GAME_RESPONSE_IDENTITY_MISMATCH")
            require(args["after"] + len(result["recipes"]) <= 512, "GAME_RESPONSE_INVALID")
        if operation == "quest_text":
            require(result["query"] == args and args["after"] + len(result["lines"]) <= 512
                    and (result["next_cursor"] is None or len(result["lines"]) > 0
                         and result["next_cursor"] == args["after"] + len(result["lines"])), "GAME_RESPONSE_INVALID")
        if operation in {"quests", "quest_components", "quest_menu"}:
            require(result["query"] == args and args["after"] + len(result["entries"]) <= (4096 if operation == "quests" else 512)
                    and (result["next_cursor"] is None or len(result["entries"]) > 0
                         and result["next_cursor"] == args["after"] + len(result["entries"])), "GAME_RESPONSE_INVALID")
        if operation in {"act", "action_status", "cancel"}:
            require(result["request_id"] == (args["batch"]["request_id"] if operation == "act" else args["request_id"]),
                    "GAME_RESPONSE_IDENTITY_MISMATCH")
        if operation == "act":
            require(result["epoch"] == args["batch"]["epoch"]
                    and result["action_seq"] == args["batch"]["seq"], "GAME_RESPONSE_IDENTITY_MISMATCH")
        return result

    def capabilities(self):
        return self.call("capabilities", {})

    def observe(self, cursor: str | None = None):
        return self.call("observe", {"cursor": cursor})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("operation", choices=READ_OPERATIONS + LANE_OPERATIONS)
    parser.add_argument("--cursor")
    parser.add_argument("--args", type=Path)
    args = parser.parse_args(argv)
    try:
        require(args.operation in {"observe", "observe_bound"} or args.cursor is None, "GAME_ARGUMENTS_INVALID")
        require(args.args is None or args.cursor is None, "GAME_ARGUMENTS_INVALID")
        client = NativeGameClient.from_file(args.connection)
        arguments = strict_json(bounded_read(args.args, MAX_REQUEST)) if args.args else (
            {"cursor": args.cursor} if args.operation in {"observe", "observe_bound"} else {})
        result = client.call(args.operation, arguments)
        print(json.dumps({"status": "completed", "result": result}))
    except (ValueError, OSError, http.client.HTTPException) as error:
        print(json.dumps({"status": "failed", "error_code": error.code if isinstance(error, Fault)
                          else "GAME_OPERATOR_REQUEST_INVALID"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
