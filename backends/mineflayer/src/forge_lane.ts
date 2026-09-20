import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import type { Scope } from './actions.js';
import { RELEASE_TIMEOUT_MS } from './actions.js';
import { Journal } from './journal.js';
import { Signals } from './signals.js';
import type { GameLane } from './server.js';
import type { DiscoveryQuery as RecipeQuery, QuestQuery, QuestTextQuery, QuestComponentsQuery, QuestMenuQuery } from './native_game.js';
import { FORGE_ACTIONS, NativeGameClient, nativeCapabilities, nativeFailureCode, type NativeLane, type NativeReceipt } from './native_game.js';
import { actionSemantics, canonical, digest, Fault, mono, requireThat, utc, validate,
  type ActionBatch, type ActionAck, type Observation } from './protocol.js';

interface Active {
  batch: ActionBatch; timer: NodeJS.Timeout; sent: boolean; nativeTerminal: boolean;
  finishing: Promise<void> | null; interrupt: string | null;
}
/** Development D06 executor. Native intent owns physical dispatch; this broker owns public authority. */
export class ForgeLane implements GameLane {
  readonly backend = {recipeList:(after:number) => this.recipeList(after), recipeQuery:(query:RecipeQuery) => this.recipeQuery(query),
    questList:(query:QuestQuery)=>this.questList(query),questText:(query:QuestTextQuery)=>this.questText(query),questComponents:(query:QuestComponentsQuery)=>this.questComponents(query),questMenu:(query:QuestMenuQuery)=>this.questMenu(query),questScreen:()=>this.questScreen(),recipePage:()=>this.recipePage()};
  readonly signals: Signals;
  private connected = true;
  private fenced = false;
  private reason: string | null = null;
  private evidenceFailed = false;
  private active: Active | null = null;
  private generation = -1;
  private revision = -1;
  private clockId: string | null = null;
  private captures = new Map<string, number>();
  private observations = new Map<string, Observation>();
  private last: Observation | null = null;
  private lastDelivery = -Infinity;
  private observationTail = Promise.resolve();
  private observationQueue = 0;
  private observing = false;
  private deadline: number;
  private leaseUntil = mono() + 6000;
  private watchdog: NodeJS.Timeout | undefined;
  private renewTask: Promise<void> | null = null;
  private fenceTask: Promise<void> | null = null;
  private releaseTask: Promise<boolean> | null = null;
  private lastRelease = false;
  private closed = false;
  private closeTask: Promise<void> | null = null;
  private usageKey = '';
  private constructor(readonly scope: Scope, readonly capabilityDigest: string,
    private client: NativeGameClient, readonly journal: Journal, private body: string,
    private primitiveLimit: number, maxWallMs: number) {
    this.deadline = mono() + maxWallMs; this.signals = new Signals(journal);
  }
  static async connect(scope: Scope, capabilityDigest: string, client: NativeGameClient,
    journal: Journal, body: string, primitiveLimit: number, maxWallMs: number, guardedGeneration?: number): Promise<ForgeLane> {
    const lane = new ForgeLane(scope, capabilityDigest, client, journal, body, primitiveLimit, maxWallMs);
    let armAttempted = false;
    try {
      const caps = await client.call('capabilities');
      requireThat(canonical(caps) === canonical(nativeCapabilities(true)), 'CAPABILITY_MISSING');
      const authority = await client.call('authority');
      requireThat(authority.campaign_id === scope.campaign_id && authority.agent_id === scope.agent_id
        && authority.capability_digest === capabilityDigest && authority.body_fingerprint === body,
        'FORBIDDEN');
      requireThat(authority.primitive_limit === primitiveLimit && authority.expires_unix_ms >= Date.now() + maxWallMs, 'BUDGET_EXHAUSTED');
      lane.usageKey = `native:${client.connection.fingerprint}:${digest(authority)}`;
      const identity = await client.call('identity');
      requireThat(identity.body_fingerprint === body, 'GAME_BODY_MISMATCH'); lane.generation = identity.connection_generation;
      requireThat(guardedGeneration === undefined || identity.connection_generation === guardedGeneration,
        'PROCESS_GUARD_BINDING_MISMATCH');
      const health = await client.call('lane_status');
      requireThat(health.fenced && health.journal_healthy && health.active_request_id === null
        && (health.epoch === null || scope.epoch > health.epoch), 'STALE_EPOCH');
      lane.write(() => {journal.recover(); journal.event('native_binding', {
        fingerprint:client.connection.fingerprint, authority, identity, epoch:scope.epoch});});
      lane.charge(health);
      armAttempted = true;
      const armed = await client.call('arm', {...lane.lease(),expected_fence_token:health.fence_token});
      lane.checkHealth(armed); lane.charge(armed);
      lane.watchdog = setInterval(() => {
        if (!lane.fenced && (mono() >= lane.deadline || mono() >= lane.leaseUntil)) lane.background(lane.fence('LEASE_EXPIRED'));
      }, 25);
      return lane;
    } catch (error) {
      if (armAttempted) await lane.releaseNative();
      lane.signals.close(); throw error;
    }
  }
  private lease() {return {epoch:this.scope.epoch,lease_id:this.scope.lease_id,lease_until_unix_ms:Date.now()+6000};}
  private write<T>(fn: () => T): T {
    try {return fn();} catch {
      this.evidenceFailed = true; this.markFenced('EVIDENCE_UNAVAILABLE'); throw new Fault('EVIDENCE_UNAVAILABLE');
    }
  }
  private charge(health: NativeLane): void {
    requireThat(health.primitive_limit === this.primitiveLimit, 'CAPABILITY_MISSING');
    this.write(() => this.journal.transaction(() => {
      const before = this.journal.counter(this.usageKey);
      // Concurrent status replies can arrive out of order. Never refund the high-water mark.
      const delta = Math.max(0, health.attempted_primitive_events - before);
      if (delta) {this.journal.counter(this.usageKey, delta); this.journal.counter('primitive_events', delta);}
      this.journal.event('native_usage', {epoch:this.scope.epoch,source:this.usageKey,
        attempted_primitive_events:health.attempted_primitive_events,charged_delta:delta});
    }));
  }
  private checkHealth(value: NativeLane): void {
    requireThat(value.journal_healthy && !value.fenced && value.epoch === this.scope.epoch, 'LEASE_EXPIRED');
  }
  health() {return {connected:this.connected,connected_once:true,fenced:this.fenced,reason:this.reason};}
  private async recipeList(after:number) {
    requireThat(!this.closed && this.connected && !this.fenced && mono() < this.deadline && mono() < this.leaseUntil, 'LEASE_EXPIRED');
    const result = await this.client.call('recipes', {after});
    requireThat(!this.closed && !this.fenced && mono() < this.deadline && mono() < this.leaseUntil, 'LEASE_EXPIRED');
    if (result.body_fingerprint !== this.body || result.connection_generation !== this.generation) {
      await this.fence('GAME_BODY_MISMATCH'); throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(() => this.journal.event('native_recipe_projection', {after,result}));
    return {revision:result.revision,recipes:result.recipes,next_cursor:result.next_cursor};
  }
  private async recipeQuery(query:RecipeQuery) {
    requireThat(!this.closed && this.connected && !this.fenced && mono() < this.deadline && mono() < this.leaseUntil, 'LEASE_EXPIRED');
    const result = await this.client.call('recipe_query', {...query});
    requireThat(!this.closed && !this.fenced && mono() < this.deadline && mono() < this.leaseUntil, 'LEASE_EXPIRED');
    if (result.body_fingerprint !== this.body || result.connection_generation !== this.generation) {
      await this.fence('GAME_BODY_MISMATCH'); throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(() => this.journal.event('native_recipe_query', {query,result}));
    return {query:result.query,source_generation:result.source_generation,policy:result.policy,
      revision:result.revision,recipes:result.recipes,next_cursor:result.next_cursor};
  }
  private async questComponents(query:QuestComponentsQuery) {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('quest_components',{...query});
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_quest_components',{query,result}));
    return {query:result.query,source_generation:result.source_generation,policy:result.policy,revision:result.revision,
      entries:result.entries,next_cursor:result.next_cursor};
  }
  private async questMenu(query:QuestMenuQuery) {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('quest_menu',{...query});
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_quest_menu',{query,result}));
    return {query:result.query,source_generation:result.source_generation,menu_generation:result.menu_generation,policy:result.policy,
      revision:result.revision,menu_kind:result.menu_kind,context:result.context,controls:result.controls,entries:result.entries,next_cursor:result.next_cursor};
  }
  private async questScreen() {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('quest_screen');
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_quest_screen',{result}));
    return {policy:result.policy,source_generation:result.source_generation,screen_generation:result.screen_generation,
      revision:result.revision,kind:result.kind,chapter_id:result.chapter_id,quest_id:result.quest_id};
  }
  private async recipePage() {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('recipe_page');
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_recipe_page',{result}));
    const {schema,body_fingerprint,connection_generation,...page}=result;return page;
  }
  private async questText(query:QuestTextQuery) {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('quest_text',{...query});
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_quest_text',{query,result}));
    return {query:result.query,source_generation:result.source_generation,policy:result.policy,revision:result.revision,
      title:result.title,subtitle:result.subtitle,description_visible:result.description_visible,lines:result.lines,next_cursor:result.next_cursor};
  }
  private async questList(query:QuestQuery) {
    requireThat(!this.closed && this.connected && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    const result=await this.client.call('quests',{...query});
    requireThat(!this.closed && !this.fenced && mono()<this.deadline && mono()<this.leaseUntil,'LEASE_EXPIRED');
    if(result.body_fingerprint!==this.body || result.connection_generation!==this.generation) {
      await this.fence('GAME_BODY_MISMATCH');throw new Fault('GAME_BODY_MISMATCH');
    }
    this.write(()=>this.journal.event('native_quest_catalog',{query,result}));
    return {query:result.query,source_generation:result.source_generation,policy:result.policy,
      revision:result.revision,entries:result.entries,next_cursor:result.next_cursor};
  }
  renewLease(): Promise<void> {
    if (this.fenced || this.closed) return Promise.resolve();
    if (this.renewTask) return this.renewTask;
    this.renewTask = (async () => {
      try {
        const health = await this.client.call('renew', this.lease(), 500);
        this.checkHealth(health); this.charge(health);
        if (!this.fenced) this.leaseUntil = mono() + 5500;
      } catch {await this.fence('LEASE_EXPIRED');}
      finally {this.renewTask = null;}
    })();
    return this.renewTask;
  }
  observe(force = false, cursor?: string): Promise<Observation> {
    requireThat(!this.closed && this.observationQueue < 8, 'CAPACITY_EXCEEDED');
    this.observationQueue++; const prior = this.observationTail; const until = mono()+2000;
    let release!: () => void;
    this.observationTail = new Promise<void>(resolve => {release = resolve;});
    return (async () => {
      try {
        await prior; requireThat(mono() < until, 'DEADLINE_EXCEEDED');
        requireThat(!this.closed && (this.connected || !cursor), 'PRECONDITION_FAILED');
        if (cursor) {const wait = 500-(mono()-this.lastDelivery); if (wait > 0) await delay(wait);}
        this.observing = true; return await this.capture(force, cursor);
      } catch (error) {
        if (!(error instanceof Fault && ['STALE_OBSERVATION','DEADLINE_EXCEEDED','PRECONDITION_FAILED'].includes(error.code))) {
          this.background(this.fence('GAME_OBSERVATION_UNAVAILABLE'));
        }
        throw error;
      } finally {this.observing = false; this.observationQueue--; release();}
    })();
  }
  private async capture(force: boolean, cursor?: string): Promise<Observation> {
    const now = mono();
    if (!cursor && this.last && (!this.connected || !force && now-this.lastDelivery < 500)) {
      const old = this.last;
      const aged = {...old,gateway_sent_mono_ms:now,age_at_send_ms:now-old.captured_mono_ms,
        state:{...old.state!,connected:this.connected},...this.signals.read(0)};
      this.validateObservation(aged);
      this.write(() => this.journal.event('observation_delivery', aged)); return aged;
    }
    requireThat(this.connected, 'PRECONDITION_FAILED');
    const mayAuthorize = !this.fenced && (!this.active || this.active.nativeTerminal);
    const start = mono();
    const bound = await this.client.call('observe_bound', {cursor:cursor ?? null}, 500);
    if (bound.body_fingerprint !== this.body || bound.connection_generation !== this.generation) {
      this.background(this.fence('CONNECTION_CHANGED')); throw new Fault('GAME_BODY_MISMATCH');
    }
    const snapshot = bound.snapshot;
    if (this.clockId && this.clockId !== snapshot.source_clock_id) {
      this.background(this.fence('CONNECTION_CHANGED')); throw new Fault('GAME_CLOCK_CHANGED');
    }
    this.clockId = snapshot.source_clock_id;
    const key = `${snapshot.source_clock_id}:${snapshot.captured_elapsed_ms}:${snapshot.state_revision}`;
    // The native reply was produced between request start and receipt. Subtracting
    // native age from request start is a conservative lower bound, never a fresh stamp.
    const captured = this.captures.get(key) ?? start-snapshot.age_ms;
    requireThat(captured >= 0 && captured <= mono(), 'STALE_OBSERVATION');
    this.captures.set(key, captured);
    if (this.captures.size > 8) this.captures.delete(this.captures.keys().next().value!);
    const observation: Observation = {
      schema:'mcbench/Observation/1',is_example:false,campaign_id:this.scope.campaign_id,agent_id:this.scope.agent_id,
      epoch:this.scope.epoch,seq:this.write(() => this.journal.next('observation')),recorded_at:utc(),observation_id:randomUUID(),
      mode:'structured',captured_mono_ms:captured,gateway_sent_mono_ms:mono(),age_at_send_ms:0,
      state_revision:snapshot.state_revision,capability_digest:this.capabilityDigest,state:snapshot.state,
      ...this.signals.read(0),frame:null,width:null,height:null,media_type:null,control_revision:this.scope.epoch,
      keymap_digest:null,pointer_locked:null,held_keys:[],last_action_seq:this.journal.counter(`${this.scope.epoch}:action`) || null,
    };
    observation.age_at_send_ms = observation.gateway_sent_mono_ms-captured;
    this.validateObservation(observation);
    requireThat(observation.state!.connected, 'GAME_RESPONSE_INVALID');
    this.write(() => this.journal.event('native_observation_projection', {snapshot,request_started_mono_ms:start,
      response_received_mono_ms:observation.gateway_sent_mono_ms,public_observation:observation}));
    if (mayAuthorize && !this.fenced && mono()-captured <= 2000) {
      await this.client.call('deliver', {observation_id:observation.observation_id,snapshot_id:snapshot.snapshot_id,
        state_revision:snapshot.state_revision}, 250);
    }
    observation.gateway_sent_mono_ms = mono(); observation.age_at_send_ms = observation.gateway_sent_mono_ms-captured;
    this.write(() => this.journal.event('observation_delivery', observation));
    if (mayAuthorize && !this.fenced && observation.age_at_send_ms <= 2000) {
      this.observations.set(observation.observation_id, observation);
      if (this.observations.size > 16) this.observations.delete(this.observations.keys().next().value!);
    }
    if (!cursor) {this.last = observation; this.revision = snapshot.state_revision;}
    this.lastDelivery = observation.gateway_sent_mono_ms; return observation;
  }
  private validateObservation(value: Observation): void {
    validate('Observation', value);
    requireThat(value.state!.truncated === (value.state!.next_cursor !== null)
      && Buffer.byteLength(JSON.stringify(value)) <= 65536, 'GAME_RESPONSE_INVALID');
  }
  observePage(cursor: string) {return this.observe(false, cursor);}
  async waitEvents(after: number, durationMs: number): Promise<Observation> {
    const before = this.last ?? await this.observe();
    const changed = await this.signals.wait(after, durationMs);
    const value = changed ? await this.observe() : before;
    const sent = mono(); const result = {...value,gateway_sent_mono_ms:sent,age_at_send_ms:sent-value.captured_mono_ms,
      state:{...value.state!,connected:this.connected},...this.signals.read(after)};
    this.validateObservation(result); this.write(() => this.journal.event('observation_delivery', result)); return result;
  }
  private ack(batch: ActionBatch, status: ActionAck['status'], extra: Partial<ActionAck> = {}): ActionAck {
    return {schema:'mcbench/ActionAck/1',is_example:false,campaign_id:this.scope.campaign_id,agent_id:this.scope.agent_id,
      epoch:this.scope.epoch,seq:this.journal.next('ack'),recorded_at:utc(),request_id:batch.request_id,action_seq:batch.seq,
      status,emitted_events:0,completed_mono_ms:null,release_confirmed:false,error_code:null,requires_resync:false,
      result_observation_id:null,...extra};
  }
  act(raw: unknown): ActionAck {
    const b = validate<ActionBatch>('ActionBatch', raw); actionSemantics(b);
    requireThat(b.campaign_id === this.scope.campaign_id && b.agent_id === this.scope.agent_id, 'FORBIDDEN');
    const previous = this.journal.previous(b); if (previous) return previous;
    requireThat(b.epoch === this.scope.epoch, 'STALE_EPOCH');
    requireThat(!this.fenced && !this.closed && mono() < this.leaseUntil && b.lease_id === this.scope.lease_id, 'LEASE_EXPIRED');
    requireThat(!this.active && !this.observing, 'ACTION_IN_PROGRESS');
    requireThat(b.capability_digest === this.capabilityDigest && b.control_revision === this.scope.epoch, 'CAPABILITY_MISSING');
    requireThat((FORGE_ACTIONS as readonly string[]).includes(b.action!.kind), 'MECHANIC_UNSUPPORTED');
    const observation = this.observations.get(b.observation_id);
    requireThat(observation && mono()-observation.captured_mono_ms <= 2000, 'STALE_OBSERVATION');
    requireThat(b.expected_state_revision === observation.state_revision && b.expected_state_revision === this.revision, 'REVISION_CONFLICT');
    const minimum = b.action!.kind === 'recipe_navigate' ? (b.action!.control === 'history_back' ? 3 : 4)
      : ['dig','interact_block','attack','interact_entity','place','equip','click_slot','craft','close_window'].includes(b.action!.kind) ? 3 : 2;
    requireThat(this.journal.counter('primitive_events')+minimum <= this.primitiveLimit, 'BUDGET_EXHAUSTED');
    const remaining = Date.parse(b.deadline_at)-Date.now();
    requireThat(remaining > 0 && remaining <= 30250 && mono() < this.deadline, 'DEADLINE_EXCEEDED');
    const ack = this.write(() => {const ack = this.ack(b, 'accepted'); this.journal.accept(b, ack); return ack;});
    const timer = setTimeout(() => this.background(this.fence('DEADLINE_EXCEEDED')),
      Math.min(remaining,b.duration_ms,this.deadline-mono()));
    const active: Active = {batch:b,timer,sent:false,nativeTerminal:false,finishing:null,interrupt:null};
    this.active = active; this.lastRelease = false;
    setImmediate(() => this.background(this.run(active))); return ack;
  }
  private async run(active: Active): Promise<void> {
    if (this.fenced || this.active !== active) return;
    let operation: 'act' | 'action_status' = 'act';
    try {
      this.write(() => this.journal.update(this.ack(active.batch,'executing')));
      active.sent = true;
      let receipt = await this.client.call('act', {batch:active.batch}, 500);
      while (!receipt.requires_resync && !this.fenced && !active.finishing) {
        await delay(25); operation = 'action_status';
        receipt = await this.client.call('action_status', {request_id:active.batch.request_id}, 500);
      }
      if (this.fenced || active.finishing || this.active !== active) return;
      active.nativeTerminal = true; clearTimeout(active.timer);
      active.finishing = Promise.resolve().then(() => this.complete(active, receipt));
      await active.finishing;
    } catch (error) {
      if (!active.finishing && this.active === active) {
        // Release/fence before optional private diagnostics. Never weaken uncertainty
        // or retry a mutation because its transport returned a classified error.
        try {await this.fence('ACTION_UNKNOWN');}
        finally {
          const code = nativeFailureCode(error);
          this.write(() => this.journal.event('native_action_call_failed', {
            policy:'native-call-failure-after-fence/1',at:utc(),mono_ms:mono(),
            epoch:this.scope.epoch,request_id:active.batch.request_id,action_seq:active.batch.seq,
            operation,code}));
        }
      }
    }
  }
  private receipt(receipt: NativeReceipt, active: Active): void {
    requireThat(receipt.request_id === active.batch.request_id && receipt.epoch === this.scope.epoch
      && receipt.action_seq === active.batch.seq && receipt.requires_resync, 'GAME_RESPONSE_INVALID');
    this.write(() => this.journal.event('native_action_receipt', receipt));
  }
  private async complete(active: Active, receipt: NativeReceipt): Promise<void> {
    try {
      this.receipt(receipt, active);
      let released = receipt.release_confirmed;
      let observation: Observation | null = null;
      if (!released || receipt.status === 'unknown' || receipt.status === 'cancelled') {
        this.markFenced(receipt.error_code ?? 'ACTION_UNKNOWN'); released = await this.releaseNative();
      } else {
        this.lastRelease = true;
        try {observation = await this.observe(true);} catch {this.markFenced('GAME_OBSERVATION_UNAVAILABLE');}
      }
      const health = await this.client.call('lane_status', {}, 250); this.charge(health);
      if (health.fenced) this.markFenced(health.reason ?? 'LEASE_EXPIRED');
      let status: ActionAck['status'] = receipt.status;
      if (!released || !observation && status === 'emitted') status = 'unknown';
      if (active.interrupt && status !== 'unknown') status = 'cancelled';
      this.terminal(active,status,released,receipt.emitted_events,
        status === 'emitted' ? null : active.interrupt ?? receipt.error_code ?? this.reason ?? 'ACTION_UNKNOWN',observation);
    } catch {
      if (this.active !== active) return; // A persisted terminal receipt is never rewritten after signal failure.
      this.markFenced(this.evidenceFailed ? 'EVIDENCE_UNAVAILABLE' : 'ACTION_UNKNOWN');
      const released = await this.releaseNative();
      this.terminal(active,'unknown',released,null,this.reason,null);
    }
  }
  private terminal(active: Active, status: ActionAck['status'], released: boolean, events: number | null,
    code: string | null, observation: Observation | null): void {
    this.write(() => {
      const ack = this.ack(active.batch,status,{emitted_events:events,completed_mono_ms:mono(),release_confirmed:released,
        error_code:code,requires_resync:this.fenced || observation === null,result_observation_id:observation?.observation_id ?? null});
      validate('ActionAck', ack); this.journal.update(ack);
    });
    if (this.active === active) this.active = null;
    this.write(() => this.signals.publish('action', `Action ${status}.`));
  }
  private markFenced(code: string): void {
    this.fenced = true; this.connected = false; this.reason ??= code; this.observations.clear();
    if (this.active) clearTimeout(this.active.timer);
  }
  private releaseNative(): Promise<boolean> {
    if (this.releaseTask) return this.releaseTask;
    this.releaseTask = (async () => {
      const started = mono();
      try {
        const health = await this.client.call('stop_all', {}, 200);
        requireThat(mono()-started <= RELEASE_TIMEOUT_MS && health.fenced && health.journal_healthy
          && health.active_request_id === null, 'INPUT_RELEASE_FAILED');
        this.charge(health); this.lastRelease = true; return true;
      } catch {this.lastRelease = false; return false;}
      finally {this.releaseTask = null;}
    })(); return this.releaseTask;
  }
  fence(code: string): Promise<void> {
    this.markFenced(code);
    if (this.active) this.active.interrupt ??= code;
    if (this.fenceTask) return this.fenceTask;
    this.fenceTask = Promise.resolve().then(async () => {
      const released = await this.releaseNative(); const active = this.active;
      if (active) {
        if (active.finishing) await active.finishing;
        else {
          active.finishing = Promise.resolve().then(async () => {
            let receipt: NativeReceipt | null = null;
            if (active.sent) {
              try {receipt = await this.client.call('action_status', {request_id:active.batch.request_id}, 250);
                this.receipt(receipt, active);} catch {receipt = null;}
            }
            const known = !active.sent || receipt !== null && receipt.status !== 'unknown';
            this.terminal(active, released && known && code !== 'ACTION_UNKNOWN' ? 'cancelled' : 'unknown',
              released,receipt?.emitted_events ?? (active.sent ? null : 0),released ? code : 'INPUT_RELEASE_FAILED',null);
          });
          await active.finishing;
        }
      }
      requireThat(released && !this.evidenceFailed, this.evidenceFailed ? 'EVIDENCE_UNAVAILABLE' : 'INPUT_RELEASE_FAILED');
    }); return this.fenceTask;
  }
  async cancel(id: string): Promise<ActionAck> {
    if (this.active?.batch.request_id === id) {try {await this.fence('CANCELLED');} catch { /* receipt retains uncertainty */ }}
    return this.journal.status(id);
  }
  async stopAll(): Promise<void> {await this.fence('STOPPED'); requireThat(this.lastRelease, 'INPUT_RELEASE_FAILED');}
  private background(task: Promise<unknown>): void {void task.catch(() => this.markFenced(this.evidenceFailed ? 'EVIDENCE_UNAVAILABLE' : 'ACTION_UNKNOWN'));}
  close(): Promise<void> {
    if (!this.closeTask) {
      clearInterval(this.watchdog); this.closed = true;
      this.closeTask = this.fence('STOPPED').finally(async () => {
        await Promise.allSettled([this.observationTail,this.renewTask ?? Promise.resolve()]); this.signals.close();
      });
    }
    return this.closeTask;
  }
}
