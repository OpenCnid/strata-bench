import { createServer, type Server } from 'node:http';
import { randomUUID, timingSafeEqual } from 'node:crypto';
import type { ChildProcess } from 'node:child_process';
import { readFileSync, statSync } from 'node:fs';
import { fields, NativeGameClient, strictJson } from './native_game.js';
import { restartCheckpoint, type RestartCheckpoint } from './native_restart.js';
import { repairPlan, type RepairPlan } from './worker_repair.js';
import { ForgeProcessGuard, type SupervisorEvidence } from './forge_guard.js';
import { outside, type ForgeRestartConfig, type ForgeResumeConfig } from './worker_config.js';
import { canonical, digest, errorBody, Fault, requireThat } from './protocol.js';

export type ReplacementPaths={connection_file:string;process_guard_file:string};
export type RestartGuardCall=(operation:'stop'|'attach',plan:RepairPlan,checkpoint:RestartCheckpoint,
  paths:ReplacementPaths|null)=>Promise<unknown>;
export function replacementPaths(raw:unknown):ReplacementPaths {
  fields(raw,['connection_file','process_guard_file']);
  requireThat(typeof raw.connection_file==='string' && typeof raw.process_guard_file==='string'
    && raw.connection_file.length<=4096 && raw.process_guard_file.length<=4096,'RESTART_REQUEST_INVALID');
  return {...raw} as ReplacementPaths;
}

