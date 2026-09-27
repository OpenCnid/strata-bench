import { DatabaseSync } from 'node:sqlite';
import { closeSync, openSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { digest, Fault, mono, requireThat, utc, type ActionBatch, type ActionAck } from './protocol.js';
import type { RepairPlan } from './worker_repair.js';
import type { ResumeDecision, ResumeState } from './native_resume.js';

export const PRIMITIVE_ACCOUNTING_POLICY = 'durable-pre-dispatch-charge/1';
export const ACTION_ADMISSION_POLICY = 'atomic-acceptance-sequence-refusal/1';

/** Private, synchronous FULL journal. Nothing dispatches before acceptance is committed. */
export class Journal {
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
          decision TEXT NOT NULL,receipt TEXT,observation TEXT);`);
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
  holdRepair(plan:RepairPlan):void {
    this.transaction(()=>{
      requireThat(plan.epoch===this.epoch && !this.unresolvedRepair(),
        'REPAIR_RECOVERY_REQUIRED');
      this.db.prepare("INSERT INTO repair_holds VALUES (?,?,?,'HELD')").run(plan.transaction_id,this.epoch,JSON.stringify(plan));
      this.event('repair_pause_intent',{schema:'strata/WorkerRepairIntent/1',plan});
    });
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
      WHERE h.state='RECOVERY_REQUIRED' OR r.receipt IS NULL LIMIT 1`).get();
  }
  resumeRecord(transaction:string):{decision:ResumeDecision;receipt:ResumeState|null;observation:unknown}|null {
    const row=this.db.prepare('SELECT decision,receipt,observation FROM repair_resumes WHERE transaction_id=?')
      .get(transaction) as {decision:string;receipt:string|null;observation:string|null}|undefined;
    return row?{decision:JSON.parse(row.decision),receipt:row.receipt?JSON.parse(row.receipt):null,
      observation:row.observation?JSON.parse(row.observation):null}:null;
  }
  beginResume(decision:ResumeDecision):void {
    this.transaction(()=>{
      const plan=decision.worker_plan;
      const row=this.db.prepare('SELECT plan,state,epoch FROM repair_holds WHERE transaction_id=?')
        .get(plan.transaction_id) as {plan:string;state:string;epoch:number}|undefined;
      requireThat(row && row.state==='HELD' && row.epoch===this.epoch && digest(JSON.parse(row.plan))===digest(plan),
        'REPAIR_NOT_OWNED');
      this.db.prepare('INSERT INTO repair_resumes(transaction_id,resume_id,decision) VALUES (?,?,?)')
        .run(plan.transaction_id,decision.resume_id,JSON.stringify(decision));
      this.event('repair_resume_intent',{decision});
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
