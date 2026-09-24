/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/ExecutionAuthorization/2";
export type AuthorizationId = string;
export type DecisionId = "D11";
export type Provider = "openai";
export type AuthMode = "chatgpt_oauth" | "api_key";
/**
 * @minItems 1
 */
export type Models = [string, ...string[]];
export type TotalSpendMicrousd = number;
export type Currency = "USD";
export type Scope = "live_validation";
export type Includes = ("development" | "training" | "evaluation")[];
export type UnknownMetering = "block";
export type OriginalDecisionId = "D04";
export type LegacyAuthorizationDigest = string;
export type Schema1 = "strata/ApiEquivalentEstimateBasis/1";
export type Kind = "api_equivalent_estimate";
export type Provider1 = "openai";
export type Model = "gpt-5.6-luna" | "gpt-6-luna";
export type Currency1 = "USD";
/**
 * @minItems 1
 */
export type PriceSources = [string, ...string[]];
export type PriceDate = string;
export type ReferenceTier = "standard" | "fast" | "flex" | "batch";
export type TierPolicy = "fixed_api_equivalent_not_subscription_tier";
export type RegionalProcessing = "none";
export type Input = number;
export type CachedInput = number;
export type CacheWrite = number;
export type Output = number;
export type LongContextAboveInputTokens = number;
export type ContextWindowTokens = number;
export type MaxOutputTokens = number;
export type CacheWritePolicy = "explicit_subset_or_all_uncached_upper_bound";
export type ReasoningPolicy = "included_in_output";
export type UnknownCategories = "block";
export type ToolCharges = "unsupported_block";
export type Rounding = "ceil_per_request_microusd";
export type FirstTrialMaxMicrousd = number;

export interface ExecutionAuthorization {
  schema: Schema;
  authorization_id: AuthorizationId;
  decision_id: DecisionId;
  provider: Provider;
  auth_mode: AuthMode;
  models: Models;
  total_spend_microusd: TotalSpendMicrousd;
  currency: Currency;
  scope: Scope;
  includes: Includes;
  unknown_metering: UnknownMetering;
  original_decision_id: OriginalDecisionId;
  legacy_authorization_digest: LegacyAuthorizationDigest;
  accounting_basis: EstimateBasis;
  first_trial_max_microusd: FirstTrialMaxMicrousd;
}
export interface EstimateBasis {
  schema: Schema1;
  kind: Kind;
  provider: Provider1;
  model: Model;
  currency: Currency1;
  price_sources: PriceSources;
  price_date: PriceDate;
  reference_tier: ReferenceTier;
  tier_policy: TierPolicy;
  regional_processing: RegionalProcessing;
  short_context: TokenRates;
  long_context: TokenRates;
  long_context_above_input_tokens: LongContextAboveInputTokens;
  context_window_tokens: ContextWindowTokens;
  max_output_tokens: MaxOutputTokens;
  cache_write_policy: CacheWritePolicy;
  reasoning_policy: ReasoningPolicy;
  unknown_categories: UnknownCategories;
  tool_charges: ToolCharges;
  rounding: Rounding;
}
export interface TokenRates {
  input: Input;
  cached_input: CachedInput;
  cache_write: CacheWrite;
  output: Output;
}
