# M0 private telemetry pipe candidate

September 21, 2026. Operator-only. M0.2c.3b.2b.3/.3.1; F04/F09/F10/F13,
N01/N04/N06/N08, C12/C24, partial T01/T06/T07/T10/T13 and G0.

## Implementation and scope

The protected writer cannot receive the legacy launcher's private key/spool
paths. `private_pipe.py`, `telemetry_pipe.py` and Java `PipeTelemetry` implement
the required broker component: signing, claims, durable evidence and the journal
stay in the operator process. The writer receives only its admitted producer
configuration and sequence/hash receipts. It receives no signing key, claim or
private spool path. The staged descriptor contains only the local pipe name,
controller PID/start time and challenge.

The Windows pipe is local-only, first-instance, non-inherited and single-client.
Its exact DACL uses specific read/write data/attribute rights for the sandbox
group and workspace scope, excluding create-instance permission. Overlapped
operations have a finite deadline; cancellation and submission share a lock,
and the handle remains retained until outstanding native I/O completes. A
connected but unbound peer is explicitly woken and rejected during close.
These choices follow Microsoft's [pipe access-rights contract](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights).

The broker obtains the [client PID from Windows](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeclientprocessid),
requires membership in the retained owned Job, matches the executable and live
handle, and verifies the actual user/group/restricting token before sending
configuration. Java independently checks the pipe's server PID, held process
creation time and liveness. Neither side accepts a self-reported PID as proof.
Only the lifecycle owner observes and retains Job members; the broker waits
at most 500 ms for that retained entry and never adopts an arbitrary PID.
The Java client requests identification-only SQOS and uses the existing pinned
JNA 5.12.1 dependency; no new dependency or runtime port was substituted.

A durable authority reservation precedes endpoint creation. The first native
event must match the retained process, sealed game/world/module and server
profile before consuming the one-use boot claim. Events require exact framing,
scope, sequence, schema and quotas. The existing HMAC envelope/claim format is
preserved. Each receipt follows file force and the committed durable cursor;
strict Java receipt parsing rejects coercion, duplicates and mismatches.
Missing stop, disconnect, timeout or ambiguity retains uncertainty and the claim.
No reconnect or request replay is provided. Full offline semantic inspection is
still required; a broker signature does not establish scorer/setup qualification.

Module candidate **0.3.6** adds `ForgeTelemetryConfig/4` for this descriptor and
`ServerStarted/7` for explicit `windows-owned-pipe/1` or legacy `private-file/1`
transport identity. Existing configuration/event versions remain supported with
their original module pins. Version 7 retains every version-6 setup, adjacency,
resource and clean-stop check; a transport declaration is not isolation proof.
The JAR is built but **not installed or tested in Minecraft**.

This is a prerequisite component for continuous protected server ownership.
`ReferenceLauncher` recognizes the new startup payload but still uses its legacy
dispatch/configuration path. The native controls below retain the prepared tree
while exercising the component through a private fixture hook; that hook is not
production launcher integration. A live custody object, pre-start native gate,
full launch/participant wiring and authenticated game reference remain required.

## Actual native controls and retained failures

Private directories have prefix
`C:/Users/Darian/.strata/evidence/2026-09-21-telemetry-pipe-`.
Every native case uses a fresh protected synthetic file preparation, existing
sandbox enrollment, the pinned Codex executable, Temurin 17.0.20 and a bounded
owned Java process. No model, Minecraft, game listener or desktop input is used.
The fixture uses the production spool/client with synthetic version-5 startup,
health and stop events; its reported ticks/online mode are not real game evidence.

