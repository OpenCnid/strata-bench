import { monitorEventLoopDelay } from 'node:perf_hooks';
import type { Journal } from './journal.js';
import { requireThat } from './protocol.js';

export const WORKER_HEALTH_POLICY = 'private-worker-resource-windows/1';
const PERIOD_MS = 1000;
const RESOLUTION_MS = 10;
type Scope = {campaign_id: string; agent_id: string; epoch: number};

/** Private executor-process measurements. Never counts Minecraft/avatar ticks. */
export class WorkerHealth {
  private readonly histogram = monitorEventLoopDelay({resolution: RESOLUTION_MS});
  private readonly started = process.hrtime.bigint();
  private readonly openingCpu = process.cpuUsage();
  private previous = this.started;
  private seq = 0;
  private timer?: NodeJS.Timeout;
  private closed = false;
  private failed = false;
  private readonly scope: Scope;
  constructor(private readonly journal: Pick<Journal, 'event'>, scope: Scope,
              onFailure: () => void) {
    // WorkerConfig is structurally a Scope, but carries private paths and its
    // own schema. Project fields explicitly rather than spreading that object.
    this.scope = {campaign_id:scope.campaign_id,agent_id:scope.agent_id,epoch:scope.epoch};
    journal.event('worker_health_start', {schema: 'strata/WorkerHealthStart/1', policy: WORKER_HEALTH_POLICY,
      ...this.scope, pid: process.pid, node: process.versions.node, platform: process.platform,
      clock: 'node-hrtime-ns/process', origin_hrtime_ns: this.started.toString(), period_ms: PERIOD_MS,
      delay_resolution_ms: RESOLUTION_MS, interval: 'executor-initialization-through-lane-close',
      visibility: 'evaluator'});
    this.histogram.enable();
    this.timer = setInterval(() => {
      try { this.record(false); }
      catch { this.failed = true; this.disable(); onFailure(); }
    }, PERIOD_MS);
    this.timer.unref();
  }
  private disable(): void { clearInterval(this.timer); this.histogram.disable(); }
  private record(terminal: boolean): void {
    requireThat(this.seq < 1023, 'WORKER_HEALTH_QUOTA');
    const ended = process.hrtime.bigint();
    const cpu = process.cpuUsage(this.openingCpu);
    const memory = process.memoryUsage();
    const count = this.histogram.count;
    requireThat(Number.isSafeInteger(Number(ended - this.started)) && ended >= this.previous, 'WORKER_HEALTH_CLOCK');
    const body = {schema: 'strata/WorkerHealthWindow/1', policy: WORKER_HEALTH_POLICY, ...this.scope,
      seq: this.seq + 1, terminal, start_ns: Number(this.previous - this.started), end_ns: Number(ended - this.started),
      elapsed_ns: Number(ended - this.started), window_ns: Number(ended - this.previous),
      cpu_user_us: cpu.user, cpu_system_us: cpu.system,
      rss_bytes: memory.rss, heap_used_bytes: memory.heapUsed, heap_total_bytes: memory.heapTotal,
      external_bytes: memory.external, array_buffers_bytes: memory.arrayBuffers,
      delay_samples: count,
      delay_ns: count ? {min: this.histogram.min, p50: this.histogram.percentile(50),
        p95: this.histogram.percentile(95), max: this.histogram.max, mean: this.histogram.mean} : null};
    // CPU/wall counters include journal overhead; the reset histogram does not
    // claim to measure its own commit/reset. Never invent samples during a stall.
    this.journal.event('worker_health_window', body);
    this.histogram.reset(); this.previous = ended; this.seq++;
  }
  close(): void {
    if (this.closed) return;
    this.closed = true; this.disable();
    requireThat(!this.failed, 'WORKER_HEALTH_INCOMPLETE');
    this.record(true);
  }
}
