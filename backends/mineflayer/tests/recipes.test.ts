import test from 'node:test';
import assert from 'node:assert/strict';
import type { Bot } from 'mineflayer';
import { FRESH_TOOL_NBT, RecipeBook } from '../src/recipes.js';
import { craft } from '../src/crafting.js';
import { Fault } from '../src/protocol.js';

const itemNames: Record<number,string> = {1:'oak_log',2:'oak_planks',3:'stick',4:'birch_log',5:'milk_bucket'};
const slot = (itemId: number, itemCount=1) => ({present:true,itemId,itemCount,nbtData:null});
function book() {
  const book = new RecipeBook(id => itemNames[id]);
  book.declare({recipes:[
    {type:'minecraft:crafting_shapeless',recipeId:'minecraft:oak_planks',data:{ingredients:[[slot(1)]],result:slot(2,4)}},
    {type:'minecraft:crafting_shaped',recipeId:'minecraft:stick',data:{width:1,height:2,
      ingredients:[[[slot(2)],[slot(2)]]],result:slot(3,4)}},
    {type:'example:hidden',recipeId:'example:private_recipe'},
  ]});
  return book;
}

test('recipes expose server unlocks only, remove unlocks, reject private guesses and unknown serializers', () => {
  const recipes = book();
  assert.deepEqual((recipes.list(0) as {recipes: unknown[]}).recipes, []);
  assert.throws(() => recipes.get('minecraft:oak_planks'), /FORBIDDEN/);
  recipes.unlock({action:0,recipes1:['minecraft:oak_planks','example:private_recipe']});
  const visible = recipes.list(0) as {recipes: {recipe_id:string;supported:boolean}[]};
  assert.equal(visible.recipes.length,2);
  assert.equal(visible.recipes[0]!.supported,false);
  assert.throws(() => recipes.get('example:private_recipe'), /MECHANIC_UNSUPPORTED/);
  assert.equal(recipes.get('minecraft:oak_planks').result.count,4);
  recipes.unlock({action:2,recipes1:['minecraft:oak_planks']});
  assert.throws(() => recipes.get('minecraft:oak_planks'), /FORBIDDEN/);
});

test('recipe selection respects shaped layout, alternative ingredient competition and actual inventory', () => {
  const recipes = book(); recipes.unlock({action:0,recipes1:['minecraft:stick']});
  assert.deepEqual(recipes.select(recipes.get('minecraft:stick'),[{type:2,count:2}],2),[2,null,2,null]);
  const alternative = {recipe_id:'fixture:alternative',serializer:'minecraft:crafting_shapeless',
    width:0,height:0,ingredients:[[1,4],[1]],result:{type:3,count:1}};
  assert.deepEqual(recipes.select(alternative,[{type:1,count:1},{type:4,count:1}],2),[4,1,null,null]);
  assert.throws(() => recipes.select(alternative,[{type:1,count:1}],2), /PRECONDITION_FAILED/);
  assert.throws(() => recipes.select(alternative,[{type:1,count:2,nbt:{private:'metadata'}}],2), /PRECONDITION_FAILED/);
});

test('NBT, ingredient remainders and unknown item IDs cannot silently use a vanilla fallback', () => {
  const recipes = new RecipeBook(id=>itemNames[id]);
  recipes.declare({recipes:[
    {type:'minecraft:crafting_shapeless',recipeId:'fixture:nbt',data:{ingredients:[[{...slot(1),nbtData:{secret:1}}]],result:slot(2)}},
    {type:'minecraft:crafting_shapeless',recipeId:'fixture:unknown',data:{ingredients:[[slot(999)]],result:slot(2)}},
    {type:'minecraft:crafting_shapeless',recipeId:'fixture:remainder',data:{ingredients:[[slot(5)]],result:slot(2)}},
  ]});
  recipes.unlock({action:0,recipes1:['fixture:nbt','fixture:unknown','fixture:remainder']});
  for (const id of ['fixture:nbt','fixture:unknown','fixture:remainder']) assert.throws(()=>recipes.get(id),/MECHANIC_UNSUPPORTED/);
});

/** Independent synthetic server slot model. Client prediction deliberately lies;
 * resynchronization restores authoritative fixture state. This is not T03 evidence.
 */
