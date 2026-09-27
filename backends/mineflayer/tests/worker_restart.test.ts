import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { NativeGameClient, NativeOutcomeUnknown, nativeCapabilities } from '../src/native_game.js';
import { restartCheckpoint, restartState, type RestartCheckpoint } from '../src/native_restart.js';
import { serveRestart } from '../src/worker_restart.js';
import { WORKER_REPAIR_POLICY, type RepairPlan } from '../src/worker_repair.js';

const checkpoint:RestartCheckpoint={schema:'strata/NativeSettingsRestartCheckpoint/1',source_instance:'old',
  request:{schema:'strata/NativeSettingsRestartRequest/1',transaction_id:'repair',plan_digest:'a'.repeat(64),
    restart_id:'restart',expected_revision:1,expected_digest:'b'.repeat(64)}};

test('uncertain native continuation sends one mutation and can only be resolved by an explicit status read',async t=>{
  const calls:string[]=[];
  const server=createServer(async(req,res)=>{
    let raw='';for await(const chunk of req)raw+=chunk;
    const request=JSON.parse(raw);calls.push(request.operation);
    if(request.operation==='settings_restart_continue') {res.destroy();return;}
    assert.equal(request.operation,'settings_restart_status');
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,session_id:'session',
      status:'completed',error_code:null,result:{schema:'strata/NativeSettingsRestartState/1',checkpoint,
        phase:'continued',current_instance:'new',continued_instance:'new',primitive_events:9,
        expires_unix_ms:Date.now()+10000,input_resumed:false}}));
  });server.listen(0,'127.0.0.1');await once(server,'listening');
  t.after(()=>{server.closeAllConnections();server.close();});
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint:'a'.repeat(64),operator_development_only:true});
  await assert.rejects(client.call('settings_restart_continue',checkpoint,500),NativeOutcomeUnknown);
  assert.deepEqual(calls,['settings_restart_continue']);
  assert.equal((await client.call('settings_restart_status',{restart_id:'restart'},500)).phase,'continued');
  assert.deepEqual(calls,['settings_restart_continue','settings_restart_status']);
  assert.doesNotMatch(JSON.stringify(nativeCapabilities(true)),/settings_restart/);
});

test('restart proof cannot imply resume or reuse its source as continued instance',()=>{
  const state={schema:'strata/NativeSettingsRestartState/1',checkpoint,phase:'prepared',current_instance:'old',
    continued_instance:null,primitive_events:7,expires_unix_ms:12345,input_resumed:false};
  assert.deepEqual(restartCheckpoint(checkpoint),checkpoint);
  assert.deepEqual(restartState(state),state);
  assert.equal(restartState({...state,phase:'continued',current_instance:'new',continued_instance:'new'}).phase,'continued');
  for(const patch of [{input_resumed:true},{phase:'continued'},{phase:'prepared',continued_instance:'new'},
    {phase:'continued',continued_instance:'old'},{phase:'continued',continued_instance:'new'},
    {primitive_events:-1},{expires_unix_ms:0},{extra:true}])assert.throws(()=>restartState({...state,...patch}));
  for(const patch of [{source_instance:'../outside'},{schema:'strata/NativeSettingsRestartCheckpoint/2'},
    {request:{...checkpoint.request,expected_revision:0}},{request:{...checkpoint.request,extra:true}}])
    assert.throws(()=>restartCheckpoint({...checkpoint,...patch}));
});

test('private replacement endpoint rejects gameplay credentials and malformed authority before dispatch',async t=>{
  let calls=0;
  const plan:RepairPlan={schema:'strata/WorkerRepairPlan/1',policy:WORKER_REPAIR_POLICY,campaign_id:'campaign',
    agent_id:'avatar',epoch:1,lease_id:'lease',transaction_id:'repair',plan_digest:'a'.repeat(64),expires_unix_ms:Date.now()+10000};
  const server=await serveRestart(async(op,p,c,paths)=>{
    calls++;assert.deepEqual(p,plan);assert.deepEqual(c,checkpoint);
    if(op==='status')throw new Error('private credential/path');
    assert.equal(op,'detach');assert.equal(paths,null);return {phase:'detached'};
  },'private-token');
  t.after(()=>{server.closeAllConnections();server.close();});
  const address=server.address();assert.ok(address && typeof address!=='string');
  const url=`http://127.0.0.1:${address.port}/v1/restart`;
  const request={schema:'strata/WorkerRestartRequest/1',request_id:'request',operation:'detach',plan,checkpoint,paths:null};
  const send=(body:string,token='private-token',extra:Record<string,string>={})=>fetch(url,{method:'POST',
    headers:{authorization:`Bearer ${token}`,'content-type':'application/json',...extra},body});
  assert.equal((await send(JSON.stringify(request),'gameplay-token')).status,403);
  assert.equal((await send(JSON.stringify(request),'private-token',{origin:'http://localhost'})).status,403);
  for(const body of [JSON.stringify({...request,operation:'resume'}),JSON.stringify({...request,extra:true}),
    JSON.stringify({...request,operation:'attach'}),JSON.stringify({...request,paths:{connection_file:'x',process_guard_file:'y'}}),
    JSON.stringify(request).replace('"operation":"detach"','"operation":"detach","operation":"status"'),
    JSON.stringify({...request,plan:{...plan,epoch:0}}),JSON.stringify({...request,checkpoint:{...checkpoint,extra:true}})])
    assert.equal((await send(body)).status,400);
  const oversized=await send(' '.repeat(16385)).catch(()=>null);assert.notEqual(oversized?.status,200);
  assert.equal(calls,0);
  assert.equal((await send(JSON.stringify(request))).status,200);assert.equal(calls,1);
  const failure=await send(JSON.stringify({...request,operation:'status'}));assert.equal(failure.status,400);
  assert.doesNotMatch(await failure.text(),/credential|private-token|\/path/);assert.equal(calls,2);
});
