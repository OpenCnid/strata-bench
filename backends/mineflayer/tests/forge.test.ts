import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn, execFile } from 'node:child_process';
import { once } from 'node:events';
import { promisify } from 'node:util';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { createServer } from 'node:http';
import { ForgeLane } from '../src/forge_lane.js';
import { forgeCapabilities } from '../src/forge_capabilities.js';
import { NativeGameClient, NativeOutcomeUnknown, RECIPE_QUERY_POLICY, QUEST_POLICY, QUEST_TEXT_POLICY, QUEST_COMPONENTS_POLICY, QUEST_MENU_POLICY, strictJson, type NativeOperation, type NativeResults } from '../src/native_game.js';
import { Journal } from '../src/journal.js';
import { serve, type GameLane } from '../src/server.js';
import { workerConfig, type ForgeConfig } from '../src/worker_config.js';
import { workerLane } from '../src/worker_lane.js';
import { digest, Fault, mono, type ActionBatch, type Observation, type ActionAck } from '../src/protocol.js';

const fingerprint = 'a'.repeat(64);
const manifest = forgeCapabilities(fingerprint); const capability = digest(manifest);
const java = process.env.STRATA_CLIENT_TEST_JAVA;
const classpathFile = process.env.STRATA_CLIENT_TEST_CLASSPATH;
const python = process.env.STRATA_GUARD_TEST_PYTHON;
const jvm = {skip: !java || !classpathFile ? 'Explicit pinned Java and fixture classpath required' : false};
const guardedJvm = {skip: jvm.skip || (!python || process.platform !== 'win32' ? 'Explicit Python and Windows guard required' : false)};
const repo = fileURLToPath(new URL('../../../../', import.meta.url));
const recipeQuery = {source:'jei',category:'minecraft:crafting',item_id:'fixture:output',role:'output',after:0} as const;

function recipePagePayload():NativeResults['recipe_page'] {
  const content:Omit<NativeResults['recipe_page'],'schema'|'body_fingerprint'|'connection_generation'|'revision'>={
    policy:'jei-task-drawn-slot-header-controls-empty-loop/4',source:'jei',coverage:'slot_header_control_draw_operands',complete:false,
    source_generation:1,screen_generation:2,screen_revision:3,chapter_id:'0000000000000001',quest_id:'0000000000000002',
    headers:[{kind:'category',state:'text',text:'Visible café <&> "title" \\u2028 \u2028\u2029 😀'},{kind:'page',state:'text',text:'1/4'}],
    controls:[{kind:'category_next',state:'enabled'},{kind:'category_previous',state:'disabled'},
      {kind:'page_next',state:'clipped'},{kind:'page_previous',state:'clipped'}],
    layouts:[{category_id:'minecraft:crafting',clipped:false,slots:[{index:0,role:'input',display:{kind:'item',id:'minecraft:stone',amount:2}}]}]};
  return {schema:'strata/NativeRecipePage/4',body_fingerprint:fingerprint,connection_generation:1,...content,revision:digest(content)};
}

