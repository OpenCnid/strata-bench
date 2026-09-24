import test from 'node:test';
import assert from 'node:assert/strict';
import { setTimeout as wait } from 'node:timers/promises';
import { WorkerHealth } from '../src/worker_health.js';

const scope = {campaign_id:'fixture',agent_id:'body',epoch:1};
test('real executor measurements retain a delayed loop and terminal partial window', async () => {
  const rows: {kind:string; body:any}[] = [];
  const sampler = new WorkerHealth({event:(kind,body)=>rows.push({kind,body})},scope,()=>assert.fail('write failed'));
  try {
    await wait(1100);
    const until = performance.now()+140;
    while(performance.now()<until) { /* Deliberately block the measured event loop. */ }
    await wait(60);
  } finally {sampler.close();}
  const count = rows.length; sampler.close(); assert.equal(rows.length,count);
  assert.equal(rows[0]!.kind,'worker_health_start');
  const windows = rows.slice(1).map(r=>r.body);
  assert.ok(windows.length>=2);
  assert.equal(windows[0]!.terminal,false);
  assert.equal(windows.at(-1)!.terminal,true);
  let previous=0, cpu=0;
  for(const [index,w] of windows.entries()) {
    assert.equal(w.seq,index+1); assert.equal(w.start_ns,previous);
    assert.equal(w.window_ns,w.end_ns-w.start_ns); assert.equal(w.elapsed_ns,w.end_ns);
    assert.ok(w.cpu_user_us>=cpu); assert.ok(w.rss_bytes>0); assert.ok(w.heap_used_bytes>0);
    previous=w.end_ns; cpu=w.cpu_user_us;
  }
  assert.ok(windows.some(w=>w.delay_samples>0 && w.delay_ns.max>=80_000_000));
});
test('failed health storage stops sampling and requests shutdown once', async () => {
  let attempts=0, failures=0;
  const sampler = new WorkerHealth({event:()=>{if(attempts++)throw Error('quota');}},scope,()=>failures++);
  await wait(1200);
  assert.equal(failures,1); assert.equal(attempts,2);
  assert.throws(()=>sampler.close(),/WORKER_HEALTH_INCOMPLETE/);
  sampler.close();
});
test('startup storage failure throws before any interval is scheduled', () => {
  assert.throws(()=>new WorkerHealth({event:()=>{throw Error('unavailable');}},scope,()=>{}),/unavailable/);
});
