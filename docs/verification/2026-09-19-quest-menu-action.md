# Current item-menu Back and wheel controls

2026-09-19. Operator-only. M0.3b.3.2.3c.3.2b.2a, F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15; partial T01/T03/T06/T07/T12. No aggregate gate closes.

The Forge candidate implements `quest_menu/back|scroll` in the scoped ActionBatch
lane. SPEC v0.2.14 / Forge minor 24 / native seventeen-action policy pins
`ftb-current-item-menu-back-wheel/1`. Stock Mineflayer rejects the action.

## Implemented behavior and limits

[GameQuestMenuAction](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestMenuAction.java)
binds the observed source/menu generation and revision, exact menu/task/parent
objects, layout and scroll state. Back requires null direction and an enabled
visible control. Scroll accepts one up/down wheel step using the panel's native
step and bounds; fractional steps and boundary no-ops are retained. The motor
revalidates inside charged dispatch, confirms immediately and next tick, and never
retries. Cancellation retains existing effects and charges; uncertain outcomes fence.

[NativeQuestMenuAction](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestMenuAction.java)
uses the pinned public FTB APIs. It requires exact item-menu and previous-book
classes, matching task/file/viewed quest, own-team non-editing authority, survival,
idle inputs, normal modifiers, ungrabbed mouse and empty cursor/crafting/result.
It rejects attached scrollbars, horizontal-default panels and a scrollable outer
menu. Wheel dispatch temporarily targets the clipped visible panel through logical
hover, calls the ordinary callback once, and restores hover in `finally`, without
moving the OS pointer or assigning scroll coordinates. Back invokes the visible
ordinary button and confirms the same parent quest. These are local UI receipts,
not server-resource or rendered-parity claims.

Installed-bytecode inspection confirms Panel's reverse child input traversal,
the exact item buttons' inherited no-op wheel callback, vertical wheel sign and
clamping, and ordinary Back's return through the previous screen. This inspection
supports the implementation but does not establish actual loaded-mod behavior.
The same three FTB artifact hashes remain pinned. Public menu observation policy
`ftb-current-item-alternatives-clipped-pages32/2` supersedes `/1`: response fields
are unchanged; revisions now include wheel-sensitive geometry and control state.
Python/generated/TypeScript validation, native dispatch and capability metadata
agree. No arbitrary callback, raw object, submission or private parent ID is exposed.

## Executed checks

Windows; Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1, Forge 43.4.23 compile
target and exact external FTB Library compile-only artifact.

| Procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 273 pass; zero failures/errors/skips; build 26 s |
| Twelve Python suites: native game/JVM, contracts, records, machine query and seven quest suites | 235 pass; zero skips; 32.44 s |
| Final full `npm test`, explicit JVM/classpath and Windows guardian Python | 129 pass; zero failures/skips; 54.302 s |

Nine new Java tests exercise ordinary Back/up/down/clamping/no-ops, fractional
steps, stale or replaced source/menu/parent/task/layout, hidden controls, refusal,
strict request shape, deduplication/reopen, cancellation, deadlines and budget
exhaustion. JVM/HTTP and scoped CLI fixtures run task opening → down → up → Back
through the real pure motors, checking revised observations, two charged primitive
invocations per action (gesture plus safety release), deduplication and parent quest.
**Game, FTB and UI authority are synthetic in these tests.**

The first full Node run had 128 pass / one failure: `quest-menu` returned
`LEASE_EXPIRED` after the direct-lane CLI fixture exceeded its six-second lease.
The fixture bypassed the worker supervisor and had no lease renewal. Added a
two-second call to the ordinary renewal API, matching the worker's lifecycle,
with cleanup. The full rerun passed; production expiry, freshness, deadlines and
retry policy are unchanged. The prior task-opening run's undiagnosed rejection
remains historical evidence; this observed failure does not prove its cause.
Both current attempts are retained. Existing Gradle deprecations remain.

Candidate JAR SHA-256:
`a3a13eb08385bd757c1acbb6ebb3ae452f4f46bf88c21f7952aaf96298cb20d8`.
Built, **uninstalled**; no bundled FTB classes. Private logs, bytecode, JUnit,
source hashes and verification record:
`C:\Users\Darian\.strata\evidence\2026-09-19-quest-menu-action-01`.

## Remaining qualification

This child is **implemented_unverified**. Choice/extension/other-menu Back and
scroll (.3.2b.2b), other task/JEI/UI routes (.3), occupied crafting-state lifecycle
(.4), submissions/claims (.3.3), rich/choice displays, and authentic callback,
viewport, pointer/modifier, resource, reference, timing and isolation cases remain
required. T03/G0 retain the exact Mineflayer/E9E failure; all aggregate gates stay open.

A fresh read-only desktop capture again showed the Windows Security/OpenJDK
prompt over the old E9E client; no input was sent. Operator handling is pending.
No new real client/server/worker, inference, soak, capacity test or study started.
Strata inference remains $0 dispatched. The goal remains active and M7 conditional.
