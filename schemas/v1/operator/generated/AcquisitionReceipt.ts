/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/AcquisitionReceipt/1";
export type IsExample = boolean;
export type RequestId = string;
export type Provider = "curseforge";
export type Target = "vanilla" | "e9e";
/**
 * @minItems 2
 * @maxItems 2
 */
export type Distributions = [DistributionInput, DistributionInput, ...DistributionInput[]];
export type Role = "client" | "server";
export type Path = string;
export type Sha256 = string;
export type Origin = string;
export type FileId = number | null;
export type LicenseRef = string;
export type EvidenceRef = string;
export type Version = string;
export type Digest = string;
export type OfficialWorkflowEvidence = string;

export interface AcquisitionReceipt {
  schema: Schema;
  is_example: IsExample;
  request_id: RequestId;
  provider: Provider;
  target: Target;
  distributions: Distributions;
  launcher: Pin;
  java: Pin;
  official_workflow_evidence: OfficialWorkflowEvidence;
}
export interface DistributionInput {
  role: Role;
  path: Path;
  sha256: Sha256;
  origin: Origin;
  file_id: FileId;
  license_ref: LicenseRef;
  evidence_ref: EvidenceRef;
}
export interface Pin {
  version: Version;
  digest: Digest;
}
