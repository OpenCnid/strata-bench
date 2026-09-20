/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/ExecutionAuthorization/1";
export type AuthorizationId = string;
export type DecisionId = string;
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
}
