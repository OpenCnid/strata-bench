import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import type { Cache, CacheFactory } from 'prismarine-auth';
import { requireSessionLifetime, sessionCacheFactory, sessionExpiresAt } from '../src/session_lifetime.js';

const token = (exp: unknown) => `e30.${Buffer.from(JSON.stringify({exp})).toString('base64url')}.c3ludGhldGlj`;

test('session preflight rejects near-expiry, expired, unknown and malformed lifetimes without leaking tokens', () => {
  const now = 1800000000000;
  requireSessionLifetime(token(now/1000+1200),1200000,now);
  for (const expires of [now/1000-1,now/1000,now/1000+1199]) {
    assert.throws(() => requireSessionLifetime(token(expires),1200000,now),/MINECRAFT_SESSION_TOO_SHORT/);
  }
  for (const value of ['SECRET',token(null),token('1800001200'),token(1.5),token(1e100),token(-1)]) {
    assert.throws(() => sessionExpiresAt(value),error => error instanceof Error
      && error.message === 'MINECRAFT_SESSION_EXPIRY_UNAVAILABLE');
  }
  for (const minimum of [-1,1.5,3600001,Infinity]) {
    assert.throws(() => requireSessionLifetime(token(now/1000+1200),minimum,now),/CONFIG_RANGE/);
  }
});

test('pinned Minecraft token manager refreshes a suppressed token without resetting Microsoft/Xbox caches', async () => {
  const require = createRequire(import.meta.url);
  const Manager = require('prismarine-auth/src/TokenManagers/MinecraftJavaTokenManager.js');
  const near = token(Math.floor(Date.now()/1000)+60);
  let stored:Record<string,unknown> = {mca:{access_token:near,obtainedOn:Date.now(),expires_in:86400},marker:'preserved'};
  let resets=0, writes=0;
  const cache:Cache = {async getCached(){return stored;},async reset(){resets++;stored={};},
    async setCached(value){writes++;stored=value;},async setCachedPartial(value){writes++;stored={...stored,...value};}};
  const base:CacheFactory = () => cache;
  const filtered = sessionCacheFactory(base,1200000);
  assert.equal(filtered({username:'fixture',cacheName:'live'}),cache);
  assert.equal(filtered({username:'fixture',cacheName:'xbl'}),cache);
  const manager = new Manager(filtered({username:'fixture',cacheName:'mca'}));
  assert.equal(await manager.verifyTokens(),false); // Provider's own refresh decision, no network.
  assert.equal((stored.mca as {access_token:string}).access_token,near);
  assert.equal(resets,0);assert.equal(writes,0);
  const fresh=token(Math.floor(Date.now()/1000)+7200);
  await manager.setCachedAccessToken({access_token:fresh,expires_in:7200});
  assert.equal(await manager.verifyTokens(),true);
  assert.equal((await manager.getCachedAccessToken()).token,fresh);
  assert.equal(stored.marker,'preserved');assert.equal(resets,0);assert.equal(writes,1);
});
