/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Role = "client" | "server";
export type Root = string;
/**
 * @minItems 1
 * @maxItems 200000
 */
export type Files = [FileEntry, ...FileEntry[]];
export type Path = string;
export type Digest = string;
export type Bytes = number;
export type Role1 = "client" | "server" | "both";
export type Origin = string;
export type ProjectId = number | null;
export type FileId = number | null;
export type LicenseRef = string | null;
export type Layer = "distribution" | "resolved" | "harness";
export type ProvenanceEvidence = string;
export type ExclusionsEvidence = string;

export interface RoleInventoryInput {
  role: Role;
  root: Root;
  files: Files;
  provenance_evidence: ProvenanceEvidence;
  exclusions_evidence: ExclusionsEvidence;
}
export interface FileEntry {
  path: Path;
  digest: Digest;
  bytes: Bytes;
  role: Role1;
  origin: Origin;
  project_id: ProjectId;
  file_id: FileId;
  license_ref: LicenseRef;
  layer: Layer;
}
