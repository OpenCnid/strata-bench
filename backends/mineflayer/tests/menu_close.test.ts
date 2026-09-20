import test from 'node:test';
import assert from 'node:assert/strict';
import type { Bot } from 'mineflayer';
import loadWindows, { type Window } from 'prismarine-windows';
import loadItems, { type Item } from 'prismarine-item';
import minecraftData from 'minecraft-data';
import { closeMenu } from '../src/menu_close.js';
import { MineflayerBackend } from '../src/adapter.js';
import { Fault } from '../src/protocol.js';

const windows = (loadWindows as unknown as (version:string)=>{createWindow(id:number,type:string,title:string):Window})('1.19.2');
const Items = (loadItems as unknown as (version:string)=>typeof Item)('1.19.2');
const data = minecraftData('1.19.2');
const item = (name:string,count=1) => new Items(data.itemsByName[name]!.id,count);
const copy = (value:Item|null) => value ? new Items(value.type,value.count,value.metadata,structuredClone(value.nbt) ?? undefined) : null;
/** Pinned window models with separately supplied server contents; synthetic close transport. */
function fixture(type='minecraft:crafting') {
  const inventory = windows.createWindow(0,'minecraft:inventory','own');
  const window = type === 'minecraft:inventory' ? inventory : windows.createWindow(1,type,'open');
  const server = windows.createWindow(0,'minecraft:inventory','server');
  let closes=0,refreshes=0,charges=0;
  let hold:Promise<void>|undefined, onSync = () => {};
  let reached!:()=>void; const syncing = new Promise<void>(resolve => {reached=resolve;});
  const abort = new AbortController();
  const fake = {inventory,currentWindow:window === inventory ? null : window,supportFeature:()=>true,
    closeWindow(closing:Window) {
      assert.equal(closing,window); closes++;
      if (window !== inventory) for (let i=0;i<36;i++) inventory.slots[i+9] = copy(window.slots[window.inventoryStart+i]!);
      fake.currentWindow=null;
    },
    async _syncWindow(target:Window) {
      assert.equal(target,inventory); refreshes++; reached(); onSync(); if (hold) await hold;
      server.slots.forEach((value,index) => {inventory.slots[index]=copy(value);}); inventory.selectedItem=copy(server.selectedItem);
    }};
  const guard = () => abort.signal.throwIfAborted();
  const emit = () => {charges++;};
  return {bot:fake as unknown as Bot,fake,inventory,window,server,abort,syncing,guard,emit,
    start:()=>closeMenu(fake as unknown as Bot,abort.signal,guard,emit),
    hold(promise:Promise<void>) {hold=promise;},onSync(callback:()=>void) {onSync=callback;},
    counts:()=>({closes,refreshes,charges})};
}

test('explicit close returns crafting inputs and cursor only after server inventory feedback',async () => {
  const f=fixture(); f.window.slots[1]=item('stone',2); f.window.selectedItem=item('bucket');
  f.window.slots[f.window.inventoryStart]=item('dirt',3); // Deliberately absent from stale local inventory.
  f.server.slots[9]=item('dirt',3); f.server.slots[10]=item('stone',2); f.server.slots[11]=item('bucket');
  let release!:()=>void; f.hold(new Promise<void>(resolve=>{release=resolve;}));
  let finished=false; const operation=f.start().then(result=>{finished=true;return result;});
  await f.syncing; assert.equal(finished,false); assert.equal(f.fake.currentWindow,null);
  assert.equal(f.counts().closes,1); release(); assert.equal(await operation,'emitted');
  assert.equal(f.counts().refreshes,1); assert.ok(f.counts().charges>=4);
});
test('player inventory close and existing offhand merge conserve owned items',async () => {
  const f=fixture('minecraft:inventory');
  for(let slot=9;slot<45;slot++) {f.inventory.slots[slot]=item('dirt',64);f.server.slots[slot]=item('dirt',64);}
  f.inventory.slots[45]=item('stone',63);f.inventory.selectedItem=item('stone');f.server.slots[45]=item('stone',64);
  assert.equal(await f.start(),'emitted'); assert.equal(f.inventory.selectedItem,null);
});
test('full inventory and multiple unstackable returns reject without dispatch or implicit equip',async () => {
  for(const unstackable of [false,true]) {
    const f=fixture();
    for(let i=unstackable?1:0;i<36;i++) f.window.slots[f.window.inventoryStart+i]=item('dirt',64);
    f.window.selectedItem=item(unstackable?'iron_pickaxe':'stone');
    if(unstackable) f.window.slots[1]=item('iron_axe');
    await assert.rejects(f.start(),/INVENTORY_FULL/); assert.equal(f.counts().closes,0); assert.equal(f.counts().charges,0);
  }
});
test('lost or gifted resources and an uncleared cursor cannot confirm close',async () => {
  for(const fault of ['lost','gift','cursor','nbt']) {
    const f=fixture(); f.window.selectedItem=item('stone',2); f.server.slots[9]=item('stone',2);
    if(fault==='lost')f.server.slots[9]=item('stone');
    if(fault==='gift')f.server.slots[9]=item('stone',3);
    if(fault==='cursor') {f.server.slots[9]=null;f.server.selectedItem=item('stone',2);}
    if(fault==='nbt') f.server.slots[9]!.nbt={type:'compound',value:{mark:{type:'int',value:1}}};
    await assert.rejects(f.start(),/PRECONDITION_FAILED/); assert.equal(f.counts().closes,1);
  }
});
test('replacement menu during confirmation rejects without a second close',async () => {
  const f=fixture(); f.onSync(()=>{f.fake.currentWindow=windows.createWindow(2,'minecraft:furnace','replacement');});
  await assert.rejects(f.start(),/REVISION_CONFLICT/); assert.equal(f.counts().closes,1);
});
test('cancellation interrupts the feedback wait and never replays the already closed window',async () => {
  const f=fixture(); let release!:()=>void;f.hold(new Promise<void>(resolve=>{release=resolve;}));
  const operation=f.start(); const rejected=assert.rejects(operation,/CANCELLED/);
  await f.syncing;f.abort.abort(new Fault('CANCELLED'));await rejected;release();
  assert.equal(f.counts().closes,1);assert.equal(f.counts().refreshes,1);
});
test('exhausted wait budget preserves its classification and sends no refresh after close',async () => {
  const f=fixture();let events=0;
  await assert.rejects(closeMenu(f.bot,f.abort.signal,f.guard,()=>{if(++events===2)throw new Fault('BUDGET_EXHAUSTED');}),/BUDGET_EXHAUSTED/);
  assert.equal(f.counts().closes,1);assert.equal(f.counts().refreshes,0);
});
test('backend rejects wrong window or revision before invoking the close motor',async () => {
  const f=fixture(); const adapter=Object.create(MineflayerBackend.prototype) as MineflayerBackend;
  Object.assign(adapter,{bot:f.bot,connected:true,windowRevision:7,stop:()=>{}});
  for(const [window_id,expected_window_revision] of [[2,7],[1,6]]) {
    await assert.rejects(adapter.execute({kind:'close_window',window_id:window_id!,expected_window_revision:expected_window_revision!},f.abort.signal,f.emit),/REVISION_CONFLICT/);
  }
  assert.equal(f.counts().closes,0);
  assert.equal(await adapter.execute({kind:'close_window',window_id:1,expected_window_revision:7},f.abort.signal,f.emit),'emitted');
});
