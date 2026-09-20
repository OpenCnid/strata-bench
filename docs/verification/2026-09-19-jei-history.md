# Ordinary JEI recipe-history Back — September 19, 2026

Operator-only; exclude this report and private evidence from gameplay contexts.

Historical minor-32 phase. The [empty-page follow-on](2026-09-19-jei-empty-page.md)
versions page observation under minor 33; history dispatch and charges remain.

M0.3b.3.2.3c.3.2b.3b.1b.3c is **implemented_unverified**. SPEC v0.2.24,
D06, Forge minor 32, nineteen actions, navigation policy
`jei-current-page-controls-history-fresh-frame200/2`. No authentic action or
physical Back-key conformance is claimed. All aggregate gates remain open.
Coverage: F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18 and
partial T01/T03/T06/T07/T12; G0/G1 and T05 remain unqualified.

The exact installed JEI 11.8.1.1034 binary was inspected locally. Its ordinary
Back input handler calls the concrete screen's public `RecipesGui.back():void`.
That callback discards the internal logic's boolean result. Empty history is a
no-op; screen close separately clears history and returns to the parent.
`IRecipesGui` does not declare Back. The implementation uses this one fixed
public concrete callback, not private fields, hidden history indices or a
fabricated interface method. It does not simulate a physical hotkey.

[GameRecipeNavigation](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeNavigation.java)
accepts `history_back` in the existing strict action envelope. It retains current
page/source/screen authority, opening-bound origin, exact artifact guards and the
full mutation lane. [NativeQuestRecipeView](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestRecipeView.java)
requires idle physical input and no pending owned JEI gesture, invokes Back once,
invalidates the prior frame, then waits for a fresh complete same-context frame.
Empty history keeps the recipe screen open; there is no Close fallback.

Admission reserves three primitive units for callback, one frame check and
safety release. Further active waits charge, up to 200 ticks within the existing
ten-second/tighter deadlines. Page/category navigation retains four-unit
admission and its ordinary preview/execute route. Receipts confirm only
`emitted`; callback exceptions, cancellation, exhausted budgets and failed
release retain partial effects and uncertainty without replay. Source changes
or reuse of the old render frame cannot confirm Back.

Verification used Windows, JDK 17.0.20.101 and Forge 1.19.2-43.4.23 with the exact
external FTB Library compile-only artifact. The game screens, history stack,
callbacks and renders are synthetic; JVM/HTTP/scoped CLI/journals are real.

- Gradle client test/build/writeTestClasspath: **395 pass**, zero failures,
  errors or skips, 42 s. Twelve new history tests cover ordinary/empty Back,
  unsupported/busy input, stale/raced selectors, disabled page buttons, fresh
  frames, bounded waits, cancellation, budgets, failures and restart deduplication.
- Sixteen selected Python public/native/quest/recipe suites: **329 pass**,
  41.78 s. Actual JVM transport covers Back and exhausted Back with three charged
  primitives apiece, keeping the task recipe screen open until explicit close.
- Full Node suite: **136 pass**, zero failures/cancelled/skipped/todo,
  76.64169 s. Scoped CLI exercises navigation, supplied history, exhausted
  history and explicit close. Broker admission and stock Mineflayer rejection pass.
- Ruff, schema export/agreement, TypeScript generation/build, artifact/source
  hashes, compiled callback inspection, local links and diff checks pass.

Commands are the previous motor report's Gradle and sixteen-suite Python
selection, followed serially by `npm test`, using the same JVM/classpath/guard
environment. Exact logs and an executable verification collector are private at
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-history-01`.
The synthetic fixture supplies its history; it does not prove that an actual
category-page operation populates JEI's history stack.

Uninstalled candidate SHA-256:
`1323c60f3d99ccfee4c7f7df477769c33ad7859610fc8d9f684fc5bbd7acc9e4`.
Installed minor-30 read-only candidate remains `f10e7ad6…`; its earlier connected
evidence cannot qualify this candidate. Required native hook application,
populated/empty Back, cancellation timing, full rendered content/overlays,
resource/reference parity and isolation remain open. No computer use, live
game mutation, paid inference, soak, capacity certification or study ran.
