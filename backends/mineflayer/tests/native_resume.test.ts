import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { NativeGameClient, NativeOutcomeUnknown } from '../src/native_game.js';
import { resumeDecision } from '../src/native_resume.js';

const decision={schema:'strata/NativeSettingsResumeDecision/1',policy:'operator-owned-settings-resume/1',
  resume_id:'resume-1',worker_plan:{schema:'strata/WorkerRepairPlan/1',policy:'operator-owned-fixed-repair-pause/1',
    campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease-1',transaction_id:'tx',
    plan_digest:'a'.repeat(64),expires_unix_ms:10000},expected_revision:4,expected_digest:'b'.repeat(64),
  completion_phase:'committed',verification_ref:'cas:sha256:'+'c'.repeat(64),connection_generation:1,lease_until_unix_ms:9000};
function state(){return {schema:'strata/NativeSettingsResumeState/1',decision,source_instance:'native-1',current_instance:'native-1',
  input_resumed:true,effects_verified_by_native:false,health:{schema:'strata/NativeGameLane/1',fenced:false,
    fence_token:'opaque',reason:null,journal_healthy:true,epoch:1,active_request_id:null,attempted_primitive_events:7,primitive_limit:100}};}

test('resume decisions reject scope, lease, head, verification and namespace violations',()=>{
  for(const change of [{extra:true},{lease_until_unix_ms:10001},{completion_phase:'applied_pending_verification'},
    {expected_revision:0},{connection_generation:-1},{verification_ref:'file:private'},{resume_id:'../foreign'}]) {
    assert.throws(()=>resumeDecision({...decision,...change}));
  }
  assert.deepEqual(resumeDecision(decision),decision);
});
test('lost resume response is queried by status without another mutation',async t=>{
  const calls:string[]=[];
  const server=createServer(async(req,res)=>{
    let raw='';for await(const chunk of req)raw+=chunk;
    const request=JSON.parse(raw);calls.push(request.operation);
    if(request.operation==='settings_resume'){res.destroy();return;}
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,session_id:'session',
      status:'completed',result:state(),error_code:null}));
  });
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>server.close());
  const address=server.address();assert(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'a'.repeat(64),fingerprint:'b'.repeat(64),operator_development_only:true});
  await assert.rejects(client.call('settings_resume',decision),NativeOutcomeUnknown);
  assert.equal((await client.call('settings_resume_status',{transaction_id:'tx'})).input_resumed,true);
  assert.deepEqual(calls,['settings_resume','settings_resume_status']);
});
test('transport rejects forged live state and foreign transaction receipts',async t=>{
  let result:any=state();
  const server=createServer(async(req,res)=>{
    let raw='';for await(const chunk of req)raw+=chunk;const request=JSON.parse(raw);
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,session_id:'session',
      status:'completed',result,error_code:null}));
  });
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>server.close());
  const address=server.address();assert(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'a'.repeat(64),fingerprint:'b'.repeat(64),operator_development_only:true});
  for(const change of [{input_resumed:1},{effects_verified_by_native:0},{effects_verified_by_native:true},
    {current_instance:'reopened'},{extra:true}]){
    result={...state(),...change};await assert.rejects(client.call('settings_resume_status',{transaction_id:'tx'}));
  }
  for(const change of [{fenced:true,reason:'STOP_ALL'},{epoch:2},{journal_healthy:false}]){
    result=state();Object.assign(result.health,change);await assert.rejects(client.call('settings_resume_status',{transaction_id:'tx'}));
  }
  result=state();await assert.rejects(client.call('settings_resume_status',{transaction_id:'foreign'}));
  result={...state(),input_resumed:false,current_instance:'reopened'};
  Object.assign(result.health,{fenced:true,reason:'RECOVERY_REQUIRED'});
  assert.equal((await client.call('settings_resume_status',{transaction_id:'tx'})).input_resumed,false);
});
