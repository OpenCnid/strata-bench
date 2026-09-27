import { createServer, type Server } from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { fields, strictJson } from './native_game.js';
import { resumeDecision, type ResumeDecision } from './native_resume.js';
import { errorBody, Fault, requireThat } from './protocol.js';

/** Operator-only endpoint. A duplicate decision is status reconciliation, never a second dispatch. */
export function serveResume(call:(operation:'resume'|'status',decision:ResumeDecision)=>Promise<unknown>,token:string):Promise<Server> {
  const bearer=Buffer.from(`Bearer ${token}`);
  const server=createServer(async(req,res)=>{
    let id:string|null=null;
    const send=(status:number,body:unknown)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(body));};
    try {
      const supplied=Buffer.from(req.headers.authorization??'');
      requireThat(supplied.length===bearer.length && timingSafeEqual(supplied,bearer) && !req.headers.origin,'FORBIDDEN');
      requireThat(req.method==='POST' && req.url==='/v1/resume' && req.headers['content-type']==='application/json','REPAIR_RESUME_INVALID');
      let size=0;const chunks:Buffer[]=[];
      for await(const chunk of req){size+=chunk.length;requireThat(size<=16384,'CAPACITY_EXCEEDED');chunks.push(Buffer.from(chunk));}
      const v=strictJson(Buffer.concat(chunks).toString('utf8'));fields(v,['schema','request_id','operation','decision']);
      requireThat(v.schema==='strata/WorkerResumeRequest/1' && typeof v.request_id==='string'
        && /^[A-Za-z0-9_.:-]{1,128}$/.test(v.request_id) && (v.operation==='resume'||v.operation==='status'),'REPAIR_RESUME_INVALID');
      id=v.request_id;
      const result=await call(v.operation,resumeDecision(v.decision));
      send(200,{schema:'strata/WorkerResumeResponse/1',request_id:id,status:'ok',result});
    }catch(error){send(error instanceof Fault && error.code==='FORBIDDEN'?403:400,
      {schema:'strata/WorkerResumeResponse/1',request_id:id,status:'error',error:errorBody(error,id,null)});}
  });
  server.requestTimeout=1000;server.headersTimeout=1000;server.timeout=7000;server.maxConnections=2;
  return new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>resolve(server));});
}
