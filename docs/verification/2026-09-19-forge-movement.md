# 2026-09-19 native level movement motor

Operator-only. Partial M0.3b.1b.2b.2c, F01/F06/F09/F11/F16,
N01/N02/N03/N04/N05/N06/N08, C09/C15, T01/T03/T06/T07/T12.
No authentic movement or release gate passes.

## Implementation

The Forge development candidate now accepts `move_to` through the same scoped
worker/CLI and durable native lane. Java, TypeScript and Python agree on eleven
actions, native policy `durable-intent-client-thread-eleven-actions/1`, the three
navigation/collision/movement policies and public capability minor 9. Movement
allows at most 30 seconds; other actions retain their 10-second cap. Tolerance
is a finite number greater than zero and at most one. Extra fields, nonnumeric
tolerance and excessive duration reject before input. Campaign admission remains
false; old capability manifests reject rather than silently gaining movement.

[GameMovement](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameMovement.java)
executes the existing delivered-map level route using ordinary camera yaw and
the forward KeyMapping. It starts at rest, waits eight neutral ticks before a
new forward press, and coasts to a settled waypoint before turning. Neutral,
walking and coasting decisions all pass through the lane's charged emitter;
terminal release is separately charged. This prevents the routine itself from
issuing a forward double tap inside vanilla's seven-tick sprint window. The
release-timing estimate uses the candidate surfaces' ordinary friction, but
does not mutate position, velocity, sprint flags or world state. Endpoint
precision can fail or time out; there is no position snap or hidden assistance.

Native preconditions require a standing, grounded survival player, ordinary
KeyboardInput and forward KeyMapping classes, no riding/swimming/flying/sprinting,
no use/dig in progress, and auto-jump/toggle-sprint/toggle-crouch disabled. These
settings are checked, not silently edited. Sampled logical input must match the
motor's last request, with no other pressed mapping, strafe/jump/sneak or modified
impulses. Owned inventory/window/selected-slot/food changes, health/absorption
loss, hurt state, horizontal collision, lost ground, changed body ticks, excessive
displacement/speed or stalled progress interrupt. The existing lane additionally
enforces body/generation/epoch/lease/deadline and primitive limits.

Each tick rechecks its short corridor against the copied delivered-state map and
its original age. No raw Level or new hidden cell enters planning. Natural
Minecraft physics still encounters actual terrain; changes outside delivered
knowledge are not secretly queried to find a replacement route. Collision/fall
or displacement feedback stops the motor. The support/clearance policy and its
limitations remain as described in the [planner report](2026-09-19-forge-route-planning.md).

Release clears registered keys, cached logical movement inputs and owned motor
state, as well as existing dig/use continuation. It retains physical momentum
and any already incurred effects. Cancellation, budget stop and ambiguous
outcomes preserve the journal and do not replay input. Receipts remain
`emitted`/`unknown`/`cancelled`/`failed`; reaching a predicted client coordinate
does not claim an authoritative server outcome.

## Executed verification

Windows 11 / Node 24.19.0 / Python 3.12.14 / Temurin JDK 17.0.20.1+1 /
Forge 43.4.23 compilation artifacts. Private logs, XML, source hashes and JAR:
`%USERPROFILE%/.strata/evidence/2026-09-19-forge-movement-01/`.

- Pinned Gradle client test/build/reobfuscation/classpath generation:
  **126 Java tests passed**, zero failures/errors/skips, final build 21 seconds.
  Eleven new tests exercise independent toy motion, settling before turns,
  charged neutral/walking/coasting ticks, no rapid re-press, unknown corridors,
  damage/absorption/context/collision/tick/displacement/stall failures, emitter
  failure and strict envelopes. Real durable-lane tests cancel a synthetic walk,
  exhaust its primitive budget without refund, expire its deadline and inject
  damage. Controls release and duplicate acceptance does not replay the intent.
- `npm run build` passed. Explicit pinned JVM/guardian
  `node --test dist/tests/forge.test.js`: **21 passed**, zero skipped,
  41.781 seconds. The real broker/JVM fixture accepts the new 30-second movement
  envelope exactly once; its effects are synthetic, not GameMovement/native
  gameplay evidence. Existing native freeze / worker kill / worker hang / parent
  kill injections terminated disposable JVMs in **492 / 42 / 1738 / 25 ms**,
  with one intent and no replay. These timings do not qualify Minecraft.
- Explicit-JVM `uv run --frozen pytest tests/test_native_game.py
  tests/test_native_game_jvm.py tests/test_gameplay_package.py`:
  **28 passed**, zero skipped, 17.59 seconds. Python/Java negotiation and the
  movement envelope agree; gameplay packaging retains its scoped projection.
- Targeted Ruff passed. Final native review additionally restricted the forward
  KeyMapping to its exact base class; the final Java suite was rerun afterward.
  Node/Python use synthetic runtime fixtures and do not qualify this native check.
  Pinned LocalPlayer bytecode confirms its seven-tick sprint-trigger counter and
  ordinary input-copy behavior; this inspection is not an effects test.

Final built JAR SHA-256:
`e0d658a7b2a1dc7421e55b75eb781caa2afb358d3e1115b20f7cbb643f6e562e`.
It is **not installed**. No Strata inference was dispatched.

## Remaining evidence and next action

The live client remains on the old read-only `c2218c6c…` JAR. A fresh read-only
window capture still showed the Windows Security prompt over its multiplayer
menu; no desktop input, installation change or game launch occurred here. User
handling is still pending. Once clear, deploy the candidate, run the 13-case
native shape probe, connected observation tests and guarded movement conformance
with server evidence. Check default settings explicitly before admitting a walk.

Authentic dynamics, start/stop latency, loaded input-mod behavior, precision,
freshness/filtering and server effects remain unverified. Slabs are only usable
along a level surface; stairs/jumps/vertical transitions and unqualified modded
geometry remain explicit limitations. Full T03, T07, T12 and G0/G1/G2 stay open.
Continue player-accessible crafting and exact expert recipe/container/machine
work independently; controller grants, aggregate accounting, runtime isolation,
soaks, capacity and scientific milestones retain all original requirements.
