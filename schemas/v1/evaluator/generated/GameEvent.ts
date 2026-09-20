/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/GameEvent/1";
export type ServerBootId = string;
export type ServerEventSeq = number;
export type ServerTick = number;
export type Kind = string;
export type PayloadSchema = string;
export type JsonValue = unknown;
export type ActorIds = string[];
export type EvidenceRefs = string[];
export type Visibility = "evaluator";

export interface GameEvent {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  server_boot_id: ServerBootId;
  server_event_seq: ServerEventSeq;
  server_tick: ServerTick;
  kind: Kind;
  payload_schema: PayloadSchema;
  payload: Payload;
  actor_ids: ActorIds;
  evidence_refs: EvidenceRefs;
  visibility: Visibility;
}
export interface Payload {
  [k: string]: JsonValue;
}
