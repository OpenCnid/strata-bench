import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { ActionLane, RELEASE_TIMEOUT_MS, type Backend, type PrimitiveEmitter } from '../src/actions.js';
import { Journal } from '../src/journal.js';
import { type Action, type ActionBatch, Fault, mono } from '../src/protocol.js';
import { SpatialPages, type Snapshot } from '../src/pagination.js';
import { serve } from '../src/server.js';
import { EventEmitter } from 'node:events';
import type { Bot } from 'mineflayer';
import { Vec3 } from 'vec3';
import { trackBodyRevision } from '../src/body_revision.js';
import { DatabaseSync } from 'node:sqlite';

/** Synthetic backend only. These tests do not establish Minecraft mechanics or T03. */
class SyntheticBackend implements Backend {
  revision = 1; connected = true; dispatched = 0; stopped = 0;
  task: (signal: AbortSignal, emit: PrimitiveEmitter) => Promise<void | 'emitted'> = async () => {};
  snapshot(): Snapshot {
    return {captured_mono_ms: mono(), state_revision: this.revision,
      state: {dimension: 'minecraft:overworld', position: {x:0,y:64,z:0}, yaw:0,pitch:0,
      health:20,food:20,inventory:[],window:null,nearby_blocks:[],nearby_entities:[],
      active_request_id:null,connected:this.connected,truncated:false,next_cursor:null}};
  }
  async execute(_action: Action, signal: AbortSignal, emit: PrimitiveEmitter) {
    this.dispatched++; return await this.task(signal,emit);
  }
  stop(): void | Promise<void> {this.stopped++;}
  disconnect() {this.connected=false;}
  recipeList(after: number) {
    if (after !== 0) throw new Fault('OUT_OF_ORDER');
    return {recipes:[{recipe_id:'fixture:public_recipe',supported:true}],next_cursor:null,revision:1};
  }
}
function fixture(t: test.TestContext, epoch = 1, actions: string[] = ['look_at']) {
  const dir=mkdtempSync(join(tmpdir(),'strata-fixture-'));
  const journal=new Journal(dir,epoch); const backend=new SyntheticBackend();
  const lane=new ActionLane({campaign_id:'c',agent_id:'a',epoch,lease_id:'lease'},'a'.repeat(64),
    backend,journal,actions,100,60000);
  t.after(async () => {
    try { await lane.close(); }
    catch (error) {
      // Fault-injection cases intentionally leave an unclean worker; closing must retain the fault.
      assert.ok(error instanceof Fault && ['INPUT_RELEASE_FAILED','EVIDENCE_UNAVAILABLE'].includes(error.code));
      assert.equal(lane.health().fenced, true);
    } finally { journal.close(); rmSync(dir,{recursive:true}); }
  });
  const batch = (request_id='r',seq=1): ActionBatch => {
    const o=lane.observe();
    return {schema:'mcbench/ActionBatch/1',is_example:false,campaign_id:'c',agent_id:'a',epoch,
      seq,recorded_at:new Date().toISOString(),lease_id:'lease',request_id,observation_id:o.observation_id,
      mode:'structured',expected_state_revision:o.state_revision,capability_digest:'a'.repeat(64),
      control_revision:epoch,keymap_digest:null,deadline_at:new Date(Date.now()+1000).toISOString(),
      duration_ms:1000,action:{kind:'look_at',target:{x:1,y:64,z:0}},events:[],release_at_end:true};
  };
  return {dir,journal,backend,lane,batch};
}

test('event-wait timeout retains capture age and disconnect signal is ordinary player state', async t => {
  const f = fixture(t);
  const before = f.lane.observe();
  const timeout = await f.lane.waitEvents(0, 25);
  assert.equal(timeout.observation_id, before.observation_id);
  assert.equal(timeout.captured_mono_ms, before.captured_mono_ms);
  assert.ok(timeout.age_at_send_ms >= 20);
  f.backend.disconnect();
  f.lane.signals.publish('connection', 'Disconnected.');
  const disconnected = await f.lane.waitEvents(0, 100);
  assert.equal(disconnected.state!.connected, false);
  assert.equal(disconnected.captured_mono_ms, before.captured_mono_ms);
  assert.equal(disconnected.signals[0]!.kind, 'connection');
});
test('acceptance is durable, a lost receipt is queried, and duplicate IDs never redispatch',async t=>{
  const f=fixture(t); const b=f.batch();
  assert.equal(f.lane.act(b).status,'accepted');
  assert.equal(f.backend.dispatched,0);
  assert.equal(f.journal.status('r').status,'accepted');
  await delay(20);
  const terminal=f.lane.act(b);
  assert.equal(terminal.status,'completed'); assert.ok(terminal.result_observation_id);
  assert.equal(f.backend.dispatched,1);
  assert.throws(()=>f.lane.act({...b,duration_ms:900}),/IDEMPOTENCY_CONFLICT/);
});

