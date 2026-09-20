"""Agent-facing SPEC 9 game records. Operator records live in records.py."""

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

MAX_INT = 2**53 - 1
Id = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_.:-]{1,128}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Utc = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z$")]
UInt = Annotated[int, Field(ge=0, le=MAX_INT)]
Positive = Annotated[int, Field(ge=1, le=MAX_INT)]
Name = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", max_length=256)]
Text = Annotated[str, StringConstraints(max_length=256)]
Ref = Annotated[str, StringConstraints(pattern=r"^cas:sha256:[0-9a-f]{64}$")]


class Strict(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, allow_inf_nan=False, serialize_by_alias=True
    )

    @model_validator(mode="after")
    def valid_dates(self):
        for field in type(self).model_fields:
            value = getattr(self, field)
            if field.endswith("_at") and isinstance(value, str) and value.endswith("Z"):
                datetime.fromisoformat(value.replace("Z", "+00:00"))
        return self


class Stream(Strict):
    is_example: bool
    campaign_id: Id
    epoch: UInt
    seq: UInt
    recorded_at: Utc


class Vec3(Strict):
    x: Annotated[float, Field(ge=-30_000_000, le=30_000_000)]
    y: Annotated[float, Field(ge=-2048, le=2048)]
    z: Annotated[float, Field(ge=-30_000_000, le=30_000_000)]


class MoveTo(Strict):
    kind: Literal["move_to"]
    target: Vec3
    tolerance: Annotated[float, Field(gt=0, le=1)]


class LookAt(Strict):
    kind: Literal["look_at"]
    target: Vec3


class BlockAction(Strict):
    kind: Literal["dig", "interact_block"]
    target: Vec3
    expected_block_id: Name


class Place(Strict):
    kind: Literal["place"]
    support: Vec3
    face: Vec3
    expected_item_id: Name

    @model_validator(mode="after")
    def axis_face(self):
        coords = list(self.face.model_dump().values())
        if sorted(abs(x) for x in coords) != [0, 0, 1]:
            raise ValueError("place face must be an axis unit vector")
        return self


class EntityAction(Strict):
    kind: Literal["interact_entity", "attack"]
    entity_id: Id


class Equip(Strict):
    kind: Literal["equip"]
    inventory_slot: Annotated[int, Field(ge=0, le=45)]
    expected_item_id: Name
    destination: Literal["hand", "off_hand", "head", "torso", "legs", "feet"]


class UseItem(Strict):
    kind: Literal["use_item"]
    hand: Literal["main", "off"]
    hold_ms: Annotated[int, Field(ge=0, le=2000)]


class ClickSlot(Strict):
    kind: Literal["click_slot"]
    window_id: UInt
    expected_window_revision: UInt
    slot: Annotated[int, Field(ge=0, le=1023)]
    button: Literal["left", "right"]
    mode: Literal["pickup", "quick_move"]


class RecipeQuery(Strict):
    source: Literal["jei"]
    category: Literal["minecraft:crafting"]
    item_id: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    role: Literal["input", "output"]
    after: int = Field(strict=True, ge=0, le=512)


class RecipeSelection(Strict):
    query: RecipeQuery
    source_generation: UInt
    revision: UInt


class MachineItemRecipeQuery(Strict):
    source: Literal["jei"]
    category: Literal["thermal:furnace", "thermal:crucible"]
    item_id: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    role: Literal["input", "output"]
    after: int = Field(strict=True, ge=0, le=512)


class MachineFluidRecipeQuery(Strict):
    source: Literal["jei"]
    category: Literal["thermal:furnace", "thermal:crucible"]
    fluid_id: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    role: Literal["input", "output"]
    after: int = Field(strict=True, ge=0, le=512)


DiscoveryQuery = RecipeQuery | MachineItemRecipeQuery | MachineFluidRecipeQuery


class QuestQuery(Strict):
    source: Literal["ftb_quests"]
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")] | None
    after: int = Field(strict=True, ge=0, le=4096)


