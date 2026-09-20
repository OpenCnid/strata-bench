# 2026-09-19 native delivered-map authority

Operator-only. Scope: M0.3b.1b.2b.2a and the existing native observation/delivery
lane; partial F01/F06/F09/F16, N01/N02/N04/N06/N08, C09/C15,
T01/T03/T06/T07 under G0/G1/G2. No movement or authentic gate passes.

## Behavior

[GameObservedMap](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameObservedMap.java)
separates captured native states from delivered planner knowledge. The native
runtime retains immutable BlockState values only for cells in the existing
filtered capture, with matching public block IDs. This is private collision
input preparation: no raw properties, NBT, block entities, chunks, registry
dumps or new public fields are exported.

Captured scenes are limited to four, each at most 16,384 cells. A scene is not
planner authority. `GamePages` resolves a page to its private scene identity,
using the same dimension/expiry/eviction checks as ordinary page reads. The
durable lane first forces the delivery journal entry, then calls the native
promotion hook, and only afterward acknowledges action-observation authority.
A journal failure cannot promote a page; a promotion failure fences and releases
the lane. An identical delivery ID does not invoke promotion twice.

Promotion validates the entire delivered page before changing the map. Only its
at most 128 listed cells are eligible; each coordinate and ID must match that
captured scene. Unknown/invented/duplicate/fractional cells and wrong scene
dimension/time/revision reject. Old pages cannot overwrite newer delivered
states. Equal capture time uses state revision as the tie-breaker; conflicting
private states at identical time/revision reject. Re-delivery does not refresh
age or eviction order.

The map retains at most 1,024 delivered cells, evicting oldest entries. Returned
map snapshots are immutable; native BlockState values are immutable. Fresh
connection/body observations and lane rearming reset both captured and delivered
states. This memory does not refresh public observation age or let an old action
bypass the lane's 2-second initial-observation requirement. It has no raw-world
reader fallback.

## Executed checks

Windows 11; pinned Node 24.19.0, Python 3.12.14, Temurin JDK 17.0.20.1+1;
Minecraft 1.19.2 / Forge 43.4.23 compile artifacts. All new geometry/state values
in tests are explicitly synthetic and do not establish collision conformance.

- Pinned Gradle client test/build/reobfuscation/classpath generation: **103 Java
  tests passed**, zero failures/errors/skips, initially 24 seconds and 22 seconds
  after the final connection-generation refinement. Twelve new tests cover
  captured/undelivered separation, immutable ownership, atomic page rejection,
  old/new/tied observations, scene/reset/dimension/expiry bounds, 1,024-cell
  eviction, journal-before-promotion ordering, duplicate delivery and failure
  fencing. Final review also made connection-object replacement independently
  reset native observations/increment generation, even if player/level references
  have not changed yet. That native lifecycle case still needs real-game evidence.
  Existing settings, action and path-provider tests also passed.
- `node --test dist/tests/forge.test.js`, with explicit Java/classpath and Python
  guardian: **21 passed**, zero skipped, 42.067 seconds. Existing synthetic
  worker/JVM routing and fault tests retain one input intent and no replay.
  Native freeze / worker kill / worker hang / parent kill stopped their disposable
  JVMs in **498 / 40 / 1742 / 36 ms** from the respective injection. These are
  synthetic process results, not timing evidence for Minecraft.
- `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py
  tests/test_gameplay_package.py`: **27 passed**, zero skipped, 16.35 seconds,
  using the explicit pinned JVM fixture. No broader Python/Node rerun is claimed.

Private logs/XML/source hashes:
`%USERPROFILE%/.strata/evidence/2026-09-19-forge-navigation-01/`.
Built JAR SHA-256:
`b1601850dde8e43f6fc76b2b7c00ef262349ebafa426588c7fe537642dbcd98d`.
It was **not installed**. The running read-only client retains the previous
`c2218c6c9ae2e1e4a7e6f216d9fd16f084404d38bcebf0f47ccca17a24f462ce`
JAR and its separate [live startup evidence](2026-09-19-forge-live-api.md).

## Remaining work

Movement stays unsupported in the ten-action candidate. M0.3b.1b.2b.2b must
consume this delivered map through filtered, qualified collision access and a
fixed bounded planner. Native shape functions must not query hidden neighbors,
block entities or a raw level fallback. M0.3b.1b.2b.2c must connect ordinary
movement controls, precondition rechecks, charged ticks, obstruction/damage
stops, deadline/cancel/release and authentic effects. Retain exact modded collision
qualification under M0.3b.3. The map foundation is not a substitute for these.

No desktop input, live JAR change, new game launch or inference occurred during
this change. A fresh read-only window inspection confirmed the live E9E client
and the same Windows Security dialog; no dialog input was sent. Connected live
checks still await user handling. Other M0–M6 requirements and all open gates
retain their scope.
