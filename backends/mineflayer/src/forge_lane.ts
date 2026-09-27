import { randomUUID } from 'node:crypto';
import { controlPublication, type ControlPublication } from './control_publication.js';
import { setTimeout as delay } from 'node:timers/promises';
import type { Scope } from './actions.js';
import { RELEASE_TIMEOUT_MS } from './actions.js';
import { Journal } from './journal.js';
import { Signals } from './signals.js';
import { repairPlan, WORKER_REPAIR_POLICY, type RepairPlan } from './worker_repair.js';
import { restartCheckpoint, type RestartCheckpoint } from './native_restart.js';
import { resumeDecision, type ResumeDecision, type ResumeState } from './native_resume.js';
import { type ReplacementPaths, type RestartGuardCall } from './worker_restart.js';
import type { ForgeGuardReady } from './forge_guard.js';
import { fields } from './native_game.js';
import type { GameLane } from './server.js';
import type { DiscoveryQuery as RecipeQuery, QuestQuery, QuestTextQuery, QuestComponentsQuery, QuestMenuQuery } from './native_game.js';
import { FORGE_ACTIONS, NativeGameClient, nativeCapabilities, nativeFailureCode, type NativeLane, type NativeReceipt } from './native_game.js';
import { actionSemantics, canonical, digest, Fault, mono, requireThat, utc, validate,
  type ActionBatch, type ActionAck, type Observation } from './protocol.js';

