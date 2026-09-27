import type { RepairPlan } from './worker_repair.js';

export const REPAIR_ACCOUNTING_POLICY='durable-worker-charge-interval/1';
export type ChargeBoundary={cursor:number;mono_ms:number;unix_ms:number;primitive_events:number;sources:Record<string,number>};
export type RepairAccounting={schema:'strata/WorkerRepairAccounting/1';policy:typeof REPAIR_ACCOUNTING_POLICY;
  worker_plan:RepairPlan;clock_id:string;resume_digest:string;opening:ChargeBoundary;closing:ChargeBoundary;
  charged_primitive_events:number;elapsed_ms:number;complete_repair_accounting:false;
  avatar_ticks:null;model_usage:null;publication_tail_included:false};
