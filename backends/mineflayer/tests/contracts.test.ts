import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validate, actionSemantics, type ActionBatch } from '../src/protocol.js';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormatsModule from 'ajv-formats';

test('choice opening binds an observed rewards page and grants no claim or raw table selector',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const query={source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'rewards',after:0};
  const selection={query,revision:1,entry_id:'0000000000000003'};
  const action={kind:'quest_reward',operation:'open',source:'ftb_quests',source_generation:1,
    expected_screen_generation:1,expected_screen_revision:1,selection};
  const batch={...example,is_example:false,duration_ms:10000,action};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{operation:'claim'},{choice_index:1},{table_id:'canary'},{selection:null},{expected_screen_revision:true}])
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
  const task=validate<ActionBatch>('ActionBatch',{...batch,action:{...action,selection:{...selection,query:{...query,part:'tasks'}}}});
  assert.throws(()=>actionSemantics(task),/PRECONDITION_FAILED/);
});

test('machine GUI observations preserve bounds and reject hidden fields or mismatched layouts',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/Observation/1');
  const machine={policy:'thermal-current-gui-energy-fluid-base-slots/1',kind:'thermal:machine_crucible',
    energy:{stored:100,capacity:1000},tanks:[{capacity_mb:4000,contents:{fluid_id:'minecraft:lava',amount_mb:250}}]};
  const observation={...example,state:{...example.state,window:{id:7,revision:10,type:'thermal:machine_crucible',
    slots:[],cursor_item:null,machine}}};
  assert.deepEqual(validate('Observation',observation),observation);
  for(const change of [
    (x:any)=>{x.energy.stored=1001;},(x:any)=>{x.energy.stored=true;},
    (x:any)=>{x.tanks[0].contents.amount_mb=4001;},(x:any)=>{x.tanks[0].contents.nbt='private-canary';},
    (x:any)=>{x.tanks=[];},(x:any)=>{x.kind='thermal:machine_furnace';},
    (x:any)=>{x.energy.capacity=0;},(x:any)=>{x.tanks[0].contents.fluid_id='not-namespaced';},
  ]) {
    const altered=structuredClone(observation);change(altered.state.window.machine);
    assert.throws(()=>validate('Observation',altered),/SCHEMA_UNSUPPORTED/);
  }
  const empty=structuredClone(observation) as any;empty.state.window.machine.tanks[0].contents=null;
  assert.deepEqual(validate('Observation',empty),empty);
  const furnace=structuredClone(observation) as any;
  furnace.state.window.type=furnace.state.window.machine.kind='thermal:machine_furnace';
  furnace.state.window.machine.tanks=[];
  assert.deepEqual(validate('Observation',furnace),furnace);
});

test('Pydantic-exported schemas accept all three SPEC game records in TypeScript',()=>{
  // Operator-only synthetic fixtures: this test does not construct a gameplay workspace.
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  let checked=0;
  for (const match of spec.matchAll(/```json\s*([\s\S]*?)```/g)) {
    const record=JSON.parse(match[1]!);
    const name=record.schema.split('/')[1];
    if (!['ActionBatch','ActionAck','Observation'].includes(name)) continue;
    assert.deepEqual(validate(name,record),record);checked++;
    assert.throws(()=>validate(name,{...record,private_field:'canary'}),/SCHEMA_UNSUPPORTED/);
    assert.throws(()=>validate(name,{...record,seq:-1}),/SCHEMA_UNSUPPORTED/);
    if (name==='ActionBatch') {
      const b={...record,is_example:false} as ActionBatch;
      actionSemantics(b);
      assert.throws(()=>actionSemantics({...b,action:null}),/CAPABILITY_MISSING/);
      assert.throws(()=>actionSemantics({...b,duration_ms:10001,action:{kind:'look_at',target:{x:0,y:64,z:0}}}),/PRECONDITION_FAILED/);
    }
  }
  assert.equal(checked,3);
});

test('all 13 canonical records agree with partitioned exported schemas', () => {
  const ajv = new Ajv2020({strict: false, strictNumbers: true, coerceTypes: false});
  (addFormatsModule as unknown as (a: Ajv2020) => void)(ajv);
  const operator = ['PackLock','CampaignConfig','AgentConfig','CheckpointManifest','BudgetLedger'];
  const evaluator = ['GameEvent','EvaluationProtocol','EvaluationResult'];
  const spec = readFileSync(new URL('../../../../SPEC.md', import.meta.url), 'utf8');
  let count = 0;
  for (const match of spec.matchAll(/```json\s*([\s\S]*?)```/g)) {
    const record = JSON.parse(match[1]!);
    const name = record.schema.split('/')[1];
    const domain = operator.includes(name) ? 'operator' : evaluator.includes(name) ? 'evaluator' : 'public';
    const schema = JSON.parse(readFileSync(new URL(`../../../../schemas/v1/${domain}/${name}.json`, import.meta.url), 'utf8'));
    const check = ajv.compile(schema);
    assert.equal(check(record), true, `${name}: ${JSON.stringify(check.errors)}`);
    assert.equal(check({...record, unknown_field: 'private-canary'}), false);
    assert.equal(check({...record, schema: `mcbench/${name}/2`}), false);
    count++;
  }
  assert.equal(count, 13);
});