function syntheticCraftingServer(outputType=2, onSync: (clicks: number) => void = () => {}, outputNbt:unknown=null, outputCount=4) {
  type Item = {type:number;count:number;nbt:unknown};
  const server: (Item|null)[] = Array(46).fill(null);
  server[9] = {type:1,count:2,nbt:null};
  let cursor: Item|null = null;
  const window = {id:0,type:'minecraft:inventory',inventoryStart:9,inventoryEnd:45,
    slots:structuredClone(server),selectedItem:null as Item|null};
  let clicks = 0;
  const bot = {currentWindow:null,inventory:window,
    clickWindow:async (index:number, button:number) => {
      clicks++;
      if (index === 0) {
        assert.equal(cursor,null);
        cursor = server[0] ?? null; server[0] = null;
        assert.ok(server[1]); server[1] = null;
      } else if (button === 1) {
        assert.ok(cursor);
        server[index] = {type:cursor.type,count:1,nbt:null};
        cursor = cursor.count > 1 ? {...cursor,count:cursor.count-1} : null;
      } else {
        const old = server[index]; server[index] = cursor; cursor = old ?? null;
      }
      server[0] = server[1]?.type === 1 ? {type:outputType,count:outputCount,nbt:structuredClone(outputNbt)} : null;
      window.slots[0] = {type:999,count:64,nbt:null}; // never treat predicted output as success
    },
    _syncWindow:async () => {window.slots = structuredClone(server); window.selectedItem = structuredClone(cursor); onSync(clicks);},
  };
  return {bot:bot as unknown as Bot,server,clicks:()=>clicks};
}

test('fixed craft motor waits for server slots, consumes inputs and counts every click/resync', async () => {
  const recipes = book(); recipes.unlock({action:0,recipes1:['minecraft:oak_planks']});
  const server = syntheticCraftingServer(); let emissions = 0;
  await craft(server.bot,recipes,{kind:'craft',recipe_id:'minecraft:oak_planks',count:2,
    window_id:0,expected_window_revision:1},1,()=>{},()=>{emissions++;});
  assert.equal(server.server.filter(item=>item?.type===1).length,0);
  assert.equal(server.server.filter(item=>item?.type===2).reduce((sum,item)=>sum+item!.count,0),8);
  assert.equal(emissions,server.clicks()*2);
});

test('craft rejects wrong authoritative output, stale window and interrupted continuation', async () => {
  const recipes = book(); recipes.unlock({action:0,recipes1:['minecraft:oak_planks']});
  const action = {kind:'craft' as const,recipe_id:'minecraft:oak_planks',count:1,window_id:0,expected_window_revision:1};
  const unsupported=syntheticCraftingServer();let unsupportedEmissions=0;
  await assert.rejects(craft(unsupported.bot,recipes,{...action,recipe_selection:{source_generation:1,revision:1,
    query:{source:'jei',category:'minecraft:crafting',item_id:'minecraft:oak_planks',role:'output',after:0}}},1,()=>{},()=>{unsupportedEmissions++;}),/CAPABILITY_MISSING/);
  assert.equal(unsupported.clicks(),0);assert.equal(unsupportedEmissions,0);
  const wrong = syntheticCraftingServer(3);
  await assert.rejects(craft(wrong.bot,recipes,action,1,()=>{},()=>{}),/PRECONDITION_FAILED/);
  assert.equal(wrong.server.filter(item=>item?.type===3 && item !== wrong.server[0]).length,0);
  const stale = syntheticCraftingServer();
  await assert.rejects(craft(stale.bot,recipes,action,2,()=>{},()=>{}),/REVISION_CONFLICT/);
  assert.equal(stale.clicks(),0);
  const cancelled = syntheticCraftingServer();
  await assert.rejects(craft(cancelled.bot,recipes,action,1,()=>{
    if (cancelled.clicks() >= 1) throw new Fault('CANCELLED');
  },()=>{}),/CANCELLED/);
  assert.equal(cancelled.clicks(),1);
});

test('craft survives unrelated and duplicate unlocks while preserving exact output and charges', async () => {
  const recipes = book(); recipes.unlock({action:0,recipes1:['minecraft:oak_planks']});
  const server = syntheticCraftingServer(2, () => recipes.unlock({action:1,recipes1:['minecraft:stick','minecraft:oak_planks']}));
  let emissions = 0;
  await craft(server.bot, recipes, {kind:'craft',recipe_id:'minecraft:oak_planks',count:2,
    window_id:0,expected_window_revision:1},1,()=>{},()=>{emissions++;});
  assert.equal(server.server.filter(item=>item?.type===2).reduce((sum,item)=>sum+item!.count,0),8);
  assert.equal(emissions,server.clicks()*2);
});

