# Initial Forge synchronization readiness — September 19, 2026

Operator-only. Scope: M0.3b.2c.3c.2b.2b.1; partial F01/F06/F09/F16,
N01/N02/N03/N04/N05/N06/N08; C02/C09/C15/C18; T01/T03/T06/T07/T12/T13.
No milestone or aggregate gate passes here. All earlier
[worker failures](2026-09-19-desktop-worker.md) remain retained.

## Source audit and repair

The pinned official-mapped Forge 1.19.2-43.4.23 class bytecode shows that
`ClientPacketListener.handleUpdateTags` runs `Blocks.rebuildCache`, updates item
search trees, and then posts `TagsUpdatedEvent`. Its recipe handler replaces
recipes, rebuilds recipe-book collections/search, then calls
`ForgeHooksClient.onRecipesUpdated`. The exact Forge event sources distinguish
client-packet tags from server-data-load events and expose the registry and
recipe-manager objects. This supports the new barrier; it does not establish
that all later mod initialization is complete or assign a cause to prior
failures without stack evidence.

[GameStartupReadiness](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameStartupReadiness.java)
now requires both current-connection synchronization events followed by a world
frame and an unobstructed admission tick with the same complete body.
[ClientGameBridge](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientGameBridge.java)
filters events by thread, tag cause and exact native source identity. It keeps
tracking after bridge creation, including a later join from the title screen.
Disconnect clears synchronization; respawn/dimension replacement needs another
frame. Ordinary menus preserve an already qualified body. Further tag/recipe
updates invalidate admission until a later frame; atomic datapack reload is not
claimed. Identity, observations and gameplay preconditions fail closed with
`GAME_INITIAL_SYNC_PENDING` while a connected body remains unqualified.

No action deadline, lease, guardian health interval, release bound, public action
shape or screenshot capability changes. The actual client JAR fingerprint changes.
Same-user desktop separation remains distinct from security isolation.

## Local verification

Executed with Java 17.0.20.1 and the pinned official FTB Library artifact:

```text
gradlew.bat --offline :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath
```

Build passed in 38 seconds: **433 Java tests, zero failures/errors/skips**,
including 13 lifecycle cases replacing the previous four. Cases cover missing
events, either packet order, premature frames, wrong-source events, overlays,
ordinary menus, reconnect/disconnect, replaced bodies, repeat updates and partial
joins. These are synthetic lifecycle cases, not authentic timing evidence.
Compiled reobfuscated bridge bytecode was retained for source-wiring inspection.
The gameplay-package exclusion check also passed: one test, 0.38 seconds.

Private root: `C:\Users\Darian\.strata\evidence\2026-09-19-forge-readiness-01`.
It retains pinned-source inspection, raw build log, all test XML, source snapshots
and candidate JAR SHA-256
`06f2998073e179c34610db7465e772125232140a9ac7980b45e9fdf7dfa9ac1c`.
Only the dedicated client copy was updated; the original CurseForge profile's
`f10e7ad6…` artifact remains unchanged. All 97 bootstrap pins and dedicated-copy
settings were rechecked before preparing the fresh read-only run. Its authenticated
session reserves at least 20 minutes and is rechecked immediately before launch.

## Authentic read-only trial

The new candidate connected to the official E9E 1.27.0 / MC 1.19.2 / Forge
43.4.23 server on the separate non-input desktop. Native readiness/identity
completed after 233.454 seconds. The read-only checker passed 2,745 world
assertions, ten transport-negative assertions and six post-disconnection assertions.
Ten subsequent identity reads all completed within the unchanged 500 ms bound,
with measured times of 47–125 ms. This run has no game actions or full worker-owned
Forge guardian; it uses the independently challenged base lifetime guardian.

Two 854×480 images were captured from Minecraft's own render target. Independent
PNG CRC, zlib, dimensions and scanline checks passed. Both were inspected and show
the rainy nighttime world, terrain/trees, crosshair, bow, hotbar and HUD. No OS
desktop image was used. Public screenshots remains false. Image correctness for
these frames does not qualify all GUI, pointer or physical-key behavior.

Client/check elapsed 263.563 seconds. The guardian confirmed process termination
in 359 ms; this forced client stop is not a clean checkpoint. The server saved and
stopped normally in 477.610 seconds total, exit 0 with complete logs. Its private
telemetry spool validates 287 records and the six expert furnace metadata
assertions, which are not player crafting or machine-effect proof. Input desktop
unchanged, client absence confirmed, temporary session arguments retired, all
97 bootstrap pins rechecked and three protected directories verified.

Private evidence is in `read-only/` under the root above. This is one successful
readiness trial, not a repeatability/latency certificate. Earlier failures remain.
The next `worker-01/` trial uses the observed new native/body fingerprints, a new
immutable authority/scope, 480-second client lifetime, 90-second worker lifetime
and 1,000-primitive ceiling; existing action/guardian deadlines stay fixed.
Authentic scoped worker actions, server-reference effects and full native
integration remain under test. No inference or campaign admission.

## First scoped worker trial: checker units and shutdown failure

