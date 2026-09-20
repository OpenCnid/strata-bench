# Ordinary task-to-JEI opening and return

2026-09-19. Operator-only. M0.3b.3.2.3c.3.2b.3b.1a; F01/F06/F09/F16,
N01/N02/N04/N05/N06, C09/C15; partial T01/T03/T06/T07/T12. No aggregate gate closes.

SPEC v0.2.17 / Forge minor 27 adds the non-consuming single-item ItemTask route
to `quest_task/open`. The ordinary TaskButton callback opens JEI; a distinct
`task_recipes` screen state identifies its originating quest. `quest_navigate/close`
returns to that same parent book and quest. Eighteen action kinds remain; policies
are `ftb-visible-item-task-menu-or-jei-open/2` and
`ftb-own-team-book-and-task-recipes-state/2`.

## Native integration

[NativeQuestTaskOpen](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestTaskOpen.java)
retains current component-page selection, selected book/quest, exact enabled and
clipped TaskButton, source/team membership, normal modifiers/tooltips, idle survival
and empty carried/crafting/result guards. The JEI branch additionally requires a
non-consuming exact ItemTask with one display item, released physical mouse
buttons and an ungrabbed mouse. Empty display lists and other task callbacks still
reject; all remaining routes retain their ledger children.

[JeiRecipePlugin](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiRecipePlugin.java)
checks exact XMod helper class and identical current XMod/Strata JEI runtime and
RecipesGui identities. Helper availability alone cannot authorize the action.
Require all five Quests/Library/Teams/XMod/JEI artifact hashes; the two additional
pins are in [GameQuestRecipeView](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestRecipeView.java).
The actual native item must be a known visible JEI item ingredient. Its private
copy is rechecked with native ItemStack equality during dispatch revalidation;
it is not exported as a recipe definition or focus. One ordinary TaskButton LEFT
callback runs; no direct recipe-manager mutation, transfer, cheat or claim hook.

A returning void callback is insufficient. The motor confirms the actual distinct
RecipesGui immediately and next tick. The [installed-route audit](2026-09-19-quest-jei-route-audit.md)
established that missing runtime/ingredient or failed showFocus may leave the
screen unchanged. Such a dispatched but unconfirmed opening is fenced with retained
costs; it is not blindly repeated.

The opening retains its parent/task/source/runtime binding privately. Screen or
source/runtime replacement invalidates it. [NativeQuestRecipeView](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestRecipeView.java)
rechecks the visible parent quest before reading its bounded task list and requires
the original task's membership before publishing origin IDs. A changed/removed origin rejects before further
task access. The screen tracker binds actual screen/kind, source, origin objects,
window dimensions and parent layout into generation/revision.

`quest-screen` keeps its bounded field set, adding only `kind:task_recipes`.
Its chapter/quest fields mean **originating quest**, not current JEI focus or
displayed recipe. No private parent/focus/page fields are reflected or exported.
Current-page contents and recipe-history/category/page navigation remain required
under .1b. Existing focused recipe lookup does not stand in for those contents.

Only `quest_navigate/close` is supported on this screen. The normal Screen.onClose
callback restores the retained parent and clears JEI history. Back is a separate
JEI history operation and rejects here, as do chapter/quest navigation, manually
opened/unbound recipe screens, and item/choice `quest-menu` projection. The
immediate and next-tick checks require the original book/quest. Ordinary resource
guards and the durable lane retain cancellation effects, safety-release charges,
uncertain attempted costs and at-most-once dispatch; no native resource-effect
success is claimed.

## Verification

Windows, Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1, Forge 43.4.23 compilation
and exact installed FTB Library compile-only dependency. The candidate bundles
neither FTB nor JEI implementation classes.

- Initial native compilation passed, 15 s. Full Java build/test/classpath task
  passed, 25 s. Review then added an explicit changed-origin guard before task
  dereference plus a missing-origin regression assertion. Final full Java suite:
  **304 pass**, zero failures/errors/skips, 26 s.
- Fourteen Python suites for native/JVM/contracts/records/machine and quest paths:
  **262 pass**, zero skips, 39.08 s.
- Full Node suite with explicit JVM/classpath and Windows guardian Python:
  **131 pass**, zero failures/skips, 58.260 s. New scoped CLI sequence exercises
  book open → quest selection → task recipe opening → origin state → ordinary
  close → same quest, with two emitted primitives and deduplication per action.
- Changed-Python Ruff, schema export, TypeScript generation/build pass. Existing
  Java/Gradle deprecation warnings remain.
- Evidence collector checked five artifact hashes, 59 source snapshots and 505
  local links; tracked `git diff --check` passed with CRLF warnings only.

Ten new Java tests cover five exact artifact pins, distinct recipe state and
return, prohibited history/selection actions, runtime/source/screen/layout races,
no-open and unavailable source, binding replacement/expiry, malformed/missing
origins, recipe-as-book rejection, refused/changed return, journal-reopen
deduplication, cancellation and unknown effects with all attempted charges.
Strict Python/Node response checks accept only the identified recipe state with
origin IDs, rejecting private focus/parent fields and the old screen policy.
Actual JVM/HTTP and CLI transports use **synthetic game/UI authority**. Python/Node
completed before the final native-only origin guard; the final Java suite includes
that guard's pure origin regression. No authentic JEI behavior is inferred.

Final candidate SHA-256:
`109e437a88948c34df14a40eb5a1d82993843db50a4f27af287c888ef30d8533`.
Built, **uninstalled**. Logs, JUnit, source hashes and pin evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-quest-jei-lifecycle-01`.

## Remaining gates

Opening/origin-state/return is **implemented_unverified**. Current-page projection,
history/category/page controls, other extension/UI routes, occupied crafting state,
submissions/claims, and loaded native input/resource/reference/isolation qualification
remain required. T03/G0 retain the separate Mineflayer/E9E handshake failure.

No desktop input, real client/server/worker launch, inference, soak, capacity test
or study ran in this phase. The last observed Windows Security prompt still has
an outstanding operator handoff; it was not recaptured or operated this phase.
Strata inference remains $0 dispatched; goal active and M7 conditional.