test('copied recipe page transport checks schema, coverage, bytes, slots and canonical digest',async t=>{
  const base=recipePagePayload();let payload:unknown=base,posts=0;
  const rehash=(value:Record<string,unknown>)=>{const {schema,body_fingerprint,connection_generation,revision,...content}=value;return {...value,revision:digest(content)};};
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,{});assert.equal(request.operation,'recipe_page');
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>server.close());
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('recipe_page'),base);
  payload=rehash({...base,layouts:[]});assert.deepEqual(await client.call('recipe_page'),payload);
  payload={...base,layouts:[]};await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  for(const patch of [{headers:[]},{controls:[]},{schema:'strata/NativeRecipePage/3'},
    {policy:'jei-task-drawn-slot-header-controls/3'}]) {
    payload=rehash({...base,layouts:[],...patch});await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  for(const patch of [{complete:true},{complete:0},{coverage:'full'},{policy:'old'},{source:'private'},
    {chapter_id:null},{quest_id:'0000000000000002\n'},{source_generation:-1},{screen_revision:true},{focus:'private'},
    {layouts:null},{layouts:Array(33).fill(base.layouts[0])}]) {
    payload=rehash({...base,...patch});await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  for(const display of [{kind:'empty',id:'private:value'},{kind:'unsupported',raw:'private'},
    {kind:'item',id:'minecraft:stone',amount:0},{kind:'item',id:'minecraft:stone',amount:true},
    {kind:'fluid',id:'minecraft:water',amount:2147483648},{kind:'item',id:'minecraft:stone\n',amount:1}]) {
    payload=rehash({...base,layouts:[{...base.layouts[0],slots:[{index:0,role:'input',display}]}]});
    await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  const slot=base.layouts[0]!.slots[0]!;
  for(const controls of [base.controls.slice(1),[...base.controls,base.controls[0]],base.controls.toReversed(),
    [base.controls[0],base.controls[0],...base.controls.slice(2)],
    [{...base.controls[0],state:'unknown'},...base.controls.slice(1)],
    [{...base.controls[0],state:['enabled']},...base.controls.slice(1)],
    [{...base.controls[0],widget:'private'},...base.controls.slice(1)]]) {
    payload=rehash({...base,controls});await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  payload={...base,controls:[{...base.controls[0],state:'disabled'},...base.controls.slice(1)]};
  await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  for(const headers of [[],[base.headers[0]],base.headers.toReversed(),
    [{kind:'category',state:'text',text:null},base.headers[1]],
    [{kind:'category',state:'text',text:'x'.repeat(1025)},base.headers[1]],
    [{kind:'category',state:'clipped',text:'private'},base.headers[1]],
    [{kind:'category',state:'text',text:'ok',full_title:'private'},base.headers[1]]]) {
    payload=rehash({...base,headers});await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  payload={...base,headers:[{kind:'category',state:'text',text:'\ud800'},base.headers[1]]};
  await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  for(const header of [{kind:'category',state:'text',text:'😀'.repeat(1024)},
    {kind:'category',state:'clipped',text:null},{kind:'category',state:'unsupported',text:null}]) {
    payload=rehash({...base,headers:[header,base.headers[1]]});assert.deepEqual(await client.call('recipe_page'),payload);
  }
  for(const role of [['input'],null,0,{},'unknown']) {
    payload=rehash({...base,layouts:[{...base.layouts[0],slots:[{...slot,role}]}]});
    await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  for(const slots of [[slot,slot],[{...slot,index:2}],Array(129).fill(slot),
    Array.from({length:128},(_,index)=>({...slot,index,display:{kind:'item',id:`minecraft:${'x'.repeat(220)}`,amount:1}}))]) {
    payload=rehash({...base,layouts:[{...base.layouts[0],slots}]});await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  }
  payload={...base,screen_revision:4};await assert.rejects(client.call('recipe_page'),/GAME_RESPONSE_INVALID/);
  payload=rehash({...base,layouts:[{category_id:'minecraft:crafting',clipped:true,slots:[{index:7,role:'render_only',display:{kind:'unsupported'}}]}]});
  assert.deepEqual(await client.call('recipe_page'),payload);
  const before=posts;await assert.rejects(client.call('recipe_page',{team_id:'private'}));assert.equal(posts,before);
});

test('private native JSON rejects duplicate, malformed, excessive-depth and trailing input', () => {
  for (const body of ['{"x":1,"x":2}','{"x":1,"\\u0078":2}','{"a":[{"b":1,"b":2}]}',
    '{"x":NaN}','[1,]','{} private', '['.repeat(22)+'0'+']'.repeat(22), '{"x":"unterminated}']) {
    assert.throws(() => strictJson(body), /GAME_RESPONSE_INVALID/);
  }
  assert.deepEqual(strictJson('{"x":-1.25,"y":[null,true,"quote\\\""]}'), {x:-1.25,y:[null,true,'quote"']});
});

test('Forge capabilities are a separate unqualified identity and config cannot silently select another backend', t => {
  const root = mkdtempSync(join(tmpdir(),'strata-forge-config-')); t.after(() => rmSync(root,{recursive:true}));
  const connection = join(root,'connection.json'); writeFileSync(connection,'{}');
  const config = {schema:'strata/ForgeDevelopmentWorker/2',purpose:'manual-conformance',server_kind:'e9e',
    backend:'forge_client',pack_version:'1.27.0',connection_file:connection,native_fingerprint:fingerprint,
    body_fingerprint:fingerprint,state_directory:root,max_wall_ms:1000,primitive_limit:100,
    campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease',process_guard_file:connection,guard_python:process.execPath};
  const path = join(root,'worker.json'); writeFileSync(path,JSON.stringify(config));
  assert.equal(workerConfig(path,repo).schema,'strata/ForgeDevelopmentWorker/2');
  assert.equal(manifest.backend,'forge_client'); assert.equal(manifest.campaign_admission,false);
  assert.equal(manifest.keybindings,false); assert.equal(manifest.motor.completion,'emitted-input-only');
  assert.equal(manifest.contract_minor,38);
  assert.equal(manifest.motor.block_target,'observed-outline-centers64-local16/1');
  for (const patch of [{backend:'mineflayer'},{server_kind:'vanilla'},{pack_version:'latest'},
    {private_extra:true},{purpose:'campaign'},{connection_file:repo},{schema:'strata/ForgeDevelopmentWorker/1'},
    {process_guard_file:undefined},{guard_python:'relative-python.exe'}]) {
    writeFileSync(path,JSON.stringify({...config,...patch})); assert.throws(() => workerConfig(path,repo));
  }
});

test('native transport polls one POST, validates identities and never replays a lost mutation', async t => {
  let posts = 0, gets = 0; let mode = 'poll'; let wire: Record<string,unknown> = {};
  const server = createServer(async (req,res) => {
    let body = ''; for await (const chunk of req) body += chunk;
    if (req.method === 'POST') {posts++; wire = JSON.parse(body); if (mode === 'drop') {req.socket.destroy(); return;}}
    else gets++;
    const pending = mode === 'poll' && req.method === 'POST';
    const response = {schema:'strata/NativeGameResponse/1',request_id:wire.request_id,
      session_id:mode === 'wrong' ? 'sibling-session' : 'session',status:pending ? 'accepted' : 'completed',
      result:pending ? null : {schema:'strata/NativeGameIdentity/1',body_fingerprint:fingerprint,connection_generation:1},error_code:null};
    res.writeHead(pending ? 202 : 200, {'Content-Type':'application/json'}); res.end(JSON.stringify(response));
  });
  await new Promise<void>(resolve => server.listen(0,'127.0.0.1',resolve));
  t.after(() => new Promise<void>(resolve => server.close(() => resolve())));
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const client = new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.equal((await client.call('identity')).body_fingerprint,fingerprint); assert.equal(posts,1); assert.equal(gets,1);
  mode = 'wrong'; await assert.rejects(client.call('identity'),/GAME_RESPONSE_INVALID/);
  mode = 'drop'; const before = posts;
  await assert.rejects(client.call('stop_all',{},100),NativeOutcomeUnknown); assert.equal(posts,before+1);
  assert.equal(gets,1);
  assert.throws(() => new NativeGameClient({...client.connection,host:'example.com'} as never),/GAME_CONNECTION_INVALID/);
});

test('recipe transport rejects hidden fields, malformed recipes and non-advancing cursors without retries', async t => {
  let payload:unknown;
  let posts = 0;
  const server = createServer(async (req,res) => {
    let body = ''; for await (const chunk of req) body += chunk;
    posts++; const request = JSON.parse(body);
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,
      session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve => server.listen(0,'127.0.0.1',resolve));
  t.after(() => new Promise<void>(resolve => server.close(() => resolve())));
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const client = new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  const page = {schema:'strata/NativeRecipeList/1',body_fingerprint:fingerprint,connection_generation:1,
    revision:2,recipes:[{recipe_id:'test:expert',supported:true,serializer:'minecraft:crafting_shapeless',width:0,height:0,
      ingredients:[['test:changed']],result:{item_id:'test:output',count:2}}],next_cursor:null};
  payload = page; assert.deepEqual(await client.call('recipes',{after:0}),page);
  for (const patch of [{next_cursor:0},{next_cursor:9},{recipes:[{recipe_id:'test:hidden',supported:false,ingredients:[['test:secret']]}]},
    {recipes:[{...page.recipes[0],ingredients:[[]]}]},{recipes:[page.recipes[0],page.recipes[0]]},
    {recipes:[{...page.recipes[0],result:{item_id:'test:output',count:65}}]}]) {
    payload = {...page,...patch}; const before = posts;
    await assert.rejects(client.call('recipes',{after:0}),/GAME_RESPONSE_INVALID/); assert.equal(posts,before+1);
  }
});

for (const source of ['jei','emi'] as const) test(`${source} recipe transport binds query and policy, rejects injected fields and never retries`,async t => {
  const selectedQuery={...recipeQuery,source};
  const page = {schema:'strata/NativeRecipeQuery/1',body_fingerprint:fingerprint,connection_generation:1,
    revision:1,query:selectedQuery,policy:RECIPE_QUERY_POLICY,source_generation:1,
    recipes:[{recipe_id:'fixture:expert',supported:false,craft_authority:'discovery_only'}],next_cursor:null};
  let payload:unknown=page, posts=0;
  const server=createServer(async (req,res) => {
    let body='';for await (const chunk of req) body+=chunk;
    const request=JSON.parse(body);posts++;
    assert.equal(request.operation,'recipe_query');assert.deepEqual(request.args,selectedQuery);
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,
      session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address !== 'string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('recipe_query',selectedQuery),page);
  for (const patch of [{query:{...selectedQuery,role:'input'}},{policy:'global-recipes'},{source_generation:-1},
    {recipes:[{...page.recipes[0],hidden_solution:'canary'}]},
    {recipes:[{...page.recipes[0],craft_authority:'arbitrary'}]},
    {recipes:[{...page.recipes[0],supported:0}]},{next_cursor:513},{next_cursor:2}]) {
    payload={...page,...patch};const before=posts;
    await assert.rejects(client.call('recipe_query',selectedQuery),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for (const patch of [{source:'server'},{category:'minecraft:smelting'},{role:'all'},
    {item_id:'*'},{after:-1},{after:513},{after:true},{include_hidden:true}]) {
    await assert.rejects(client.call('recipe_query',{...selectedQuery,...patch}));
  }
  assert.equal(posts,before);
});

test('Thermal discovery transport preserves fluid units and rejects category, hidden-data and authority confusion',async t => {
  const query={source:'jei',category:'thermal:crucible',fluid_id:'fixture:fluid',role:'output',after:0} as const;
  const row={recipe_id:'fixture:machine',supported:true,category:'thermal:crucible',energy_rf:4000,craft_authority:'discovery_only',
    slots:[{role:'input',ingredients:[{kind:'item',item_id:'fixture:input',count:1}]},
      {role:'output',ingredients:[{kind:'fluid',fluid_id:'fixture:fluid',amount_mb:250}]}],output_tooltip:null};
  const page={schema:'strata/NativeRecipeQuery/1',body_fingerprint:fingerprint,connection_generation:1,revision:1,
    query,source_generation:1,policy:RECIPE_QUERY_POLICY,recipes:[row],next_cursor:null};
  let payload:unknown=page,posts=0;
  const server=createServer(async (req,res)=>{
    let body='';for await(const chunk of req) body+=chunk; const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,query);
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('recipe_query',query),page);
  for (const patch of [{category:'thermal:furnace'},{craft_authority:'recipe_book'},{energy_rf:0},{energy_rf:true},
    {energy_rf:2147483648},{supported:1},{hidden_solution:'canary'},{output_tooltip:{kind:'chance',percent:50}},
    {slots:[]},{slots:[row.slots[1],row.slots[0]]},
    {slots:[row.slots[0],{role:'output',ingredients:[{kind:'fluid',fluid_id:'fixture:fluid',amount_mb:0}]}]},
    {slots:[row.slots[0],{role:'output',ingredients:[{kind:'fluid',fluid_id:'fixture:fluid',amount_mb:250,nbt:'hidden'}]}]},
    {slots:[{role:'input',ingredients:[row.slots[0]!.ingredients[0],row.slots[0]!.ingredients[0]]},row.slots[1]]}]) {
    payload={...page,recipes:[{...row,...patch}]};const before=posts;
    await assert.rejects(client.call('recipe_query',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for(const patch of [{item_id:'fixture:also'},{category:'minecraft:crafting'},{category:'thermal:unknown'},
    {include_hidden:true},{after:true},{fluid_id:'*'}]) await assert.rejects(client.call('recipe_query',{...query,...patch}));
  assert.equal(posts,before);
});

test('quest catalog transport rejects hidden fields, sibling selectors and malformed public progress without replay',async t=>{
  const query={source:'ftb_quests',chapter_id:'0000000000000001',after:0};
  const row={kind:'quest',entry_id:'0000000000000002',title:'Visible quest',progress_percent:25,
    completed:false,startable:false,details_visible:true};
  const page={schema:'strata/NativeQuestPage/1',body_fingerprint:fingerprint,connection_generation:1,query,
    source_generation:1,policy:QUEST_POLICY,revision:1,entries:[row],next_cursor:null};
  let payload:unknown=page,posts=0;
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req) body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,query);assert.equal(request.operation,'quests');
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('quests',query),page);
  for(const patch of [{description:'hidden canary'},{team_id:'sibling'},{entry_id:'private-id'},{entry_id:'0000000000000002\n'},{kind:'chapter'},
    {progress_percent:101},{progress_percent:true},{completed:true},{completed:0},{startable:null},
    {startable:true,details_visible:false},{title:'x'.repeat(1025)},{title:'\ud800'}]) {
    payload={...page,entries:[{...row,...patch}]};const before=posts;
    await assert.rejects(client.call('quests',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  for(const patch of [{entries:[row,row]},{next_cursor:2},{source_generation:-1},{policy:'all-quests'},
    {query:{...query,chapter_id:null}}]) {
    payload={...page,...patch};const before=posts;
    await assert.rejects(client.call('quests',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for(const patch of [{team_id:'sibling'},{source:'server'},{chapter_id:'*'},{chapter_id:'0000000000000001\n'},{after:true},{after:4097}])
    await assert.rejects(client.call('quests',{...query,...patch}));
  assert.equal(posts,before);
});

test('quest text transport rejects hidden description and unsupported rich-content leaks without replay',async t=>{
  const query={source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',after:0};
  const page={schema:'strata/NativeQuestText/1',body_fingerprint:fingerprint,connection_generation:1,query,
    source_generation:1,policy:QUEST_TEXT_POLICY,revision:1,title:'Visible quest',subtitle:'Public subtitle',
    description_visible:true,lines:[{kind:'text',text:'Readable description'}],next_cursor:null};
  let payload:unknown=page,posts=0;
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req) body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,query);assert.equal(request.operation,'quest_text');
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('quest_text',query),page);
  for(const patch of [{description_visible:false,lines:[]},{lines:[{kind:'unsupported',text:null},{kind:'page_break',text:null}]}]) {
    payload={...page,...patch};assert.deepEqual(await client.call('quest_text',query),payload);
  }
  for(const patch of [{description_visible:false},{description_visible:1},{team_id:'sibling'},{subtitle:'x'.repeat(1025)},
    {lines:[{kind:'text',text:'\ud800'}]},{lines:[{kind:'unsupported',text:'hidden rich data'}]},
    {lines:[{kind:'text',text:null}]},{lines:[{kind:'raw_nbt',text:null}]},{lines:[],next_cursor:0},{next_cursor:2},
    {lines:Array(33).fill({kind:'text',text:'x'})},{query:{...query,quest_id:query.quest_id+'\n'}},
    {policy:'all-text'},{source_generation:-1}]) {
    payload={...page,...patch};const before=posts;
    await assert.rejects(client.call('quest_text',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for(const patch of [{team_id:'sibling'},{source:'server'},{chapter_id:null},{quest_id:query.quest_id+'\n'},{after:true},{after:513}])
    await assert.rejects(client.call('quest_text',{...query,...patch}));
  assert.equal(posts,before);
});

test('quest component transport enforces display roles, hidden metadata and exact cursor scope',async t=>{
  const query={source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'tasks' as const,after:0};
  const row={entry_id:'0000000000000003',kind:'task',title:'Visible task',tooltip:[{kind:'text',text:'Ordinary tooltip'}],
    task:{completed:false,optional:false,progress_label:'2 / 4'},reward:null};
  const page={schema:'strata/NativeQuestComponents/1',body_fingerprint:fingerprint,connection_generation:1,query,
    source_generation:1,policy:QUEST_COMPONENTS_POLICY,revision:1,entries:[row],next_cursor:null};
  let payload:unknown=page,posts=0;
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,query);assert.equal(request.operation,'quest_components');
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('quest_components',query),page);
  for(const patch of [{command:'hidden command'},{team_id:'sibling'},{kind:'reward'},{entry_id:row.entry_id+'\n'},
    {task:null},{task:{...row.task,completed:1}},{task:{...row.task,progress_label:'x'.repeat(257)}},
    {reward:{claim_state:'claimed',team_reward:false}},{tooltip:[{kind:'unsupported',text:'raw data'}]},
    {tooltip:[{kind:'page_break',text:null}]},{tooltip:[{kind:'text',text:'\ud800'}]},
    {tooltip:Array(65).fill({kind:'text',text:'x'})},{tooltip:[{kind:'text',text:'😀'.repeat(4096)}]}]) {
    payload={...page,entries:[{...row,...patch}]};const before=posts;
    await assert.rejects(client.call('quest_components',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  for(const patch of [{entries:[row,row]},{next_cursor:2},{source_generation:-1},{policy:'raw-definitions'},
    {query:{...query,part:'rewards'}}]) {
    payload={...page,...patch};const before=posts;
    await assert.rejects(client.call('quest_components',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for(const patch of [{team_id:'sibling'},{part:'server_commands'},{chapter_id:null},{quest_id:query.quest_id+'\n'},{after:true},{after:513}])
    await assert.rejects(client.call('quest_components',{...query,...patch}));
  assert.equal(posts,before);
});

test('quest screen transport rejects raw identities, malformed state and unrelated query selectors',async t=>{
  const page={schema:'strata/NativeQuestScreen/1',body_fingerprint:fingerprint,connection_generation:1,
    policy:'ftb-own-team-book-and-task-recipes-state/2',source_generation:1,screen_generation:2,revision:3,
    kind:'quest_book',chapter_id:'0000000000000001',quest_id:'0000000000000002'};
  let payload:unknown=page,posts=0;
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,{});assert.equal(request.operation,'quest_screen');
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',request_id:request.request_id,session_id:'session',
      status:'completed',result:payload,error_code:null}));
  });server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>server.close());
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('quest_screen'),page);
  for(const patch of [{kind:'closed'},{kind:'editor'},{chapter_id:null},{quest_id:'0000000000000002\n'},
    {revision:true},{source_generation:-1},{screen_object:'private'},{policy:'raw'}, {screen_generation:2**53},
    {policy:'ftb-own-team-book-state-navigation/1'},{kind:'task_recipes',quest_id:null},{kind:'task_recipes',chapter_id:null},
    {focus:'private'},{parent_screen:'private'}]) {
    payload={...page,...patch};const before=posts;await assert.rejects(client.call('quest_screen'),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  payload={...page,kind:'closed',chapter_id:null,quest_id:null};assert.deepEqual(await client.call('quest_screen'),payload);
  payload={...page,kind:'task_recipes'};assert.deepEqual(await client.call('quest_screen'),payload);
  const before=posts;await assert.rejects(client.call('quest_screen',{team_id:'private'}));assert.equal(posts,before);
});

test('current quest menu transport rejects private data, false control state and invalid viewport-page identity',async t=>{
  const query={source:'ftb_quests' as const,after:0};
  const row={index:0,item_id:'minecraft:stone',count:1,name:'Stone',tooltip:[{kind:'text',text:'Stone'}]};
  const control={control:'submit',title:'Submit',enabled:false,tooltip:[]};
  const page={schema:'strata/NativeQuestMenu/1',body_fingerprint:fingerprint,connection_generation:1,query,
    source_generation:1,menu_generation:1,policy:QUEST_MENU_POLICY,revision:1,menu_kind:'item_alternatives',
    context:{chapter_id:'0000000000000001',quest_id:'0000000000000002',task_id:'0000000000000003',title:'Valid items'},
    entries:[row],controls:[control],next_cursor:null};
  let payload:unknown=page,posts=0;
  const server=createServer(async(req,res)=>{
    let body='';for await(const chunk of req)body+=chunk;const request=JSON.parse(body);posts++;
    assert.deepEqual(request.args,query);assert.equal(request.operation,'quest_menu');
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({schema:'strata/NativeGameResponse/1',
      request_id:request.request_id,session_id:'session',status:'completed',result:payload,error_code:null}));
  });
  server.listen(0,'127.0.0.1');await once(server,'listening');t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const client=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
    session_id:'session',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
  assert.deepEqual(await client.call('quest_menu',query),page);
  for(const patch of [{nbt:'private'}, {index:1}, {item_id:'minecraft:stone\n'}, {item_id:'minecraft:stone\r'}, {item_id:'minecraft:stone\u2028'}, {count:0}, {count:2147483648},
    {name:'\ud800'}, {tooltip:[{kind:'unsupported',text:'hidden'}]}, {tooltip:[{kind:'page_break',text:null}]},
    {tooltip:Array(65).fill({kind:'text',text:'line'})}, {tooltip:[{kind:'text',text:'😀'.repeat(4096)}]}]) {
    payload={...page,entries:[{...row,...patch}]};const before=posts;
    await assert.rejects(client.call('quest_menu',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  for(const patch of [{screen_identity:'private'}, {context:{...page.context,task_id:page.context.task_id+'\n'}},
    {controls:[control,control]}, {controls:[{...control,enabled:1}]}, {controls:[{...control,control:'admin_submit'}]},
    {controls:[{...control,tooltip:Array(2).fill({kind:'text',text:'x'.repeat(4096)})}]},
    {query:{...query,after:1}},{menu_generation:0},{menu_kind:'reward_table'}, {entries:[row,row]}, {next_cursor:2}, {policy:'all-items'}]) {
    payload={...page,...patch};const before=posts;
    await assert.rejects(client.call('quest_menu',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const choiceRow={index:0,title:'Visible choice',enabled:false,tooltip:[{kind:'text',text:'Visible tooltip'}]};
  const choicePage={...page,menu_kind:'reward_choices',context:{chapter_id:page.context.chapter_id,quest_id:page.context.quest_id,
    reward_id:'0000000000000003',title:'Choose'},entries:[choiceRow],controls:[]};
  payload=choicePage;assert.deepEqual(await client.call('quest_menu',query),choicePage);
  for(const patch of [{table:'private'},{weight:5},{command:'private'},{raw_index:6},{enabled:1},
    {title:'x'.repeat(1025)},{tooltip:[{kind:'unsupported',text:'canary'}]}]) {
    payload={...choicePage,entries:[{...choiceRow,...patch}]};const before=posts;
    await assert.rejects(client.call('quest_menu',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  for(const patch of [{menu_kind:'item_alternatives'},{context:page.context},{entries:[row]},{controls:[control]},
    {context:{...choicePage.context,task_id:'0000000000000004'}},{policy:'ftb-current-item-alternatives-clipped-pages32/2'},
    {policy:'ftb-current-item-choice-clipped-pages32/3'}]) {
    payload={...choicePage,...patch};const before=posts;
    await assert.rejects(client.call('quest_menu',query),/GAME_RESPONSE_INVALID/);assert.equal(posts,before+1);
  }
  const before=posts;
  for(const patch of [{team_id:'sibling'},{task_id:'hidden'},{source:'server'},{after:true},{after:-1},{after:513}])
    await assert.rejects(client.call('quest_menu',{...query,...patch}));
  assert.equal(posts,before);
});

async function fixture(t: test.TestContext, hold = false, recipeMode = false) {
  const root = mkdtempSync(join(tmpdir(),'strata-forge-jvm-'));
  const nativeRoot = join(root,'native'); const state = join(root,'worker'); mkdirSync(nativeRoot); mkdirSync(state);
  const authority = {schema:'strata/NativeGameAuthority/1',campaign_id:'campaign',agent_id:'avatar',
    capability_digest:capability,body_fingerprint:fingerprint,expires_unix_ms:Date.now()+120000,primitive_limit:1000};
  writeFileSync(join(nativeRoot,'game-authority.json'),JSON.stringify(authority));
  const connection = join(root,'connection.json'); const argfile = join(root,'java-args.txt');
  const quote = (x: string) => '"'+x.replaceAll('\\','\\\\').replaceAll('"','\\"')+'"';
  const freeze = join(root,'freeze-client-thread');
  const args = ['-cp',readFileSync(classpathFile!,'utf8').trim(),'io.github.opencnid.strata.client.GameBridgeFixture',connection,nativeRoot,hold ? 'hold' : '-',freeze];
  if(recipeMode)args.unshift('-Dstrata.fixture.taskRecipes=true');
  writeFileSync(argfile,args.map(quote).join('\n'));
  const process = spawn(java!,['@'+argfile],{stdio:['pipe','pipe','pipe'],windowsHide:true});
  let stderr = ''; process.stderr.on('data',(b: Buffer) => {stderr += b.toString();}); process.stdout.resume();
  const ended = once(process,'exit');
  const config: ForgeConfig = {schema:'strata/ForgeDevelopmentWorker/2',purpose:'manual-conformance',server_kind:'e9e',
    backend:'forge_client',pack_version:'1.27.0',connection_file:connection,native_fingerprint:fingerprint,
    body_fingerprint:fingerprint,state_directory:state,max_wall_ms:60000,primitive_limit:1000,
    campaign_id:'campaign',agent_id:'avatar',epoch:1,lease_id:'lease',process_guard_file:join(root,'guard.json'),
    guard_python:python ?? ''};
  let lane: GameLane | undefined; let journal: Journal | undefined;
  t.after(async () => {
    try {await lane?.close();} catch (error) {assert.ok(error instanceof Fault);}
    journal?.close();
    if (!process.killed && process.exitCode === null && process.signalCode === null) process.stdin.end('stop\n');
    const kill = setTimeout(() => {if (process.exitCode === null && process.signalCode === null) process.kill();},5000);
    try {await ended;} finally {clearTimeout(kill);}
    rmSync(root,{recursive:true});
  });
  const until = mono()+20000;
  while (!existsSync(connection) && mono() < until) {
    assert.equal(process.exitCode,null,stderr); await delay(20);
  }
  assert.ok(existsSync(connection),'Fixture connection missing');
  const client = NativeGameClient.fromFile(connection);
  return {root,nativeRoot,config,client,process,freeze,
    async guardConfig(maxWallMs = 5000) {
      assert.ok(python); assert.ok(process.pid);
      const inspect = await promisify(execFile)(python,['-I','-m','mcbench.process_guard','--inspect',String(process.pid)],{windowsHide:true});
      const grant = {schema:'strata/ForgeProcessGuardGrant/1',purpose:'dedicated-development-client-lifetime',
        campaign_id:config.campaign_id,agent_id:config.agent_id,epoch:config.epoch,process:JSON.parse(inspect.stdout),
        expires_unix_ms:Date.now()+120000,max_wall_ms:maxWallMs+5000,connection_file:connection,
        connection_digest:digest(client.connection),native_fingerprint:fingerprint,body_fingerprint:fingerprint,
        capability_digest:capability,primitive_limit:1000};
      writeFileSync(config.process_guard_file,JSON.stringify(grant)); return {...config,max_wall_ms:maxWallMs};
    },
    own(j: Journal, l?: GameLane) {journal = j; lane = l;},
    async start(changes: Partial<ForgeConfig> = {}) {
      const c = {...config,...changes}; journal = new Journal(c.state_directory,c.epoch);
      const result = await ForgeLane.connect(c,capability,client,journal,c.body_fingerprint,c.primitive_limit,c.max_wall_ms);
      lane = result; return {lane:result,journal};
    }};
}
function batch(observation: Observation, request_id = 'request', seq = 1): ActionBatch {
  return {schema:'mcbench/ActionBatch/1',is_example:false,campaign_id:'campaign',agent_id:'avatar',epoch:1,seq,
    recorded_at:new Date().toISOString(),lease_id:'lease',request_id,observation_id:observation.observation_id,
    mode:'structured',expected_state_revision:observation.state_revision,capability_digest:capability,
    control_revision:1,keymap_digest:null,deadline_at:new Date(Date.now()+2000).toISOString(),duration_ms:2000,
    action:{kind:'look_at',target:{x:1,y:65,z:2}},events:[],release_at_end:true};
}
async function terminal(journal: Journal, id = 'request'): Promise<ActionAck> {
  const until = mono()+5000;
  while (mono() < until) {
    const ack = journal.status(id); if (!['accepted','executing'].includes(ack.status)) return ack;
    await delay(20);
  }
  assert.fail('No terminal action receipt');
}

test('actual JVM bound observations, public lane, fresh receipts and charges preserve at-most-once input',jvm,async t => {
  const f = await fixture(t); const {lane,journal} = await f.start();
  const bound = await f.client.call('observe_bound',{cursor:null});
  assert.equal(bound.body_fingerprint,fingerprint); assert.equal(bound.connection_generation,1);
  const first = await lane.observe(); const page = await lane.observePage(first.state!.next_cursor!);
  assert.equal(page.captured_mono_ms,first.captured_mono_ms); assert.equal(page.state_revision,first.state_revision);
  assert.ok(page.age_at_send_ms >= 490); assert.equal(first.state!.position.x,-1.25);
  const b = batch(await lane.observe(true));
  assert.equal(lane.act(b).status,'accepted'); assert.equal(journal.status('request').release_confirmed,false);
  const ack = await terminal(journal); assert.equal(ack.status,'emitted'); assert.equal(ack.release_confirmed,true);
  assert.equal(ack.emitted_events,2); assert.ok(ack.result_observation_id); assert.equal(ack.requires_resync,false);
  assert.equal((await lane.observe()).state!.position.x,-0.25); assert.equal(journal.counter('primitive_events'),3);
  assert.equal(lane.act(b).status,'emitted');
  assert.throws(() => lane.act({...b,duration_ms:1999}),/IDEMPOTENCY_CONFLICT/);
  const nativeLog = readFileSync(join(f.nativeRoot,'game-actions.jsonl'),'utf8');
  assert.equal((nativeLog.match(/"kind":"intent"/g) ?? []).length,1);
  await lane.close(); const charged = journal.counter('primitive_events');
  assert.ok(charged >= 4); assert.equal((await f.client.call('lane_status')).fenced,true);
});

test('expanded gesture envelopes cross the public broker and real JVM once, with synthetic game effects',jvm,async t => {
  const f = await fixture(t); const {lane,journal} = await f.start();
  const actions: NonNullable<ActionBatch['action']>[] = [
    {kind:'use_item',hand:'off',hold_ms:250}, {kind:'attack',entity_id:'fixture-observed'},
    {kind:'interact_entity',entity_id:'fixture-observed'}, {kind:'chat',text:'café 中文 🧭'},
    {kind:'equip',inventory_slot:10,expected_item_id:'minecraft:stone',destination:'hand'},
    {kind:'place',support:{x:0,y:64,z:0},face:{x:0,y:1,z:0},expected_item_id:'minecraft:stone'},
    {kind:'move_to',target:{x:2,y:65,z:2},tolerance:.1},
    {kind:'craft',recipe_id:'fixture:expert',count:1,window_id:0,expected_window_revision:1},
    {kind:'craft',recipe_id:'fixture:expert',count:1,window_id:0,expected_window_revision:1,
      recipe_selection:{query:recipeQuery,source_generation:1,revision:1}},
    {kind:'close_window',window_id:1,expected_window_revision:1},
    {kind:'quest_ui',operation:'open',source:'ftb_quests',source_generation:1,expected_catalog_revision:1},
  ];
  for (const [index, action] of actions.entries()) {
    const request = {...batch(await lane.observe(true),`gesture-${index}`,index+1),action};
    if (action.kind === 'move_to') { request.duration_ms = 30000; request.deadline_at = new Date(Date.now()+30000).toISOString(); }
    lane.act(request); const ack = await terminal(journal,request.request_id);
    assert.equal(ack.status,'emitted'); assert.equal(ack.release_confirmed,true);
    assert.equal(lane.act(request).status,'emitted');
  }
  const events = readFileSync(join(f.nativeRoot,'game-actions.jsonl'),'utf8').trim().split('\n')
    .map(line => JSON.parse(line).payload);
  const intents = events.filter(event => event.kind === 'intent');
  assert.deepEqual(intents.map(event => JSON.parse(event.batch_json).action),actions);
  assert.equal(journal.counter('primitive_events'),actions.length*2+1); // fixture input plus release per envelope, plus arm
});

test('recipe projection binds the original body and connection generation before public delivery',jvm,async t => {
  const f = await fixture(t); const {lane} = await f.start();
  const call = f.client.call.bind(f.client);
  f.client.call = async <K extends NativeOperation>(operation:K,args:Record<string,unknown> = {},timeout?:number):Promise<NativeResults[K]> => {
    const result = await call(operation,args,timeout);
    if (operation === 'recipes') (result as NativeResults['recipes']).connection_generation++;
    return result;
  };
  await assert.rejects(lane.backend.recipeList(0),/GAME_BODY_MISMATCH/);
  assert.equal(lane.health().fenced,true);
});

test('quest screen projection rejects changed body generation before public delivery',jvm,async t=>{
  const f=await fixture(t);const {lane}=await f.start();const call=f.client.call.bind(f.client);
  f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
    const result=await call(operation,args,timeout);
    if(operation==='quest_screen')(result as NativeResults['quest_screen']).connection_generation++;
    return result;
  };
  await assert.rejects(lane.backend.questScreen(),/GAME_BODY_MISMATCH/);assert.equal(lane.health().fenced,true);
});

test('copied recipe page refuses a changed body before scoped delivery',jvm,async t=>{
  const f=await fixture(t);const {lane}=await f.start();const call=f.client.call.bind(f.client);
  f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
    if(operation==='recipe_page')return {...recipePagePayload(),connection_generation:2} as NativeResults[K];
    return call(operation,args,timeout);
  };
  await assert.rejects(lane.backend.recipePage(),/GAME_BODY_MISMATCH/);assert.equal(lane.health().fenced,true);
});

test('stop during a copied page read prevents late public delivery',jvm,async t=>{
  const f=await fixture(t);const {lane}=await f.start();const call=f.client.call.bind(f.client);
  let finish:((page:NativeResults['recipe_page'])=>void)|undefined;
  f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
    if(operation==='recipe_page')return await new Promise<NativeResults['recipe_page']>(resolve=>{finish=resolve;}) as NativeResults[K];
    return call(operation,args,timeout);
  };
  const rejected=assert.rejects(lane.backend.recipePage(),/LEASE_EXPIRED/);
  assert.ok(finish);await lane.stopAll();finish(recipePagePayload());await rejected;
  assert.equal(lane.health().fenced,true);
});

test('focused discovery rejects changed body generation before public delivery',jvm,async t => {
  const f=await fixture(t);const {lane}=await f.start();const call=f.client.call.bind(f.client);
  f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
    const result=await call(operation,args,timeout);
    if(operation==='recipe_query') (result as NativeResults['recipe_query']).connection_generation++;
    return result;
  };
  await assert.rejects(lane.backend.recipeQuery(recipeQuery),/GAME_BODY_MISMATCH/);
  assert.equal(lane.health().fenced,true);
});

test('actual JVM native authority denies sibling scope and capability mismatches before arming',jvm,async t => {
  const f = await fixture(t);
  const journal = new Journal(f.config.state_directory,1); f.own(journal);
  for (const patch of [{agent_id:'sibling'},{campaign_id:'other'}]) {
    await assert.rejects(ForgeLane.connect({...f.config,...patch},capability,f.client,journal,fingerprint,1000,60000),/FORBIDDEN/);
  }
  await assert.rejects(ForgeLane.connect(f.config,'b'.repeat(64),f.client,journal,fingerprint,1000,60000),/FORBIDDEN/);
  await assert.rejects(ForgeLane.connect(f.config,capability,f.client,journal,'b'.repeat(64),1000,60000),/FORBIDDEN/);
  await assert.rejects(ForgeLane.connect(f.config,capability,f.client,journal,fingerprint,1000,60000,2),/PROCESS_GUARD_BINDING_MISMATCH/);
  assert.equal((await f.client.call('lane_status')).epoch,null);
  assert.equal((await f.client.call('lane_status')).attempted_primitive_events,0);
});

test('actual JVM cancellation releases the held motor and fences public re-entry',jvm,async t => {
  const f = await fixture(t,true); const {lane,journal} = await f.start(); const b = batch(await lane.observe());
  lane.act(b); await delay(80); const started = mono(); const ack = await lane.cancel(b.request_id);
  assert.equal(ack.status,'cancelled'); assert.equal(ack.release_confirmed,true);
  assert.ok(mono()-started < 1000); assert.equal(ack.requires_resync,true);
  assert.throws(() => lane.act({...b,request_id:'late',seq:2}),/LEASE_EXPIRED/);
  assert.equal(journal.counter('primitive_events'),(await f.client.call('lane_status')).attempted_primitive_events);
  assert.equal(lane.act(b).status,'cancelled');
});

test('higher broker epoch retains native consumption and never replays old known requests',jvm,async t => {
  const f = await fixture(t); const first = await f.start(); const b = batch(await first.lane.observe());
  first.lane.act(b); await terminal(first.journal); await first.lane.close();
  const before = first.journal.counter('primitive_events'); first.journal.close();
  const journal = new Journal(f.config.state_directory,2); f.own(journal);
  const scope = {...f.config,epoch:2,lease_id:'lease-2'};
  const lane = await ForgeLane.connect(scope,capability,f.client,journal,fingerprint,1000,60000); f.own(journal,lane);
  assert.equal(journal.counter('primitive_events'),before+1); // the new arm's safety release is also charged
  assert.equal(lane.act(b).status,'emitted');
  const next = {...batch(await lane.observe(),'second'),epoch:2,control_revision:2,lease_id:'lease-2'};
  lane.act(next); assert.equal((await terminal(journal,'second')).status,'emitted');
  assert.equal(journal.counter('primitive_events'),before+3);
  const nativeLog = readFileSync(join(f.nativeRoot,'game-actions.jsonl'),'utf8');
  assert.equal((nativeLog.match(/"kind":"intent"/g) ?? []).length,2);
});

test('a second broker cannot seize or stop an already armed native body',jvm,async t => {
  const f = await fixture(t); const {lane,journal} = await f.start();
  const secondDirectory = join(f.root,'second-worker'); mkdirSync(secondDirectory);
  const second = new Journal(secondDirectory,2);
  try {
    await assert.rejects(ForgeLane.connect({...f.config,epoch:2,lease_id:'other'},capability,f.client,second,fingerprint,1000,60000),/STALE_EPOCH/);
    assert.equal((await f.client.call('lane_status')).fenced,false);
    assert.equal((await f.client.call('lane_status')).attempted_primitive_events,1);
    lane.act(batch(await lane.observe())); assert.equal((await terminal(journal)).status,'emitted');
  } finally {second.close();}
});

test('lost native action reply becomes unknown without another action POST',jvm,async t => {
  const f = await fixture(t); const {lane,journal} = await f.start();
  const original = f.client.call.bind(f.client); let actCalls = 0;
  f.client.call = async <K extends NativeOperation>(operation: K,args: Record<string,unknown> = {},timeout?: number): Promise<NativeResults[K]> => {
    const result = await original(operation,args,timeout);
    if (operation === 'act') {actCalls++; throw new NativeOutcomeUnknown('lost-reply','act');}
    return result;
  };
  const b = batch(await lane.observe()); lane.act(b); const ack = await terminal(journal);
  assert.equal(ack.status,'unknown'); assert.equal(ack.requires_resync,true); assert.equal(actCalls,1);
  assert.equal(lane.act(b).status,'unknown'); assert.equal(actCalls,1);
});

for (const scenario of ['typed','pending','unlisted','wrong_identity','extra_field','dropped'] as const) {
  test(`HTTP mutation diagnostics survive unknown wrapping without replay or public leakage: ${scenario}`,jvm,async t => {
    const f=await fixture(t);const {lane,journal}=await f.start();
    let posts=0,gets=0,wire:Record<string,unknown>={};
    const server=createServer(async(req,res)=>{
      if(req.method==='POST') {
        let body='';for await(const chunk of req)body+=chunk;wire=JSON.parse(body);posts++;
        assert.equal(wire.operation,'act');
      } else gets++;
      if(scenario==='dropped') {req.socket.destroy();return;}
      const pending=scenario==='pending' && req.method==='POST';
      const response={schema:'strata/NativeGameResponse/1',request_id:wire.request_id,
        session_id:scenario==='wrong_identity' ? 'sibling-session' : 'diagnostic-fixture',
        status:pending?'accepted':'failed',result:null,
        error_code:pending?null:scenario==='unlisted'?'PRIVATE_CANARY':'PRECONDITION_FAILED',
        ...(scenario==='extra_field'?{private_detail:'private-message-canary'}:{})};
      res.writeHead(pending?202:200,{'Content-Type':'application/json'});res.end(JSON.stringify(response));
    });
    server.listen(0,'127.0.0.1');await once(server,'listening');
    t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
    const address=server.address();assert.ok(address && typeof address!=='string');
    const transport=new NativeGameClient({schema:'strata/NativeGameConnection/1',host:'127.0.0.1',port:address.port,
      session_id:'diagnostic-fixture',bearer_token:'b'.repeat(64),fingerprint,operator_development_only:true});
    const original=f.client.call.bind(f.client),event=journal.event.bind(journal);
    let released=false;const records:Array<Record<string,unknown>>=[];
    journal.event=(kind,body)=>{
      if(kind==='native_action_call_failed') {assert.equal(released,true);records.push(body as Record<string,unknown>);}
      event(kind,body);
    };
    f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
      if(operation==='act')return transport.call(operation,args,timeout);
      const value=await original(operation,args,timeout);if(operation==='stop_all')released=true;return value;
    };
    const b=batch(await lane.observe());lane.act(b);const ack=await terminal(journal);await delay(20);
    assert.equal(ack.status,'unknown');assert.equal(ack.error_code,'ACTION_UNKNOWN');
    assert.equal(ack.release_confirmed,true);assert.equal(ack.requires_resync,true);
    assert.equal(lane.health().fenced,true);assert.equal(lane.act(b).status,'unknown');
    assert.equal(posts,1);assert.equal(gets,scenario==='pending'?1:0);assert.equal(records.length,1);
    const expected=scenario==='typed'||scenario==='pending'?'PRECONDITION_FAILED':scenario==='unlisted'
      ?'UNCLASSIFIED_NATIVE_FAILURE':scenario==='dropped'?'GAME_TRANSPORT_UNAVAILABLE':'GAME_RESPONSE_INVALID';
    assert.equal(records[0]!.code,expected);assert.equal(records[0]!.request_id,b.request_id);
    assert.equal(records[0]!.operation,'act');
    assert.deepEqual(Object.keys(records[0]!).sort(),['action_seq','at','code','epoch','mono_ms','operation','policy','request_id']);
    assert.equal(JSON.stringify(records).includes('CANARY'),false);
    assert.equal(JSON.stringify(records).includes('private-message'),false);
    for(const secret of ['PRECONDITION_FAILED','diagnosticCode','private-message','PRIVATE_CANARY','native_action_call_failed'])
      assert.equal(JSON.stringify(ack).includes(secret),false);
    assert.equal((await original('lane_status')).fenced,true);
  });
}

for (const scenario of ['typed','unclassified','unlisted_fault','status','diagnostic_disk_failure'] as const) {
  test(`native failure diagnostics preserve fencing and private sanitization: ${scenario}`,jvm,async t => {
    const f=await fixture(t);const {lane,journal}=await f.start();
    const original=f.client.call.bind(f.client), event=journal.event.bind(journal);
    let acts=0,released=false;const records:Array<Record<string,unknown>>=[];
    journal.event=(kind:string,body:unknown)=>{
      if(kind==='native_action_call_failed') {
        assert.equal(released,true,'diagnostics cannot precede native release');
        if(scenario==='diagnostic_disk_failure')throw new Error('private-storage-canary');
        records.push(body as Record<string,unknown>);
      }
      event(kind,body);
    };
    f.client.call=async <K extends NativeOperation>(operation:K,args:Record<string,unknown>={},timeout?:number):Promise<NativeResults[K]>=>{
      if(operation==='act') {
        acts++;
        if(scenario!=='status')throw scenario==='unclassified' ? new Error('private-error-canary')
          : new Fault(scenario==='unlisted_fault' ? 'PRIVATE_CANARY' : 'TARGET_OCCLUDED');
      }
      if(operation==='action_status' && scenario==='status')throw new Fault('GAME_TRANSPORT_UNAVAILABLE');
      const value=await original(operation,args,timeout);
      if(operation==='stop_all')released=true;
      return value;
    };
    const b=batch(await lane.observe());
    if(scenario==='status')b.action={kind:'use_item',hand:'main',hold_ms:1500};
    lane.act(b);const ack=await terminal(journal);await delay(20);
    assert.equal(ack.status,'unknown');assert.equal(ack.error_code,'ACTION_UNKNOWN');
    assert.equal(ack.requires_resync,true);assert.equal(ack.release_confirmed,true);
    assert.equal(lane.health().fenced,true);assert.equal(acts,1);
    assert.equal(lane.act(b).status,'unknown');assert.equal(acts,1);
    assert.equal((await original('lane_status')).fenced,true);
    if(scenario==='diagnostic_disk_failure')assert.equal(records.length,0);
    else {
      assert.equal(records.length,1);
      const record=records[0];assert.ok(record);
      assert.equal(record.request_id,b.request_id);assert.equal(record.action_seq,b.seq);
      assert.equal(record.operation,scenario==='status' ? 'action_status' : 'act');
      assert.equal(record.code,scenario==='status' ? 'GAME_TRANSPORT_UNAVAILABLE'
        : scenario==='typed' ? 'TARGET_OCCLUDED' : 'UNCLASSIFIED_NATIVE_FAILURE');
      assert.equal(JSON.stringify(records).includes('canary'),false);
      assert.equal(JSON.stringify(records).includes('PRIVATE_CANARY'),false);
      assert.deepEqual(Object.keys(record).sort(),['action_seq','at','code','epoch','mono_ms','operation','policy','request_id']);
    }
  });
}

test('public Forge observations reject hidden state and quarantine the lane',jvm,async t => {
  const f = await fixture(t); const {lane} = await f.start(); const original = f.client.call.bind(f.client);
  f.client.call = async <K extends NativeOperation>(operation: K,args: Record<string,unknown> = {},timeout?: number): Promise<NativeResults[K]> => {
    const value = await original(operation,args,timeout);
    if (operation === 'observe_bound') (value as NativeResults['observe_bound']).snapshot.state = {
      ...(value as NativeResults['observe_bound']).snapshot.state,private_score:7} as never;
    return value;
  };
  await assert.rejects(lane.observe(),/SCHEMA_UNSUPPORTED/);
  assert.equal(lane.health().fenced,true);
});

for (const identityField of ['body_fingerprint','connection_generation'] as const) {
  test(`public Forge observation rejects changed ${identityField} before projection`,jvm,async t => {
    const f = await fixture(t); const {lane} = await f.start(); const original = f.client.call.bind(f.client);
    f.client.call = async <K extends NativeOperation>(operation: K,args: Record<string,unknown> = {},timeout?: number): Promise<NativeResults[K]> => {
      const value = await original(operation,args,timeout);
      if (operation === 'observe_bound') {
        const bound = value as NativeResults['observe_bound'];
        if (identityField === 'connection_generation') bound.connection_generation++;
        else bound.body_fingerprint = 'b'.repeat(64);
      }
      return value;
    };
    await assert.rejects(lane.observe(),/GAME_BODY_MISMATCH/); assert.equal(lane.health().fenced,true);
  });
}

test('killed native JVM cannot produce a confirmed release or replay an active action',jvm,async t => {
  const f = await fixture(t,true); const {lane,journal} = await f.start(); const b = batch(await lane.observe());
  lane.act(b); await delay(80); f.process.kill();
  const ack = await terminal(journal); assert.equal(ack.status,'unknown'); assert.equal(ack.release_confirmed,false);
  assert.equal(ack.emitted_events,null); assert.equal(lane.act(b).status,'unknown');
  await assert.rejects(lane.close(),/INPUT_RELEASE_FAILED/);
});

test('same scoped CLI reaches the selected Forge lane and private native authority has no public route',jvm,async t => {
  const f = await fixture(t); const journal = new Journal(f.config.state_directory,1);
  await assert.rejects(workerLane(f.config,journal),/PROCESS_GUARD_REQUIRED/);
  const lane = await ForgeLane.connect(f.config,capability,f.client,journal,fingerprint,1000,60000);
  // This direct-lane fixture owns the worker's renewal lifecycle while exercising
  // many real CLI processes. Reads must not implicitly extend the six-second lease.
  const renew = setInterval(() => {void lane.renewLease();},2000);
  t.after(() => clearInterval(renew));
  const capabilities = {...manifest,digest:capability,lease_id:f.config.lease_id,epoch:1};
  f.own(journal,lane);
  const server = await serve(lane,'public-fixture-token',capabilities);
  t.after(() => new Promise<void>(r => server.close(() => r())));
  const address = server.address(); assert.ok(address && typeof address !== 'string');
  const grant = join(f.root,'public-grant.json'); const url = `http://127.0.0.1:${address.port}/v1/game`;
  const publicGrant = {url,token:'public-fixture-token',campaign_id:'campaign',agent_id:'avatar',epoch:1};
  writeFileSync(grant,JSON.stringify(publicGrant));
  assert.doesNotMatch(JSON.stringify(publicGrant),/bearer_token|native_fingerprint|body_fingerprint/);
  const cli = fileURLToPath(new URL('../src/cli.js',import.meta.url));
  const env = {...process.env,STRATA_GAME_GRANT:grant};
  const recipeCall = await promisify(execFile)(process.execPath,[cli,'recipes','--after','0','--json'],{env});
  const recipePage = JSON.parse(recipeCall.stdout).result;
  assert.equal(recipePage.recipes[0].recipe_id,'fixture:expert');
  assert.deepEqual(recipePage.recipes[0].ingredients,[['fixture:changed_ingredient']]);
  assert.equal(recipePage.recipes[1].supported,false);
  assert.deepEqual(Object.keys(recipePage).sort(),['next_cursor','recipes','revision']);
  const queryCall=await promisify(execFile)(process.execPath,[cli,'recipe-query','--item','fixture:output','--role','output','--after','0','--json'],{env});
  const queryPage=JSON.parse(queryCall.stdout).result;
  assert.deepEqual(queryPage.query,recipeQuery);assert.equal(queryPage.policy,RECIPE_QUERY_POLICY);
  for (const [category,flag,target] of [['thermal:crucible','--fluid','fixture:fluid'],['thermal:furnace','--item','fixture:output']]) {
    const machineCall=await promisify(execFile)(process.execPath,[cli,'recipe-query','--category',category!,flag!,target!,
      '--role','output','--after','0','--json'],{env});
    const machine=JSON.parse(machineCall.stdout).result;
    assert.equal(machine.query.category,category);assert.equal(machine.recipes[0].category,category);
    assert.equal(machine.recipes[0].craft_authority,'discovery_only');assert.equal(machine.recipes[0].energy_rf,4000);
    assert.equal(machine.body_fingerprint,undefined);assert.equal(machine.connection_generation,undefined);
  }
  assert.equal(queryPage.recipes[0].craft_authority,'discovery_only');
  assert.equal(queryPage.recipes[1].supported,false);
  assert.doesNotMatch(JSON.stringify(queryPage),/body_fingerprint|connection_generation|private|bearer/);
  for(const args of [['--after','0'],['--chapter','0000000000000001','--after','0']]) {
    const questCall=await promisify(execFile)(process.execPath,[cli,'quests',...args,'--json'],{env});
    const questPage=JSON.parse(questCall.stdout).result;
    assert.equal(questPage.policy,QUEST_POLICY);assert.equal(questPage.entries[0].kind,args.length===2 ? 'chapter' : 'quest');
    assert.doesNotMatch(JSON.stringify(questPage),/body_fingerprint|connection_generation|team_id|private|bearer/);
  }
  const textCall=await promisify(execFile)(process.execPath,[cli,'quest-text','--chapter','0000000000000001',
    '--quest','0000000000000002','--after','0','--json'],{env});
  const textPage=JSON.parse(textCall.stdout).result;
  assert.equal(textPage.policy,QUEST_TEXT_POLICY);assert.equal(textPage.lines[0].text,'Visible description');
  assert.doesNotMatch(JSON.stringify(textPage),/body_fingerprint|connection_generation|team_id|private|bearer/);
  for(const part of ['tasks','rewards']) {
    const componentCall=await promisify(execFile)(process.execPath,[cli,'quest-components','--chapter','0000000000000001',
      '--quest','0000000000000002','--part',part,'--after','0','--json'],{env});
    const componentPage=JSON.parse(componentCall.stdout).result;
    assert.equal(componentPage.policy,QUEST_COMPONENTS_POLICY);assert.equal(componentPage.entries[0].kind,part==='tasks' ? 'task' : 'reward');
    assert.doesNotMatch(JSON.stringify(componentPage),/body_fingerprint|connection_generation|team_id|private|bearer/);
  }
  const menuCall=await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env});
  const menuPage=JSON.parse(menuCall.stdout).result;
  assert.equal(menuPage.policy,QUEST_MENU_POLICY);assert.equal(menuPage.entries[0].item_id,'minecraft:stone');
  assert.equal(menuPage.controls[0].enabled,false);
  assert.doesNotMatch(JSON.stringify(menuPage),/body_fingerprint|connection_generation|team_id|private|bearer|layout/);
  for (const patch of [{method:'quests.menu',quest_menu_query:null},{method:'observe',quest_menu_query:{source:'ftb_quests',after:0}},
    {method:'quests.menu',quest_menu_query:{source:'ftb_quests',after:0,team_id:'sibling'}},
    {method:'quests.menu',quest_menu_query:{source:'ftb_quests',after:0},agent_id:'sibling'},
    {method:'recipes.query',recipe_query:null},{method:'observe',recipe_query:recipeQuery},
    {method:'recipes.query',recipe_query:{...recipeQuery,include_hidden:true}},
    {method:'recipes.query',recipe_query:recipeQuery,agent_id:'sibling'},
    {method:'quests.list',quest_query:null},{method:'quests.text',quest_text_query:null},{method:'quests.components',quest_components_query:null},
    {method:'observe',quest_components_query:{source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'tasks',after:0}},
    {method:'observe',quest_text_query:{source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',after:0}},
    {method:'observe',quest_query:{source:'ftb_quests',chapter_id:null,after:0}},
    {method:'quests.list',quest_query:{source:'ftb_quests',chapter_id:null,after:0,team_id:'sibling'}},
    {method:'quests.list',quest_query:{source:'ftb_quests',chapter_id:null,after:0},agent_id:'sibling'}]) {
    const malformed={schema:'strata/GameRequest/1',request_id:'query-reject',campaign_id:'campaign',agent_id:'avatar',epoch:1,
      deadline_at:new Date(Date.now()+5000).toISOString(),action:null,target_request_id:null,after:null,...patch};
    const denied=await fetch(url,{method:'POST',headers:{Authorization:'Bearer public-fixture-token','Content-Type':'application/json'},body:JSON.stringify(malformed)});
    assert.equal((await denied.json() as {status:string}).status,'error');
  }
  const call = await promisify(execFile)(process.execPath,[cli,'look-at','--x','1','--y','65','--z','2','--json'],{env})
    .catch(error => error as {stdout:string;stderr:string});
  const ack = JSON.parse(call.stdout).result as ActionAck; assert.equal(ack.status,'accepted');
  assert.equal((await terminal(journal,ack.request_id)).status,'emitted');
  const openObservation=await lane.observe(true);
  const openRequest={...batch(openObservation,'quest-open-cli',(openObservation.last_action_seq??0)+1),action:{kind:'quest_ui',operation:'open',
    source:'ftb_quests',source_generation:1,expected_catalog_revision:1}};
  const openCall=await new Promise<{stdout:string;stderr:string}>((resolve,reject)=>{
    const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout,stderr)=>{
      if(error && error.code!==2)reject(new Error(`Synthetic opening CLI failed: ${stdout}`,{cause:error}));else resolve({stdout,stderr});
    });child.stdin!.end(JSON.stringify(openRequest));
  });
  const openAck=JSON.parse(openCall.stdout).result as ActionAck;assert.equal(openAck.status,'accepted');
  const opened=await terminal(journal,openAck.request_id);assert.equal(opened.status,'emitted');assert.equal(opened.emitted_events,2);
  assert.equal(opened.release_confirmed,true);assert.equal(lane.act(openRequest as ActionBatch).status,'emitted');
  for(const operation of ['chapter','quest','back','close'] as const) {
    const screenCall=await promisify(execFile)(process.execPath,[cli,'quest-screen','--json'],{env});
    const screen=JSON.parse(screenCall.stdout).result;
    assert.equal(screen.kind,'quest_book');assert.doesNotMatch(JSON.stringify(screen),/body_fingerprint|connection_generation|screen_object|bearer/);
    let selection=null;
    if(operation==='chapter' || operation==='quest') {
      const chapterArgs=operation==='quest'?['--chapter','0000000000000001']:[];
      const page=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quests',...chapterArgs,'--after','0','--json'],{env})).stdout).result;
      selection={query:page.query,revision:page.revision,entry_id:page.entries[0].entry_id};
    }
    const observation=await lane.observe(true);
    const navigation:ActionBatch={...batch(observation,`navigate-${operation}`,(observation.last_action_seq??0)+1),
      action:{kind:'quest_navigate',operation,source:'ftb_quests',source_generation:screen.source_generation,
        expected_screen_generation:screen.screen_generation,expected_screen_revision:screen.revision,selection}};
    const submitted=await new Promise<string>((resolve,reject)=>{
      const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
        if(error && error.code!==2)reject(new Error(`Synthetic navigation CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
      });child.stdin!.end(JSON.stringify(navigation));
    });
    assert.equal(JSON.parse(submitted).result.status,'accepted');const receipt=await terminal(journal,navigation.request_id);
    assert.equal(receipt.status,'emitted');assert.equal(receipt.emitted_events,2);assert.equal(lane.act(navigation).status,'emitted');
  }
  const closed=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-screen','--json'],{env})).stdout).result;
  assert.equal(closed.kind,'closed');assert.equal(closed.quest_id,null);
  for(const kind of ['quest_ui','quest_navigate','quest_task'] as const) {
    let action:ActionBatch['action'];
    if(kind==='quest_ui')action={kind,operation:'open',source:'ftb_quests',source_generation:1,expected_catalog_revision:1};
    else {
      const screen=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-screen','--json'],{env})).stdout).result;
      const args=kind==='quest_task'?['quest-components','--chapter','0000000000000001','--quest','0000000000000002','--part','tasks']:
        ['quests','--chapter','0000000000000001'];
      const page=JSON.parse((await promisify(execFile)(process.execPath,[cli,...args,'--after','0','--json'],{env})).stdout).result;
      const common={source:'ftb_quests' as const,source_generation:screen.source_generation,
        expected_screen_generation:screen.screen_generation,expected_screen_revision:screen.revision,
        selection:{query:page.query,revision:page.revision,entry_id:page.entries[0].entry_id}};
      action=kind==='quest_task'?{...common,kind,operation:'open'}:{...common,kind,operation:'quest'};
    }
    const observation=await lane.observe(true);
    const request:ActionBatch={...batch(observation,`task-menu-${kind}`,(observation.last_action_seq??0)+1),action};
    const submitted=await new Promise<string>((resolve,reject)=>{
      const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
        if(error && error.code!==2)reject(new Error(`Synthetic ${kind} CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
      });child.stdin!.end(JSON.stringify(request));
    });
    assert.equal(JSON.parse(submitted).result.status,'accepted');
    const receipt=await terminal(journal,request.request_id);assert.equal(receipt.status,'emitted');assert.equal(receipt.emitted_events,2);
    assert.equal(lane.act(request).status,'emitted');
  }
  for(const direction of ['down','up',null] as const) {
    const menu=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env})).stdout).result;
    const observation=await lane.observe(true);
    const request:ActionBatch={...batch(observation,`menu-${direction??'back'}`,(observation.last_action_seq??0)+1),
      action:{kind:'quest_menu',operation:direction===null?'back':'scroll',direction,source:'ftb_quests',source_generation:menu.source_generation,
        expected_menu_generation:menu.menu_generation,expected_menu_revision:menu.revision}};
    const submitted=await new Promise<string>((resolve,reject)=>{
      const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
        if(error && error.code!==2)reject(new Error(`Synthetic menu CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
      });child.stdin!.end(JSON.stringify(request));
    });
    assert.equal(JSON.parse(submitted).result.status,'accepted');const receipt=await terminal(journal,request.request_id);
    assert.equal(receipt.status,'emitted');assert.equal(receipt.emitted_events,2);assert.equal(lane.act(request).status,'emitted');
    if(direction!==null) {
      const after=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env})).stdout).result;
      assert.ok(after.revision>menu.revision);
    }
  }
  const restored=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-screen','--json'],{env})).stdout).result;
  assert.equal(restored.quest_id,'0000000000000002');
  const rewards=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-components','--chapter','0000000000000001',
    '--quest','0000000000000002','--part','rewards','--after','0','--json'],{env})).stdout).result;
  const observed=await lane.observe(true);
  const choiceRequest:ActionBatch={...batch(observed,'choice-open',(observed.last_action_seq??0)+1),action:{kind:'quest_reward',operation:'open',
    source:'ftb_quests',source_generation:restored.source_generation,expected_screen_generation:restored.screen_generation,
    expected_screen_revision:restored.revision,selection:{query:rewards.query,revision:rewards.revision,entry_id:rewards.entries[0].entry_id}}};
  const choiceCall=await new Promise<string>((resolve,reject)=>{
    const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
      if(error && error.code!==2)reject(new Error(`Synthetic choice CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
    });child.stdin!.end(JSON.stringify(choiceRequest));
  });
  assert.equal(JSON.parse(choiceCall).result.status,'accepted');
  const choiceReceipt=await terminal(journal,choiceRequest.request_id);
  assert.equal(choiceReceipt.status,'emitted');assert.equal(choiceReceipt.emitted_events,2);
  assert.equal(lane.act(choiceRequest).status,'emitted');
  const choices=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env})).stdout).result;
  assert.equal(choices.menu_kind,'reward_choices');assert.equal(choices.entries[0].title,'Visible choice');
  assert.equal(choices.context.reward_id,rewards.entries[0].entry_id);
  assert.doesNotMatch(JSON.stringify(choices),/body_fingerprint|connection_generation|weight|table|packet|command|layout/);
  for(const direction of ['down','up',null] as const) {
    const menu=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env})).stdout).result;
    assert.equal(menu.menu_kind,'reward_choices');assert.deepEqual(menu.controls,[]);
    const observation=await lane.observe(true);
    const request:ActionBatch={...batch(observation,`choice-${direction??'back'}`,(observation.last_action_seq??0)+1),
      action:{kind:'quest_menu',operation:direction===null?'back':'scroll',direction,source:'ftb_quests',source_generation:menu.source_generation,
        expected_menu_generation:menu.menu_generation,expected_menu_revision:menu.revision}};
    const submitted=await new Promise<string>((resolve,reject)=>{
      const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
        if(error && error.code!==2)reject(new Error(`Synthetic choice control CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
      });child.stdin!.end(JSON.stringify(request));
    });
    assert.equal(JSON.parse(submitted).result.status,'accepted');const receipt=await terminal(journal,request.request_id);
    assert.equal(receipt.status,'emitted');assert.equal(receipt.emitted_events,2);assert.equal(lane.act(request).status,'emitted');
    if(direction!==null) {
      const after=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-menu','--after','0','--json'],{env})).stdout).result;
      assert.ok(after.revision>menu.revision);
    }
  }
  const afterChoice=JSON.parse((await promisify(execFile)(process.execPath,[cli,'quest-screen','--json'],{env})).stdout).result;
  assert.equal(afterChoice.quest_id,'0000000000000002');
  const request = {schema:'strata/GameRequest/1',request_id:'rpc',campaign_id:'campaign',agent_id:'avatar',epoch:1,
    deadline_at:new Date(Date.now()+5000).toISOString(),method:'authority',action:null,target_request_id:null,after:null};
  const response = await fetch(url,{method:'POST',headers:{Authorization:'Bearer public-fixture-token','Content-Type':'application/json'},body:JSON.stringify(request)});
  assert.equal((await response.json() as {status:string}).status,'error');
});

test('recipe navigation budget admission reserves each dispatch, a frame check and safety release',jvm,async t=>{
  const f=await fixture(t);const {lane,journal}=await f.start();const observation=await lane.observe(true);
  journal.counter('primitive_events',f.config.primitive_limit-3-journal.counter('primitive_events'));
  const request:ActionBatch={...batch(observation,'recipe-budget',1),action:{kind:'recipe_navigate',source:'jei',control:'category_next',
    source_generation:1,expected_screen_generation:2,expected_screen_revision:3,expected_page_revision:'a'.repeat(64)}};
  assert.throws(()=>lane.act(request),/BUDGET_EXHAUSTED/);
  journal.counter('primitive_events',1);
  assert.throws(()=>lane.act({...request,action:{...request.action!,kind:'recipe_navigate',source:'jei',control:'history_back',
    source_generation:1,expected_screen_generation:2,expected_screen_revision:3,expected_page_revision:'a'.repeat(64)}}),/BUDGET_EXHAUSTED/);
  assert.equal((await f.client.call('lane_status')).active_request_id,null);
  assert.equal((await f.client.call('lane_status')).attempted_primitive_events,1);
});

test('scoped CLI opens, navigates, follows history and closes an origin-bound synthetic recipe screen without private data',jvm,async t=>{
  const f=await fixture(t,false,true);const {lane,journal}=await f.start();
  const renew=setInterval(()=>{void lane.renewLease();},2000);t.after(()=>clearInterval(renew));
  const server=await serve(lane,'recipe-fixture-token',{...manifest,digest:capability,lease_id:f.config.lease_id,epoch:1});
  t.after(()=>new Promise<void>(resolve=>server.close(()=>resolve())));
  const address=server.address();assert.ok(address && typeof address!=='string');
  const grant=join(f.root,'recipe-grant.json');
  writeFileSync(grant,JSON.stringify({url:`http://127.0.0.1:${address.port}/v1/game`,token:'recipe-fixture-token',campaign_id:'campaign',agent_id:'avatar',epoch:1}));
  const cli=fileURLToPath(new URL('../src/cli.js',import.meta.url));const env={...process.env,STRATA_GAME_GRANT:grant};
  const read=async(args:string[])=>JSON.parse((await promisify(execFile)(process.execPath,[cli,...args,'--json'],{env,windowsHide:true})).stdout).result;
  for(const operation of ['open','quest','task','navigate','history','history-empty','close'] as const) {
    let action:ActionBatch['action'];
    if(operation==='open')action={kind:'quest_ui',operation:'open',source:'ftb_quests',source_generation:1,expected_catalog_revision:1};
    else {
      const screen=await read(['quest-screen']);
      if(operation==='close' || operation==='navigate' || operation==='history' || operation==='history-empty') {
        assert.equal(screen.kind,'task_recipes');assert.equal(screen.quest_id,'0000000000000002');
        assert.doesNotMatch(JSON.stringify(screen),/body_fingerprint|connection_generation|parent_screen|focus|recipe_id|runtime|layout/);
        const page=await read(['recipe-page']);assert.equal(page.coverage,'slot_header_control_draw_operands');assert.equal(page.complete,false);
        if(operation==='history')assert.equal(page.headers[0].text,'Synthetic category 1');
        else assert.deepEqual(page.headers,recipePagePayload().headers);
        assert.deepEqual(page.controls,recipePagePayload().controls);
        assert.equal(page.quest_id,screen.quest_id);assert.equal(page.screen_generation,screen.screen_generation);
        if(operation==='history')assert.deepEqual(page.layouts,[]);
        else assert.deepEqual(page.layouts[0].slots.map((slot:{display:{kind:string}})=>slot.display.kind),['item','fluid','unsupported','empty']);
        assert.doesNotMatch(JSON.stringify(page),/body_fingerprint|connection_generation|parent_screen|focus|recipe_id|runtime|screen_object|nbt/);
      } else assert.equal(screen.kind,'quest_book');
      const common={source:'ftb_quests' as const,source_generation:screen.source_generation,
        expected_screen_generation:screen.screen_generation,expected_screen_revision:screen.revision};
      if(operation==='close')action={...common,kind:'quest_navigate',operation:'close',selection:null};
      else if(operation==='navigate' || operation==='history' || operation==='history-empty') {
        const page=await read(['recipe-page']);
        action={...common,source:'jei',kind:'recipe_navigate',control:operation==='navigate'?'category_next':'history_back',expected_page_revision:page.revision};
      }
      else {
        const page=await read(operation==='task'?['quest-components','--chapter','0000000000000001','--quest','0000000000000002','--part','tasks','--after','0']:
          ['quests','--chapter','0000000000000001','--after','0']);
        const selection={query:page.query,revision:page.revision,entry_id:page.entries[0].entry_id};
        action=operation==='task'?{...common,kind:'quest_task',operation:'open',selection}:{...common,kind:'quest_navigate',operation:'quest',selection};
      }
    }
    const observed=await lane.observe(true);const request:ActionBatch={...batch(observed,`recipe-${operation}`,(observed.last_action_seq??0)+1),action};
    const submitted=await new Promise<string>((resolve,reject)=>{
      const child=execFile(process.execPath,[cli,'act','--json'],{env,windowsHide:true},(error,stdout)=>{
        if(error && error.code!==2)reject(new Error(`Synthetic recipe CLI failed: ${stdout}`,{cause:error}));else resolve(stdout);
      });child.stdin!.end(JSON.stringify(request));
    });
    assert.equal(JSON.parse(submitted).result.status,'accepted');const receipt=await terminal(journal,request.request_id);
    assert.equal(receipt.status,'emitted');
    assert.equal(receipt.emitted_events,operation==='navigate'?4:operation==='history'||operation==='history-empty'?3:2);
    assert.equal(lane.act(request).status,'emitted');
  }
  const parent=await read(['quest-screen']);assert.equal(parent.kind,'quest_book');assert.equal(parent.quest_id,'0000000000000002');
  await assert.rejects(read(['recipe-page']));
});

test('actual guarded supervisor and worker expose only a public grant and terminate the dedicated JVM after drain',guardedJvm,async t => {
  const f = await fixture(t); const c = await f.guardConfig();
  const path = join(f.root,'worker.json'); writeFileSync(path,JSON.stringify(c));
  const workerPath = fileURLToPath(new URL('../src/worker.js',import.meta.url));
  const worker = spawn(process.execPath,[workerPath,path],{windowsHide:true,stdio:['ignore','pipe','pipe']});
  const exited = once(worker,'exit'); let output = ''; let stderr = '';
  worker.stdout.on('data',(b: Buffer) => {output += b.toString();}); worker.stderr.on('data',(b: Buffer) => {stderr += b.toString();});
  t.after(async () => {if (worker.exitCode === null && worker.signalCode === null) worker.kill(); await exited;});
  const grantFile = join(c.state_directory,'grant-1.json'); const until = mono()+8000;
  while (!existsSync(grantFile) && mono() < until) {
    assert.equal(worker.exitCode,null,stderr || output); await delay(20);
  }
  assert.ok(existsSync(grantFile),stderr || output);
  const grant = JSON.parse(readFileSync(grantFile,'utf8'));
  assert.deepEqual(Object.keys(grant).sort(),['agent_id','campaign_id','epoch','token','url']);
  const cli = fileURLToPath(new URL('../src/cli.js',import.meta.url));
  const response = await promisify(execFile)(process.execPath,[cli,'look-at','--x','1','--y','65','--z','2','--json'],
    {env:{...process.env,STRATA_GAME_GRANT:grantFile}}).catch(error => error as {stdout:string});
  assert.equal(JSON.parse(response.stdout).result.status,'accepted');
  const [code] = await exited; assert.equal(code,0,(stderr || output)+'\n'+readFileSync(join(c.state_directory,'supervisor-1.jsonl'),'utf8'));
  assert.notEqual(f.process.exitCode,null,'Dedicated JVM survived worker drain');
  const records = readFileSync(join(c.state_directory,'supervisor-1.jsonl'),'utf8').trim().split('\n').map(line => JSON.parse(line));
  assert.ok(records.some(r => r.kind === 'guard_ready'));
  const stopped = records.find(r => r.kind === 'guard_stopped');
  const stopIntent = records.find(r => r.kind === 'guard_stop_requested');
  assert.deepEqual(stopIntent.value,{already_exited:false});
  assert.ok(stopIntent.seq > records.find(r => r.kind === 'worker_exit').seq);
  assert.ok(stopIntent.seq < stopped.seq);
  const timing = records.find(r => r.kind === 'guard_termination_timing');
  assert.ok(stopIntent.seq < timing.seq && timing.seq < stopped.seq);
  assert.equal(timing.value.wait_result,'signaled'); assert.equal(timing.value.wait_bound_ms,500);
  assert.ok(timing.value.job_returned_after_ns <= timing.value.wait_started_after_ns);
  assert.ok(timing.value.wait_started_after_ns <= timing.value.wait_returned_after_ns);
  assert.equal(timing.value.policy,'job-call-wait-tree-qpc/2');
  assert.equal(timing.value.tree_result,'empty');assert.equal(timing.value.active_processes,0);
  assert.ok(timing.value.total_processes>0);
  assert.equal(timing.value.total_processes,timing.value.held_processes);
  assert.equal(timing.value.held_processes,timing.value.signaled_processes);
  assert.ok(timing.value.tree_checked_after_ns >= timing.value.wait_returned_after_ns);
  assert.ok(timing.value.tree_checked_after_ns-timing.value.wait_started_after_ns <= 500_000_000);
  assert.equal(stopped.value.termination_confirmed,true); assert.equal(stopped.value.release_confirmed,false);
  assert.equal(stopped.value.reason,'PROCESS_STOP_REQUESTED');
  let previous = '0'.repeat(64);
  const clock = records[0].source_clock_id;
  for (const record of records) {
    const {hash,...body} = record;
    assert.equal(body.schema,'strata/SupervisorEvent/1'); assert.equal(body.source_clock_id,clock);
    assert.equal(body.previous,previous); assert.equal(digest(body),hash); previous = hash;
  }
  assert.ok(!existsSync(join(c.state_directory,'executor.lock')),'Worker failed to close journal cleanly');
});

for(const fault of ['slow_bootstrap','hung_bootstrap','crashed_bootstrap','malformed_bootstrap',
  'slow_initialization','hung_initialization','crashed_initialization'] as const) {
  test(`guarded worker startup handles ${fault} without premature grants or invented health`,guardedJvm,async t=>{
    const f=await fixture(t);const c=await f.guardConfig(8000);
    const configPath=join(f.root,'startup-worker.json');writeFileSync(configPath,JSON.stringify(c));
    const preload=join(f.root,'synthetic-startup.mjs');
    const setup=fault==='slow_bootstrap'?`await new Promise(r=>setTimeout(r,1200));`
      : fault==='hung_bootstrap'?`Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0);`
      : fault==='crashed_bootstrap'?`process.exit(23);`
      : fault==='malformed_bootstrap'?`process.send({kind:'gateway_ready',port:1234});await new Promise(()=>{});`
      : `const original=process.emit;let held=false;process.emit=function(event,...args){
          if(event==='message' && args[0]?.config && !held){held=true;
            ${fault==='crashed_initialization'?`process.exit(23);`
              :fault==='slow_initialization'?`setTimeout(()=>original.call(this,event,...args),1400);`:''}
            return true;
          }return original.call(this,event,...args);
        };`;
    writeFileSync(preload,`if(process.send){${setup}}\n`);
    const parent=spawn(process.execPath,['--import',pathToFileURL(preload).href,
      fileURLToPath(new URL('../src/worker.js',import.meta.url)),configPath],
      {windowsHide:true,stdio:['ignore','pipe','pipe']});
    const exited=once(parent,'exit');let output='';let error='';
    parent.stdout.on('data',(b:Buffer)=>{output+=b.toString();});parent.stderr.on('data',(b:Buffer)=>{error+=b.toString();});
    t.after(async()=>{if(parent.exitCode===null && parent.signalCode===null)parent.kill();await exited;});
    const grant=join(c.state_directory,'grant-1.json');
    const [code]=await exited;
    const records=readFileSync(join(c.state_directory,'supervisor-1.jsonl'),'utf8').trim().split('\n').map(line=>JSON.parse(line));
    const boot=records.find(r=>r.kind==='worker_bootstrap_ready');
    const guarding=records.find(r=>r.kind==='guard_start_intent');
    const init=records.find(r=>r.kind==='worker_initializing');
    const ready=records.find(r=>r.kind==='worker_gateway_ready');
    const slow=fault.startsWith('slow_');
    assert.equal(existsSync(grant),slow,output+'\n'+error);
    assert.ok(records.some(r=>r.kind==='worker_exit'),'Missing exit evidence for early failure');
    if(slow){
      assert.equal(code,0,error+'\n'+JSON.stringify(records));
      assert.ok(boot.seq<guarding.seq && guarding.seq<init.seq && init.seq<ready.seq);
      assert.equal(init.value.startup_limit_ms,2250);
      if(fault==='slow_bootstrap')assert.ok(boot.value.elapsed_ms>=1200);
      else assert.ok(ready.value.elapsed_ms-init.value.elapsed_ms>=1400);
      assert.notEqual(f.process.exitCode,null);
    } else {
      assert.notEqual(code,0);
      assert.equal(ready,undefined);
      if(fault.endsWith('bootstrap')){
        assert.equal(guarding,undefined);assert.equal(f.process.exitCode,null);
        assert.equal((await f.client.call('lane_status')).epoch,null);
      } else {
        assert.ok(boot && guarding && init);assert.notEqual(f.process.exitCode,null);
      }
      if(fault==='hung_bootstrap')assert.ok(records.some(r=>r.kind==='supervisor_fault' && r.value.reason==='WORKER_BOOT_TIMEOUT'));
      if(fault==='hung_initialization')assert.ok(records.some(r=>r.kind==='supervisor_fault' && r.value.reason==='WORKER_INITIALIZATION_TIMEOUT'));
      if(fault==='malformed_bootstrap')assert.ok(records.some(r=>r.kind==='supervisor_fault' && r.value.reason==='WORKER_PROTOCOL'));
    }
    assert.equal((readFileSync(join(f.nativeRoot,'game-actions.jsonl'),'utf8').match(/"kind":"intent"/g)??[]).length,0);
  });
}

test('mismatched process grants cannot arm the JVM or create a public worker grant',guardedJvm,async t => {
  const f = await fixture(t); const base = await f.guardConfig();
  const valid = JSON.parse(readFileSync(base.process_guard_file,'utf8'));
  const workerPath = fileURLToPath(new URL('../src/worker.js',import.meta.url));
  const changes = [{epoch:2},{body_fingerprint:'b'.repeat(64)},{connection_digest:'b'.repeat(64)},
    {capability_digest:'b'.repeat(64)},{agent_id:'sibling'}];
  for (const [index,patch] of changes.entries()) {
    const directory = join(f.root,`denied-${index}`); mkdirSync(directory);
    const config = {...base,state_directory:directory};
    const configFile = join(f.root,`denied-${index}.json`); writeFileSync(configFile,JSON.stringify(config));
    writeFileSync(base.process_guard_file,JSON.stringify({...valid,...patch}));
    await assert.rejects(promisify(execFile)(process.execPath,[workerPath,configFile],{windowsHide:true}),
      (error:unknown) => Boolean(error && typeof error === 'object' && 'code' in error && error.code === 1));
    assert.equal(existsSync(join(directory,'grant-1.json')),false);
    assert.equal(f.process.exitCode,null);
    assert.equal((await f.client.call('lane_status')).epoch,null);
  }
});

for (const fault of ['native_freeze','worker_kill','worker_hang','parent_kill'] as const) {
  test(`guarded process chain fences an in-flight action after ${fault}`,guardedJvm,async t => {
    const f = await fixture(t,true); const c = await f.guardConfig(15000);
    const configPath = join(f.root,'worker.json'); writeFileSync(configPath,JSON.stringify(c));
    const freezeWorker = join(f.root,'freeze-worker');
    const preload = join(f.root,'synthetic-worker-hang.mjs');
    writeFileSync(preload,`import {existsSync} from 'node:fs';\nif (process.send) setInterval(() => {
      if (existsSync(${JSON.stringify(freezeWorker)})) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0);
    },10);\n`);
    const workerPath = fileURLToPath(new URL('../src/worker.js',import.meta.url));
    const parent = spawn(process.execPath,['--import',pathToFileURL(preload).href,workerPath,configPath],
      {windowsHide:true,stdio:['ignore','pipe','pipe']});
    const ended = once(parent,'exit'); parent.stdout.resume(); parent.stderr.resume();
    let childPid: number | undefined;
    t.after(async () => {
      if (parent.exitCode === null && parent.signalCode === null) parent.kill(); await ended;
    });
    const grantFile = join(c.state_directory,'grant-1.json'); const until = mono()+8000;
    while (!existsSync(grantFile) && mono() < until) {
      assert.equal(parent.exitCode,null); await delay(20);
    }
    assert.ok(existsSync(grantFile),'Guarded gateway did not start');
    const evidenceFile = join(c.state_directory,'supervisor-1.jsonl');
    const records = () => readFileSync(evidenceFile,'utf8').split('\n').slice(0,-1).map(line => JSON.parse(line));
    childPid = records().find(r => r.kind === 'worker_started').value.pid;
    assert.ok(childPid);
    const cli = fileURLToPath(new URL('../src/cli.js',import.meta.url));
    const response = await promisify(execFile)(process.execPath,[cli,'look-at','--x','1','--y','65','--z','2','--json'],
      {env:{...process.env,STRATA_GAME_GRANT:grantFile}}).catch(error => error as {stdout:string});
    assert.equal(JSON.parse(response.stdout).result.status,'accepted');
    const nativeJournal = join(f.nativeRoot,'game-actions.jsonl'); const sentBy = mono()+1000;
    while (!(readFileSync(nativeJournal,'utf8').includes('"kind":"intent"')) && mono()<sentBy) await delay(10);
    assert.equal((readFileSync(nativeJournal,'utf8').match(/"kind":"intent"/g) ?? []).length,1);
    const started = mono();
    if (fault === 'native_freeze') writeFileSync(f.freeze,'synthetic frozen client thread');
    else if (fault === 'worker_hang') writeFileSync(freezeWorker,'synthetic blocked Node event loop');
    else if (fault === 'worker_kill') process.kill(childPid!,'SIGKILL');
    else parent.kill('SIGKILL');
    while (f.process.exitCode === null && f.process.signalCode === null && mono()-started<2250) await delay(10);
    assert.ok(f.process.exitCode !== null || f.process.signalCode !== null,`JVM survived ${fault}`);
    t.diagnostic(`${fault} to JVM exit: ${mono()-started} ms (synthetic Windows process test)`);
    const [code,signal] = await ended; assert.ok(code !== 0 || signal !== null);
    assert.equal((readFileSync(nativeJournal,'utf8').match(/"kind":"intent"/g) ?? []).length,1);
    if (fault !== 'parent_kill') {
      assert.ok(records().some(r => r.kind === 'guard_stopped' && r.value.termination_confirmed
        && r.value.release_confirmed === false));
    }
    // The crashed parent's final evidence is intentionally incomplete. Its Java
    // lifetime still ends via the independent pipe lease/Job Object guardian.
  });
}