test('idle heartbeat preserves action authority but actual body changes and age still reject', async t => {
  const f=fixture(t);
  const bot=Object.assign(new EventEmitter(),{entity:{position:new Vec3(0,64,0),velocity:new Vec3(0,0,0),
    yaw:0,pitch:0,onGround:true},game:{dimension:'overworld'}});
  const tracker=trackBodyRevision(bot as unknown as Bot,()=>{f.backend.revision++;});
  t.after(()=>tracker.close());
  const unchanged=f.batch();bot.emit('move');bot.emit('physicsTick');
  assert.equal(f.lane.act(unchanged).status,'accepted');
  await delay(20);assert.equal(f.backend.dispatched,1);
  const current=f.lane.observe(true);
  const next={...f.batch(),request_id:'after-heartbeat',seq:2,observation_id:current.observation_id,
    expected_state_revision:current.state_revision};
  bot.entity.position.x+=.00001;bot.emit('physicsTick');
  assert.throws(()=>f.lane.act(next),/REVISION_CONFLICT/);
  bot.entity.position.x=0;bot.emit('forcedMove');
  assert.throws(()=>f.lane.act(next),/REVISION_CONFLICT/);
  const fresh=f.lane.observe(true);
  fresh.captured_mono_ms=mono()-2001;
  bot.emit('move');
  assert.throws(()=>f.lane.act({...next,observation_id:fresh.observation_id,
    expected_state_revision:fresh.state_revision}),/STALE_OBSERVATION/);
  assert.equal(f.backend.dispatched,1);
});
test('stale scope, state, observation, sequence and unsupported action cannot dispatch',async t=>{
  const f=fixture(t); const b=f.batch();
  for (const [change,error] of [
    [{agent_id:'sibling'},'FORBIDDEN'],[{epoch:0},'STALE_EPOCH'],[{lease_id:'other'},'LEASE_EXPIRED'],
    [{expected_state_revision:999},'REVISION_CONFLICT'],[{observation_id:'missing'},'STALE_OBSERVATION'],
    [{seq:3},'OUT_OF_ORDER'],[{capability_digest:'b'.repeat(64)},'CAPABILITY_MISSING'],
    [{deadline_at:'2000-01-01T00:00:00Z'},'DEADLINE_EXCEEDED'],
    [{action:{kind:'chat',text:'/op me'}},'FORBIDDEN'],
    [{action:{kind:'craft',recipe_id:'minecraft:planks',count:1,window_id:0,expected_window_revision:0}},'MECHANIC_UNSUPPORTED'],
    [{is_example:true},'PRECONDITION_FAILED'],[{private_score:5},'SCHEMA_UNSUPPORTED'],
  ] as const) assert.throws(()=>f.lane.act({...b,...change}),new RegExp(error));
  await delay(10); assert.equal(f.backend.dispatched,0);
});
test('mutation lane rejects overlap and cancellation fences late completion',async t=>{
  const f=fixture(t); let finish: (()=>void) | undefined;
  f.backend.task=async (_s,emit)=>{emit();await new Promise<void>(r=>{finish=r;});};
  f.lane.act(f.batch()); await delay(20);
  assert.throws(()=>f.lane.act(f.batch('r2',2)),/ACTION_IN_PROGRESS/);
  assert.equal((await f.lane.cancel('r')).status,'cancelled');
  finish!(); await delay(20);
  assert.equal(f.journal.status('r').status,'cancelled');
  assert.throws(()=>f.lane.act(f.batch('r2',2)),/LEASE_EXPIRED/);
  assert.equal(f.backend.dispatched,1);
});

