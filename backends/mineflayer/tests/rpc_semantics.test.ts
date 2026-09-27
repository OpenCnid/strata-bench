import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validate} from '../src/protocol.js';

const root = new URL('../../../../', import.meta.url);
const rpc = JSON.parse(readFileSync(new URL('tests/fixtures/rpc_semantics.json', root), 'utf8'));
const corpus = JSON.parse(readFileSync(new URL('tests/fixtures/public_record_semantics.json', root), 'utf8'));
const action = [...readFileSync(new URL('SPEC.md', root), 'utf8').matchAll(/```json\s*([\s\S]*?)```/g)]
  .map(match => JSON.parse(match[1]!)).find(record => record.schema === 'mcbench/ActionBatch/1');
function at(body: any, path: string): any {
  return path.split('/').reduce((node, part) => node[part], body);
}
function assign(body: any, path: string, value: unknown): void {
  const parts = path.split('/');
  const parent = parts.length > 1 ? at(body, parts.slice(0, -1).join('/')) : body;
  parent[parts.at(-1)!] = structuredClone(value);
}
function check(body: unknown, valid: boolean): void {
  const before = structuredClone(body);
  if (valid) assert.deepEqual(validate('RpcRequest', body), body);
  else assert.throws(() => validate('RpcRequest', body), /SCHEMA_UNSUPPORTED/);
  assert.deepEqual(body, before);
}
for (const entry of rpc.cases) test(`RPC envelope: ${entry.id}`, () => {
  check(structuredClone({...rpc.base, ...entry.set}), entry.valid);
});
for (const entry of corpus.cases.filter((entry: any) => corpus.profiles[entry.base].record === 'ActionBatch')) {
  test(`RPC nested action: ${entry.id}`, () => {
    const body = structuredClone(action);
    for (const [path, value] of Object.entries(corpus.profiles[entry.base].set)) assign(body, path, value);
    for (const [target, source] of Object.entries(entry.copy ?? {})) assign(body, target, at(body, source as string));
    for (const [path, value] of Object.entries(entry.set)) assign(body, path, value);
    check({...rpc.base, method: 'act', action: body}, entry.valid);
  });
}
