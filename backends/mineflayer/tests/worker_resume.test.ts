import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Journal } from '../src/journal.js';
import { resumeDecision, type ResumeState } from '../src/native_resume.js';
import { serveResume } from '../src/worker_resume.js';
import { ForgeLane } from '../src/forge_lane.js';
import { NativeGameClient, NativeOutcomeUnknown, nativeCapabilities } from '../src/native_game.js';
import { Fault } from '../src/protocol.js';

function decision(){return resumeDecision({schema:'strata/NativeSettingsResumeDecision/1',policy:'operator-owned-settings-resume/1',
  resume_id:'resume',worker_plan:{schema:'strata/WorkerRepairPlan/1',policy:'operator-owned-fixed-repair-pause/1',
    campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease',transaction_id:'tx',plan_digest:'a'.repeat(64),expires_unix_ms:10000},
  expected_revision:4,expected_digest:'b'.repeat(64),completion_phase:'committed',verification_ref:'cas:sha256:'+'c'.repeat(64),
  connection_generation:1,lease_until_unix_ms:9000});}
function receipt():ResumeState {return {schema:'strata/NativeSettingsResumeState/1',decision:decision(),source_instance:'native',
  current_instance:'native',input_resumed:true,effects_verified_by_native:false,health:{schema:'strata/NativeGameLane/1',
    fenced:false,fence_token:'token',reason:null,journal_healthy:true,epoch:1,active_request_id:null,
    attempted_primitive_events:7,primitive_limit:100}};}

test('consumed resume intent cannot be replayed or made recoverable by a new epoch',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-resume-intent-'));t.after(()=>rmSync(root,{recursive:true}));
  let j=new Journal(root,1);const d=decision();j.holdRepair(d.worker_plan);j.counter('primitive_events',7);
  j.beginResume(d);assert.throws(()=>j.beginResume(d));j.close();j=new Journal(root,2);
  try {assert.deepEqual(j.resumeRecord('tx')!.decision,d);assert.equal(j.resumeRecord('tx')!.receipt,null);
    assert.throws(()=>j.recover(),/REPAIR_RECOVERY_REQUIRED/);assert.equal(j.counter('primitive_events'),7);}
  finally{j.close();}
});

test('completed receipt retains counters and consumed history; failed completion remains held',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-resume-complete-'));
  const j=new Journal(root,1),d=decision();t.after(()=>{j.close();rmSync(root,{recursive:true});});j.holdRepair(d.worker_plan);j.beginResume(d);
  j.counter('primitive_events',7);j.next('action');
  const event=j.event.bind(j);j.event=()=>{throw new Error('synthetic durable-write failure');};
  assert.throws(()=>j.finishResume(d,receipt(),{}),/durable-write/);j.event=event;
  assert.equal(j.resumeRecord('tx')!.receipt,null);assert.throws(()=>j.recover(),/REPAIR_RECOVERY_REQUIRED/);
  assert.throws(()=>j.finishResume(d,{...receipt(),decision:{...d,resume_id:'foreign'}},{}),/REPAIR_NOT_OWNED/);
  j.finishResume(d,receipt(),{observation_id:'fresh'});j.recover();
  assert.equal(j.counter('primitive_events'),7);assert.equal(j.counter('1:action'),1);
  assert.throws(()=>j.beginResume(d));assert.throws(()=>j.finishResume(d,receipt(),{}));
  assert.throws(()=>j.holdRepair(d.worker_plan));
  j.holdRepair({...d.worker_plan,transaction_id:'next'});
  j.failRepair({...d.worker_plan,transaction_id:'next'},'STOPPED');assert.throws(()=>j.recover(),/REPAIR_RECOVERY_REQUIRED/);
});

