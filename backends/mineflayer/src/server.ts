import { createServer, type Server } from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import type { Scope } from './actions.js';
import type { Journal } from './journal.js';
import type { DiscoveryQuery as RecipeQuery, QuestQuery, QuestTextQuery, QuestComponentsQuery, QuestMenuQuery } from './native_game.js';
import { errorBody, Fault, requireThat, validate, type RpcRequest, type Observation, type ActionAck } from './protocol.js';

/** Both implementations retain the same actor-scoped, allowlisted public surface. */
export interface GameLane {
  readonly scope: Scope; readonly journal: Journal; readonly backend: {recipeList?(after: number): unknown; recipeQuery?(query: RecipeQuery): unknown; recipePage?():unknown;questList?(query:QuestQuery):unknown;questText?(query:QuestTextQuery):unknown;questComponents?(query:QuestComponentsQuery):unknown;questMenu?(query:QuestMenuQuery):unknown;questScreen?():unknown};
  observe(): Observation | Promise<Observation>;
  observePage(cursor: string): Promise<Observation>;
  waitEvents(after: number, durationMs: number): Promise<Observation>;
  act(raw: unknown): ActionAck;
  cancel(id: string): Promise<ActionAck>;
  stopAll(): Promise<void>;
  fence(code: string): Promise<void>;
  close(): Promise<void>;
  renewLease(): void | Promise<void>;
  health(): {connected: boolean; connected_once: boolean; fenced: boolean; reason: string | null};
}
export function serve(lane: GameLane, token: string, capabilities: unknown): Promise<Server> {
  const bearer = Buffer.from(`Bearer ${token}`);
  const server = createServer(async (req, res) => {
    let requestId: string | null = null;
    const send = (status: number, body: unknown) => {
      res.writeHead(status, {'Content-Type': 'application/json', 'Cache-Control': 'no-store'});
      res.end(JSON.stringify(body));
    };
    try {
      const provided = Buffer.from(req.headers.authorization ?? '');
      requireThat(provided.length === bearer.length && timingSafeEqual(provided, bearer), 'FORBIDDEN');
      requireThat(req.method === 'POST' && req.url === '/v1/game' && !req.headers.origin, 'FORBIDDEN');
      requireThat(req.headers['content-type'] === 'application/json', 'SCHEMA_UNSUPPORTED');
      let size = 0; const chunks: Buffer[] = [];
      for await (const chunk of req) {
        size += chunk.length;
        requireThat(size <= 65536, 'CAPACITY_EXCEEDED'); chunks.push(Buffer.from(chunk));
      }
      let parsed: unknown;
      try { parsed = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch {throw new Fault('SCHEMA_UNSUPPORTED');}
      const r = validate<RpcRequest>('RpcRequest', parsed); requestId = r.request_id;
      requireThat(r.campaign_id === lane.scope.campaign_id && r.agent_id === lane.scope.agent_id, 'FORBIDDEN');
      requireThat(r.epoch === lane.scope.epoch, 'STALE_EPOCH');
      const remaining = Date.parse(r.deadline_at) - Date.now();
      requireThat(remaining > 0 && remaining <= 5250, 'DEADLINE_EXCEEDED');
      requireThat((r.method === 'act') === (r.action !== null), 'SCHEMA_UNSUPPORTED');
      requireThat(['action_status','cancel'].includes(r.method) === (r.target_request_id !== null), 'SCHEMA_UNSUPPORTED');
      requireThat(['wait_events','recipes.list'].includes(r.method) === (r.after !== null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'observe.page') === (r.cursor != null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'recipes.query') === (r.recipe_query != null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'quests.list') === (r.quest_query != null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'quests.text') === (r.quest_text_query != null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'quests.components') === (r.quest_components_query != null), 'SCHEMA_UNSUPPORTED');
      requireThat((r.method === 'quests.menu') === (r.quest_menu_query != null), 'SCHEMA_UNSUPPORTED');
      let result: unknown;
      if (r.method.startsWith('controls.')) throw new Fault('CAPABILITY_MISSING');
      switch (r.method) {
        case 'capabilities': result = capabilities; break;
        case 'observe': result = await lane.observe(); break;
        case 'observe.page': result = await lane.observePage(r.cursor!); break;
        case 'recipes.list':
          requireThat(lane.backend.recipeList, 'CAPABILITY_MISSING');
          result = await lane.backend.recipeList(r.after!); break;
        case 'recipes.query':
          requireThat(lane.backend.recipeQuery, 'CAPABILITY_MISSING');
          result = await lane.backend.recipeQuery(r.recipe_query!); break;
        case 'quests.components':
          requireThat(lane.backend.questComponents,'CAPABILITY_MISSING');result=await lane.backend.questComponents(r.quest_components_query!);break;
        case 'quests.menu':
          requireThat(lane.backend.questMenu,'CAPABILITY_MISSING');result=await lane.backend.questMenu(r.quest_menu_query!);break;
        case 'quests.screen':
          requireThat(lane.backend.questScreen,'CAPABILITY_MISSING');result=await lane.backend.questScreen();break;
        case 'recipes.page':
          requireThat(lane.backend.recipePage,'CAPABILITY_MISSING');result=await lane.backend.recipePage();break;
        case 'quests.text':
          requireThat(lane.backend.questText,'CAPABILITY_MISSING');result=await lane.backend.questText(r.quest_text_query!);break;
        case 'quests.list':
          requireThat(lane.backend.questList,'CAPABILITY_MISSING');result=await lane.backend.questList(r.quest_query!);break;
        case 'act': result = lane.act(r.action); break;
        case 'action_status': result = lane.journal.status(r.target_request_id!); break;
        case 'cancel': result = await lane.cancel(r.target_request_id!); break;
        case 'stop_all': await lane.stopAll(); result = {status: 'stopped'}; break;
        case 'wait_events':
          result = await lane.waitEvents(r.after!, Math.min(3000, remaining)); break;
        default: throw new Fault('CAPABILITY_MISSING');
      }
      send(200, {schema: 'strata/GameResponse/1', status: 'ok', request_id: r.request_id, result});
    } catch (e) {
      send(e instanceof Fault && e.code === 'FORBIDDEN' ? 403 : 400,
        {schema: 'strata/GameResponse/1', status: 'error', error: errorBody(e, requestId, lane.scope.epoch)});
    }
  });
  server.requestTimeout = 1000; server.headersTimeout = 1000; server.timeout = 5500;
  server.maxConnections = 8;
  return new Promise((resolve, reject) => {server.once('error', reject); server.listen(0, '127.0.0.1', () => resolve(server));});
}
