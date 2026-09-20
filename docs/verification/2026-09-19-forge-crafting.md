# 2026-09-19 native recipe discovery and crafting

Operator-only. Partial M0.3b.1b.2b.3.1/.2, F01/F06/F09/F11/F16,
N01/N02/N03/N04/N05/N06/N08, C09/C15, T01/T03/T06/T07/T12.
Authentic expert recipe qualification (.3.3) and all release gates remain open.

## Implemented candidate

[NativeRecipes](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeRecipes.java)
reads the actual client book's known recipes. It filters known status before
inspecting definitions; exact lookup checks known status before manager access.
It requires the current manager's exact recipe object and accepts only exact
ShapedRecipe/ShapelessRecipe classes, matching native serializers and ordinary
simple ingredients. Namespaced modded item ingredients/results are read from the
actual definition/registries; no minecraft-data or other vanilla substitution.
Unknown/custom/special or unprojectable recipes return an unsupported ID entry.
There is no global recipe solution or evaluator lookup.

[GameRecipes](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipes.java)
bounds/sorts the projection: at most 32 recipes / 32 KiB per page, 64 alternatives
per ingredient, 9 grid cells, 10,000 inspected book entries / 4 MiB of definitions.
Pages carry a revision; callers must restart if it changes between integer-cursor
pages. Output contains ID/count, never private stack components/NBT. The native
response binds body/generation atomically; the broker checks them before exposing
the public page and journals the raw permitted source privately. The existing
`mcgame recipes --after 0 --json` now awaits that asynchronous backend operation.

[GameCrafting](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameCrafting.java)
executes one requested known recipe, repeated 1–64 times within the entire action's
10-second bound. The native recipe-book method fills one set through ordinary
player mechanics. Require an empty initial grid/result/cursor, the requested
window/revision, actual full-menu feedback, resource conservation and exactly one
item in each nonempty ingredient slot. Verify the requested recipe against the
filled grid and output; calculate actual native remaining items from an isolated
copy. Reserve separate empty own-inventory destinations and check their capacity
and permissions before the ordinary result pickup. Check exact server-confirmed
consumption/result/remainders, then confirm each storage transfer separately.

Recipe identity, definition, unlock status, menu and selected slot remain fenced
throughout. No resource collection, recipe chaining, drops, automatic inventory
rearrangement or rollback occurs. The conservative empty-slot requirement may
reject a craft that a player could finish through merging. Cancellation after fill
retains grid ingredients; stopping after output pickup retains its cursor stack.
The existing durable lane prevents replay and charges fill, clicks, refreshes,
feedback waits and final release. Missing/contradictory feedback stops continuation.
Full-menu feedback has no causal nonce; native ordering/no-op conformance remains
unverified. Receipts remain input-only, with fresh observations and explicit
uncertainty, not authoritative recipe-success assertions.

Java, TypeScript and Python now negotiate twelve actions, native policy
`durable-intent-client-thread-twelve-actions/1`, discovery policy
`player-book-exact-shaped-shapeless-pages32/1`, crafting policy
`known-recipe-book-fill-single-output-remainders/1`, and public capability minor 10.
Old native manifests reject. Campaign admission remains disabled. This is the
separately identified D06 Forge candidate; the Mineflayer/E9E failure is unchanged.

## Executed checks

Windows / Node 24.19.0 / Python 3.12.14 / Temurin JDK 17.0.20.1+1 /
Forge 43.4.23 compilation artifacts. Private logs, XML, source hashes and built JAR:
`%USERPROFILE%/.strata/evidence/2026-09-19-forge-crafting-01/`.

- Pinned Gradle client tests/build/reobfuscation/classpath generation:
  **144 Java tests pass**, zero failures/errors/skips, final build 21 seconds.
  Eighteen new tests cover bounded projections/revisions, missing resources,
  server-versus-predicted feedback, repeated consumption, remaining containers,
  capacity/permissions, malformed fills/outputs, stale state, interrupted emission,
  strict envelopes, real durable-lane cancellation/deadline/exhaustion and no replay.
  Native adapters compile, but these tests use synthetic menu effects.
- `npm run build` passes. Explicit pinned JVM/Windows guardian
  `node --test dist/tests/forge.test.js`: **23 pass**, zero skips, 43.369 seconds.
  Actual HTTP/CLI/broker/JVM tests carry a synthetic expert recipe definition and
  craft envelope, reject malformed/private fields and stale recipe body generation,
  and preserve existing at-most-once and scoped-authority cases. Fixture execution
  is labeled synthetic; it does not exercise Minecraft recipe mechanics.
  Native-freeze / worker-kill / worker-hang / parent-kill injections stopped the
  owned disposable JVMs in **511 / 45 / 1741 / 24 ms**, with one intent/no replay.
  These timings are not Minecraft release certification.
- Explicit-JVM `uv run --frozen pytest tests/test_native_game.py
  tests/test_native_game_jvm.py tests/test_gameplay_package.py -q`:
  **38 pass**, zero skips, 19.25 seconds. Includes strict typed recipe responses,
  actual Python/Java recipe transport, craft envelope and gameplay packaging.
- Targeted Ruff passes. Failed attempts are retained: one Python negative test
  exposed a result-count limit overridden by an annotated base type; explicit
  strict bounded integers fix count/dimensions/cursor. Final cross-language review also rejected numeric 1/0 for recipe booleans before Pydantic literal coercion; a new negative test passes. Two Java lane assertions
  initially ran before its required deferred start; advancing the fixture clock
  fixed test setup without weakening assertions or changing lane semantics.

Final built JAR SHA-256:
`287a2c21cbcfa2855cebbd46c759df174c2fe51607e43db854ceaaedb593dcc2`.
It is **not installed**. No inference was dispatched and no game/server was started.

## Remaining qualification

A fresh read-only desktop capture still showed the Windows Security/Firewall
prompt over the dedicated client's multiplayer screen. No input was sent and the
old read-only JAR remains loaded. User handling of that dialog is still pending.

After it clears, deploy the candidate, run the native shape probe and connected
observation tests, then qualify movement/inventory/crafting and cancellation with
actual server/reference evidence. Prove the book's player-accessible semantics,
the exact expert recipe, remaining-item/mod-hook behavior and feedback ordering;
retain custom serializers/JEI discovery, broader menus, full collision/placement,
modded machines/energy/fluids/quests under M0.3b.3. Compilation, a synthetic expert
ID or a vanilla craft cannot pass those cases. Complete controller/aggregate
accounting, isolation, native host integration, soaks, capacity and scientific
milestones remain required. No M0–M6 milestone or T/G gate closes here.
