import { compile } from 'json-schema-to-typescript';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { validatorSource } from './validators.mjs';
const base = new URL('../../../schemas/v1/public/', import.meta.url);
const out = new URL('../src/generated/', import.meta.url);
await mkdir(out, { recursive: true });
// Top-level compiled module: implementationPins includes its executable bytes.
await writeFile(new URL('../src/schema_validators.ts', import.meta.url),
  await validatorSource());
for (const name of ['ActionBatch', 'ActionAck', 'Observation', 'RpcRequest', 'SkillRevision', 'KeybindingPatch']) {
  const schema = JSON.parse(await readFile(new URL(`${name}.json`, base), 'utf8'));
  await writeFile(new URL(`${name}.ts`, out), await compile(schema, name, {
    bannerComment: '/* Generated from Pydantic. Run tools/export_schemas.py then npm run generate. */',
    additionalProperties: false, maxItems: -1,
  }));
}
// Operator/evaluator bindings are deliberately outside the gameplay worker tree.
for (const [domain, names] of Object.entries({
  operator: ['PackLock','CampaignConfig','AgentConfig','CheckpointManifest','BudgetLedger',
    'ExecutionAuthorization','NativeLaunch','AcquisitionReceipt','LaunchProfile',
    'ProvisioningCheck','ProvisioningEvidence','RoleInventoryInput'],
  evaluator: ['GameEvent','EvaluationProtocol','EvaluationResult'],
})) {
  const source = new URL(`../../../schemas/v1/${domain}/`, import.meta.url);
  const destination = new URL('generated/', source);
  await mkdir(destination, {recursive: true});
  for (const name of names) {
    const schema = JSON.parse(await readFile(new URL(`${name}.json`, source), 'utf8'));
    await writeFile(new URL(`${name}.ts`, destination), await compile(schema, name, {
      bannerComment: '/* Operator-only generated binding. Never ship in a gameplay workspace. */',
      additionalProperties: false, maxItems: -1,
    }));
  }
}