class QuestTextQuery(Strict):
    source: Literal["ftb_quests"]
    chapter_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    quest_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]
    after: int = Field(strict=True, ge=0, le=512)


class QuestComponentsQuery(QuestTextQuery):
    part: Literal["tasks", "rewards"]


class QuestMenuQuery(Strict):
    source: Literal["ftb_quests"]
    after: int = Field(strict=True, ge=0, le=512)


class Craft(Strict):
    kind: Literal["craft"]
    recipe_id: Name
    count: Annotated[int, Field(ge=1, le=64)]
    window_id: UInt
    expected_window_revision: UInt
    recipe_selection: RecipeSelection | None = None


class CloseWindow(Strict):
    kind: Literal["close_window"]
    window_id: UInt
    expected_window_revision: UInt


class QuestUi(Strict):
    kind: Literal["quest_ui"]
    operation: Literal["open"]
    source: Literal["ftb_quests"]
    source_generation: UInt
    expected_catalog_revision: UInt


class QuestSelection(Strict):
    query: QuestQuery
    revision: UInt
    entry_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]


class QuestNavigate(Strict):
    kind: Literal["quest_navigate"]
    operation: Literal["chapter", "quest", "back", "close"]
    source: Literal["ftb_quests"]
    source_generation: UInt
    expected_screen_generation: UInt
    expected_screen_revision: UInt
    selection: QuestSelection | None

    @model_validator(mode="after")
    def selection_matches_operation(self):
        if (self.operation in {"chapter", "quest"}) != (self.selection is not None):
            raise ValueError("quest selection does not match operation")
        if self.selection is not None and ((self.operation == "chapter") != (self.selection.query.chapter_id is None)):
            raise ValueError("quest catalog does not match operation")
        return self


class RecipeNavigate(Strict):
    kind: Literal["recipe_navigate"]
    source: Literal["jei"]
    control: Literal["category_next", "category_previous", "page_next", "page_previous", "history_back"]
    source_generation: UInt
    expected_screen_generation: UInt
    expected_screen_revision: UInt
    expected_page_revision: Annotated[Digest, Field(min_length=64, max_length=64)]


class QuestTaskSelection(Strict):
    query: QuestComponentsQuery
    revision: UInt
    entry_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]

    @model_validator(mode="after")
    def task_only(self):
        if self.query.part != "tasks":
            raise ValueError("task opening requires a tasks page")
        return self


class QuestTask(Strict):
    kind: Literal["quest_task"]
    operation: Literal["open"]
    source: Literal["ftb_quests"]
    source_generation: UInt
    expected_screen_generation: UInt
    expected_screen_revision: UInt
    selection: QuestTaskSelection


class QuestRewardSelection(Strict):
    query: QuestComponentsQuery
    revision: UInt
    entry_id: Annotated[str, Field(min_length=16, max_length=16, pattern=r"^[0-9A-F]{16}$")]

    @model_validator(mode="after")
    def reward_only(self):
        if self.query.part != "rewards":
            raise ValueError("reward opening requires a rewards page")
        return self


class QuestReward(Strict):
    kind: Literal["quest_reward"]
    operation: Literal["open"]
    source: Literal["ftb_quests"]
    source_generation: UInt
    expected_screen_generation: UInt
    expected_screen_revision: UInt
    selection: QuestRewardSelection


class QuestMenuAction(Strict):
    kind: Literal["quest_menu"]
    operation: Literal["back", "scroll"]
    direction: Literal["up", "down"] | None
    source: Literal["ftb_quests"]
    source_generation: UInt
    expected_menu_generation: UInt
    expected_menu_revision: UInt

    @model_validator(mode="after")
    def direction_matches_operation(self):
        if (self.operation == "scroll") != (self.direction is not None):
            raise ValueError("scroll requires direction; back forbids it")
        return self


