/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/EvaluationProtocol/1";
export type ProtocolId = string;
export type Visibility = "evaluator";
export type PreregisteredAt = string;
export type SystemDigests = string[];
export type SuiteDigest = string;
export type SealedInstances = string;
export type Scorer = string;
export type ExposureS = number[];
export type PrimaryCheckpointS = number;
export type ActiveWallS = number;
export type InputTokens = number;
export type OutputTokens = number;
export type ModelCalls = number;
export type PrimitiveEvents = number;
export type AvatarTicks = number;
export type PracticeWorldS = number;
export type SpendMicrousd = number | null;
export type ArtifactProjection = string;
export type ControlKeymap = string | null;
export type PrimaryEstimand = "paired_success_gain";
export type SamplePlan = string;
export type RandomizationPlan = string;
export type CensoringPlan = string;
export type Alpha = number;
export type MinEffect = number;
export type RetentionMargin = number;
export type AnalysisPlan = string;
export type AccessLog = string;

export interface EvaluationProtocol {
  is_example: IsExample;
  schema: Schema;
  protocol_id: ProtocolId;
  visibility: Visibility;
  preregistered_at: PreregisteredAt;
  system_digests: SystemDigests;
  suite_digest: SuiteDigest;
  sealed_instances: SealedInstances;
  scorer: Scorer;
  family_weights: FamilyWeights;
  exposure_s: ExposureS;
  primary_checkpoint_s: PrimaryCheckpointS;
  probe_limits: Limits;
  artifact_projection: ArtifactProjection;
  control_keymap: ControlKeymap;
  primary_estimand: PrimaryEstimand;
  sample_plan: SamplePlan;
  randomization_plan: RandomizationPlan;
  censoring_plan: CensoringPlan;
  alpha: Alpha;
  min_effect: MinEffect;
  retention_margin: RetentionMargin;
  analysis_plan: AnalysisPlan;
  access_log: AccessLog;
}
export interface FamilyWeights {
  [k: string]: number;
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
