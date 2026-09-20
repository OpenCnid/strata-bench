import test from 'node:test';
import assert from 'node:assert/strict';
import { Vec3 } from 'vec3';
import type { Block } from 'prismarine-block';
import { ObservedMap, trace, key } from '../src/observations.js';

function block(p: Vec3,name: string): Block {return {position:p.clone(),name,boundingBox:name==='air'?'empty':'block'} as Block;}
test('voxel rays stop before hidden ore, unknown chunks, and diagonal cracks',()=>{
  const reads:string[]=[];
  const read=(p:Vec3)=>{reads.push(key(p));return block(p,p.x===1?'stone':p.x===2?'diamond_ore':'air');};
  const visible=trace(new Vec3(.5,.5,.5),new Vec3(1,0,0),16,read);
  assert.deepEqual(visible.map(b=>b.name),['air','stone']);
  assert.ok(!reads.includes('2,0,0'));
  assert.equal(trace(new Vec3(.5,.5,.5),new Vec3(1,1,0),16,read).length,1);
  assert.equal(trace(new Vec3(.5,.5,.5),new Vec3(1,0,0),16,()=>null).length,0);
});
test('planning cache only contains projected observations and resets across dimensions',()=>{
  const read=(p:Vec3)=>block(p,p.y===0?'stone':'air');
  const map=new ObservedMap(read); const publicBlocks=map.scan(new Vec3(.43,2.62,.57),'minecraft:overworld');
  assert.ok(publicBlocks.length<=128);
  for(let x=-16;x<=16;x++) for(let y=-2;y<=18;y++) for(let z=-16;z<=16;z++){
    const p=new Vec3(x,y,z);
    if(map.blockAt(p)) assert.ok(publicBlocks.some(b=>key(new Vec3(b.position.x,b.position.y,b.position.z))===key(p)));
  }
  map.scan(new Vec3(1000.4,100,1000.6),'minecraft:the_nether');
  assert.equal(map.blockAt(new Vec3(0,1,0)),null);
});
test('unseen block updates never refresh stored observations',()=>{
  let hidden=false;
  const map=new ObservedMap(p=>block(p,p.x===1?'stone':p.x===0&&p.y===0?'gold_ore':hidden?'diamond_ore':'air'));
  map.scan(new Vec3(.43,2.62,.57),'minecraft:overworld');
  const old=map.blockAt(new Vec3(0,0,0)); hidden=true;
  map.scan(new Vec3(100.4,100,100.6),'minecraft:overworld');
  assert.equal(map.blockAt(new Vec3(0,0,0)),old);
});