class Chat(Strict):
    kind: Literal["chat"]
    text: Text


GameAction = Annotated[
    Union[MoveTo, LookAt, BlockAction, Place, EntityAction, Equip, UseItem, ClickSlot, CloseWindow, Craft, QuestUi, QuestNavigate, RecipeNavigate, QuestTask, QuestReward, QuestMenuAction, Chat],
    Field(discriminator="kind"),
]


class Key(Strict):
    backend: Literal["glfw", "lwjgl2", "os"]
    representation: Literal["keysym", "scancode", "mouse_button", "unbound"]
    code: UInt | None
    name: Text
    modifiers: list[Literal["SHIFT", "CONTROL", "ALT"]]
    persisted: Text

    @model_validator(mode="after")
    def physical_representation(self):
        if len(set(self.modifiers)) != len(self.modifiers):
            raise ValueError("duplicate modifiers")
        if self.representation == "unbound":
            if self.code is not None or self.modifiers:
                raise ValueError("unbound key has no code or modifiers")
        elif self.code is None:
            raise ValueError("physical key requires code; tested-pool admission is separate")
        return self


class KeyEvent(Strict):
    at_ms: UInt
    kind: Literal["key_down", "key_up"]
    key: Key


class PointerAbsolute(Strict):
    at_ms: UInt
    kind: Literal["pointer_absolute"]
    x: UInt
    y: UInt


class PointerDelta(Strict):
    at_ms: UInt
    kind: Literal["pointer_relative", "scroll"]
    dx: float
    dy: float


class TextEvent(Strict):
    at_ms: UInt
    kind: Literal["text"]
    text: Text


class WaitEvent(Strict):
    at_ms: UInt
    kind: Literal["wait"]


InputEvent = Annotated[
    Union[KeyEvent, PointerAbsolute, PointerDelta, TextEvent, WaitEvent],
    Field(discriminator="kind"),
]


class ActionBatch(Stream):
    wire_schema: Literal["mcbench/ActionBatch/1"] = Field(alias="schema")
    agent_id: Id
    lease_id: Id
    request_id: Id
    observation_id: Id
    mode: Literal["structured", "input"]
    expected_state_revision: UInt
    capability_digest: Digest
    control_revision: UInt
    keymap_digest: Digest | None
    deadline_at: Utc
    duration_ms: Annotated[int, Field(gt=0, le=30000)]
    action: GameAction | None
    events: Annotated[list[InputEvent], Field(max_length=64)]
    release_at_end: Literal[True]

    @field_validator("release_at_end", mode="before")
    @classmethod
    def literal_boolean(cls, value):
        if value is not True:
            raise ValueError("release_at_end must be the JSON boolean true")
        return value

    @model_validator(mode="after")
    def action_semantics(self):
        if self.mode == "structured":
            if self.action is None or self.events:
                raise ValueError("structured action requires exactly one action and no events")
            cap = 30000 if self.action.kind == "move_to" else 10000
            if self.duration_ms > cap:
                raise ValueError("action duration exceeds cap")
            if isinstance(self.action, UseItem) and self.action.hold_ms > self.duration_ms:
                raise ValueError("hold exceeds action duration")
        elif self.action is not None or self.duration_ms > 2000:
            raise ValueError("input mode requires null action and <=2000ms")
        if self.mode == "input":
            held = set()
            previous = 0
            for event in self.events:
                if not previous <= event.at_ms <= self.duration_ms:
                    raise ValueError("input events must be ordered within duration")
                previous = event.at_ms
                if isinstance(event, KeyEvent):
                    if event.key.representation == "unbound":
                        raise ValueError("cannot emit unbound key")
                    key = (event.key.backend, event.key.representation, event.key.code,
                           tuple(sorted(event.key.modifiers)))
                    if event.kind == "key_down":
                        if key in held:
                            raise ValueError("duplicate key down")
                        held.add(key)
                    else:
                        if key not in held:
                            raise ValueError("key up without down")
                        held.remove(key)
            if held:
                raise ValueError("unbalanced input keys")
        return self


