# Paired modded block reference — September 19, 2026

Operator-only. Private saves, account/session material, raw observations and
evaluator scripts remain outside source/gameplay workspaces.

Scope: M0.3b.1b.4, M0.3b.2c.3c.2b.2c.1 and the existing guardian trial
M0.3b.2c.3c.2b.2b.2; F01/F06/F09/F10/F13/F16,
N01/N02/N03/N04/N05/N06/N08; C09/C14/C15/C18/C19;
partial T01/T03/T06/T07/T10/T12/T13. All remain incomplete; no aggregate gate
pass or research/campaign admission follows from a bounded operator trial.

## Procedure and profile

This follows the [offline saved-block reader](2026-09-19-saved-block-reference.md)
and [first bounded worker/stop pass](2026-09-19-stop-boundaries.md), preserving
every previous failure. Official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23,
JDK 17.0.20.1, Node 24.19.0 and Python 3.12.14. Native client remains
`06f2998073e179c34610db7465e772125232140a9ac7980b45e9fdf7dfa9ac1c`.
Fresh campaign/lease scope; current 33 compiled broker pins and 97 bootstrap
pins. The 4 GiB heap, 854x480/30-FPS setting, 480-second client, 90-second worker,
600-second server plus normal-stop grace, and 500 ms guardian exit wait remain.

Private root:
`C:\Users\Darian\.strata\evidence\2026-09-19-paired-block-reference-01\worker-01`.
The server/client are dedicated installations; client uses the separate Windows
desktop. No shared-desktop input, provider inference or admin game command.

Before launch, the prior normal server stop and Java-process absence are checked.
Four Twilight Forest region files and the player save are copied, 17,604,736
bytes total. Stable file identity/size/modify/change timestamps and source/copy
hashes must match; read access time is recorded separately. Copies become
read-only in the protected private directory. These selected files are not a
complete checkpoint, an authenticated seal or an adversarial isolation boundary.

The first copy attempt rejected full `stat` equality, which also includes
read-sensitive access times. That attempt did not record the differing fields,
so its exact trigger remains unproven. The failed script and partial copy are
retained. The corrected copy passed before any game launch.

The scoped CLI checker selects a `twilightforest:mayapple` solely from its
current delivered observation, within the existing reach bound. It retains the
pre-dig observation, sends the ordinary dig action once, and requires a public
air observation afterward. Missing target/effect fails; no private save data
informs targeting. Existing look, terminal-request deduplication, active-use
cancellation and fenced-action rejection remain exercised.

After normal server stop, a second selected-file copy is compared using
the private saved-block reader. Target before/after, unchanged support, ordered
capture boundaries, observed-ID agreement and selected changed positions are
separate checks. The reader does not infer item-drop/resource conservation,
authenticated causal actor provenance or score eligibility.

## Execution result

The trial **fails** its action procedure. Native readiness succeeds in 176.266 s,
without identity retry. Twelve public calls pass look and known-terminal
deduplication, then the dig receipt becomes `unknown / ACTION_UNKNOWN`, with
release confirmed and resynchronization required. The checker sends stop-all;
it does not replay dig. Use/cancel and post-fence negative checks are not reached.

Independent before/after copies contain the same mayapple. All 128 pre-action
observed IDs match the before-save reference, and all 128 selected saved states
are unchanged afterward. The validated native journal has **zero dig intents
and zero dig primitives** for the failed request. These checks resolve the
persisted state; they do not turn the unknown action into a successful dig.
The original native error code was discarded by the broker's generic catch,
so the historical response cannot be reconstructed.

The guardian does stop successfully: job call 1.0083 ms, signaled wait 436.8138 ms,
unchanged 500 ms wait bound. Worker exits 0; the outer procedure exits 1 because
the gameplay checks failed. Client exits 125 before outer cleanup, no desktop
watchdog intervention. Client/check duration 278.094 s; server normal save/stop
422.875 s, exit 0, complete logs. This passing stop does not repair or erase
previous failed stops. Input desktop unchanged and temporary arguments retired.

