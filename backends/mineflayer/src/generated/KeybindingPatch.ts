/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */

export type IsExample = boolean;
export type CampaignId = string;
export type Epoch = number;
export type Seq = number;
export type RecordedAt = string;
export type Schema = "mcbench/KeybindingPatch/1";
export type AgentId = string;
export type TransactionId = string;
export type ExpectedRevision = number;
export type ExpectedKeymapDigest = string;
export type BackendFingerprint = string;
export type BindingId = string;
export type OwnerMod = string;
export type OwnerEvidence = string;
export type Contexts = string[];
export type ContextConfidence = "known" | "unknown";
export type Backend = "glfw" | "lwjgl2" | "os";
export type Representation = "keysym" | "scancode" | "mouse_button" | "unbound";
export type Code = number | null;
export type Name = string;
export type Modifiers = ("SHIFT" | "CONTROL" | "ALT")[];
export type Persisted = string;
export type Protected = boolean;
export type CompetingBindingIds = string[];
export type CandidateEvidence = string;
export type TestId = string;
export type Status = "not_run" | "pass" | "fail";
export type Refs = string[];
export type Checks = Evidence[];
export type Changes = BindingChange[];
export type BackupRef = string | null;
export type Phase = "planned" | "applying" | "verifying" | "committed" | "rolled_back" | "failed";
export type ResultingRevision = number | null;
export type ResultingKeymapDigest = string | null;
export type FailureCode = string | null;

export interface KeybindingPatch {
  is_example: IsExample;
  campaign_id: CampaignId;
  epoch: Epoch;
  seq: Seq;
  recorded_at: RecordedAt;
  schema: Schema;
  agent_id: AgentId;
  transaction_id: TransactionId;
  expected_revision: ExpectedRevision;
  expected_keymap_digest: ExpectedKeymapDigest;
  backend_fingerprint: BackendFingerprint;
  changes: Changes;
  backup_ref: BackupRef;
  phase: Phase;
  resulting_revision: ResultingRevision;
  resulting_keymap_digest: ResultingKeymapDigest;
  restart_check: Evidence;
  failure_code: FailureCode;
}
export interface BindingChange {
  binding_id: BindingId;
  owner_mod: OwnerMod;
  owner_evidence: OwnerEvidence;
  contexts: Contexts;
  context_confidence: ContextConfidence;
  before: Key;
  after: Key;
  protected: Protected;
  competing_binding_ids: CompetingBindingIds;
  candidate_evidence: CandidateEvidence;
  checks: Checks;
}
export interface Key {
  backend: Backend;
  representation: Representation;
  code: Code;
  name: Name;
  modifiers: Modifiers;
  persisted: Persisted;
}
export interface Evidence {
  test_id: TestId;
  status: Status;
  refs: Refs;
}