/** Parent owns OS custody; the executor can request only its one recorded repair. */
export class RestartGuardOwner {
  private plan:RepairPlan|null=null;private checkpoint:RestartCheckpoint|null=null;
  private stopped:Promise<unknown>|null=null;private attaching:Promise<unknown>|null=null;private paths:ReplacementPaths|null=null;
  constructor(private config:ForgeRestartConfig|ForgeResumeConfig,private repository:string,private capability:string,
    private evidence:SupervisorEvidence,private remaining:()=>number,private usable:()=>boolean,
    private getGuard:()=>ForgeProcessGuard,private setGuard:(guard:ForgeProcessGuard)=>void,
    private fail:(reason:string)=>void) {}
  async receive(raw:unknown):Promise<unknown> {
    fields(raw,['kind','id','operation','plan','checkpoint','paths']);
    requireThat(raw.kind==='restart_guard_request' && typeof raw.id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(raw.id)
      && (raw.operation==='stop'||raw.operation==='attach') && this.usable(),'RESTART_REQUEST_INVALID');
    const plan=repairPlan(raw.plan), checkpoint=restartCheckpoint(raw.checkpoint);
    requireThat(['campaign_id','agent_id','epoch','lease_id'].every(k=>plan[k as keyof RepairPlan]===this.config[k as keyof ForgeRestartConfig])
      && plan.transaction_id===checkpoint.request.transaction_id && plan.plan_digest===checkpoint.request.plan_digest
      && plan.expires_unix_ms>Date.now() && this.remaining()>0,'REPAIR_NOT_OWNED');
    if(this.plan)requireThat(canonical(plan)===canonical(this.plan) && canonical(checkpoint)===canonical(this.checkpoint),'REPAIR_NOT_OWNED');
    if(raw.operation==='stop') {
      requireThat(raw.paths===null,'RESTART_REQUEST_INVALID');
      if(this.stopped)return this.stopped;
      this.plan=plan;this.checkpoint=checkpoint;
      this.stopped=(async()=>{
        const guard=this.getGuard(), ready=await guard.ready;
        const native=NativeGameClient.fromFile(this.config.connection_file);
        const proof=await native.call('settings_restart_status',{restart_id:checkpoint.request.restart_id},500);
        requireThat(canonical(proof.checkpoint)===canonical(checkpoint) && proof.phase==='prepared'
          && proof.current_instance===checkpoint.source_instance && proof.expires_unix_ms===plan.expires_unix_ms,'RESTART_CHECKPOINT_MISMATCH');
        this.evidence.event('repair_restart_stop_intent',{plan,checkpoint,process_digest:ready.process_digest,connection_digest:ready.connection_digest});
        await guard.stop();
        const result={schema:'strata/WorkerRestartOldTerminal/1',checkpoint_digest:digest(checkpoint),
          process_digest:ready.process_digest,connection_digest:ready.connection_digest,termination_confirmed:true};
        this.evidence.event('repair_restart_old_terminal',result);return result;
      })();return this.stopped;
    }
    requireThat(this.stopped && this.checkpoint,'RESTART_OLD_TERMINAL_REQUIRED');await this.stopped;
    const paths=replacementPaths(raw.paths);
    if(this.paths)requireThat(canonical(paths)===canonical(this.paths),'REPAIR_NOT_OWNED');
    if(this.attaching)return this.attaching;
    this.paths=paths;
    this.attaching=(async()=>{
      const remaining=Math.floor(Math.min(this.remaining(),plan.expires_unix_ms-Date.now()));
      requireThat(this.usable() && remaining>0,'REPAIR_DEADLINE_EXPIRED');
      const config={...this.config,max_wall_ms:remaining,connection_file:outside(paths.connection_file,this.repository),
        process_guard_file:outside(paths.process_guard_file,this.repository)};
      const connection=NativeGameClient.fromFile(config.connection_file).connection;
      const old=NativeGameClient.fromFile(this.config.connection_file).connection;
      requireThat(connection.fingerprint===this.config.native_fingerprint && connection.session_id!==old.session_id
        && digest(connection)!==digest(old),'RESTART_CONNECTION_MISMATCH');
      requireThat(statSync(config.process_guard_file).size<=8192,'PROCESS_GRANT_QUOTA');
      const grant=strictJson(readFileSync(config.process_guard_file,'utf8')) as Record<string,unknown>;
      requireThat(grant.schema===(this.config.schema==='strata/ForgeDevelopmentWorker/5'?'strata/ForgeProcessGuardGrant/4':'strata/ForgeProcessGuardGrant/3')
        && canonical(restartCheckpoint(grant.restart_checkpoint))===canonical(checkpoint)
        && canonical(repairPlan(grant.repair_plan))===canonical(plan),'RESTART_CHECKPOINT_MISMATCH');
      this.evidence.event('repair_restart_attach_intent',{checkpoint_digest:digest(checkpoint),connection_digest:digest(connection),remaining_wall_ms:remaining});
      const guard=new ForgeProcessGuard(config,this.capability,this.evidence,this.usable,this.fail);this.setGuard(guard);
      const binding=await guard.ready;
      const oldReady=await this.stopped as {process_digest:string};
      requireThat(binding.process_digest!==oldReady.process_digest && this.usable() && this.remaining()>0
        && Date.now()<plan.expires_unix_ms,'RESTART_CONNECTION_MISMATCH');
      const result={schema:'strata/WorkerRestartReplacement/1',connection_file:config.connection_file,guard:binding};
      this.evidence.event('repair_restart_replacement_guarded',{checkpoint_digest:digest(checkpoint),guard:binding});return result;
    })();return this.attaching;
  }
}

