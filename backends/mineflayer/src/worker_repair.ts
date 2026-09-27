import { createServer, type Server } from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { fields, strictJson } from './native_game.js';
import { errorBody, Fault, requireThat } from './protocol.js';

export const WORKER_REPAIR_POLICY = 'operator-owned-fixed-repair-pause/1';
export type RepairPlan = {
  schema:'strata/WorkerRepairPlan/1'; policy:typeof WORKER_REPAIR_POLICY;
  campaign_id:string; agent_id:string; epoch:number; lease_id:string;
  transaction_id:string; plan_digest:string; expires_unix_ms:number;
};
export function repairPlan(raw:unknown):RepairPlan {
  fields(raw,['schema','policy','campaign_id','agent_id','epoch','lease_id','transaction_id','plan_digest','expires_unix_ms']);
  requireThat(raw.schema==='strata/WorkerRepairPlan/1' && raw.policy===WORKER_REPAIR_POLICY,'REPAIR_PLAN_INVALID');
  for(const key of ['campaign_id','agent_id','lease_id','transaction_id']) requireThat(typeof raw[key]==='string'
    && /^[A-Za-z0-9_.:-]{1,128}$/.test(raw[key]),'REPAIR_PLAN_INVALID');
  requireThat(Number.isSafeInteger(raw.epoch) && Number(raw.epoch)>0 && Number.isSafeInteger(raw.expires_unix_ms)
    && Number(raw.expires_unix_ms)>0 && typeof raw.plan_digest==='string' && /^[a-f0-9]{64}$/.test(raw.plan_digest),
    'REPAIR_PLAN_INVALID');
  return {...raw} as RepairPlan;
}
export interface RepairLane {
  pauseRepair(plan:RepairPlan):Promise<unknown>;
  repairStatus(plan:RepairPlan):unknown;
}

/** Separate private bearer/port. Never attach this capability to the gameplay grant. */
export function serveRepair(lane:RepairLane,token:string):Promise<Server> {
  const bearer=Buffer.from(`Bearer ${token}`);
  const server=createServer(async(req,res)=>{
    let requestId:string|null=null;
    const send=(status:number,body:unknown)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(body));};
    try {
      const supplied=Buffer.from(req.headers.authorization??'');
      requireThat(supplied.length===bearer.length && timingSafeEqual(supplied,bearer),'FORBIDDEN');
      requireThat(req.method==='POST' && req.url==='/v1/repair' && !req.headers.origin,'FORBIDDEN');
      requireThat(req.headers['content-type']==='application/json','REPAIR_REQUEST_INVALID');
      let size=0;const chunks:Buffer[]=[];
      for await(const chunk of req){size+=chunk.length;requireThat(size<=4096,'CAPACITY_EXCEEDED');chunks.push(Buffer.from(chunk));}
      const value=strictJson(Buffer.concat(chunks).toString('utf8'));
      fields(value,['schema','request_id','operation','plan']);
      requireThat(value.schema==='strata/WorkerRepairRequest/1' && typeof value.request_id==='string'
        && /^[A-Za-z0-9_.:-]{1,128}$/.test(value.request_id)
        && (value.operation==='pause'||value.operation==='status'),'REPAIR_REQUEST_INVALID');
      requestId=value.request_id;const plan=repairPlan(value.plan);
      const result=value.operation==='pause' ? await lane.pauseRepair(plan) : lane.repairStatus(plan);
      send(200,{schema:'strata/WorkerRepairResponse/1',request_id:requestId,status:'ok',result});
    } catch(error) {
      send(error instanceof Fault && error.code==='FORBIDDEN' ? 403 : 400,
        {schema:'strata/WorkerRepairResponse/1',request_id:requestId,status:'error',error:errorBody(error,requestId,null)});
    }
  });
  server.requestTimeout=1000;server.headersTimeout=1000;server.timeout=2000;server.maxConnections=2;
  return new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>resolve(server));});
}
