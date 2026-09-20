import { isDeepStrictEqual } from 'node:util';
import { setTimeout as delay } from 'node:timers/promises';
import type { Bot } from 'mineflayer';
import type { Item } from 'prismarine-item';
import { Fault, requireThat } from './protocol.js';

export const MENU_CLOSE_POLICY = 'explicit-close-own-inventory-feedback-conservation/1';
type Stack = {type:number;metadata:number;count:number;stackSize:number;nbt:Item['nbt']} | null;
const copy = (item:Item|null):Stack => item ? {type:item.type,metadata:item.metadata,count:item.count,
  stackSize:item.stackSize,nbt:structuredClone(item.nbt ?? null)} : null;
const same = (a:Stack,b:Stack) => !!a && !!b && a.type === b.type && a.metadata === b.metadata && isDeepStrictEqual(a.nbt,b.nbt);
type State = {inventory:Stack[];returning:Stack[]};
function preserved(a:State,b:State) {
  const before = [...a.inventory,...a.returning], after = [...b.inventory,...b.returning];
  const total = (items:Stack[],item:Stack) => items.reduce((sum,other) => sum + (same(item,other) ? other!.count : 0),0);
  return [...before,...after].every(item => !item || total(before,item) === total(after,item));
}
function fits(state:State) {
  const slots = structuredClone(state.inventory);
  for (const item of state.returning) {
    if (!item) continue;
    let remaining = item.count;
    for (const empty of [false,true]) for (let slot=4;slot<41 && remaining>0;slot++) {
      if (empty && slot === 40) continue; // Offhand is a merge destination, never an implicit equipment target.
      const target = slots[slot]!;
      if (empty ? !!target : !same(item,target)) continue;
      const moved = Math.min(remaining,Math.max(0,item.stackSize-(target?.count ?? 0)));
      if (moved) {slots[slot] = {...item,count:(target?.count ?? 0)+moved}; remaining -= moved;}
    }
    requireThat(remaining === 0,'INVENTORY_FULL');
  }
}

/** Normal explicit close plus full own-inventory feedback. No storage read after close. */
export async function closeMenu(bot:Bot, signal:AbortSignal, guard:()=>void, emit:()=>void):Promise<'emitted'> {
  guard();
  const window = bot.currentWindow ?? bot.inventory, inventory = bot.inventory;
  const sync = (bot as Bot & {_syncWindow?:(window:Bot['inventory'])=>Promise<void>})._syncWindow;
  requireThat(typeof sync === 'function' && bot.supportFeature('stateIdUsed') && inventory.slots.length === 46
    && (window.type === 'minecraft:inventory' || window.type === 'minecraft:crafting' || window.type === 'minecraft:furnace'
      || /^minecraft:generic_(9x[1-6]|3x3)$/.test(String(window.type))), 'MECHANIC_UNSUPPORTED');
  requireThat(window.inventoryEnd-window.inventoryStart === 36,'MECHANIC_UNSUPPORTED');
  const beforeInventory = inventory.slots.slice(5,46).map(copy);
  if (window !== inventory) {
    requireThat(inventory.slots.slice(1,5).every(item => !item) && !inventory.selectedItem, 'PRECONDITION_FAILED');
    for (let i=0;i<36;i++) beforeInventory[i+4] = copy(window.slots[window.inventoryStart+i]!);
  }
  const gridSize = window.type === 'minecraft:inventory' ? 4 : window.type === 'minecraft:crafting' ? 9 : 0;
  const before:State = {inventory:beforeInventory,returning:[copy(window.selectedItem),...window.slots.slice(1,gridSize+1).map(copy)]};
  requireThat([...before.inventory,...before.returning].every(item => !item || Number.isInteger(item.count)
    && item.count >= 1 && item.count <= 64 && Number.isInteger(item.stackSize) && item.stackSize >= item.count && item.stackSize <= 64), 'MECHANIC_UNSUPPORTED');
  fits(before);
  const checkClosed = () => {guard(); requireThat(!bot.currentWindow && bot.inventory === inventory,'REVISION_CONFLICT');};
  const wait = async (pending:Promise<void>) => {
    let result:'pending'|'done'|'failed' = 'pending';
    pending.then(() => {result = 'done';},() => {result = 'failed';});
    // Promise callbacks do not dispatch input. Each active 50-ms feedback wait is charged.
    while (result === 'pending') {
      checkClosed(); emit();
      try {await delay(50,undefined,{signal});}
      catch (error) {signal.throwIfAborted(); throw error;}
    }
    checkClosed(); requireThat(result === 'done','GAME_MENU_SYNC_UNAVAILABLE');
  };
  requireThat((bot.currentWindow ?? bot.inventory) === window,'REVISION_CONFLICT');
  guard(); emit();
  try {await wait(Promise.resolve(bot.closeWindow(window)));}
  catch (error) {if (signal.aborted || error instanceof Fault) throw error; throw new Fault('GAME_MENU_CLOSE_UNCONFIRMED');}
  checkClosed(); emit(); await wait(sync.call(bot,inventory)); checkClosed();
  const after:State = {inventory:inventory.slots.slice(5,46).map(copy),
    returning:[copy(inventory.selectedItem),...inventory.slots.slice(1,5).map(copy)]};
  requireThat(after.returning.every(item => !item) && preserved(before,after)
    && before.inventory.slice(0,4).every((item,index) => isDeepStrictEqual(item,after.inventory[index])), 'PRECONDITION_FAILED');
  return 'emitted';
}
