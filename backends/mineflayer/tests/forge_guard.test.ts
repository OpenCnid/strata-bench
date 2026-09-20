import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, unlinkSync, rmdirSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { recordGuardFailure, recordTerminationTiming, SupervisorEvidence } from '../src/forge_guard.js';
import { digest, Fault } from '../src/protocol.js';

const failed = {schema:'strata/ProcessGuardEvent/1',kind:'failed',
  reason:'PROCESS_STOP_UNCONFIRMED',termination_confirmed:false};

test('guardian failure retains its typed private cause and never confirms termination', t => {
  const root=mkdtempSync(join(tmpdir(),'strata-guard-failure-'));
  const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  recordGuardFailure(evidence,failed);
  const record=JSON.parse(readFileSync(join(root,'supervisor-1.jsonl'),'utf8'));
  const {hash,...body}=record;
  assert.equal(hash,digest(body));assert.equal(body.previous,'0'.repeat(64));assert.equal(body.seq,1);
  assert.equal(body.kind,'guard_failed');assert.deepEqual(body.value,failed);
});

test('malformed guardian failures cannot put exception text, extra fields or false success in evidence', t => {
  const root=mkdtempSync(join(tmpdir(),'strata-guard-failure-'));
  const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  for (const patch of [{reason:'private/token-or-path'}, {reason:'A'.repeat(97)}, {reason:7},
      {reason:'PRIVATE\nVALUE'}, {schema:'unknown'}, {kind:'stopped'},
      {termination_confirmed:true}, {exception:'private exception text'}]) {
    assert.throws(()=>recordGuardFailure(evidence,{...failed,...patch}),Fault);
    assert.equal(readFileSync(join(root,'supervisor-1.jsonl'),'utf8'),'');
  }
});

const timing={schema:'strata/ProcessGuardEvent/1',kind:'termination_timing',policy:'job-call-wait-tree-qpc/2',
  started_qpc_ns:'785737300000000',clock_resolution_ns:100,wait_bound_ms:500,job_succeeded:true,
  job_returned_after_ns:2000,wait_started_after_ns:2100,wait_returned_after_ns:500100000,wait_result:'timeout',
  tree_checked_after_ns:null,active_processes:null,tree_result:'not_started',
  total_processes:null,held_processes:null,signaled_processes:null};
const drained={...timing,wait_returned_after_ns:400000000,wait_result:'signaled',
  tree_checked_after_ns:400100000,active_processes:0,tree_result:'empty',
  total_processes:3,held_processes:3,signaled_processes:3};

test('bounded termination diagnostics keep each result separate from confirmed stop', t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-guard-timing-'));const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  for(const result of ['signaled','timeout','error','not_started']) {
    const message=result==='not_started'?{...timing,job_succeeded:false,wait_started_after_ns:null,wait_returned_after_ns:null,wait_result:result}:
      result==='signaled'?drained:{...timing,wait_result:result};
    assert.equal(recordTerminationTiming(evidence,message),result);
  }
  let previous='0'.repeat(64);
  for(const line of readFileSync(join(root,'supervisor-1.jsonl'),'utf8').trim().split('\n')) {
    const {hash,...record}=JSON.parse(line);assert.equal(hash,digest(record));assert.equal(record.previous,previous);previous=hash;
    assert.equal(record.kind,'guard_termination_timing');assert.equal(record.value.termination_confirmed,undefined);
  }
});

test('root exit alone cannot authorize a successful guardian stop',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-guard-tree-'));const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  for(const result of ['timeout','error','incomplete']) {
    const message={...drained,tree_result:result,active_processes:result==='timeout'?1:0,
      held_processes:2,signaled_processes:1};
    assert.equal(recordTerminationTiming(evidence,message),`tree_${result}`);
  }
});

test('empty job proof must be timely, ordered and consistent with the root wait',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-guard-tree-'));const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  for(const patch of [{policy:'job-call-wait-qpc/1'},{tree_checked_after_ns:null},
    {tree_checked_after_ns:399999999},{tree_checked_after_ns:500002101},
    {active_processes:1},{active_processes:null},{active_processes:-1},{active_processes:true},
    {held_processes:2},{signaled_processes:2},{signaled_processes:4},{total_processes:4},
    {held_processes:257,total_processes:257,signaled_processes:257},
    {tree_result:'not_started'},{wait_result:'timeout'},{wait_result:'error'}]) {
    assert.throws(()=>recordTerminationTiming(evidence,{...drained,...patch}),Fault);
    assert.equal(readFileSync(join(root,'supervisor-1.jsonl'),'utf8'),'');
  }
});

test('malformed or contradictory termination timings cannot enter the private journal',t=>{
  const root=mkdtempSync(join(tmpdir(),'strata-guard-timing-'));const evidence=new SupervisorEvidence(root,1);
  t.after(()=>{evidence.close();unlinkSync(join(root,'supervisor-1.jsonl'));rmdirSync(root);});
  for(const patch of [{policy:'unknown'},{started_qpc_ns:'private/path'},{started_qpc_ns:1},
    {started_qpc_ns:'01'},{started_qpc_ns:'18446744073709551616'},{wait_bound_ms:1000},
    {clock_resolution_ns:0},{clock_resolution_ns:1000001},{job_succeeded:1},
    {job_returned_after_ns:-1},{job_returned_after_ns:NaN},{job_returned_after_ns:Infinity},
    {job_returned_after_ns:Number.MAX_SAFE_INTEGER+1},{wait_started_after_ns:1000},
    {wait_returned_after_ns:2000},{wait_result:['signaled']},{wait_result:'not_started'},
    {job_succeeded:false},{termination_confirmed:true},{exception:'private/token'}]) {
    assert.throws(()=>recordTerminationTiming(evidence,{...timing,...patch}),Fault);
    assert.equal(readFileSync(join(root,'supervisor-1.jsonl'),'utf8'),'');
  }
});
