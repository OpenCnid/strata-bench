import test from 'node:test';
import assert from 'node:assert/strict';
import { setTimeout as delay } from 'node:timers/promises';
import { Vec3 } from 'vec3';
import type { Entity } from 'prismarine-entity';
import { MineflayerBackend, ACTION_KINDS } from '../src/adapter.js';
import { ObservedEntities } from '../src/entities.js';
import { chat } from '../src/gestures.js';
import type { PrimitiveEmitter } from '../src/actions.js';
import type { Bot } from 'mineflayer';

/** The actual adapter executes against a synthetic Bot; no connection/auth is started. */
test('stock Mineflayer does not advertise or execute Forge quest UI actions',async()=>{
  const f=fixture();assert.ok(!(ACTION_KINDS as readonly string[]).includes('quest_ui'));
  await assert.rejects(f.backend.execute({kind:'quest_ui',operation:'open',source:'ftb_quests',
    source_generation:1,expected_catalog_revision:1},new AbortController().signal,f.emit),/MECHANIC_UNSUPPORTED/);
  assert.equal(f.emissions.length,0);
  assert.ok(!(ACTION_KINDS as readonly string[]).includes('quest_navigate'));
  await assert.rejects(f.backend.execute({kind:'quest_navigate',operation:'back',source:'ftb_quests',source_generation:1,
    expected_screen_generation:1,expected_screen_revision:1,selection:null},new AbortController().signal,f.emit),/MECHANIC_UNSUPPORTED/);
  assert.equal(f.emissions.length,0);
});

test('stock Mineflayer rejects item-task menu authority',async()=>{
  const f=fixture();assert.ok(!(ACTION_KINDS as readonly string[]).includes('quest_task'));
  assert.ok(!(ACTION_KINDS as readonly string[]).includes('quest_reward'));
  await assert.rejects(f.backend.execute({kind:'quest_reward',operation:'open',source:'ftb_quests',source_generation:1,
    expected_screen_generation:1,expected_screen_revision:1,selection:{revision:1,entry_id:'0000000000000003',
      query:{source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'rewards',after:0}}},
    new AbortController().signal,f.emit),/MECHANIC_UNSUPPORTED/);
  await assert.rejects(f.backend.execute({kind:'quest_task',operation:'open',source:'ftb_quests',source_generation:1,
    expected_screen_generation:1,expected_screen_revision:1,selection:{revision:1,entry_id:'0000000000000003',
      query:{source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'tasks',after:0}}},
    new AbortController().signal,f.emit),/MECHANIC_UNSUPPORTED/);
  assert.equal(f.emissions.length,0);
  assert.ok(!(ACTION_KINDS as readonly string[]).includes('quest_menu'));
  await assert.rejects(f.backend.execute({kind:'quest_menu',operation:'back',direction:null,source:'ftb_quests',source_generation:1,
    expected_menu_generation:1,expected_menu_revision:1},new AbortController().signal,f.emit),/MECHANIC_UNSUPPORTED/);
  assert.equal(f.emissions.length,0);
});

