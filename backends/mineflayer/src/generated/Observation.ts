/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/Observation/1";
export type AgentId = string;
export type ObservationId = string;
export type Mode = "structured" | "pixels";
export type CapturedMonoMs = number;
export type GatewaySentMonoMs = number;
export type AgeAtSendMs = number;
export type StateRevision = number;
export type CapabilityDigest = string;
export type Dimension = string;
export type X = number;
export type Y = number;
export type Z = number;
export type Yaw = number;
export type Pitch = number;
export type Health = number;
export type Food = number;
export type Slot = number;
export type ItemId = string | null;
export type Count = number;
/**
 * @maxItems 46
 */
export type Inventory = ItemSlot[];
export type Id = number;
export type Revision = number;
export type Type = string;
/**
 * @maxItems 1024
 */
export type Slots = ItemSlot[];
export type ItemId1 = string;
export type Count1 = number;
export type Policy = "thermal-current-gui-energy-fluid-base-slots/1";
export type Kind = "thermal:machine_furnace" | "thermal:machine_crucible";
export type Stored = number;
export type Capacity = number;
export type CapacityMb = number;
export type FluidId = string;
export type AmountMb = number;
/**
 * @maxItems 1
 */
export type Tanks = MachineTank[];
export type BlockId = string;
export type ObservedAt = string;
/**
 * @maxItems 128
 */
export type NearbyBlocks = SeenBlock[];
export type Id1 = string;
export type Type1 = string;
export type ObservedAt1 = string;
/**
 * @maxItems 128
 */
export type NearbyEntities = SeenEntity[];
export type ActiveRequestId = string | null;
export type Connected = boolean;
export type Truncated = boolean;
export type NextCursor = string | null;
export type Cursor = number;
export type Kind1 = "action" | "health" | "inventory" | "window" | "chat" | "connection";
export type RecordedAt1 = string;
export type Summary = string;
/**
 * @maxItems 32
 */
export type Signals = PublicSignal[];
export type EventGap = boolean;
export type Frame = string | null;
export type Width = number | null;
export type Height = number | null;
export type MediaType = ("image/png" | "image/jpeg") | null;
export type ControlRevision = number;
export type KeymapDigest = string | null;
export type PointerLocked = boolean | null;
export type Backend = "glfw" | "lwjgl2" | "os";
export type Representation = "keysym" | "scancode" | "mouse_button" | "unbound";
export type Code = number | null;
export type Name = string;
export type Modifiers = ("SHIFT" | "CONTROL" | "ALT")[];
export type Persisted = string;
export type HeldKeys = Key[];
export type LastActionSeq = number | null;

export interface Observation {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  agent_id: AgentId;
  observation_id: ObservationId;
  mode: Mode;
  captured_mono_ms: CapturedMonoMs;
  gateway_sent_mono_ms: GatewaySentMonoMs;
  age_at_send_ms: AgeAtSendMs;
  state_revision: StateRevision;
  capability_digest: CapabilityDigest;
  state: StructuredState | null;
  signals: Signals;
  event_gap: EventGap;
  frame: Frame;
  width: Width;
  height: Height;
  media_type: MediaType;
  control_revision: ControlRevision;
  keymap_digest: KeymapDigest;
  pointer_locked: PointerLocked;
  held_keys: HeldKeys;
  last_action_seq: LastActionSeq;
}
export interface StructuredState {
  dimension: Dimension;
  position: Vec3;
  yaw: Yaw;
  pitch: Pitch;
  health: Health;
  food: Food;
  inventory: Inventory;
  window: Window | null;
  nearby_blocks: NearbyBlocks;
  nearby_entities: NearbyEntities;
  active_request_id: ActiveRequestId;
  connected: Connected;
  truncated: Truncated;
  next_cursor: NextCursor;
}
export interface Vec3 {
  x: X;
  y: Y;
  z: Z;
}
export interface ItemSlot {
  slot: Slot;
  item_id: ItemId;
  count: Count;
  component_summary: Strict;
}
export interface Strict {}
export interface Window {
  id: Id;
  revision: Revision;
  type: Type;
  slots: Slots;
  cursor_item?: CursorItem | null;
  machine?: MachineDisplay | null;
}
export interface CursorItem {
  item_id: ItemId1;
  count: Count1;
  component_summary: Strict;
}
export interface MachineDisplay {
  policy: Policy;
  kind: Kind;
  energy: MachineEnergy;
  tanks: Tanks;
}
export interface MachineEnergy {
  stored: Stored;
  capacity: Capacity;
}
export interface MachineTank {
  capacity_mb: CapacityMb;
  contents: MachineFluid | null;
}
export interface MachineFluid {
  fluid_id: FluidId;
  amount_mb: AmountMb;
}
export interface SeenBlock {
  position: Vec3;
  block_id: BlockId;
  observed_at: ObservedAt;
}
export interface SeenEntity {
  id: Id1;
  type: Type1;
  position: Vec3;
  observed_at: ObservedAt1;
}
export interface PublicSignal {
  cursor: Cursor;
  kind: Kind1;
  recorded_at: RecordedAt1;
  summary: Summary;
}
export interface Key {
  backend: Backend;
  representation: Representation;
  code: Code;
  name: Name;
  modifiers: Modifiers;
  persisted: Persisted;
}
