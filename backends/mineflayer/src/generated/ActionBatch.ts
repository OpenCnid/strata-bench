/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/ActionBatch/1";
export type AgentId = string;
export type LeaseId = string;
export type RequestId = string;
export type ObservationId = string;
export type Mode = "structured" | "input";
export type ExpectedStateRevision = number;
export type CapabilityDigest = string;
export type ControlRevision = number;
export type KeymapDigest = string | null;
export type DeadlineAt = string;
export type DurationMs = number;
export type Action =
  | (
      | MoveTo
      | LookAt
      | BlockAction
      | Place
      | EntityAction
      | Equip
      | UseItem
      | ClickSlot
      | CloseWindow
      | Craft
      | QuestUi
      | QuestNavigate
      | RecipeNavigate
      | QuestTask
      | QuestReward
      | QuestMenuAction
      | Chat
    )
  | null;
export type Kind = "move_to";
export type X = number;
export type Y = number;
export type Z = number;
export type Tolerance = number;
export type Kind1 = "look_at";
export type Kind2 = "dig" | "interact_block";
export type ExpectedBlockId = string;
export type Kind3 = "place";
export type ExpectedItemId = string;
export type Kind4 = "interact_entity" | "attack";
export type EntityId = string;
export type Kind5 = "equip";
export type InventorySlot = number;
export type ExpectedItemId1 = string;
export type Destination = "hand" | "off_hand" | "head" | "torso" | "legs" | "feet";
export type Kind6 = "use_item";
export type Hand = "main" | "off";
export type HoldMs = number;
export type Kind7 = "click_slot";
export type WindowId = number;
export type ExpectedWindowRevision = number;
export type Slot = number;
export type Button = "left" | "right";
export type Mode1 = "pickup" | "quick_move";
export type Kind8 = "close_window";
export type WindowId1 = number;
export type ExpectedWindowRevision1 = number;
export type Kind9 = "craft";
export type RecipeId = string;
export type Count = number;
export type WindowId2 = number;
export type ExpectedWindowRevision2 = number;
export type Source = "jei" | "emi";
export type Category = "minecraft:crafting";
export type ItemId = string;
export type Role = "input" | "output";
export type After = number;
export type SourceGeneration = number;
export type Revision = number;
export type Kind10 = "quest_ui";
export type Operation = "open";
export type Source1 = "ftb_quests";
export type SourceGeneration1 = number;
export type ExpectedCatalogRevision = number;
export type Kind11 = "quest_navigate";
export type Operation1 = "chapter" | "quest" | "back" | "close";
export type Source2 = "ftb_quests";
export type SourceGeneration2 = number;
export type ExpectedScreenGeneration = number;
export type ExpectedScreenRevision = number;
export type Source3 = "ftb_quests";
export type ChapterId = string | null;
export type After1 = number;
export type Revision1 = number;
export type EntryId = string;
export type Kind12 = "recipe_navigate";
export type Source4 = "jei";
export type Control = "category_next" | "category_previous" | "page_next" | "page_previous" | "history_back";
export type SourceGeneration3 = number;
export type ExpectedScreenGeneration1 = number;
export type ExpectedScreenRevision1 = number;
export type ExpectedPageRevision = string;
export type Kind13 = "quest_task";
export type Operation2 = "open";
export type Source5 = "ftb_quests";
export type SourceGeneration4 = number;
export type ExpectedScreenGeneration2 = number;
export type ExpectedScreenRevision2 = number;
export type Source6 = "ftb_quests";
export type ChapterId1 = string;
export type QuestId = string;
export type After2 = number;
export type Part = "tasks" | "rewards";
export type Revision2 = number;
export type EntryId1 = string;
export type Kind14 = "quest_reward";
export type Operation3 = "open";
export type Source7 = "ftb_quests";
export type SourceGeneration5 = number;
export type ExpectedScreenGeneration3 = number;
export type ExpectedScreenRevision3 = number;
export type Revision3 = number;
export type EntryId2 = string;
export type Kind15 = "quest_menu";
export type Operation4 = "back" | "scroll";
export type Direction = ("up" | "down") | null;
export type Source8 = "ftb_quests";
export type SourceGeneration6 = number;
export type ExpectedMenuGeneration = number;
export type ExpectedMenuRevision = number;
export type Kind16 = "chat";
export type Text = string;
export type AtMs = number;
export type Kind17 = "key_down" | "key_up";
export type Backend = "glfw" | "lwjgl2" | "os";
export type Representation = "keysym" | "scancode" | "mouse_button" | "unbound";
export type Code = number | null;
export type Name = string;
export type Modifiers = ("SHIFT" | "CONTROL" | "ALT")[];
export type Persisted = string;
export type AtMs1 = number;
export type Kind18 = "pointer_absolute";
export type X1 = number;
export type Y1 = number;
export type AtMs2 = number;
export type Kind19 = "pointer_relative" | "scroll";
export type Dx = number;
export type Dy = number;
export type AtMs3 = number;
export type Kind20 = "text";
export type Text1 = string;
export type AtMs4 = number;
export type Kind21 = "wait";
/**
 * @maxItems 64
 */
export type Events = (KeyEvent | PointerAbsolute | PointerDelta | TextEvent | WaitEvent)[];
export type ReleaseAtEnd = true;