`worker-01/` reached ready/fenced native state in 229.657 seconds, with no startup
identity timeout. Its independent Forge-aware guardian attached and the scoped
worker armed successfully. The public CLI submitted one look action; its terminal
receipt reports `emitted`, two emitted events, confirmed release and no resync.
The fresh result observation changed pitch from 0.0628316974 to 1.1644815677
**radians**. The checker incorrectly required a difference greater than `5`,
intending degrees, and reported `LOOK_EFFECT_MISSING`. It issued stop-all and
did not run deduplication, dig or use/cancel checks. Retain the original failed
result; do not retrospectively relabel its planned suite as passed.

The two captured game-buffer frames independently show the camera change and
passed bounded PNG decoding/visual inspection. A separate retrospective audit of
the final saved player data converts Minecraft degree axes to the API's documented
Mineflayer radians convention: saved rotation, position and dimension match the
last public pose. This supports the narrow look effect, not the unexecuted actions.
The next checker uses a five-degree threshold expressed in radians and chooses
an alternate target pitch using the same units. Saved-pose comparison also converts
axes/units before comparison. No game behavior or acceptance threshold was relaxed.

After its 90-second lifetime the executor exited normally, but the independent
guardian returned failure without a confirmed-stop receipt; the supervising
process exited 1. Its internal reason was discarded by the Node adapter, so the
precise cause is unresolved. Timing near the 500 ms stop wait does not prove that
particular cause. The native client was subsequently confirmed absent, exit 125,
before outer cleanup. No desktop-watchdog trigger occurred. The original failure
remains a failed shutdown check despite eventual process absence.

Total client/check time: 337.110 seconds. Server saved/stopped normally in
510.344 seconds, exit 0 and complete logs. Input desktop unchanged, arguments
retired. The collector validates 11 native journal frames, seven supervisor frames,
one action and four reconciled primitive charges, plus 321 telemetry records and
the expert furnace metadata assertions. No refunds, inference or campaign admission.

## Bounded guardian failure evidence

[forge_guard.py](../../src/mcbench/forge_guard.py) now uses the existing shared
sanitizer for failed receipts.
[forge_guard.ts](../../backends/mineflayer/src/forge_guard.ts) validates the exact
failed-event shape and bounded uppercase reason before retaining `guard_failed`
in the private supervisor journal. It still rejects the session, reports the
generic supervisor failure and never claims confirmed termination. Unknown fields,
raw exception/path text, malformed codes and a false successful-termination flag
cannot enter this event. No watchdog/lease/stop bound changes.

Actual verification: Node build passed; two targeted journal/negative tests pass
(0.490 seconds); six existing real-process/synthetic-game guardian integration
tests pass (38.287 seconds, zero skips/failures). They cover normal drain,
mismatched grants and native/worker/parent faults. Two Python main-failure cases
pass (0.23 seconds; seven unrelated tests deselected). These disposable JVM results
do not qualify real Minecraft shutdown timing. The broker/Python implementation
fingerprint changes; the native client JAR remains 06f29980….

## Corrected scoped trial: bounded checks pass, shutdown fails

`worker-02/` uses a new scope/authority, corrected checker and separately pinned
current broker bytes. Native readiness completes in 230.469 seconds with no
identity retry. The worker-owned Forge guardian attaches and the public grant
becomes available. The 16 CLI requests pass the planned narrow checks:

- Look changes the observed camera pose; the terminal receipt confirms release.
- Resubmitting that known terminal ID returns the same result without another
  action. No uncertain mutation is replayed.
- Reachable observed grass is targeted; dig returns `emitted`. Independent
  server block-change/resource verification remains unrun.
- Two-second held item use is cancelled while active, returning `cancelled`,
  confirmed release and required resynchronization. The fenced public observation
  marks the worker connection unusable; a subsequent action rejects with
  `LEASE_EXPIRED`. This does not establish the entire cancellation timing suite.

The executor drains normally after 90 seconds, but the guardian emits the now
retained `PROCESS_STOP_UNCONFIRMED`, termination_confirmed:false. The private
failed event arrives about 517 ms after the worker-exit record; the process
guard's existing 500 ms process-exit wait did not confirm termination. The
supervisor exits 1, so the overall trial is **fail** despite the CLI subset pass.
The exact underlying reason for slow process termination is unresolved; the first
worker trial's discarded inner cause cannot be reconstructed from this run.
The client is subsequently confirmed absent with exit 125, before outer cleanup.
No desktop watchdog fired and no deadline was relaxed.

Total client/check time is 335.500 seconds. The server saves/stops normally in
504.485 seconds, exit 0 and complete logs. The evidence collector validates three
action records, 14 reconciled primitive charges, 31 native journal frames, eight
supervisor frames, 318 telemetry records and the expert furnace metadata checks.
Three saved-player pose comparisons pass after proper unit/axis conversion.
Both 854×480 game-buffer PNGs pass decoding and visual inspection: the first shows
sky/clouds and the second the downward view after interaction, with ordinary HUD
and quest toast. This is not independent block/resource or quest-success scoring.

All three new clients/servers are now stopped; temporary argument files are
retired. Input desktop unchanged in every run; no OS input, inference or campaign
admission. Earlier records and real partial effects remain retained. The next
step is to investigate rendered-process termination latency without waiving its
bound, then complete independent block/resource, menu/machine and input evidence.
Full actions, isolation, accounting, soaks, capacity and every release gate remain
open. A successful CLI subset does not qualify the whole backend.
