/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/BudgetLedger/1";
export type LedgerId = string;
export type CampaignAccount = "training" | "evaluation" | "development";
export type AgentId = string | null;
export type OperationId = string;
export type ParentOperationId = string | null;
export type SourceEventId = string;
export type Posting = "reserve" | "settle" | "adjust";
export type Kind = "model" | "helper" | "tool" | "practice" | "body" | "infrastructure";
export type InputTokens = number;
export type CachedInputTokens = number;
export type OutputTokens = number;
export type ReasoningTokens = number | null;
export type ModelCalls = number;
export type PrimitiveEvents = number;
export type AvatarTicks = number;
export type WallMs = number;
export type SpendMicrousd = number | null;
export type Metering = "reported" | "estimated" | "unknown";
export type PricingRef = string | null;
export type ModelIdentity = string | null;
export type RawUsageRef = string | null;
export type Reason = string;

export interface BudgetLedger {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  ledger_id: LedgerId;
  campaign_account: CampaignAccount;
  agent_id: AgentId;
  operation_id: OperationId;
  parent_operation_id: ParentOperationId;
  source_event_id: SourceEventId;
  posting: Posting;
  kind: Kind;
  usage: Usage;
  metering: Metering;
  pricing_ref: PricingRef;
  model_identity: ModelIdentity;
  raw_usage_ref: RawUsageRef;
  reason: Reason;
}
export interface Usage {
  input_tokens: InputTokens;
  cached_input_tokens: CachedInputTokens;
  output_tokens: OutputTokens;
  reasoning_tokens: ReasoningTokens;
  model_calls: ModelCalls;
  primitive_events: PrimitiveEvents;
  avatar_ticks: AvatarTicks;
  wall_ms: WallMs;
  spend_microusd: SpendMicrousd;
}
