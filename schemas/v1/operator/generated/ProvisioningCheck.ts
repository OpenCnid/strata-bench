/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/ProvisioningCheck/1";
export type IsExample = boolean;
export type RequestId = string;
export type CheckId = string;
export type Result = "pass" | "fail" | "not_run";
export type InventoryDigest = string;
export type ReceiptDigest = string;
export type LaunchProfileDigest = string;
/**
 * @minItems 1
 */
export type EvidenceRefs = [string, ...string[]];

export interface ProvisioningCheck {
  schema: Schema;
  is_example: IsExample;
  request_id: RequestId;
  check_id: CheckId;
  result: Result;
  inventory_digest: InventoryDigest;
  receipt_digest: ReceiptDigest;
  launch_profile_digest: LaunchProfileDigest;
  evidence_refs: EvidenceRefs;
}