/** Only the current child process can receive these replies; they are never heartbeat evidence. */
export function restartGuardClient():{call:RestartGuardCall;close:()=>void} {
  const pending=new Map<string,{resolve:(value:unknown)=>void;reject:(error:Error)=>void;timer:NodeJS.Timeout}>();
  const onMessage=(raw:unknown)=>{
    if(!raw || typeof raw!=='object' || (raw as {kind?:unknown}).kind!=='restart_guard_reply')return;
    try {
      fields(raw,['kind','id','ok','result','error_code']);
      requireThat(typeof raw.id==='string' && typeof raw.ok==='boolean','RESTART_PROTOCOL');
      const item=pending.get(raw.id);if(!item)return;
      if(raw.ok)requireThat(raw.error_code===null,'RESTART_PROTOCOL');
      pending.delete(raw.id);clearTimeout(item.timer);
      if(raw.ok){item.resolve(raw.result);}
      else item.reject(new Fault(typeof raw.error_code==='string' && /^[A-Z][A-Z0-9_]{1,95}$/.test(raw.error_code)?raw.error_code:'RESTART_UNAVAILABLE'));
    } catch {for(const item of pending.values()){clearTimeout(item.timer);item.reject(new Fault('RESTART_PROTOCOL'));}pending.clear();}
  };
  process.on('message',onMessage);
  return {call:(operation,plan,checkpoint,paths)=>new Promise((resolve,reject)=>{
    requireThat(process.send && process.connected,'RESTART_SUPERVISOR_UNAVAILABLE');
    const id=randomUUID();const timer=setTimeout(()=>{pending.delete(id);reject(new Fault('RESTART_OUTCOME_UNKNOWN'));},6000);
    pending.set(id,{resolve,reject,timer});process.send({kind:'restart_guard_request',id,operation,plan,checkpoint,paths});
  }),close:()=>{process.removeListener('message',onMessage);for(const item of pending.values()){clearTimeout(item.timer);item.reject(new Fault('RESTART_STOPPED'));}pending.clear();}};
}
export function replyRestart(owner:RestartGuardOwner,child:ChildProcess,raw:unknown,fail:(reason:string)=>void):void {
  const id=(raw as {id?:unknown}).id;
  const send=(ok:boolean,result:unknown,error_code:string|null)=>{if(child.connected)child.send({kind:'restart_guard_reply',id,ok,result,error_code},()=>{});};
  void owner.receive(raw).then(result=>send(true,result,null),error=>{
    const code=error instanceof Fault?error.code:'RESTART_UNAVAILABLE';send(false,null,code);fail(code);
  });
}

export function serveRestart(call:(operation:'detach'|'attach'|'status',plan:RepairPlan,checkpoint:RestartCheckpoint,
  paths:ReplacementPaths|null)=>Promise<unknown>,token:string):Promise<Server> {
  const bearer=Buffer.from(`Bearer ${token}`);
  const server=createServer(async(req,res)=>{
    let id:string|null=null;
    const send=(status:number,body:unknown)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(body));};
    try {
      const supplied=Buffer.from(req.headers.authorization??'');
      requireThat(supplied.length===bearer.length && timingSafeEqual(supplied,bearer) && !req.headers.origin,'FORBIDDEN');
      requireThat(req.method==='POST' && req.url==='/v1/restart' && req.headers['content-type']==='application/json','RESTART_REQUEST_INVALID');
      let size=0;const chunks:Buffer[]=[];
      for await(const chunk of req){size+=chunk.length;requireThat(size<=16384,'CAPACITY_EXCEEDED');chunks.push(Buffer.from(chunk));}
      const v=strictJson(Buffer.concat(chunks).toString('utf8'));fields(v,['schema','request_id','operation','plan','checkpoint','paths']);
      requireThat(v.schema==='strata/WorkerRestartRequest/1' && typeof v.request_id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(v.request_id)
        && (v.operation==='detach'||v.operation==='attach'||v.operation==='status'),'RESTART_REQUEST_INVALID');id=v.request_id;
      const paths=v.operation==='attach'?replacementPaths(v.paths):null;
      requireThat(v.operation==='attach'||v.paths===null,'RESTART_REQUEST_INVALID');
      const result=await call(v.operation,repairPlan(v.plan),restartCheckpoint(v.checkpoint),paths);
      send(200,{schema:'strata/WorkerRestartResponse/1',request_id:id,status:'ok',result});
    }catch(error){send(error instanceof Fault && error.code==='FORBIDDEN'?403:400,
      {schema:'strata/WorkerRestartResponse/1',request_id:id,status:'error',error:errorBody(error,id,null)});}
  });
  server.requestTimeout=1000;server.headersTimeout=1000;server.timeout=7000;server.maxConnections=2;
  return new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>resolve(server));});
}
