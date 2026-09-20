/** Operator/worker only. Never included in the allowlisted gameplay client. */
import { execFileSync } from 'node:child_process';
import { closeSync, existsSync, fsyncSync, lstatSync, mkdirSync, openSync, readFileSync,
  readdirSync, realpathSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import type { Cache, CacheFactory } from 'prismarine-auth';
import { Fault, requireThat } from './errors.js';

const repository = fileURLToPath(new URL('../../../../', import.meta.url));
const limit = 2 * 1024 * 1024;
const cacheNames = new Set(['msal','live','sisu','xbl','bed','mca','mcs','pfb']);

export function noLinks(path: string): void {
  let part = resolve(path);
  for (;;) {
    try {
      const stat = lstatSync(part);
      requireThat(!stat.isSymbolicLink() && (!stat.isFile() || stat.nlink === 1), 'UNSAFE_PATH');
    } catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error; }
    const parent = dirname(part); if (parent === part) break; part = parent;
  }
}

export function protectedCache(path: string, create = false): string {
  requireThat(isAbsolute(path), 'UNSAFE_PATH'); noLinks(path);
  const full = resolve(path);
  const rel = relative(realpathSync(repository), full);
  requireThat(rel === '..' || rel.startsWith('../') || rel.startsWith('..\\') || isAbsolute(rel), 'FORBIDDEN');
  requireThat(existsSync(full) || create, 'AWAITING_OPERATOR_AUTH');
  if (process.platform === 'win32') {
    const script = fileURLToPath(new URL('../../tools/auth_cache_acl.py', import.meta.url));
    noLinks(script);
    const python = resolve(repository, '.venv/Scripts/python.exe'); noLinks(python);
    try {
      execFileSync(python, ['-I',script,full,existsSync(full) ? 'Verify' : 'Create'],
      {stdio: 'pipe', windowsHide: true, timeout: 15000, maxBuffer: 4096});
    } catch { throw new Fault('AUTH_CACHE_PROTECTION_FAILED'); }
  } else {
    if (!existsSync(full)) mkdirSync(full, {mode: 0o700});
    const stat = lstatSync(full);
    requireThat(stat.isDirectory() && stat.uid === process.getuid?.() && (stat.mode & 0o077) === 0, 'AUTH_CACHE_PROTECTION_FAILED');
    for (const entry of readdirSync(full)) {
      const file = resolve(full, entry); noLinks(file);
      const child = lstatSync(file);
      requireThat(child.isFile() && child.uid === stat.uid && (child.mode & 0o077) === 0, 'AUTH_CACHE_PROTECTION_FAILED');
    }
  }
  requireThat(readdirSync(full).length <= 32, 'AUTH_CACHE_INVALID');
  noLinks(full); return realpathSync(full);
}

export function readPrivateJson(path: string, missing: boolean): Record<string, unknown> {
  noLinks(path);
  if (!existsSync(path)) { requireThat(missing, 'AWAITING_OPERATOR_AUTH'); return {}; }
  const stat = lstatSync(path);
  requireThat(stat.isFile() && stat.size <= limit, 'AUTH_CACHE_INVALID');
  try {
    const value: unknown = JSON.parse(readFileSync(path, 'utf8'));
    requireThat(value !== null && typeof value === 'object' && !Array.isArray(value), 'AUTH_CACHE_INVALID');
    return value as Record<string, unknown>;
  } catch { throw new Fault('AUTH_CACHE_INVALID'); }
}

export function writePrivateJson(path: string, value: unknown): void {
  noLinks(path);
  const bytes = Buffer.from(JSON.stringify(value) + '\n');
  requireThat(bytes.length <= limit, 'AUTH_CACHE_INVALID');
  const temporary = resolve(dirname(path), `.pending-${randomUUID()}`);
  let fd: number | undefined;
  try {
    fd = openSync(temporary, 'wx', 0o600); writeFileSync(fd, bytes); fsyncSync(fd);
    closeSync(fd); fd = undefined; noLinks(path); renameSync(temporary, path);
  } finally {
    if (fd !== undefined) closeSync(fd);
    if (existsSync(temporary)) unlinkSync(temporary);
  }
}

export function lockCache(directory: string): () => void {
  const path = resolve(directory, 'auth.lock');
  let fd: number;
  try { fd = openSync(path, 'wx', 0o600); } catch { throw new Fault('AUTH_CACHE_IN_USE'); }
  try { writeFileSync(fd, JSON.stringify({pid: process.pid}) + '\n'); fsyncSync(fd); }
  catch (error) { closeSync(fd); unlinkSync(path); throw error; }
  closeSync(fd);
  let released = false;
  return () => { if (!released) { released = true; unlinkSync(path); } };
}

export function strictCacheFactory(directory: string, account: string): CacheFactory {
  requireThat(/^[A-Za-z0-9_-]{1,64}$/.test(account), 'CONFIG_RANGE');
  return ({username, cacheName}) => {
    requireThat(username === account && cacheNames.has(cacheName), 'AUTH_CACHE_INVALID');
    const path = resolve(directory, `${cacheName}.json`);
    let value: Record<string, unknown> | undefined;
    const cache: Cache = {
      async reset() { writePrivateJson(path, {}); value = {}; },
      async getCached() { value ??= readPrivateJson(path, true); return value; },
      async setCached(next: unknown) {
        requireThat(next !== null && typeof next === 'object' && !Array.isArray(next), 'AUTH_CACHE_INVALID');
        writePrivateJson(path, next); value = next as Record<string, unknown>;
      },
      async setCachedPartial(next: unknown) {
        requireThat(next !== null && typeof next === 'object' && !Array.isArray(next), 'AUTH_CACHE_INVALID');
        await cache.setCached({...await cache.getCached(), ...next});
      },
    };
    return cache;
  };
}
