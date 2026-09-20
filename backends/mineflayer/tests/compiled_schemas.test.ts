import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormatsModule from 'ajv-formats';
import * as compiled from '../src/schema_validators.js';
import { implementationPins } from '../src/capability_pins.js';

const backend=fileURLToPath(new URL('../../',import.meta.url));
const root=fileURLToPath(new URL('../../../../',import.meta.url));
const source=new URL('../src/',import.meta.url);
const names=['ActionBatch','ActionAck','Observation','RpcRequest'] as const;

function* mutations(value:any):Generator<unknown> {
  yield null;yield true;yield 'unknown';yield 0;yield NaN;yield Infinity;yield [];yield {};
  function* walk(node:any,path:(string|number)[]):Generator<unknown> {
    if(node===null || typeof node!=='object')return;
    for(const key of Object.keys(node)) {
      const keys=[...path,key];
      for(const replacement of [null,true,'unknown','',0,-1,0.5,NaN,Infinity,{},[],
        Number.MAX_SAFE_INTEGER+1,-Infinity,'2026-99-99T99:99:99Z','☃'.repeat(1025),
        ['private-canary'],1e308,-1e308,65536]) {
        const copy=structuredClone(value);let parent=copy;
        for(const p of keys.slice(0,-1))parent=parent[p];
        parent[key]=replacement;yield copy;
      }
      if(!Array.isArray(node)) {
        const copy=structuredClone(value);let parent=copy;
        for(const p of path)parent=parent[p];
        delete parent[key];yield copy;
      }
      yield* walk(node[key],keys);
    }
    if(!Array.isArray(node)) {
      const copy=structuredClone(value);let parent=copy;
      for(const p of path)parent=parent[p];
      parent.private_canary='forbidden';yield copy;
    }
  }
  yield* walk(value,[]);
}

test('standalone validators match runtime Ajv on public records and deep malformed variants',t=>{
  const ajv=new Ajv2020({strict:false,strictNumbers:true,allErrors:false,coerceTypes:false});
  (addFormatsModule as unknown as (a:Ajv2020)=>void)(ajv);
  const examples=Object.fromEntries([...readFileSync(join(root,'SPEC.md'),'utf8').matchAll(/```json\s*([\s\S]*?)```/g)]
    .map(match=>JSON.parse(match[1]!)).map(value=>[value.schema.split('/')[1],value]));
  examples.RpcRequest={schema:'strata/GameRequest/1',request_id:'r1',campaign_id:'c1',agent_id:'a1',epoch:1,
    deadline_at:'2026-09-20T12:00:00Z',method:'act',action:examples.ActionBatch,target_request_id:null,after:null};
  let comparisons=0;
  for(const name of names) {
    const runtime=ajv.compile(JSON.parse(readFileSync(join(root,`schemas/v1/public/${name}.json`),'utf8')));
    const standalone=compiled[name] as (value:unknown)=>boolean;
    assert.equal(runtime(examples[name]),true,`${name} positive fixture`);
    for(const value of [examples[name],...mutations(examples[name])]) {
      const before=structuredClone(value);
      assert.equal(standalone(value),runtime(value),`${name} comparison ${comparisons}`);
      assert.deepEqual(value,before,'validation must not coerce, add defaults or remove fields');comparisons++;
    }
  }
  assert.ok(comparisons>2000);t.diagnostic(`${comparisons} differential comparisons`);
});

test('generated validators are reproducible and their executable bytes are capability pinned',()=>{
  execFileSync(process.execPath,['tools/validators.mjs','--check'],{cwd:backend,windowsHide:true});
  assert.deepEqual(Object.keys(compiled.schemaHashes).sort(),[...names].sort());
  assert.equal(implementationPins()['schema_validators.js'],createHash('sha256')
    .update(readFileSync(new URL('schema_validators.js',source))).digest('hex'));
});

test('runtime rejects stale schema bytes before validation and does not load the Ajv compiler',t=>{
  const parent=resolve(tmpdir());const fixture=mkdtempSync(join(parent,'strata-schema-'));
  t.after(()=>{
    assert.ok(fixture.startsWith(parent+sep) && fixture!==parent);
    rmSync(fixture,{recursive:true,force:true});
  });
  const modules=join(fixture,'backends/mineflayer/dist/src');
  const schemas=join(fixture,'schemas/v1/public');
  mkdirSync(modules,{recursive:true});mkdirSync(schemas,{recursive:true});
  writeFileSync(join(fixture,'package.json'),' {"type":"module"}');
  for(const name of ['protocol.js','schema_validators.js','errors.js'])
    copyFileSync(new URL(name,source),join(modules,name));
  for(const name of names)copyFileSync(join(root,`schemas/v1/public/${name}.json`),join(schemas,`${name}.json`));
  const script=`import {createRequire} from 'node:module';
    await import(${JSON.stringify(pathToFileURL(join(modules,'protocol.js')).href)});
    const require=createRequire(import.meta.url);
    if(Object.keys(require.cache).some(p=>/ajv[\\\\/]dist[\\\\/](compile|2020)/.test(p)))throw Error('RUNTIME_COMPILER');`;
  const run=()=>spawnSync(process.execPath,['--input-type=module','-e',script],{cwd:backend,windowsHide:true,
    encoding:'utf8',env:{...process.env,NODE_PATH:join(backend,'node_modules')}});
  const good=run();assert.equal(good.status,0,good.stderr);
  for(const name of names) {
    const file=join(schemas,`${name}.json`);const bytes=readFileSync(file);
    writeFileSync(file,Buffer.concat([bytes,Buffer.from('\n')]));
    const stale=run();assert.notEqual(stale.status,0);assert.match(stale.stderr,/SCHEMA_BUILD_STALE/);
    writeFileSync(file,bytes);
  }
});
