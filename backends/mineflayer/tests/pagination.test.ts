import test from 'node:test';
import assert from 'node:assert/strict';
import { Vec3 } from 'vec3';
import type { Block } from 'prismarine-block';
import { SpatialPages, type Scene } from '../src/pagination.js';
import { ObservedMap } from '../src/observations.js';

/** Synthetic geometry/state. No live Minecraft conformance is inferred. */
function scene(count = 300, captured = 100): Scene {
  const blocks = Array.from({length: count}, (_, x) => ({position: {x, y: 0, z: 0},
    block_id: 'fixture:block', observed_at: '2026-09-18T00:00:00Z'}));
  return {state: {dimension: 'minecraft:overworld', position: {x: 0, y: 0, z: 0},
    yaw: 0, pitch: 0, health: 20, food: 20, inventory: [], window: null,
    nearby_blocks: [], nearby_entities: [], active_request_id: null, connected: true,
    truncated: false, next_cursor: null}, blocks,
    entities: blocks.map((b, i) => ({id: String(i), type: 'fixture:entity', position: b.position,
      observed_at: b.observed_at})), captured_mono_ms: captured, state_revision: 7, promote: () => {}};
}
test('pages are immutable captured regions with stable timestamps, no skips or duplicates', () => {
  let now = 100; const pages = new SpatialPages(() => now);
  const source = scene(); const offsets: number[] = []; source.promote = offset => offsets.push(offset);
  const first = pages.capture(source); assert.equal(offsets.length, 0); first.delivered!();
  assert.equal(first.state.nearby_blocks.length, 128); assert.equal(first.state.truncated, true);
  const cursor = first.state.next_cursor!;
  source.blocks[128]!.block_id = 'fixture:private_later_update'; source.state.health = 1;
  now = 600;
  const next = pages.page(cursor, 'minecraft:overworld'); next.delivered!();
  assert.equal(next.captured_mono_ms, 100); assert.equal(next.state_revision, 7);
  assert.equal(next.state.health, 20); assert.equal(next.state.nearby_blocks[0]!.block_id, 'fixture:block');
  next.state.nearby_blocks[0]!.block_id = 'fixture:caller_mutation';
  assert.equal(pages.page(cursor, 'minecraft:overworld').state.nearby_blocks[0]!.block_id, 'fixture:block');
  const last = pages.page(next.state.next_cursor!, 'minecraft:overworld'); last.delivered!();
  assert.equal(last.state.nearby_entities.length, 44); assert.equal(last.state.next_cursor, null);
  assert.equal(last.state.truncated, false); assert.deepEqual(offsets, [0, 128, 256]);
  const positions = [...first.state.nearby_blocks, ...next.state.nearby_blocks, ...last.state.nearby_blocks].map(b => b.position.x);
  assert.deepEqual(positions, Array.from({length: 300}, (_, i) => i));
});
test('cursors expire, are scoped to the worker and dimension, evict and reset', () => {
  let now = 100; const pages = new SpatialPages(() => now);
  const cursor = pages.capture(scene()).state.next_cursor!;
  assert.throws(() => pages.page(cursor, 'minecraft:the_nether'), /STALE_OBSERVATION/);
  assert.throws(() => new SpatialPages(() => now).page(cursor, 'minecraft:overworld'), /STALE_OBSERVATION/);
  for (let i = 0; i < 4; i++) pages.capture(scene());
  assert.throws(() => pages.page(cursor, 'minecraft:overworld'), /STALE_OBSERVATION/);
  const expiring = pages.capture(scene()).state.next_cursor!; now = 30100;
  assert.throws(() => pages.page(expiring, 'minecraft:overworld'), /STALE_OBSERVATION/);
  const reset = pages.capture(scene(300, now)).state.next_cursor!; pages.reset();
  assert.throws(() => pages.page(reset, 'minecraft:overworld'), /STALE_OBSERVATION/);
  assert.equal(pages.capture(scene(128, now)).state.truncated, false);
  assert.equal(pages.capture(scene(0, now)).state.next_cursor, null);
  assert.throws(() => pages.capture(scene(16385, now)), /CAPACITY_EXCEEDED/);
});
test('capturing pages does not grant the planner unseen blocks or future block updates', () => {
  const live = new Map<string, Block>();
  const map = new ObservedMap(p => {
    const k = p.toString();
    if (!live.has(k)) live.set(k, {position: p.clone(), name: p.y === 0 ? 'stone' : 'air',
      boundingBox: p.y === 0 ? 'block' : 'empty', shapes: []} as unknown as Block);
    return live.get(k)!;
  });
  const entries = map.capture(new Vec3(.43, 2.62, .57), 'minecraft:overworld');
  assert.ok(entries.length > 128);
  for (const entry of entries) assert.equal(map.blockAt(entry.block.position), null);
  map.deliver(entries.slice(0, 128), 'minecraft:overworld');
  for (const entry of entries.slice(128)) assert.equal(map.blockAt(entry.block.position), null);
  const pending = entries[128]!; const original = pending.block.name;
  live.get(pending.block.position.toString())!.name = 'private_later_update';
  map.deliver(entries.slice(128, 256), 'minecraft:overworld');
  assert.equal(map.blockAt(pending.block.position)!.name, original);
  map.deliver([{block: {...pending.block, name: 'newer'} as Block, at: '9999-01-01T00:00:00Z'}], 'minecraft:overworld');
  map.deliver([pending], 'minecraft:overworld');
  assert.equal(map.blockAt(pending.block.position)!.name, 'newer');
  map.capture(new Vec3(1000.43, 2.62, 1000.57), 'minecraft:the_nether');
  map.deliver([pending], 'minecraft:overworld');
  assert.equal(map.blockAt(pending.block.position), null);
});