class ItemSlot(Strict):
    slot: UInt
    item_id: Name | None
    count: UInt
    # Empty allowlist in the initial vanilla profile. Never pass raw NBT.
    component_summary: Strict


class CursorItem(Strict):
    item_id: Name
    count: Positive
    component_summary: Strict


class MachineEnergy(Strict):
    stored: Annotated[UInt, Field(le=2_147_483_647)]
    capacity: Annotated[Positive, Field(le=2_147_483_647)]

    @model_validator(mode="after")
    def within_capacity(self):
        if self.stored > self.capacity:
            raise ValueError("machine energy exceeds capacity")
        return self


class MachineFluid(Strict):
    fluid_id: Annotated[str, Field(strict=True, max_length=256, pattern=r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")]
    amount_mb: Annotated[Positive, Field(le=2_147_483_647)]


class MachineTank(Strict):
    capacity_mb: Annotated[Positive, Field(le=2_147_483_647)]
    contents: MachineFluid | None

    @model_validator(mode="after")
    def within_capacity(self):
        if self.contents is not None and self.contents.amount_mb > self.capacity_mb:
            raise ValueError("machine fluid exceeds capacity")
        return self


class MachineDisplay(Strict):
    policy: Literal["thermal-current-gui-energy-fluid-base-slots/1"]
    kind: Literal["thermal:machine_furnace", "thermal:machine_crucible"]
    energy: MachineEnergy
    tanks: Annotated[list[MachineTank], Field(max_length=1)]

    @model_validator(mode="after")
    def exact_tanks(self):
        if len(self.tanks) != (1 if self.kind == "thermal:machine_crucible" else 0):
            raise ValueError("machine tank layout mismatch")
        return self


class Window(Strict):
    id: UInt
    revision: UInt
    type: Text
    slots: Annotated[list[ItemSlot], Field(max_length=1024)]
    cursor_item: CursorItem | None = None
    machine: MachineDisplay | None = None

    @model_validator(mode="after")
    def machine_type(self):
        if self.machine is not None and self.type != self.machine.kind:
            raise ValueError("machine window type mismatch")
        return self


class SeenBlock(Strict):
    position: Vec3
    block_id: Name
    observed_at: Utc


class SeenEntity(Strict):
    id: Id
    type: Text
    position: Vec3
    observed_at: Utc


class StructuredState(Strict):
    dimension: Name
    position: Vec3
    yaw: float
    pitch: float
    health: float
    food: float
    inventory: Annotated[list[ItemSlot], Field(max_length=46)]
    window: Window | None
    nearby_blocks: Annotated[list[SeenBlock], Field(max_length=128)]
    nearby_entities: Annotated[list[SeenEntity], Field(max_length=128)]
    active_request_id: Id | None
    connected: bool
    truncated: bool
    next_cursor: Id | None


class PublicSignal(Strict):
    cursor: UInt
    kind: Literal["action", "health", "inventory", "window", "chat", "connection"]
    recorded_at: Utc
    summary: Text


class Observation(Stream):
    wire_schema: Literal["mcbench/Observation/1"] = Field(alias="schema")
    agent_id: Id
    observation_id: Id
    mode: Literal["structured", "pixels"]
    captured_mono_ms: UInt
    gateway_sent_mono_ms: UInt
    age_at_send_ms: UInt
    state_revision: UInt
    capability_digest: Digest
    state: StructuredState | None
    signals: Annotated[list[PublicSignal], Field(max_length=32)]
    event_gap: bool
    frame: Ref | None
    width: Positive | None
    height: Positive | None
    media_type: Literal["image/png", "image/jpeg"] | None
    control_revision: UInt
    keymap_digest: Digest | None
    pointer_locked: bool | None
    held_keys: list[Key]
    last_action_seq: UInt | None

    @model_validator(mode="after")
    def modes(self):
        if self.gateway_sent_mono_ms < self.captured_mono_ms:
            raise ValueError("inconsistent monotonic clock")
        if self.age_at_send_ms != self.gateway_sent_mono_ms - self.captured_mono_ms:
            raise ValueError("incorrect observation age")
        if self.mode == "structured" and self.state is None:
            raise ValueError("structured state required")
        if self.mode == "pixels" and any(
            x is None for x in (self.frame, self.width, self.height, self.media_type)
        ):
            raise ValueError("pixel frame required")
        return self


class ActionAck(Stream):
    wire_schema: Literal["mcbench/ActionAck/1"] = Field(alias="schema")
    agent_id: Id
    request_id: Id
    action_seq: UInt
    status: Literal[
        "accepted",
        "executing",
        "completed",
        "failed",
        "cancelled",
        "emitted",
        "rejected",
        "unknown",
    ]
    emitted_events: UInt | None
    completed_mono_ms: UInt | None
    release_confirmed: bool
    error_code: Id | None
    requires_resync: bool
    result_observation_id: Id | None

    @model_validator(mode="after")
    def terminal_semantics(self):
        if self.status == "unknown" and not self.requires_resync:
            raise ValueError("unknown effects require resync")
        if self.status == "completed" and (
            self.result_observation_id is None or self.completed_mono_ms is None
        ):
            raise ValueError("completion requires fresh observation and time")
        if self.status in {"failed", "cancelled"} and not (
            self.result_observation_id or self.requires_resync
        ):
            raise ValueError("partial effects need an observation or resync")
        return self


class RpcRequest(Strict):
    wire_schema: Literal["strata/GameRequest/1"] = Field(alias="schema")
    request_id: Id
    campaign_id: Id
    agent_id: Id
    epoch: UInt
    deadline_at: Utc
    method: Literal[
        "capabilities",
        "observe",
        "observe.page",
        "wait_events",
        "recipes.list",
        "recipes.query",
        "recipes.page",
        "quests.list",
        "quests.text",
        "quests.components",
        "quests.menu",
        "quests.screen",
        "act",
        "action_status",
        "cancel",
        "stop_all",
        "controls.capabilities",
        "controls.list",
        "controls.plan",
        "controls.apply",
        "controls.status",
        "controls.rollback",
    ]
    action: ActionBatch | None
    target_request_id: Id | None
    after: UInt | None
    cursor: Id | None = None
    recipe_query: DiscoveryQuery | None = None
    quest_query: QuestQuery | None = None
    quest_text_query: QuestTextQuery | None = None
    quest_components_query: QuestComponentsQuery | None = None
    quest_menu_query: QuestMenuQuery | None = None

    @model_validator(mode="after")
    def method_fields(self):
        if (self.method == "act") != (self.action is not None):
            raise ValueError("action field does not match method")
        if (self.method in {"action_status", "cancel"}) != (self.target_request_id is not None):
            raise ValueError("target field does not match method")
        if (self.method in {"wait_events", "recipes.list"}) != (self.after is not None):
            raise ValueError("event/recipe cursor does not match method")
        if (self.method == "observe.page") != (self.cursor is not None):
            raise ValueError("spatial cursor does not match method")
        if (self.method == "recipes.query") != (self.recipe_query is not None):
            raise ValueError("recipe query does not match method")
        if (self.method == "quests.list") != (self.quest_query is not None):
            raise ValueError("quest query does not match method")
        if (self.method == "quests.text") != (self.quest_text_query is not None):
            raise ValueError("quest text query does not match method")
        if (self.method == "quests.components") != (self.quest_components_query is not None):
            raise ValueError("quest components query does not match method")
        if (self.method == "quests.menu") != (self.quest_menu_query is not None):
            raise ValueError("quest menu query does not match method")
        return self


PUBLIC_RECORDS = (ActionBatch, ActionAck, Observation, RpcRequest)
