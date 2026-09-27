import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormatsModule from 'ajv-formats';
import { validatePrivateRecord, type PrivateRecordName } from '../operator/records.js';

const root = new URL('../../../../', import.meta.url);
const corpus = JSON.parse(readFileSync(new URL('tests/fixtures/private_record_semantics.json', root), 'utf8'));
const examples = Object.fromEntries([...readFileSync(new URL('SPEC.md', root), 'utf8')
  .matchAll(/```json\s*([\s\S]*?)```/g)].map(match => JSON.parse(match[1]!))
  .map(record => [record.schema.split('/')[1], record]));
const ajv = new Ajv2020({strict: false, strictNumbers: true, coerceTypes: false});
(addFormatsModule as unknown as (a: Ajv2020) => void)(ajv);
const names = ['PackLock', 'CampaignConfig', 'AgentConfig', 'CheckpointManifest', 'BudgetLedger',
  'GameEvent', 'EvaluationProtocol', 'EvaluationResult'];
const schemas = Object.fromEntries(names.map(name => [name, ajv.compile(JSON.parse(readFileSync(
  new URL(`schemas/v1/${names.indexOf(name) < 5 ? 'operator' : 'evaluator'}/${name}.json`, root), 'utf8')))]));
function at(body: any, path: string): any {
  return path.split('/').reduce((node, part) => node[part], body);
}
function assign(body: any, path: string, value: unknown): void {
  const parts = path.split('/');
  const parent = parts.length > 1 ? at(body, parts.slice(0, -1).join('/')) : body;
  parent[parts.at(-1)!] = structuredClone(value);
}
for (const entry of corpus.cases) test(`private record semantics: ${entry.id}`, () => {
  const profile = corpus.profiles[entry.base];
  const body = structuredClone(examples[profile.record]);
  for (const [path, value] of Object.entries(profile.set)) assign(body, path, value);
  for (const [target, source] of Object.entries(entry.copy ?? {})) assign(body, target, at(body, source as string));
  for (const [path, value] of Object.entries(entry.set)) assign(body, path, value);
  const before = structuredClone(body);
  if (entry.valid) assert.deepEqual(validatePrivateRecord(profile.record, body), body);
  else assert.throws(() => validatePrivateRecord(profile.record, body), /SCHEMA_UNSUPPORTED/);
  if (entry.schema_reject) assert.equal(schemas[profile.record]!(body), false);
  assert.deepEqual(body, before);
});
test('private validator dispatch rejects unknown names and schema/name substitution', () => {
  for (const name of ['ActionBatch', '__proto__', 'Unknown'])
    assert.throws(() => validatePrivateRecord(name as PrivateRecordName, examples.PackLock), /SCHEMA_UNSUPPORTED/);
  assert.throws(() => validatePrivateRecord('PackLock', examples.GameEvent), /SCHEMA_UNSUPPORTED/);
});
