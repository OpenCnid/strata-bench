import { isDeepStrictEqual } from 'node:util';
import type { Bot } from 'mineflayer';
import type { Item } from 'prismarine-item';
import { requireThat, type Action } from './protocol.js';
import { id } from './observations.js';

type Stack = {type: number; metadata: number; count: number; stackSize: number; nbt: Item['nbt']} | null;
function copy(item: Item | null): Stack {
  return item ? {type: item.type, metadata: item.metadata, count: item.count,
    stackSize: item.stackSize, nbt: structuredClone(item.nbt ?? null)} : null;
}
function same(a: Stack, b: Stack): boolean {
  return !!a && !!b && a.type === b.type && a.metadata === b.metadata && isDeepStrictEqual(a.nbt, b.nbt);
}
function exact(a: Stack, b: Stack): boolean { return !a && !b || same(a, b) && a!.count === b!.count; }
function conserved(before: Stack[], after: Stack[]): boolean {
  const identities = before.filter((item, index) => item && !before.slice(0, index).some(old => same(item, old)));
  const total = (items: Stack[], type: Stack) => items.reduce((sum, item) => sum + (same(item, type) ? item!.count : 0), 0);
  return after.every(item => !item || identities.some(old => same(item, old))) &&
    identities.every(item => total(before, item) === total(after, item));
}

/** Fixed, explicit inventory clicks; no item acquisition, drops or auto-equipment. */
export class InventoryMotor {
  private readonly window: Bot['inventory'];
  private readonly sync: (window: Bot['inventory']) => Promise<void>;
  constructor(private bot: Bot, private guard: () => void, private emit: () => void) {
    this.window = (bot.currentWindow ?? bot.inventory) as Bot['inventory'];
    const sync = (bot as Bot & {_syncWindow?: (window: Bot['inventory']) => Promise<void>})._syncWindow;
    requireThat(typeof sync === 'function', 'MECHANIC_UNSUPPORTED'); this.sync = sync.bind(bot);
    requireThat(this.window.type === 'minecraft:inventory' || this.window.type === 'minecraft:crafting' ||
      this.window.type === 'minecraft:furnace' || /^minecraft:generic_(9x[1-6]|3x3)$/.test(String(this.window.type)),
      'MECHANIC_UNSUPPORTED');
  }
  private check(): void {
    this.guard(); requireThat((this.bot.currentWindow ?? this.bot.inventory) === this.window, 'REVISION_CONFLICT');
  }
  private stacks(): Stack[] {
    // Crafting result slots are a preview of the inputs, not an additional owned stack.
    return [...this.window.slots.map((item, index) =>
      index === 0 && ['minecraft:inventory', 'minecraft:crafting'].includes(String(this.window.type)) ? null : copy(item)),
      copy(this.window.selectedItem)];
  }
  private capacity(slot: number, held: Stack): number {
    if (this.window === this.bot.inventory && slot >= 5 && slot <= 8) return 1;
    return held?.stackSize ?? 64;
  }
  async click(slot: number, button: 'left' | 'right', mode: 'pickup' | 'quick_move'): Promise<void> {
    this.check();
    requireThat(Number.isInteger(slot) && slot >= 0 && slot < this.window.slots.length, 'PRECONDITION_FAILED');
    requireThat(!(slot === 0 && ['minecraft:inventory', 'minecraft:crafting'].includes(String(this.window.type))),
      'MECHANIC_UNSUPPORTED');
    const before = this.stacks(); const target = copy(this.window.slots[slot]!); const cursor = copy(this.window.selectedItem);
    let expectedTarget: Stack = target; let expectedCursor: Stack = cursor;
    if (mode === 'quick_move') {
      requireThat(!cursor && target, 'PRECONDITION_FAILED');
    } else if (!cursor) {
      if (target) {
        const moved = button === 'left' ? target.count : Math.ceil(target.count / 2);
        expectedCursor = {...target, count: moved};
        expectedTarget = target.count === moved ? null : {...target, count: target.count - moved};
      }
    } else if (!target || same(target, cursor)) {
      const moved = Math.min(cursor.count, button === 'right' ? 1 : cursor.count,
        Math.max(0, this.capacity(slot, cursor) - (target?.count ?? 0)));
      expectedTarget = {...cursor, count: (target?.count ?? 0) + moved};
      expectedCursor = moved === cursor.count ? null : {...cursor, count: cursor.count - moved};
    } else {
      requireThat(cursor.count <= this.capacity(slot, cursor), 'PRECONDITION_FAILED');
      expectedTarget = cursor; expectedCursor = target;
    }
    this.emit(); await this.bot.clickWindow(slot, button === 'left' ? 0 : 1, mode === 'pickup' ? 0 : 1);
    this.check(); this.emit(); await this.sync(this.window); this.check();
    const actualTarget = copy(this.window.slots[slot]!); const actualCursor = copy(this.window.selectedItem);
    requireThat(conserved(before, this.stacks()), 'PRECONDITION_FAILED');
    if (mode === 'pickup') requireThat(exact(expectedTarget, actualTarget) && exact(expectedCursor, actualCursor), 'PRECONDITION_FAILED');
    else requireThat(!actualCursor && (!same(target, actualTarget) || actualTarget!.count < target!.count), 'PRECONDITION_FAILED');
  }
}

export async function equip(bot: Bot, action: Extract<Action, {kind: 'equip'}>,
  guard: () => void, emit: () => void): Promise<void> {
  guard(); requireThat(!bot.currentWindow && !bot.inventory.selectedItem, 'PRECONDITION_FAILED');
  requireThat(action.inventory_slot >= 5 && action.inventory_slot <= 45, 'PRECONDITION_FAILED');
  const source = bot.inventory.slots[action.inventory_slot];
  requireThat(source && id(source.name) === action.expected_item_id, 'PRECONDITION_FAILED');
  const armor = {off_hand: 45, head: 5, torso: 6, legs: 7, feet: 8};
  requireThat(Number.isInteger(bot.quickBarSlot) && bot.quickBarSlot >= 0 && bot.quickBarSlot <= 8, 'PRECONDITION_FAILED');
  if (action.destination === 'hand' && action.inventory_slot >= 36 && action.inventory_slot <= 44) {
    if (bot.quickBarSlot !== action.inventory_slot - 36) { emit(); bot.setQuickBarSlot(action.inventory_slot - 36); }
  } else {
    const destination = action.destination === 'hand' ? 36 + bot.quickBarSlot : armor[action.destination];
    if (destination !== action.inventory_slot) {
      const motor = new InventoryMotor(bot, guard, emit);
      await motor.click(action.inventory_slot, 'left', 'pickup');
      await motor.click(destination, 'left', 'pickup');
      if (bot.inventory.selectedItem) await motor.click(action.inventory_slot, 'left', 'pickup');
    }
  }
  guard();
  const equipped = action.destination === 'hand' ? bot.heldItem : bot.inventory.slots[armor[action.destination]];
  requireThat(!bot.inventory.selectedItem && equipped && id(equipped.name) === action.expected_item_id, 'PRECONDITION_FAILED');
}
