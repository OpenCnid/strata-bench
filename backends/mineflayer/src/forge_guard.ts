import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { closeSync, fsyncSync, openSync, readFileSync, realpathSync, statSync, writeSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { hashFile } from './capability_pins.js';
import { fields, NativeGameClient, strictJson } from './native_game.js';
import { canonical, digest, Fault, mono, requireThat } from './protocol.js';
import type { ForgeConfig } from './worker_config.js';

export function guardImplementationDigest(): string {
  const names = ['forge_guard.py','process_guard.py','processes.py','native_game.py',
    'native_settings.py','contracts.py','storage.py','client_discovery.py'];
  return digest(Object.fromEntries(names.map(name => [name,
    hashFile(new URL(`../../../../src/mcbench/${name}`,import.meta.url))])));
}
export interface ForgeGuardReady {
  schema:'strata/ProcessGuardEvent/1'; kind:'ready'; process_digest:string;
  campaign_id:string; agent_id:string; epoch:number; whole_client_lifetime:true;
  campaign_admission:false; remaining_wall_ms:number; policy:'forge-process-listener-client-thread/1';
  connection_digest:string; body_fingerprint:string; connection_generation:number;
  implementation_digest:string; python:'3.12.14';
}

/** Private lifecycle evidence. A truncated final frame is not a clean stop. */
export class SupervisorEvidence {
  private fd: number; private sequence = 0; private previous = '0'.repeat(64); private bytes = 0;
  private clock = randomUUID();
  constructor(directory: string, epoch: number) {
    this.fd = openSync(resolve(directory,`supervisor-${epoch}.jsonl`),'wx',0o600);
  }
  event(kind: string, value: unknown): void {
    const body = {schema:'strata/SupervisorEvent/1',seq:++this.sequence,at:new Date().toISOString(),
      source_clock_id:this.clock,mono_ms:mono(),kind,value,previous:this.previous};
    const hash = digest(body); const bytes = Buffer.from(canonical({...body,hash})+'\n');
    requireThat(this.bytes + bytes.length <= 1024*1024, 'EVIDENCE_UNAVAILABLE');
    let offset = 0;
    while (offset < bytes.length) {
      const written = writeSync(this.fd,bytes,offset,bytes.length-offset);
      requireThat(written > 0,'EVIDENCE_UNAVAILABLE'); offset += written;
    }
    fsyncSync(this.fd); this.bytes += bytes.length; this.previous = hash;
  }
  close(): void {if (this.fd >= 0) {const fd = this.fd; this.fd = -1; closeSync(fd);}}
}

/** Keep only the validated private failure code; never turn it into a stop receipt. */
export function recordGuardFailure(evidence: SupervisorEvidence, message: Record<string,unknown>): void {
  fields(message,['schema','kind','reason','termination_confirmed']);
  requireThat(message.schema === 'strata/ProcessGuardEvent/1' && message.kind === 'failed'
    && message.termination_confirmed === false && typeof message.reason === 'string'
    && /^[A-Z_]{1,96}$/.test(message.reason), 'PROCESS_GUARD_PROTOCOL');
  evidence.event('guard_failed',message);
}

/** Diagnostic timestamps never replace a separate confirmed-stop receipt. */
export function recordTerminationTiming(evidence: SupervisorEvidence, message: Record<string,unknown>): string {
  fields(message,['schema','kind','policy','started_qpc_ns','clock_resolution_ns','wait_bound_ms',
    'job_succeeded','job_returned_after_ns','wait_started_after_ns','wait_returned_after_ns','wait_result',
    'tree_checked_after_ns','active_processes','tree_result',
    'total_processes','held_processes','signaled_processes']);
  const duration = (value:unknown):value is number => Number.isSafeInteger(value) && Number(value)>=0;
  requireThat(message.schema === 'strata/ProcessGuardEvent/1' && message.kind === 'termination_timing'
    && message.policy === 'job-call-wait-tree-qpc/2' && typeof message.started_qpc_ns === 'string'
    && /^(0|[1-9][0-9]{0,19})$/.test(message.started_qpc_ns)
    && BigInt(message.started_qpc_ns)<=18446744073709551615n
    && duration(message.clock_resolution_ns) && message.clock_resolution_ns>0 && message.clock_resolution_ns<=1000000
    && message.wait_bound_ms === 500 && typeof message.job_succeeded === 'boolean'
    && duration(message.job_returned_after_ns), 'PROCESS_GUARD_PROTOCOL');
  if (message.job_succeeded) {
    requireThat(duration(message.wait_started_after_ns) && duration(message.wait_returned_after_ns)
      && message.job_returned_after_ns<=message.wait_started_after_ns
      && message.wait_started_after_ns<=message.wait_returned_after_ns
      && typeof message.wait_result === 'string'
      && ['signaled','timeout','error'].includes(message.wait_result), 'PROCESS_GUARD_PROTOCOL');
  } else {
    requireThat(message.wait_started_after_ns === null && message.wait_returned_after_ns === null
      && message.wait_result === 'not_started', 'PROCESS_GUARD_PROTOCOL');
  }
  if (message.wait_result === 'signaled') {
    const counts=[message.active_processes,message.total_processes,message.held_processes,message.signaled_processes];
    const counted=counts.every(duration) && Number(message.active_processes)<=Number(message.total_processes)
      && Number(message.signaled_processes)<=Number(message.held_processes)
      && Number(message.held_processes)<=Number(message.total_processes) && Number(message.held_processes)<=256;
    requireThat(duration(message.tree_checked_after_ns)
      && message.tree_checked_after_ns>=Number(message.wait_returned_after_ns)
      && (counted || counts.every(x=>x===null))
      && typeof message.tree_result==='string' && ['empty','timeout','error','incomplete'].includes(message.tree_result),
    'PROCESS_GUARD_PROTOCOL');
    if (message.tree_result==='empty') requireThat(counted && message.active_processes===0
      && Number(message.total_processes)>0 && message.total_processes===message.held_processes
      && message.held_processes===message.signaled_processes
      && message.tree_checked_after_ns-Number(message.wait_started_after_ns)<=500_000_000,
    'PROCESS_GUARD_PROTOCOL');
  } else {
    requireThat(message.tree_result==='not_started' && message.tree_checked_after_ns===null
      && message.active_processes===null && message.total_processes===null
      && message.held_processes===null && message.signaled_processes===null,'PROCESS_GUARD_PROTOCOL');
  }
  evidence.event('guard_termination_timing',message);
  return message.wait_result==='signaled' && message.tree_result!=='empty'
    ? `tree_${message.tree_result}` : message.wait_result as string;
}

/** Dedicated Java lifetime owner, independent of the worker event loop. */
export class ForgeProcessGuard {
  readonly exited: Promise<number>;
  readonly ready: Promise<ForgeGuardReady>;
  private child: ChildProcessWithoutNullStreams;
  private stopping = false;
  private ended = false;
  private renewalAllowed = true;
  private failure: string | null = null;
  private readyValue: ForgeGuardReady | null = null;
  private stoppedReceipt = false;
  private terminationOutcome: string | null = null;
  private stopTask: Promise<void> | null = null;
  private pendingRenew: {kind:'renew';seq:number;nonce:string} | null = null;
  private challengeSeq = 0;

  constructor(c: ForgeConfig, capability: string, private evidence: SupervisorEvidence,
    private canRenew: () => boolean, private onFailure: (reason: string) => void) {
    requireThat(process.platform === 'win32', 'PROCESS_GUARD_UNSUPPORTED');
    requireThat(statSync(c.process_guard_file).size <= 8192,'PROCESS_GRANT_QUOTA');
    const grant = strictJson(readFileSync(c.process_guard_file,'utf8')) as Record<string,unknown>;
    fields(grant,
      ['schema','purpose','campaign_id','agent_id','epoch','process','expires_unix_ms','max_wall_ms',
        'connection_file','connection_digest','native_fingerprint','body_fingerprint','capability_digest','primitive_limit']);
    const connection = NativeGameClient.fromFile(c.connection_file).connection;
    requireThat(grant.schema === 'strata/ForgeProcessGuardGrant/1'
      && grant.purpose === 'dedicated-development-client-lifetime'
      && grant.campaign_id === c.campaign_id && grant.agent_id === c.agent_id && grant.epoch === c.epoch
      && grant.native_fingerprint === c.native_fingerprint && grant.body_fingerprint === c.body_fingerprint
      && grant.capability_digest === capability && grant.primitive_limit === c.primitive_limit
      && typeof grant.connection_file === 'string' && realpathSync(grant.connection_file) === c.connection_file
      && grant.connection_digest === digest(connection), 'PROCESS_GRANT_MISMATCH');
    const processDigest = digest(grant.process); const implementation = guardImplementationDigest();
    this.evidence.event('guard_start_intent',{grant_digest:digest(grant),process_digest:processDigest,
      connection_digest:digest(connection),implementation_digest:implementation});
    let accept!: (value:ForgeGuardReady) => void; let reject!: (error:Fault) => void;
    this.ready = new Promise((yes,no) => {accept=yes; reject=no;});
    const env = Object.fromEntries(['SystemRoot','WINDIR'].flatMap(key => process.env[key] ? [[key,process.env[key]!]] : []));
    this.child = spawn(c.guard_python,['-I','-m','mcbench.forge_guard','--grant',c.process_guard_file],
      {windowsHide:true,stdio:['pipe','pipe','pipe'],env,cwd:fileURLToPath(new URL('../../../../',import.meta.url))});
    this.child.stderr.resume(); this.child.stdin.on('error',() => this.fail('PROCESS_GUARD_PIPE_FAILED'));
    this.exited = new Promise(resolveExit => {
      this.child.once('close',(code) => {
        this.ended = true; const result = code ?? 1;
        try {this.evidence.event('guard_exit',{code:result,termination_confirmed:this.stoppedReceipt});}
        catch {this.fail('EVIDENCE_UNAVAILABLE');}
        if (!this.stopping || !this.stoppedReceipt || result !== 0) this.fail(this.failure ?? 'PROCESS_GUARD_EXITED');
        reject(new Fault(this.failure ?? 'PROCESS_GUARD_EXITED')); resolveExit(result);
      });
    });
    this.child.once('error',() => this.fail('PROCESS_GUARD_UNAVAILABLE'));
    const startup = setTimeout(() => {this.fail('PROCESS_GUARD_START_TIMEOUT'); this.child.kill();},5000);
    const renew = setInterval(() => this.renew(),20);
    this.exited.then(() => {clearTimeout(startup); clearInterval(renew);}).catch(() => {});
    let pending = '';
    this.child.stdout.on('data',(chunk:Buffer) => {
      try {
        pending += chunk.toString('utf8'); requireThat(pending.length <= 16384,'PROCESS_GUARD_PROTOCOL');
        while (pending.includes('\n')) {
          const end = pending.indexOf('\n'); const line = pending.slice(0,end); pending = pending.slice(end+1);
          const message = strictJson(line) as Record<string,unknown>;
          requireThat(message?.schema === 'strata/ProcessGuardEvent/1','PROCESS_GUARD_PROTOCOL');
          if (message.kind === 'ready') {
            fields(message,['schema','kind','process_digest','campaign_id','agent_id','epoch','whole_client_lifetime',
              'campaign_admission','remaining_wall_ms','policy','connection_digest','body_fingerprint',
              'connection_generation','implementation_digest','python']);
            requireThat(!this.readyValue && message.process_digest === processDigest
              && message.campaign_id === c.campaign_id && message.agent_id === c.agent_id && message.epoch === c.epoch
              && message.whole_client_lifetime === true && message.campaign_admission === false
              && message.policy === 'forge-process-listener-client-thread/1' && message.python === '3.12.14'
              && message.connection_digest === digest(connection) && message.body_fingerprint === c.body_fingerprint
              && Number.isSafeInteger(message.connection_generation) && Number(message.connection_generation) >= 0
              && Number.isSafeInteger(message.remaining_wall_ms) && Number(message.remaining_wall_ms) >= c.max_wall_ms+2250
              && message.implementation_digest === implementation, 'PROCESS_GUARD_BINDING_MISMATCH');
            this.readyValue = message as unknown as ForgeGuardReady;
            this.evidence.event('guard_ready',this.readyValue); clearTimeout(startup); accept(this.readyValue);
          } else if (message.kind === 'challenge') {
            fields(message,['schema','kind','seq','nonce','lease_ms']);
            requireThat(this.readyValue && Number.isSafeInteger(message.seq) && Number(message.seq)>0
              && typeof message.nonce === 'string' && /^[a-f0-9]{32}$/.test(message.nonce)
              && message.lease_ms === 1500,'PROCESS_GUARD_PROTOCOL');
            requireThat(message.seq === this.challengeSeq+1 && !this.pendingRenew,'PROCESS_GUARD_PROTOCOL');
            this.challengeSeq = Number(message.seq);
            this.pendingRenew = {kind:'renew',seq:this.challengeSeq,nonce:message.nonce}; this.renew();
          } else if (message.kind === 'termination_timing') {
            requireThat(this.readyValue && this.terminationOutcome === null, 'PROCESS_GUARD_PROTOCOL');
            this.terminationOutcome = recordTerminationTiming(this.evidence,message);
          } else if (message.kind === 'stopped') {
            fields(message,['schema','kind','reason','termination_confirmed','release_confirmed',
              'elapsed_ms','termination_wait_ms','requires_resync','campaign_admission']);
            requireThat(this.terminationOutcome === 'signaled'
              && message.termination_confirmed === true && message.release_confirmed === false
              && message.requires_resync === true && message.campaign_admission === false
              && typeof message.reason === 'string' && /^[A-Z_]{1,96}$/.test(message.reason)
              && Number.isFinite(message.elapsed_ms) && Number(message.elapsed_ms)>=0
              && Number.isFinite(message.termination_wait_ms) && Number(message.termination_wait_ms)>=0,
              'PROCESS_GUARD_PROTOCOL');
            this.evidence.event('guard_stopped',message); this.stoppedReceipt = true;
            if (!this.stopping) this.fail(message.reason);
          } else if (message.kind === 'failed') {
            recordGuardFailure(this.evidence,message);
            this.fail('PROCESS_GUARD_FAILED');
          } else throw new Fault('PROCESS_GUARD_PROTOCOL');
        }
      } catch {this.fail('PROCESS_GUARD_PROTOCOL'); this.child.stdin.destroy();}
    });
  }
  private send(value: unknown): void {
    if (this.ended || this.child.stdin.destroyed) return;
    try {this.child.stdin.write(canonical(value)+'\n');} catch {this.fail('PROCESS_GUARD_PIPE_FAILED');}
  }
  private renew():void {
    if (this.pendingRenew && this.renewalAllowed && this.canRenew()) {
      const value = this.pendingRenew; this.pendingRenew = null; this.send(value);
    }
  }
  get usable():boolean {return this.readyValue !== null && !this.failure && !this.stopping && !this.ended;}
  private fail(reason:string):void {
    if (this.failure) return;
    this.failure = reason; this.renewalAllowed = false;
    try {this.evidence.event('guard_fault',{reason});} catch {this.failure='EVIDENCE_UNAVAILABLE';}
    this.onFailure(this.failure);
  }
  stop(): Promise<void> {
    return this.stopTask ??= (async () => {
      this.stopping = true; this.renewalAllowed = false;
      // Private intent precedes pipe dispatch. Evidence failure must not suppress
      // the stop request; the independent lease remains the kernel backstop.
      try {this.evidence.event('guard_stop_requested',{already_exited:this.ended});}
      catch {this.fail('EVIDENCE_UNAVAILABLE');}
      if (!this.ended) this.send({kind:'stop'});
      const killer = setTimeout(() => this.child.kill(),1000);
      try {
        const code = await this.exited;
        requireThat(code === 0 && this.stoppedReceipt && !this.failure,'PROCESS_STOP_UNCONFIRMED');
      } finally {clearTimeout(killer);}
    })();
  }
}
