/** Operator-only canonical validation. Never import from a gameplay module.
 * Schema/semantic validity does not resolve CAS refs or confer admission.
 */
import { readFileSync } from 'node:fs';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormatsModule from 'ajv-formats';

const domains = {
  PackLock: 'operator', CampaignConfig: 'operator', AgentConfig: 'operator',
  CheckpointManifest: 'operator', BudgetLedger: 'operator', GameEvent: 'evaluator',
  EvaluationProtocol: 'evaluator', EvaluationResult: 'evaluator',
} as const;
export type PrivateRecordName = keyof typeof domains;
const ajv = new Ajv2020({strict: false, strictNumbers: true, coerceTypes: false});
(addFormatsModule as unknown as (a: Ajv2020) => void)(ajv);
const validators = new Map(Object.entries(domains).map(([name, domain]) => [name,
  ajv.compile(JSON.parse(readFileSync(new URL(`../../../../schemas/v1/${domain}/${name}.json`, import.meta.url), 'utf8')))]));
function requireValid(valid: boolean): void {
  if (!valid) throw new Error('SCHEMA_UNSUPPORTED');
}
function increasing(values: number[]): boolean {
  return values.every((value, i) => i === 0 || values[i - 1]! < value);
}
export function validatePrivateRecord<T = unknown>(name: PrivateRecordName, value: unknown): T {
  requireValid(validators.get(name)?.(value) === true);
  // Only reached after the exact closed schema validated every referenced field.
  const record = value as Record<string, any>;
  for (const [field, value] of Object.entries(record)) {
    if (field.endsWith('_at') && typeof value === 'string' && value.endsWith('Z')) {
      const date = new Date(value);
      requireValid(Number.isFinite(date.getTime()) && Number(value.slice(0, 4)) > 0
        && date.toISOString().slice(0, 19) === value.slice(0, 19));
    }
  }
  if (name === 'CampaignConfig') {
    requireValid(record.agent_ids.length === record.n && new Set(record.agent_ids).size === record.n);
    requireValid(record.checkpoints_active_s[0] === 0 && increasing(record.checkpoints_active_s)
      && record.checkpoints_active_s.at(-1) <= record.training_team_limits.active_wall_s);
  } else if (name === 'CheckpointManifest') {
    const ids = record.agents.map((agent: {agent_id: string}) => agent.agent_id);
    requireValid(ids.length > 0 && new Set(ids).size === ids.length);
    requireValid(record.clocks.active_wall_s <= record.clocks.elapsed_wall_s);
  } else if (name === 'BudgetLedger' && record.posting !== 'adjust') {
    const usage = record.usage;
    requireValid(Object.values(usage).every(value => value === null || (value as number) >= 0));
    requireValid(usage.cached_input_tokens <= usage.input_tokens);
    requireValid(usage.reasoning_tokens === null || usage.reasoning_tokens <= usage.output_tokens);
  } else if (name === 'EvaluationProtocol') {
    requireValid(record.exposure_s.includes(record.primary_checkpoint_s) && increasing(record.exposure_s));
  }
  return value as T;
}
