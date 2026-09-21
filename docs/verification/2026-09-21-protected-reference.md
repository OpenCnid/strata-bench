# M0 protected ReferenceLauncher integration

September 21, 2026. Operator-only. Partial M0.2c.3b.2b.3.2; F04/F09/F10/F13/F16,
N01/N04/N06/N08, C12/C24, partial T01/T06/T07/T10/T13 and G0.

## Implementation

`ProtectedReferences` binds a strict `ProtectedReferencePlan/1` to fresh private
evidence and a fresh protected workspace. Its durable instance/workspace intent
precedes preparation. The production continuation seals the newly prepared
world while the same namespace/input handles remain held, then invokes the
actual `ReferenceLauncher` with `PrivateReferenceLaunch/4` and live custody.
The outer transaction cannot reach STOPPED until preparation, launch,
participant checks and custody release complete. No JSON/result reconstructs
live custody, and the legacy pair entrypoint rejects this new profile.

The protected launcher creates a private pipe authority and stages only its
version-4 descriptor. Keys, claims, spool paths, private sealing inputs and
participant reports stay outside the child workspace. The native gate and
actual connecting JVM token are checked through the held Job. The protected
path does not produce the legacy direct-key/spool configuration.

`OwnedCli` supplies the sole log readers and Job observer. Its optional bounded
line reader signals server readiness while the process is still running; the
launcher does not race a second reader or observer. Existing participant
readiness/report leases and exact completion digest checks apply. Version-4
abort scope includes the full launch digest, custody ID and helper pin; a
version-3 request cannot masquerade as the same launch.
Live broker uncertainty stops launcher admission. After recording the failure,
the launcher publishes a bound cooperative abort before native cleanup, without
replacing any existing abort. Endpoint cleanup is attempted even if custody
cleanup itself faults.

Candidate import now additionally requires the complete protected lifetime,
matching plan/setup/spool bindings and closed stopped custody. A clean server
shutdown cannot bypass a failed participant receipt. Complete raw streams from
an uncertain parent remain unavailable for import. Existing report schemas and
scoring-disabled semantics are preserved.

This version deliberately admits only the declared synthetic JVM profile.
Authentic E9E preparation/runtime exposure and the owned real-client driver are
the next part of the same M0 child. This is actual native integration using
synthetic world/events/participant data, not authentic Minecraft or gameplay
execution evidence. The selected Codex/Dovetail runtime is unchanged.

## Native evidence and retained failure

Private prefix: `C:/Users/Darian/.strata/evidence/2026-09-21-protected-reference-`.
The pinned Codex executable and Temurin 17.0.20 use existing sandbox enrollment.
Preparation copies pinned fixture classes/libraries and synthetic files through
the native Java writer; all runtime launches use the production orchestration,
seal, launcher, participant and telemetry implementations. The external test
driver submits an explicitly synthetic completion report, never a gameplay
execution certificate. `participant_execution_verified` and scoring remain false.

| Case | Result |
|---|---|
| `01` retained failure | Preparation and seal complete, with normal 10/10 preparation termination. The old abort-scope whitelist rejects the new launch schema with `REFERENCE_ABORT_PROFILE` before broker/server dispatch. The instance remains UNCERTAIN/reserved. |
| `02` changed profile | Explicit version-4 abort support permits the complete path. Preparation 10/10 and server/gate 12/12 signal, active zero, complete logs, exit 0/no force. Participant receipt completes, three authenticated records/4,327 bytes inspect, and candidate import is idempotent/unscorable. |
| `03` wrong receipt | Deliberately changed readiness challenge yields `REFERENCE_PARTICIPANT_SCOPE`. Server/gate shutdown is normal 12/12 and the three-record stream is complete, but the parent remains UNCERTAIN and import rejects. |
| `04` missing stop | Participant receipt completes, but the synthetic JVM omits server_stopped. Broker retains two records/3,386 bytes and its consumed claim as UNCERTAIN. Server/gate exits 1 with 12/12 signaled, active zero, complete logs/no force. `WRITER_CUSTODY_TERMINAL_UNCERTAIN` blocks the parent and import. |
| `05` live telemetry fault | Explicit injection after the second durable event changes the live broker to UNCERTAIN. The launcher detects `REFERENCE_TELEMETRY_UNCERTAIN`, durably records it, publishes the matching server-monitor abort and stops the owned tree. No participant readiness is published. All 12/12 signal, active zero, complete logs, deliberate force/exit 125. Two records and the consumed claim remain; import rejects. |

Reopening all five stores and trying the original instance with a different
preparation ID, workspace and output paths rejects before dispatch. Exact table
rows/outbox events and claim/spool hashes remain unchanged. The final import
checks run against preserved streams: case 02 returns the same report, cases
03/04/05 reject, and case 01 has no stream. Raw failures are retained privately.
No Minecraft, model request, game listener or desktop input was used.

## Focused verification and next dependency

**40 distinct selected Python checks passed:** 17 protected schema, abort,
lifetime and corrupt-binding controls; 11 custody controls; 12 selected legacy
abort/owned-cleanup regressions. The initial protected/custody run passed 23;
the final protected selection passed 17/1.74 s, and the legacy selection passed
12/0.42 s. Ruff and diff checks pass. The positive native profile is not rerun
after the import-only hardening; preserved-stream reinspection verifies that
change. The final live-uncertainty/cooperative-abort change has the distinct
case-05 native fault control. No broad suite or unchanged authentic trajectory
was repeated.

The private 354-file source/evidence inventory has SHA-256
`8def1eb5989c152770997dfa3300ae00eaffa7a3a488547896479d0be30066a8`;
it precedes this final manifest-reference insertion. Actual staged-file scans
across all five workspaces find no signing-key bytes/hex, private key path or
private spool path. This is an artifact audit, not a substitute for the remaining
access-isolation tests. Prior append-only history, 288 unique milestone IDs and
local links pass inspection. No Java process or listener on ports 25565–25580
remained at final inspection.

Read-only inspection of the previous authentic profile establishes the next
finite requirements: 600-second server window, 120-second graceful stop,
400-second participant window, 1,540 immutable files/646,731,537 bytes and a
104-file/35,295,178-byte sealed fixture. Its server used telemetry 0.3.5; the
new pipe-capable 0.3.6 is built but uninstalled. This metadata does not authorize
adopting the progressed old world. Prepare from the preserved initial fixture
and pinned software, maintain custody, declare the required server token/network
and runtime capability changes, and integrate the owned real-client driver.
Then qualify a changed authentic reference and its setup/history/control evidence.

The original $10 and $0.7554 uncertain hold are unchanged; no accounting reset,
refund or model replay occurred. Sibling-read/original loopback failures,
failed 500-ms samples, five effective-file failures, Mineflayer/E9E
incompatibility and full scorer/provenance/recovery/soak/capacity/pilot gates
remain. **M0 is incomplete; G0 fails; G1–G5 are not run.** Required M0–M6 and
conditional M7/extensions remain intact.
