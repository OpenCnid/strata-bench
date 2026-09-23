import type { Readable } from 'node:stream';
import { fields, strictJson } from './native_game.js';
import { Fault, requireThat } from './errors.js';

export const OPERATOR_STOP_POLICY = 'operator-stdin-stop2250/1';
export const OPERATOR_STOP_ARGUMENT = '--operator-stop';
export const OPERATOR_DRAIN_MS = 2250;
export type StopScope = {campaign_id:string;agent_id:string;epoch:number;lease_id:string};
export type StopRequest = StopScope & {schema:'strata/WorkerStop/1';policy:typeof OPERATOR_STOP_POLICY;request_id:string};

/** One bounded command on the operator-owned pipe; never a game RPC or shell. */
export class WorkerControl {
  request:StopRequest|null = null;
  received:number|null = null;
  private buffer=Buffer.alloc(0);
  private failed=false;
  private closed=false;
  constructor(private input:Readable, private scope:StopScope, private stop:()=>void,
    private fault:(reason:string)=>void, private now:()=>number=()=>performance.now()) {
    input.on('data',this.data);input.once('end',this.end);input.once('error',this.error);
  }
  private reject(reason:string):void {
    if(this.failed || this.closed)return;
    this.failed=true;this.close();this.fault(reason);
  }
  private error=():void=>this.reject('WORKER_OPERATOR_LOST');
  private end=():void=>{if(!this.request || this.buffer.length)this.reject('WORKER_OPERATOR_LOST');};
  private data=(chunk:Buffer):void=>{
    try {
      requireThat(!this.request && Buffer.isBuffer(chunk) && this.buffer.length+chunk.length<=4096,
        'WORKER_OPERATOR_COMMAND');
      this.buffer=Buffer.concat([this.buffer,chunk]);
      const end=this.buffer.indexOf(10);
      if(end<0)return;
      requireThat(end===this.buffer.length-1,'WORKER_OPERATOR_COMMAND');
      const value=strictJson(this.buffer.subarray(0,end).toString('utf8'));
      fields(value,['schema','policy','request_id','campaign_id','agent_id','epoch','lease_id']);
      requireThat(value.schema==='strata/WorkerStop/1' && value.policy===OPERATOR_STOP_POLICY
        && typeof value.request_id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(value.request_id)
        && Object.entries(this.scope).every(([key,v])=>value[key]===v),'WORKER_OPERATOR_COMMAND');
      this.received=this.now();this.request=value as unknown as StopRequest;
      this.buffer=Buffer.alloc(0);this.stop();
    } catch(error) {this.reject(error instanceof Fault ? error.code : 'WORKER_OPERATOR_COMMAND');}
  };
  expired():boolean {return this.received!==null && this.now()-this.received>=OPERATOR_DRAIN_MS;}
  receipt(exitCode:number, forced:boolean) {
    const ended=this.now();const elapsed=this.received===null ? null : ended-this.received;
    return {schema:'strata/WorkerStopReceipt/1',policy:OPERATOR_STOP_POLICY,scope:this.scope,
      request:this.request,received_mono_ms:this.received,child_exit_mono_ms:ended,elapsed_ms:elapsed,
      drain_limit_ms:OPERATOR_DRAIN_MS,exit_code:exitCode,forced,
      status:this.request===null ? 'not_requested' : !this.failed && exitCode===0 && !forced
        && elapsed!==null && elapsed>=0 && elapsed<=OPERATOR_DRAIN_MS ? 'pass' : 'fail',
      complete_checkpoint:false,shutdown_gate_qualified:false};
  }
  close():void {
    this.closed=true;this.input.removeListener('data',this.data);this.input.removeListener('end',this.end);
    this.input.removeListener('error',this.error);this.input.pause();
  }
}
