/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */

export type IsExample = boolean;
export type Schema = "mcbench/SkillRevision/1";
export type RevisionId = string;
export type AgentId = string;
export type ParentRevisionId = string | null;
export type Kind = "initial" | "notes" | "procedure" | "executable" | "handoff";
export type Content = string;
export type ProvenanceRefs = string[];
export type GeneratingCallIds = string[];
export type Origin = "initial" | "campaign" | "practice" | "probe";
export type Status = "candidate" | "active" | "rejected";
export type ActivatedAt = string | null;

export interface SkillRevision {
  is_example: IsExample;
  schema: Schema;
  revision_id: RevisionId;
  agent_id: AgentId;
  parent_revision_id: ParentRevisionId;
  kind: Kind;
  content: Content;
  provenance_refs: ProvenanceRefs;
  generating_call_ids: GeneratingCallIds;
  origin: Origin;
  status: Status;
  activated_at: ActivatedAt;
}
