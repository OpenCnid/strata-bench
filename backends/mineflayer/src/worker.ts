import { fork, type ChildProcess } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { closeSync, fsyncSync, openSync, statfsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { workerConfig, type WorkerConfig } from './worker_config.js';
import { workerLane } from './worker_lane.js';
import { forgeCapabilities } from './forge_capabilities.js';
import { Journal } from './journal.js';
import { digest, errorBody, Fault, requireThat } from './protocol.js';
import { serve } from './server.js';
import { ForgeProcessGuard, SupervisorEvidence, type ForgeGuardReady } from './forge_guard.js';
import { WorkerStartup, WORKER_STARTUP_MS, WORKER_STARTUP_POLICY } from './worker_startup.js';
import { OPERATOR_STOP_ARGUMENT, WorkerControl } from './worker_control.js';
import { WorkerHealth } from './worker_health.js';

const repository = fileURLToPath(new URL('../../../../', import.meta.url));

async function child(c: WorkerConfig, token: string, initialized:()=>void, guard?: ForgeGuardReady): Promise<void> {
  const journal = new Journal(c.state_directory, c.epoch);
  let healthFailed = false;
  let requestStop: (() => void) | undefined;
  let metrics: WorkerHealth;
  try {
    metrics = new WorkerHealth(journal,c,() => {healthFailed = true; requestStop?.();});
  } catch (error) {journal.close(); throw error;}
  const {lane,capabilities} = await workerLane(c,journal,guard).catch(error => {
    try {metrics.close();} finally {journal.close();} throw error;
  });
  const server = await serve(lane,token,capabilities).catch(async error => {
    try {await lane.close();} finally {try {metrics.close();} finally {journal.close();}} throw error;
  });
  const address = server.address(); requireThat(address && typeof address !== 'string', 'INTERNAL_ERROR');
  const beat = setInterval(() => process.send?.({kind: 'alive', health: lane.health()}), 100);
  const disk = setInterval(() => {
    try {
      const fs = statfsSync(c.state_directory);
      if (fs.bavail * fs.bsize < 5 * 1024**3) void lane.fence('DISK_RESERVE_LOW').catch(stop);
    } catch { void lane.fence('EVIDENCE_UNAVAILABLE').catch(stop); }
  }, 1000);
  let shutdown: Promise<void> | undefined;
  const stop = () => {
    shutdown ??= (async () => {
      clearInterval(beat); clearInterval(disk); server.close();
      let code = healthFailed ? 1 : 0;
      try { await lane.close(); } catch { code = 1; }
      finally {
        try {metrics.close();} catch {code = 1;}
        journal.close(); process.exit(code);
      }
    })();
  };
  requestStop = stop;
  if (healthFailed) {stop(); return;}
  process.once('disconnect', stop); process.once('SIGINT', stop); process.once('SIGTERM', stop);
  process.on('message', m => {if (m === 'renew') void Promise.resolve(lane.renewLease()).catch(stop); else if (m === 'stop') stop();});
  initialized();
  process.send?.({kind: 'gateway_ready', port: address.port});
}

async function main(): Promise<void> {
  requireThat(process.versions.node === '24.19.0', 'CAPABILITY_MISSING');
  if (process.send) {
    // This pulse is actual child event-loop liveness. No config or capability is
    // available until the parent has validated bootstrap and attached the guard.
    const lostParent = () => process.exit(1);
    process.once('disconnect',lostParent);
    const starting = setInterval(() => process.send?.({kind:'startup_alive'}),100);
    process.send({kind:'bootstrap_ready'});
    process.once('message', (m: {config: WorkerConfig; token: string; guard?: ForgeGuardReady}) => {
      void child(m.config, m.token, () => {
        clearInterval(starting);process.removeListener('disconnect',lostParent);
      },m.guard).catch(() => {clearInterval(starting);process.exit(1);});
    }); return;
  }
  if (process.argv[2] === '--forge-capabilities') {
    requireThat(process.argv.length === 4, 'SCHEMA_UNSUPPORTED');
    const capabilities = forgeCapabilities(process.argv[3]!);
    console.log(JSON.stringify({...capabilities,digest:digest(capabilities)})); return;
  }
  if (process.argv[2] === '--check-vanilla-runtime') {
    requireThat(process.argv.length === 3, 'SCHEMA_UNSUPPORTED');
    // Load/compile dependencies before admitting a game process. No backend,
    // authentication callback, socket, journal or avatar is constructed here.
    await Promise.all([import('./actions.js'),import('./adapter.js')]);
    const {capabilityDigest}=await import('./capabilities.js');
    console.log(JSON.stringify({status:'vanilla_runtime_loaded',capability_digest:capabilityDigest,
      avatar_created:false,campaign_admission:false}));return;
  }
  const operatorControl=process.argv.length===4 && process.argv[3]===OPERATOR_STOP_ARGUMENT;
  requireThat(process.argv.length === 3 || operatorControl, 'SCHEMA_UNSUPPORTED');
  const c = workerConfig(resolve(process.argv[2]!),repository);
  requireThat(!operatorControl || c.schema==='strata/DevelopmentWorker/1','CAPABILITY_MISSING');
  const fs = statfsSync(c.state_directory);
  requireThat(fs.bavail * fs.bsize >= 5 * 1024**3, 'DISK_RESERVE_LOW');
  const token = randomBytes(32).toString('hex');
  let worker: ChildProcess | undefined;
  let executorExit:Promise<number>|undefined;
  let acceptExitEvidence=true;
  let guard: ForgeProcessGuard | undefined;
  const evidence = c.schema === 'strata/ForgeDevelopmentWorker/2' ? new SupervisorEvidence(c.state_directory,c.epoch) : undefined;
  let startup:WorkerStartup|undefined;
  let rejectBoot:((error:Fault)=>void)|undefined;
  let stopping = false;
  let forced = false;
  let health: NodeJS.Timeout | undefined;
  let lease: NodeJS.Timeout | undefined;
  let forcedKill: NodeJS.Timeout | undefined;
  let connectionReported = false;
  let fenceReported = false;
  let control:WorkerControl|undefined;
  const stop = () => {
    if (!stopping) {stopping=true; if (worker?.connected) worker.send('stop',() => {});}
    rejectBoot?.(new Fault('WORKER_STOPPED'));
  };
  const fail = (reason:string) => {
    if (forced) return;
    forced = true; stop();
    console.error(JSON.stringify(errorBody(new Fault(reason),null,c.epoch)));
    try {evidence?.event('supervisor_fault',{reason});} catch { /* Guardian stops when renewals end. */ }
    forcedKill ??= setTimeout(() => worker?.kill('SIGKILL'),250);
  };
  try {
    // Bootstrap has no avatar authority. Its deadline starts before fork, and
    // the worker wall budget includes bootstrap/guardian/initialization latency.
    startup = new WorkerStartup();
    const lifecycle = startup; const started = performance.now();
    worker = fork(fileURLToPath(import.meta.url), [], {stdio: ['ignore','ignore','pipe','ipc'], windowsHide: true});
    const activeWorker = worker;
    // stderr stays operator-only; no game/provider errors flow through the public endpoint.
    worker.stderr?.resume();
    let acceptBoot!:()=>void;
    const booted = new Promise<void>((yes,no) => {acceptBoot=yes;rejectBoot=no;});
    // A storage/spawn error may enter cleanup before the await is installed.
    void booted.catch(()=>{});
    const ended = new Promise<number>(resolveExit => activeWorker.once('exit',code => {
      if (acceptExitEvidence) {
        try {evidence?.event('worker_exit',{code:code ?? 1,forced});} catch {fail('EVIDENCE_UNAVAILABLE');}
      }
      rejectBoot?.(new Fault('WORKER_PROCESS_FAILED'));resolveExit(code ?? 1);
    }));
    executorExit=ended;
    if(operatorControl)control=new WorkerControl(process.stdin,
      {campaign_id:c.campaign_id,agent_id:c.agent_id,epoch:c.epoch,lease_id:c.lease_id},()=>{
        requireThat(lifecycle.phase==='active' && !stopping && !forced,'WORKER_OPERATOR_NOT_ACTIVE');stop();
      },fail);
    worker.once('error',() => fail('WORKER_PROCESS_FAILED'));
    evidence?.event('worker_started',{pid:worker.pid,epoch:c.epoch});
    health = setInterval(() => {
      if (!stopping && performance.now()-started >= c.max_wall_ms) stop();
      const failure=lifecycle.failure();
      if (failure || control?.expired() || performance.now()-started >= c.max_wall_ms+2250) {
        fail(failure ?? 'WORKER_DRAIN_TIMEOUT');activeWorker.kill('SIGKILL');
      }
    },50);
    lease = setInterval(() => {if (activeWorker.connected && !stopping && lifecycle.phase==='active') activeWorker.send('renew',() => {});},2000);
    worker.on('message', (raw:unknown) => {
    try {
    const m=lifecycle.receive(raw);
    if (m.kind==='bootstrap_ready') {
      evidence?.event('worker_bootstrap_ready',{policy:WORKER_STARTUP_POLICY,elapsed_ms:performance.now()-started});
      acceptBoot();
    }
    if (m.kind === 'gateway_ready') {
      requireThat(!stopping && !forced && (!guard || guard.usable),'PROCESS_GUARD_UNAVAILABLE');
      evidence?.event('worker_gateway_ready',{policy:WORKER_STARTUP_POLICY,elapsed_ms:performance.now()-started});
      const path = resolve(c.state_directory, `grant-${c.epoch}.json`);
      writeFileSync(path, JSON.stringify({url: `http://127.0.0.1:${m.port}/v1/game`, token,
        campaign_id: c.campaign_id, agent_id: c.agent_id, epoch: c.epoch})+'\n', {flag: 'wx', mode: 0o600});
      console.log(JSON.stringify({status: 'development_gateway_ready', grant_file: path,
        avatar_readiness: 'unverified', campaign_admission: false}));
    }
    if (m.kind === 'alive' && m.health.connected && !m.health.fenced && !connectionReported) {
      connectionReported = true;
      console.log(JSON.stringify({status: 'development_avatar_connected', epoch: c.epoch,
        fresh_observation_required: true, campaign_admission: false}));
    }
    if (m.kind === 'alive' && m.health.fenced && !fenceReported) {
      fenceReported = true;
      console.log(JSON.stringify({status: 'development_worker_fenced', epoch: c.epoch,
        reason: m.health.reason, new_epoch_required: true, campaign_admission: false}));
    }
    } catch (error) {fail(error instanceof Fault ? error.code : 'EVIDENCE_UNAVAILABLE');}
    });
    process.once('SIGINT',stop); process.once('SIGTERM',stop);
    await booted;rejectBoot=undefined;
    requireThat(!forced && !stopping && lifecycle.canRenew(),'WORKER_BOOT_UNAVAILABLE');
    let binding: ForgeGuardReady | undefined;
    if (c.schema === 'strata/ForgeDevelopmentWorker/2') {
      guard = new ForgeProcessGuard(c,digest(forgeCapabilities(c.native_fingerprint)),evidence!,
        () => !forced && lifecycle.canRenew(),fail);
      binding = await guard.ready;
      requireThat(!forced && !stopping,'PROCESS_GUARD_UNAVAILABLE');
    }
    lifecycle.initialize();
    evidence?.event('worker_initializing',{policy:WORKER_STARTUP_POLICY,elapsed_ms:performance.now()-started,
      startup_limit_ms:WORKER_STARTUP_MS});
    worker.send({config:c,token,guard:binding},error => {if (error) fail('WORKER_PROCESS_FAILED');});
    const code = await ended;
    process.exitCode = code === 0 && !forced ? 0 : 1;
    if(control){
      const receipt=control.receipt(code,forced);
      if(receipt.status==='fail')process.exitCode=1;
      const fd=openSync(resolve(c.state_directory,`supervisor-stop-${c.epoch}.json`),'wx',0o600);
      try {writeFileSync(fd,JSON.stringify(receipt)+'\n');fsyncSync(fd);} finally {closeSync(fd);}
    }
  } finally {
    control?.close();
    clearInterval(health); clearInterval(lease); clearTimeout(forcedKill);
    process.removeListener('SIGINT',stop); process.removeListener('SIGTERM',stop);
    if (worker && worker.exitCode === null && worker.signalCode === null) worker.kill('SIGKILL');
    if (guard) {
      try {await guard.stop();} catch {process.exitCode=1;}
    }
    clearTimeout(forcedKill);
    // Reap exit evidence after initiating both stops, never ahead of native
    // termination. Early bootstrap rejection otherwise closes the journal first.
    if (executorExit) {
      let timer:NodeJS.Timeout|undefined;
      const confirmed=await Promise.race([executorExit.then(()=>true),
        new Promise<false>(resolveWait=>{timer=setTimeout(()=>resolveWait(false),500);})]);
      clearTimeout(timer);
      if (!confirmed) {
        process.exitCode=1;evidence?.event('worker_exit_unconfirmed',{wait_ms:500});
      }
    }
    acceptExitEvidence=false;
    evidence?.close();
  }
}
try { await main(); } catch(e) { console.error(JSON.stringify(errorBody(e, null, null))); process.exitCode = 1; }
