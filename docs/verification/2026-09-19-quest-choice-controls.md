# Opening-bound choice-menu Back and wheel controls

2026-09-19. Operator-only. M0.3b.3.2.3c.3.2b.2b.1; F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15; partial T01/T03/T06/T07/T12. No gate closes.

SPEC v0.2.16 / Forge minor 26 extends `quest_menu/back|scroll` to the exact
opening-bound choice menu. Policy `ftb-current-item-choice-menu-back-wheel/2`
supersedes item-only `/1`; menu projection `/4` supersedes `/3`, incorporating
scrollbar state into revisions without exporting private scrollbar fields.
The native eighteen-action policy and strict action envelope remain unchanged.

## Native behavior and limits

[NativeQuestChoiceAction](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestChoiceAction.java)
requires the eligible opening's retained source/parent/reward binding, exact
public widget tree, current own-team context, idle survival player, empty carried/
crafting/result state, ungrabbed mouse, and released modifiers and physical mouse
buttons. Unknown contexts, changed identity/layout and scrollable outer menus reject.

Back invokes the normal ScreenWrapper Backspace/onBack callback, which restores
the prior book. It does not invoke a reward-choice button or claim. Observations
still have empty `controls`: the choice menu has no visible Back button. The
immediate and next-tick checks require the same parent book and selected quest.
The ephemeral choice binding clears on Back or source/screen replacement.

Wheel input targets the clipped panel with temporary logical hover, invokes one
normal native wheel callback, and restores logical hover in `finally`. The exact
attached vertical PanelScrollBar owns the value and clamping. No scroll fields
are written directly. [GameQuestMenuAction](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestMenuAction.java)
confirms both value and panel offset, with unchanged native object/source/layout
identity, immediately and next tick. Step, range and value enter the observation
revision through [NativeQuestChoiceMenu](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestChoiceMenu.java).

Pinned FTB Library bytecode uses Minecraft Mth clamp even when content height
minus viewport height is negative. For content 30 / viewport 160 / step 20,
successive downward wheel callbacks change scrollbar value 0 → -130 → 0 while
panel Y remains 0. The implementation preserves and confirms this behavior. An
unchanged visible panel alone cannot prove the callback succeeded. Boundary
no-ops still consume the gesture and safety release.

The exact native Back callback can restore the OS pointer through FTB's
`closeGui(true)` route. This clarifies earlier broad pointer wording: temporary
wheel targeting does not move the OS pointer; ordinary Back may restore it.
There is no alternate injected-pointer or direct scroll-state route.

All operations use the existing single durable mutation lane. Cancellation before
dispatch still charges the safety release; cancellation after dispatch retains the
scroll effect and both charges. A callback that throws after an effect retains
attempted charges and reports uncertain emitted count. No uncertain mutation is
replayed. This is local menu confirmation, not server-resource success.

## Verification

Windows; Python 3.12.14; Node 24.19.0; JDK 17.0.20.1+1; Forge 43.4.23 compile
target. Exact installed FTB Quests 1902.5.10-build.497, Library
1902.4.1-build.236 and Teams 1902.2.14-build.123 retain their previous hash pins.
Library is compile-only; the candidate bundles no FTB classes.

- Full Java tests/build/classpath task: **294 pass**, zero failures/errors/skips,
  24 s. Initial run: 293 pass / one failure because the new test incorrectly
  expected zero charged releases before dispatch. Corrected the assertion to
  retain the release charge and unknown emitted count after a throwing callback;
  production accounting was unchanged. Both attempts and failed JUnit XML retained.
- Fourteen focused Python native/JVM/contracts/records/machine/quest suites:
  **255 pass**, zero skips, 35.89 s.
- Full Node suite, with explicit JVM/classpath and Windows guardian Python:
  **130 pass**, zero skips, 58.331 s; TypeScript build passed.
- Changed-Python Ruff, schema export and TypeScript generation passed.

Nine new Java cases cover exact positive/fractional/clamped traces, negative
maximum with stationary panel, refused/partial callback detection, stale value/
range/step/source/layout/screen, replaced reward/parent, next-tick changes,
malformed/desynchronized values, ordinary Back, retained cancellation charges,
unknown effects, and journal-reopen deduplication. Python and Node reject the old
choice policy and execute choice open → read → down → up → Back through actual
JVM/HTTP and scoped CLI transports, checking revisions and deduplicated charges.
Game/UI authority in these tests is **synthetic**, not authentic Minecraft.

Candidate JAR SHA-256:
`f5785b62ccb9aa8e1bf7d6acf4aef0fc618168d24a874e34ed3412099df131ac`.
Built, **uninstalled**. Private logs, installed bytecode inspection, JUnit and
source hashes: `C:\Users\Darian\.strata\evidence\2026-09-19-quest-choice-controls-01`.

## Remaining acceptance

This child is **implemented_unverified**. Loaded callbacks, clipping/viewport,
dragging/polling, pointer restoration, server-resource conservation, ordinary
reference parity, timing and isolation remain .4's authentic qualification.
Other extension displays/controls, task/JEI contexts, occupied crafting lifecycle,
submission/claim effects and rich/dependency surfaces remain required.
T03/G0 retain the exact Mineflayer/E9E handshake failure.

A fresh read-only desktop capture still showed Windows Security over the existing
E9E client. Operator handling remains pending; no desktop input or new real client/
server/worker, inference, soak, capacity test or study ran. Strata inference remains
$0 dispatched. The long-horizon goal remains active, with M7 conditional.
