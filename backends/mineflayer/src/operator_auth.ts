/** Operator entry point. No game connection, model call, or automatic browser login. */
import { parseArgs } from 'node:util';
import { resolve } from 'node:path';
import { lockCache, protectedCache, writePrivateJson } from './auth_cache.js';
import { Fault, requireThat } from './errors.js';

const emit = (value: unknown) => process.stdout.write(JSON.stringify(value) + '\n');
// The pinned provider includes console/debug paths containing raw provider errors.
// Keep this entry point's output explicitly selected, including on failure.
delete process.env.DEBUG;
for (const method of ['log','info','warn','error','debug'] as const) console[method] = () => {};
let timer: ReturnType<typeof setTimeout> | undefined;
try {
  const {values} = parseArgs({options: {cache: {type:'string'}, account: {type:'string'},
    'timeout-ms': {type:'string',default:'300000'}, 'prepare-only': {type:'boolean',default:false}}});
  requireThat(process.versions.node === '24.19.0', 'CAPABILITY_MISSING');
  requireThat(typeof values.cache === 'string' && typeof values.account === 'string', 'CONFIG_REQUIRED');
  const duration = Number(values['timeout-ms']);
  requireThat(Number.isSafeInteger(duration) && duration >= 1000 && duration <= 600000, 'CONFIG_RANGE');
  const cache = protectedCache(values.cache, true);
  const {authenticateAccount, accountBinding} = await import('./authentication.js');
  if (values['prepare-only']) {
    const unlock = lockCache(cache);
    try { accountBinding(cache, values.account, true); } finally { unlock(); }
    emit({status:'prepared', cache, authenticated:false, proves_gameplay_isolation:false});
  } else {
    const control = new AbortController();
    timer = setTimeout(() => {
      control.abort(); emit({status:'blocked',code:'AUTHENTICATION_TIMEOUT'});
      // Upstream polling has no complete AbortSignal contract. Terminate the
      // dedicated initializer process; a stale auth.lock requires operator review.
      process.exit(124);
    }, duration);
    const result = await authenticateAccount(cache, values.account, code => {
      requireThat(/^[A-Za-z0-9-]{4,32}$/.test(code.user_code) &&
        Number.isFinite(code.expires_in) && code.expires_in > 0, 'AUTHENTICATION_FAILED');
      const url = new URL(code.verification_uri);
      requireThat(url.protocol === 'https:' && ['microsoft.com','www.microsoft.com','login.live.com'].includes(url.hostname)
        && !url.username && !url.password, 'AUTHENTICATION_FAILED');
      const prompt = resolve(cache, 'operator-login.json');
      writePrivateJson(prompt, {verification_uri: url.href, user_code: code.user_code,
        expires_at: new Date(Date.now() + Math.min(code.expires_in*1000, duration)).toISOString(),
        instruction:'The operator must complete sign-in. Never forward this file to gameplay agents.'});
      emit({status:'awaiting_operator_auth',prompt_file:prompt});
    }, control.signal, true);
    // Keep the actual account identity in the protected directory, not tool logs.
    writePrivateJson(resolve(cache, 'operator-result.json'), {profile_id:result.profile.id,
      profile_name:result.profile.name, authenticated_at:new Date().toISOString()});
    writePrivateJson(resolve(cache, 'operator-login.json'), {status:'completed'});
    emit({status:'authenticated',cache,account:values.account,proves_gameplay_isolation:false});
  }
} catch (error) {
  emit({status:'blocked',code:error instanceof Fault ? error.code : 'AUTHENTICATION_FAILED'});
  process.exitCode = 1;
} finally { if (timer) clearTimeout(timer); }
