# Visible item-task menu opening

2026-09-19. Operator-only. M0.3b.3.2.3c.3.2b.1, F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15, partial T01/T03/T06/T07/T12. No aggregate gate closes.

The Forge candidate now accepts `quest_task/open` through the scoped ActionBatch
lane. SPEC v0.2.13 / Forge minor 23 / native sixteen-action policy pins
`ftb-visible-item-task-menu-open/1`. Stock Mineflayer rejects this action.

## Implementation and native scope

[GameQuestTaskOpen](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestTaskOpen.java)
requires the selected task in the exact bounded components page, with query/revision
and current source/screen generation/revision. The selected chapter and quest must
already be displayed. The motor validates again inside charged dispatch, retaining
the actual task/button identity and private layout digest. It calls once, verifies
a distinct resulting screen immediately and next tick, and never retries. Cancellation
retains already-created UI state and cost; post-effect uncertainty fences the lane.

[NativeQuestTaskOpen](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestTaskOpen.java)
uses exact installed public FTB APIs and the existing three artifact pins. Own team,
non-editing source, unlocked/enabled quests, survival, released inputs/modifiers,
idle hands, no server container, empty cursor/crafting/result and normal tooltips
are required. The fixed public widget path is book → detail → content → tasks →
TaskButton. Check membership, enabled state and clipped visibility before task IDs.
Native Panel bytecode confirms list-order drawing and reverse-order input; later
sibling layers conservatively obstruct selection. Widget hit testing requires every
ancestor's own mouse-over, and native scroll offsets truncate toward zero. Offsets,
unknown widgets or unsupported overlapping contexts reject rather than bypassing UI.

The exact TaskButton LEFT callback delegates to its task with ordinary native
startability/completion flags. Initial support is exact ItemTask whose nonempty
alternatives (maximum 512) open ValidItemsScreen. Non-consuming single-item tasks
can route to JEI; that separate route and empty-alternative toast/extension tasks
remain explicit follow-up work. Selection inspects at most 512 members/buttons/
alternatives, with a cooperative 100-ms bound. Confirmation checks the actual new
exact menu, retained task, source, visible parent IDs and previous-book identity.
No private fields, raw definitions, progress writes or submission packets are used.
`emitted` confirms this local opening only, not rendering or server resource effects.

Python/generated/TypeScript schemas, native policy validation, runtime dispatch and
Forge capability metadata were updated. The existing CLI `act` route carries the
new action; no general invocation or raw-object route was added.

## Executed verification

Environment: Windows, Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1, Forge 43.4.23
compile target and the existing exact external FTB Library compile-only artifact.

| Procedure | Result |
|---|---|
| Full `:forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 264 Java pass, zero failures/errors/skips |
| Focused `:forge1192-client:test --tests '*GameQuestTaskOpenTest' :forge1192-client:writeTestClasspath` after using the real components projector in the synthetic port | 7 pass, zero failures/errors/skips |
| Eleven selected Python suites: native game, contracts, records, native JVM, machine query and six quest suites including task opening | 232 pass, zero skips, 31.34 s |
| Full `npm test`, explicit JVM/classpath and Windows guardian Python | Final 128 pass, zero failures/skips, 52.799 s |
| Focused scoped CLI | 1 pass, zero skips |

Seven new Java tests cover normal one-shot opening, wrong/stale/hidden/off-page
selection, replaced button/task/layout/book, refusal and post-effect changes,
strict requests, durable deduplication/reopen, and cancellation before/after input.
Python and Node reject submission/reward selectors and malformed identity/bounds.
Actual JVM/HTTP and scoped CLI run book → quest → selected task menu through the
real pure motors. **FTB/game/UI authority in these tests is synthetic.**

Retained failures: the first focused Gradle command attached `--tests` to the
classpath task, so argument parsing failed before testing; corrected option order
passed. The initial full Node run had 127 pass/one CLI exit-4 rejection while the
Python suite ran concurrently. Its old callback discarded the response diagnostic.
Added diagnostic output; the focused case and full rerun passed without changing
production timeouts, freshness checks or retry policy. The initial cause is
**unresolved**, not established as a fixture or production defect. Authentic/load
timing remains unqualified. All attempts are retained; existing Java deprecations remain.

Candidate JAR SHA-256:
`5b42905061db0947fb1b0eaa387b1a6508b808911cbcff6b851c153cec790a15`.
Built, **uninstalled**, no bundled FTB classes. Private logs, bytecode, JUnit and
source/evidence hashes: `C:\Users\Darian\.strata\evidence\2026-09-19-quest-task-open-01`.

## Remaining work

This child is **implemented_unverified**. Menu back/scroll (.3.2b.2), other
task/choice/JEI routes and UI contexts (.3), occupied crafting-state conservation
(.4), submissions/claims (.3.3), rich/choice displays and authentic exact-pack
callback/viewport/reference/timing/isolation qualification remain required.
T03/G0 retain the Mineflayer/E9E handshake failure; all aggregate gates stay open.

A fresh read-only capture still showed the Windows Security/OpenJDK prompt over
E9E; no input was sent and the existing skill handoff remains pending. No new
real client/server/worker, inference, soak, capacity test or study was started.
Strata inference remains $0 dispatched. M7 remains conditional.
