/** Operator session-expiry preflight. JWT claims restrict reuse; they do not authenticate a player. */
import type { CacheFactory } from 'prismarine-auth';
import { Fault, requireThat } from './errors.js';

export function sessionLifetimeLimit(minimumMs: number): void {
  requireThat(Number.isSafeInteger(minimumMs) && minimumMs >= 0 && minimumMs <= 3600000, 'CONFIG_RANGE');
}

export function sessionExpiresAt(token: string): number {
  try {
    requireThat(typeof token === 'string' && token.length <= 16384
      && /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token), 'MINECRAFT_SESSION_EXPIRY_UNAVAILABLE');
    const payload = JSON.parse(Buffer.from(token.split('.')[1]!, 'base64url').toString('utf8')) as {exp?:unknown};
    requireThat(payload !== null && typeof payload === 'object' && !Array.isArray(payload)
      && typeof payload.exp === 'number' && Number.isSafeInteger(payload.exp) && payload.exp > 0
      && Number.isSafeInteger(payload.exp * 1000), 'MINECRAFT_SESSION_EXPIRY_UNAVAILABLE');
    return payload.exp * 1000;
  } catch { throw new Fault('MINECRAFT_SESSION_EXPIRY_UNAVAILABLE'); }
}

export function requireSessionLifetime(token: string, minimumMs: number, now = Date.now()): void {
  sessionLifetimeLimit(minimumMs);
  requireThat(Number.isSafeInteger(now) && now >= 0, 'CONFIG_RANGE');
  requireThat(sessionExpiresAt(token) - now >= minimumMs, 'MINECRAFT_SESSION_TOO_SHORT');
}

/** Suppress only a near-expiry Minecraft token from this read, without erasing any cache.
 * The pinned provider refreshes through its ordinary Xbox login path. Microsoft/Xbox
 * caches, account binding, exclusive locking and atomic writes remain unchanged.
 */
export function sessionCacheFactory(base: CacheFactory, minimumMs: number): CacheFactory {
  sessionLifetimeLimit(minimumMs);
  if (minimumMs === 0) return base;
  return descriptor => {
    const cache = base(descriptor);
    if (descriptor.cacheName !== 'mca') return cache;
    return {...cache, async getCached() {
      const value = await cache.getCached();
      if (value.mca == null) return value;
      const expires = sessionExpiresAt(value.mca.access_token);
      return expires - Date.now() >= minimumMs ? value : {...value, mca:undefined};
    }};
  };
}
