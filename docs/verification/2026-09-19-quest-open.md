# Ordinary quest-book opening — implementation evidence

Date: 2026-09-19. Operator-only. M0.3b.3.2.3c.3.1; F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15; partial T01/T03/T06/T07/T12. No aggregate gate closes.

The Forge candidate now accepts `quest_ui` / `operation:open` through the existing
full ActionBatch and scoped `mcgame act` route. SPEC v0.2.11, Forge minor 21 and
`durable-intent-client-thread-fourteen-actions/1` identify the new implementation.
Opening policy is `ftb-own-team-open-screen-cas/1`. The previously recorded
Mineflayer/E9E failure is unchanged, and stock Mineflayer rejects this action.

## Behavior and boundaries

The request names `ftb_quests`, source generation and the expected root chapter
catalog revision. It cannot select a team, hidden quest, task, reward or arbitrary
callback. Native validation retains all three exact FTB artifact hashes and
the bound player/connection/file/own-team context. Require survival, no editing,
quests enabled, team unlocked, no existing screen/server container/carried stack,
idle hands and released mapped keys and modifiers. Recompute the bounded root
catalog before dispatch and reject changed source/revision.

The actual installed Quests bytecode confirms that public
`ClientQuestFile.openGui()` checks its disabled/locked state and constructs the
ordinary quest UI. This adapter calls that public method once; it does not invoke
the private implementation or write progress. A journaled, charged primitive
precedes the callback. Exact returned GUI/current ScreenWrapper identity, file,
source and normal context are verified immediately and on the next client tick.
An `emitted` receipt establishes only that local transition. A later catalog
progress revision alone does not trigger another open. Changed source/screen,
callback refusal or an exception after possible input yields an uncertain fenced
outcome. Existing cancellation, deadline, budget and durable deduplication rules
retain incurred costs/effects and never reopen automatically. Cancelling after
opening leaves that ordinary UI open.

Implementation:

- [Pure opening motor](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestOpen.java)
  and [native FTB binding](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestOpening.java).
- [Source binding](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuests.java),
  [runtime](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeGameRuntime.java),
  [strict batch](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameBatch.java).
- [Public contracts](../../src/mcbench/contracts.py), generated ActionBatch/RpcRequest,
  [native Python client](../../src/mcbench/native_game.py),
  [native TypeScript client](../../backends/mineflayer/src/native_game.ts) and
  [Forge capabilities](../../backends/mineflayer/src/forge_capabilities.ts).

## Executed verification

Environment: Windows, pinned Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1,
Forge 43.4.23 compile target; exact installed FTB Library supplied compile-only.
No FTB classes are bundled. The official exact Library Maven limitation and
hash-checked external dependency remain unchanged.

| Procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 246 Java tests pass, zero failures/errors/skips; build succeeds |
| `npm test` in `backends/mineflayer`, with explicit JVM/classpath/guardian Python | 123 pass, zero failures/skips |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py tests/test_quest_catalog.py tests/test_quest_text.py tests/test_quest_components.py tests/test_quest_menu.py -q`, with explicit JVM/classpath | 214 pass, zero skips |

Ten [new Java tests](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameQuestOpenTest.java)
exercise positive screen confirmation, source/catalog/permission/screen rejection,
recheck inside dispatch, callback refusal, uncertain post-effect failure, strict
selectors/integers, durable reopen/deduplication, cancellation before/after effect,
budget exhaustion and deadlines. Python and TypeScript test the discriminated
contract; the stock Mineflayer adapter test proves no advertised support or input.
The actual JVM HTTP bridge invokes the pure opening motor with a synthetic GUI;
the scoped CLI sends a real full batch over the broker and receives the terminal
receipt, retained charges and duplicate result. **FTB/UI/game effects remain
synthetic.** This does not qualify actual optional class loading or GUI parity.

The first Java suite failed two new tests because their journal subdirectories
had not been created. The production path-safety guard correctly rejected them.
The fixtures now create those directories; the guard was not relaxed. Both the
failed and successful logs are retained. Gradle deprecation warnings remain.

Final schema export/generation, TypeScript build, Ruff on changed Python files
and tracked `git diff --check` pass (line-ending warnings only). After clarifying
the capability field to `server_effects_verified:false`, the focused scoped CLI
test passes again: one test, zero failures/skips. Local documentation links and
the candidate's absence of bundled FTB classes are checked by the evidence collector.

Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-quest-open-01`
contains logs, installed public API/bytecode audit, JUnit results, source hashes and
`verification.json`. The candidate JAR SHA-256 is
`382a674d43ec6b844cdff55e23fc9580cf46c3ea6adc254cb76b9e9e43775048`.
It is **built but uninstalled**; running E9E still has the old read-only build.

## Remaining work

M0.3b.3.2.3c.3.1 is **implemented_unverified**. Chapter/task selection, back,
scrolling and a structured way to close this new quest screen remain .3.2;
submission/reward/choice resource effects and server feedback remain .3.3.
Choice/rich/extension observations retain their other named children. Authentic
exact-pack opening/refusal, GUI lifecycle, permissions, persistence, timing,
modifier/input parity, cancellation, privacy and reference/server evidence remain
unrun. No release, campaign, full quest surface or modpack support is claimed.

A fresh read-only desktop capture still showed the Windows Security/OpenJDK
network prompt; no input was sent. The existing operator handoff remains pending
under the computer-use skill. No new client/server/worker or inference run started;
Strata inference remains $0 dispatched. G0–G5 and all other outstanding gates
retain their previous status.
