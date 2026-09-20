import { forgeCapabilities } from './forge_capabilities.js';
import { ForgeLane } from './forge_lane.js';
import type { Journal } from './journal.js';
import { NativeGameClient } from './native_game.js';
import { digest, requireThat } from './protocol.js';
import type { GameLane } from './server.js';
import type { WorkerConfig } from './worker_config.js';
import type { ForgeGuardReady } from './forge_guard.js';

export async function workerLane(c: WorkerConfig, journal: Journal, guard?: ForgeGuardReady): Promise<{lane: GameLane; capabilities: unknown}> {
  if (c.schema === 'strata/ForgeDevelopmentWorker/2') {
    const client = NativeGameClient.fromFile(c.connection_file);
    requireThat(client.connection.fingerprint === c.native_fingerprint, 'CAPABILITY_MISSING');
    requireThat(guard && guard.connection_digest === digest(client.connection)
      && guard.body_fingerprint === c.body_fingerprint && guard.campaign_id === c.campaign_id
      && guard.agent_id === c.agent_id && guard.epoch === c.epoch,'PROCESS_GUARD_REQUIRED');
    const manifest = forgeCapabilities(c.native_fingerprint); const capability = digest(manifest);
    journal.event('guard_binding',guard);
    const lane = await ForgeLane.connect(c,capability,client,journal,c.body_fingerprint,c.primitive_limit,c.max_wall_ms,
      guard.connection_generation);
    return {lane,capabilities:{...manifest,digest:capability,lease_id:c.lease_id,epoch:c.epoch}};
  }
  // The Forge executor must not pay Mineflayer's module/data initialization cost.
  // Neither backend is a fallback for the other; selection remains explicit.
  const [{ActionLane},{MineflayerBackend,ACTION_KINDS},{capabilityManifest,capabilityDigest}] = await Promise.all([
    import('./actions.js'),import('./adapter.js'),import('./capabilities.js')]);
  const backend = new MineflayerBackend({host:c.host,port:c.port,username:c.username,profilesFolder:c.auth_cache});
  return {lane:new ActionLane(c,capabilityDigest,backend,journal,ACTION_KINDS,c.primitive_limit,c.max_wall_ms),
    capabilities:{...capabilityManifest,digest:capabilityDigest,lease_id:c.lease_id,epoch:c.epoch}};
}
