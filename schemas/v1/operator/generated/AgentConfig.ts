/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/AgentConfig/1";
export type AgentId = string;
export type SystemDigest = string;
export type Version = string;
export type Digest = string;
export type Provider = string;
export type RequestedModel = string;
export type ImmutableModelId = string | null;
export type IdentityAssurance = "immutable" | "provider_version_unverified";
export type InferenceConfig = string;
export type DovetailCommit = string;
export type DovetailVersion = string;
export type InitialSkills = string;
export type LearnedOverlay = string | null;
export type MemoryPolicy = string;
export type CapabilityProfile = string;
export type AccountRef = string;
export type ProviderAuthRef = string;
export type HelperLimit = number;
export type HelperDepth = number;
export type SelfPlay = boolean;
export type ResumeMode = "session" | "fresh_handoff";

export interface AgentConfig {
  is_example: IsExample;
  schema: Schema;
  agent_id: AgentId;
  system_digest: SystemDigest;
  runtime: Pin;
  provider: Provider;
  requested_model: RequestedModel;
  immutable_model_id: ImmutableModelId;
  identity_assurance: IdentityAssurance;
  inference_config: InferenceConfig;
  dovetail_commit: DovetailCommit;
  dovetail_version: DovetailVersion;
  initial_skills: InitialSkills;
  learned_overlay: LearnedOverlay;
  memory_policy: MemoryPolicy;
  capability_profile: CapabilityProfile;
  account_ref: AccountRef;
  provider_auth_ref: ProviderAuthRef;
  helper_limit: HelperLimit;
  helper_depth: HelperDepth;
  self_play: SelfPlay;
  resume_mode: ResumeMode;
}
export interface Pin {
  version: Version;
  digest: Digest;
}
