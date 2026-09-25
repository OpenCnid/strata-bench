/** Real worker/config/journal wiring with synthetic token provider and bot transport. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync,mkdirSync,writeFileSync,rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { DatabaseSync } from 'node:sqlite';
import mineflayer, {type Bot} from 'mineflayer';
import prismarineAuth from 'prismarine-auth';
import type {Client,ClientOptions} from 'minecraft-protocol';
import { PlayerIdentity,profileId } from '../src/player_identity.js';
import { protectedCache,writePrivateJson } from '../src/auth_cache.js';
import { workerConfig } from '../src/worker_config.js';
import { workerLane } from '../src/worker_lane.js';
import { Journal } from '../src/journal.js';
import type {ActionLane} from '../src/actions.js';

const uuid='00000000-0000-4000-8000-000000000001';
test('authentication, server UUID and closed lifetime all gate identity receipts',()=>{
  for(const failure of ['unauthenticated','provider','server','closed']) {
    const p=new PlayerIdentity(uuid);
    if(failure==='provider')assert.throws(()=>p.authenticate('b'.repeat(32)),/AUTH_PLAYER_MISMATCH/);
    else if(failure!=='unauthenticated')p.authenticate(profileId(uuid));
    if(failure==='closed')p.close();
    assert.throws(()=>p.spawn(failure==='server'?'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb':uuid),/AUTH_PLAYER_MISMATCH/);
    assert.throws(()=>p.spawn(uuid),/AUTH_PLAYER_MISMATCH/);
  }
  const p=new PlayerIdentity(uuid);p.authenticate(profileId(uuid));
  assert.equal(p.spawn(uuid).spawn_seq,1);assert.equal(p.spawn(uuid).spawn_seq,2);
  assert.throws(()=>p.authenticate(profileId(uuid)),/AUTH_PLAYER_MISMATCH/);
  assert.throws(()=>p.spawn(uuid),/AUTH_PLAYER_MISMATCH/);
  for(const value of ['','0'.repeat(32),uuid.toUpperCase().replace('4000','FFFF'),'../secret'])
    assert.throws(()=>profileId(value),/AUTH_PLAYER_IDENTITY_INVALID/);
});

for(const outcome of ['matched','server-mismatch','journal-failure'] as const)
test(`configured worker ${outcome} gates readiness and keeps identity private`,async t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-bound-worker-'));
  let active:ActionLane|undefined,opened:Journal|undefined;
  t.after(async()=>{await active?.close();opened?.close();rmSync(root,{recursive:true,force:true});});
  const state=join(root,'state');mkdirSync(state);
  const cache=protectedCache(join(root,'cache'),true);
  writePrivateJson(join(cache,'account.json'),{schema:'strata/MinecraftAccount/1',account:'avatar1',profile_id:profileId(uuid)});
  t.mock.method(prismarineAuth.Authflow.prototype,'getMinecraftJavaToken',async()=>({
    token:'SYNTHETIC-SECRET',profile:{id:profileId(uuid),name:'SyntheticAvatar',skins:[],capes:[]},
    certificates:{profileKeys:{private:{},public:{},expiresOn:new Date(Date.now()+60000)}}}));
  const client=new EventEmitter() as Client;
  let connections=0,ended=false,connected!:()=>void;
  const handoff=new Promise<void>(resolve=>{connected=resolve;});
  const bot=Object.assign(new EventEmitter(),{_client:client,game:{dimension:'overworld'},
    end:()=>{if(!ended){ended=true;bot.emit('end');}}});
  client.end=()=>{bot.end();};client.on('error',(error:Error)=>{bot.emit('error',error);});
  t.mock.method(mineflayer,'createBot',(options:unknown)=>{
    const auth=(options as {auth:(c:Client,o:ClientOptions)=>void}).auth;
    auth(client,{username:'avatar1',connect:()=>{connections++;connected();}} as ClientOptions);
    return bot as unknown as Bot;
  });
  const value={schema:'strata/DevelopmentWorker/2',purpose:'manual-conformance',server_kind:'vanilla',
    state_directory:state,max_wall_ms:60000,primitive_limit:10,campaign_id:'probe-copy',agent_id:'body',
    epoch:1,lease_id:'fresh-lease',host:'127.0.0.1',port:25565,username:'avatar1',auth_cache:cache,
    expected_player_uuid:uuid};
  const file=join(root,'config.json');writeFileSync(file,JSON.stringify(value));
  const config=workerConfig(file,process.cwd());
  for(const patch of [{expected_player_uuid:null},{expected_player_uuid:undefined},
    {schema:'strata/DevelopmentWorker/1'},{schema:'strata/DevelopmentWorker/3'},{extra:true}]) {
    writeFileSync(file,JSON.stringify({...value,...patch}));
    assert.throws(()=>workerConfig(file,process.cwd()));
  }
  const journal=new Journal(state,1);opened=journal;
  if(outcome==='journal-failure') {
    const original=journal.event.bind(journal);
    t.mock.method(journal,'event',(kind:string,body:unknown)=>{if(kind==='player_identity')throw Error('PRIVATE-CANARY');original(kind,body);});
  }
  const {lane:base}=await workerLane(config,journal);const lane=base as ActionLane;
  active=lane;
  await handoff;assert.equal(connections,1);assert.equal(lane.health().connected,false);
  client.uuid=outcome==='server-mismatch'?'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb':uuid;
  bot.emit('spawn');
  assert.equal(lane.health().connected,outcome==='matched');
  if(outcome!=='matched') {
    assert.equal(ended,true);client.uuid=uuid;bot.emit('spawn');assert.equal(lane.health().connected,false);
  }
  const reader=new DatabaseSync(join(state,'actions.sqlite'),{readOnly:true});
  const records=reader.prepare("SELECT body FROM events WHERE kind='player_identity'").all() as {body:string}[];
  reader.close();assert.equal(records.length,outcome==='matched'?1:0);
  if(records.length) {
    assert.equal(JSON.parse(records[0]!.body).connected_player_uuid,uuid);
    if(process.env.STRATA_TEST_IDENTITY_RECEIPT)
      writeFileSync(process.env.STRATA_TEST_IDENTITY_RECEIPT,records[0]!.body,{flag:'wx'});
  }
  const publicSignals=JSON.stringify(lane.signals.read(0));
  assert.equal(publicSignals.includes(uuid),false);assert.equal(publicSignals.includes('SYNTHETIC-SECRET'),false);
  assert.equal(publicSignals.includes('PRIVATE-CANARY'),false);
});
