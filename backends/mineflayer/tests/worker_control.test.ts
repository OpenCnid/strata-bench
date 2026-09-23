import test from 'node:test';
import assert from 'node:assert/strict';
import { PassThrough } from 'node:stream';
import { OPERATOR_STOP_POLICY, WorkerControl } from '../src/worker_control.js';

const scope={campaign_id:'c',agent_id:'a',epoch:2,lease_id:'new-lease'};
const request={schema:'strata/WorkerStop/1',policy:OPERATOR_STOP_POLICY,request_id:'stop-1',...scope};
function fixture() {
  const input=new PassThrough();let time=100;let stopped=0;const faults:string[]=[];
  const control=new WorkerControl(input,scope,()=>{stopped++;},code=>faults.push(code),()=>time);
  return {input,control,faults,stops:()=>stopped,at:(value:number)=>{time=value;}};
}
test('one fragmented scoped command invokes drain and retains its measured receipt',()=>{
  const f=fixture();const raw=JSON.stringify(request)+'\n';
  f.input.write(raw.slice(0,21));assert.equal(f.stops(),0);
  f.input.write(raw.slice(21));assert.equal(f.stops(),1);
  f.at(2349);assert.equal(f.control.expired(),false);
  const receipt=f.control.receipt(0,false);assert.equal(receipt.elapsed_ms,2249);
  assert.equal(receipt.status,'pass');assert.deepEqual(receipt.request,request);
  assert.equal(receipt.shutdown_gate_qualified,false);f.control.close();
});
for(const [name,raw] of Object.entries({
  scope:JSON.stringify({...request,epoch:1})+'\n',
  lease:JSON.stringify({...request,lease_id:'old'})+'\n',
  schema:JSON.stringify({...request,schema:'strata/GameRequest/1'})+'\n',
  extra:JSON.stringify({...request,command:'eval'})+'\n',
  invalid:'stop\n',duplicate:JSON.stringify(request)+'\n'+JSON.stringify(request)+'\n',
  quota:'x'.repeat(4097),id:JSON.stringify({...request,request_id:'invalid id'})+'\n',
  repeated_key:JSON.stringify(request).replace('"epoch":2','"epoch":2,"epoch":2')+'\n',
}))test(`operator ${name} rejects without invoking drain`,()=>{
  const f=fixture();f.input.write(raw);assert.equal(f.stops(),0);
  assert.equal(f.faults.length,1);assert.notEqual(f.control.receipt(0,false).status,'pass');f.control.close();
});
test('a second command cannot invoke a second drain or turn a rejected stream into a pass',()=>{
  const f=fixture();f.input.write(JSON.stringify(request)+'\n');f.input.write(JSON.stringify(request)+'\n');
  assert.equal(f.stops(),1);assert.equal(f.faults.length,1);assert.equal(f.control.receipt(0,false).status,'fail');
  f.control.close();
});
test('drain deadline remains fixed and forced or late exits fail',()=>{
  const f=fixture();f.input.write(JSON.stringify(request)+'\n');
  f.at(2350);assert.equal(f.control.expired(),true);
  assert.equal(f.control.receipt(0,true).status,'fail');assert.equal(f.control.receipt(1,false).status,'fail');
  f.at(2351);assert.equal(f.control.receipt(0,false).status,'fail');f.control.close();
});
test('EOF before a complete command fails without dispatch',async()=>{
  for(const partial of ['',JSON.stringify(request)]){
    const f=fixture();f.input.end(partial);await new Promise(resolve=>setImmediate(resolve));
    assert.equal(f.stops(),0);assert.deepEqual(f.faults,['WORKER_OPERATOR_LOST']);f.control.close();
  }
});
test('wall-deadline exit without an operator request is explicitly not an operator stop',()=>{
  const f=fixture();assert.equal(f.control.receipt(0,false).status,'not_requested');f.control.close();
});
