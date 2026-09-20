/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/EvaluationResult/1";
export type ResultId = string;
export type ProtocolId = string;
export type Visibility = "evaluator";
export type LineageId = string;
export type CheckpointId = string;
export type PairId = string;
export type InstanceId = string;
export type Arm = "experienced" | "initial";
export type Outcome = "success" | "failure" | "censored" | "invalid";
export type Success = boolean | null;
export type Progress = number | null;
export type ActiveTimeS = number;
export type EventObserved = boolean;
export type CensorReason = string | null;
export type Scores = string;
export type EvidenceRefs = string[];
export type BudgetLedgerRef = string;
export type ValidityFlags = string[];
export type ScoredAt = string;

export interface EvaluationResult {
  is_example: IsExample;
  schema: Schema;
  result_id: ResultId;
  protocol_id: ProtocolId;
  visibility: Visibility;
  lineage_id: LineageId;
  checkpoint_id: CheckpointId;
  pair_id: PairId;
  instance_id: InstanceId;
  arm: Arm;
  outcome: Outcome;
  success: Success;
  progress: Progress;
  active_time_s: ActiveTimeS;
  event_observed: EventObserved;
  censor_reason: CensorReason;
  scores: Scores;
  evidence_refs: EvidenceRefs;
  budget_ledger_ref: BudgetLedgerRef;
  validity_flags: ValidityFlags;
  scored_at: ScoredAt;
}