test('recipe navigation rejects malformed selectors and remains unavailable in the Mineflayer action profile',async t=>{
  const f=fixture(t); const base=f.batch();
  const action={kind:'recipe_navigate' as const,source:'jei' as const,control:'category_next' as const,
    source_generation:1,expected_screen_generation:2,expected_screen_revision:3,expected_page_revision:'a'.repeat(64)};
  for(const patch of [{source:'admin'},{control:'history'},{mouse_x:10},{widget:'private'},
    {source_generation:true},{expected_screen_generation:-1},{expected_screen_revision:1.5},
    {expected_page_revision:'a'.repeat(64)+'\n'},{expected_page_revision:'A'.repeat(64)}]) {
    assert.throws(()=>f.lane.act({...base,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
  }
  assert.throws(()=>f.lane.act({...base,action}),/MECHANIC_UNSUPPORTED/);
  assert.throws(()=>f.lane.act({...base,action:{...action,control:'history_back'}}),/MECHANIC_UNSUPPORTED/);
  await delay(10); assert.equal(f.backend.dispatched,0);
});
test('deadline cancels without a model round trip',async t=>{
  const f=fixture(t);
  f.backend.task=async signal=>{await delay(1000,undefined,{signal});};
  f.lane.act({...f.batch(),duration_ms:30}); await delay(100);
  assert.equal(f.journal.status('r').status,'cancelled');
  assert.equal(f.journal.status('r').error_code,'DEADLINE_EXCEEDED'); assert.ok(f.backend.stopped);
});
test('uncertain partial effect is retained, stops controls and blocks the next mutation',async t=>{
  const f=fixture(t); f.backend.task=async (_s,emit)=>{emit();throw new Error('private stack canary');};
  f.lane.act(f.batch()); await delay(20);
  assert.equal(f.journal.status('r').status,'unknown');
  assert.equal(f.journal.status('r').requires_resync,true);
  assert.equal(f.journal.counter('primitive_events'),1);
  assert.throws(()=>f.lane.act(f.batch('r2',2)),/LEASE_EXPIRED/);
  assert.doesNotMatch(JSON.stringify(f.journal.status('r')),/canary/);
});
test('primitive charge and exact attribution commit before emission; duplicates retain one charge',async t=>{
  const f=fixture(t); const b=f.batch();
  f.backend.task=async (_signal,emit)=>{
    emit();
    const read=new DatabaseSync(join(f.dir,'actions.sqlite'),{readOnly:true});
    try {
      const row=read.prepare("SELECT body FROM events WHERE kind='primitive_charge'").get() as {body:string};
      const charge=JSON.parse(row.body);
      assert.equal(charge.request_id,b.request_id); assert.equal(charge.action_seq,b.seq);
      assert.equal(charge.charge_seq,1); assert.equal(charge.action_charge_seq,1);
      assert.equal(charge.emission_confirmed,false); assert.equal(charge.safety_release,false);
      assert.equal(f.journal.counter('primitive_events'),1);
    } finally {read.close();}
  };
  f.lane.act(b); await delay(30);
  assert.equal(f.journal.status('r').status,'completed');
  assert.equal(f.lane.act(b).emitted_events,1);
  assert.equal(f.journal.counter('primitive_events'),1);
});
test('failed charge journal prevents emission and rolls its counter back atomically',async t=>{
  const f=fixture(t); let emitted=false;
  const write=new DatabaseSync(join(f.dir,'actions.sqlite'));
  try {write.exec("CREATE TRIGGER synthetic_failure BEFORE INSERT ON events WHEN NEW.kind='primitive_charge' " +
    "BEGIN SELECT RAISE(ABORT,'synthetic disk fault'); END");} finally {write.close();}
  f.backend.task=async (_signal,emit)=>{emit();emitted=true;};
  f.lane.act(f.batch()); await delay(30);
  assert.equal(emitted,false); assert.equal(f.journal.counter('primitive_events'),0);
  assert.equal(f.journal.status('r').status,'failed');
});
test('release charges survive uncertainty with explicit safety attribution',async t=>{
  const f=fixture(t);
  f.backend.task=async (_signal,emit)=>{emit();emit('safety_release');throw new Error('unknown effect');};
  f.lane.act(f.batch()); await delay(30);
  assert.equal(f.journal.status('r').status,'unknown');
  const read=new DatabaseSync(join(f.dir,'actions.sqlite'),{readOnly:true});
  try {
    const charges=read.prepare("SELECT body FROM events WHERE kind='primitive_charge' ORDER BY cursor").all() as {body:string}[];
    assert.deepEqual(charges.map(r=>JSON.parse(r.body).safety_release),[false,true]);
    assert.deepEqual(charges.map(r=>JSON.parse(r.body).charge_seq),[1,2]);
    assert.equal(f.journal.counter('primitive_events'),2);
  } finally {read.close();}
});
test('pre-dispatch failure does not assert uncertain effects',async t=>{
  const f=fixture(t); f.backend.task=async()=>{throw new Fault('PRECONDITION_FAILED');};
  f.lane.act(f.batch()); await delay(20);
  assert.equal(f.journal.status('r').status,'failed');
  assert.equal(f.journal.status('r').requires_resync,false);
});
test('coalesced and disconnected observations retain their capture time',async t=>{
  const f=fixture(t); const a=f.lane.observe(); await delay(10);
  assert.equal(f.lane.observe().observation_id,a.observation_id);
  f.backend.connected=false; const b=f.lane.observe(true);
  assert.equal(b.captured_mono_ms,a.captured_mono_ms); assert.ok(b.age_at_send_ms>0);
  assert.equal(b.state?.connected,false);
});
test('journal restores unresolved actions as unknown and keeps primitive consumption',t=>{
  const dir=mkdtempSync(join(tmpdir(),'strata-recovery-'));
  t.after(()=>rmSync(dir,{recursive:true}));
  const j=new Journal(dir,1); const b=fixture(t).batch();
  j.accept(b,{schema:'mcbench/ActionAck/1',is_example:false,campaign_id:'c',agent_id:'a',epoch:1,seq:1,
    recorded_at:new Date().toISOString(),request_id:'r',action_seq:1,status:'executing',emitted_events:2,
    completed_mono_ms:null,release_confirmed:false,error_code:null,requires_resync:false,result_observation_id:null});
  j.counter('primitive_events',2); j.close();
  const next=new Journal(dir,2); next.recover();
  assert.equal(next.status('r').status,'unknown'); assert.equal(next.status('r').emitted_events,null);
  assert.equal(next.counter('primitive_events'),2); next.close();
  assert.throws(()=>new Journal(dir,2),/STALE_EPOCH/);
});
test('one executor lock excludes a second worker before action acceptance',t=>{
  const f=fixture(t); assert.throws(()=>new Journal(f.dir,2),/EEXIST/);
});
test('loopback gateway rejects wrong auth, scope, malformed JSON and settings; CLI reaches same worker',async t=>{
  const f=fixture(t); const token='test-fixture-token';
  const server=await serve(f.lane,token,{keybindings:false,lease_id:'lease'});
  t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address(); assert.ok(address && typeof address!=='string');
  const url=`http://127.0.0.1:${address.port}/v1/game`;
  const request={schema:'strata/GameRequest/1',request_id:'rpc',campaign_id:'c',agent_id:'a',epoch:1,
    deadline_at:new Date(Date.now()+5000).toISOString(),method:'observe',action:null,target_request_id:null,after:null};
  async function call(body: unknown, auth=token) {
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${auth}`},body:JSON.stringify(body)});
    return await r.json() as {status:string;error?:{code:string};result?:unknown};
  }
  assert.equal((await call(request,'wrong')).error?.code,'FORBIDDEN');
  assert.equal((await call({...request,agent_id:'other'})).error?.code,'FORBIDDEN');
  assert.equal((await call({...request,private_canary:1})).error?.code,'SCHEMA_UNSUPPORTED');
  assert.equal((await call({...request,method:'controls.apply'})).error?.code,'CAPABILITY_MISSING');
  assert.equal((await call(request)).status,'ok');
  const grant=join(f.dir,'own-grant.json');
  writeFileSync(grant,JSON.stringify({url,token,campaign_id:'c',agent_id:'a',epoch:1}));
  const cli=fileURLToPath(new URL('../src/cli.js',import.meta.url));
  const result=await promisify(execFile)(process.execPath,[cli,'observe','--json'],{env:{...process.env,STRATA_GAME_GRANT:grant}});
  assert.equal(JSON.parse(result.stdout).result.agent_id,'a');
  const recipes = await promisify(execFile)(process.execPath,[cli,'recipes','--after','0','--json'],
    {env:{...process.env,STRATA_GAME_GRANT:grant}});
  assert.equal(JSON.parse(recipes.stdout).result.recipes[0].recipe_id,'fixture:public_recipe');
  assert.equal((await call({...request,method:'recipes.list'})).error?.code,'SCHEMA_UNSUPPORTED');
  const query={source:'jei',category:'minecraft:crafting',item_id:'minecraft:furnace',role:'output',after:0};
  assert.equal((await call({...request,method:'recipes.query',recipe_query:query})).error?.code,'CAPABILITY_MISSING');
  assert.equal((await call({...request,method:'recipes.page'})).error?.code,'CAPABILITY_MISSING');
  assert.equal((await call({...request,method:'recipes.page',recipe_query:query})).error?.code,'SCHEMA_UNSUPPORTED');
  assert.equal((await call({...request,recipe_query:query})).error?.code,'SCHEMA_UNSUPPORTED');
  assert.equal((await call({...request,method:'recipes.query',recipe_query:{...query,include_hidden:true}})).error?.code,'SCHEMA_UNSUPPORTED');
  f.lane.signals.publish('health','Health changed.');
  const events = await promisify(execFile)(process.execPath,[cli,'wait-events','--after','0','--json'],
    {env:{...process.env,STRATA_GAME_GRANT:grant}});
  assert.equal(JSON.parse(events.stdout).result.signals[0].kind,'health');
  assert.equal(f.backend.dispatched,0);
  const accepted = await promisify(execFile)(process.execPath,[cli,'look-at','--x','1','--y','64','--z','0','--json'],
    {env:{...process.env,STRATA_GAME_GRANT:grant}}).catch(e=>e as {code:number;stdout:string;stderr:string});
  assert.equal(JSON.parse(accepted.stdout).result.status,'accepted');
  await delay(20); assert.equal(f.backend.dispatched,1);
  assert.match(accepted.stderr,/request_id/);
});
test('disconnect while an upstream action is pending fences locally',async t=>{
  const f=fixture(t);
  f.backend.task=async signal=>{await delay(10000,undefined,{signal});};
  f.lane.act(f.batch()); await delay(10); f.backend.connected=false; await delay(60);
  assert.equal(f.journal.status('r').status,'unknown');
  assert.equal(f.journal.status('r').requires_resync,true);
});

test('idle disconnect also fences the epoch and a spontaneous reconnect cannot reuse it', async t => {
  const f = fixture(t); const before = f.batch();
  f.backend.connected = false;
  assert.deepEqual(f.lane.health(), {connected:false, connected_once:true,
    fenced:true, reason:'CONNECTION_LOST'});
  // Simulate a backend silently restoring the same revision/connection.
  f.backend.connected = true;
  assert.throws(() => f.lane.act(before), /LEASE_EXPIRED/);
  await f.lane.fence('CONNECTION_LOST');
  assert.equal(f.backend.connected, false);
  assert.equal(f.backend.dispatched, 0);
});

test('initial connecting state is not ready and does not consume a recovery fence', t => {
  const directory = mkdtempSync(join(tmpdir(), 'strata-connect-'));
  const journal = new Journal(directory, 1); const backend = new SyntheticBackend();
  backend.connected = false;
  const lane = new ActionLane({campaign_id:'c',agent_id:'a',epoch:1,lease_id:'lease'},
    'a'.repeat(64), backend, journal, ['look_at'], 100, 60000);
  t.after(async () => {await lane.close();journal.close();rmSync(directory,{recursive:true});});
  assert.deepEqual(lane.health(), {connected:false, connected_once:false, fenced:false, reason:null});
  assert.throws(() => lane.observe(), /PRECONDITION_FAILED/);
  backend.connected = true;
  assert.deepEqual(lane.health(), {connected:true, connected_once:true, fenced:false, reason:null});
  assert.equal(lane.observe().state!.connected, true);
});

test('real backend reports a blocked authentication cache before any spawn or dispatch', async t => {
  const {MineflayerBackend} = await import('../src/adapter.js');
  const {protectedCache, lockCache} = await import('../src/auth_cache.js');
  const directory = mkdtempSync(join(tmpdir(), 'strata-startup-failure-'));
  const cache = protectedCache(join(directory, 'credentials'), true);
  const unlock = lockCache(cache);
  const journal = new Journal(directory, 1);
  const backend = new MineflayerBackend({host:'127.0.0.1',port:1,username:'synthetic',profilesFolder:cache});
  const lane = new ActionLane({campaign_id:'c',agent_id:'a',epoch:1,lease_id:'lease'},
    'a'.repeat(64), backend, journal, ['look_at'], 100, 60000);
  t.after(async () => {await lane.close();journal.close();unlock();rmSync(directory,{recursive:true});});
  await delay(60);
  assert.deepEqual(lane.health(), {connected:false,connected_once:false,fenced:true,reason:'AUTH_CACHE_IN_USE'});
  assert.equal(journal.counter('primitive_events'), 0);
  // A late connection cannot revive this failed startup's authority.
  backend.connected = true;
  lane.health();
  await lane.fence('AUTH_CACHE_IN_USE');
  assert.equal(lane.health().fenced, true);
});

test('disconnect callbacks cannot recurse through fencing or replace terminal receipts', async t => {
  const f = fixture(t);
  f.backend.task = async (signal, emit) => {emit(); await delay(1000, undefined, {signal});};
  f.lane.act(f.batch()); await delay(20);
  let callbacks = 0;
  f.backend.disconnect = () => {
    callbacks++; f.backend.connected = false;
    void f.lane.fence('NESTED_DISCONNECT');
  };
  await f.lane.fence('CONNECTION_LOST');
  assert.equal(callbacks, 1);
  const receipt = f.journal.status('r');
  assert.equal(receipt.status, 'unknown');
  assert.equal(receipt.error_code, 'CONNECTION_LOST');
  assert.equal(f.journal.counter('primitive_events'), 1);
  await delay(20);
  assert.deepEqual(f.journal.status('r'), receipt);
});
test('primitive budget cannot be multiplied by retries or commands',async t=>{
  const f=fixture(t);
  f.journal.counter('primitive_events',99);
  f.backend.task=async (_s,emit)=>{emit();emit();};
  f.lane.act(f.batch()); await delay(20);
  assert.equal(f.journal.counter('primitive_events'),100);
  assert.equal(f.journal.status('r').error_code,'BUDGET_EXHAUSTED');
  assert.equal(f.journal.status('r').status,'unknown');
  assert.ok(f.backend.stopped>0);
});
test('paged observations retain age/revision, do not recapture, and journal before planner admission', async t => {
  const f = fixture(t); const base = f.backend.snapshot(); let captures = 0; let delivered = 0;
  const pages = new SpatialPages();
  f.backend.snapshot = (cursor?: string) => {
    if (cursor) return pages.page(cursor, base.state.dimension);
    captures++;
    return pages.capture({...base, blocks: Array.from({length: 260}, (_, x) => ({position: {x, y: 0, z: 0},
      block_id: 'fixture:block', observed_at: new Date().toISOString()})), entities: [],
      promote: () => { delivered++; }});
  };
  const first = f.lane.observe(); const cursor = first.state!.next_cursor!;
  assert.equal(delivered, 1);
  f.backend.revision = 2;
  const second = await f.lane.observePage(cursor);
  assert.equal(second.captured_mono_ms, first.captured_mono_ms);
  assert.equal(second.state_revision, 1); assert.ok(second.age_at_send_ms >= 490);
  assert.equal(captures, 1); assert.equal(delivered, 2);
  assert.equal(second.state!.nearby_blocks[0]!.position.x, 128);
  const batch = {...f.batch(), observation_id: second.observation_id, expected_state_revision: 1};
  assert.throws(() => f.lane.act(batch), /REVISION_CONFLICT/);
  const original = f.journal.event;
  f.journal.event = () => { throw new Error('fixture disk full'); };
  assert.throws(() => f.lane.observe(false, second.state!.next_cursor!), /disk full/);
  assert.equal(delivered, 2);
  f.journal.event = original;
  f.backend.connected = false;
  await assert.rejects(f.lane.observePage(cursor), /PRECONDITION_FAILED/);
});
test('scoped CLI follows opaque snapshot cursors and the gateway rejects cursor confusion', async t => {
  const f = fixture(t); const base = f.backend.snapshot(); const pages = new SpatialPages();
  f.backend.snapshot = (cursor?: string) => cursor ? pages.page(cursor, base.state.dimension) :
    pages.capture({...base, blocks: [], entities: Array.from({length: 130}, (_, i) => ({id: String(i),
      type: 'fixture:entity', position: {x: 0, y: 0, z: 0}, observed_at: new Date().toISOString()})), promote: () => {}});
  const server = await serve(f.lane, 'page-fixture-token', {});
  t.after(() => new Promise<void>(resolve => server.close(() => resolve())));
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const grant = join(f.dir, 'grant.json'); const url = `http://127.0.0.1:${address.port}/v1/game`;
  writeFileSync(grant, JSON.stringify({url, token: 'page-fixture-token', campaign_id: 'c', agent_id: 'a', epoch: 1}));
  const cli = fileURLToPath(new URL('../src/cli.js', import.meta.url));
  const first = f.lane.observe();
  const response = await promisify(execFile)(process.execPath, [cli, 'observe', '--cursor', first.state!.next_cursor!, '--json'],
    {env: {...process.env, STRATA_GAME_GRANT: grant}});
  const page = JSON.parse(response.stdout).result;
  assert.equal(page.state.nearby_entities[0].id, '128'); assert.equal(page.state.nearby_entities.length, 2);
  assert.equal(page.captured_mono_ms, first.captured_mono_ms);
  const request = {schema: 'strata/GameRequest/1', request_id: 'rpc', campaign_id: 'c', agent_id: 'a', epoch: 1,
    deadline_at: new Date(Date.now() + 5000).toISOString(), method: 'observe', action: null,
    target_request_id: null, after: null, cursor: first.state!.next_cursor};
  const wrong = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json',
    Authorization: 'Bearer page-fixture-token'}, body: JSON.stringify(request)});
  assert.equal((await wrong.json() as {error: {code: string}}).error.code, 'SCHEMA_UNSUPPORTED');
});
test('input-only emission is never promoted to completed or blindly re-emitted', async t => {
  const f = fixture(t); f.backend.task = async (_signal, emit) => {emit(); return 'emitted';};
  const b = f.batch(); f.lane.act(b); await delay(20);
  assert.equal(f.journal.status('r').status, 'emitted');
  assert.ok(f.journal.status('r').result_observation_id);
  assert.equal(f.lane.act(b).status, 'emitted'); assert.equal(f.backend.dispatched, 1);
});
test('held-use admission leaves room for release and cancellation retains its charge', async t => {
  const f = fixture(t, 1, ['use_item']);
  const b = {...f.batch(), action: {kind: 'use_item', hand: 'main', hold_ms: 1000} as const};
  f.journal.counter('primitive_events', 99);
  assert.throws(() => f.lane.act(b), /BUDGET_EXHAUSTED/); assert.equal(f.backend.dispatched, 0);
  const running = fixture(t, 1, ['use_item']);
  running.backend.task = async (signal, emit) => {
    emit(); signal.addEventListener('abort', () => emit('safety_release'), {once: true});
    await delay(5000, undefined, {signal});
  };
  const batch = {...running.batch(), action: b.action}; running.lane.act(batch); await delay(20);
  const cancelled = await running.lane.cancel(batch.request_id);
  assert.equal(cancelled.emitted_events, 2); assert.equal(running.journal.counter('primitive_events'), 2);
});
test('a failed local stop never produces a confirmed release or a successful terminal receipt', async t => {
  const f = fixture(t); f.backend.task = async (_signal, emit) => {emit();};
  f.backend.stop = () => {throw new Error('fixture stop failure');};
  f.lane.act(f.batch()); await delay(20);
  const ack = f.journal.status('r');
  assert.equal(ack.status, 'unknown'); assert.equal(ack.release_confirmed, false);
  assert.equal(ack.error_code, 'INPUT_RELEASE_FAILED'); assert.equal(ack.requires_resync, true);
  assert.equal(f.backend.connected, false); assert.equal(ack.emitted_events, 1);
});

test('an asynchronous release keeps the action pending and excludes a second mutation', async t => {
  const f = fixture(t); let confirm!: () => void; let releases = 0;
  const confirmation = new Promise<void>(resolve => {confirm = resolve;});
  f.backend.stop = () => {releases++; return confirmation;};
  f.backend.task = async (_signal, emit) => {emit(); return 'emitted';};
  const batch = f.batch(); f.lane.act(batch); await delay(30);
  assert.equal(f.journal.status('r').status, 'executing');
  assert.equal(f.journal.status('r').release_confirmed, false);
  assert.equal(f.lane.observe(true).state!.active_request_id, 'r');
  assert.throws(() => f.lane.act(f.batch('other', 2)), /ACTION_IN_PROGRESS/);
  assert.equal(releases, 1);
  confirm(); await delay(20);
  const ack = f.journal.status('r');
  assert.equal(ack.status, 'emitted'); assert.equal(ack.release_confirmed, true);
  assert.equal(f.lane.observe().state!.active_request_id, null);
  assert.equal(f.lane.act(batch).status, 'emitted'); assert.equal(f.backend.dispatched, 1);
});

test('cancel during asynchronous release wins over success and concurrent stops share confirmation', async t => {
  const f = fixture(t); let confirm!: () => void; let releases = 0;
  const confirmation = new Promise<void>(resolve => {confirm = resolve;});
  f.backend.stop = () => {releases++; return confirmation;};
  f.lane.act(f.batch()); await delay(20);
  let returned = false;
  const cancelled = f.lane.cancel('r').then(ack => {returned = true; return ack;});
  const stopped = f.lane.stopAll(); const closed = f.lane.close();
  await delay(20);
  assert.equal(returned, false); assert.equal(releases, 1);
  assert.equal(f.journal.status('r').status, 'executing');
  confirm(); const [ack] = await Promise.all([cancelled, stopped, closed]);
  assert.equal(ack.status, 'cancelled'); assert.equal(ack.release_confirmed, true);
  assert.equal(releases, 1); assert.equal(f.backend.connected, false);
});

test('a rejected asynchronous release produces unknown without leaking the rejection', async t => {
  const f = fixture(t);
  f.backend.stop = async () => {await delay(10); throw new Error('private release canary');};
  f.lane.act(f.batch()); await delay(50);
  const ack = f.journal.status('r');
  assert.equal(ack.status, 'unknown'); assert.equal(ack.release_confirmed, false);
  assert.equal(ack.error_code, 'INPUT_RELEASE_FAILED');
  assert.doesNotMatch(JSON.stringify(ack), /canary/);
  await assert.rejects(f.lane.stopAll(), /INPUT_RELEASE_FAILED/);
  await assert.rejects(f.lane.close(), /INPUT_RELEASE_FAILED/);
});

test('a hung release times out, and a late resolution cannot rewrite the unknown receipt', async t => {
  const f = fixture(t); let confirm!: () => void;
  const confirmation = new Promise<void>(resolve => {confirm = resolve;});
  f.backend.stop = () => confirmation;
  f.lane.act(f.batch());
  const started = mono(); await delay(RELEASE_TIMEOUT_MS + 150);
  const ack = f.journal.status('r');
  assert.equal(ack.status, 'unknown'); assert.equal(ack.release_confirmed, false);
  assert.ok(mono() - started < RELEASE_TIMEOUT_MS + 1000);
  confirm(); await delay(20);
  assert.deepEqual(f.journal.status('r'), ack);
  assert.equal(f.backend.connected, false);
});

test('a blocking release cannot evade its bound by starving the timeout callback', async t => {
  const f = fixture(t);
  f.backend.stop = () => {
    const until = mono() + RELEASE_TIMEOUT_MS + 20;
    while (mono() < until) { /* synthetic unresponsive backend */ }
  };
  f.lane.act(f.batch()); await delay(RELEASE_TIMEOUT_MS + 80);
  assert.equal(f.journal.status('r').status, 'unknown');
  assert.equal(f.journal.status('r').release_confirmed, false);
  assert.equal(f.lane.health().reason, 'INPUT_RELEASE_FAILED');
});

test('journal failure after release prevents a clean-stop claim and preserves recoverable intent', async t => {
  const f = fixture(t); const update = f.journal.update.bind(f.journal);
  f.journal.update = ack => {
    if (ack.status !== 'executing') throw new Error('private disk failure');
    update(ack);
  };
  f.lane.act(f.batch()); await delay(30);
  assert.equal(f.journal.status('r').status, 'executing');
  assert.equal(f.lane.health().reason, 'EVIDENCE_UNAVAILABLE');
  assert.equal(f.backend.connected, false);
  await assert.rejects(f.lane.close(), /EVIDENCE_UNAVAILABLE/);
  f.journal.update = update;
  f.journal.recover();
  assert.equal(f.journal.status('r').status, 'unknown');
  assert.equal(f.journal.status('r').release_confirmed, false);
});

test('stop-all fences idle and accepted-but-undispatched work before waiting for release', async t => {
  const idle = fixture(t); const oldBatch = idle.batch();
  const stopped = idle.lane.stopAll();
  assert.throws(() => idle.lane.act(oldBatch), /LEASE_EXPIRED/);
  await stopped; assert.equal(idle.backend.dispatched, 0);
  const queued = fixture(t); queued.lane.act(queued.batch());
  await queued.lane.stopAll(); await delay(10);
  assert.equal(queued.backend.dispatched, 0);
  assert.equal(queued.journal.status('r').status, 'cancelled');
  assert.equal(queued.journal.status('r').release_confirmed, true);
});

test('HTTP stop-all waits for asynchronous release and returns an error on uncertainty', async t => {
  const f = fixture(t); let reject!: (error: Error) => void;
  f.backend.stop = () => new Promise<void>((_, fail) => {reject = fail;});
  const server = await serve(f.lane, 'release-token', {});
  t.after(() => new Promise<void>(resolve => server.close(() => resolve())));
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const request = {schema:'strata/GameRequest/1', request_id:'stop', campaign_id:'c', agent_id:'a', epoch:1,
    deadline_at:new Date(Date.now()+5000).toISOString(), method:'stop_all', action:null, target_request_id:null, after:null};
  let returned = false;
  const response = fetch(`http://127.0.0.1:${address.port}/v1/game`, {method:'POST', headers:{
    'Content-Type':'application/json', Authorization:'Bearer release-token'}, body:JSON.stringify(request)})
    .then(async r => {returned = true; return await r.json() as {status:string; error:{code:string}};});
  for (let i = 0; !reject && i < 100; i++) await delay(5);
  assert.ok(reject); assert.equal(returned, false);
  reject(new Error('private failure'));
  const result = await response;
  assert.equal(result.status, 'error'); assert.equal(result.error.code, 'INPUT_RELEASE_FAILED');
});
