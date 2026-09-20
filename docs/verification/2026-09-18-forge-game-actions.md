# 2026-09-18 native Forge action lane evidence

Operator-only. Scope: M0.3b.1b/M0.3b.2, F01/F06/F09/F11/F16,
N02/N03/N04/N05/N08, C09/C15/C18, T01/T03/T06/T07/T12, G0/G1/G2.
The previous goal turn made concrete progress with the read-only native API.
This change adds real implementation and synthetic integration evidence; it
does not qualify a Minecraft backend or close any aggregate test/release gate.

## Delivered implementation

- `GameActionLane` owns one client-thread motor and a process-locked, bounded,
  forced hash-chain journal. It binds immutable private authority/body/software
  identity, scopes, increasing epochs/sequences, six-second renewable leases,
  absolute/monotonic limits and recorded fresh observation delivery.
- Public ActionBatch fields and implemented kinds are strictly checked by
  `GameBatch`. A separate signed-number parser admits coordinates without
  relaxing unsigned sequences or the settings parser. Invalid timestamps,
  unknown fields, raw inputs, wrong scopes and unsupported mechanics reject.
- Ordinary native motors in `NativeGameRuntime`: camera look, bounded tick-based
  destruction, main-hand block interaction and native inventory pickup/quick-move.
  Targets require delivered block identity, current state/reach/hit checks or
  matching menu/revision/slot. No raw packet/admin/direct-destroy calls are added.
- Primitive intent is durable before invocation; ambiguous effects retain unknown
  counts and require resynchronization. Safety release remains available during
  budget/journal failure. Replay recovers pending requests as unknown; repeated
  identical IDs query prior status, including after expiry, and cannot emit twice.
- Reserved urgent HTTP queue for cancel/stop, drained before the motor; a rotating
  fence token prevents a previously queued rearm from crossing a stop. Native
  action acceptance waits a tick before input. Python mutation uncertainty retains
  action/request IDs and never causes an automatic POST retry.
- State revisions now change with projected state rather than read frequency;
  timestamp-only changes and the action's own bookkeeping do not invalidate CAS.

The native action API is opt-in via a private `game-authority.json`; the default
bridge stays read-only. Capabilities enumerate the exact four development actions
and retain `campaign_admission=false` and `conformance=unverified`. Native receipts
say `emitted`, not `completed`: neither server acknowledgment nor task success is
inferred from a client call. Each terminal action requires a fresh observation.

## Actual verification

Windows 11, Python 3.12.14, Temurin JDK 17.0.20.1+1, Gradle 8.8,
ForgeGradle 6.0.42, Forge 1.19.2-43.4.23 with official mappings. Existing build-input
hash checks ran; no dependency added. No game, account login or inference launched.

- Pinned `JAVA_HOME`; from `java/`:
  `./gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain`.
  **56 Java tests passed**, including **16 native lane cases**, five page cases,
  four visibility cases, two game HTTP cases and 29 retained settings/parser cases.
- With explicit `STRATA_CLIENT_TEST_JAVA/CLASSPATH` and
  `STRATA_SETTINGS_TEST_JAVA/CLASSPATH` pointing at the pinned JVM/generated classpath:
  `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py tests/test_native_settings.py tests/test_native_settings_jvm.py tests/test_gameplay_package.py -q`.
  **38 passed in 15.86 s; zero skipped**. This includes **six actual Python/JVM game
  HTTP cases**, four actual settings JVM cases, typed payload/uncertainty checks,
  and gameplay allowlist packaging.
- Targeted Ruff over both native Python clients and the game tests passed.
  Diff whitespace check passed. No unrelated full Python/Node suite was rerun.

Fault evidence covers durable intent before the synthetic motor, duplicate/altered
IDs, foreign scope/capability/lease, old epoch/sequence, valid initial zero sequence,
undelivered/stale/changed state, absolute and monotonic expiry, expired renewals,
queued cancellation, reserved cancellation capacity, queued stale rearm, body/
connection changes, lost emission acknowledgment, release failure, corrupt journal
tail, concurrent owner, changed budget authority, exhaustion and unrefunded attempts.

An actual synthetic JVM process was killed while its motor was executing. A new
process recovered the same journal with a fresh transport session, retained the
two attempted events, classified the action `unknown`, rejected the old epoch and
did not replay input. Another test lost a real HTTP acknowledgment and queried the
action through a new request without a second action POST. These prove properties
of the bridge/journal with a synthetic runtime, not real client crashes, native key
release timing, modded effects, or paired game/agent world restoration. The test
body deliberately resets on process startup and is not recovery-equivalence evidence.

Review found and corrected the queued-rearm cancellation race before claiming the
passing result. The ordinary action API cannot be enabled simply by editing a
finished/expired journal's limits: authority mismatch prevents reopening it.

Built client JAR SHA-256:
`14b24422f18ca155cca7788d105a70e2e7440bc723269a7e166b703955a2214b`.
Not installed in the live profile. Private test reports, source/artifact hashes and
scope receipt are under
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-game-actions-01/`.
No connection credentials or proprietary game files are included in that archive.

## Unresolved contract and next work

M0.3b.1b.1 and .2a are **implemented but unverified in-game**. M0.3b.1b and .2
remain partial. Native body binding and an operator token do not prove the public
worker's executor grants, actual model delivery or OS isolation. The gameplay
package still routes to its existing Mineflayer worker; the Forge private client
is excluded from that package. Native attempted-event counters are conservative
local accounting, not posted aggregate tool/body/model usage.

Next: M0.3b.2b scoped worker integration, including asynchronous confirmed release,
capability/source/body binding, actor lease handoff and private/public observation
mapping. M0.3b.2c must reconcile native events/clocks with host budgets and implement
external hung-client termination, storage archival and actual isolation evidence.
The client-thread watchdog cannot run while that thread hangs. Wall-clock restart
continuity, real latency, custom input consumers and exact-pack effects are unproven.

`move_to`, `place`, `equip`, `use_item`, `attack`, `interact_entity`, `craft` and
`chat` remain unsupported on this Forge candidate. Custom containers, player recipe/
quest APIs and expert machines remain M0.3b.3/M0.3.4–10 work. The exact Mineflayer
E9E T03/G0 failure remains recorded; the Forge candidate's authentic T03 is still
`not_run`. Desktop remains paused; no live profile modification or game launch.