test('selected recipe revocation, revoke-regrant, reset and redeclaration fence partial craft without replay', async () => {
  for (const mode of ['revoke','regrant','reset','declare']) {
    const recipes = book(); recipes.unlock({action:0,recipes1:['minecraft:oak_planks']});
    const server = syntheticCraftingServer(2, () => {
      if (mode === 'declare') recipes.declare({recipes:[{type:'minecraft:crafting_shapeless',recipeId:'minecraft:oak_planks',
        data:{ingredients:[[slot(1)]],result:slot(2,8)}}]});
      else if (mode === 'reset') recipes.unlock({action:0,recipes1:['minecraft:oak_planks']});
      else {
        recipes.unlock({action:2,recipes1:['minecraft:oak_planks']});
        if (mode === 'regrant') recipes.unlock({action:1,recipes1:['minecraft:oak_planks']});
      }
    });
    await assert.rejects(craft(server.bot,recipes,{kind:'craft',recipe_id:'minecraft:oak_planks',count:1,
      window_id:0,expected_window_revision:1},1,()=>{},()=>{}),/FORBIDDEN|REVISION_CONFLICT/);
    assert.equal(server.clicks(),1,mode);
    assert.equal(server.server.filter(item=>item?.type===2).length,0,mode);
  }
});

test('fresh damageable outputs admit only exact Damage=0; tagged ingredients and custom output tags stay unsupported', () => {
  for (const [nbt,damageable,count,ingredient,allowed] of [
    [FRESH_TOOL_NBT,true,1,false,true],
    [FRESH_TOOL_NBT,false,1,false,false],
    [FRESH_TOOL_NBT,true,2,false,false],
    [FRESH_TOOL_NBT,true,1,true,false],
    [{...FRESH_TOOL_NBT,value:{Damage:{type:'int',value:1}}},true,1,false,false],
    [{...FRESH_TOOL_NBT,value:{...FRESH_TOOL_NBT.value,Unbreakable:{type:'byte',value:1}}},true,1,false,false],
  ] as const) {
    const recipes = new RecipeBook(id => itemNames[id], () => damageable ? 59 : undefined);
    recipes.declare({recipes:[{type:'minecraft:crafting_shapeless',recipeId:'fixture:fresh_tool',data:{
      ingredients:[[{...slot(1),nbtData:ingredient ? nbt : null}]],result:{...slot(2,count),nbtData:nbt}}}]});
    recipes.unlock({action:0,recipes1:['fixture:fresh_tool']});
    if (allowed) assert.deepEqual(recipes.get('fixture:fresh_tool').result.nbt,FRESH_TOOL_NBT);
    else assert.throws(() => recipes.get('fixture:fresh_tool'),/MECHANIC_UNSUPPORTED/);
  }
});

test('fresh tool craft checks exact server output metadata and preserves existing tagged stacks', async () => {
  const recipes = new RecipeBook(id=>itemNames[id],()=>59);
  recipes.declare({recipes:[{type:'minecraft:crafting_shapeless',recipeId:'fixture:fresh_tool',data:{
    ingredients:[[slot(1)]],result:{...slot(2),nbtData:FRESH_TOOL_NBT}}}]});
  recipes.unlock({action:0,recipes1:['fixture:fresh_tool']});
  const action={kind:'craft' as const,recipe_id:'fixture:fresh_tool',count:1,window_id:0,expected_window_revision:1};
  for (const nbt of [FRESH_TOOL_NBT,null,{...FRESH_TOOL_NBT,value:{Damage:{type:'int',value:1}}}]) {
    const server=syntheticCraftingServer(2,()=>{},nbt,1);
    if (nbt===FRESH_TOOL_NBT) {
      await craft(server.bot,recipes,action,1,()=>{},()=>{});
      assert.deepEqual(server.server.find(item=>item?.type===2)?.nbt,FRESH_TOOL_NBT);
    } else await assert.rejects(craft(server.bot,recipes,action,1,()=>{},()=>{}),/PRECONDITION_FAILED/);
  }
  const altered=syntheticCraftingServer(2,()=>{
    // Same total item counts, but an unsolicited damaged stack is not conservation.
    altered.server[40]={type:3,count:1,nbt:{...FRESH_TOOL_NBT,value:{Damage:{type:'int',value:1}}}};
  },FRESH_TOOL_NBT,1);
  altered.server[40]={type:3,count:1,nbt:FRESH_TOOL_NBT};
  await (altered.bot as Bot & {_syncWindow:(w:unknown)=>Promise<void>})._syncWindow(altered.bot.inventory);
  await assert.rejects(craft(altered.bot,recipes,action,1,()=>{},()=>{}),/PRECONDITION_FAILED/);
});
