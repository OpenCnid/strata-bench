/** Trusted worker identity seam. Receipts are operator-only, never observations. */
import { mono, requireThat, utc } from './protocol.js';

export const PLAYER_IDENTITY_POLICY = 'authenticated-saved-player-binding/1';
export function profileId(playerUuid: string): string {
  requireThat(typeof playerUuid === 'string' &&
    /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(playerUuid),
  'AUTH_PLAYER_IDENTITY_INVALID');
  return playerUuid.replaceAll('-', '');
}

export class PlayerIdentity {
  private authenticated = false;
  private fenced = false;
  private sequence = 0;
  readonly expectedProfileId: string;
  constructor(readonly expectedUuid: string) { this.expectedProfileId = profileId(expectedUuid); }
  authenticate(id: string): void {
    try {
      requireThat(!this.fenced && !this.authenticated && id === this.expectedProfileId,
        'AUTH_PLAYER_MISMATCH');
      this.authenticated = true;
    } catch (error) { this.fenced = true; throw error; }
  }
  spawn(serverUuid: string): PlayerIdentityMatch {
    try {
      requireThat(!this.fenced && this.authenticated && serverUuid === this.expectedUuid,
        'AUTH_PLAYER_MISMATCH');
      return {expected_player_uuid:this.expectedUuid, authenticated_player_uuid:this.expectedUuid,
        connected_player_uuid:serverUuid, spawn_seq:++this.sequence, recorded_at:utc(), mono_ms:mono()};
    } catch (error) { this.fenced = true; throw error; }
  }
  close(): void { this.fenced = true; }
}
export interface PlayerIdentityMatch {
  expected_player_uuid:string; authenticated_player_uuid:string; connected_player_uuid:string;
  spawn_seq:number; recorded_at:string; mono_ms:number;
}
