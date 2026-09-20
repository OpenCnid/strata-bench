import test from 'node:test';
import assert from 'node:assert/strict';
import { WorkerStartup, WORKER_STARTUP_MS } from '../src/worker_startup.js';

const health={connected:true,connected_once:true,fenced:false,reason:null};
function fixture() {let now=0;return {state:new WorkerStartup(()=>now),at:(t:number)=>{now=t;}};}

test('bootstrap has no renewal authority until a real ready message and expires at the bound',()=>{
  const f=fixture();assert.equal(f.state.canRenew(),false);
  assert.throws(()=>f.state.receive({kind:'startup_alive'}),/WORKER_PROTOCOL/);
  f.at(WORKER_STARTUP_MS);assert.equal(f.state.failure(),'WORKER_BOOT_TIMEOUT');
  assert.throws(()=>f.state.receive({kind:'bootstrap_ready'}),/WORKER_BOOT_TIMEOUT/);
});
test('fresh bootstrap and initialization pulses support renewal without authorizing a gateway',()=>{
  const f=fixture();f.at(1700);f.state.receive({kind:'bootstrap_ready'});
  assert.equal(f.state.canRenew(),true);assert.equal(f.state.phase,'waiting_config');
  f.at(1901);assert.equal(f.state.canRenew(),false);
  assert.throws(()=>f.state.initialize(),/WORKER_BOOT_UNAVAILABLE/);
  f.state.receive({kind:'startup_alive'});f.state.initialize();
  for(let t=2000;t<4000;t+=100){f.at(t);f.state.receive({kind:'startup_alive'});assert.equal(f.state.canRenew(),true);}
  assert.equal(f.state.phase,'initializing');f.at(4000);f.state.receive({kind:'gateway_ready',port:1234});
  assert.equal(f.state.phase,'active');f.state.receive({kind:'alive',health});
});
test('continuous live initialization pulses cannot extend the fixed initialization deadline',()=>{
  const f=fixture();f.state.receive({kind:'bootstrap_ready'});f.state.initialize();
  for(let t=100;t<2250;t+=100){f.at(t);f.state.receive({kind:'startup_alive'});}
  f.at(2250);assert.equal(f.state.canRenew(),false);
  assert.throws(()=>f.state.receive({kind:'gateway_ready',port:1234}),/WORKER_INITIALIZATION_TIMEOUT/);
  assert.throws(()=>f.state.receive({kind:'startup_alive'}),/WORKER_INITIALIZATION_TIMEOUT/);
});
test('active and waiting children lose freshness and expire when their event loops stop',()=>{
  for(const active of [false,true]){
    const f=fixture();f.state.receive({kind:'bootstrap_ready'});
    if(active){f.state.initialize();f.state.receive({kind:'gateway_ready',port:1234});}
    f.at(200);assert.equal(f.state.canRenew(),true);f.at(201);assert.equal(f.state.canRenew(),false);
    f.at(2251);assert.equal(f.state.failure(),'WORKER_HEARTBEAT_EXPIRED');
    assert.throws(()=>f.state.receive(active?{kind:'alive',health}:{kind:'startup_alive'}),/WORKER_HEARTBEAT_EXPIRED/);
  }
});
test('out-of-order, duplicate and malformed messages cannot become readiness or a heartbeat',()=>{
  for(const raw of [null,[],0,{kind:'gateway_ready',port:1234},{kind:'alive',health},
    {kind:'bootstrap_ready',private_token:'fixture'},{kind:'unknown'}]){
    const f=fixture();assert.throws(()=>f.state.receive(raw),/WORKER_PROTOCOL/);assert.equal(f.state.canRenew(),false);
  }
  const f=fixture();f.state.receive({kind:'bootstrap_ready'});
  assert.throws(()=>f.state.receive({kind:'bootstrap_ready'}),/WORKER_PROTOCOL/);
  assert.throws(()=>f.state.receive({kind:'gateway_ready',port:1234}),/WORKER_PROTOCOL/);
  f.state.initialize();
  for(const port of [0,65536,1.5,'1234',null])assert.throws(()=>f.state.receive({kind:'gateway_ready',port}),/WORKER_PROTOCOL/);
  f.state.receive({kind:'gateway_ready',port:1234});
  for(const raw of [{kind:'startup_alive'},{kind:'gateway_ready',port:1234},
    {kind:'alive',health:{...health,private_token:'fixture'}},{kind:'alive',health:{...health,reason:'raw secret text'}},
    {kind:'alive',health:{...health,connected_once:undefined}},{kind:'alive',health:null}]){
    f.at(201);assert.throws(()=>f.state.receive(raw),/WORKER_PROTOCOL/);assert.equal(f.state.canRenew(),false);
  }
});
