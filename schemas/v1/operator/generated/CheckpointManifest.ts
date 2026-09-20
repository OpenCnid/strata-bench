/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/CheckpointManifest/1";
export type CheckpointId = string;
export type CampaignId = string;
export type ParentCheckpointId = string | null;
export type Status = "preparing" | "committed";
export type CreatedAt = string;
export type SourceEpoch = number;
export type ScheduledActiveS = number | null;
export type PackLock = string;
export type SystemDigest = string;
export type ServerBootId = string;
export type ServerTick = number;
export type WorldAndExternalState = string;
export type AgentId = string;
export type Workspace = string;
export type Skills = string;
export type Keymap = string | null;
export type BackendState = string;
export type RuntimeState = string;
export type LastActionSeq = number;
export type ModelIdentity = string | null;
export type Agents = AgentSnapshot[];
export type EventCursor = number;
export type LedgerCursor = number;
export type CleanStopReport = string;
export type ActiveWallS = number;
export type ElapsedWallS = number;
export type AvatarTicks = number;
export type ManifestDigest = string | null;

export interface CheckpointManifest {
  is_example: IsExample;
  schema: Schema;
  checkpoint_id: CheckpointId;
  campaign_id: CampaignId;
  parent_checkpoint_id: ParentCheckpointId;
  status: Status;
  created_at: CreatedAt;
  source_epoch: SourceEpoch;
  scheduled_active_s: ScheduledActiveS;
  pack_lock: PackLock;
  system_digest: SystemDigest;
  server_boot_id: ServerBootId;
  server_tick: ServerTick;
  world_and_external_state: WorldAndExternalState;
  agents: Agents;
  event_cursor: EventCursor;
  ledger_cursor: LedgerCursor;
  clean_stop_report: CleanStopReport;
  clocks: Clocks;
  manifest_digest: ManifestDigest;
}
export interface AgentSnapshot {
  agent_id: AgentId;
  workspace: Workspace;
  skills: Skills;
  keymap: Keymap;
  backend_state: BackendState;
  runtime_state: RuntimeState;
  last_action_seq: LastActionSeq;
  model_identity: ModelIdentity;
}
export interface Clocks {
  active_wall_s: ActiveWallS;
  elapsed_wall_s: ElapsedWallS;
  avatar_ticks: AvatarTicks;
}