test('private resume endpoint rejects public credentials, browser origins and malformed decisions',async t=>{
  let calls=0;const d=decision();
  const server=await serveResume(async(op,value)=>{calls++;assert.deepEqual(value,d);
    if(op==='status')throw new Error('private path and credential');return {candidate:true};},'private-token');
  t.after(()=>{server.closeAllConnections();server.close();});
  const address=server.address();assert(address && typeof address!=='string');
  const url=`http://127.0.0.1:${address.port}/v1/resume`;
  const request={schema:'strata/WorkerResumeRequest/1',request_id:'request',operation:'resume',decision:d};
  const send=(body:unknown,token='private-token',extra:Record<string,string>={})=>fetch(url,{method:'POST',
    headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json',...extra},body:JSON.stringify(body)});
  assert.equal((await send(request,'gameplay-token')).status,403);
  assert.equal((await send(request,'private-token',{Origin:'https://example.test'})).status,403);
  for(const patch of [{operation:'arm'},{extra:true},{decision:{...d,lease_until_unix_ms:10001}}])
    assert.equal((await send({...request,...patch})).status,400);
  assert.equal(calls,0);assert.equal((await send(request)).status,200);
  const refused=await send({...request,operation:'status'});assert.equal(refused.status,400);
  assert.doesNotMatch(await refused.text(),/private path|credential/);
});

/** Native transport/replacement and observations are synthetic here; process joins have JVM tests. */
async function paused(t:test.TestContext) {
  const root=mkdtempSync(join(tmpdir(),'strata-resume-fault-')),journal=new Journal(root,1);
  const d=decision();d.worker_plan.expires_unix_ms=Date.now()+9000;d.lease_until_unix_ms=Date.now()+5000;
  let health={...receipt().health,fenced:true,epoch:null as number|null,attempted_primitive_events:0};
  let mutations=0,lost=false;
  let beforeReturn:()=>Promise<void>=async()=>{};
  const client={connection:{fingerprint:'a'.repeat(64)},call:async(op:string)=>{
    if(op==='capabilities')return nativeCapabilities(true);
    if(op==='authority')return {campaign_id:'campaign',agent_id:'avatar',capability_digest:'c'.repeat(64),
      body_fingerprint:'b'.repeat(64),primitive_limit:100,expires_unix_ms:Date.now()+20000};
    if(op==='identity')return {body_fingerprint:'b'.repeat(64),connection_generation:1};
    if(op==='arm')health={...health,fenced:false,epoch:1};
    if(op==='stop_all')health={...health,fenced:true,active_request_id:null};
    if(op==='settings_resume'){
      mutations++;health={...health,fenced:false,attempted_primitive_events:7};await beforeReturn();
      if(lost)throw new NativeOutcomeUnknown('request','settings_resume',new Fault('GAME_TRANSPORT_UNAVAILABLE'));
    }
    if(op==='settings_resume'||op==='settings_resume_status')return {...receipt(),decision:d,health:{...health},input_resumed:!health.fenced};
    return {...health};
  }} as unknown as NativeGameClient;
  const lane=await ForgeLane.connect({campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease'},
    'c'.repeat(64),client,journal,'b'.repeat(64),100,10000,1,'operator-owned-fixed-repair-pause/1');
  lane.enableRestart(async()=>{});lane.enableResume();await lane.pauseRepair(d.worker_plan);
  Object.assign(lane,{connected:true,restart:{phase:'attached',old_terminal:{},replacement:{policy:'forge-process-listener-client-thread/4'}}});
  lane.observe=async()=>({observation_id:'synthetic-fresh'} as any);
  t.after(async()=>{await lane.close().catch(()=>{});journal.close();rmSync(root,{recursive:true});});
  return {lane,journal,d,mutations:()=>mutations,health:()=>health,lose:()=>{lost=true;},
    defer:(wait:()=>Promise<void>)=>{beforeReturn=wait;}};
}

test('worker reconciles lost native reply once and stop cannot resurrect consumed resume',async t=>{
  const f=await paused(t);f.lose();
  await assert.rejects(f.lane.resumeControl('resume',f.d),/GAME_OUTCOME_UNKNOWN/);
  assert.equal(f.journal.resumeRecord('tx')!.receipt,null);
  assert.equal((await f.lane.resumeControl('status',f.d) as any).gameplay_resumed,true);
  assert.equal(f.mutations(),1);assert.equal(f.journal.counter('primitive_events'),7);
  await f.lane.stopAll();
  assert.equal((await f.lane.resumeControl('resume',f.d) as any).gameplay_resumed,false);
  assert.equal(f.mutations(),1);assert.equal(f.health().fenced,true);
});

test('failed durable completion stops resumed input and retains unresolved intent',async t=>{
  const f=await paused(t);f.journal.finishResume=()=>{throw new Error('synthetic persistence failure');};
  await assert.rejects(f.lane.resumeControl('resume',f.d),/EVIDENCE_UNAVAILABLE/);
  assert.equal(f.health().fenced,true);assert.equal(f.journal.resumeRecord('tx')!.receipt,null);
  assert.throws(()=>f.journal.recover(),/REPAIR_RECOVERY_REQUIRED/);
});

test('stop during native resume prevents late receipt from releasing the worker hold',async t=>{
  const f=await paused(t);let release!:()=>void,entered!:()=>void;
  const ready=new Promise<void>(resolve=>{entered=resolve;});
  f.defer(()=>{entered();return new Promise(resolve=>{release=resolve;});});
  const pending=f.lane.resumeControl('resume',f.d);const rejected=assert.rejects(pending,/REPAIR_RESUME_UNCONFIRMED/);
  await ready;await f.lane.stopAll();release();await rejected;
  assert.equal(f.health().fenced,true);assert.equal(f.journal.resumeRecord('tx')!.receipt,null);
  assert.equal(f.mutations(),1);
});
