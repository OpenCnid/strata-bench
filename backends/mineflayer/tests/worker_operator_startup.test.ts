/** Actual parent/fork/control path, with a synthetic IPC executor and no network. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {existsSync,mkdtempSync,mkdirSync,readFileSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {setTimeout as delay} from 'node:timers/promises';

for(const profile of ['vanilla1','vanilla2','forge'] as const)
test(`operator supervisor startup ${profile} preserves its scope and drain boundary`,async t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-operator-startup-'));
  const state=join(root,'state');mkdirSync(state);
  const common={purpose:'manual-conformance',state_directory:state,max_wall_ms:10000,primitive_limit:10,
    campaign_id:'synthetic-copy',agent_id:'body',epoch:1,lease_id:'fresh-lease'};
  const uuid='00000000-0000-4000-8000-000000000001';
  const config=profile==='forge' ? {...common,schema:'strata/ForgeDevelopmentWorker/2',server_kind:'e9e',
    backend:'forge_client',pack_version:'1.27.0',connection_file:root,process_guard_file:root,
    guard_python:process.execPath,native_fingerprint:'a'.repeat(64),body_fingerprint:'b'.repeat(64)} :
    {...common,schema:`strata/DevelopmentWorker/${profile==='vanilla1'?1:2}`,server_kind:'vanilla',
      host:'127.0.0.1',port:25565,username:'synthetic',auth_cache:root,
      ...(profile==='vanilla2'?{expected_player_uuid:uuid}:{})};
  const path=join(root,'config.json');writeFileSync(path,JSON.stringify(config));
  const preload=join(root,'synthetic-child.mjs');
  writeFileSync(preload,`import {writeFileSync} from 'node:fs';
    import {join} from 'node:path';
    if(process.send) {
      process.once('disconnect',()=>process.exit(1));
      let active=false;
      setInterval(()=>process.send(active?{kind:'alive',health:{connected:true,connected_once:true,fenced:false,reason:null}}:{kind:'startup_alive'}),100);
      process.send({kind:'bootstrap_ready'});
      process.on('message',m=>{
        if(m==='stop')process.exit(0);
        if(m && typeof m==='object' && m.config) {
          writeFileSync(join(m.config.state_directory,'synthetic-child-config.json'),JSON.stringify(m.config));
          active=true;process.send({kind:'gateway_ready',port:12345});
        }
      });
      await new Promise(()=>{});
    }`);
  const parent=spawn(process.execPath,['--import',pathToFileURL(preload).href,
    fileURLToPath(new URL('../src/worker.js',import.meta.url)),path,'--operator-stop'],
    {windowsHide:true,stdio:['pipe','pipe','pipe']});
  const ended=once(parent,'exit');let error='';parent.stderr.on('data',c=>{error+=c;});parent.stdout.resume();
  t.after(async()=>{if(parent.exitCode===null && parent.signalCode===null)parent.kill();
    await ended;rmSync(root,{recursive:true,force:true});});
  const grant=join(state,'grant-1.json');const until=performance.now()+8000;
  while(!existsSync(grant) && parent.exitCode===null && performance.now()<until)await delay(20);
  if(profile==='forge') {
    assert.equal((await ended)[0],1);assert.match(error,/CAPABILITY_MISSING/);
    assert.equal(existsSync(grant),false);assert.equal(existsSync(join(state,'synthetic-child-config.json')),false);return;
  }
  assert.ok(existsSync(grant),error || 'no gateway');
  assert.deepEqual(JSON.parse(readFileSync(join(state,'synthetic-child-config.json'),'utf8')),config);
  parent.stdin.write(JSON.stringify({schema:'strata/WorkerStop/1',policy:'operator-stdin-stop2250/1',
    request_id:'stop-1',campaign_id:common.campaign_id,agent_id:common.agent_id,epoch:1,lease_id:common.lease_id})+'\n');
  assert.equal((await ended)[0],0,error);
  const receipt=JSON.parse(readFileSync(join(state,'supervisor-stop-1.json'),'utf8'));
  assert.equal(receipt.status,'pass');assert.equal(receipt.forced,false);assert.equal(receipt.drain_limit_ms,2250);
  assert.deepEqual(receipt.scope,{campaign_id:common.campaign_id,agent_id:common.agent_id,epoch:1,lease_id:common.lease_id});
});
