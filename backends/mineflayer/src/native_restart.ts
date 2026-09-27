import { canonical, requireThat } from './protocol.js';

export type RestartCheckpoint = {schema:'strata/NativeSettingsRestartCheckpoint/1';source_instance:string;
  request:{schema:'strata/NativeSettingsRestartRequest/1';transaction_id:string;plan_digest:string;restart_id:string;
    expected_revision:number;expected_digest:string}};
export type RestartState = {schema:'strata/NativeSettingsRestartState/1';checkpoint:RestartCheckpoint;
  phase:'prepared'|'continued'|'recovery_required';current_instance:string;continued_instance:string|null;
  primitive_events:number;expires_unix_ms:number;input_resumed:false};
const id=(x:unknown):x is string=>typeof x==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const uint=(x:unknown):x is number=>Number.isSafeInteger(x) && Number(x)>=0;
const hash=(x:unknown):x is string=>typeof x==='string' && /^[a-f0-9]{64}$/.test(x);
function shape(x:unknown,keys:string[]):asserts x is Record<string,unknown> {
  requireThat(x!==null && typeof x==='object' && !Array.isArray(x)
    && Object.keys(x).sort().join(',')===keys.sort().join(','),'SETTINGS_RESTART_INVALID');
}
export function restartCheckpoint(raw:unknown):RestartCheckpoint {
  shape(raw,['schema','request','source_instance']);
  requireThat(raw.schema==='strata/NativeSettingsRestartCheckpoint/1' && id(raw.source_instance),'SETTINGS_RESTART_INVALID');
  const r=raw.request;shape(r,['schema','transaction_id','plan_digest','restart_id','expected_revision','expected_digest']);
  requireThat(r.schema==='strata/NativeSettingsRestartRequest/1' && id(r.transaction_id) && id(r.restart_id)
    && hash(r.plan_digest) && hash(r.expected_digest) && uint(r.expected_revision) && r.expected_revision>0,'SETTINGS_RESTART_INVALID');
  return JSON.parse(canonical(raw)) as RestartCheckpoint;
}
export function restartState(raw:unknown):RestartState {
  shape(raw,['schema','checkpoint','phase','current_instance','continued_instance','primitive_events','expires_unix_ms','input_resumed']);
  const checkpoint=restartCheckpoint(raw.checkpoint);
  requireThat(raw.schema==='strata/NativeSettingsRestartState/1' && ['prepared','continued','recovery_required'].includes(String(raw.phase))
    && id(raw.current_instance) && (raw.continued_instance===null || id(raw.continued_instance))
    && raw.continued_instance!==checkpoint.source_instance && uint(raw.primitive_events)
    && uint(raw.expires_unix_ms) && raw.expires_unix_ms>0 && raw.input_resumed===false
    && (raw.phase!=='prepared' || raw.continued_instance===null)
    && (raw.phase!=='continued' || raw.current_instance===raw.continued_instance),'SETTINGS_RESTART_INVALID');
  return JSON.parse(canonical(raw)) as RestartState;
}
