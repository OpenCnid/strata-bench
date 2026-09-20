import { readFileSync, realpathSync, statSync } from 'node:fs';
import { isAbsolute, relative } from 'node:path';
import type { Scope } from './actions.js';
import { fields, strictJson } from './native_game.js';
import { requireThat } from './protocol.js';

interface Common extends Scope {
  purpose: 'manual-conformance'; state_directory: string; max_wall_ms: number; primitive_limit: number;
}
export interface VanillaConfig extends Common {
  schema:'strata/DevelopmentWorker/1'; server_kind:'vanilla'; host:string; port:number; username:string; auth_cache:string;
}
export interface ForgeConfig extends Common {
  schema:'strata/ForgeDevelopmentWorker/2'; server_kind:'e9e'; backend:'forge_client'; pack_version:'1.27.0';
  connection_file:string; native_fingerprint:string; body_fingerprint:string;
  process_guard_file:string; guard_python:string;
}
export type WorkerConfig = VanillaConfig | ForgeConfig;
export function outside(path: string, repository: string): string {
  requireThat(typeof path === 'string' && isAbsolute(path), 'FORBIDDEN');
  const full = realpathSync(path); const rel = relative(realpathSync(repository), full);
  requireThat(rel === '..' || rel.startsWith('..\\') || rel.startsWith('../') || isAbsolute(rel), 'FORBIDDEN'); return full;
}
export function workerConfig(path: string, repository: string): WorkerConfig {
  const full = outside(path, repository); requireThat(statSync(full).size <= 8192, 'CAPACITY_EXCEEDED');
  const value = strictJson(readFileSync(full,'utf8'));
  requireThat(value && typeof value === 'object' && !Array.isArray(value), 'SCHEMA_UNSUPPORTED');
  const c = value as Record<string, unknown>;
  const common = ['schema','purpose','server_kind','state_directory','max_wall_ms','primitive_limit','campaign_id','agent_id','epoch','lease_id'];
  if (c.schema === 'strata/DevelopmentWorker/1') {
    fields(c, [...common,'host','port','username','auth_cache']);
    requireThat(c.server_kind === 'vanilla', 'CAPABILITY_MISSING');
    requireThat(typeof c.host === 'string' && c.host.length > 0 && c.host.length < 256 &&
      typeof c.username === 'string' && c.username.length > 0 && c.username.length < 256, 'SCHEMA_UNSUPPORTED');
    requireThat(Number.isSafeInteger(c.port) && Number(c.port) > 0 && Number(c.port) < 65536, 'CONFIG_RANGE');
    c.auth_cache = outside(c.auth_cache as string, repository);
  } else {
    fields(c, [...common,'backend','pack_version','connection_file','native_fingerprint','body_fingerprint','process_guard_file','guard_python']);
    requireThat(c.schema === 'strata/ForgeDevelopmentWorker/2' && c.server_kind === 'e9e'
      && c.backend === 'forge_client' && c.pack_version === '1.27.0', 'CAPABILITY_MISSING');
    for (const name of ['native_fingerprint','body_fingerprint']) requireThat(typeof c[name] === 'string'
      && /^[a-f0-9]{64}$/.test(c[name]), 'CAPABILITY_MISSING');
    c.connection_file = outside(c.connection_file as string, repository);
    c.process_guard_file = outside(c.process_guard_file as string, repository);
    requireThat(typeof c.guard_python === 'string' && isAbsolute(c.guard_python), 'FORBIDDEN');
    c.guard_python = realpathSync(c.guard_python);
    requireThat(statSync(c.guard_python as string).isFile(), 'PROCESS_GUARD_UNAVAILABLE');
  }
  requireThat(c.purpose === 'manual-conformance', 'FORBIDDEN');
  for (const name of ['campaign_id','agent_id','lease_id']) requireThat(typeof c[name] === 'string'
    && /^[A-Za-z0-9_.:-]{1,128}$/.test(c[name]), 'SCHEMA_UNSUPPORTED');
  requireThat(Number.isSafeInteger(c.epoch) && Number(c.epoch) >= 1, 'CONFIG_RANGE');
  requireThat(Number.isSafeInteger(c.max_wall_ms) && Number(c.max_wall_ms) > 0 && Number(c.max_wall_ms) <= 600000, 'CONFIG_RANGE');
  requireThat(Number.isSafeInteger(c.primitive_limit) && Number(c.primitive_limit) >= (c.schema === 'strata/ForgeDevelopmentWorker/2' ? 2 : 1)
    && Number(c.primitive_limit) <= 100000, 'CONFIG_RANGE');
  c.state_directory = outside(c.state_directory as string, repository);
  return c as unknown as WorkerConfig;
}
