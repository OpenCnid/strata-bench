import test, { type TestContext } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync, linkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { EventEmitter } from 'node:events';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { generateKeyPairSync } from 'node:crypto';
import type { Client, ClientOptions } from 'minecraft-protocol';
import { accountBinding, authenticateAccount, workerAuthentication, type TokenProvider } from '../src/authentication.js';
import { lockCache, protectedCache, readPrivateJson, strictCacheFactory, writePrivateJson } from '../src/auth_cache.js';

const fixture = () => ({token:'SYNTHETIC-SECRET',profile:{id:'a'.repeat(32),name:'SyntheticAvatar',skins:[],capes:[]},
  entitlements:{items:[],signature:'fixture',keyId:'fixture'},
  certificates:{profileKeys:{private:{},public:{},expiresOn:new Date(Date.now()+60000)}}} as unknown as
    Awaited<ReturnType<TokenProvider>>);
const provider: TokenProvider = async () => fixture();
const control = () => new AbortController();
const ignored = () => { throw Error('Unexpected device request'); };

function directory(t: TestContext) {
  const root = mkdtempSync(join(tmpdir(), 'strata-auth-test-'));
  t.after(() => rmSync(root, {recursive:true,force:true}));
  return protectedCache(join(root, 'cache'), true);
}

test('real filesystem cache protection, exclusive auth and atomic cache updates', async t => {
  const cache = directory(t);
  const unlock = lockCache(cache);
  assert.throws(() => lockCache(cache), /AUTH_CACHE_IN_USE/); unlock();
  assert.equal(protectedCache(cache), cache);
  const store = strictCacheFactory(cache, 'avatar1')({username:'avatar1',cacheName:'live'});
  assert.deepEqual(await store.getCached(), {});
  await store.setCached({token:'SYNTHETIC-SECRET'});
  await store.setCachedPartial({expires:42});
  assert.deepEqual(readPrivateJson(join(cache,'live.json'), false), {token:'SYNTHETIC-SECRET',expires:42});
  assert.throws(() => strictCacheFactory(cache,'avatar1')({username:'avatar2',cacheName:'live'}), /AUTH_CACHE_INVALID/);
  assert.throws(() => strictCacheFactory(cache,'avatar1')({username:'avatar1',cacheName:'../outside'}), /AUTH_CACHE_INVALID/);
  protectedCache(cache); // Actual Windows child ACL / POSIX file mode check.
});

test('corrupt and hardlinked caches reject without reset or directory fallback', async t => {
  const cache = directory(t);
  const path = join(cache,'live.json'); writeFileSync(path,'{broken',{mode:0o600});
  const store = strictCacheFactory(cache,'avatar1')({username:'avatar1',cacheName:'live'});
  await assert.rejects(store.getCached(), /AUTH_CACHE_INVALID/);
  assert.equal(readFileSync(path,'utf8'),'{broken');
  linkSync(path,join(cache,'alias.json'));
  assert.throws(() => readPrivateJson(path,false),/UNSAFE_PATH/);
  assert.throws(() => writePrivateJson(path,{}),/UNSAFE_PATH/);
});

test('an existing cache cannot be adopted under another unbound identity', t => {
  const cache = directory(t);
  writePrivateJson(join(cache,'live.json'),{token:'SYNTHETIC-SECRET'});
  assert.throws(() => accountBinding(cache,'avatar1',true),/AUTH_CACHE_INVALID/);
  assert.equal(existsSync(join(cache,'account.json')),false);
});

test('weakened native cache permissions reject before any provider call', t => {
  const cache = directory(t);
  if (process.platform === 'win32') {
    const icacls=join(process.env.SystemRoot!, 'System32/icacls.exe');
    execFileSync(icacls,[cache,'/grant','*S-1-1-0:(OI)(CI)R'],{stdio:'pipe',windowsHide:true});
  } else {
    // This branch is exercised only on a POSIX host; no Windows mode-bit fiction.
    execFileSync('chmod',['755',cache]);
  }
  assert.throws(()=>protectedCache(cache),/AUTH_CACHE_PROTECTION_FAILED/);
});

test('profile binding, missing certificate and account switching fail closed', async t => {
  const cache = directory(t);
  await authenticateAccount(cache,'avatar1',ignored,control().signal,true,provider);
  assert.equal(accountBinding(cache,'avatar1').profile_id,'a'.repeat(32));
  assert.throws(() => accountBinding(cache,'avatar2',true),/AUTH_ACCOUNT_MISMATCH/);
  await assert.rejects(authenticateAccount(cache,'avatar1',ignored,control().signal,true,async () => {
    const result = fixture(); result.profile.id = 'b'.repeat(32); return result;
  }), /AUTH_ACCOUNT_MISMATCH/);
  await assert.rejects(authenticateAccount(cache,'avatar1',ignored,control().signal,false,async () => {
    const result = fixture(); result.certificates!.profileKeys.expiresOn=new Date('2000-01-01'); return result;
  }), /MINECRAFT_CERTIFICATES_UNAVAILABLE/);
  assert.equal(accountBinding(cache,'avatar1').profile_id,'a'.repeat(32));
  assert.equal(existsSync(join(cache,'auth.lock')),false);
});

