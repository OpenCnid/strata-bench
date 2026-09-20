#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { errorBody, requireThat } from './errors.js';
import type { ActionBatch } from './generated/ActionBatch.js';
import type { Observation } from './generated/Observation.js';
import type { DiscoveryQuery as RecipeQuery, QuestQuery, QuestTextQuery, QuestComponentsQuery, QuestMenuQuery } from './native_game.js';

/** This small client never spawns a bot. Deployment supplies an own-avatar grant file. */
async function main(): Promise<number> {
  const [command, ...args] = process.argv.slice(2);
  if (command === '--help') {
    console.log('mcgame observe|capabilities|act|action-status|cancel|stop-all|controls-capabilities --json\n' +
      'mcgame observe --cursor CURSOR --json\n' +
      'mcgame wait-events --after CURSOR --json\n' +
      'mcgame recipes --after CURSOR --json\n' +
      'mcgame quests [--chapter HEX_ID] --after CURSOR --json\n' +
      'mcgame quest-text --chapter HEX_ID --quest HEX_ID --after CURSOR --json\n' +
      'mcgame quest-components --chapter HEX_ID --quest HEX_ID --part tasks|rewards --after CURSOR --json\n' +
      'mcgame quest-menu --after CURSOR --json\n' +
      'mcgame quest-screen --json\n' +
      'mcgame recipe-page --json\n' +
      'mcgame recipe-query [--source jei|emi] [--category minecraft:crafting|thermal:furnace|thermal:crucible] --item ITEM_ID|--fluid FLUID_ID --role input|output --after CURSOR --json\n' +
      'mcgame move-to|look-at --x N --y N --z N [--timeout-ms N] --json\n' +
      'act reads a full ActionBatch from stdin. action-status/cancel require --request-id ID.');
    return 0;
  }
  requireThat(['observe','capabilities','wait-events','recipes','recipe-query','recipe-page','quests','quest-text','quest-components','quest-menu','quest-screen','act','action-status','cancel','stop-all','controls-capabilities','move-to','look-at'].includes(command ?? ''), 'SCHEMA_UNSUPPORTED');
  const path = process.env.STRATA_GAME_GRANT;
  requireThat(path, 'FORBIDDEN');
  const grant = JSON.parse(readFileSync(path, 'utf8')) as {
    url: string; token: string; campaign_id: string; agent_id: string; epoch: number;
  };
  const endpoint = new URL(grant.url);
  requireThat(endpoint.protocol === 'http:' && endpoint.hostname === '127.0.0.1' &&
    endpoint.pathname === '/v1/game' && !endpoint.username && !endpoint.password && !endpoint.search && !endpoint.hash, 'FORBIDDEN');
  let method = ({'action-status': 'action_status', 'stop-all': 'stop_all', 'wait-events': 'wait_events', 'recipes': 'recipes.list',
    'recipe-query':'recipes.query', 'recipe-page':'recipes.page', 'quests':'quests.list','quest-text':'quests.text','quest-components':'quests.components','quest-menu':'quests.menu','quest-screen':'quests.screen',
    'controls-capabilities': 'controls.capabilities'} as Record<string,string>)[command!] ?? command!;
  let target: string | null = null;
  let after: number | null = null;
  let cursor: string | null = null;
  let recipeQuery: RecipeQuery | null = null;
  let questQuery: QuestQuery | null = null;
  let questTextQuery: QuestTextQuery | null = null;
  let questComponentsQuery: QuestComponentsQuery | null = null;
  let questMenuQuery:QuestMenuQuery|null=null;
  const jsonArgs = args.filter(a => a !== '--json');
  const wrapper = command === 'move-to' || command === 'look-at';
  if (method === 'action_status' || method === 'cancel') {
    requireThat(jsonArgs.length === 2 && jsonArgs[0] === '--request-id', 'SCHEMA_UNSUPPORTED'); target = jsonArgs[1]!;
  } else if (method === 'wait_events' || method === 'recipes.list') {
    requireThat(jsonArgs.length === 2 && jsonArgs[0] === '--after', 'SCHEMA_UNSUPPORTED');
    after = Number(jsonArgs[1]);
    requireThat(Number.isSafeInteger(after) && after >= 0, 'SCHEMA_UNSUPPORTED');
  } else if (method === 'quests.menu') {
    requireThat(jsonArgs.length===2 && jsonArgs[0]==='--after','SCHEMA_UNSUPPORTED');const page=Number(jsonArgs[1]);
    requireThat(Number.isSafeInteger(page) && page>=0 && page<=512,'SCHEMA_UNSUPPORTED');questMenuQuery={source:'ftb_quests',after:page};
  } else if (method === 'quests.components') {
    const options:Record<string,string>={};requireThat(jsonArgs.length===8,'SCHEMA_UNSUPPORTED');
    for(let i=0;i<jsonArgs.length;i+=2) {
      const key=jsonArgs[i]!;requireThat(['--chapter','--quest','--part','--after'].includes(key) && !Object.hasOwn(options,key),'SCHEMA_UNSUPPORTED');
      options[key]=jsonArgs[i+1]!;
    }
    const chapter=options['--chapter']!,quest=options['--quest']!,part=options['--part']!,page=Number(options['--after']);
    requireThat([chapter,quest].every(x=>typeof x==='string' && x.length===16 && /^[0-9A-F]{16}$/.test(x))
      && (part==='tasks' || part==='rewards') && Number.isSafeInteger(page) && page>=0 && page<=512,'SCHEMA_UNSUPPORTED');
    questComponentsQuery={source:'ftb_quests',chapter_id:chapter,quest_id:quest,part,after:page};
  } else if (method === 'quests.text') {
    const options:Record<string,string>={};requireThat(jsonArgs.length===6,'SCHEMA_UNSUPPORTED');
    for(let i=0;i<jsonArgs.length;i+=2) {
      const key=jsonArgs[i]!;requireThat(['--chapter','--quest','--after'].includes(key) && !Object.hasOwn(options,key),'SCHEMA_UNSUPPORTED');
      options[key]=jsonArgs[i+1]!;
    }
    const chapter=options['--chapter']!,quest=options['--quest']!,page=Number(options['--after']);
    requireThat([chapter,quest].every(x=>typeof x==='string' && x.length===16 && /^[0-9A-F]{16}$/.test(x))
      && Number.isSafeInteger(page) && page>=0 && page<=512,'SCHEMA_UNSUPPORTED');
    questTextQuery={source:'ftb_quests',chapter_id:chapter,quest_id:quest,after:page};
  } else if (method === 'quests.list') {
    const options:Record<string,string>={};requireThat(jsonArgs.length===2 || jsonArgs.length===4,'SCHEMA_UNSUPPORTED');
    for(let i=0;i<jsonArgs.length;i+=2) {
      const key=jsonArgs[i]!;requireThat(['--chapter','--after'].includes(key) && !Object.hasOwn(options,key),'SCHEMA_UNSUPPORTED');
      options[key]=jsonArgs[i+1]!;
    }
    const chapter=options['--chapter'] ?? null,page=Number(options['--after']);
    requireThat((chapter===null || chapter.length===16 && /^[0-9A-F]{16}$/.test(chapter)) && Number.isSafeInteger(page) && page>=0 && page<=4096,'SCHEMA_UNSUPPORTED');
    questQuery={source:'ftb_quests',chapter_id:chapter,after:page};
  } else if (method === 'recipes.query') {
    const options: Record<string,string> = {};
    requireThat([6,8,10].includes(jsonArgs.length), 'SCHEMA_UNSUPPORTED');
    for (let i=0;i<jsonArgs.length;i+=2) {
      const name=jsonArgs[i]!;
      requireThat(['--source','--category','--item','--fluid','--role','--after'].includes(name) && !Object.hasOwn(options,name), 'SCHEMA_UNSUPPORTED');
      options[name]=jsonArgs[i+1]!;
    }
    const category=options['--category'] ?? 'minecraft:crafting', source=options['--source'] ?? 'jei';
    const item = options['--item'] ?? options['--fluid'], role = options['--role']!, page = Number(options['--after']);
    requireThat((options['--item'] === undefined) !== (options['--fluid'] === undefined)
      && typeof item==='string' && item.length <= 256 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(item)
      && ['input','output'].includes(role) && Number.isSafeInteger(page) && page >= 0 && page <= 512, 'SCHEMA_UNSUPPORTED');
    requireThat(['jei','emi'].includes(source) && (source !== 'emi' || category === 'minecraft:crafting')
      && ['minecraft:crafting','thermal:furnace','thermal:crucible'].includes(category)
      && (category!=='minecraft:crafting' || options['--fluid']===undefined), 'SCHEMA_UNSUPPORTED');
    recipeQuery = {source,category,...(options['--fluid']===undefined ? {item_id:item} : {fluid_id:item}),
      role:role as 'input'|'output',after:page} as RecipeQuery;
  } else if (method === 'observe' && jsonArgs.length) {
    requireThat(jsonArgs.length === 2 && jsonArgs[0] === '--cursor', 'SCHEMA_UNSUPPORTED');
    cursor = jsonArgs[1]!; method = 'observe.page';
  } else if (!wrapper) requireThat(jsonArgs.length === 0, 'SCHEMA_UNSUPPORTED');
  let action: unknown = null;
  const call = async (method: string, action: unknown = null, target_request_id: string | null = null) => {
    const request = {schema: 'strata/GameRequest/1', request_id: randomUUID(),
      campaign_id: grant.campaign_id, agent_id: grant.agent_id, epoch: grant.epoch,
      deadline_at: new Date(Date.now()+5000).toISOString(), method, action, target_request_id, after, cursor, recipe_query:recipeQuery, quest_query:questQuery, quest_text_query:questTextQuery, quest_components_query:questComponentsQuery,quest_menu_query:questMenuQuery};
    // Never retry a mutation after a timeout. Query its existing ID explicitly.
    const response = await fetch(endpoint, {method: 'POST', headers: {
      Authorization: `Bearer ${grant.token}`, 'Content-Type': 'application/json'},
      body: JSON.stringify(request), signal: AbortSignal.timeout(5500), redirect: 'error'});
    const body = await response.text();
    requireThat(Buffer.byteLength(body) <= 131072, 'CAPACITY_EXCEEDED');
    return JSON.parse(body);
  };
  if (wrapper) {
    const options: Record<string, number> = {};
    requireThat(jsonArgs.length % 2 === 0, 'SCHEMA_UNSUPPORTED');
    for (let i=0;i<jsonArgs.length;i+=2) {
      const name=jsonArgs[i]!;
      requireThat(['--x','--y','--z','--timeout-ms'].includes(name) && !(name in options), 'SCHEMA_UNSUPPORTED');
      options[name]=Number(jsonArgs[i+1]); requireThat(Number.isFinite(options[name]), 'SCHEMA_UNSUPPORTED');
    }
    requireThat(['--x','--y','--z'].every(k=>k in options), 'SCHEMA_UNSUPPORTED');
    const caps=await call('capabilities');
    const observed=await call('observe');
    if (caps.status !== 'ok' || observed.status !== 'ok') {
      console.log(JSON.stringify(caps.status !== 'ok' ? caps : observed)); return 4;
    }
    const o=observed.result as Observation;
    const duration=options['--timeout-ms'] ?? (command === 'move-to' ? 30000 : 10000);
    const target={x:options['--x']!,y:options['--y']!,z:options['--z']!};
    const b: ActionBatch = {schema:'mcbench/ActionBatch/1',is_example:false,campaign_id:grant.campaign_id,
      agent_id:grant.agent_id,epoch:grant.epoch,seq:(o.last_action_seq ?? 0)+1,recorded_at:new Date().toISOString(),
      lease_id:caps.result.lease_id,request_id:randomUUID(),observation_id:o.observation_id,
      mode:'structured',expected_state_revision:o.state_revision,capability_digest:o.capability_digest,
      control_revision:o.control_revision,keymap_digest:null,deadline_at:new Date(Date.now()+duration).toISOString(),
      duration_ms:duration,action:command === 'move-to' ? {kind:'move_to',target,tolerance:.5} : {kind:'look_at',target},
      events:[],release_at_end:true};
    action=b; method='act';
    // Retain the ID even if transport acknowledgement is lost; this is not a secret.
    process.stderr.write(JSON.stringify({request_id:b.request_id})+'\n');
  }
  if (method === 'act' && !wrapper) {
    let body = '';
    for await (const chunk of process.stdin) {
      body += chunk; requireThat(Buffer.byteLength(body) <= 65536, 'CAPACITY_EXCEEDED');
    }
    action = JSON.parse(body);
  }
  const result = await call(method,action,target) as {status: string; result?: {status?: string}};
  console.log(JSON.stringify(result));
  if (result.status === 'error') return 4;
  if (['accepted','executing'].includes(result.result?.status ?? '')) return 2;
  if (['failed','rejected','cancelled','unknown'].includes(result.result?.status ?? '')) return 3;
  return 0;
}
try { process.exitCode = await main(); }
catch(e) { console.log(JSON.stringify({schema: 'strata/GameResponse/1', status: 'error', error: errorBody(e, null, null)})); process.exitCode = 4; }
