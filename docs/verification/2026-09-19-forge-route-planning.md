# 2026-09-19 delivered-state route planning

Operator-only. Partial M0.3b.1b.2b.2b; F01/F06/F09/F16,
N01/N02/N04/N06/N08, C09/C15, T01/T03/T06/T07. This is development
implementation and synthetic verification, not an authentic movement pass.

## Implemented behavior

[GameRoute](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRoute.java)
implements deterministic four-neighbor breadth-first search for level walking.
It has a 16-block radius, 512 expansions, 4,096 distinct cell lookups, 64 waypoints
and a 20 ms computation deadline. It returns a complete route or an error, never
a partial route presented as success. The planner has no mutation or world API.
Unknown cells are barriers. Each edge checks a conservative swept body prism
with a 0.025-block margin and continuous support beneath its full footprint.
Rectangular subdivision detects gaps between supporting faces; checking only
the corners would miss those gaps. Native collision boxes must be finite,
nonempty, contained in their own cell and limited to 16 per cell.

[NativeCollisionView](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeCollisionView.java)
owns a copy of at most 1,024 delivered BlockStates. Its BlockGetter has no Level,
Entity, socket or raw-world fallback. Missing cells, future captures, captures
older than 30 seconds, fluid-bearing states, unlisted IDs and unexpected block
classes cannot resolve geometry. Block-entity and dimension-height queries reject.
The development allowlist is deliberately explicit: air/cave air/void air,
stone/cobblestone/dirt/coarse dirt/grass, oak/spruce planks and stone/oak slabs,
with exact expected classes and ordinary friction/speed/jump factors. Native
shape calls use an entity-free context. This allowlist is a candidate requiring
loaded-pack qualification; it is not evidence that modded geometry is supported.

`NativeGameRuntime.planMove` connects the delivered map and the same elapsed
clock used by captured observations. It resets connection/body changes first,
then requires a standing, grounded, non-riding, non-swimming survival body.
It prepares a route only. The public ten-action catalog is unchanged and
`move_to` remains unsupported. There is no movement input, teleport, implicit
digging, placement, equipment change or resource planning.

## Executed checks and retained failure

Environment: Windows 11, pinned Temurin JDK 17.0.20.1+1, Forge 43.4.23 /
Minecraft 1.19.2 compilation artifacts. Command from `java/`:

```powershell
.\gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
```

- Final build/reobfuscation: **115 Java tests passed**, no failures, errors or
  skips, 22 seconds. Twelve additions comprise eight synthetic planner tests,
  three native-view boundary tests without bootstrapped game state and one
  observation-clock test. Planner cases cover deterministic routes, fractional
  endpoints, detours/corner cutting, unknown intermediate cells, headroom,
  narrow gaps, support holes/unions, level slab geometry, invalid inputs,
  reader failure, timeout/expansion limits and cache invalidation between plans.
- An earlier attempt to bootstrap real block classes inside plain JUnit failed
  before its native assertions: Forge NetworkEvent lacked the no-argument
  constructor normally installed by its runtime transformations. That run had
  **111 passes and one initialization failure**. Its log, original test source
  and failure XML remain archived. It is not counted as native collision evidence.
- The actual block-shape assertions are retained in the opt-in
  [ClientCollisionProbe](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientCollisionProbe.java).
  Its 13 checks run on the client thread after Forge loading, without joining a
  world or sending input. They include native air/stone/slab shapes, waterlogged
  rejection, age/identity/missing-cell negatives and a constructed route using
  native shapes. **This probe has not run.** Its constructed route would still
  not establish movement effects, observed-world filtering or runtime timing.
- Earlier delivered-map Node/Python checks retain their separate
  [103 Java / 21 Node / 27 Python scope](2026-09-19-forge-delivered-map.md).
  No new Node or Python rerun is claimed for this subsequent private planner.

Private source hashes, logs, test XML and built JAR:
`%USERPROFILE%/.strata/evidence/2026-09-19-forge-navigation-02/`.
Final JAR SHA-256:
`7f30ca7496ee25102c759be3da75ac0f858edfc16e08f6246032fdb65432e0a4`.
It has not been installed. The running client still uses the previously recorded
read-only `c2218c6c…` build. No desktop input, game launch or inference occurred
in this planner change.

## Native probe procedure and remaining work

For the next authorized dedicated client launch, create a new private evidence
directory outside the repository and game profile, then set the JVM property
`-Dstrata.collisionProbeDirectory=<absolute-existing-private-directory>`.
The one-shot probe writes and forces a bounded `collision-<uuid>.json` containing
the exact client JAR hash, both candidate policy IDs, all case results and an
aggregate result. Missing opt-in means no probe. This does not grant action
authority or connect to a server. Preserve results with the exact pack inventory.

The Windows Security prompt still needs user handling before live UI work can
resume. Full M0.3b.1b.2b.2b remains in progress: expand and qualify geometry and
modded collision under M0.3b.3. Steps, jumps and vertical transitions currently
reject. M0.3b.1b.2b.2c still requires ordinary controls, local rechecks, charged
active ticks, damage/obstruction/deadline/cancel handling and authentic route
effects. Neither this implementation nor a passing native shape probe closes
T03 or any release gate.

## Subsequent loaded-runtime evidence

The [September 19 minor-34 probe](2026-09-19-native-collision.md) now passes all
13 cases on the actual E9E/Forge client, with 20 disconnected read-only checks
and bounded base-guardian stop. This is constructed-state native integration;
world motion and the remaining geometry scope above are still unqualified.
