/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/CampaignConfig/1";
export type CampaignId = string;
export type LineageId = string;
export type CohortId = string;
export type SystemDigest = string;
export type PackLock = string;
export type ProtocolRef = string;
export type WorldBaseline = string;
export type Track = "structured-actions/v1" | "pixels-input-settings/v1" | "pixels-os/v1" | "semantic-assisted/v1";
export type Kind = "mineflayer" | "forge_client" | "os_input";
export type Version = string;
export type Digest = string;
export type CapabilityManifest = string;
export type N = number;
export type AgentIds = string[];
export type Topology = "shared_cooperative";
export type InformationPolicy = string;
export type CommunicationPolicy = string;
export type RuntimeProfile = string;
export type BudgetPolicy = "fixed_team" | "fixed_per_agent";
export type ActiveWallS = number;
export type InputTokens = number;
export type OutputTokens = number;
export type ModelCalls = number;
export type PrimitiveEvents = number;
export type AvatarTicks = number;
export type PracticeWorldS = number;
export type SpendMicrousd = number | null;
export type CheckpointsActiveS = number[];
export type EpisodeS = number;
export type CheckpointPeriodS = number;
export type Admission = "queue" | "reject";
export type DriftPolicy = "split_quarantine";
export type RecoveryPolicy = "terminate_confirmatory" | "resume_development";

export interface CampaignConfig {
  is_example: IsExample;
  schema: Schema;
  campaign_id: CampaignId;
  lineage_id: LineageId;
  cohort_id: CohortId;
  system_digest: SystemDigest;
  pack_lock: PackLock;
  protocol_ref: ProtocolRef;
  world_baseline: WorldBaseline;
  track: Track;
  backend: BackendProfile;
  n: N;
  agent_ids: AgentIds;
  topology: Topology;
  information_policy: InformationPolicy;
  communication_policy: CommunicationPolicy;
  runtime_profile: RuntimeProfile;
  budget_policy: BudgetPolicy;
  training_team_limits: Limits;
  per_agent_limits: Limits;
  evaluation_limits: Limits;
  checkpoints_active_s: CheckpointsActiveS;
  episode_s: EpisodeS;
  checkpoint_period_s: CheckpointPeriodS;
  admission: Admission;
  drift_policy: DriftPolicy;
  recovery_policy: RecoveryPolicy;
}
export interface BackendProfile {
  kind: Kind;
  implementation: Pin;
  capability_manifest: CapabilityManifest;
}
export interface Pin {
  version: Version;
  digest: Digest;
}
export interface Limits {
  active_wall_s: ActiveWallS;
  input_tokens: InputTokens;
  output_tokens: OutputTokens;
  model_calls: ModelCalls;
  primitive_events: PrimitiveEvents;
  avatar_ticks: AvatarTicks;
  practice_world_s: PracticeWorldS;
  spend_microusd: SpendMicrousd;
}
