import { Journal } from './journal.js';
import { requireThat, utc, type PublicSignal } from './protocol.js';

/** Only explicit player-facing templates enter this stream. Private telemetry has no entry point. */
export class Signals {
  private ring: PublicSignal[] = [];
  private wake: (() => void) | null = null;
  private waiting = false;
  private closed = false;
  constructor(private readonly journal: Journal) {}
  get cursor(): number { return this.journal.counter('public_signal'); }
  publish(kind: PublicSignal['kind'], summary: string): void {
    requireThat(!this.closed, 'STOPPED');
    requireThat(['action','health','inventory','window','chat','connection'].includes(kind), 'FORBIDDEN');
    const signal = this.journal.transaction(() => {
      const signal: PublicSignal = {cursor: this.journal.counter('public_signal', 1), kind,
        recorded_at: utc(), summary: Array.from(summary.replace(/[\x00-\x1f\x7f]/g, '')).slice(0,256).join('')};
      this.journal.event('public_signal', signal); return signal;
    });
    this.ring.push(signal);
    if (this.ring.length > 128) this.ring.shift();
    this.wake?.();
  }
  read(after: number): {signals: PublicSignal[]; event_gap: boolean} {
    requireThat(Number.isSafeInteger(after) && after >= 0 && after <= this.cursor, 'OUT_OF_ORDER');
    const earliest = this.ring[0]?.cursor ?? this.cursor + 1;
    return {signals: this.ring.filter(s => s.cursor > after).slice(0,32), event_gap: after < earliest - 1};
  }
  async wait(after: number, durationMs: number): Promise<boolean> {
    requireThat(!this.closed, 'STOPPED');
    requireThat(durationMs >= 0 && durationMs <= 3000, 'DEADLINE_EXCEEDED');
    const current = this.read(after);
    if (current.signals.length || current.event_gap) return true;
    requireThat(!this.waiting, 'RATE_LIMITED');
    this.waiting = true;
    try {
      const changed = await new Promise<boolean>(resolve => {
        const timer = setTimeout(() => {this.wake = null; resolve(false);}, durationMs);
        this.wake = () => {clearTimeout(timer); this.wake = null; resolve(true);};
      });
      requireThat(!this.closed, 'STOPPED');
      return changed;
    } finally { this.waiting = false; }
  }
  close(): void { this.closed = true; this.wake?.(); }
}
