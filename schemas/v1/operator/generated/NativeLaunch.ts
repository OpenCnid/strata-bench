/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/NativeLaunch/1";
export type JobId = string;
export type CampaignId = string;
export type AgentId = string;
export type Epoch = number;
export type Role = "executor" | "helper";
export type Purpose = "campaign" | "conformance" | "development_piloting";
export type ParentJobId = string | null;
export type Depth = number;
export type HelperLimit = number;
export type Account = string;
export type OperationId = string;
export type Workspace = string;
export type ProfileDirectory = string;
export type Executable = string;
export type BinaryDigest = string;
export type BinaryVersion = string;
export type DovetailCommit = string;
export type Model = string;
export type Provider = string;
export type AuthMode = "chatgpt_oauth" | "api_key";
export type BudgetMode = "whole_job" | "per_dispatch";
export type SessionStorage = "ephemeral" | "private_profile";
export type AccountingBasisDigest = string | null;
export type BrokerPolicy = "native-stdio-projected-artifacts-executor-game/1" | null;
export type BootstrapManifest = string | null;
export type BootstrapDigest = string | null;
export type IngressPolicy = "native-job-http-header/1" | null;
export type GatewayConfigDigest = string | null;
export type ToolProjectionRef = string | null;
export type ToolCatalogPolicy = ("native-selected-model-without-apply-patch/1" | "native-luna6-broker-tools/1") | null;
export type SkillActivationRef = string | null;
export type HelperSkillActivationRef = string | null;
export type ResumeComponentRef = string | null;
export type JsonValue = unknown;
export type Prompt = string;
export type HardTimeoutS = number;
export type OutputLimitBytes = number;
export type QualificationRef = string | null;

export interface NativeLaunch {
  schema: Schema;
  job_id: JobId;
  campaign_id: CampaignId;
  agent_id: AgentId;
  epoch: Epoch;
  role: Role;
  purpose?: Purpose;
  parent_job_id: ParentJobId;
  depth: Depth;
  helper_limit?: HelperLimit;
  account: Account;
  operation_id: OperationId;
  workspace: Workspace;
  profile_directory: ProfileDirectory;
  executable: Executable;
  binary_digest: BinaryDigest;
  binary_version: BinaryVersion;
  dovetail_commit: DovetailCommit;
  model: Model;
  provider?: Provider;
  auth_mode?: AuthMode;
  budget_mode?: BudgetMode;
  session_storage?: SessionStorage;
  accounting_basis_digest?: AccountingBasisDigest;
  broker_policy?: BrokerPolicy;
  bootstrap_manifest?: BootstrapManifest;
  bootstrap_digest?: BootstrapDigest;
  ingress_policy?: IngressPolicy;
  gateway_config_digest?: GatewayConfigDigest;
  tool_projection_ref?: ToolProjectionRef;
  tool_catalog_policy?: ToolCatalogPolicy;
  skill_activation_ref?: SkillActivationRef;
  helper_skill_activation_ref?: HelperSkillActivationRef;
  resume_component_ref?: ResumeComponentRef;
  config_overrides: ConfigOverrides;
  environment: Environment;
  prompt: Prompt;
  hard_timeout_s: HardTimeoutS;
  output_limit_bytes: OutputLimitBytes;
  qualification_ref: QualificationRef;
}
export interface ConfigOverrides {
  [k: string]: JsonValue;
}
export interface Environment {
  [k: string]: string;
}