function fixture() {
  const calls: string[] = []; const emissions: string[] = [];
  const self = {id: 1, height: 1.8, position: new Vec3(0, 64, 0)} as Entity;
  const other = {id: 2, height: 1.8, position: new Vec3(2, 64, 0)} as Entity;
  const inventory = {slots: Array(46).fill(null), selectedItem: null};
  inventory.slots[45] = {name: 'shield', count: 1};
  const bot = {entity: self, entities: {1: self, 2: other} as Record<number, Entity>,
    heldItem: {name: 'apple', count: 1}, inventory, currentWindow: null, usingHeldItem: false,
    game: {dimension: 'overworld'}, supportFeature: () => false,
    activateItem(off: boolean) {calls.push(off ? 'off' : 'main'); this.usingHeldItem = true;},
    deactivateItem() {calls.push('release'); this.usingHeldItem = false;},
    clearControlStates() {}, stopDigging() {}, end() {calls.push('disconnect');},
    async lookAt() {calls.push('look');}, attack() {calls.push('attack');}, useOn() {calls.push('entity');},
    chat(text: string) {calls.push(`chat:${text}`);}};
  const entities = new ObservedEntities(); let visible = true;
  const backend = Object.assign(Object.create(MineflayerBackend.prototype), {
    bot, connected: true, entities, map: {visible: () => visible}, itemHeld: false,
    moving: false, activeEmit: null, authenticationAbort: new AbortController(),
  }) as MineflayerBackend;
  const emit: PrimitiveEmitter = kind => {emissions.push(kind ?? 'ordinary');};
  return {bot, self, other, backend, entities, calls, emissions, emit,
    hide() {visible = false;}, show() {entities.deliver([other], 'minecraft:overworld', 1);}};
}
test('use is bounded, uses the chosen hand, and releases despite an upstream flag reset', async () => {
  const f = fixture(); const start = performance.now();
  const running = f.backend.execute({kind: 'use_item', hand: 'off', hold_ms: 40}, new AbortController().signal, f.emit);
  await delay(10); f.bot.usingHeldItem = false; // unrelated upstream entity-status event
  assert.equal(await running, 'emitted');
  assert.ok(performance.now() - start >= 35);
  assert.deepEqual(f.calls, ['off', 'release']);
  assert.deepEqual(f.emissions, ['ordinary', 'safety_release']);
  f.backend.stop(); assert.deepEqual(f.calls, ['off', 'release']);
});
test('abort releases held use once, closes the connection, and never emits a late continuation', async () => {
  const f = fixture(); const cancel = new AbortController();
  const running = f.backend.execute({kind: 'use_item', hand: 'main', hold_ms: 2000}, cancel.signal, f.emit);
  const rejected = assert.rejects(running, /abort/i);
  await delay(10); const stopped = performance.now(); cancel.abort(); await rejected;
  assert.ok(performance.now() - stopped < 250);
  assert.deepEqual(f.calls, ['main', 'release', 'disconnect']);
  assert.deepEqual(f.emissions, ['ordinary', 'safety_release']);
  await delay(30); assert.equal(f.calls.length, 3);
});
test('unavailable release evidence closes the connection and missing items never activate', async () => {
  const f = fixture();
  await f.backend.execute({kind: 'use_item', hand: 'main', hold_ms: 0}, new AbortController().signal,
    kind => {if (kind === 'safety_release') throw new Error('fixture disk full');});
  assert.equal(f.backend.connected, false); assert.deepEqual(f.calls, ['main', 'disconnect']);
  const empty = fixture(); empty.bot.inventory.slots[45] = null;
  await assert.rejects(empty.backend.execute({kind: 'use_item', hand: 'off', hold_ms: 0}, new AbortController().signal, empty.emit), /PRECONDITION_FAILED/);
  assert.deepEqual(empty.calls, []);
});
test('attack and interaction require an actually delivered, visible and reachable entity identity', async () => {
  const f = fixture(); const action = {kind: 'attack', entity_id: '2'} as const;
  await assert.rejects(f.backend.execute(action, new AbortController().signal, f.emit), /PRECONDITION_FAILED/);
  assert.deepEqual(f.calls, []); f.show(); f.hide();
  await assert.rejects(f.backend.execute(action, new AbortController().signal, f.emit), /PRECONDITION_FAILED/);
  const visible = fixture(); visible.show();
  assert.equal(await visible.backend.execute(action, new AbortController().signal, visible.emit), 'emitted');
  assert.deepEqual(visible.calls, ['look', 'attack']); assert.equal(visible.emissions.length, 3);
  assert.equal(await visible.backend.execute({kind: 'interact_entity', entity_id: '2'}, new AbortController().signal, visible.emit), 'emitted');
  assert.deepEqual(visible.calls.slice(-2), ['look', 'entity']);
});
test('entity reuse, movement behind cover, dimension changes and cancellation during look fail closed', async () => {
  const f = fixture(); f.show(); f.bot.entities[2] = {...f.other} as Entity;
  await assert.rejects(f.backend.execute({kind: 'attack', entity_id: '2'}, new AbortController().signal, f.emit), /PRECONDITION_FAILED/);
  const moved = fixture(); moved.show(); moved.other.position.x = 20;
  await assert.rejects(moved.backend.execute({kind: 'attack', entity_id: '2'}, new AbortController().signal, moved.emit), /PRECONDITION_FAILED/);
  const dimension = fixture(); dimension.show(); dimension.bot.game.dimension = 'the_nether';
  await assert.rejects(dimension.backend.execute({kind: 'attack', entity_id: '2'}, new AbortController().signal, dimension.emit), /PRECONDITION_FAILED/);
  const raced = fixture(); raced.show(); raced.bot.lookAt = async () => {raced.calls.push('look'); raced.hide();};
  await assert.rejects(raced.backend.execute({kind: 'attack', entity_id: '2'}, new AbortController().signal, raced.emit), /PRECONDITION_FAILED/);
  assert.deepEqual(raced.calls, ['look']);
  const cancelled = fixture(); cancelled.show(); const abort = new AbortController();
  cancelled.bot.lookAt = async () => {abort.abort();};
  await assert.rejects(cancelled.backend.execute({kind: 'attack', entity_id: '2'}, abort.signal, cancelled.emit), /abort/i);
  assert.ok(!cancelled.calls.includes('attack'));
});
test('ordinary Unicode chat is one input; commands, controls, implicit multi-message and queued profiles reject', () => {
  const f = fixture(); const bot = f.bot as unknown as Bot;
  assert.equal(chat(bot, 'hello 世界 🌱', () => {}, f.emit), 'emitted');
  for (const text of ['/op me', '  /say x', 'one\ntwo', '\u0000', '', '🌱'.repeat(129)]) {
    assert.throws(() => chat(bot, text, () => {}, f.emit), /FORBIDDEN/);
  }
  assert.equal(f.calls.length, 1); assert.equal(f.emissions.length, 1);
  f.bot.supportFeature = () => true;
  assert.throws(() => chat(bot, 'hello', () => {}, f.emit), /MECHANIC_UNSUPPORTED/);
});