test('real pinned certificate decoder supplies nested Date expiry and signing keys', async t => {
  const require = createRequire(import.meta.url);
  const Manager = require('prismarine-auth/src/TokenManagers/MinecraftJavaTokenManager.js');
  const {publicKey, privateKey} = generateKeyPairSync('rsa', {modulusLength:2048});
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async () => new Response(JSON.stringify({
    keyPair: {publicKey:publicKey.export({type:'spki',format:'pem'}),
      privateKey:privateKey.export({type:'pkcs8',format:'pem'})},
    publicKeySignature:Buffer.from('synthetic-signature').toString('base64'),
    publicKeySignatureV2:Buffer.from('synthetic-signature-v2').toString('base64'),
    expiresAt:new Date(Date.now()+60000).toISOString(), refreshedAfter:new Date().toISOString(),
  }), {status:200,headers:{'content-type':'application/json'}});
  const certificates = await new Manager({}).fetchCertificates('synthetic-token');
  assert.ok(certificates.profileKeys.expiresOn instanceof Date);
  assert.equal(certificates.profileKeys.private.type, 'private');
  assert.equal(certificates.profileKeys.public.type, 'public');
  const cache = directory(t);
  await authenticateAccount(cache,'avatar1',ignored,control().signal,true,
    async () => ({...fixture(),certificates}));
  assert.equal(accountBinding(cache,'avatar1').profile_id,'a'.repeat(32));
});

test('cancelled authentication does not bind an account or leave a running cache writer', async t => {
  const cache = directory(t); const abort = control();
  await assert.rejects(authenticateAccount(cache,'avatar1',ignored,abort.signal,true,async () => {
    abort.abort(); return fixture();
  }), /abort/i);
  assert.throws(() => accountBinding(cache,'avatar1'),/AWAITING_OPERATOR_AUTH/);
  assert.equal(existsSync(join(cache,'auth.lock')),false);
});

test('long startup lifetime is requested and rechecked after provider work before account binding', async t => {
  const cache=directory(t);
  let requested:number|undefined;
  const session=(seconds:number)=>`e30.${Buffer.from(JSON.stringify({exp:Math.floor(Date.now()/1000)+seconds})).toString('base64url')}.c3ludGhldGlj`;
  await assert.rejects(authenticateAccount(cache,'avatar1',ignored,control().signal,true,
    async (_a,_c,_cb,minimum)=>{requested=minimum;return {...fixture(),token:session(60)};},1200000),/MINECRAFT_SESSION_TOO_SHORT/);
  assert.equal(requested,1200000);
  assert.throws(()=>accountBinding(cache,'avatar1'),/AWAITING_OPERATOR_AUTH/);
  assert.equal(existsSync(join(cache,'auth.lock')),false);
  await authenticateAccount(cache,'avatar1',ignored,control().signal,true,
    async ()=>({...fixture(),token:session(7200)}),1200000);
  assert.equal(accountBinding(cache,'avatar1').profile_id,'a'.repeat(32));
});

test('worker handoff connects once with the verified profile and sanitizes provider errors', async t => {
  const cache = directory(t);
  await authenticateAccount(cache,'avatar1',ignored,control().signal,true,provider);
  const client = new EventEmitter() as Client;
  let ended = false; client.end = () => { ended=true; };
  let connected = 0;
  const options = {username:'avatar1',connect:() => { connected++; }} as ClientOptions;
  const done = new Promise<void>(resolve => client.once('session',() => { resolve(); }));
  workerAuthentication(cache,'avatar1',control().signal,provider)(client,options);
  await done; await new Promise(resolve => setImmediate(resolve));
  assert.equal(connected,1); assert.equal(ended,false); assert.equal(client.username,'SyntheticAvatar');
  const failed = new Promise<Error>(resolve => client.once('error', resolve));
  workerAuthentication(cache,'avatar1',control().signal,async () => { throw Error('SYNTHETIC-SECRET'); })(client, options);
  assert.equal((await failed).message,'AUTHENTICATION_FAILED');
  assert.equal(connected,1); assert.equal(ended,true);
});

test('worker never exposes or accepts a device prompt; fencing prevents a late connection', async t => {
  const cache = directory(t);
  await authenticateAccount(cache,'avatar1',ignored,control().signal,true,provider);
  const client = new EventEmitter() as Client; client.end=()=>{};
  let connected=0;
  const options = {username:'avatar1',connect:()=>{connected++;}} as ClientOptions;
  const blocked = new Promise<Error>(resolve => client.once('error',resolve));
  workerAuthentication(cache,'avatar1',control().signal,async (_a,_c,callback) => {
    callback({user_code:'SECRET-CODE',device_code:'SECRET-TOKEN',verification_uri:'https://microsoft.com/link',expires_in:60,interval:5,message:'SECRET'});
    return fixture();
  })(client,options);
  assert.equal((await blocked).message,'AWAITING_OPERATOR_AUTH');
  const abort=control(); const fenced = new Promise<Error>(resolve=>client.once('error',resolve));
  workerAuthentication(cache,'avatar1',abort.signal,async()=>{abort.abort();return fixture();})(client,options);
  assert.equal((await fenced).message,'AUTHENTICATION_FAILED'); assert.equal(connected,0);
});

test('operator prepare-only command creates no credentials and rejects repository storage', t => {
  const cache = directory(t);
  const cli = new URL('../src/operator_auth.js',import.meta.url);
  const output=execFileSync(process.execPath,[fileURLToPath(cli),'--cache',cache,'--account','avatar1','--prepare-only'],{encoding:'utf8'});
  assert.equal(JSON.parse(output).authenticated,false);
  assert.throws(()=>protectedCache(process.cwd(),true),/FORBIDDEN/);
  assert.equal(existsSync(join(cache,'live.json')),false);
});
