import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { Vec3 } from 'vec3';
import type { Bot } from 'mineflayer';
import type { Block } from 'prismarine-block';
import { ObservedMap } from '../src/observations.js';
import { plan } from '../src/navigation.js';
const require = createRequire(import.meta.url);
const registry = require('prismarine-registry')('1.19.2');
const BlockType = require('prismarine-block')(registry);

test('paging beyond cache capacity retains the delivered nearby floor needed for a route',()=>{
  let liveReads=0;
  const map=new ObservedMap(p=>{
    liveReads++;
    const block=BlockType.fromStateId(registry.blocksByName[p.y===67?'stone':'air'].minStateId,0) as Block;
    block.position=p.clone();return block;
  });
  const position=new Vec3(-52.27586971958149,68,16.699067428484803);
  const entries=map.capture(position.offset(0,1.62,0),'minecraft:overworld');
  assert.ok(entries.length>1024);
  assert.equal(map.blockAt(new Vec3(-50,67,16)),null); // Captured does not mean delivered.
  for(let offset=0;offset<entries.length;offset+=128) map.deliver(entries.slice(offset,offset+128),'minecraft:overworld');
  const reads=liveReads;
  const bot={registry,game:{minY:-64},entity:{position,onGround:true}} as unknown as Bot;
  const route=plan(bot,map,new Vec3(-49.5,68,16.5),.3);
  assert.equal(route.length,3);assert.equal(liveReads,reads);
  assert.ok(entries.filter(e=>map.blockAt(e.block.position)!==null).length<=1024);
  assert.equal(map.blockAt(new Vec3(-50,67,16))?.name,'stone');
});

test('actual pinned pathfinder plans a flat synthetic scene through the filtered facade only',()=>{
  let liveReads=0;
  const map=new ObservedMap(p=>{
    liveReads++;
    const block=BlockType.fromStateId(registry.blocksByName[p.y===0?'stone':'air'].minStateId,0) as Block;
    block.position=p.clone();return block;
  });
  map.scan(new Vec3(.43,2.62,.57),'minecraft:overworld');
  const bot={registry,game:{minY:-64},entity:{position:new Vec3(.43,1,.57),onGround:true}} as unknown as Bot;
  const prior=liveReads;
  const path=plan(bot,map,new Vec3(1.5,1,.5),.5);
  assert.ok(path.length>0); assert.equal(liveReads,prior);
  assert.throws(()=>plan(bot,map,new Vec3(15,1,15),.5),/PATH_BLOCKED/);
  assert.equal(liveReads,prior);
});

test('uneven observed terrain reaches the landing-height branch without raw world access', () => {
  let reads = 0;
  const map = new ObservedMap(p => {
    reads++;
    const floor = p.x < 1 ? 0 : -1;
    const block = BlockType.fromStateId(registry.blocksByName[p.y <= floor ? 'stone':'air'].minStateId,0) as Block;
    block.position=p.clone(); return block;
  });
  map.scan(new Vec3(.43,2.62,.57),'minecraft:overworld');
  const bot = {registry,game:{minY:-64},entity:{position:new Vec3(.43,1,.57),onGround:true}} as unknown as Bot;
  const captured = reads;
  assert.throws(() => plan(bot,map,new Vec3(2.5,0,.5),.5), /PATH_BLOCKED/);
  assert.equal(reads, captured);
  assert.throws(() => plan({...bot,game:{}} as Bot,map,new Vec3(2.5,0,.5),.5), /CAPABILITY_MISSING/);
});
