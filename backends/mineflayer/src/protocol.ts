import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import * as compiled from './schema_validators.js';
import type { ActionBatch } from './generated/ActionBatch.js';
import type { Observation } from './generated/Observation.js';
import { requireThat } from './errors.js';
export { Fault, requireThat, errorBody } from './errors.js';
export type { ActionBatch } from './generated/ActionBatch.js';
export type { ActionAck } from './generated/ActionAck.js';
export type { Observation, StructuredState, Vec3 } from './generated/Observation.js';
export type { PublicSignal } from './generated/Observation.js';
export type { RpcRequest } from './generated/RpcRequest.js';
export type Action = NonNullable<ActionBatch['action']>;

const validators = new Map<string, (value: unknown) => boolean>();
for (const [name, expected] of Object.entries(compiled.schemaHashes)) {
  const bytes = readFileSync(new URL(`../../../../schemas/v1/public/${name}.json`, import.meta.url));
  requireThat(createHash('sha256').update(bytes).digest('hex') === expected, 'SCHEMA_BUILD_STALE');
  validators.set(name, compiled[name as keyof typeof compiled.schemaHashes] as (value: unknown) => boolean);
}

export function validate<T>(name: string, value: unknown): T {
  requireThat(validators.get(name)?.(value), 'SCHEMA_UNSUPPORTED');
  if (name === 'Observation') {
    const window = (value as Observation).state?.window;
    const machine = window?.machine;
    if (machine) {
      requireThat(window!.type === machine.kind && machine.energy.stored <= machine.energy.capacity
        && machine.tanks.length === (machine.kind === 'thermal:machine_crucible' ? 1 : 0)
        && machine.tanks.every(tank => tank.contents === null || tank.contents.amount_mb <= tank.capacity_mb), 'SCHEMA_UNSUPPORTED');
    }
  }
  return value as T;
}
export function canonical(value: unknown): string {
  if (typeof value === 'number') {
    requireThat(Number.isFinite(value), 'SCHEMA_UNSUPPORTED');
    // Counts are schema-bounded; other numeric fields use interoperable IEEE-754.
    return JSON.stringify(value);
  }
  if (typeof value === 'string') {
    requireThat(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/.test(value), 'SCHEMA_UNSUPPORTED');
    return JSON.stringify(value);
  }
  if (value === null || typeof value === 'boolean') return JSON.stringify(value);
  requireThat(typeof value === 'object', 'SCHEMA_UNSUPPORTED');
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  const obj = value as Record<string, unknown>;
  return `{${Object.keys(obj).sort().map(k => `${canonical(k)}:${canonical(obj[k])}`).join(',')}}`;
}
export const digest = (x: unknown): string => createHash('sha256').update(canonical(x)).digest('hex');
export const mono = (): number => Math.floor(performance.now());
export const utc = (): string => new Date().toISOString();
export function actionSemantics(b: ActionBatch): void {
  requireThat(!b.is_example, 'PRECONDITION_FAILED');
  requireThat(b.mode === 'structured' && b.action !== null && b.events.length === 0, 'CAPABILITY_MISSING');
  requireThat(b.keymap_digest === null, 'CAPABILITY_MISSING');
  const a = b.action;
  requireThat(b.duration_ms <= (a.kind === 'move_to' ? 30000 : 10000), 'PRECONDITION_FAILED');
  if (a.kind === 'use_item') requireThat(a.hold_ms <= b.duration_ms, 'PRECONDITION_FAILED');
  if(a.kind==='quest_menu')requireThat((a.operation==='scroll')===(a.direction!==null),'PRECONDITION_FAILED');
  if(a.kind==='quest_task')requireThat(a.selection.query.part==='tasks','PRECONDITION_FAILED');
  if(a.kind==='quest_reward')requireThat(a.selection.query.part==='rewards','PRECONDITION_FAILED');
  if(a.kind==='quest_navigate') {
    requireThat(['chapter','quest'].includes(a.operation)===(a.selection!==null),'PRECONDITION_FAILED');
    if(a.selection!==null)requireThat((a.operation==='chapter')===(a.selection.query.chapter_id===null),'PRECONDITION_FAILED');
  }
  if (a.kind === 'place') {
    requireThat([a.face.x, a.face.y, a.face.z].map(Math.abs).sort().join(',') === '0,0,1', 'PRECONDITION_FAILED');
  }
  if (a.kind === 'chat') requireThat(!/[\r\n\u0000-\u001f\u007f]/u.test(a.text) && !a.text.trimStart().startsWith('/'), 'FORBIDDEN');
  requireThat(Number.isFinite(Date.parse(b.deadline_at)), 'SCHEMA_UNSUPPORTED');
}