| Suffix | Result |
|---|---|
| `01` | Both OS peer checks passed. Java then failed its first overlapped completion; zero signed events, UNCERTAIN. Native 10/10 terminated, exit 1. |
| `02` | Changed native-memory handling passes: three authenticated records, durable receipts, normal exit, native 10/10 terminated. |
| `03` | Foreign Job rejected before configuration or signing. Native 10/10 terminated, but the auxiliary helper retained 0 of 5 handles. This is incomplete cleanup evidence, not a fully qualified negative trial. |
| `04` | Wrong controller PID rejected by Java; no configuration sent, zero signed records, UNCERTAIN. Native 10/10 terminated, exit 1. |
| `05` | Missing stop rejected; two durable records and the consumed claim remain, broker UNCERTAIN and independent inspection rejects. Native 10/10 terminated, exit 1. |
| `06` | Final strict receipt/event path: three records/4,327 wire bytes, normal exit/no force, native 10/10 terminated, active zero and complete logs. Offline authentication/inspection passes; scoring stays false. |
| `07` | Readiness barrier fixes auxiliary history to 5/5, but waiting after native dispatch misses one native handle (9/10). Rejection is retained, complete trial qualification fails. |
| `08` | Start and observe the auxiliary helper before native dispatch, keeping native monitoring uninterrupted. Foreign Job rejected with no configuration or events; native 10/10 and auxiliary 5/5 fully signal, active zero, complete logs. Auxiliary termination is deliberately forced. |

The initial Java failure is consistent with JNA automatically writing stale
`OVERLAPPED` fields before querying completion. The changed implementation
initializes native memory once and passes its retained pointer thereafter,
following [JNA's structure synchronization contract](https://java-native-access.github.io/jna/5.12.1/javadoc/com/sun/jna/Structure.html).
The original failure had no precise Win32 subcode; retain that diagnostic limit.
No history threshold was relaxed to repair the negative fixture's scheduling.

Reopened authority stores 01–06 reject new-endpoint replay, preserve exact rows
and outbox counts and create no output/dispatch. This includes zero-event
uncertainty, a partial claimed stream and completed streams. The original raw
failures, class inventories, descriptors, fixtures, keys, spools and databases
remain private. Dispatch source is archived with 06; subsequent cancellation
and diagnostic changes have focused tests and the changed 08 native control.
The final owner-only Job observation change has a focused negative test; it
still needs coverage through the continuous-custody native integration.

## Focused checks

The affected Python files are `test_private_pipe.py`, `test_telemetry_pipe.py`,
`test_setup_facts.py` and `test_gameplay_package.py`. Explicit existing Windows
group and JRE/classpath variables enable the native checks. The main run has
47 passes and one initially skipped JVM fixture; running that fixture explicitly
adds its pass. New unbound-close, framing/path and unobserved-peer controls add
four checks: **52 distinct selected checks executed and passed**. The changed pipe/core
subset passes 13/3.38 s; the two framing/path checks pass 2/0.37 s. No broad suite.

Gradle ran targeted `TelemetryConfigTest`, `EventSpoolTest`,
`SpoolAuthenticationTest` and `PipeTelemetryTest`, plus `writeTestClasspath` and
`jar`/reobfuscation, offline with the pinned JDK: **13 tests, zero failures/errors**,
build successful. The first invocation misplaced `--tests` after the classpath
task and failed before compilation; the corrected task ordering is retained.
An initial Python fixture incorrectly combined module 0.3.6 with startup schema
5 (two failures/seven passes); preserve that failure. The fix keeps strict old
pins and adds version 7 with positive/negative setup regression coverage.
Ruff passes for affected Python files; the gameplay package excludes operator
material. The public source contains no keys, live descriptors, private instances,
compiled artifacts or native run logs.

Read-only durable accounting at **08:17:22 UTC** retains the original
10,000,000-microUSD authority, one D11 migration and **755,400 microUSD uncertain
exposure**, counted once. No model receipt retry, settlement, refund or reset.

Private 196-file source/evidence inventory: SHA-256
`24430b23ba6ffdef3aef7e4c80c921260787a1dd93dadbfc52b46cb368e1a610`.
The inventory precedes these final report/count corrections. Final process
inspection found no Java process or listener on ports 25565–25580.

## Next M0 action

Implement M0.2c.3b.2b.3.2: maintain preparation/root/input custody through the
actual launcher, bind a native pre-start gate before server mutation, and use
this channel for private configuration/evidence. Then qualify the changed
authentic setup/history and joint scorer controls. Do not adopt closed fixture
paths or repeat the completed positive craft trajectory without that change.

The prior sibling-read failure, original loopback failures, failed 500-ms
samples, five effective-file failures, Mineflayer/E9E incompatibility, unresolved
inventory and OAuth attempts, full scorer/provenance/recovery/soak/capacity/pilot
requirements remain. **M0 is incomplete; G0 fails; G1–G5 are not run.** Required
M0–M6 and conditional M7/extensions are unchanged.