test('quest navigation binds UI and catalog selections with strict operation semantics',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!)).find(x=>x.schema==='mcbench/ActionBatch/1');
  const action={kind:'quest_navigate',operation:'quest',source:'ftb_quests',source_generation:1,expected_screen_generation:2,expected_screen_revision:3,
    selection:{query:{source:'ftb_quests',chapter_id:'0000000000000001',after:0},revision:1,entry_id:'0000000000000002'}};
  const batch={...example,is_example:false,duration_ms:10000,action};actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{operation:'back'},{operation:'chapter'},{selection:null}]) {
    assert.throws(()=>actionSemantics(validate<ActionBatch>('ActionBatch',{...batch,action:{...action,...patch}})),/PRECONDITION_FAILED/);
  }
  for(const patch of [{operation:'claim'},{expected_screen_generation:true},{expected_screen_revision:-1},{team_id:'private'}])
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
});

test('quest open requires source revisions and rejects submission or hidden selectors', () => {
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const action={kind:'quest_ui',operation:'open',source:'ftb_quests',source_generation:1,expected_catalog_revision:1};
  const batch={...example,is_example:false,duration_ms:10000,action};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{operation:'claim'},{source:'server'},{source_generation:true},{source_generation:-1},
    {expected_catalog_revision:'1'},{expected_catalog_revision:2**53},{team_id:'private'},{quest_id:'hidden'}]) {
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
  }
  for(const key of Object.keys(action)) {
    assert.throws(()=>validate('ActionBatch',{...batch,action:Object.fromEntries(Object.entries(action).filter(([k])=>k!==key))}),/SCHEMA_UNSUPPORTED/);
  }
  assert.throws(()=>actionSemantics({...batch,duration_ms:10001} as ActionBatch),/PRECONDITION_FAILED/);
});

test('explicit close requires a window revision and rejects extra behavior or excessive duration', () => {
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const batch={...example,is_example:false,duration_ms:10000,action:{kind:'close_window',window_id:1,expected_window_revision:4}};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{window_id:-1},{window_id:true},{expected_window_revision:'4'},{drop:true},{kind:'close_all'}]) {
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...batch.action,...patch}}),/SCHEMA_UNSUPPORTED/);
  }
  assert.throws(()=>actionSemantics({...batch,duration_ms:10001} as ActionBatch),/PRECONDITION_FAILED/);
});

test('item-task open never grants reward or submission authority',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const query={source:'ftb_quests',chapter_id:'0000000000000001',quest_id:'0000000000000002',part:'tasks',after:0};
  const selection={query,revision:1,entry_id:'0000000000000003'};
  const action={kind:'quest_task',operation:'open',source:'ftb_quests',source_generation:1,expected_screen_generation:1,expected_screen_revision:1,selection};
  const batch={...example,is_example:false,duration_ms:10000,action};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{operation:'submit'},{selection:null},{team_id:'canary'},{expected_screen_revision:true},
    {selection:{...selection,query:{...query,after:513}}},{selection:{...selection,include_hidden:true}}])
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
  const reward=validate<ActionBatch>('ActionBatch',{...batch,action:{...action,selection:{...selection,query:{...query,part:'rewards'}}}});
  assert.throws(()=>actionSemantics(reward),/PRECONDITION_FAILED/);
});

test('item-menu actions bind menu revision and cannot submit or multiply scrolling',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const action={kind:'quest_menu',operation:'scroll',direction:'down',source:'ftb_quests',source_generation:1,
    expected_menu_generation:2,expected_menu_revision:3};
  const batch={...example,is_example:false,duration_ms:10000,action};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{operation:'submit'},{direction:1},{direction:'left'},{steps:99},{team_id:'private'},{expected_menu_revision:true}])
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,...patch}}),/SCHEMA_UNSUPPORTED/);
  for(const patch of [{operation:'back'},{direction:null}])
    assert.throws(()=>actionSemantics(validate<ActionBatch>('ActionBatch',{...batch,action:{...action,...patch}})),/PRECONDITION_FAILED/);
});

test('craft selection carries only a bounded visible query and source revision',()=>{
  const spec=readFileSync(new URL('../../../../SPEC.md',import.meta.url),'utf8');
  const example=[...spec.matchAll(/```json\s*([\s\S]*?)```/g)].map(match=>JSON.parse(match[1]!))
    .find(value=>value.schema==='mcbench/ActionBatch/1');
  const selection={source_generation:1,revision:2,query:{source:'jei',category:'minecraft:crafting',item_id:'test:output',role:'output',after:0}};
  const action={kind:'craft',recipe_id:'test:recipe',count:1,window_id:0,expected_window_revision:1,recipe_selection:selection};
  const batch={...example,is_example:false,duration_ms:10000,action};
  actionSemantics(validate<ActionBatch>('ActionBatch',batch));
  for(const patch of [{source_generation:-1},{source_generation:true},{revision:'2'},{private_solver:true},
    {query:{...selection.query,include_hidden:true}},{query:{...selection.query,category:'all'}}]) {
    assert.throws(()=>validate('ActionBatch',{...batch,action:{...action,recipe_selection:{...selection,...patch}}}),/SCHEMA_UNSUPPORTED/);
  }
});
