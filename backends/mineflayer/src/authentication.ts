/** Trusted Microsoft authentication seam using the pinned protocol's supported callback. */
import prismarineAuth from 'prismarine-auth';
import type { Client, ClientOptions } from 'minecraft-protocol';
import { resolve } from 'node:path';
import { existsSync, readdirSync } from 'node:fs';
import { lockCache, protectedCache, readPrivateJson, strictCacheFactory, writePrivateJson } from './auth_cache.js';
import { Fault, requireThat } from './errors.js';
import { requireSessionLifetime, sessionCacheFactory, sessionLifetimeLimit } from './session_lifetime.js';

const {Authflow, Titles} = prismarineAuth;
export const authOptions = Object.freeze({flow: 'live' as const,
  authTitle: Titles.MinecraftNintendoSwitch, deviceType: 'Nintendo'});
type ProviderResult = Awaited<ReturnType<InstanceType<typeof Authflow>['getMinecraftJavaToken']>>;
// prismarine-auth 3.1.1's declaration puts expiry at the certificate root, but
// its runtime returns a Date at profileKeys.expiresOn. Pin the observed source
// contract here and test the real token-manager decoder, not a mirrored fixture.
type Result = Omit<ProviderResult, 'certificates'> & {certificates?: {
  profileKeys: {private: unknown; public: unknown; expiresOn: Date};
}};
type CodeCallback = NonNullable<ConstructorParameters<typeof Authflow>[3]>;
export type TokenProvider = (account: string, cache: string, callback: CodeCallback, minimumLifetimeMs?: number) => Promise<Result>;
const tokens: TokenProvider = async (account, cache, callback, minimumLifetimeMs = 0) => {
  const factory = sessionCacheFactory(strictCacheFactory(cache, account), minimumLifetimeMs);
  const flow = new Authflow(account, factory, authOptions, callback);
  return await flow.getMinecraftJavaToken({fetchProfile: true, fetchEntitlements: true,
    fetchCertificates: true}) as unknown as Result;
};

export function accountBinding(cache: string, account: string, initialize = false) {
  requireThat(/^[A-Za-z0-9_-]{1,64}$/.test(account), 'CONFIG_RANGE');
  const path = resolve(cache, 'account.json');
  const missing = !existsSync(path);
  const binding = readPrivateJson(path, initialize);
  if (missing && initialize) {
    requireThat(readdirSync(cache).every(name => name === 'auth.lock'), 'AUTH_CACHE_INVALID');
    const initial = {schema: 'strata/MinecraftAccount/1', account, profile_id: null};
    writePrivateJson(path, initial); return initial;
  }
  requireThat(Object.keys(binding).sort().join(',') === 'account,profile_id,schema' &&
    binding.schema === 'strata/MinecraftAccount/1' && binding.account === account &&
    (binding.profile_id === null || typeof binding.profile_id === 'string' && /^[a-f0-9]{32}$/.test(binding.profile_id)),
  'AUTH_ACCOUNT_MISMATCH');
  requireThat(initialize || binding.profile_id !== null, 'AWAITING_OPERATOR_AUTH');
  return binding;
}

export async function authenticateAccount(cachePath: string, account: string, callback: CodeCallback,
  signal: AbortSignal, initialize = false, provider: TokenProvider = tokens, minimumLifetimeMs = 0): Promise<Result> {
  sessionLifetimeLimit(minimumLifetimeMs);
  signal.throwIfAborted();
  const cache = protectedCache(cachePath, initialize);
  const unlock = lockCache(cache);
  try {
    const binding = accountBinding(cache, account, initialize);
    const result = await provider(account, cache, code => { signal.throwIfAborted(); callback(code); }, minimumLifetimeMs);
    signal.throwIfAborted();
    requireThat(typeof result.token === 'string' && result.token.length > 0 &&
      typeof result.profile?.id === 'string' && /^[a-f0-9]{32}$/.test(result.profile.id) &&
      typeof result.profile?.name === 'string' && /^[A-Za-z0-9_]{1,16}$/.test(result.profile.name),
    'MINECRAFT_PROFILE_UNAVAILABLE');
    requireThat(binding.profile_id === null || binding.profile_id === result.profile.id, 'AUTH_ACCOUNT_MISMATCH');
    if (minimumLifetimeMs > 0) requireSessionLifetime(result.token, minimumLifetimeMs);
    requireThat(result.certificates?.profileKeys?.private && result.certificates?.profileKeys?.public &&
      result.certificates.profileKeys.expiresOn instanceof Date &&
      result.certificates.profileKeys.expiresOn.getTime() > Date.now(), 'MINECRAFT_CERTIFICATES_UNAVAILABLE');
    if (initialize) writePrivateJson(resolve(cache, 'account.json'), {...binding, profile_id: result.profile.id});
    return result;
  } finally { unlock(); }
}

export function workerAuthentication(cache: string, account: string, signal: AbortSignal,
  provider: TokenProvider = tokens): (client: Client, options: ClientOptions) => void {
  return (client, options) => {
    void authenticateAccount(cache, account, () => { throw new Fault('AWAITING_OPERATOR_AUTH'); },
      signal, false, provider).then(result => {
      signal.throwIfAborted();
      // Same session/certificate handoff as minecraft-protocol 1.68.0 microsoftAuth.
      // The private cache factory prevents its default writable-directory fallback.
      const session = {accessToken: result.token, selectedProfile: result.profile, availableProfile: [result.profile]};
      Object.assign(client, result.certificates, {session, username: result.profile.name});
      Object.assign(options, {haveCredentials: true, accessToken: result.token, auth: 'microsoft'});
      client.emit('session', session);
      signal.throwIfAborted();
      requireThat(typeof options.connect === 'function', 'AUTHENTICATION_FAILED');
      options.connect(client);
    }).catch(error => {
      // Raw provider bodies can contain credentials, identifiers or nested errors.
      client.emit('error', new Fault(error instanceof Fault ? error.code : 'AUTHENTICATION_FAILED'));
      client.end('AUTHENTICATION_FAILED');
    });
  };
}
