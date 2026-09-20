/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/ActionAck/1";
export type AgentId = string;
export type RequestId = string;
export type ActionSeq = number;
export type Status =
  "accepted" | "executing" | "completed" | "failed" | "cancelled" | "emitted" | "rejected" | "unknown";
export type EmittedEvents = number | null;
export type CompletedMonoMs = number | null;
export type ReleaseConfirmed = boolean;
export type ErrorCode = string | null;
export type RequiresResync = boolean;
export type ResultObservationId = string | null;

export interface ActionAck {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  agent_id: AgentId;
  request_id: RequestId;
  action_seq: ActionSeq;
  status: Status;
  emitted_events: EmittedEvents;
  completed_mono_ms: CompletedMonoMs;
  release_confirmed: ReleaseConfirmed;
  error_code: ErrorCode;
  requires_resync: RequiresResync;
  result_observation_id: ResultObservationId;
}
