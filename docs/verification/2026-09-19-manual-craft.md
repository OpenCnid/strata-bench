# Explicit visible-recipe manual crafting — September 19, 2026

Operator-only development evidence. M0.3b.3.1d.1/.2 are **implemented_unverified**;
authentic execution remains .3. SPEC v0.2.3/D09 and Forge capability minor 13
declare the added route. No aggregate test/gate or pack support is passed.

## Behavior

The earlier JEI query could expose player-visible recipes while the only crafting
routine required recipe-book membership. `craft` now accepts an explicit nullable
`recipe_selection` containing the returned JEI `query`, `source_generation` and
initial page `revision`. Omitted/null selection preserves the existing book route.
The scoped action envelope, window/revision and observation/lease checks remain
mandatory. Mineflayer rejects a JEI selection before crafting input.

Native preparation repeats that focused, bounded player-visible query and checks
the initial generation/revision and selected supported ID before accessing its
native recipe object. Execution rechecks generation, visibility, selected object
and exact definition. Book membership changing after a successful craft is not
itself a definition change. Hidden/missing/unsupported recipes, runtime reloads,
changed definitions and page shifts that remove the selected recipe fail closed.
There is no fallback to a global recipe lookup, another backend or book transfer.

`GameRecipeGrid` allocates one ingredient set using only the 36 main/hotbar slots
in the current supported player/crafting menu. At most 4,096 search visits handle
competing alternatives; shaped blanks and shapeless layout are preserved. It
executes normal pickup, place-one and optional return clicks, awaiting server
feedback after every click. Exact cursor and non-result slot checks reject gifts,
component changes and even resource-conserving unrelated rearrangements. Derived
output preview changes are allowed during filling; output is never taken then.

The existing `GameCrafting` output/remainder routine verifies the final selected
recipe and output, exact consumption and actual native remainders before storing
them. Repetitions refill only that recipe. Empty grid/cursor, known serializers,
permissions and conservative output/remainder space checks remain prerequisites.
No automatic gathering, dependency search, bulk crafting, quick-move, drop,
JEI transfer hook or automatic recovery is added. Counts remain 1–64 executions
within the existing ten-second action deadline, not a guarantee all repetitions
will fit. Clicks, refreshes and active feedback waits consume primitive budget;
source checks and planning consume real execution time. Cancellation/exhaustion
retains partial cursor/grid effects and consumed costs without replay.

Policy: `visible-recipe-manual-grid-feedback-search4096/1`. Source selection policy:
`query-generation-initial-revision-and-current-definition/1`. The new schema field
is generated across public ActionBatch/RpcRequest and their dependent bindings.
Strict Java, TypeScript and Python validation rejects unknown source fields and
invalid query/generation/revision values. Forge's capability digest changes;
campaign admission remains disabled.

## Executed checks

Environment: Windows; Node **24.19.0**, Python **3.12.14**, pinned Temurin
17.0.20.1+1, Forge 43.4.23 / Minecraft 1.19.2 official mappings; JEI common API
11.8.1.1034 from the preceding query work. All menu and recipe effects below are
synthetic; native compilation and real HTTP/JVM transport are not live pack proof.

| Command/procedure | Actual result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 173 Java tests, zero failures/errors/skips; final build succeeds. |
| `npm test` with explicit JVM/classpath/guardian environment | 115 Node tests pass, zero failures/skips; 45.825 s. |
| `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py tests/test_contracts.py tests/test_gameplay_package.py -q` with explicit JVM/classpath | 78 pass, zero skips; 22.57 s. |
| Ruff on changed contracts/native client/tests | Pass. |

Ten new manual-grid tests cover waiting for feedback at every step; returning the
unused stack; repeated output/remainder handling; competing alternatives; shaped
empty cells; 3x3 nine-ingredient fill; shapeless allocation; unavailable resources,
dirty cursor/grid and permission rejection; gift/component/rearrangement faults;
source loss/cancel/exhaustion; wrong final output; and the search bound. The 3x3
case performs 26 ordinary clicks and 52 charged click/refresh primitives without
taking an output. Three selection tests bind source/query/revision, distinguish
book unlock from source drift, and reject unknown/hidden/unsupported selection.

The actual TypeScript/Python-to-HTTP-to-JVM fixtures accept the new action shape
and preserve a single journaled dispatch. Their synthetic generic motor does not
validate native JEI behavior; the manual motor is exercised separately over the
independent menu simulation. Existing book-action requests also pass. Mineflayer's
craft routine rejects the JEI field with zero clicks or primitive emissions.
The full Node suite retains guarded synthetic JVM fault stops: freeze 500 ms,
worker kill 42 ms, worker hang 1,974 ms, parent kill 25 ms. These are process-fixture
timings, not Minecraft watchdog qualification.

## Evidence and limits

Candidate client JAR SHA-256:
`7151fffbed4744a2b516c6d9503d3ebcb329bde0694733b400aa8815aa5b4cf4`.
It is built and **uninstalled**. Private evidence root:
`C:\Users\Darian\.strata\evidence\2026-09-19-manual-craft-01`.
Compiler/build/test/lint logs, copied XML and source files/hashes, the JAR hash and
collector are retained there. No proprietary installation or account material is
copied into the repository. No desktop input, real-game action or model inference
was dispatched. The Java compile retains existing deprecation warnings.

A fresh read-only E9E window capture after implementation (recorded 09:13 UTC)
still shows the Windows Security/OpenJDK network permission prompt over the
multiplayer screen. No window input or activation was sent. The computer-use
skill's referenced guidance prohibits acting on security permission requests;
the existing operator handoff remains pending while independent work continues.

Required next: deploy and qualify .1c/.1d.3 in exact E9E, including actual JEI UI
visibility, expert craft, server consumption/remainders, changed menu/recipe,
cancel/deadline/uncertain feedback and independent reference parity. Repeated JEI
source checks need real client latency/watchdog qualification; cooperative query
limits cannot preempt a blocked upstream call. Full-menu refresh still lacks a
causal nonce and retains its live ordering/ambiguity gate. Conservative empty-slot
requirements, custom ingredients/serializers, modded containers, machine energy/
fluid and quests remain explicit limitations and required later adapter work.
No synthetic result closes T03/T06/T07/G0, and the original Mineflayer/E9E
handshake failure remains recorded. **$0 inference dispatched.**
