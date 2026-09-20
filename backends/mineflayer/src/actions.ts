import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import type { Snapshot } from './pagination.js';
import { Journal } from './journal.js';
import { Signals } from './signals.js';
import { actionSemantics, Fault, mono, requireThat, utc, validate,
  type Action, type ActionAck, type ActionBatch, type Observation, type PublicSignal } from './protocol.js';

export interface Backend {
  readonly revision: number;
  readonly connected: boolean;
  snapshot(cursor?: string): Snapshot;
  execute(action: Action, signal: AbortSignal, emit: PrimitiveEmitter): Promise<void | 'emitted'>;
  /** Resolve only after local input release is confirmed; reject uncertain release. */
  stop(): void | Promise<void>;
  disconnect(): void;
  recipeList?(after: number): unknown;
  subscribeSignals?(listener: (kind: PublicSignal['kind'], summary: string) => void): () => void;
}
export type PrimitiveEmitter = (kind?: 'safety_release') => void;
export interface Scope { campaign_id: string; agent_id: string; epoch: number; lease_id: string }
interface ActiveAction {
  batch: ActionBatch; abort: AbortController; emitted: number; timer: NodeJS.Timeout;
  finishing: Promise<void> | null; terminal: ActionAck['status']; code: string | null; released: boolean;
}
export const RELEASE_TIMEOUT_MS = 250;

