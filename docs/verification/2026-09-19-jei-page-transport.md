# Current JEI slot-page transport — September 19, 2026

Operator-only; exclude this report and private evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.2c is **implemented_unverified**. The copied render
operands now reach `mcgame recipe-page --json` through scoped `recipes.page`
and private native `recipe_page`. SPEC v0.2.20 records D06's partial observation;
Forge minor 28 retains eighteen actions. No authentic gate closes.

Affected coverage: F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial
T01/T03/T06/T07. Exact Mineflayer/E9E T03/G0 failure remains recorded.

## Supported contract

The no-argument route requires the actual origin-bound task recipe screen,
five exact FTB/XMod/JEI pins and the prior complete-frame/copy guards. It
revalidates visible own-team parent quest/task membership, source, screen and
copied content around projection. A defensive list copy prevents a mutable
provider from changing both sides of the comparison. Native reads enforce
250-ms frame age and a cooperative 100-ms projection limit; this does not
promise 250-ms freshness at final network delivery.

Public output declares policy `jei-task-drawn-slot-copies/1`, source `jei`,
`coverage:slot_draw_operands` and `complete:false`. Origin chapter/quest IDs,
source/screen generations, screen revision and a canonical content SHA-256
accompany copied layouts. Origin IDs do not identify the currently focused recipe.

Each layout has a category ID, clipping flag and ordered native slot indices.
Each slot has a role and either an empty/unsupported marker or a plain item/fluid
registry ID with a positive signed-32-bit amount. Empty/unsupported markers cannot
carry hidden data. Indices may have gaps only when clipping is explicit. Reject
unknown fields, coerced roles, invalid types/order, digest mismatches and overflow.
The full public envelope is bounded to 32 KiB, with at most 32 layouts and 128 slots
per layout; never silently truncate. Python and TypeScript independently validate
the native response and recompute its canonical digest.

The broker checks deadlines/leases/fences before and after transport, verifies
the bound body/connection, journals private evidence and removes native schema/body
metadata before delivery. Body replacement and stopping during a read prevent late
public delivery. There is no recipe/team selector, raw ingredient/source object,
private evaluator data or mutation authority. Stock Mineflayer rejects the route.

Sources: [native projection](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipePage.java),
[native view](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestRecipeView.java),
[Python boundary](../../src/mcbench/native_game.py),
[TypeScript boundary](../../backends/mineflayer/src/native_game.ts),
[broker](../../backends/mineflayer/src/forge_lane.ts),
[CLI](../../backends/mineflayer/src/cli.ts).

## Executed verification

Windows, JDK 17.0.20.101, Forge 1.19.2-43.4.23, exact external FTB Library
compile-only dependency and pinned JEI API. Java/classpath and guardian Python
were explicitly supplied for the cross-language suites; game/render authority
remains synthetic even where the real JVM/HTTP/scoped CLI is exercised.

| Check | Result |
|---|---|
| Gradle client test/build/writeTestClasspath | 333 Java cases; zero failures/errors/skips; 29 s |
| Selected native/contracts/records/quest/recipe Python suites | 285 passed; zero skips; 39.10 s |
| Initial full Node suite | 133 passed; zero failures/skips; 60.211960 s |
| Full Node suite after adding stop-during-read case | 134 passed; zero failures/skips; 59.499551 s |
| Final strict-role correction: TypeScript build and selected transport test | Build pass; one selected test passed; zero failures/skips; 0.755569 s |
| Schema export, generated TypeScript, changed Python Ruff | Pass |

Java adds seven projection/source/content/timeout cases. Python adds 23 cases
covering headers, raw payloads, bounds, order, digest and selector rejection. JVM
and scoped CLI lifecycle cases read item/fluid/empty/unsupported copies while
the synthetic task recipe screen is open and reject after close. Node adds
strict transport, changed-body and stop-during-read cases. Final review found
that `String(role)` could accept an array containing `input`; the validator now
requires a string and the transport test checks arrays, null, number, object and
unknown role with otherwise consistent hashes. The earlier full-suite result is
retained separately from this final targeted rerun.

Executed commands include the three Gradle tasks above, `uv run --frozen pytest -q`
for the fifteen named suites in the private manifest, `npm test`, and after the
final role change `npm run build` plus
`node --test --test-name-pattern='copied recipe page transport' dist/tests/forge.test.js`.
Existing Gradle/Java deprecation warnings remain.

The evidence collector verified all five installed artifact hashes, packaged
Mixin configuration, absence of bundled FTB/JEI classes, candidate installation
absence, exported request-schema equality and generated method presence. It
retained 32 source snapshots and checked 518 local links. Tracked `git diff --check`
passed with CRLF warnings only. Its initial duration check compared textual
formatting (`60211.960` versus `60211.96`); numeric comparison corrected that
collector-only failure without changing the measured result or rerunning tests.

Candidate SHA-256:
`64ccebf745b5c4519863df79415ec046ff848e7d71ee8d22b4f6698ca9c5f35d`.
Built, **uninstalled**. Private logs/JUnit/source snapshots and verification manifest:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-transport-01`.

## Remaining qualification

This exposes copied slot operands, not a complete recipe page or final-pixel
visibility proof. Category/page labels, rich/tagged/custom ingredients, decorators
and overlays remain .1b.2b. History/category/page controls remain .1b.3. Actual
Mixin application, visible-page parity, native inputs, mechanics, clocks/overhead,
server/reference and isolation remain .1b.4. Parent .1b.2 stays in_progress.

A fresh read-only E9E window capture still shows the Windows Security/OpenJDK
network-permission dialog. No input was sent; the outstanding operator handoff
remains. No real client/server/worker launch, inference, soak, capacity test or
study ran in this phase. Strata inference remains $0 dispatched. The long-horizon
goal stays active, M7 conditional, and all aggregate release gates remain open.