Post-save copies total 17,604,716 bytes. The collector validates two action
records/four primitive charges, 12 native journal frames, eight supervisor
events and 287 telemetry records. Two 854x480 PNGs decode correctly; they were
not visually inspected in this run. Three saved-player pose comparisons pass.
All client/server processes are stopped; Strata inference remains $0.

The exact installed Twilight Forest 4.2.1518 `MayappleBlock` bytecode defines
its outline box as (4,0,4)–(13,6,13), in sixteenths of a block. The current
native motor aims at the block-cell center (height 8/16); from the recorded
eye position the ray stays above the 6/16 outline. This is a concrete geometry
defect and a plausible explanation of the rejection, **not a recovered native
error code**. Next fix bounded shape-aware aiming, retain private native failure
diagnostics without weakening unknown-action fencing, then repeat the relevant
fresh-scope conformance case. Full causal/resource/scoring gates remain open.

## Repair candidate, separate from the failed live run

SPEC v0.2.32 / Forge minor 34 records motor revision
`durable-intent-client-thread-nineteen-actions/2` and explicit
`observed-outline-centers64-local16/1` negotiation in Java/TypeScript/Python.
[GameBlockTarget](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameBlockTarget.java)
collects at most 64 finite positive-volume outline boxes, local coordinates
[-16,16]. Distinct centers are tried in stable nearest-first order, within the
current native pick range, using the ordinary player-context outline raycast.
Only an actual hit on the already-delivered target is accepted. Dig/interact
share this correction; the existing preconditions, single mutation lane,
primitive charges, no-replay rules and release limits stay intact.

[ForgeLane](../../backends/mineflayer/src/forge_lane.ts) now retains private
allowlisted native failure codes and act/status phase after its existing fencing
and release attempt. Unknown errors are unclassified, with no raw exception
message/stack. The public result remains unknown and requires resynchronization.
Diagnostic write failure cannot delay the release attempt or permit more input.
This cannot recover the old run's discarded native response.

Executed after all authentic trial processes stopped:

```text
gradlew.bat --offline :forge1192-client:test :forge1192-client:writeTestClasspath
npm.cmd run build
node --test dist/tests/forge.test.js
python -m pytest tests/test_native_game.py tests/test_gameplay_package.py -q
ruff check src/mcbench/native_game.py tests/test_native_game.py
```

- **439 Java tests pass**, no failures/errors/skips, Gradle build 25 s. Six new
  synthetic geometry tests include the actual audited mayapple dimensions and
  Minecraft AABB clipping: old cell-center ray misses, new center hits. Also
  full cubes, disjoint/occluded components, reach rejection, shape quota/invalid
  geometry, duplicate centers and immediate abort on probe failure.
- Initial TypeScript build fails in the new test's unchecked array indexing.
  Added an explicit presence assertion; the next build passes. Runtime behavior
  was not weakened to satisfy the compiler.
- **42 Node Forge tests pass in 67.987 s**, no skips/failures, with pinned
  Java/classpath/Python enabled. Five new fault cases prove typed/unclassified
  errors, status failure, private-string omission, release-before-diagnostic,
  diagnostic disk failure and no mutation replay. These JVM/process integrations
  have synthetic game behavior and are not new Minecraft trial results.
- **41 Python tests pass in 0.93 s**, including compiled TypeScript-to-Python
  capability agreement, old/missing/wrong target-policy rejection and the
  gameplay package check. Lint passes.

Candidate remains **implemented but unverified in the real game**. The installed
dedicated client is still minor 33; no authentic rerun or reliable-shutdown,
complete geometry/resource/scoring qualification is inferred from these tests.

Offline `:forge1192-client:jar`/reobfuscation also passes (11 s). Candidate SHA-256:
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
Private sibling `candidate-34/` archives the JAR, 439-test XML results, 16 source
snapshots and 33 compiled broker modules with hashes. Dedicated and original
CurseForge client JARs were checked unchanged; the new JAR is not installed.
Final code/broker hash checks, local links and diff whitespace checks pass.