export class ActionLane {
  private active: ActiveAction | null = null;
  private observations = new Map<string, Observation>();
  private lastObservation: Observation | null = null;
  private lastSnapshotDelivery = -Infinity;
  private pageTail: Promise<void> = Promise.resolve();
  private waitingPages = 0;
  private leaseUntil = mono() + 6000;
  private fenced = false;
  private fenceReason: string | null = null;
  private applyingFence = false;
  private fenceTask: Promise<void> | null = null;
  private fenceComplete = false;
  private releaseTask: Promise<boolean> | null = null;
  private lastRelease = false;
  private closeTask: Promise<void> | null = null;
  private connectedOnce = false;
  private deadline: number;
  private watchdog: NodeJS.Timeout;
  readonly signals: Signals;
  private deliveredSignal = 0;
  private unsubscribeSignals: (() => void) | undefined;
  constructor(readonly scope: Scope, readonly capabilityDigest: string, readonly backend: Backend,
    readonly journal: Journal, readonly actionKinds: readonly string[],
    readonly primitiveLimit: number, maxWallMs: number) {
    this.deadline = mono() + maxWallMs;
    this.connectedOnce = backend.connected;
    journal.recover();
    this.signals = new Signals(journal);
    this.unsubscribeSignals = backend.subscribeSignals?.((kind, summary) => {
      try { this.signals.publish(kind, summary); }
      catch { this.background(this.fence('EVIDENCE_UNAVAILABLE')); }
      if (kind === 'connection') this.checkConnection();
    });
    this.watchdog = setInterval(() => {
      this.checkConnection();
      if (mono() >= this.leaseUntil || mono() >= this.deadline) this.background(this.fence('LEASE_EXPIRED'));
    }, 25);
  }
  /** Private supervisor state. A transport gateway alone is not avatar readiness. */
  health(): {connected: boolean; connected_once: boolean; fenced: boolean; reason: string | null} {
    this.checkConnection();
    return {connected: this.backend.connected, connected_once: this.connectedOnce,
      fenced: this.fenced, reason: this.fenceReason};
  }
  private checkConnection(): void {
    if (this.backend.connected) {
      this.connectedOnce = true;
      if (this.fenced && this.fenceComplete) this.disconnectBackend();
    }
    else if (this.connectedOnce && !this.fenced) this.background(this.fence('CONNECTION_LOST'));
  }
  renewLease(): void { if (!this.fenced) this.leaseUntil = mono() + 6000; }
  observe(force = false, cursor?: string): Observation {
    const now = mono();
    const old = this.lastObservation;
    const events = this.signals.read(this.deliveredSignal);
    if (!cursor && old && (!this.backend.connected || (!force && now - this.lastSnapshotDelivery < 500))) {
      const aged = {...old, gateway_sent_mono_ms: now, age_at_send_ms: now - old.captured_mono_ms, ...events};
      if (!this.backend.connected && aged.state) aged.state = {...aged.state, connected: false};
      requireThat(Buffer.byteLength(JSON.stringify(aged)) <= 65536, 'CAPACITY_EXCEEDED');
      this.journal.event('observation_delivery', aged);
      if (events.signals.length) this.deliveredSignal = events.signals.at(-1)!.cursor;
      return aged;
    }
    requireThat(this.backend.connected, 'PRECONDITION_FAILED');
    const snapshot = this.backend.snapshot(cursor);
    const state = snapshot.state;
    state.active_request_id = this.active && !this.active.released ? this.active.batch.request_id : null;
    const sent = mono();
    const observation: Observation = {
      schema: 'mcbench/Observation/1', is_example: false, ...this.scopeFields(),
      seq: this.journal.next('observation'), recorded_at: utc(), observation_id: randomUUID(),
      mode: 'structured', captured_mono_ms: snapshot.captured_mono_ms, gateway_sent_mono_ms: sent,
      age_at_send_ms: sent - snapshot.captured_mono_ms,
      state_revision: snapshot.state_revision, capability_digest: this.capabilityDigest, state,
      ...events, frame: null, width: null, height: null, media_type: null,
      control_revision: this.scope.epoch, keymap_digest: null, pointer_locked: null, held_keys: [],
      last_action_seq: this.journal.counter(`${this.scope.epoch}:action`) || null,
    };
    requireThat(Buffer.byteLength(JSON.stringify(observation)) <= 65536, 'CAPACITY_EXCEEDED');
    validate('Observation', observation);
    this.journal.event('observation_delivery', observation);
    if (events.signals.length) this.deliveredSignal = events.signals.at(-1)!.cursor;
    snapshot.delivered?.();
    this.observations.set(observation.observation_id, observation);
    if (this.observations.size > 16) this.observations.delete(this.observations.keys().next().value!);
    this.lastSnapshotDelivery = sent;
    if (!cursor) this.lastObservation = observation;
    return observation;
  }
  async observePage(cursor: string): Promise<Observation> {
    requireThat(this.waitingPages < 8, 'CAPACITY_EXCEEDED');
    this.waitingPages++;
    const prior = this.pageTail;
    let release!: () => void;
    this.pageTail = new Promise(resolve => { release = resolve; });
    try {
      await prior;
      const wait = 500 - (mono() - this.lastSnapshotDelivery);
      if (wait > 0) await delay(wait);
      return this.observe(false, cursor);
    } finally { this.waitingPages--; release(); }
  }
  async waitEvents(after: number, durationMs = 3000): Promise<Observation> {
    const before = this.lastObservation ?? this.observe();
    const changed = await this.signals.wait(after, durationMs);
    const observation = changed ? this.observe() : {...before, gateway_sent_mono_ms: mono(),
      age_at_send_ms: mono() - before.captured_mono_ms};
    // Use a single clock read so exact age equality survives millisecond boundaries.
    observation.age_at_send_ms = observation.gateway_sent_mono_ms - observation.captured_mono_ms;
    const result = {...observation, ...this.signals.read(after)};
    if (!this.backend.connected && result.state) result.state = {...result.state, connected: false};
    requireThat(Buffer.byteLength(JSON.stringify(result)) <= 65536, 'CAPACITY_EXCEEDED');
    validate('Observation', result);
    this.journal.event('observation_delivery', result);
    return result;
  }
  private scopeFields() {
    const {campaign_id, agent_id, epoch} = this.scope;
    return {campaign_id, agent_id, epoch};
  }
  private ack(b: ActionBatch, status: ActionAck['status'], extra: Partial<ActionAck> = {}): ActionAck {
    return {schema: 'mcbench/ActionAck/1', is_example: false, ...this.scopeFields(),
      seq: this.journal.next('ack'), recorded_at: utc(), request_id: b.request_id, action_seq: b.seq,
      status, emitted_events: 0, completed_mono_ms: null, release_confirmed: false,
      error_code: null, requires_resync: false, result_observation_id: null, ...extra};
  }
  act(raw: unknown): ActionAck {
    const b = validate<ActionBatch>('ActionBatch', raw);
    actionSemantics(b);
    requireThat(b.campaign_id === this.scope.campaign_id && b.agent_id === this.scope.agent_id, 'FORBIDDEN');
    const previous = this.journal.previous(b);
    if (previous) return previous; // includes expired requests: status lookup, never re-emission
    this.checkConnection();
    requireThat(b.epoch === this.scope.epoch, 'STALE_EPOCH');
    requireThat(!this.fenced && mono() < this.leaseUntil && b.lease_id === this.scope.lease_id, 'LEASE_EXPIRED');
    requireThat(!this.active, 'ACTION_IN_PROGRESS');
    requireThat(this.backend.connected, 'PRECONDITION_FAILED');
    requireThat(b.capability_digest === this.capabilityDigest, 'CAPABILITY_MISSING');
    requireThat(this.actionKinds.includes(b.action!.kind), 'MECHANIC_UNSUPPORTED');
    requireThat(b.control_revision === this.scope.epoch && b.expected_state_revision === this.backend.revision, 'REVISION_CONFLICT');
    const observation = this.observations.get(b.observation_id);
    requireThat(observation?.state?.connected && mono() - observation.captured_mono_ms <= 2000, 'STALE_OBSERVATION');
    requireThat(observation.state_revision === b.expected_state_revision, 'REVISION_CONFLICT');
    requireThat(this.journal.counter('primitive_events') < this.primitiveLimit, 'BUDGET_EXHAUSTED');
    const minimum = b.action!.kind === 'attack' ? 3 :
      ['use_item', 'interact_entity'].includes(b.action!.kind) ? 2 : 1;
    requireThat(this.journal.counter('primitive_events') + minimum <= this.primitiveLimit, 'BUDGET_EXHAUSTED');
    const remaining = Date.parse(b.deadline_at) - Date.now();
    requireThat(remaining > 0 && remaining <= 30250 && mono() < this.deadline, 'DEADLINE_EXCEEDED');
    const ack = this.ack(b, 'accepted');
    this.journal.accept(b, ack);
    const timer = setTimeout(() => this.background(this.cancel(b.request_id, 'DEADLINE_EXCEEDED')),
      Math.min(b.duration_ms, remaining, this.deadline - mono()));
    this.lastRelease = false;
    this.active = {batch: b, abort: new AbortController(), emitted: 0, timer,
      finishing: null, terminal: 'completed', code: null, released: false};
    // The durable acceptance is observable before dispatch, including for fast actions.
    setImmediate(() => { this.background(this.run(b)); });
    return ack;
  }
  private async run(b: ActionBatch): Promise<void> {
    const active = this.active;
    if (!active || active.batch !== b || active.abort.signal.aborted) return;
    try {
      this.journal.update(this.ack(b, 'executing'));
      const result = await this.backend.execute(b.action!, active.abort.signal, kind => {
        requireThat(this.active === active && !active.released, 'LEASE_EXPIRED');
        // Safety releases remain charged and allowed during cancellation/fencing.
        // They cannot be skipped because a lease or ordinary budget just expired.
        if (kind !== 'safety_release') {
          requireThat(!active.abort.signal.aborted && !this.fenced, 'LEASE_EXPIRED');
          requireThat(this.journal.counter('primitive_events') < this.primitiveLimit, 'BUDGET_EXHAUSTED');
        }
        this.journal.counter('primitive_events', 1); active.emitted++;
      });
      if (this.active === active && !active.finishing) await this.finish(result ?? 'completed', null);
    } catch (e) {
      if (this.active !== active || active.finishing) return;
      // An adapter's rejected promise does not establish whether a packet took effect.
      const uncertain = active.emitted > 0;
      if (uncertain) { this.fenced = true; this.fenceReason ??= e instanceof Fault ? e.code : 'ACTION_UNKNOWN'; }
      await this.finish(uncertain ? 'unknown' : 'failed', e instanceof Fault ? e.code : 'ACTION_UNKNOWN');
    }
  }
  private finish(status: ActionAck['status'], code: string | null): Promise<void> {
    const active = this.active;
    if (!active) return Promise.resolve();
    if (active.finishing) {
      // A cancellation/fault arriving during release must not leave a success receipt.
      if (status === 'unknown' || (status === 'cancelled' && active.terminal !== 'unknown')) {
        active.terminal = status; active.code = code;
      }
      return active.finishing;
    }
    active.terminal = status; active.code = code;
    // Install the promise before abort/disconnect callbacks can re-enter the lane.
    active.finishing = Promise.resolve().then(async () => {
      const released = await this.stopBackend();
      active.released = released;
      if (!released) { active.terminal = 'unknown'; active.code = 'INPUT_RELEASE_FAILED'; this.fenced = true; }
      try {
        let observation: Observation | null = null;
        try { if (this.backend.connected) observation = this.observe(true); } catch { this.fenced = true; }
        if (['completed', 'emitted'].includes(active.terminal) && !observation) {
          active.terminal = 'unknown'; this.fenced = true;
        }
        const ack = this.ack(active.batch, active.terminal, {emitted_events: active.emitted,
          completed_mono_ms: mono(), release_confirmed: released, error_code: active.code,
          requires_resync: this.fenced || active.terminal === 'unknown' || observation === null,
          result_observation_id: observation?.observation_id ?? null});
        this.journal.update(ack);
        this.signals.publish('action', `Action ${active.terminal}.`);
      } catch {
        this.fenced = true; this.fenceReason = 'EVIDENCE_UNAVAILABLE';
        this.disconnectBackend(); throw new Fault('EVIDENCE_UNAVAILABLE');
      } finally { this.active = null; }
    });
    clearTimeout(active.timer); active.abort.abort();
    return active.finishing;
  }
  async cancel(id: string, code = 'CANCELLED'): Promise<ActionAck> {
    if (this.active?.batch.request_id === id) {
      // An in-flight upstream promise may complete late: fence this worker until a new epoch.
      await this.applyFence(code, 'cancelled');
    }
    return this.journal.status(id);
  }
  async stopAll(): Promise<void> {
    // Also fence idle and not-yet-dispatched work. A stopped epoch never re-arms itself.
    await this.applyFence('STOPPED', 'cancelled');
    requireThat(this.lastRelease, 'INPUT_RELEASE_FAILED');
    requireThat(this.fenceReason !== 'EVIDENCE_UNAVAILABLE', 'EVIDENCE_UNAVAILABLE');
  }
  private stopBackend(): Promise<boolean> {
    if (this.releaseTask) return this.releaseTask;
    this.releaseTask = (async () => {
      let timer: NodeJS.Timeout | undefined;
      const started = mono();
      try {
        await Promise.race([
          Promise.resolve().then(() => this.backend.stop()),
          new Promise<never>((_, reject) => {timer = setTimeout(() => reject(new Fault('INPUT_RELEASE_FAILED')), RELEASE_TIMEOUT_MS);}),
        ]);
        // A blocking backend can prevent the timer from running. It still missed the bound.
        requireThat(mono() - started <= RELEASE_TIMEOUT_MS, 'INPUT_RELEASE_FAILED');
        this.lastRelease = true; return true;
      } catch {
        // A timeout/rejection is not evidence of release; never upgrade a late response.
        this.lastRelease = false; this.fenced = true; this.fenceReason ??= 'INPUT_RELEASE_FAILED';
        this.disconnectBackend(); return false;
      } finally { clearTimeout(timer); this.releaseTask = null; }
    })();
    return this.releaseTask;
  }
  private disconnectBackend(): void {
    if (this.applyingFence) return;
    this.applyingFence = true;
    try { this.backend.disconnect(); } catch { /* supervisor owns process termination */ }
    finally { this.applyingFence = false; }
  }
  private background(task: Promise<unknown>): void {
    void task.catch(() => {
      this.fenced = true; this.fenceReason = 'EVIDENCE_UNAVAILABLE'; this.disconnectBackend();
    });
  }
  fence(code: string): Promise<void> { return this.applyFence(code, 'unknown'); }
  private applyFence(code: string, status: ActionAck['status']): Promise<void> {
    this.fenceReason ??= code;
    this.fenced = true; this.observations.clear();
    if (this.fenceTask) return this.fenceTask;
    this.fenceTask = Promise.resolve().then(async () => {
      try {
        if (this.active) await this.finish(status, code);
        else await this.stopBackend();
      } finally { this.fenceComplete = true; this.disconnectBackend(); }
    });
    // Abort immediately, before any queued executor can emit a primitive.
    this.active?.abort.abort();
    return this.fenceTask;
  }
  close(): Promise<void> {
    if (!this.closeTask) {
      clearInterval(this.watchdog); this.unsubscribeSignals?.();
      this.closeTask = this.fence('STOPPED').then(() => {
        requireThat(this.lastRelease, 'INPUT_RELEASE_FAILED');
        requireThat(this.fenceReason !== 'EVIDENCE_UNAVAILABLE', 'EVIDENCE_UNAVAILABLE');
      }).finally(() => this.signals.close());
    }
    return this.closeTask;
  }
}
