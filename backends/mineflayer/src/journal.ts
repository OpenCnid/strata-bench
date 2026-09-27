import { DatabaseSync } from 'node:sqlite';
import { randomUUID } from 'node:crypto';
import { closeSync, openSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { digest, Fault, mono, requireThat, utc, type ActionBatch, type ActionAck } from './protocol.js';
import type { RepairPlan } from './worker_repair.js';
import type { ResumeDecision, ResumeState } from './native_resume.js';
import type { ControlPublication } from './control_publication.js';
import { REPAIR_ACCOUNTING_POLICY, type ChargeBoundary, type RepairAccounting } from './repair_accounting.js';

export const PRIMITIVE_ACCOUNTING_POLICY = 'durable-pre-dispatch-charge/1';
export const ACTION_ADMISSION_POLICY = 'atomic-acceptance-sequence-refusal/1';

/** Private, synchronous FULL journal. Nothing dispatches before acceptance is committed. */
export class Journal {
  private readonly clockId=randomUUID();
  private db!: DatabaseSync;
  private lockFd: number;
  private lockPath: string;
  constructor(directory: string, readonly epoch: number) {
    this.lockPath = join(directory, 'executor.lock');
    // A crash deliberately requires operator fencing before this lock is removed.
    this.lockFd = openSync(this.lockPath, 'wx');
    try {
      this.db = new DatabaseSync(join(directory, 'actions.sqlite'));
      this.db.exec(`PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
        CREATE TABLE IF NOT EXISTS epochs(epoch INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS actions(request_id TEXT PRIMARY KEY, epoch INTEGER NOT NULL,
          seq INTEGER NOT NULL, digest TEXT NOT NULL, request TEXT NOT NULL, ack TEXT NOT NULL,
          UNIQUE(epoch, seq));
        CREATE TABLE IF NOT EXISTS events(cursor INTEGER PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS counters(name TEXT PRIMARY KEY, value INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS repair_holds(transaction_id TEXT PRIMARY KEY,epoch INTEGER NOT NULL,
          plan TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('HELD','RECOVERY_REQUIRED')));
        CREATE TABLE IF NOT EXISTS repair_resumes(transaction_id TEXT PRIMARY KEY,resume_id TEXT UNIQUE NOT NULL,
          decision TEXT NOT NULL,receipt TEXT,observation TEXT);
        CREATE TABLE IF NOT EXISTS repair_publications(transaction_id TEXT PRIMARY KEY,
          decision TEXT,observation TEXT);
        CREATE TABLE IF NOT EXISTS repair_accounting(transaction_id TEXT PRIMARY KEY,
          clock_id TEXT NOT NULL,opening TEXT NOT NULL,receipt TEXT);`);
      const last = this.db.prepare('SELECT MAX(epoch) AS epoch FROM epochs').get() as { epoch: number | null };
      requireThat(last.epoch === null || epoch > last.epoch, 'STALE_EPOCH');
      this.db.prepare('INSERT INTO epochs VALUES (?)').run(epoch);
    } catch (e) {
      this.db?.close();
      closeSync(this.lockFd); unlinkSync(this.lockPath); throw e;
    }
  }
  transaction<T>(fn: () => T): T {
    this.db.exec('BEGIN IMMEDIATE');
    try { const result = fn(); this.db.exec('COMMIT'); return result; }
    catch (e) { this.db.exec('ROLLBACK'); throw e; }
  }
  counter(name: string, increment = 0): number {
    if (increment) this.db.prepare(`INSERT INTO counters VALUES (?, ?)
      ON CONFLICT(name) DO UPDATE SET value=value+excluded.value`).run(name, increment);
    return (this.db.prepare('SELECT value FROM counters WHERE name=?').get(name) as {value: number} | undefined)?.value ?? 0;
  }
  next(kind: string): number { return this.counter(`${this.epoch}:${kind}`, 1); }
  event(kind: string, body: unknown): void {
    this.db.prepare('INSERT INTO events(kind,body) VALUES (?,?)').run(kind, JSON.stringify(body));
  }
  holdRepair(plan:RepairPlan,accounting=false):void {
    this.transaction(()=>{
      requireThat(plan.epoch===this.epoch && !this.unresolvedRepair(),
        'REPAIR_RECOVERY_REQUIRED');
      this.db.prepare("INSERT INTO repair_holds VALUES (?,?,?,'HELD')").run(plan.transaction_id,this.epoch,JSON.stringify(plan));
      this.event('repair_pause_intent',{schema:'strata/WorkerRepairIntent/1',plan});
      if(accounting) {
        const opening=this.chargeBoundary();
        this.db.prepare('INSERT INTO repair_accounting(transaction_id,clock_id,opening) VALUES (?,?,?)')
          .run(plan.transaction_id,this.clockId,JSON.stringify(opening));
        this.event('repair_accounting_opened',{policy:REPAIR_ACCOUNTING_POLICY,plan,clock_id:this.clockId,opening});
      }
    });
  }
  private chargeBoundary():ChargeBoundary {
    const rows=this.db.prepare("SELECT name,value FROM counters WHERE name LIKE 'native:%' ORDER BY name").all() as unknown as {name:string;value:number}[];
    requireThat(rows.length<=64 && rows.every(r=>/^native:[a-f0-9]{64}:[a-f0-9]{64}$/.test(r.name)
      && Number.isSafeInteger(r.value) && r.value>=0),'REPAIR_ACCOUNTING_INVALID');
    const total=this.counter('primitive_events');
    requireThat(Number.isSafeInteger(total) && rows.reduce((n,r)=>n+r.value,0)===total,'REPAIR_ACCOUNTING_MISMATCH');
    const cursor=this.db.prepare('SELECT MAX(cursor) AS value FROM events').get()!.value as number;
    return {cursor,mono_ms:mono(),unix_ms:Date.now(),primitive_events:total,sources:Object.fromEntries(rows.map(r=>[r.name,r.value]))};
  }
  repairAccounting(plan:RepairPlan,resumeDigest:string):RepairAccounting {
    return this.transaction(()=>{
      const row=this.db.prepare('SELECT * FROM repair_accounting WHERE transaction_id=?').get(plan.transaction_id) as {clock_id:string;opening:string;receipt:string|null}|undefined;
      const held=this.db.prepare('SELECT plan,state FROM repair_holds WHERE transaction_id=?').get(plan.transaction_id);
      const resume=this.resumeRecord(plan.transaction_id),publication=this.publicationRecord(plan.transaction_id);
      requireThat(row && row.clock_id===this.clockId && held?.state==='HELD'
        && digest(JSON.parse(held.plan as string))===digest(plan) && resume?.receipt
        && digest(resume.decision)===resumeDigest && publication && !publication.observation,'REPAIR_ACCOUNTING_UNAVAILABLE');
      if(row.receipt) {
        const saved=JSON.parse(row.receipt) as RepairAccounting,current=this.chargeBoundary();
        requireThat(saved.closing.primitive_events===current.primitive_events
          && digest(saved.closing.sources)===digest(current.sources),'REPAIR_ACCOUNTING_CHANGED');
        return saved;
      }
      const opening:ChargeBoundary=JSON.parse(row.opening),closing=this.chargeBoundary();
      requireThat(closing.mono_ms>=opening.mono_ms && closing.primitive_events>=opening.primitive_events
        && closing.primitive_events>=resume.receipt.health.attempted_primitive_events
        && Object.entries(opening.sources).every(([key,value])=>(closing.sources[key]??-1)>=value),'REPAIR_ACCOUNTING_INVALID');
      const receipt:RepairAccounting={schema:'strata/WorkerRepairAccounting/1',policy:REPAIR_ACCOUNTING_POLICY,
        worker_plan:plan,clock_id:this.clockId,resume_digest:resumeDigest,opening,closing,
        charged_primitive_events:closing.primitive_events-opening.primitive_events,elapsed_ms:closing.mono_ms-opening.mono_ms,
        complete_repair_accounting:false,avatar_ticks:null,model_usage:null,publication_tail_included:false};
      this.db.prepare('UPDATE repair_accounting SET receipt=? WHERE transaction_id=?').run(JSON.stringify(receipt),plan.transaction_id);
      this.event('repair_accounting_measured',receipt);return receipt;
    });
  }
  measuredRepair(transaction:string):RepairAccounting|null {
    const row=this.db.prepare('SELECT receipt FROM repair_accounting WHERE transaction_id=?').get(transaction);
    return row?.receipt?JSON.parse(row.receipt as string) as RepairAccounting:null;
  }
  failRepair(plan:RepairPlan,reason:string):void {
    this.transaction(()=>{
      const result=this.db.prepare("UPDATE repair_holds SET state='RECOVERY_REQUIRED' WHERE transaction_id=? AND epoch=?")
        .run(plan.transaction_id,this.epoch);
      requireThat(result.changes===1,'REPAIR_NOT_OWNED');
      this.event('repair_pause_failed',{plan,reason});
    });
  }
  private unresolvedRepair():boolean {
    return !!this.db.prepare(`SELECT 1 FROM repair_holds h LEFT JOIN repair_resumes r USING(transaction_id)
      LEFT JOIN repair_publications p USING(transaction_id)
      WHERE h.state='RECOVERY_REQUIRED' OR r.receipt IS NULL
        OR (p.transaction_id IS NOT NULL AND p.observation IS NULL) LIMIT 1`).get();
  }
  resumeRecord(transaction:string):{decision:ResumeDecision;receipt:ResumeState|null;observation:unknown}|null {
    const row=this.db.prepare('SELECT decision,receipt,observation FROM repair_resumes WHERE transaction_id=?')
      .get(transaction) as {decision:string;receipt:string|null;observation:string|null}|undefined;
    return row?{decision:JSON.parse(row.decision),receipt:row.receipt?JSON.parse(row.receipt):null,
      observation:row.observation?JSON.parse(row.observation):null}:null;
  }
  beginResume(decision:ResumeDecision,publicationRequired=false):void {
    this.transaction(()=>{
      const plan=decision.worker_plan;
      const row=this.db.prepare('SELECT plan,state,epoch FROM repair_holds WHERE transaction_id=?')
        .get(plan.transaction_id) as {plan:string;state:string;epoch:number}|undefined;
      requireThat(row && row.state==='HELD' && row.epoch===this.epoch && digest(JSON.parse(row.plan))===digest(plan),
        'REPAIR_NOT_OWNED');
      this.db.prepare('INSERT INTO repair_resumes(transaction_id,resume_id,decision) VALUES (?,?,?)')
        .run(plan.transaction_id,decision.resume_id,JSON.stringify(decision));
      this.event('repair_resume_intent',{decision});
      if(publicationRequired)this.db.prepare('INSERT INTO repair_publications(transaction_id) VALUES (?)').run(plan.transaction_id);
    });
  }
  publicationRecord(transaction:string):{decision:ControlPublication|null;observation:unknown}|null {
    const row=this.db.prepare('SELECT decision,observation FROM repair_publications WHERE transaction_id=?')
      .get(transaction) as {decision:string|null;observation:string|null}|undefined;
    return row?{decision:row.decision?JSON.parse(row.decision):null,observation:row.observation?JSON.parse(row.observation):null}:null;
  }
  beginPublication(value:ControlPublication):void {
    this.transaction(()=>{
      const tx=value.worker_plan.transaction_id,old=this.publicationRecord(tx),resume=this.resumeRecord(tx);
      requireThat(old && !old.decision && resume?.receipt && digest(resume.decision)===value.resume_digest
        && digest(resume.decision.worker_plan)===digest(value.worker_plan),'REPAIR_NOT_OWNED');
      this.db.prepare('UPDATE repair_publications SET decision=? WHERE transaction_id=?').run(JSON.stringify(value),tx);
      this.event('repair_publication_intent',value);
    });
  }
  finishPublication(value:ControlPublication,observation:unknown):void {
    this.transaction(()=>{
      const old=this.publicationRecord(value.worker_plan.transaction_id);
      requireThat(old?.decision && !old.observation && digest(old.decision)===digest(value),'REPAIR_NOT_OWNED');
      this.db.prepare('UPDATE repair_publications SET observation=? WHERE transaction_id=?')
        .run(JSON.stringify(observation),value.worker_plan.transaction_id);
      this.event('repair_publication_confirmed',{decision:value,observation});
    });
  }
  finishResume(decision:ResumeDecision,receipt:ResumeState,observation:unknown):void {
    this.transaction(()=>{
      const row=this.resumeRecord(decision.worker_plan.transaction_id);
      requireThat(row && !row.receipt && digest(row.decision)===digest(decision)
        && digest(receipt.decision)===digest(decision) && receipt.input_resumed,'REPAIR_NOT_OWNED');
      const hold=this.db.prepare('SELECT state FROM repair_holds WHERE transaction_id=?').get(decision.worker_plan.transaction_id);
      requireThat(hold?.state==='HELD','REPAIR_RECOVERY_REQUIRED');
      this.db.prepare('UPDATE repair_resumes SET receipt=?,observation=? WHERE transaction_id=?')
        .run(JSON.stringify(receipt),JSON.stringify(observation),decision.worker_plan.transaction_id);
      this.event('repair_resume_confirmed',{decision,receipt,observation});
    });
  }
  beginPrimitiveAccounting(scope: {campaign_id:string; agent_id:string; epoch:number}): void {
    this.transaction(() => {
      requireThat(scope.epoch === this.epoch && !this.db.prepare(
        "SELECT 1 FROM events WHERE kind='primitive_accounting' AND json_extract(body,'$.epoch')=?"
      ).get(this.epoch), 'PRIMITIVE_ACCOUNTING_ALREADY_STARTED');
      this.event('primitive_accounting', {schema:'strata/MineflayerPrimitiveAccounting/1',
        policy:PRIMITIVE_ACCOUNTING_POLICY, ...scope, opening_primitive_events:this.counter('primitive_events')});
    });
  }
  charge(batch: ActionBatch, actionChargeSeq: number, safetyRelease: boolean): void {
    // Commit both charge and its attribution before the adapter can emit. A
    // crash after this commit retains the charge; it never proves packet delivery.
    this.transaction(() => {
      const chargeSeq = this.counter('primitive_events', 1);
      this.event('primitive_charge', {schema:'strata/MineflayerPrimitiveCharge/1',
        policy:PRIMITIVE_ACCOUNTING_POLICY, campaign_id:batch.campaign_id, agent_id:batch.agent_id,
        epoch:batch.epoch, request_id:batch.request_id, action_seq:batch.seq,
        request_digest:digest(batch), charge_seq:chargeSeq, action_charge_seq:actionChargeSeq,
        safety_release:safetyRelease, recorded_at:utc(), mono_ms:mono(), emission_confirmed:false});
    });
  }
  previous(batch: ActionBatch): ActionAck | null {
    const row = this.db.prepare('SELECT digest,ack FROM actions WHERE request_id=?').get(batch.request_id) as
      {digest: string; ack: string} | undefined;
    if (!row) return null;
    requireThat(row.digest === digest(batch), 'IDEMPOTENCY_CONFLICT');
    return JSON.parse(row.ack) as ActionAck;
  }
  status(id: string): ActionAck {
    const row = this.db.prepare('SELECT ack FROM actions WHERE request_id=?').get(id) as {ack: string} | undefined;
    if (!row) throw new Fault('ACTION_UNKNOWN');
    return JSON.parse(row.ack) as ActionAck;
  }
  accept(batch: ActionBatch, makeAck: () => ActionAck): ActionAck {
    const result = this.transaction(() => {
      const expected = this.counter(`${this.epoch}:action`) + 1;
      if (batch.seq !== expected) {
        // Commit a private pre-intent refusal before returning the public error.
        // This records a known zero-dispatch outcome, unlike a missing receipt.
        this.event('action_refusal', {schema:'strata/ActionSequenceRefusal/1', policy:ACTION_ADMISSION_POLICY,
          campaign_id:batch.campaign_id, agent_id:batch.agent_id, epoch:batch.epoch,
          request_id:batch.request_id, request_digest:digest(batch), action_seq:batch.seq,
          expected_action_seq:expected, ack_counter:this.counter(`${this.epoch}:ack`),
          primitive_events:this.counter('primitive_events'), code:'OUT_OF_ORDER',
          recorded_at:utc(), mono_ms:mono()});
        return null;
      }
      // Allocate the receipt inside the same transaction as its durable intent.
      // Refusals and failed inserts must not consume an unrecorded ack sequence.
      const ack = makeAck();
      this.db.prepare('INSERT INTO actions VALUES (?,?,?,?,?,?)').run(batch.request_id, batch.epoch,
        batch.seq, digest(batch), JSON.stringify(batch), JSON.stringify(ack));
      this.counter(`${this.epoch}:action`, 1); this.event('ack', ack);
      return ack;
    });
    requireThat(result !== null, 'OUT_OF_ORDER');
    return result;
  }
  update(ack: ActionAck): void {
    this.transaction(() => {
      this.db.prepare('UPDATE actions SET ack=? WHERE request_id=?').run(JSON.stringify(ack), ack.request_id);
      this.event('ack', ack);
    });
  }
  recover(): void {
    // A new executor epoch is not authority to bypass a pending settings repair.
    // Only a durable confirmed resume clears the hold; intents retain recovery.
    requireThat(!this.unresolvedRepair(),'REPAIR_RECOVERY_REQUIRED');
    const rows = this.db.prepare('SELECT ack FROM actions').all() as {ack: string}[];
    for (const row of rows) {
      const ack = JSON.parse(row.ack) as ActionAck;
      if (ack.status === 'accepted' || ack.status === 'executing') {
        this.update({...ack, status: 'unknown', error_code: 'ACTION_UNKNOWN', requires_resync: true,
          seq: this.counter(`${ack.epoch}:ack`, 1), recorded_at: utc(),
          emitted_events: null, release_confirmed: false});
      }
    }
  }
  close(): void { this.db.close(); closeSync(this.lockFd); unlinkSync(this.lockPath); }
}
