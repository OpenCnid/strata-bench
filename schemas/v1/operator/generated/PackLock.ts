/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type IsExample = boolean;
export type Schema = "mcbench/PackLock/1";
export type LockId = string;
export type Status = "candidate" | "sealed";
export type Provider = "curseforge";
export type PackSlug = string;
export type Release = string;
export type ProjectId = number | null;
export type ClientFileId = number | null;
export type ServerFileId = number | null;
export type Minecraft = string;
export type Name = "forge" | "none";
export type Version = string | null;
export type SourceRevision = string | null;
export type DistributionRefs = string[];
export type ResolvedInventory = string | null;
export type InstalledRootDigest = string | null;
export type Version1 = string;
export type Digest = string;
export type LaunchProfile = string | null;
export type ExpertAssertions = string | null;
export type HarnessAdditions = string[];
export type AcquisitionReport = string | null;
export type SealedAt = string | null;

export interface PackLock {
  is_example: IsExample;
  schema: Schema;
  lock_id: LockId;
  status: Status;
  provider: Provider;
  pack_slug: PackSlug;
  release: Release;
  project_id: ProjectId;
  client_file_id: ClientFileId;
  server_file_id: ServerFileId;
  minecraft: Minecraft;
  loader: Loader;
  source_revision: SourceRevision;
  distribution_refs: DistributionRefs;
  resolved_inventory: ResolvedInventory;
  installed_root_digest: InstalledRootDigest;
  java: Pin | null;
  launcher: Pin | null;
  launch_profile: LaunchProfile;
  expert_assertions: ExpertAssertions;
  harness_additions: HarnessAdditions;
  acquisition_report: AcquisitionReport;
  sealed_at: SealedAt;
}
export interface Loader {
  name: Name;
  version: Version;
}
export interface Pin {
  version: Version1;
  digest: Digest;
}
