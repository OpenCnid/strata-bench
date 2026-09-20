import test from 'node:test';
import assert from 'node:assert/strict';
import type { Bot } from 'mineflayer';
import loadWindows, { type Window } from 'prismarine-windows';
import loadItems, { type Item } from 'prismarine-item';
import minecraftData from 'minecraft-data';
import { EventEmitter } from 'node:events';
import { equip, InventoryMotor } from '../src/inventory_motor.js';
import { trackCursor } from '../src/inventory_feedback.js';

/** Pinned library prediction plus an independent synthetic server copy, not a live server. */
const windows = (loadWindows as unknown as (version: string) => {
  createWindow(id: number, type: string, title: string): Window;
})('1.19.2');
const Items = (loadItems as unknown as (version: string) => typeof Item)('1.19.2');
const data = minecraftData('1.19.2');
const item = (name: string, count = 1) => new Items(data.itemsByName[name]!.id, count);
const clone = (item: Item | null) => item ? new Items(item.type, item.count, item.metadata, structuredClone(item.nbt) ?? undefined) : null;
function fixture(type = 'minecraft:inventory') {
  const inventory = windows.createWindow(0, 'minecraft:inventory', 'fixture');
  const local = type === 'minecraft:inventory' ? inventory : windows.createWindow(1, type, 'fixture');
  const server = windows.createWindow(local.id, type, 'server fixture');
  let emitted = 0; let syncs = 0; let alive = true; let accept = true;
  const calls: number[][] = [];
  let beforeSync: (() => void) | undefined;
  const fake = {inventory, currentWindow: local === inventory ? null : local, quickBarSlot: 0,
    get heldItem() { return inventory.slots[36 + this.quickBarSlot]; },
    setQuickBarSlot(slot: number) { this.quickBarSlot = slot; },
    async clickWindow(slot: number, mouseButton: number, mode: number) {
      calls.push([slot, mouseButton, mode]);
      const predicted = {slot, mouseButton, mode, item: local.slots[slot]!};
      const authoritative = {slot, mouseButton, mode, item: server.slots[slot]!};
      local.acceptClick(predicted, 0);
      if (accept) server.acceptClick(authoritative, 0);
    },
    async _syncWindow(window: Window) {
      syncs++; beforeSync?.(); assert.equal(window, local);
      // The pinned implementation accepts null, despite its narrower published declaration.
      server.slots.forEach((item, i) => local.updateSlot(i, clone(item) as Item));
      local.selectedItem = clone(server.selectedItem);
    }};
  const bot = fake as unknown as Bot;
  const guard = () => { if (!alive) throw new Error('CANCELLED'); };
  const emit = () => { emitted++; };
  return {bot, local, server, calls, guard, emit, motor: new InventoryMotor(bot, guard, emit),
    put(slot: number, value: Item) {local.updateSlot(slot, clone(value)!); server.updateSlot(slot, clone(value)!);},
    held(value: Item) {local.selectedItem = clone(value); server.selectedItem = clone(value);},
    reject() { accept = false; }, cancel() { alive = false; },
    onSync(callback: () => void) { beforeSync = callback; },
    counts() { return {emitted, syncs}; }};
}
test('pickup splits, places one, merges and swaps with server resync for each explicit click', async () => {
  const f = fixture(); f.put(9, item('stone', 9)); f.put(11, item('dirt', 2));
  await f.motor.click(9, 'right', 'pickup');
  assert.equal(f.local.slots[9]!.count, 4); assert.equal(f.local.selectedItem!.count, 5);
  await f.motor.click(10, 'right', 'pickup');
  assert.equal(f.local.slots[10]!.count, 1); assert.equal(f.local.selectedItem!.count, 4);
  await f.motor.click(9, 'left', 'pickup');
  assert.equal(f.local.slots[9]!.count, 8); assert.equal(f.local.selectedItem, null);
  await f.motor.click(9, 'left', 'pickup');
  await f.motor.click(11, 'right', 'pickup');
  assert.equal(f.local.slots[11]!.name, 'stone'); assert.equal(f.local.selectedItem!.name, 'dirt');
  await f.motor.click(9, 'left', 'pickup'); assert.equal(f.local.selectedItem, null);
  assert.deepEqual(f.counts(), {emitted: 12, syncs: 6});
});
test('full stacks preserve the remainder and pickup no-ops are acknowledged without dropping', async () => {
  const f = fixture(); f.put(9, item('stone', 63)); f.held(item('stone', 4));
  await f.motor.click(9, 'left', 'pickup');
  assert.equal(f.local.slots[9]!.count, 64); assert.equal(f.local.selectedItem!.count, 3);
  await f.motor.click(9, 'right', 'pickup'); assert.equal(f.local.selectedItem!.count, 3);
  await f.motor.click(10, 'left', 'pickup'); assert.equal(f.local.selectedItem, null);
  await f.motor.click(11, 'left', 'pickup'); assert.equal(f.local.selectedItem, null);
  await assert.rejects(f.motor.click(-999, 'left', 'pickup'), /PRECONDITION_FAILED/);
  await assert.rejects(f.motor.click(0, 'left', 'pickup'), /MECHANIC_UNSUPPORTED/);
  assert.equal(f.calls.length, 4);
});
test('right quick move preserves item identities and requires an empty cursor', async () => {
  const f = fixture('minecraft:generic_9x3'); f.put(0, item('stone', 9));
  await f.motor.click(0, 'right', 'quick_move');
  assert.equal(f.local.slots[0], null);
  assert.equal(f.local.slots.reduce((n, value) => n + (value?.count ?? 0), 0), 9);
  f.put(0, item('stone')); f.held(item('dirt'));
  await assert.rejects(f.motor.click(0, 'left', 'quick_move'), /PRECONDITION_FAILED/);
  assert.deepEqual(f.counts(), {emitted: 2, syncs: 1});
});
test('predicted clicks, wrong carried item and server-created extras cannot satisfy completion', async () => {
  const denied = fixture(); denied.put(9, item('stone', 3)); denied.reject();
  await assert.rejects(denied.motor.click(9, 'left', 'pickup'), /PRECONDITION_FAILED/);
  assert.equal(denied.local.slots[9]!.count, 3); assert.equal(denied.local.selectedItem, null);
  const gifted = fixture(); gifted.put(9, item('stone', 3));
  gifted.onSync(() => gifted.server.updateSlot(10, item('diamond')));
  await assert.rejects(gifted.motor.click(9, 'left', 'pickup'), /PRECONDITION_FAILED/);
  const changed = fixture(); changed.put(9, item('stone', 3));
  changed.onSync(() => { changed.server.selectedItem!.nbt = {type: 'compound', name: '', value: {}} as Item['nbt']; });
  await assert.rejects(changed.motor.click(9, 'left', 'pickup'), /PRECONDITION_FAILED/);
});
test('inventory interruption and window replacement stop the remaining fixed motor steps', async () => {
  const f = fixture(); f.put(9, item('stone', 3)); f.onSync(() => f.cancel());
  await assert.rejects(equip(f.bot, {kind: 'equip', inventory_slot: 9, expected_item_id: 'minecraft:stone', destination: 'hand'}, f.guard, f.emit), /CANCELLED/);
  assert.equal(f.calls.length, 1); assert.equal(f.local.selectedItem!.count, 3);
  const changed = fixture(); changed.put(9, item('stone'));
  changed.onSync(() => {changed.bot.currentWindow = windows.createWindow(2, 'minecraft:generic_9x3', 'other') as Bot['currentWindow'];});
  await assert.rejects(changed.motor.click(9, 'left', 'pickup'), /REVISION_CONFLICT/);
  assert.equal(changed.calls.length, 1);
});
test('explicit equipment uses fixed slots, returns replaced items, and accounts each click', async () => {
  for (const [destination, sourceName, oldName, slot] of [
    ['hand', 'stone', 'dirt', 36], ['off_hand', 'shield', 'stone', 45],
    ['head', 'iron_helmet', 'leather_helmet', 5], ['torso', 'iron_chestplate', 'leather_chestplate', 6],
    ['legs', 'iron_leggings', 'leather_leggings', 7], ['feet', 'iron_boots', 'leather_boots', 8],
  ] as const) {
    const f = fixture(); f.put(9, item(sourceName)); f.put(slot, item(oldName));
    await equip(f.bot, {kind: 'equip', inventory_slot: 9, expected_item_id: `minecraft:${sourceName}`, destination}, f.guard, f.emit);
    assert.equal(f.local.slots[slot]!.name, sourceName); assert.equal(f.local.slots[9]!.name, oldName);
    assert.equal(f.local.selectedItem, null); assert.deepEqual(f.calls.map(c => c[0]), [9, slot, 9]);
    assert.deepEqual(f.counts(), {emitted: 6, syncs: 3});
  }
});
test('hotbar selection never silently rearranges inventory; invalid preconditions emit nothing', async () => {
  const f = fixture(); f.put(38, item('stone', 3));
  await equip(f.bot, {kind: 'equip', inventory_slot: 38, expected_item_id: 'minecraft:stone', destination: 'hand'}, f.guard, f.emit);
  assert.equal(f.bot.quickBarSlot, 2); assert.equal(f.bot.heldItem!.count, 3);
  assert.deepEqual(f.counts(), {emitted: 1, syncs: 0});
  await assert.rejects(equip(f.bot, {kind: 'equip', inventory_slot: 38, expected_item_id: 'minecraft:dirt', destination: 'hand'}, f.guard, f.emit), /PRECONDITION_FAILED/);
  assert.equal(f.counts().emitted, 1);
  const opened = fixture('minecraft:generic_9x3'); opened.put(0, item('stone'));
  await assert.rejects(equip(opened.bot, {kind: 'equip', inventory_slot: 9, expected_item_id: 'minecraft:stone', destination: 'hand'}, opened.guard, opened.emit), /PRECONDITION_FAILED/);
  assert.equal(opened.counts().emitted, 0);
});
test('server cursor-only packets update only the open player window and invalidate its revision', () => {
  const inventory = windows.createWindow(0, 'minecraft:inventory', 'fixture');
  const opened = windows.createWindow(2, 'minecraft:generic_9x3', 'fixture');
  const network = new EventEmitter(); let changes = 0;
  // Registry is supplied by Mineflayer; this fixture uses the same pinned data.
  const bot = {_client: network, registry: data, inventory, currentWindow: opened} as unknown as Bot;
  const stop = trackCursor(bot, () => { changes++; });
  network.emit('set_slot', {windowId: -1, slot: -1, item: Items.toNotch(item('stone', 3))});
  assert.equal(opened.selectedItem!.count, 3); assert.equal(inventory.selectedItem, null); assert.equal(changes, 1);
  network.emit('set_slot', {windowId: 99, slot: -1, item: Items.toNotch(item('diamond'))});
  network.emit('window_items', {windowId: 99, carriedItem: Items.toNotch(item('diamond'))});
  assert.equal(changes, 1);
  network.emit('window_items', {windowId: 2, carriedItem: Items.toNotch(item('stone', 3))});
  assert.equal(changes, 2);
  network.emit('set_slot', {windowId: -1, slot: -1, item: Items.toNotch(null)});
  assert.equal(opened.selectedItem, null); assert.equal(changes, 3);
  stop(); assert.equal(network.listenerCount('set_slot'), 0); assert.equal(network.listenerCount('window_items'), 0);
});
