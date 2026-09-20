/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/NativeLaunch/1";
export type JobId = string;
export type CampaignId = string;
export type AgentId = string;
export type Epoch = number;
export type Role = "executor" | "helper";
export type Purpose = "campaign" | "conformance";
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
