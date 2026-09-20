import mineflayer, { type Bot } from 'mineflayer';
import { Vec3 } from 'vec3';
import { setTimeout as delay } from 'node:timers/promises';
import type { Block } from 'prismarine-block';
import { EventEmitter } from 'node:events';
import { type Backend, type PrimitiveEmitter } from './actions.js';
import { Fault, mono, requireThat, type Action, type PublicSignal, type StructuredState } from './protocol.js';
import { SpatialPages, type Snapshot } from './pagination.js';
import { ObservedMap, id, slots, vector } from './observations.js';
import { plan } from './navigation.js';
import { RecipeBook } from './recipes.js';
import { craft } from './crafting.js';
import { equip, InventoryMotor } from './inventory_motor.js';
import { trackCursor } from './inventory_feedback.js';
import { closeMenu } from './menu_close.js';
import { chat, useItem } from './gestures.js';
import { ObservedEntities } from './entities.js';
import { workerAuthentication } from './authentication.js';
import { trackBodyRevision } from './body_revision.js';

export const ACTION_KINDS = ['move_to', 'look_at', 'dig', 'place', 'craft', 'equip', 'interact_block', 'click_slot',
  'use_item', 'attack', 'interact_entity', 'chat', 'close_window'] as const;
export class MineflayerBackend implements Backend {
  revision = 0;
  connected = false;
  connectionFailure: string | null = null;
  windowRevision = 0;
  private map: ObservedMap;
  private readonly pages = new SpatialPages();
  private readonly entities = new ObservedEntities();
  private activeEmit: PrimitiveEmitter | null = null;
  private moving = false;
  private itemHeld = false;
  private lastDigFinished = -Infinity;
  private readonly publicEvents = new EventEmitter();
  private readonly recipes: RecipeBook;
  readonly bot: Bot;
  private readonly authenticationAbort = new AbortController();
  private readonly bodyRevision: ReturnType<typeof trackBodyRevision>;
  constructor(options: {host: string; port: number; username: string; profilesFolder: string}) {
    this.bot = mineflayer.createBot({...options, version: '1.19.2',
      auth: workerAuthentication(options.profilesFolder, options.username, this.authenticationAbort.signal),
      hideErrors: true, logErrors: false});
    this.bodyRevision = trackBodyRevision(this.bot, () => {this.revision++;});
    this.map = new ObservedMap(p => this.bot.blockAt(p, false));
    this.recipes = new RecipeBook(item => this.bot.registry?.items[item]?.name,
      item => this.bot.registry?.items[item]?.maxDurability);
    this.bot._client.on('declare_recipes', packet => {
      try { this.recipes.declare(packet); } catch { this.disconnect(); }
    });
    this.bot._client.on('unlock_recipes', packet => {
      try { this.recipes.unlock(packet); this.revision++;
        this.publicEvents.emit('signal', 'inventory', 'Recipe book changed.');
      } catch { this.disconnect(); }
    });
    this.bot.on('spawn', () => {this.connected = true; this.revision++; this.map.reset(); this.pages.reset(); this.entities.reset();
      this.publicEvents.emit('signal', 'connection', 'Connected.');});
    this.bot.on('end', () => {this.authenticationAbort.abort(); this.connected = false;
      this.connectionFailure ??= 'CONNECTION_LOST'; this.revision++; this.pages.reset(); this.entities.reset();
      this.publicEvents.emit('signal', 'connection', 'Disconnected.');});
    this.bot.on('error', error => {
      this.connectionFailure ??= error instanceof Fault && /^[A-Z0-9_]{1,96}$/.test(error.code)
        ? error.code : 'CONNECTION_FAILED';
      this.connected = false; this.stop();
      this.publicEvents.emit('signal', 'connection', 'Connection failed.');
    });
    this.bot.on('physicsTick', () => {
      if (this.moving) {
        try { this.activeEmit?.(); } catch { this.stop(); this.disconnect(); }
      }
    });
    this.bot.on('health', () => {this.revision++;
      this.publicEvents.emit('signal', 'health', `Health ${this.bot.health}; food ${this.bot.food}.`);});
    this.bot.on('chat', (username, message) => {
      this.publicEvents.emit('signal', 'chat', `${username}: ${message}`);
    });
    this.bot.on('windowOpen', window => {
      this.windowRevision++; this.revision++;
      this.publicEvents.emit('signal', 'window', 'Container opened.');
      (window as unknown as EventEmitter).on('updateSlot', () => {this.windowRevision++; this.revision++;
        this.publicEvents.emit('signal', 'window', 'Open container changed.');});
    });
    this.bot.on('windowClose', () => {this.windowRevision++; this.revision++;
      this.publicEvents.emit('signal', 'window', 'Container closed.');});
    this.bot.once('inject_allowed', () => {
      const untrackCursor = trackCursor(this.bot, () => {
        this.windowRevision++; this.revision++;
        this.publicEvents.emit('signal', 'window', 'Carried item changed.');
      });
      this.bot.once('end', untrackCursor);
      this.bot.inventory.on('updateSlot', () => {this.windowRevision++; this.revision++;
        this.publicEvents.emit('signal', 'inventory', 'Inventory changed.');});
    });
  }
  subscribeSignals(listener: (kind: PublicSignal['kind'], summary: string) => void): () => void {
    this.publicEvents.on('signal', listener);
    return () => { this.publicEvents.off('signal', listener); };
  }
  recipeList(after: number): unknown { return this.recipes.list(after); }
  private eye(): Vec3 { return this.bot.entity.position.offset(0, 1.62, 0); }
  snapshot(cursor?: string): Snapshot {
    requireThat(this.connected, 'PRECONDITION_FAILED');
    const bot = this.bot;
    const dimension = id(String(bot.game.dimension));
    if (cursor) return this.pages.page(cursor, dimension);
    this.bodyRevision.sample();
    const captured = mono();
    const blocks = this.map.capture(this.eye(), dimension);
    const entities = Object.values(bot.entities).filter(e => e.id !== bot.entity.id &&
      this.map.visible(this.eye(), e.position.offset(0, Math.min(e.height / 2, 1), 0)))
      .sort((a,b) => a.position.distanceSquared(bot.entity.position)-b.position.distanceSquared(bot.entity.position));
    const window = bot.currentWindow ?? bot.inventory;
    const state: StructuredState = {dimension, position: vector(bot.entity.position), yaw: bot.entity.yaw, pitch: bot.entity.pitch,
      health: bot.health, food: bot.food, inventory: slots(bot.inventory.slots),
      window: window ? {id: window.id, revision: this.windowRevision, type: String(window.type), slots: slots(window.slots),
        cursor_item: window.selectedItem ? {item_id: id(window.selectedItem.name), count: window.selectedItem.count,
          component_summary: {}} : null} : null,
      nearby_blocks: [], nearby_entities: [],
      active_request_id: null, connected: true, truncated: false,
      next_cursor: null};
    return this.pages.capture({state, captured_mono_ms: captured, state_revision: this.revision,
      blocks: this.map.project(blocks), entities: entities.map(e => ({id: String(e.id),
        type: e.name ?? e.type, position: vector(e.position), observed_at: new Date().toISOString()})),
      promote: offset => {
        this.map.deliver(blocks.slice(offset, offset + 128), dimension);
        this.entities.deliver(entities.slice(offset, offset + 128), dimension, captured);
      }});
  }
  private target(point: {x: number; y: number; z: number}, expected: string): Block {
    const pos = new Vec3(point.x, point.y, point.z);
    requireThat([point.x,point.y,point.z].every(Number.isInteger), 'PRECONDITION_FAILED');
    const seen = this.map.blockAt(pos);
    requireThat(seen && id(seen.name) === expected, 'PRECONDITION_FAILED');
    requireThat(this.eye().distanceTo(pos.offset(.5,.5,.5)) <= 4.5 &&
      this.map.visible(this.eye(), pos.offset(.5,.5,.5)), 'PRECONDITION_FAILED');
    const block = this.bot.blockAt(pos, false);
    requireThat(block && id(block.name) === expected, 'PRECONDITION_FAILED');
    return block;
  }
  async execute(a: Action, signal: AbortSignal, emit: PrimitiveEmitter): Promise<void | 'emitted'> {
    const bot = this.bot;
    const guard = () => { signal.throwIfAborted(); requireThat(this.connected, 'PRECONDITION_FAILED'); };
    // Closing the socket is the conservative fallback for upstream async operations that have no cancellation API.
    const aborted = () => {this.stop(); this.disconnect();};
    guard(); signal.addEventListener('abort', aborted, {once: true});
    this.activeEmit = emit;
    try {
      switch (a.kind) {
        case 'use_item': return await useItem(bot, a, signal, guard, emit,
          off => { this.itemHeld = true; bot.activateItem(off); }, () => this.releaseItem());
        case 'chat': return chat(bot, a.text, guard, emit);
        case 'attack':
        case 'interact_entity': {
          const target = () => this.entities.target(a.entity_id, id(String(bot.game.dimension)),
            entityId => bot.entities[entityId], this.eye(), (eye, point) => this.map.visible(eye, point));
          const first = target();
          emit(); await bot.lookAt(first.position.offset(0, Math.min(first.height / 2, 1), 0)); guard();
          const current = target();
          requireThat(current !== bot.entity && current === first, 'PRECONDITION_FAILED');
          if (a.kind === 'attack') {
            // The pinned attack method emits an attack plus its ordinary arm swing.
            emit(); emit(); bot.attack(current);
          } else { emit(); bot.useOn(current); }
          return 'emitted';
        }
        case 'look_at': {
          const p = new Vec3(a.target.x,a.target.y,a.target.z);
          requireThat(this.eye().distanceTo(p) <= 16, 'PRECONDITION_FAILED');
          emit(); await bot.lookAt(p); guard(); break;
        }
        case 'move_to': {
          const target = new Vec3(a.target.x,a.target.y,a.target.z);
          const route = plan(bot, this.map, target, a.tolerance);
          this.moving = true;
          for (const p of route) {
            while (bot.entity.position.distanceTo(p) > .25) {
              guard();
              const feet = this.map.blockAt(p);
              const head = this.map.blockAt(p.offset(0,1,0));
              const floor = this.map.blockAt(p.offset(0,-1,0));
              requireThat(feet?.boundingBox === 'empty' && head?.boundingBox === 'empty' &&
                floor?.boundingBox === 'block', 'PATH_BLOCKED');
              await bot.lookAt(p.offset(0,1.62,0)); guard();
              bot.setControlState('forward', true);
              await delay(50, undefined, {signal});
            }
          }
          requireThat(bot.entity.position.distanceTo(target) <= a.tolerance, 'PATH_BLOCKED');
          break;
        }
        case 'dig': {
          const block = this.target(a.target, a.expected_block_id);
          requireThat(bot.canDigBlock(block), 'PRECONDITION_FAILED');
          await bot.lookAt(block.position.offset(.5,.5,.5)); guard();
          // 'ignore' removes the upstream pre-dig await; abort always closes its socket.
          const current = this.target(a.target, a.expected_block_id);
          requireThat(bot.canDigBlock(current), 'PRECONDITION_FAILED');
          emit(); await bot.dig(current, 'ignore'); this.lastDigFinished = performance.now(); guard();
          const after = bot.blockAt(block.position, false);
          requireThat(after && id(after.name) !== a.expected_block_id, 'PRECONDITION_FAILED'); break;
        }
        case 'place': {
          const supportPosition = new Vec3(a.support.x,a.support.y,a.support.z);
          const seen = this.map.blockAt(supportPosition);
          requireThat(seen, 'PRECONDITION_FAILED');
          const expectedSupport = id(seen.name);
          let block = this.target(a.support, expectedSupport);
          const face = new Vec3(a.face.x,a.face.y,a.face.z);
          const destination = block.position.plus(face);
          const checkDestination = () => {
            const visible = this.map.blockAt(destination);
            const current = bot.blockAt(destination, false);
            requireThat(visible && ['air','cave_air','void_air'].includes(visible.name) &&
              current && ['air','cave_air','void_air'].includes(current.name), 'PRECONDITION_FAILED');
            requireThat(bot.heldItem && id(bot.heldItem.name) === a.expected_item_id &&
              bot.registry.blocksByName[bot.heldItem.name], 'MECHANIC_UNSUPPORTED');
          };
          checkDestination();
          await bot.lookAt(block.position.offset(.5+face.x*.5,.5+face.y*.5,.5+face.z*.5)); guard();
          block = this.target(a.support, expectedSupport); checkDestination();
          const placer = bot as Bot & {_placeBlockWithOptions?: (block: Block, face: Vec3,
            options: {forceLook: 'ignore'; swingArm: 'right'}) => Promise<void>};
          requireThat(typeof placer._placeBlockWithOptions === 'function', 'MECHANIC_UNSUPPORTED');
          emit(); await placer._placeBlockWithOptions(block,face,{forceLook:'ignore',swingArm:'right'}); guard();
          const placed = bot.blockAt(destination,false);
          requireThat(placed && id(placed.name) === a.expected_item_id, 'PRECONDITION_FAILED');
          break;
        }
        case 'craft': {
          requireThat(a.recipe_selection == null, 'CAPABILITY_MISSING');
          requireThat(performance.now() - this.lastDigFinished >= 500, 'PRECONDITION_FAILED');
          await craft(bot,this.recipes,a,this.windowRevision,guard,emit); guard(); break;
        }
        case 'equip': {
          requireThat(performance.now() - this.lastDigFinished >= 500, 'PRECONDITION_FAILED');
          await equip(bot, a, guard, emit); break;
        }
        case 'interact_block': {
          const block = this.target(a.target, a.expected_block_id);
          requireThat(['chest','barrel','furnace','crafting_table'].includes(block.name), 'MECHANIC_UNSUPPORTED');
          await bot.lookAt(block.position.offset(.5,.5,.5)); guard();
          const current = this.target(a.target, a.expected_block_id);
          emit(); await bot.openBlock(current); guard();
          const expected = current.name === 'furnace' ? 'minecraft:furnace' :
            current.name === 'crafting_table' ? 'minecraft:crafting' : 'minecraft:generic';
          requireThat(bot.currentWindow && String(bot.currentWindow.type).startsWith(expected), 'PRECONDITION_FAILED'); break;
        }
        case 'click_slot': {
          const window = bot.currentWindow ?? bot.inventory;
          requireThat(window && window.id === a.window_id && this.windowRevision === a.expected_window_revision, 'REVISION_CONFLICT');
          // Avoid the pinned clickWindow pre-dispatch dig cooldown await changing our CAS window.
          requireThat(performance.now() - this.lastDigFinished >= 500, 'PRECONDITION_FAILED');
          await new InventoryMotor(bot, guard, emit).click(a.slot, a.button, a.mode); break;
        }
        case 'close_window': {
          const window = bot.currentWindow ?? bot.inventory;
          requireThat(window.id === a.window_id && this.windowRevision === a.expected_window_revision, 'REVISION_CONFLICT');
          return await closeMenu(bot, signal, guard, emit);
        }
        default: throw new Fault('MECHANIC_UNSUPPORTED');
      }
    } finally {
      signal.removeEventListener('abort', aborted); this.stop(); this.activeEmit = null; this.moving = false;
    }
  }
  stop(): void {
    this.moving = false;
    this.bot.clearControlStates?.(); this.bot.stopDigging?.();
    this.releaseItem();
  }
  private releaseItem(): void {
    if (this.connected && (this.itemHeld || this.bot.usingHeldItem)) {
      // If evidence cannot be retained, close the connection instead of leaving
      // held input active or sending an unjournaled follow-up action.
      try { this.activeEmit?.('safety_release'); } catch { this.disconnect(); return; }
      this.itemHeld = false;
      this.bot.deactivateItem();
    }
  }
  disconnect(): void { this.authenticationAbort.abort(); this.connected = false; this.itemHeld = false; this.bot.end('Strata control fence'); }
}
