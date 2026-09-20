import { request as httpRequest } from 'node:http';
import { readFileSync, statSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import type { RpcRequest } from './generated/RpcRequest.js';
export type DiscoveryQuery = NonNullable<RpcRequest['recipe_query']>;
export type QuestQuery = NonNullable<RpcRequest['quest_query']>;
export type QuestTextQuery = NonNullable<RpcRequest['quest_text_query']>;
export type QuestComponentsQuery=NonNullable<RpcRequest['quest_components_query']>;
export type QuestMenuQuery=NonNullable<RpcRequest['quest_menu_query']>;
import { actionSemantics, canonical, digest, Fault, mono, requireThat, validate,
  type ActionBatch, type StructuredState } from './protocol.js';

/** Private broker transport. Never include this module or its descriptor in gameplay packages. */
export const FORGE_ACTIONS = ['attack','chat','click_slot','close_window','craft','dig','equip','interact_block','interact_entity','look_at','move_to','place','quest_menu','quest_navigate','quest_reward','quest_task','quest_ui','recipe_navigate','use_item'] as const;
const READ = ['capabilities','observe','identity','observe_bound','recipes','recipe_query','quests','quest_text','quest_components','quest_menu','quest_screen','recipe_page'];
export const RECIPE_PAGE_POLICY='jei-task-drawn-slot-header-controls-empty-loop/4';
export const RECIPE_NAVIGATION_POLICY='jei-current-page-controls-history-fresh-frame200/2';
export const QUEST_MENU_ACTION_POLICY='ftb-current-item-choice-menu-back-wheel/2';
export const QUEST_REWARD_POLICY='ftb-visible-choice-reward-menu-open/1';
export const QUEST_TASK_POLICY='ftb-visible-item-task-menu-or-jei-open/2';
export const QUEST_NAVIGATION_POLICY='ftb-own-team-book-and-task-recipes-state/2';
export const QUEST_OPEN_POLICY='ftb-own-team-open-screen-cas/1';
export const QUEST_MENU_POLICY='ftb-current-item-choice-clipped-pages32/4';
export const QUEST_COMPONENTS_POLICY='ftb-visible-own-quest-task-reward-tooltips-pages32/1';
export const QUEST_TEXT_POLICY='ftb-visible-own-quest-plain-text-pages32/1';
export const QUEST_POLICY = 'ftb-visible-chapters-quests-own-team-pages32/1';
export const RECIPE_QUERY_POLICY = 'jei-thermal-emi-crafting-visible-focus-pages32/3';
const LANE = ['arm','renew','deliver','act','action_status','cancel','stop_all','lane_status','authority'];
const MUTATIONS = new Set(['arm','renew','deliver','act','cancel','stop_all']);
type ObjectValue = Record<string, unknown>;
export function fields(value: unknown, names: string[]): asserts value is ObjectValue {
  requireThat(value !== null && typeof value === 'object' && !Array.isArray(value), 'GAME_RESPONSE_INVALID');
  requireThat(Object.keys(value).length === names.length && names.every(k => Object.hasOwn(value, k)), 'GAME_RESPONSE_INVALID');
}
const uint = (x: unknown): x is number => Number.isSafeInteger(x) && Number(x) >= 0;
const id = (x: unknown): x is string => typeof x === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(x);
const hash = (x: unknown): x is string => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const code = (x: unknown): boolean => x === null || typeof x === 'string' && /^[A-Z][A-Z0-9_]{1,95}$/.test(x);
function queryArgs(value: unknown): asserts value is DiscoveryQuery {
  const target = value && typeof value === 'object' && Object.hasOwn(value,'fluid_id') ? 'fluid_id' : 'item_id';
  fields(value, ['source','category',target,'role','after']);
  const targetId = value[target];
  requireThat(['jei','emi'].includes(String(value.source)) && (value.source !== 'emi' || value.category === 'minecraft:crafting') && ['minecraft:crafting','thermal:furnace','thermal:crucible'].includes(String(value.category))
    && (value.category !== 'minecraft:crafting' || target === 'item_id')
    && typeof targetId === 'string' && targetId.length <= 256 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(targetId)
    && ['input','output'].includes(String(value.role)) && uint(value.after) && value.after <= 512, 'GAME_ARGUMENTS_INVALID');
}
function questComponentsArgs(value:unknown): asserts value is QuestComponentsQuery {
  fields(value,['source','chapter_id','quest_id','part','after']);
  requireThat(value.part==='tasks' || value.part==='rewards','GAME_ARGUMENTS_INVALID');
  const {part,...query}=value;questTextArgs(query);
}
function questTextArgs(value:unknown): asserts value is QuestTextQuery {
  fields(value,['source','chapter_id','quest_id','after']);
  requireThat(value.source==='ftb_quests' && [value.chapter_id,value.quest_id].every(x=>typeof x==='string'
    && x.length===16 && /^[0-9A-F]{16}$/.test(x)) && uint(value.after) && value.after<=512,'GAME_ARGUMENTS_INVALID');
}
function questArgs(value:unknown): asserts value is QuestQuery {
  fields(value,['source','chapter_id','after']);
  requireThat(value.source==='ftb_quests' && (value.chapter_id===null || typeof value.chapter_id==='string' && value.chapter_id.length===16
    && /^[0-9A-F]{16}$/.test(value.chapter_id)) && uint(value.after) && value.after<=4096,'GAME_ARGUMENTS_INVALID');
}

/** JSON.parse alone silently accepts duplicate keys. Check nesting and duplicates first. */
export function strictJson(text: string): unknown {
  let at = 0;
  const space = () => {while (/\s/.test(text[at] ?? '') && at < text.length) at++;};
  function string(): string {
    const start = at++;
    while (at < text.length) {
      const char = text[at++];
      if (char === '\\') {at++; continue;}
      if (char === '"') return JSON.parse(text.slice(start, at)) as string;
    }
    throw new Fault('GAME_RESPONSE_INVALID');
  }
  function value(depth: number): void {
    requireThat(depth <= 20, 'GAME_RESPONSE_INVALID'); space();
    const char = text[at];
    if (char === '"') {string(); return;}
    if (char === '{' || char === '[') {
      at++; space(); const end = char === '{' ? '}' : ']'; const keys = new Set<string>();
      if (text[at] === end) {at++; return;}
      while (at < text.length) {
        if (char === '{') {
          requireThat(text[at] === '"', 'GAME_RESPONSE_INVALID'); const key = string();
          requireThat(!keys.has(key), 'GAME_RESPONSE_INVALID'); keys.add(key); space();
          requireThat(text[at++] === ':', 'GAME_RESPONSE_INVALID');
        }
        value(depth + 1); space();
        if (text[at] === end) {at++; return;}
        requireThat(text[at++] === ',', 'GAME_RESPONSE_INVALID'); space();
      }
      throw new Fault('GAME_RESPONSE_INVALID');
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(at));
    requireThat(token, 'GAME_RESPONSE_INVALID'); at += token[0].length;
  }
  try {value(0); space(); requireThat(at === text.length, 'GAME_RESPONSE_INVALID'); return JSON.parse(text);}
  catch {throw new Fault('GAME_RESPONSE_INVALID');}
}
export interface NativeConnection {
  schema: 'strata/NativeGameConnection/1'; host: '127.0.0.1'; port: number; session_id: string;
  bearer_token: string; fingerprint: string; operator_development_only: true;
}
export interface NativeSnapshot {
  schema: 'strata/NativeGameSnapshot/1'; snapshot_id: string; state_revision: number;
  source_clock_id: string; captured_elapsed_ms: number; age_ms: number; state: StructuredState;
}
export interface NativeAuthority {
  schema: 'strata/NativeGameAuthority/1'; campaign_id: string; agent_id: string;
  capability_digest: string; body_fingerprint: string; expires_unix_ms: number; primitive_limit: number;
}
export interface NativeLane {
  schema: 'strata/NativeGameLane/1'; fenced: boolean; fence_token: string; reason: string | null;
  journal_healthy: boolean; epoch: number | null; active_request_id: string | null;
  attempted_primitive_events: number; primitive_limit: number;
}
export interface NativeReceipt {
  schema: 'strata/NativeGameActionReceipt/1'; request_id: string; epoch: number; action_seq: number;
  status: 'accepted'|'executing'|'emitted'|'cancelled'|'unknown'|'failed'; attempted_events: number;
  emitted_events: number | null; release_confirmed: boolean; error_code: string | null; requires_resync: boolean;
}
export interface NativeResults {
  quest_screen:{schema:string;body_fingerprint:string;connection_generation:number;policy:string;source_generation:number;
    screen_generation:number;revision:number;kind:'closed'|'quest_book'|'task_recipes';chapter_id:string|null;quest_id:string|null};
  recipe_page:{schema:string;body_fingerprint:string;connection_generation:number;policy:string;source:'jei';coverage:'slot_header_control_draw_operands';complete:false;
    source_generation:number;screen_generation:number;screen_revision:number;chapter_id:string;quest_id:string;revision:string;
    headers:{kind:'category'|'page';state:'text'|'clipped'|'unsupported';text:string|null}[];
    controls:{kind:'category_next'|'category_previous'|'page_next'|'page_previous';state:'enabled'|'disabled'|'clipped'}[];
    layouts:{category_id:string;clipped:boolean;slots:{index:number;role:'input'|'output'|'catalyst'|'render_only';
      display:{kind:'empty'|'unsupported'}|{kind:'item'|'fluid';id:string;amount:number}}[]}[]};
  quest_menu:{schema:string;body_fingerprint:string;connection_generation:number;query:QuestMenuQuery;source_generation:number;
    menu_generation:number;policy:string;revision:number;menu_kind:'item_alternatives'|'reward_choices';
    context:{chapter_id:string;quest_id:string;title:string} & ({task_id:string}|{reward_id:string});
    controls:Array<{control:'back'|'submit';title:string;enabled:boolean;tooltip:Array<{kind:'text'|'unsupported';text:string|null}>}>;
    entries:Array<{index:number;tooltip:Array<{kind:'text'|'unsupported';text:string|null}>} &
      ({item_id:string;count:number;name:string}|{title:string;enabled:boolean})>;next_cursor:number|null};
  capabilities: ObjectValue; observe: NativeSnapshot;
  observe_bound: {schema: string; snapshot: NativeSnapshot; body_fingerprint: string; connection_generation: number};
  identity: {schema: string; body_fingerprint: string; connection_generation: number};
  recipes: {schema:string;body_fingerprint:string;connection_generation:number;revision:number;recipes:ObjectValue[];next_cursor:number|null};
  recipe_query: NativeResults['recipes'] & {query:DiscoveryQuery;source_generation:number;policy:string};
  quest_components:{schema:string;body_fingerprint:string;connection_generation:number;query:QuestComponentsQuery;source_generation:number;
    policy:string;revision:number;entries:Array<{entry_id:string;kind:'task'|'reward';title:string;
      tooltip:Array<{kind:'text'|'unsupported';text:string|null}>;
      task:{completed:boolean;optional:boolean;progress_label:string|null}|null;
      reward:{claim_state:'can_claim'|'cannot_claim'|'claimed';team_reward:boolean}|null}>;next_cursor:number|null};
  quest_text:{schema:string;body_fingerprint:string;connection_generation:number;query:QuestTextQuery;source_generation:number;
    policy:string;revision:number;title:string;subtitle:string;description_visible:boolean;
    lines:Array<{kind:'text'|'page_break'|'unsupported';text:string|null}>;next_cursor:number|null};
  quests: {schema:string;body_fingerprint:string;connection_generation:number;query:QuestQuery;source_generation:number;
    policy:string;revision:number;entries:ObjectValue[];next_cursor:number|null};
  authority: NativeAuthority; arm: NativeLane; renew: NativeLane; lane_status: NativeLane; stop_all: NativeLane;
  deliver: {observation_id: string; snapshot_id: string; state_revision: number};
  act: NativeReceipt; action_status: NativeReceipt; cancel: NativeReceipt;
}
export type NativeOperation = keyof NativeResults;
const NATIVE_FAILURE_CODES = new Set(['TARGET_OCCLUDED','OUT_OF_REACH','PRECONDITION_FAILED',
  'TARGET_NOT_OBSERVED','REVISION_CONFLICT','GAME_MENU_RESYNC_REQUIRED','GAME_SURVIVAL_CONTEXT_REQUIRED',
  'GAME_SCREEN_OPEN','GAME_RESPONSE_INVALID','GAME_TRANSPORT_UNAVAILABLE','GAME_OBSERVATION_UNAVAILABLE',
  'DEADLINE_EXCEEDED','LEASE_EXPIRED','STALE_EPOCH','CAPABILITY_MISSING','MECHANIC_UNSUPPORTED',
  'BUDGET_EXHAUSTED','GAME_BODY_MISMATCH','EVIDENCE_UNAVAILABLE']);
/** Operator-only diagnosis; never a known-outcome receipt or retry permission. */
export function nativeFailureCode(error: unknown): string {
  const code = error instanceof NativeOutcomeUnknown ? error.diagnosticCode
    : error instanceof Fault ? error.code : null;
  return code !== null && NATIVE_FAILURE_CODES.has(code) ? code : 'UNCLASSIFIED_NATIVE_FAILURE';
}
export class NativeOutcomeUnknown extends Fault {
  readonly diagnosticCode: string;
  constructor(readonly transportRequestId: string, readonly operation: string, failure?: unknown) {
    super('GAME_OUTCOME_UNKNOWN');
    this.diagnosticCode = nativeFailureCode(failure);
  }
}
export const nativeCapabilities = (mutation: boolean) => ({
  schema:'strata/NativeGameCapabilities/1', profile:'forge1192-structured-development/1',
  backend:'forge_client', track:'structured-actions/v1', observation_policy:'opaque-voxel-fixed305-radius16/2',
  campaign_admission:false, conformance:'unverified', operator_development_only:true,
  operations:[...READ,...(mutation ? LANE : [])], actions:mutation ? [...FORGE_ACTIONS] : [],
  native_action_policy:'durable-intent-client-thread-nineteen-actions/2',block_target_policy:'observed-outline-centers64-local16/1',menu_close_policy:'explicit-close-own-inventory-feedback-conservation/1',
  recipe_policy:'player-book-exact-shaped-shapeless-pages32/1',crafting_policy:'known-recipe-server-preview-transition-bound20/6',
  recipe_query_policy:RECIPE_QUERY_POLICY,
  quest_policy:QUEST_POLICY,
  quest_text_policy:QUEST_TEXT_POLICY,
  quest_components_policy:QUEST_COMPONENTS_POLICY,
  quest_menu_action_policy:QUEST_MENU_ACTION_POLICY,quest_reward_policy:QUEST_REWARD_POLICY,quest_task_policy:QUEST_TASK_POLICY,quest_navigation_policy:QUEST_NAVIGATION_POLICY,quest_menu_policy:QUEST_MENU_POLICY,quest_open_policy:QUEST_OPEN_POLICY,
  recipe_page_policy:RECIPE_PAGE_POLICY,
  recipe_navigation_policy:RECIPE_NAVIGATION_POLICY,
  manual_crafting_policy:'visible-recipe-manual-grid-feedback-search4096/1',
  machine_observation_policy:'thermal-current-gui-energy-fluid-base-slots/1',
  machine_inventory_policy:'thermal-visible-slot-owned-transfer-feedback/2',
  machine_input_policy:'thermal-display-independent-slot-cursor-fence/1',
  navigation_policy:'delivered-shapes-level-bfs512-radius16/1', collision_policy:'delivered-static-vanilla-shapes-age30s/1',
  movement_policy:'level-forward-coast-neutral8-charged-ticks/1', keybindings:false, screenshots:false,
});
function result(operation: NativeOperation, args: ObjectValue, value: unknown): unknown {
  if (operation === 'capabilities') {
    requireThat([true,false].some(m => canonical(value) === canonical(nativeCapabilities(m))), 'CAPABILITY_MISSING'); return value;
  }
  if (operation === 'observe_bound') {
    fields(value, ['schema','snapshot','body_fingerprint','connection_generation']);
    requireThat(value.schema === 'strata/NativeBoundSnapshot/1' && hash(value.body_fingerprint)
      && uint(value.connection_generation), 'GAME_RESPONSE_INVALID');
    result('observe', args, value.snapshot);
  } else if (operation === 'recipes' || operation === 'recipe_query') {
    const queried = operation === 'recipe_query';
    fields(value, ['schema','body_fingerprint','connection_generation','revision','recipes','next_cursor',
      ...(queried ? ['query','source_generation','policy'] : [])]);
    requireThat(value.schema === (queried ? 'strata/NativeRecipeQuery/1' : 'strata/NativeRecipeList/1') && hash(value.body_fingerprint) && uint(value.connection_generation)
      && uint(value.revision) && Array.isArray(value.recipes) && value.recipes.length <= 32
      && (value.next_cursor === null || uint(value.next_cursor) && value.next_cursor <= (queried ? 512 : 10000)
        && value.next_cursor === Number(args.after) + value.recipes.length && value.recipes.length > 0), 'GAME_RESPONSE_INVALID');
    if (queried) requireThat(canonical(value.query) === canonical(args) && uint(value.source_generation)
      && value.policy === RECIPE_QUERY_POLICY && Number(args.after) + value.recipes.length <= 512, 'GAME_RESPONSE_INVALID');
    let previous = '';
    const itemId = (x:unknown) => typeof x === 'string' && x.length <= 256 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(x);
    for (const recipe of value.recipes) {
      requireThat(recipe && typeof recipe === 'object', 'GAME_RESPONSE_INVALID');
      const machine = queried && args.category !== 'minecraft:crafting';
      fields(recipe, [...(recipe.supported === true ? machine ? ['recipe_id','supported','category','energy_rf','slots','output_tooltip']
        : ['recipe_id','supported','serializer','width','height','ingredients','result'] : ['recipe_id','supported']),
        ...(queried ? ['craft_authority'] : [])]);
      if (queried) requireThat((machine ? ['discovery_only'] : ['recipe_book','discovery_only']).includes(String(recipe.craft_authority)), 'GAME_RESPONSE_INVALID');
      requireThat(itemId(recipe.recipe_id) && String(recipe.recipe_id) > previous && typeof recipe.supported === 'boolean', 'GAME_RESPONSE_INVALID');
      previous = String(recipe.recipe_id);
      if (!recipe.supported) continue;
      if (machine) {
        requireThat(recipe.category === args.category && (recipe.energy_rf === null
          || uint(recipe.energy_rf) && recipe.energy_rf > 0 && recipe.energy_rf <= 2147483647)
          && Array.isArray(recipe.slots) && recipe.slots.length === 2, 'GAME_RESPONSE_INVALID');
        for (let i=0;i<2;i++) {
          const slot=recipe.slots[i];fields(slot,['role','ingredients']);
          requireThat(slot.role === (i===0 ? 'input' : 'output') && Array.isArray(slot.ingredients)
            && slot.ingredients.length >= 1 && slot.ingredients.length <= (i===0 ? 64 : 1), 'GAME_RESPONSE_INVALID');
          const kind=i===0 || recipe.category==='thermal:furnace' ? 'item' : 'fluid'; let previousChoice='';
          for (const choice of slot.ingredients) {
            const key=kind+'_id', quantity=kind==='item' ? 'count' : 'amount_mb';
            fields(choice,['kind',key,quantity]);
            requireThat(choice.kind===kind && itemId(choice[key]) && String(choice[key])>previousChoice
              && uint(choice[quantity]) && Number(choice[quantity])>0 && Number(choice[quantity])<=(kind==='item' ? 64 : 2147483647), 'GAME_RESPONSE_INVALID');
            previousChoice=String(choice[key]);
          }
        }
        if (recipe.output_tooltip !== null) {
          fields(recipe.output_tooltip,['kind','percent']);
          requireThat(recipe.category==='thermal:furnace' && ['chance','additional_chance'].includes(String(recipe.output_tooltip.kind))
            && uint(recipe.output_tooltip.percent) && recipe.output_tooltip.percent <=99, 'GAME_RESPONSE_INVALID');
        }
        continue;
      }
      const shaped = recipe.serializer === 'minecraft:crafting_shaped';
      requireThat((shaped || recipe.serializer === 'minecraft:crafting_shapeless') && uint(recipe.width) && uint(recipe.height)
        && Array.isArray(recipe.ingredients) && recipe.ingredients.length > 0 && recipe.ingredients.length <= 9
        && (shaped ? recipe.width >= 1 && recipe.width <= 3 && recipe.height >= 1 && recipe.height <= 3
          && recipe.ingredients.length === recipe.width * recipe.height : recipe.width === 0 && recipe.height === 0), 'GAME_RESPONSE_INVALID');
      let nonempty = false;
      for (const alternatives of recipe.ingredients) {
        requireThat(Array.isArray(alternatives) && alternatives.length <= 64 && (shaped || alternatives.length > 0)
          && alternatives.every(itemId) && alternatives.every((x:string,i:number) => i === 0 || x > alternatives[i-1]), 'GAME_RESPONSE_INVALID');
        nonempty ||= alternatives.length > 0;
      }
      fields(recipe.result, ['item_id','count']);
      requireThat(nonempty && itemId(recipe.result.item_id) && uint(recipe.result.count) && recipe.result.count >= 1 && recipe.result.count <= 64, 'GAME_RESPONSE_INVALID');
    }
    requireThat(Buffer.byteLength(canonical({revision:value.revision,recipes:value.recipes,next_cursor:value.next_cursor,
      ...(queried ? {query:value.query,source_generation:value.source_generation,policy:value.policy} : {})})) <= 32768, 'GAME_RESPONSE_INVALID');
  } else if (operation === 'recipe_page') {
    fields(value,['schema','body_fingerprint','connection_generation','policy','source','coverage','complete',
      'source_generation','screen_generation','screen_revision','chapter_id','quest_id','revision','layouts','headers','controls']);
    requireThat(value.schema==='strata/NativeRecipePage/4' && value.policy===RECIPE_PAGE_POLICY && value.source==='jei'
      && value.coverage==='slot_header_control_draw_operands' && value.complete===false && hash(value.body_fingerprint) && hash(value.revision)
      && [value.connection_generation,value.source_generation,value.screen_generation,value.screen_revision].every(uint)
      && [value.chapter_id,value.quest_id].every(x=>typeof x==='string' && x.length===16 && /^[0-9A-F]{16}$/.test(x))
      && Array.isArray(value.layouts) && value.layouts.length<=32,'GAME_RESPONSE_INVALID');
    requireThat(Array.isArray(value.headers) && value.headers.length===2,'GAME_RESPONSE_INVALID');
    for(const [index,label] of value.headers.entries()) {
      fields(label,['kind','state','text']);
      requireThat(label.kind===(index===0?'category':'page') && typeof label.state==='string'
        && ['text','clipped','unsupported'].includes(label.state),'GAME_RESPONSE_INVALID');
      if(label.state==='text')requireThat(typeof label.text==='string' && Array.from(label.text).length<=1024
        && !/[\uD800-\uDFFF]/u.test(label.text) && Buffer.byteLength(label.text)<=4096,'GAME_RESPONSE_INVALID');
      else requireThat(label.text===null,'GAME_RESPONSE_INVALID');
    }
    requireThat(Array.isArray(value.controls) && value.controls.length===4,'GAME_RESPONSE_INVALID');
    for(const [index,control] of value.controls.entries()) {
      fields(control,['kind','state']);
      requireThat(control.kind===['category_next','category_previous','page_next','page_previous'][index]
        && typeof control.state==='string' && ['enabled','disabled','clipped'].includes(control.state),'GAME_RESPONSE_INVALID');
    }
    const registry=(x:unknown):x is string=>typeof x==='string' && x.length<=256 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.exec(x)?.[0]===x;
    for(const layout of value.layouts) {
      fields(layout,['category_id','clipped','slots']);
      requireThat(registry(layout.category_id) && typeof layout.clipped==='boolean' && Array.isArray(layout.slots) && layout.slots.length<=128,'GAME_RESPONSE_INVALID');
      let previous=-1;
      for(const slot of layout.slots) {
        fields(slot,['index','role','display']);
        requireThat(uint(slot.index) && slot.index<=127 && slot.index>previous
          && (layout.clipped || slot.index===previous+1) && typeof slot.role==='string'
          && ['input','output','catalyst','render_only'].includes(slot.role),'GAME_RESPONSE_INVALID');
        previous=slot.index;
        const display=slot.display;
        requireThat(display!==null && typeof display==='object' && !Array.isArray(display),'GAME_RESPONSE_INVALID');
        const kind=(display as Record<string,unknown>).kind;
        if(kind==='empty' || kind==='unsupported')fields(display,['kind']);
        else {
          fields(display,['kind','id','amount']);
          requireThat((kind==='item' || kind==='fluid') && registry(display.id) && uint(display.amount)
            && display.amount>=1 && display.amount<=2147483647,'GAME_RESPONSE_INVALID');
        }
      }
    }
    const {schema,body_fingerprint,connection_generation,...projected}=value;
    requireThat(Buffer.byteLength(canonical(projected))<=32768,'GAME_RESPONSE_INVALID');
    const {revision,...content}=projected;requireThat(revision===digest(content),'GAME_RESPONSE_INVALID');
  } else if (operation === 'quest_screen') {
    fields(value,['schema','body_fingerprint','connection_generation','policy','source_generation','screen_generation','revision','kind','chapter_id','quest_id']);
    requireThat(value.schema==='strata/NativeQuestScreen/1' && value.policy===QUEST_NAVIGATION_POLICY
      && hash(value.body_fingerprint) && [value.connection_generation,value.source_generation,value.screen_generation,value.revision].every(uint)
      && ['closed','quest_book','task_recipes'].includes(String(value.kind))
      && [value.chapter_id,value.quest_id].every(id=>id===null || typeof id==='string' && /^[0-9A-F]{16}$/.test(id) && id.length===16)
      && (value.kind!=='closed' || value.chapter_id===null && value.quest_id===null)
      && (value.quest_id===null || value.chapter_id!==null)
      && (value.kind!=='task_recipes' || value.quest_id!==null),'GAME_RESPONSE_INVALID');
  } else if (operation === 'quest_menu') {
    fields(value,['schema','body_fingerprint','connection_generation','query','source_generation','menu_generation','policy','revision',
      'menu_kind','context','controls','entries','next_cursor']);
    const text=(x:unknown,max:number):x is string=>typeof x==='string' && [...x].length<=max
      && !/[\uD800-\uDFFF]/u.test(x) && Buffer.byteLength(x)<=max*4;
    const tooltip=(x:unknown)=>{
      requireThat(Array.isArray(x) && x.length<=64,'GAME_RESPONSE_INVALID');
      for(const line of x) {fields(line,['kind','text']);requireThat(line.kind==='text' ? text(line.text,4096)
        : line.kind==='unsupported' && line.text===null,'GAME_RESPONSE_INVALID');}
    };
    requireThat(value.schema==='strata/NativeQuestMenu/1' && hash(value.body_fingerprint) && uint(value.connection_generation)
      && canonical(value.query)===canonical(args) && uint(value.source_generation) && uint(value.menu_generation) && value.menu_generation>0
      && value.policy===QUEST_MENU_POLICY && uint(value.revision) && (value.menu_kind==='item_alternatives' || value.menu_kind==='reward_choices')
      && Array.isArray(value.entries) && value.entries.length<=32 && Number(args.after)+value.entries.length<=512
      && Array.isArray(value.controls) && value.controls.length<=2 && Buffer.byteLength(canonical(value.controls))<=8192
      && (value.next_cursor===null || uint(value.next_cursor) && value.next_cursor<=512 && value.entries.length>0
        && value.next_cursor===Number(args.after)+value.entries.length),'GAME_RESPONSE_INVALID');
    const choice=value.menu_kind==='reward_choices';
    requireThat(!choice || value.controls.length===0,'GAME_RESPONSE_INVALID');
    const member=choice?'reward_id':'task_id';
    fields(value.context,['chapter_id','quest_id',member,'title']);
    for(const field of ['chapter_id','quest_id',member])requireThat(typeof value.context[field]==='string'
      && value.context[field].length===16 && /^[0-9A-F]{16}$/.test(value.context[field]),'GAME_RESPONSE_INVALID');
    requireThat(text(value.context.title,1024),'GAME_RESPONSE_INVALID');
    for(const [i,entry] of value.entries.entries()) {
      if(choice) {
        fields(entry,['index','title','enabled','tooltip']);
        requireThat(uint(entry.index) && entry.index===Number(args.after)+i && text(entry.title,1024)
          && typeof entry.enabled==='boolean' && Buffer.byteLength(canonical(entry))<=16384,'GAME_RESPONSE_INVALID');
        tooltip(entry.tooltip);continue;
      }
      fields(entry,['index','item_id','count','name','tooltip']);
      requireThat(uint(entry.index) && entry.index===Number(args.after)+i
        && typeof entry.item_id==='string' && entry.item_id.length<=256 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(entry.item_id)
        && entry.item_id===entry.item_id.trim() && uint(entry.count) && entry.count>=1
        && entry.count<=2147483647 && text(entry.name,1024) && Buffer.byteLength(canonical(entry))<=16384,'GAME_RESPONSE_INVALID');
      tooltip(entry.tooltip);
    }
    const roles=new Set<string>();
    for(const control of value.controls) {
      fields(control,['control','title','enabled','tooltip']);
      requireThat((control.control==='back' || control.control==='submit') && !roles.has(control.control)
        && text(control.title,1024) && typeof control.enabled==='boolean' && Buffer.byteLength(canonical(control))<=16384,'GAME_RESPONSE_INVALID');
      roles.add(control.control);tooltip(control.tooltip);
    }
    const {schema,body_fingerprint,connection_generation,...publicValue}=value;
    requireThat(Buffer.byteLength(canonical(publicValue))<=32768,'GAME_RESPONSE_INVALID');
  } else if (operation === 'quest_components') {
    fields(value,['schema','body_fingerprint','connection_generation','query','source_generation','policy','revision','entries','next_cursor']);
    const text=(x:unknown,max:number):x is string=>typeof x==='string' && [...x].length<=max
      && !/[\uD800-\uDFFF]/u.test(x) && Buffer.byteLength(x)<=max*4;
    requireThat(value.schema==='strata/NativeQuestComponents/1' && hash(value.body_fingerprint) && uint(value.connection_generation)
      && canonical(value.query)===canonical(args) && uint(value.source_generation) && value.policy===QUEST_COMPONENTS_POLICY
      && uint(value.revision) && Array.isArray(value.entries) && value.entries.length<=32 && Number(args.after)+value.entries.length<=512
      && (value.next_cursor===null || uint(value.next_cursor) && value.next_cursor<=512 && value.entries.length>0
        && value.next_cursor===Number(args.after)+value.entries.length),'GAME_RESPONSE_INVALID');
    let previous='';
    for(const entry of value.entries) {
      fields(entry,['entry_id','kind','title','tooltip','task','reward']);
      requireThat(entry.kind===(args.part==='tasks' ? 'task' : 'reward') && typeof entry.entry_id==='string'
        && entry.entry_id.length===16 && /^[0-9A-F]{16}$/.test(entry.entry_id) && entry.entry_id>previous
        && text(entry.title,1024) && Array.isArray(entry.tooltip) && entry.tooltip.length<=64,'GAME_RESPONSE_INVALID');
      previous=entry.entry_id;
      for(const line of entry.tooltip) {
        fields(line,['kind','text']);requireThat(line.kind==='text' ? text(line.text,4096)
          : line.kind==='unsupported' && line.text===null,'GAME_RESPONSE_INVALID');
      }
      if(entry.kind==='task') {
        requireThat(entry.reward===null,'GAME_RESPONSE_INVALID');fields(entry.task,['completed','optional','progress_label']);
        requireThat(typeof entry.task.completed==='boolean' && typeof entry.task.optional==='boolean'
          && (entry.task.progress_label===null || text(entry.task.progress_label,256)),'GAME_RESPONSE_INVALID');
      } else {
        requireThat(entry.task===null,'GAME_RESPONSE_INVALID');fields(entry.reward,['claim_state','team_reward']);
        requireThat(['can_claim','cannot_claim','claimed'].includes(String(entry.reward.claim_state))
          && typeof entry.reward.team_reward==='boolean','GAME_RESPONSE_INVALID');
      }
      requireThat(Buffer.byteLength(canonical(entry))<=16384,'GAME_RESPONSE_INVALID');
    }
    requireThat(Buffer.byteLength(canonical({query:value.query,source_generation:value.source_generation,policy:value.policy,
      revision:value.revision,entries:value.entries,next_cursor:value.next_cursor}))<=32768,'GAME_RESPONSE_INVALID');
  } else if (operation === 'quest_text') {
    fields(value,['schema','body_fingerprint','connection_generation','query','source_generation','policy','revision',
      'title','subtitle','description_visible','lines','next_cursor']);
    const text=(x:unknown,max:number):x is string=>typeof x==='string' && [...x].length<=max
      && !/[\uD800-\uDFFF]/u.test(x) && Buffer.byteLength(x)<=max*4;
    requireThat(value.schema==='strata/NativeQuestText/1' && hash(value.body_fingerprint) && uint(value.connection_generation)
      && canonical(value.query)===canonical(args) && uint(value.source_generation) && value.policy===QUEST_TEXT_POLICY
      && uint(value.revision) && text(value.title,1024) && text(value.subtitle,1024) && typeof value.description_visible==='boolean'
      && Array.isArray(value.lines) && value.lines.length<=32 && Number(args.after)+value.lines.length<=512
      && (value.next_cursor===null || uint(value.next_cursor) && value.next_cursor<=512 && value.lines.length>0
        && value.next_cursor===Number(args.after)+value.lines.length)
      && (value.description_visible || value.lines.length===0 && value.next_cursor===null && args.after===0),'GAME_RESPONSE_INVALID');
    for(const line of value.lines) {
      fields(line,['kind','text']);requireThat(['text','page_break','unsupported'].includes(String(line.kind))
        && (line.kind==='text' ? text(line.text,4096) : line.text===null),'GAME_RESPONSE_INVALID');
    }
    requireThat(Buffer.byteLength(canonical({query:value.query,source_generation:value.source_generation,policy:value.policy,
      revision:value.revision,title:value.title,subtitle:value.subtitle,description_visible:value.description_visible,
      lines:value.lines,next_cursor:value.next_cursor}))<=32768,'GAME_RESPONSE_INVALID');
  } else if (operation === 'quests') {
    fields(value,['schema','body_fingerprint','connection_generation','query','source_generation','policy','revision','entries','next_cursor']);
    requireThat(value.schema==='strata/NativeQuestPage/1' && hash(value.body_fingerprint) && uint(value.connection_generation)
      && canonical(value.query)===canonical(args) && uint(value.source_generation) && value.policy===QUEST_POLICY
      && uint(value.revision) && Array.isArray(value.entries) && value.entries.length<=32
      && Number(args.after)+value.entries.length<=4096 && (value.next_cursor===null || uint(value.next_cursor)
      && value.next_cursor<=4096 && value.entries.length>0 && value.next_cursor===Number(args.after)+value.entries.length),'GAME_RESPONSE_INVALID');
    let previous='';
    for(const entry of value.entries) {
      fields(entry,['kind','entry_id','title','progress_percent','completed','startable','details_visible']);
      requireThat(entry.kind===(args.chapter_id===null ? 'chapter' : 'quest') && typeof entry.entry_id==='string' && entry.entry_id.length===16
        && /^[0-9A-F]{16}$/.test(entry.entry_id) && entry.entry_id>previous && typeof entry.title==='string'
        && [...entry.title].length<=1024 && !/[\uD800-\uDFFF]/u.test(entry.title) && Buffer.byteLength(entry.title)<=4096 && uint(entry.progress_percent)
        && entry.progress_percent<=100 && typeof entry.completed==='boolean' && (!entry.completed || entry.progress_percent===100)
        && (entry.kind==='chapter' ? entry.startable===null && entry.details_visible===null
          : typeof entry.startable==='boolean' && typeof entry.details_visible==='boolean' && (!entry.startable || entry.details_visible)), 'GAME_RESPONSE_INVALID');
      previous=entry.entry_id;
    }
    requireThat(Buffer.byteLength(canonical({query:value.query,source_generation:value.source_generation,policy:value.policy,
      revision:value.revision,entries:value.entries,next_cursor:value.next_cursor}))<=32768,'GAME_RESPONSE_INVALID');
  } else if (operation === 'identity') {
    fields(value, ['schema','body_fingerprint','connection_generation']);
    requireThat(value.schema === 'strata/NativeGameIdentity/1' && hash(value.body_fingerprint) && uint(value.connection_generation), 'GAME_RESPONSE_INVALID');
  } else if (operation === 'authority') {
    fields(value, ['schema','campaign_id','agent_id','capability_digest','body_fingerprint','expires_unix_ms','primitive_limit']);
    requireThat(value.schema === 'strata/NativeGameAuthority/1' && id(value.campaign_id) && id(value.agent_id)
      && hash(value.capability_digest) && hash(value.body_fingerprint) && uint(value.expires_unix_ms)
      && uint(value.primitive_limit) && value.primitive_limit >= 2, 'GAME_RESPONSE_INVALID');
  } else if (operation === 'observe') {
    fields(value, ['schema','snapshot_id','state_revision','source_clock_id','captured_elapsed_ms','age_ms','state']);
    requireThat(value.schema === 'strata/NativeGameSnapshot/1' && id(value.snapshot_id) && id(value.source_clock_id)
      && uint(value.state_revision) && uint(value.captured_elapsed_ms) && uint(value.age_ms), 'GAME_RESPONSE_INVALID');
    // Full state validation occurs in the public Observation envelope before delivery.
  } else if (operation === 'deliver') {
    requireThat(canonical(value) === canonical(args), 'GAME_RESPONSE_INVALID');
  } else if (['act','action_status','cancel'].includes(operation)) {
    fields(value, ['schema','request_id','epoch','action_seq','status','attempted_events','emitted_events','release_confirmed','error_code','requires_resync']);
    const batch = args.batch as ActionBatch | undefined;
    const terminal = !['accepted','executing'].includes(String(value.status));
    requireThat(value.schema === 'strata/NativeGameActionReceipt/1' && value.request_id === (batch?.request_id ?? args.request_id)
      && uint(value.epoch) && uint(value.action_seq) && (!batch || value.epoch === batch.epoch && value.action_seq === batch.seq)
      && ['accepted','executing','emitted','cancelled','unknown','failed'].includes(String(value.status))
      && uint(value.attempted_events) && (value.emitted_events === null || uint(value.emitted_events) && value.emitted_events <= value.attempted_events)
      && typeof value.release_confirmed === 'boolean' && code(value.error_code) && value.requires_resync === terminal
      && (terminal || value.release_confirmed === false && value.error_code === null)
      && (!['cancelled','unknown','failed'].includes(String(value.status)) || value.error_code !== null)
      && (value.status !== 'emitted' || value.release_confirmed && value.error_code === null && value.emitted_events === value.attempted_events), 'GAME_RESPONSE_INVALID');
  } else {
    fields(value, ['schema','fenced','fence_token','reason','journal_healthy','epoch','active_request_id','attempted_primitive_events','primitive_limit']);
    requireThat(value.schema === 'strata/NativeGameLane/1' && typeof value.fenced === 'boolean' && id(value.fence_token)
      && code(value.reason) && value.fenced === (value.reason !== null) && typeof value.journal_healthy === 'boolean'
      && (value.journal_healthy || value.fenced) && (value.epoch === null || uint(value.epoch))
      && (value.active_request_id === null || id(value.active_request_id))
      && uint(value.attempted_primitive_events) && uint(value.primitive_limit), 'GAME_RESPONSE_INVALID');
  }
  return value;
}

export class NativeGameClient {
  private inFlight = 0;
  constructor(readonly connection: NativeConnection) {
    fields(connection, ['schema','host','port','session_id','bearer_token','fingerprint','operator_development_only']);
    requireThat(connection.schema === 'strata/NativeGameConnection/1' && connection.host === '127.0.0.1'
      && uint(connection.port) && connection.port > 0 && connection.port < 65536 && id(connection.session_id)
      && hash(connection.bearer_token) && hash(connection.fingerprint) && connection.operator_development_only === true, 'GAME_CONNECTION_INVALID');
  }
  static fromFile(path: string): NativeGameClient {
    try {
      requireThat(statSync(path).size <= 4096, 'GAME_CONNECTION_INVALID');
      return new NativeGameClient(strictJson(readFileSync(path, 'utf8')) as NativeConnection);
    } catch {throw new Fault('GAME_CONNECTION_INVALID');}
  }
  async call<K extends NativeOperation>(operation: K, args: ObjectValue = {}, timeoutMs = 1500): Promise<NativeResults[K]> {
    requireThat([...READ,...LANE].includes(operation) && uint(timeoutMs) && timeoutMs >= 50 && timeoutMs <= 30000, 'GAME_ARGUMENTS_INVALID');
    if (operation === 'act') {fields(args, ['batch']); const b = validate<ActionBatch>('ActionBatch', args.batch);
      actionSemantics(b); requireThat((FORGE_ACTIONS as readonly string[]).includes(b.action!.kind), 'MECHANIC_UNSUPPORTED');}
    else if (operation === 'observe' || operation === 'observe_bound') {fields(args, ['cursor']); requireThat(args.cursor === null || id(args.cursor), 'GAME_ARGUMENTS_INVALID');}
    else if (operation === 'recipes') {fields(args, ['after']); requireThat(uint(args.after) && args.after <= 10000, 'GAME_ARGUMENTS_INVALID');}
    else if (operation === 'recipe_query') queryArgs(args);
    else if (operation === 'quests') questArgs(args);
    else if (operation === 'quest_text') questTextArgs(args);
    else if (operation === 'quest_components') questComponentsArgs(args);
    else if (operation === 'quest_menu') {
      fields(args,['source','after']);requireThat(args.source==='ftb_quests' && uint(args.after) && args.after<=512,'GAME_RESPONSE_INVALID');
    }
    else if (operation === 'arm' || operation === 'renew') {
      fields(args, ['epoch','lease_id','lease_until_unix_ms',...(operation === 'arm' ? ['expected_fence_token'] : [])]);
      requireThat(uint(args.epoch) && id(args.lease_id) && uint(args.lease_until_unix_ms)
        && (operation !== 'arm' || id(args.expected_fence_token)), 'GAME_ARGUMENTS_INVALID');
    } else if (operation === 'deliver') {fields(args, ['observation_id','snapshot_id','state_revision']);
      requireThat(id(args.observation_id) && id(args.snapshot_id) && uint(args.state_revision), 'GAME_ARGUMENTS_INVALID');}
    else if (operation === 'action_status' || operation === 'cancel') {fields(args, ['request_id']); requireThat(id(args.request_id), 'GAME_ARGUMENTS_INVALID');}
    else fields(args, []);
    requireThat(this.inFlight < 8, 'CAPACITY_EXCEEDED');
    const requestId = randomUUID(); const expires = mono() + timeoutMs;
    const body = canonical({schema:'strata/NativeGameRequest/1',request_id:requestId,
      session_id:this.connection.session_id, deadline_unix_ms:Date.now()+timeoutMs, operation,args});
    requireThat(Buffer.byteLength(body) <= 32768, 'CAPACITY_EXCEEDED');
    this.inFlight++;
    try {
      // Exactly one POST. Pending responses are queried only by their transport ID.
      let response = await this.exchange('POST', '/v1/game', body, expires);
      while (true) {
        fields(response, ['schema','request_id','session_id','status','result','error_code']);
        requireThat(response.schema === 'strata/NativeGameResponse/1' && response.request_id === requestId
          && response.session_id === this.connection.session_id, 'GAME_RESPONSE_INVALID');
        requireThat(['accepted','completed','failed'].includes(String(response.status)), 'GAME_RESPONSE_INVALID');
        if (response.status === 'failed') {
          requireThat(code(response.error_code) && response.error_code !== null && response.result === null, 'GAME_RESPONSE_INVALID');
          throw new Fault(response.error_code as string);
        }
        requireThat(response.error_code === null, 'GAME_RESPONSE_INVALID');
        if (response.status === 'completed') return result(operation, args, response.result) as NativeResults[K];
        requireThat(response.result === null && mono() < expires, 'DEADLINE_EXCEEDED');
        await delay(Math.min(10, expires - mono()));
        response = await this.exchange('GET', `/v1/game/${requestId}`, null, expires);
      }
    } catch (error) {
      if (MUTATIONS.has(operation)) throw new NativeOutcomeUnknown(requestId, operation, error);
      throw error instanceof Fault ? error : new Fault('GAME_OBSERVATION_UNAVAILABLE');
    } finally {this.inFlight--;}
  }
  private exchange(method: string, path: string, body: string | null, expires: number): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const remaining = expires - mono();
      if (remaining <= 0) {reject(new Fault('DEADLINE_EXCEEDED')); return;}
      const req = httpRequest({host:'127.0.0.1',port:this.connection.port,path,method,
        headers:{Authorization:`Bearer ${this.connection.bearer_token}`,'Content-Type':'application/json'}}, res => {
        if (![200,202].includes(res.statusCode ?? 0) || res.headers['content-type']?.split(';')[0] !== 'application/json') {
          res.destroy(); reject(new Fault('GAME_TRANSPORT_UNAVAILABLE')); return;
        }
        const chunks: Buffer[] = []; let size = 0;
        res.on('data', (chunk: Buffer) => {size += chunk.length;
          if (size > 524288) {res.destroy(); reject(new Fault('CAPACITY_EXCEEDED'));}
          else chunks.push(chunk);});
        res.on('end', () => {try {resolve(strictJson(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks))));} catch {reject(new Fault('GAME_RESPONSE_INVALID'));}});
        res.on('error', () => reject(new Fault('GAME_TRANSPORT_UNAVAILABLE')));
      });
      const timer = setTimeout(() => req.destroy(new Error('timeout')), remaining);
      req.on('error', () => reject(new Fault('GAME_TRANSPORT_UNAVAILABLE')));
      req.on('close', () => clearTimeout(timer));
      req.end(body ?? undefined);
    });
  }
}
