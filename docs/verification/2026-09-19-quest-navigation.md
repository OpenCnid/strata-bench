# Current quest-book state and navigation

2026-09-19. Operator-only. M0.3b.3.2.3c.3.2a, F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15, partial T01/T03/T06/T07/T12. No release gate closes.

The Forge development candidate now exposes `mcgame quest-screen --json` and
`quest_navigate` chapter/quest/back/close actions through the existing scoped
ActionBatch lane. SPEC v0.2.12, Forge minor 22 and
`durable-intent-client-thread-fifteen-actions/1` identify the implementation;
screen/navigation policy is `ftb-own-team-book-state-navigation/1`.

## Implemented behavior

The bounded screen read exposes only closed/book kind, visible current chapter
and quest IDs, source/screen generations and revision. Native object references
and the resize fingerprint stay private. It validates own-team membership,
non-editing source and the three exact FTB artifacts, then checks visibility
before IDs and detail access before a viewed quest ID. Two captures must agree;
source/screen/object replacement or layout change invalidates stale authority.
The observer has a cooperative 100-ms bound. The broker strips private body and
connection identity after verifying its own lease/body binding.

Chapter/quest requests name an entry in the exact returned catalog page, with
query, source generation and catalog revision, plus current screen generation
and revision. Hidden, inaccessible, stale or off-page selections reject. Native
target lookup visits at most 4,096 chapter and 4,096 quest entries and checks a
100-ms cooperative limit; it neither solves dependencies nor exports raw graph
state. It retains the selected native object and rechecks state around selection
and immediately inside the charged dispatch.

The exact installed bytecode confirms public `QuestScreen.open(QuestObject,false)`
is the ordinary chapter/quest link path. `onBack()` leaves quest details first;
from overview it uses ordinary close. The book hotkey invokes `closeGui(true)`.
The adapter calls these public callbacks once, then confirms the local resulting
screen/selection immediately and on the next tick. Selecting the same chapter
preserves FTB's no-op behavior, including any existing detail view. Cancellation
retains already-produced UI changes and charges; exceptions or changed state after
possible emission yield fenced/unknown outcomes with no replay.

Inspection found that Library's close callback also calls player container close.
The shared quest input guard now requires empty carried, 2×2 crafting-grid and
result slots, preventing this initial UI route from implicitly returning/dropping
crafting items. It still requires survival, idle hands, released mapped keys and
modifiers, and the own inventory menu. This guard is a declared initial restriction;
it does not satisfy occupied-grid lifecycle or server-resource conformance.

## Files and verification

- [Screen projection](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestScreen.java),
  [navigation motor](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestNavigation.java)
  and [native binding](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestNavigation.java).
- NativeQuests/runtime/protocol and GameBatch; Python/public generated contracts,
  native Python/TypeScript validators, Forge capability policy, scoped broker and CLI.
- [Java tests](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameQuestNavigationTest.java),
  [Python contract tests](../../tests/test_quest_navigation.py), actual JVM integration
  in [Python](../../tests/test_native_game_jvm.py) and the
  [scoped Node CLI](../../backends/mineflayer/tests/forge.test.ts).

Environment: Windows, Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1, Forge 43.4.23
compile target and the existing hash-checked external FTB Library compile-only JAR.

| Executed procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 257 Java pass, zero failures/errors/skips |
| `npm test` in `backends/mineflayer`, with explicit JVM/classpath and guardian Python | 126 pass, zero failures/skips |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py tests/test_quest_catalog.py tests/test_quest_text.py tests/test_quest_components.py tests/test_quest_menu.py tests/test_quest_navigation.py -q`, with explicit JVM/classpath | 230 pass, zero skips |

Eleven new Java cases cover the complete basic lifecycle, same-chapter behavior,
state identity/revision, malformed/changing/timed-out projection, hidden/off-page
or inaccessible catalog choices, selection races, refusal, strict requests,
durable deduplication/reopen, cancellation before/after effect and post-effect
uncertainty. Python/Node reject extra private fields and malformed state without
retry; a body-generation mismatch fences before public delivery. Stock Mineflayer
does not advertise or execute either quest action. Actual HTTP/JVM/scoped CLI
tests perform the complete open → chapter → quest → back → close sequence through
the real pure motors. **Their FTB/game/UI authority is synthetic.**

The first Node run had 124 pass and one failure: a new HTTP fixture omitted its
required JSON content-type header. The transport correctly rejected it. The
fixture was corrected; production validation was unchanged. A body-generation
negative was then added and the complete suite passed. Both logs are retained.
Java compilation/build succeeds with existing deprecation warnings.

Candidate JAR SHA-256:
`387c2d6aa51cf241d008f9c4aef97112964e1f2af3116d3b3c69af9e03fb59bd`.
The candidate is **uninstalled**, with no bundled FTB classes. Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-quest-navigation-01` (logs, exact
installed API bytecode, JUnit, source hashes and verification record).

## Remaining qualification

M0.3b.3.2.3c.3.2a is **implemented_unverified**. Initial native scope is the exact
book opened from gameplay with no previous-screen chain, context menu, active
drag/editor selection or hidden detail panel. Unknown GUI contexts reject; they
are not reported as closed. Other ordinary contexts and occupied crafting-grid
handling remain .3.2b, alongside task/item/choice menus and scrolling. Submission,
claims and server resource feedback stay .3.3. Full rich/choice/extension surfaces,
actual callback/class loading, UI layout/persistence/modifier/timing parity,
server/reference and process/network isolation remain unverified. Existing
Mineflayer/E9E T03/G0 failure and every aggregate gate remain unchanged.

A fresh read-only capture still showed Windows Security/OpenJDK covering E9E.
No input was sent; the existing computer-use skill handoff remains pending.
No new real game client/server/worker, model inference, soak, capacity test or
study started. Strata inference remains $0 dispatched.
