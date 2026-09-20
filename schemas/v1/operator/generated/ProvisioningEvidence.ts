/* Operator-only generated binding. Never ship in a gameplay workspace. */

export type Schema = "strata/ProvisioningEvidence/1";
export type IsExample = boolean;
export type RequestId = string;
export type InventoryDigest = string;
export type ReceiptDigest = string;
export type LaunchProfileDigest = string;

export interface ProvisioningEvidence {
  schema: Schema;
  is_example: IsExample;
  request_id: RequestId;
  inventory_digest: InventoryDigest;
  receipt_digest: ReceiptDigest;
  launch_profile_digest: LaunchProfileDigest;
  checks: Checks;
}
export interface Checks {
  [k: string]: string;
}
