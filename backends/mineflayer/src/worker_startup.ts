import { Fault, requireThat } from './errors.js';

export const WORKER_STARTUP_POLICY = 'child-bootstrap-initialization-heartbeat2250/1';
export const WORKER_STARTUP_MS = 2250;
export type WorkerMessage = {kind:'bootstrap_ready'|'startup_alive'} | {kind:'gateway_ready';port:number}
  | {kind:'alive';health:{connected:boolean;connected_once:boolean;fenced:boolean;reason:string|null}};

/** Private IPC lifecycle. Pulses prove event-loop liveness, never game readiness. */
export class WorkerStartup {
  phase:'bootstrap'|'waiting_config'|'initializing'|'active' = 'bootstrap';
  private began:number;
  private lastBeat:number|null = null;
  constructor(private now:()=>number = () => performance.now()) {this.began=now();}
  failure():string|null {
    const age=this.now()-this.began;
    if (this.phase==='bootstrap' && age>=WORKER_STARTUP_MS) return 'WORKER_BOOT_TIMEOUT';
    if (this.phase==='initializing' && age>=WORKER_STARTUP_MS) return 'WORKER_INITIALIZATION_TIMEOUT';
    if (this.lastBeat!==null && this.now()-this.lastBeat>2250) return 'WORKER_HEARTBEAT_EXPIRED';
    return null;
  }
  canRenew():boolean {return !this.failure() && this.phase!=='bootstrap'
    && this.lastBeat!==null && this.now()-this.lastBeat<=200;}
  initialize():void {
    requireThat(this.phase==='waiting_config' && this.canRenew(),'WORKER_BOOT_UNAVAILABLE');
    this.phase='initializing';this.began=this.now();
  }
  receive(raw:unknown):WorkerMessage {
    const failure=this.failure();if (failure) throw new Fault(failure);
    requireThat(raw!==null && typeof raw==='object' && !Array.isArray(raw),'WORKER_PROTOCOL');
    const m=raw as Record<string,unknown>;
    const keys=(expected:string[]) => requireThat(Object.keys(m).sort().join(',')===expected.sort().join(','),'WORKER_PROTOCOL');
    if (m.kind==='bootstrap_ready') {
      keys(['kind']);requireThat(this.phase==='bootstrap','WORKER_PROTOCOL');this.phase='waiting_config';
    } else if (m.kind==='startup_alive') {
      keys(['kind']);requireThat(this.phase==='waiting_config'||this.phase==='initializing','WORKER_PROTOCOL');
    } else if (m.kind==='gateway_ready') {
      keys(['kind','port']);requireThat(this.phase==='initializing' && Number.isInteger(m.port)
        && Number(m.port)>0 && Number(m.port)<=65535,'WORKER_PROTOCOL');this.phase='active';
    } else if (m.kind==='alive') {
      keys(['kind','health']);requireThat(this.phase==='active' && m.health!==null
        && typeof m.health==='object' && !Array.isArray(m.health),'WORKER_PROTOCOL');
      const h=m.health as Record<string,unknown>;
      requireThat(Object.keys(h).sort().join(',')==='connected,connected_once,fenced,reason'
        && typeof h.connected==='boolean' && typeof h.connected_once==='boolean' && typeof h.fenced==='boolean'
        && (h.reason===null || typeof h.reason==='string' && /^[A-Z0-9_]{1,96}$/.test(h.reason)),'WORKER_PROTOCOL');
    } else throw new Fault('WORKER_PROTOCOL');
    this.lastBeat=this.now();return m as WorkerMessage;
  }
}