export interface ActionBatch {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  agent_id: AgentId;
  lease_id: LeaseId;
  request_id: RequestId;
  observation_id: ObservationId;
  mode: Mode;
  expected_state_revision: ExpectedStateRevision;
  capability_digest: CapabilityDigest;
  control_revision: ControlRevision;
  keymap_digest: KeymapDigest;
  deadline_at: DeadlineAt;
  duration_ms: DurationMs;
  action: Action;
  events: Events;
  release_at_end: ReleaseAtEnd;
}
export interface MoveTo {
  kind: Kind;
  target: Vec3;
  tolerance: Tolerance;
}
export interface Vec3 {
  x: X;
  y: Y;
  z: Z;
}
export interface LookAt {
  kind: Kind1;
  target: Vec3;
}
export interface BlockAction {
  kind: Kind2;
  target: Vec3;
  expected_block_id: ExpectedBlockId;
}
export interface Place {
  kind: Kind3;
  support: Vec3;
  face: Vec3;
  expected_item_id: ExpectedItemId;
}
export interface EntityAction {
  kind: Kind4;
  entity_id: EntityId;
}
export interface Equip {
  kind: Kind5;
  inventory_slot: InventorySlot;
  expected_item_id: ExpectedItemId1;
  destination: Destination;
}
export interface UseItem {
  kind: Kind6;
  hand: Hand;
  hold_ms: HoldMs;
}
export interface ClickSlot {
  kind: Kind7;
  window_id: WindowId;
  expected_window_revision: ExpectedWindowRevision;
  slot: Slot;
  button: Button;
  mode: Mode1;
}
export interface CloseWindow {
  kind: Kind8;
  window_id: WindowId1;
  expected_window_revision: ExpectedWindowRevision1;
}
export interface Craft {
  kind: Kind9;
  recipe_id: RecipeId;
  count: Count;
  window_id: WindowId2;
  expected_window_revision: ExpectedWindowRevision2;
  recipe_selection?: RecipeSelection | null;
}
export interface RecipeSelection {
  query: RecipeQuery;
  source_generation: SourceGeneration;
  revision: Revision;
}
export interface RecipeQuery {
  source: Source;
  category: Category;
  item_id: ItemId;
  role: Role;
  after: After;
}
export interface QuestUi {
  kind: Kind10;
  operation: Operation;
  source: Source1;
  source_generation: SourceGeneration1;
  expected_catalog_revision: ExpectedCatalogRevision;
}
export interface QuestNavigate {
  kind: Kind11;
  operation: Operation1;
  source: Source2;
  source_generation: SourceGeneration2;
  expected_screen_generation: ExpectedScreenGeneration;
  expected_screen_revision: ExpectedScreenRevision;
  selection: QuestSelection | null;
}
export interface QuestSelection {
  query: QuestQuery;
  revision: Revision1;
  entry_id: EntryId;
}
export interface QuestQuery {
  source: Source3;
  chapter_id: ChapterId;
  after: After1;
}
export interface RecipeNavigate {
  kind: Kind12;
  source: Source4;
  control: Control;
  source_generation: SourceGeneration3;
  expected_screen_generation: ExpectedScreenGeneration1;
  expected_screen_revision: ExpectedScreenRevision1;
  expected_page_revision: ExpectedPageRevision;
}
export interface QuestTask {
  kind: Kind13;
  operation: Operation2;
  source: Source5;
  source_generation: SourceGeneration4;
  expected_screen_generation: ExpectedScreenGeneration2;
  expected_screen_revision: ExpectedScreenRevision2;
  selection: QuestTaskSelection;
}
export interface QuestTaskSelection {
  query: QuestComponentsQuery;
  revision: Revision2;
  entry_id: EntryId1;
}
export interface QuestComponentsQuery {
  source: Source6;
  chapter_id: ChapterId1;
  quest_id: QuestId;
  after: After2;
  part: Part;
}
export interface QuestReward {
  kind: Kind14;
  operation: Operation3;
  source: Source7;
  source_generation: SourceGeneration5;
  expected_screen_generation: ExpectedScreenGeneration3;
  expected_screen_revision: ExpectedScreenRevision3;
  selection: QuestRewardSelection;
}
export interface QuestRewardSelection {
  query: QuestComponentsQuery;
  revision: Revision3;
  entry_id: EntryId2;
}
export interface QuestMenuAction {
  kind: Kind15;
  operation: Operation4;
  direction: Direction;
  source: Source8;
  source_generation: SourceGeneration6;
  expected_menu_generation: ExpectedMenuGeneration;
  expected_menu_revision: ExpectedMenuRevision;
}
export interface Chat {
  kind: Kind16;
  text: Text;
}
export interface KeyEvent {
  at_ms: AtMs;
  kind: Kind17;
  key: Key;
}
export interface Key {
  backend: Backend;
  representation: Representation;
  code: Code;
  name: Name;
  modifiers: Modifiers;
  persisted: Persisted;
}
export interface PointerAbsolute {
  at_ms: AtMs1;
  kind: Kind18;
  x: X1;
  y: Y1;
}
export interface PointerDelta {
  at_ms: AtMs2;
  kind: Kind19;
  dx: Dx;
  dy: Dy;
}
export interface TextEvent {
  at_ms: AtMs3;
  kind: Kind20;
  text: Text1;
}
export interface WaitEvent {
  at_ms: AtMs4;
  kind: Kind21;
}
