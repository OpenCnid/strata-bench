import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import type { Bot } from 'mineflayer';
import { Vec3 } from 'vec3';
import { trackBodyRevision } from '../src/body_revision.js';

function fixture() {
  const body = () => ({position:new Vec3(1,64,2),velocity:new Vec3(0,-.0784,0),yaw:0,pitch:0,onGround:true});
  const bot = Object.assign(new EventEmitter(), {entity:body(),game:{dimension:'overworld'}});
  let revision=1;
  const tracker = trackBodyRevision(bot as unknown as Bot,()=>{revision++;});
  return {bot,body,tracker,revision:()=>revision};
}

test('idle position heartbeats and duplicate physics/move events do not invalidate the body', () => {
  const f=fixture();
  for(let tick=0;tick<200;tick++) {
    f.bot.emit('physicsTick');
    if(tick%20===0)f.bot.emit('move',f.bot.entity.position.clone());
    f.tracker.sample();
  }
  assert.equal(f.revision(),1);
  f.tracker.close();
});

test('every exact coordinate, orientation, motion, ground, dimension and body-identity change invalidates', () => {
  const f=fixture();
  const changes = [
    ()=>{f.bot.entity.position.x+=1e-10;}, ()=>{f.bot.entity.position.y+=1e-10;},
    ()=>{f.bot.entity.position.z+=1e-10;}, ()=>{f.bot.entity.yaw+=1e-10;},
    ()=>{f.bot.entity.pitch+=1e-10;}, ()=>{f.bot.entity.velocity.x+=1e-10;},
    ()=>{f.bot.entity.velocity.y+=1e-10;}, ()=>{f.bot.entity.velocity.z+=1e-10;},
    ()=>{f.bot.entity.onGround=false;}, ()=>{f.bot.game.dimension='the_nether';},
    ()=>{f.bot.entity={...f.bot.entity};},
  ];
  for(const [index,change] of changes.entries()) {
    change();f.bot.emit('physicsTick');f.bot.emit('move');f.tracker.sample();
    assert.equal(f.revision(),index+2);
  }
  f.tracker.close();
});

test('forced movement, direct pose sampling and returning to old coordinates do not revive an old revision', () => {
  const f=fixture();
  f.bot.entity.position.x=3;f.bot.emit('forcedMove');
  f.bot.entity.position.x=1;f.tracker.sample();
  assert.equal(f.revision(),3);
  f.bot.entity.position.y=NaN;f.tracker.sample();f.tracker.sample();
  assert.equal(f.revision(),5); // Invalid values never compare equal to a stable valid pose.
  f.tracker.close();
});

test('missing body, replacement body and listener cleanup are explicit', () => {
  const f=fixture();
  (f.bot as unknown as {entity:unknown}).entity=undefined;
  f.bot.emit('spawn');f.bot.emit('move');assert.equal(f.revision(),2);
  f.bot.entity=f.body();f.bot.emit('spawn');assert.equal(f.revision(),3);
  f.bot.emit('end');
  f.bot.entity.position.x=9;f.bot.emit('move');f.bot.emit('physicsTick');
  assert.equal(f.revision(),3);
  for(const event of ['move','physicsTick','forcedMove','spawn'])assert.equal(f.bot.listenerCount(event),0);
});