interface Active {
  batch: ActionBatch; nativeBatch:ActionBatch; timer: NodeJS.Timeout; sent: boolean; nativeTerminal: boolean;
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
  private repair:RepairPlan|null = null;
  private repairPhase:'quiescing'|'paused'|'resuming'|'failed'|null = null;
  private repairUntil = 0;
  private repairTask:Promise<unknown>|null = null;
  private repairAbort:Promise<void>|null = null;
  private restartGuard:RestartGuardCall|null=null;
  private restart: {checkpoint:RestartCheckpoint;phase:'detaching'|'detached'|'attaching'|'attached';
    old_connection_digest:string;old_terminal:unknown;paths:ReplacementPaths|null;replacement:ForgeGuardReady|null;
    continuation_sent:boolean}|null=null;
  private restartTask:Promise<unknown>|null=null;
  private resumeEnabled=false;
  private resumeTask:Promise<unknown>|null=null;
  private resumeIntent:ResumeDecision|null=null;
  private resumeUntil=0;
  private publicationRequired=false;
  private publicationTask:Promise<unknown>|null=null;
  private publicationIntent:ControlPublication|null=null;
  private controls:{revision:number;digest:string;publication:string;transaction:string}|null=null;
  private constructor(readonly scope: Scope, readonly capabilityDigest: string,
    private client: NativeGameClient, readonly journal: Journal, private body: string,
    private primitiveLimit: number, maxWallMs: number, private repairPolicy?:typeof WORKER_REPAIR_POLICY) {
    this.deadline = mono() + maxWallMs; this.signals = new Signals(journal);
  }
  static async connect(scope: Scope, capabilityDigest: string, client: NativeGameClient,
    journal: Journal, body: string, primitiveLimit: number, maxWallMs: number, guardedGeneration?: number,
    repairPolicy?:typeof WORKER_REPAIR_POLICY): Promise<ForgeLane> {
    requireThat(repairPolicy===undefined || repairPolicy===WORKER_REPAIR_POLICY,'CAPABILITY_MISSING');
    const lane = new ForgeLane(scope, capabilityDigest, client, journal, body, primitiveLimit, maxWallMs,repairPolicy);
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
        if(lane.repairPhase==='resuming' && lane.resumeIntent && Date.now()>=lane.resumeIntent.lease_until_unix_ms) {
          lane.background(lane.abortRepair('REPAIR_RESUME_EXPIRED'));return;
        }
        if(lane.repair && lane.repairPhase!=='failed' && (mono()>=lane.repairUntil
          || Date.now()>=lane.repair.expires_unix_ms || mono()>=lane.deadline)) {
          lane.background(lane.abortRepair('REPAIR_DEADLINE_EXPIRED'));return;
        }
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
  repairStatus(raw:RepairPlan) {
    const plan=repairPlan(raw);
    requireThat(this.repair && canonical(plan)===canonical(this.repair),'REPAIR_NOT_OWNED');
    return {schema:'strata/WorkerRepairState/1',policy:WORKER_REPAIR_POLICY,plan:this.repair,
      phase:this.repairPhase,reason:this.repairPhase==='failed' ? this.reason : null,
      inputs_released:this.lastRelease,primitive_events:this.journal.counter('primitive_events'),
      gameplay_suspended:true,resume_authorized:false};
  }
  pauseRepair(raw:RepairPlan):Promise<unknown> {
    requireThat(this.repairPolicy===WORKER_REPAIR_POLICY,'CAPABILITY_MISSING');
    const plan=repairPlan(raw);
    for(const name of ['campaign_id','agent_id','epoch','lease_id'] as const)
      requireThat(plan[name]===this.scope[name],'REPAIR_NOT_OWNED');
    if(this.repair) {
      requireThat(canonical(plan)===canonical(this.repair),'REPAIR_NOT_OWNED');
      return this.repairPhase==='quiescing' ? this.repairTask! : Promise.resolve(this.repairStatus(plan));
    }
    const remaining=plan.expires_unix_ms-Date.now();
    requireThat(!this.closed && !this.fenced && remaining>0 && remaining<=900000
      && remaining<=this.deadline-mono(),'REPAIR_DEADLINE_INVALID');
    try {this.write(()=>this.journal.holdRepair(plan,this.publicationRequired));}
    catch(error) {
      // Intent failure cannot leave an already executing motor running while
      // the local admission lane merely reports itself fenced.
      return this.fence('EVIDENCE_UNAVAILABLE').then(()=>{throw error;});
    }
    this.repair=Object.freeze(plan);this.repairPhase='quiescing';this.repairUntil=mono()+remaining;
    const started=mono();const activeId=this.active?.batch.request_id;
    const renewing=this.renewTask;
    this.repairTask=(async()=>{
      try {
        if(renewing)await renewing;
        requireThat(!this.closed && !this.fenced && this.repairPhase==='quiescing','REPAIR_INTERRUPTED');
        await this.fence('RECONFIGURING');
        requireThat(mono()-started<=1000 && this.lastRelease && this.active===null,'REPAIR_QUIESCE_UNCONFIRMED');
        if(activeId)requireThat(!['accepted','executing','unknown'].includes(this.journal.status(activeId).status),
          'REPAIR_ACTION_UNCERTAIN');
        await this.pollRepair();
        requireThat(mono()-started<=1000 && this.repairPhase==='quiescing','REPAIR_QUIESCE_UNCONFIRMED');
        this.repairPhase='paused';
        this.write(()=>this.journal.event('repair_paused',this.repairStatus(plan)));
        return this.repairStatus(plan);
      } catch(error) {
        await this.abortRepair(error instanceof Fault ? error.code : 'REPAIR_UNAVAILABLE');throw error;
      }
    })();
    return this.repairTask;
  }
  private repairLive():boolean {
    return this.repair!==null && this.repairPhase!=='failed' && !this.closed
      && mono()<this.repairUntil && mono()<this.deadline && Date.now()<this.repair.expires_unix_ms;
  }
  enableRestart(guard:RestartGuardCall):void {
    requireThat(this.repairPolicy===WORKER_REPAIR_POLICY && !this.restartGuard,'CAPABILITY_MISSING');this.restartGuard=guard;
  }
  enableResume(publicationRequired=false):void {
    requireThat(this.restartGuard && !this.resumeEnabled,'CAPABILITY_MISSING');this.resumeEnabled=true;
    this.publicationRequired=publicationRequired;
  }
  async resumeControl(operation:'resume'|'status',raw:ResumeDecision):Promise<unknown> {
    requireThat(this.resumeEnabled,'CAPABILITY_MISSING');
    const decision=resumeDecision(raw), plan=decision.worker_plan;
    const old=this.journal.resumeRecord(plan.transaction_id);
    if(old)requireThat(canonical(old.decision)===canonical(decision),'REPAIR_NOT_OWNED');
    if(old?.receipt) {
      const native=await this.client.call('settings_resume_status',{transaction_id:plan.transaction_id},500);
      requireThat(canonical(native.decision)===canonical(decision),'REPAIR_NOT_OWNED');
      try {this.charge(native.health);} catch(error) {await this.fence('EVIDENCE_UNAVAILABLE');throw error;}
      return this.resumeStatus(decision,native,old.observation);
    }
    requireThat(this.repair && canonical(this.repair)===canonical(plan) && this.repairLive()
      && this.repairPhase!=='failed' && this.restart?.phase==='attached'
      && this.restart.replacement?.policy==='forge-process-listener-client-thread/4','REPAIR_NOT_OWNED');
    requireThat(decision.connection_generation===this.generation,'CONNECTION_CHANGED');
    if(this.resumeTask)return this.resumeTask;
    requireThat(operation==='resume' || old,'REPAIR_RESUME_UNKNOWN');
    const remaining=decision.lease_until_unix_ms-Date.now();
    requireThat(remaining>0 && remaining<=6000,'REPAIR_RESUME_EXPIRED');
    // Monotonic expiry is fixed before any durable I/O or native request.
    const until=Math.min(mono()+remaining,this.repairUntil,this.deadline,...(this.resumeIntent?[this.resumeUntil]:[]));
    this.resumeUntil=until;
    this.repairPhase='resuming';this.resumeIntent=decision;
    this.resumeTask=(async()=>{
      try {
        if(this.renewTask)await this.renewTask;
        requireThat(this.repairLive() && this.repairPhase==='resuming','REPAIR_DEADLINE_EXPIRED');
        if(!old) {
          await this.pollRepair();
          this.write(()=>this.journal.beginResume(decision,this.publicationRequired));
        }
        this.releaseTask=null;this.fenceTask=null;this.lastRelease=false;
        const native:ResumeState=old
          ? await this.client.call('settings_resume_status',{transaction_id:plan.transaction_id},500)
          : await this.client.call('settings_resume',decision,500);
        requireThat(canonical(native.decision)===canonical(decision),'REPAIR_NOT_OWNED');
        this.charge(native.health);
        requireThat(native.input_resumed && this.repairLive() && this.repairPhase==='resuming'
          && mono()<until && Date.now()<decision.lease_until_unix_ms,'REPAIR_RESUME_UNCONFIRMED');
        this.checkHealth(native.health);
        this.captures.clear();this.observations.clear();this.last=null;
        this.releaseTask=null;this.fenceTask=null;this.lastRelease=false;
        this.leaseUntil=until;this.fenced=false;this.reason=null;
        // Input admission still sees this.repair until a fresh observation and
        // durable receipt are both present. No public action can race this join.
        const observation=await this.observe(true);
        requireThat(this.repairLive() && this.repairPhase==='resuming' && !this.fenced
          && mono()<until && Date.now()<decision.lease_until_unix_ms,'REPAIR_RESUME_UNCONFIRMED');
        this.write(()=>this.journal.finishResume(decision,native,observation));
        if(!this.publicationRequired)this.releaseRepair();
        return this.resumeStatus(decision,native,observation);
      } catch(error) {
        if(!(error instanceof Fault && error.code==='GAME_OUTCOME_UNKNOWN'))
          await this.abortRepair(error instanceof Fault?error.code:'REPAIR_RESUME_UNAVAILABLE');
        throw error;
      }
    })().finally(()=>{this.resumeTask=null;});
    return this.resumeTask;
  }
  private releaseRepair():void {
    this.repair=null;this.repairPhase=null;this.repairUntil=0;this.repairAbort=null;
    this.restart=null;this.resumeIntent=null;
  }
  async measureRepair(raw:RepairPlan):Promise<unknown> {
    const plan=repairPlan(raw);
    requireThat(this.publicationRequired && this.repair && canonical(this.repair)===canonical(plan)
      && this.repairLive() && this.repairPhase==='resuming' && this.resumeIntent
      && mono()<this.resumeUntil && !this.publicationTask,'REPAIR_ACCOUNTING_UNAVAILABLE');
    const intent=this.resumeIntent,resume=this.journal.resumeRecord(plan.transaction_id);
    requireThat(resume?.receipt,'REPAIR_ACCOUNTING_UNAVAILABLE');
    try {
      const state=await this.client.call('settings_resume_status',{transaction_id:plan.transaction_id},500);
      requireThat(canonical(state.decision)===canonical(intent) && state.input_resumed
        && state.source_instance===resume.receipt.source_instance && state.current_instance===resume.receipt.current_instance,
        'REPAIR_NOT_OWNED');
      this.checkHealth(state.health);this.charge(state.health);
      requireThat(this.repairLive() && this.repairPhase==='resuming' && !this.fenced
        && mono()<this.resumeUntil && !this.publicationTask,'REPAIR_ACCOUNTING_UNAVAILABLE');
      return this.write(()=>this.journal.repairAccounting(plan,digest(intent)));
    }catch(error){await this.abortRepair(error instanceof Fault?error.code:'REPAIR_ACCOUNTING_UNAVAILABLE');throw error;}
  }
  async publishControls(operation:'publish'|'status',raw:ControlPublication):Promise<unknown> {
    requireThat(this.publicationRequired,'CAPABILITY_MISSING');
    const value=controlPublication(raw),tx=value.worker_plan.transaction_id;
    const old=this.journal.publicationRecord(tx),resume=this.journal.resumeRecord(tx);
    requireThat(old && resume?.receipt && digest(resume.decision)===value.resume_digest
      && canonical(value.worker_plan)===canonical(resume.decision.worker_plan)
      && value.control_revision===resume.decision.expected_revision
      && value.verification_ref===resume.decision.verification_ref,'REPAIR_NOT_OWNED');
    const measured=this.journal.measuredRepair(tx);
    requireThat(measured && measured.resume_digest===value.resume_digest
      && measured.closing.primitive_events===value.primitive_events,'REPAIR_ACCOUNTING_REQUIRED');
    if(old.decision)requireThat(canonical(old.decision)===canonical(value),'REPAIR_NOT_OWNED');
    const result=(observation:unknown)=>({schema:'strata/WorkerControlPublicationState/1',decision:value,observation,
      primitive_events:this.journal.counter('primitive_events'),published:!this.closed && !this.fenced && !this.repair
        && this.controls?.revision===value.control_revision && this.controls.digest===value.keymap_digest
        && this.controls.publication===value.publication_id
        && this.controls.transaction===tx
        && mono()<this.leaseUntil && mono()<this.deadline});
    if(old.observation)return result(old.observation);
    requireThat(operation==='publish' || old.decision,'CONTROL_PUBLICATION_UNKNOWN');
    requireThat(this.repairLive() && this.repairPhase==='resuming' && this.resumeIntent
      && digest(this.resumeIntent)===value.resume_digest && mono()<this.resumeUntil,'REPAIR_RESUME_EXPIRED');
    if(this.publicationTask) {
      requireThat(canonical(this.publicationIntent)===canonical(value),'REPAIR_NOT_OWNED');return this.publicationTask;
    }
    this.publicationIntent=value;
    this.publicationTask=(async()=>{
      try {
        const native=await this.client.call('settings_resume_status',{transaction_id:tx},500);
        requireThat(canonical(native.decision)===canonical(resume.decision) && native.input_resumed
          && native.source_instance===resume.receipt!.source_instance
          && native.current_instance===resume.receipt!.current_instance,'REPAIR_NOT_OWNED');
        this.checkHealth(native.health);this.charge(native.health);
        requireThat(value.primitive_events===this.journal.counter('primitive_events'),'REPAIR_ACCOUNTING_MISMATCH');
        if(!old.decision)this.write(()=>this.journal.beginPublication(value));
        this.controls={revision:value.control_revision,digest:value.keymap_digest,publication:value.publication_id,transaction:tx};
        this.captures.clear();this.observations.clear();this.last=null;
        const observation=await this.observe(true);
        requireThat(this.repairLive() && this.repairPhase==='resuming' && !this.fenced
          && mono()<this.resumeUntil && Date.now()<resume.decision.lease_until_unix_ms,'REPAIR_RESUME_EXPIRED');
        this.write(()=>this.journal.finishPublication(value,observation));
        this.releaseRepair();return result(observation);
      } catch(error) {
        await this.abortRepair(error instanceof Fault?error.code:'CONTROL_PUBLICATION_UNAVAILABLE');throw error;
      }
    })().finally(()=>{this.publicationTask=null;});
    return this.publicationTask;
  }
  private resumeStatus(decision:ResumeDecision,native:ResumeState,observation:unknown) {
    return {schema:'strata/WorkerResumeState/1',decision,native,observation,
      primitive_events:this.journal.counter('primitive_events'),
      gameplay_resumed:!this.closed && !this.fenced && this.repair===null && native.input_resumed
        && mono()<this.deadline && mono()<this.leaseUntil};
  }
  private restartStatus() {
    requireThat(this.restart && this.repair,'REPAIR_NOT_OWNED');
    return {schema:'strata/WorkerRestartState/1',plan:this.repair,checkpoint:this.restart.checkpoint,
      phase:this.repairPhase==='failed'?'recovery_required':this.restart.phase,
      old_connection_digest:this.restart.old_connection_digest,old_terminal:this.restart.old_terminal,
      replacement:this.restart.replacement,primitive_events:this.journal.counter('primitive_events'),
      gameplay_suspended:true,input_resumed:false};
  }
  async restartControl(operation:'detach'|'attach'|'status',raw:RepairPlan,rawCheckpoint:RestartCheckpoint,
    paths:ReplacementPaths|null):Promise<unknown> {
    const plan=repairPlan(raw), checkpoint=restartCheckpoint(rawCheckpoint);
    requireThat(this.restartGuard && this.repair && canonical(plan)===canonical(this.repair)
      && checkpoint.request.transaction_id===plan.transaction_id && checkpoint.request.plan_digest===plan.plan_digest,'REPAIR_NOT_OWNED');
    if(this.restart)requireThat(canonical(checkpoint)===canonical(this.restart.checkpoint),'REPAIR_NOT_OWNED');
    if(operation==='status') {
      requireThat(this.restart,'REPAIR_NOT_OWNED');
      if(this.restart.phase==='attaching' && this.restart.continuation_sent && !this.restartTask && this.repairLive()) {
        this.restartTask=this.finishReplacement(true).finally(()=>{this.restartTask=null;});
        return this.restartTask;
      }
      return this.restartStatus();
    }
    requireThat(this.repairLive() && this.repairPhase==='paused','REPAIR_DEADLINE_EXPIRED');
    if(operation==='detach') {
      if(this.restartTask)return this.restartTask;
      if(this.restart)return this.restartStatus();
      this.restartTask=(async()=>{
        if(this.renewTask)await this.renewTask;
        await this.pollRepair();
        const state=await this.client.call('settings_restart_status',{restart_id:checkpoint.request.restart_id},500);
        requireThat(canonical(state.checkpoint)===canonical(checkpoint) && state.phase==='prepared'
          && state.current_instance===checkpoint.source_instance && state.expires_unix_ms===plan.expires_unix_ms,'RESTART_CHECKPOINT_MISMATCH');
        requireThat(this.repairLive() && this.repairPhase==='paused','REPAIR_DEADLINE_EXPIRED');
        const old=digest(this.client.connection);
        this.write(()=>this.journal.event('repair_restart_detach_intent',{plan,checkpoint,old_connection_digest:old}));
        this.restart={checkpoint,phase:'detaching',old_connection_digest:old,old_terminal:null,paths:null,replacement:null,continuation_sent:false};
        const terminal=await this.restartGuard!('stop',plan,checkpoint,null);
        fields(terminal,['schema','checkpoint_digest','process_digest','connection_digest','termination_confirmed']);
        requireThat(terminal.schema==='strata/WorkerRestartOldTerminal/1' && terminal.checkpoint_digest===digest(checkpoint)
          && terminal.connection_digest===old && terminal.termination_confirmed===true,'RESTART_OLD_TERMINAL_REQUIRED');
        this.write(()=>this.journal.event('repair_restart_old_terminal',terminal));
        this.restart.old_terminal=terminal;this.restart.phase='detached';this.connected=false;
        return this.restartStatus();
      })().finally(()=>{this.restartTask=null;});return this.restartTask;
    }
    requireThat(this.restart && this.restart.old_terminal && paths,'RESTART_OLD_TERMINAL_REQUIRED');
    if(this.restart.paths)requireThat(canonical(paths)===canonical(this.restart.paths),'REPAIR_NOT_OWNED');
    if(this.restartTask)return this.restartTask;
    if(this.restart.phase==='attached')return this.restartStatus();
    this.restart.paths={...paths};this.restart.phase='attaching';
    this.restartTask=(async()=>{
      if(!this.restart!.replacement) {
        this.write(()=>this.journal.event('repair_restart_attach_intent',{checkpoint_digest:digest(checkpoint),paths}));
        const replacement=await this.restartGuard!('attach',plan,checkpoint,paths);
        fields(replacement,['schema','connection_file','guard']);
        requireThat(replacement.schema==='strata/WorkerRestartReplacement/1' && typeof replacement.connection_file==='string','RESTART_CONNECTION_MISMATCH');
        const next=NativeGameClient.fromFile(replacement.connection_file),guard=replacement.guard as ForgeGuardReady;
        requireThat(guard && guard.connection_digest===digest(next.connection) && guard.body_fingerprint===this.body
          && guard.campaign_id===plan.campaign_id && guard.agent_id===plan.agent_id && guard.epoch===plan.epoch
          && next.connection.fingerprint===this.client.connection.fingerprint
          && next.connection.session_id!==this.client.connection.session_id,'RESTART_CONNECTION_MISMATCH');
        const authority=await next.call('authority',{},500), identity=await next.call('identity',{},500);
        requireThat(this.usageKey===`native:${next.connection.fingerprint}:${digest(authority)}`
          && identity.body_fingerprint===this.body && identity.connection_generation===guard.connection_generation,'RESTART_AUTHORITY_MISMATCH');
        const state=await next.call('settings_restart_status',{restart_id:checkpoint.request.restart_id},500);
        requireThat(canonical(state.checkpoint)===canonical(checkpoint) && state.phase==='prepared'
          && state.current_instance!==checkpoint.source_instance && state.expires_unix_ms===plan.expires_unix_ms,'RESTART_CHECKPOINT_MISMATCH');
        this.write(()=>this.journal.event('repair_restart_replacement_bound',{guard,checkpoint_digest:digest(checkpoint),authority,identity}));
        this.client=next;this.generation=identity.connection_generation;this.restart!.replacement=guard;
        this.releaseTask=null;this.fenceTask=null;this.lastRelease=false;
        this.captures.clear();this.observations.clear();this.last=null;this.clockId=null;this.revision=-1;
      }
      return this.finishReplacement(this.restart!.continuation_sent);
    })().finally(()=>{this.restartTask=null;});return this.restartTask;
  }
  private async finishReplacement(statusOnly:boolean):Promise<unknown> {
    const restart=this.restart!;requireThat(this.repairLive() && restart.replacement,'REPAIR_DEADLINE_EXPIRED');
    if(!statusOnly) {
      this.write(()=>this.journal.event('repair_restart_continue_intent',{checkpoint:restart.checkpoint}));
      restart.continuation_sent=true;
    }
    const state=await this.client.call(statusOnly?'settings_restart_status':'settings_restart_continue',statusOnly
      ? {restart_id:restart.checkpoint.request.restart_id}:restart.checkpoint,500);
    requireThat(canonical(state.checkpoint)===canonical(restart.checkpoint) && state.phase==='continued'
      && state.expires_unix_ms===this.repair!.expires_unix_ms,'RESTART_CONTINUATION_UNCONFIRMED');
    await this.pollRepair();
    this.write(()=>this.journal.event('repair_restart_attached',{state,guard:restart.replacement,
      primitive_events:this.journal.counter('primitive_events')}));
    restart.phase='attached';this.connected=true;this.lastRelease=true;this.reason='RECONFIGURING';
    return this.restartStatus();
  }
  private async pollRepair():Promise<void> {
    requireThat(this.repairLive(),'REPAIR_DEADLINE_EXPIRED');
    const identity=await this.client.call('identity',{},500);
    requireThat(identity.body_fingerprint===this.body && identity.connection_generation===this.generation,
      'CONNECTION_CHANGED');
    const health=await this.client.call('lane_status',{},500);
    this.charge(health); // Retain consumption even when a subsequent ownership check fails.
    requireThat(health.fenced && health.journal_healthy && health.active_request_id===null
      && health.epoch===this.scope.epoch,'REPAIR_FENCE_LOST');
    requireThat(this.repairLive(),'REPAIR_DEADLINE_EXPIRED');
  }
  private abortRepair(code:string):Promise<void> {
    if(this.repairAbort)return this.repairAbort;
    this.repairPhase='failed';this.reason=code;this.markFenced(code);
    this.repairAbort=(async()=>{
      try {if(this.repair)this.write(()=>this.journal.failRepair(this.repair!,code));}
      finally {if(!this.restart?.old_terminal || this.restart.replacement)requireThat(await this.releaseNative(),'INPUT_RELEASE_FAILED');}
    })();return this.repairAbort;
  }
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
    if(this.repair) {
      if(this.restart && this.restart.phase!=='attached')return Promise.resolve();
      if(this.repairPhase==='quiescing' || this.repairPhase==='resuming')return Promise.resolve();
      if(this.renewTask)return this.renewTask;
      this.renewTask=this.pollRepair().catch(async error=>{
        await this.abortRepair(error instanceof Fault ? error.code : 'REPAIR_UNAVAILABLE');throw error;
      }).finally(()=>{this.renewTask=null;});
      return this.renewTask;
    }
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
      ...this.signals.read(0),frame:null,width:null,height:null,media_type:null,control_revision:this.controls?.revision??this.scope.epoch,
      keymap_digest:this.controls?.digest??null,pointer_locked:null,held_keys:[],last_action_seq:this.journal.counter(`${this.scope.epoch}:action`) || null,
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
    const b = validate<ActionBatch>('ActionBatch', raw);
    requireThat(b.campaign_id === this.scope.campaign_id && b.agent_id === this.scope.agent_id, 'FORBIDDEN');
    const previous = this.journal.previous(b); if (previous) return previous;
    actionSemantics(b,this.controls?.digest??null);
    requireThat(!this.repair,'RECONFIGURING');
    requireThat(b.epoch === this.scope.epoch, 'STALE_EPOCH');
    requireThat(!this.fenced && !this.closed && mono() < this.leaseUntil && b.lease_id === this.scope.lease_id, 'LEASE_EXPIRED');
    requireThat(!this.active && !this.observing, 'ACTION_IN_PROGRESS');
    requireThat(b.capability_digest === this.capabilityDigest, 'CAPABILITY_MISSING');
    requireThat(b.control_revision === (this.controls?.revision??this.scope.epoch), 'REVISION_CONFLICT');
    requireThat((FORGE_ACTIONS as readonly string[]).includes(b.action!.kind), 'MECHANIC_UNSUPPORTED');
    const observation = this.observations.get(b.observation_id);
    requireThat(observation && mono()-observation.captured_mono_ms <= 2000, 'STALE_OBSERVATION');
    requireThat(observation.control_revision===b.control_revision && observation.keymap_digest===b.keymap_digest,'REVISION_CONFLICT');
    requireThat(b.expected_state_revision === observation.state_revision && b.expected_state_revision === this.revision, 'REVISION_CONFLICT');
    const minimum = b.action!.kind === 'recipe_navigate' ? (b.action!.control === 'history_back' ? 3 : 4)
      : ['dig','interact_block','attack','interact_entity','place','equip','click_slot','craft','close_window'].includes(b.action!.kind) ? 3 : 2;
    requireThat(this.journal.counter('primitive_events')+minimum <= this.primitiveLimit, 'BUDGET_EXHAUSTED');
    const remaining = Date.parse(b.deadline_at)-Date.now();
    requireThat(remaining > 0 && remaining <= 30250 && mono() < this.deadline, 'DEADLINE_EXCEEDED');
    const ack = this.write(() => this.journal.accept(b, () => this.ack(b, 'accepted')));
    const timer = setTimeout(() => this.background(this.fence('DEADLINE_EXCEEDED')),
      Math.min(remaining,b.duration_ms,this.deadline-mono()));
    const nativeBatch:ActionBatch={...b,control_revision:this.scope.epoch,keymap_digest:null};
    const active: Active = {batch:b,nativeBatch,timer,sent:false,nativeTerminal:false,finishing:null,interrupt:null};
    this.active = active; this.lastRelease = false;
    setImmediate(() => this.background(this.run(active))); return ack;
  }
  private async run(active: Active): Promise<void> {
    if (this.fenced || this.active !== active) return;
    let operation: 'act' | 'action_status' = 'act';
    try {
      this.write(() => this.journal.update(this.ack(active.batch,'executing')));
      this.write(()=>this.journal.event('native_action_translation',{policy:'published-controls-to-structured-native/1',
        public_digest:digest(active.batch),native_digest:digest(active.nativeBatch),native_batch:active.nativeBatch}));
      active.sent = true;
      let receipt = await this.client.call('act', {batch:active.nativeBatch}, 500);
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
  async stopAll(): Promise<void> {
    if(this.repair)await this.abortRepair('STOPPED');
    else await this.fence('STOPPED');
    requireThat(this.lastRelease, 'INPUT_RELEASE_FAILED');
  }
  private background(task: Promise<unknown>): void {void task.catch(() => this.markFenced(this.evidenceFailed ? 'EVIDENCE_UNAVAILABLE' : 'ACTION_UNKNOWN'));}
  close(): Promise<void> {
    if (!this.closeTask) {
      clearInterval(this.watchdog); this.closed = true;
      this.closeTask = (this.repair ? this.abortRepair('STOPPED') : this.fence('STOPPED')).finally(async () => {
        await Promise.allSettled([this.observationTail,this.renewTask ?? Promise.resolve(),this.repairTask ?? Promise.resolve(),
          this.restartTask ?? Promise.resolve(),this.resumeTask ?? Promise.resolve(),this.publicationTask ?? Promise.resolve()]); this.signals.close();
      });
    }
    return this.closeTask;
  }
}
