import { canonical, requireThat } from './protocol.js';
import { repairPlan, type RepairPlan } from './worker_repair.js';
import type { NativeLane } from './native_game.js';

export type ResumeDecision = {schema:'strata/NativeSettingsResumeDecision/1';policy:'operator-owned-settings-resume/1';
  resume_id:string;worker_plan:RepairPlan;expected_revision:number;expected_digest:string;
  completion_phase:'committed'|'rolled_back';verification_ref:string;connection_generation:number;lease_until_unix_ms:number};
export type ResumeState = {schema:'strata/NativeSettingsResumeState/1';decision:ResumeDecision;
  source_instance:string;current_instance:string;health:NativeLane;input_resumed:boolean;effects_verified_by_native:false};
const id=(x:unknown):x is string=>typeof x==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const uint=(x:unknown):x is number=>Number.isSafeInteger(x) && Number(x)>=0;
function shape(x:unknown,keys:string[]):asserts x is Record<string,unknown> {
  requireThat(x!==null && typeof x==='object' && !Array.isArray(x)
    && Object.keys(x).sort().join(',')===keys.sort().join(','),'SETTINGS_RESUME_INVALID');
}
export function resumeDecision(raw:unknown):ResumeDecision {
  shape(raw,['schema','policy','resume_id','worker_plan','expected_revision','expected_digest','completion_phase',
    'verification_ref','connection_generation','lease_until_unix_ms']);
  const plan=repairPlan(raw.worker_plan);
  requireThat(raw.schema==='strata/NativeSettingsResumeDecision/1' && raw.policy==='operator-owned-settings-resume/1'
    && id(raw.resume_id) && uint(raw.expected_revision) && raw.expected_revision>0
    && typeof raw.expected_digest==='string' && /^[a-f0-9]{64}$/.test(raw.expected_digest)
    && (raw.completion_phase==='committed'||raw.completion_phase==='rolled_back')
    && typeof raw.verification_ref==='string' && /^cas:sha256:[a-f0-9]{64}$/.test(raw.verification_ref)
    && uint(raw.connection_generation) && uint(raw.lease_until_unix_ms) && raw.lease_until_unix_ms>0
    && raw.lease_until_unix_ms<=plan.expires_unix_ms,'SETTINGS_RESUME_INVALID');
  return JSON.parse(canonical(raw)) as ResumeDecision;
}
export function resumeState(raw:unknown,validateLane:(value:unknown)=>NativeLane):ResumeState {
  shape(raw,['schema','decision','source_instance','current_instance','health','input_resumed','effects_verified_by_native']);
  const decision=resumeDecision(raw.decision),health=validateLane(raw.health);
  requireThat(raw.schema==='strata/NativeSettingsResumeState/1' && id(raw.source_instance) && id(raw.current_instance)
    && typeof raw.input_resumed==='boolean' && raw.effects_verified_by_native===false
    && (!raw.input_resumed || raw.source_instance===raw.current_instance && !health.fenced
      && health.journal_healthy && health.epoch===decision.worker_plan.epoch),'SETTINGS_RESUME_RESPONSE_INVALID');
  return JSON.parse(canonical(raw)) as ResumeState;
}
