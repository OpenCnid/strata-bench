import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { Journal } from '../src/journal.js';
import { repairPlan, serveRepair, WORKER_REPAIR_POLICY, type RepairPlan } from '../src/worker_repair.js';

function plan():RepairPlan {return {schema:'strata/WorkerRepairPlan/1',policy:WORKER_REPAIR_POLICY,
  campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease',transaction_id:'repair',
  plan_digest:'a'.repeat(64),expires_unix_ms:Date.now()+10000};}

test('repair plan requires exact authority fields and interoperable values',()=>{
  const valid=plan();assert.deepEqual(repairPlan(valid),valid);
  for(const key of Object.keys(valid)) {const missing={...valid} as Record<string,unknown>;delete missing[key];
    assert.throws(()=>repairPlan(missing));}
  for(const patch of [{schema:'strata/WorkerRepairPlan/2'},{policy:'automatic-resume'}, {extra:true},
    {epoch:0},{epoch:1.5},{epoch:true},{expires_unix_ms:Number.MAX_SAFE_INTEGER+1},
    {expires_unix_ms:0},{transaction_id:'../outside'},{agent_id:'😀'},{plan_digest:'A'.repeat(64)}])
    assert.throws(()=>repairPlan({...valid,...patch}));
});

test('repair hold is atomic, survives a new epoch and cannot silently rearm',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-repair-journal-'));t.after(()=>rmSync(root,{recursive:true}));
  const p=plan();let j=new Journal(root,1);
  const original=j.event.bind(j);j.event=()=>{throw new Error('synthetic storage failure');};
  assert.throws(()=>j.holdRepair(p),/synthetic storage failure/);
  j.event=original;j.recover(); // failed intent must leave no partial hold
  j.holdRepair(p);assert.throws(()=>j.holdRepair(p),/REPAIR_RECOVERY_REQUIRED/);
  assert.throws(()=>j.failRepair({...p,transaction_id:'foreign'},'STOPPED'),/REPAIR_NOT_OWNED/);
  j.counter('primitive_events',7);j.close();
  j=new Journal(root,2);
  try {assert.throws(()=>j.recover(),/REPAIR_RECOVERY_REQUIRED/);assert.equal(j.counter('primitive_events'),7);}
  finally {j.close();}
  const db=new DatabaseSync(join(root,'actions.sqlite'),{readOnly:true});
  try {assert.equal(db.prepare('SELECT state FROM repair_holds').get()!.state,'HELD');
    assert.equal(db.prepare("SELECT COUNT(*) AS n FROM events WHERE kind='repair_pause_intent'").get()!.n,1);}
  finally {db.close();}
});

test('failed repair retains consumed plan and usage after close',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-repair-failed-'));t.after(()=>rmSync(root,{recursive:true}));
  const p=plan(),j=new Journal(root,1);j.holdRepair(p);j.counter('primitive_events',3);
  j.failRepair(p,'REPAIR_DEADLINE_EXPIRED');j.close();
  const next=new Journal(root,2);
  try {assert.throws(()=>next.recover(),/REPAIR_RECOVERY_REQUIRED/);assert.equal(next.counter('primitive_events'),3);}
  finally {next.close();}
  const db=new DatabaseSync(join(root,'actions.sqlite'),{readOnly:true});
  try {assert.equal(db.prepare('SELECT state FROM repair_holds').get()!.state,'RECOVERY_REQUIRED');}
  finally {db.close();}
});

test('private repair HTTP rejects public token, browser origin, duplicate fields and undeclared operations',async t=>{
  let calls=0;const p=plan();
  const server=await serveRepair({pauseRepair:async input=>{calls++;assert.deepEqual(input,p);return {paused:true};},
    repairStatus:()=>{calls++;throw new Error('private filesystem credential detail');}},'private-token');
  t.after(()=>{server.closeAllConnections();server.close();});
  const address=server.address();assert.ok(address && typeof address!=='string');
  const url=`http://127.0.0.1:${address.port}/v1/repair`;
  const request={schema:'strata/WorkerRepairRequest/1',request_id:'request',operation:'pause',plan:p};
  const send=(body:string,token='private-token',extra:Record<string,string>={})=>fetch(url,{method:'POST',
    headers:{authorization:`Bearer ${token}`,'content-type':'application/json',...extra},body});
  assert.equal((await send(JSON.stringify(request),'gameplay-token')).status,403);
  assert.equal((await send(JSON.stringify(request),'private-token',{origin:'http://localhost'})).status,403);
  for(const body of [JSON.stringify({...request,operation:'resume'}),JSON.stringify({...request,secret:true}),
    JSON.stringify(request).replace('"operation":"pause"','"operation":"pause","operation":"status"'),
    JSON.stringify({...request,plan:{...p,epoch:0}})])assert.equal((await send(body)).status,400);
  assert.equal(calls,0);
  const oversized=await send(' '.repeat(4097)).catch(()=>null);
  assert.notEqual(oversized?.status,200);assert.equal(calls,0);
  const accepted=await send(JSON.stringify(request));assert.equal(accepted.status,200);
  assert.equal((await accepted.json() as {status:string}).status,'ok');assert.equal(calls,1);
  const failure=await send(JSON.stringify({...request,operation:'status'}));assert.equal(failure.status,400);
  assert.doesNotMatch(await failure.text(),/filesystem|credential|private-token/);assert.equal(calls,2);
});
