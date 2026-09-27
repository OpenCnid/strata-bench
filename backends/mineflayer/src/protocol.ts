import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import * as compiled from './schema_validators.js';
import type { ActionBatch, Key } from './generated/ActionBatch.js';
import type { ActionAck } from './generated/ActionAck.js';
import type { Observation } from './generated/Observation.js';
import type { KeybindingPatch } from './generated/KeybindingPatch.js';
import type { SkillRevision } from './generated/SkillRevision.js';
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
  if (name === 'ActionBatch') actionContract(value as ActionBatch);
  if (name === 'ActionAck') {
    const ack = value as ActionAck;
    recordDate(ack.recorded_at);
    requireThat(ack.status !== 'unknown' || ack.requires_resync, 'SCHEMA_UNSUPPORTED');
    requireThat(ack.status !== 'completed' || ack.result_observation_id !== null
      && ack.completed_mono_ms !== null, 'SCHEMA_UNSUPPORTED');
    requireThat(!['failed', 'cancelled'].includes(ack.status) || ack.result_observation_id !== null
      || ack.requires_resync, 'SCHEMA_UNSUPPORTED');
  }
  if (name === 'SkillRevision') {
    const activated = (value as SkillRevision).activated_at;
    if (activated !== null) recordDate(activated);
  }
  if (name === 'KeybindingPatch') {
    const patch = value as KeybindingPatch;
    recordDate(patch.recorded_at);
    requireThat(new Set(patch.changes.map(change => change.binding_id)).size === patch.changes.length,
      'SCHEMA_UNSUPPORTED');
    if (patch.phase === 'committed') requireThat(patch.resulting_revision! > patch.expected_revision,
      'SCHEMA_UNSUPPORTED');
    for (const change of patch.changes) for (const key of [change.before, change.after]) keyContract(key);
  }
  if (name === 'Observation') {
    const observation = value as Observation;
    recordDate(observation.recorded_at);
    for (const signal of observation.signals) recordDate(signal.recorded_at);
    for (const seen of [...(observation.state?.nearby_blocks ?? []), ...(observation.state?.nearby_entities ?? [])])
      recordDate(seen.observed_at);
    for (const key of observation.held_keys) keyContract(key);
    requireThat(observation.gateway_sent_mono_ms >= observation.captured_mono_ms
      && observation.age_at_send_ms === observation.gateway_sent_mono_ms - observation.captured_mono_ms,
    'SCHEMA_UNSUPPORTED');
    requireThat(observation.mode !== 'structured' || observation.state !== null, 'SCHEMA_UNSUPPORTED');
    requireThat(observation.mode !== 'pixels' || [observation.frame, observation.width,
      observation.height, observation.media_type].every(value => value !== null), 'SCHEMA_UNSUPPORTED');
    const window = observation.state?.window;
    const machine = window?.machine;
    if (machine) {
      requireThat(window!.type === machine.kind && machine.energy.stored <= machine.energy.capacity
        && machine.tanks.length === (machine.kind === 'thermal:machine_crucible' ? 1 : 0)
        && machine.tanks.every(tank => tank.contents === null || tank.contents.amount_mb <= tank.capacity_mb), 'SCHEMA_UNSUPPORTED');
    }
  }
  return value as T;
}
function recordDate(value: string): void {
  const date = new Date(value);
  requireThat(Number.isFinite(date.getTime()) && Number(value.slice(0, 4)) > 0
    && date.toISOString().slice(0, 19) === value.slice(0, 19), 'SCHEMA_UNSUPPORTED');
}
function keyContract(key: Key): void {
  requireThat(new Set(key.modifiers).size === key.modifiers.length, 'SCHEMA_UNSUPPORTED');
  requireThat(key.representation === 'unbound' ? key.code === null && key.modifiers.length === 0
    : key.code !== null, 'SCHEMA_UNSUPPORTED');
}
/** Wire semantics only: this does not admit input mode or grant a capability. */
function actionContract(batch: ActionBatch): void {
  recordDate(batch.recorded_at); recordDate(batch.deadline_at);
  // Key constraints also apply to events in an otherwise invalid mode.
  for (const event of batch.events) if ('key' in event) keyContract(event.key);
  if (batch.mode === 'structured') {
    requireThat(batch.action !== null && batch.events.length === 0, 'SCHEMA_UNSUPPORTED');
    const action = batch.action!;
    requireThat(batch.duration_ms <= (action.kind === 'move_to' ? 30000 : 10000), 'SCHEMA_UNSUPPORTED');
    if (action.kind === 'use_item') requireThat(action.hold_ms <= batch.duration_ms, 'SCHEMA_UNSUPPORTED');
  } else {
    requireThat(batch.action === null && batch.duration_ms <= 2000, 'SCHEMA_UNSUPPORTED');
    let previous = 0;
    const held = new Set<string>();
    for (const event of batch.events) {
      requireThat(previous <= event.at_ms && event.at_ms <= batch.duration_ms, 'SCHEMA_UNSUPPORTED');
      previous = event.at_ms;
      if ('key' in event) {
        requireThat(event.key.representation !== 'unbound', 'SCHEMA_UNSUPPORTED');
        const key = JSON.stringify([event.key.backend, event.key.representation, event.key.code,
          [...event.key.modifiers].sort()]);
        requireThat(event.kind === 'key_down' ? !held.has(key) : held.has(key), 'SCHEMA_UNSUPPORTED');
        if (event.kind === 'key_down') held.add(key); else held.delete(key);
      }
    }
    requireThat(held.size === 0, 'SCHEMA_UNSUPPORTED');
  }
  const action = batch.action;
  if (action?.kind === 'place') requireThat([action.face.x, action.face.y, action.face.z]
    .map(Math.abs).sort().join(',') === '0,0,1', 'SCHEMA_UNSUPPORTED');
  if (action?.kind === 'quest_menu') requireThat((action.operation === 'scroll') === (action.direction !== null), 'SCHEMA_UNSUPPORTED');
  if (action?.kind === 'quest_task') requireThat(action.selection.query.part === 'tasks', 'SCHEMA_UNSUPPORTED');
  if (action?.kind === 'quest_reward') requireThat(action.selection.query.part === 'rewards', 'SCHEMA_UNSUPPORTED');
  if (action?.kind === 'quest_navigate') {
    requireThat(['chapter', 'quest'].includes(action.operation) === (action.selection !== null), 'SCHEMA_UNSUPPORTED');
    if (action.selection !== null) requireThat((action.operation === 'chapter') ===
      (action.selection.query.chapter_id === null), 'SCHEMA_UNSUPPORTED');
  }
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
