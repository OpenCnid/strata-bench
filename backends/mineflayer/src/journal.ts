import { DatabaseSync } from 'node:sqlite';
import { closeSync, openSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { digest, Fault, requireThat, utc, type ActionBatch, type ActionAck } from './protocol.js';

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
        CREATE TABLE IF NOT EXISTS counters(name TEXT PRIMARY KEY, value INTEGER NOT NULL);`);
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
  accept(batch: ActionBatch, ack: ActionAck): void {
    this.transaction(() => {
      requireThat(batch.seq === this.counter(`${this.epoch}:action`) + 1, 'OUT_OF_ORDER');
      this.db.prepare('INSERT INTO actions VALUES (?,?,?,?,?,?)').run(batch.request_id, batch.epoch,
        batch.seq, digest(batch), JSON.stringify(batch), JSON.stringify(ack));
      this.counter(`${this.epoch}:action`, 1); this.event('ack', ack);
    });
  }
  update(ack: ActionAck): void {
    this.transaction(() => {
      this.db.prepare('UPDATE actions SET ack=? WHERE request_id=?').run(JSON.stringify(ack), ack.request_id);
      this.event('ack', ack);
    });
  }
  recover(): void {
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
