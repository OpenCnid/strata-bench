import { fields } from './native_game.js';
import { canonical, requireThat } from './protocol.js';
import { repairPlan, type RepairPlan } from './worker_repair.js';

export const PUBLICATION_POLICY='verified-controls-after-settlement/1';
export type ControlPublication={schema:'strata/WorkerControlPublication/1';policy:typeof PUBLICATION_POLICY;
  publication_id:string;worker_plan:RepairPlan;resume_digest:string;control_revision:number;keymap_digest:string;
  verification_ref:string;settlement_ref:string;primitive_events:number};
export function controlPublication(raw:unknown):ControlPublication {
  fields(raw,['schema','policy','publication_id','worker_plan','resume_digest','control_revision','keymap_digest',
    'verification_ref','settlement_ref','primitive_events']);
  const v=raw as Record<string,unknown>;
  repairPlan(v.worker_plan);
  requireThat(v.schema==='strata/WorkerControlPublication/1' && v.policy===PUBLICATION_POLICY
    && typeof v.publication_id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(v.publication_id)
    && Number.isSafeInteger(v.control_revision) && Number(v.control_revision)>0
    && Number.isSafeInteger(v.primitive_events) && Number(v.primitive_events)>=0,'CONTROL_PUBLICATION_INVALID');
  for(const key of ['resume_digest','keymap_digest'])
    requireThat(typeof v[key]==='string' && /^[a-f0-9]{64}$/.test(v[key]),'CONTROL_PUBLICATION_INVALID');
  for(const key of ['verification_ref','settlement_ref'])
    requireThat(typeof v[key]==='string' && /^cas:sha256:[a-f0-9]{64}$/.test(v[key]),'CONTROL_PUBLICATION_INVALID');
  return JSON.parse(canonical(v));
}
