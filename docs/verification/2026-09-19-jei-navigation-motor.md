# Bounded JEI page/category navigation — September 19, 2026

Operator-only; exclude this report and its private evidence from gameplay contexts.

Historical minor-31 phase. The [history follow-on](2026-09-19-jei-history.md)
adds ordinary Back under minor 32; the evidence below remains specific to this phase.

M0.3b.3.2.3c.3.2b.3b.1b.3b and its motor child .2 are
**implemented_unverified**. SPEC v0.2.23 / D06, Forge minor 31, nineteen actions,
navigation policy `jei-current-page-preview-execute-fresh-frame200/1`, native
motor `durable-intent-client-thread-nineteen-actions/1`. No authentic game input
was performed. All aggregate gates remain open; the original Mineflayer/E9E
failure, recipe-history Back and full rendered-page requirements remain.

Affected coverage: F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18
and partial T01/T03/T06/T07/T12. No scope, accounting or acceptance threshold
was reduced. A new capability identity is required; old installed clients cannot
be used with the new strict native capability contract without updating both.

## Delivered behavior

[GameRecipeNavigation](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeNavigation.java)
implements one ordinary page/category gesture. The typed `recipe_navigate`
action accepts source `jei`, one of the four displayed control names, source and
screen generations, screen revision and the exact page digest. The full
ActionBatch still supplies body/observation/epoch/lease/sequence/deadline authority.
No caller coordinates, widget IDs, raw keys, history, callbacks or recipe graph
selectors are admitted. Python/JSON Schema/TypeScript and native Java agree;
the scoped `mcgame act --json` path carries the action. Mineflayer's action
profile rejects it before dispatch.

[NativeQuestRecipeView](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestRecipeView.java)
binds the motor to an ordinary task-opened recipe screen, own quest origin and
the five exact FTB/XMod/JEI artifacts. Every input phase rechecks the same public
page digest, screen/source revisions, private copied button identity/geometry,
enabled state, viewport containment and idle physical input/modifiers. The
ordinary constructor/factory/router/button witness from the
[input foundation](2026-09-19-jei-input-provenance.md) is required.

Mouse-down previews once. Mouse-up executes once on a later tick, after another
complete check. The prior render capture is then invalidated. The motor waits
for a fresh complete frame from the same source, screen and origin; the private
frame identity never enters the public schema. At most 200 active ticks may
wait, bounded also by the unchanged ten-second action limit and tighter lease,
wall and resource deadlines. Same-content fresh frames may confirm an ordinary
no-op, but never a recipe-progress claim. Reusing the pre-input frame cannot
complete the action.

Preview, execution, each wait tick and the combined safety release are charged.
Both native and broker admission require at least four remaining primitive units;
the existing safety-release reserve remains in force during longer waits.
Cancellation and failure use the public router's non-executing reset, including
when ordinary player-input cleanup throws. Failed cleanup retains ownership and
fences the lane; uncertain event counts remain null while attempted charges
remain durable. No mouse-up replay, request replay after a lost receipt, or
automatic navigation retry occurs.

## Verification

Windows, JDK 17.0.20.101, Forge 1.19.2-43.4.23, exact external FTB Library
compile-only JAR. All screen/button/render effects in these tests are synthetic.
Real JVM, HTTP, scoped CLI, durable journal and selected process checks are
distinguished from authentic Minecraft behavior.

- Final Gradle client test/build/writeTestClasspath: **383 pass**, zero failures,
  errors or skips, 39 s. Fifteen new navigation tests cover all four controls,
  stale/hidden/disabled/clipped targets, races, missing/wrong callbacks, two-phase
  ordering, old/missing frames, 200-tick exhaustion, source replacement,
  strict fields, before/between/after cancellation, deadline/budget fences,
  failed cleanup, partial-effect uncertainty and durable duplicate/restart paths.
- Selected public/native/quest/recipe Python suites: **328 pass**, 40.63 s.
  Twenty-seven new strict-selector cases include missing fields, private fields,
  coercion and digest bounds. Actual JVM/HTTP synthetic lifecycle now opens,
  navigates and closes the recipe view with four charged navigation primitives.
- Full Node suite before the final four-unit admission refinement: **135 pass**,
  zero failures/skips, 75.8680505 s. The real scoped CLI reaches the Java motor,
  observes the synthetic changed page, deduplicates the request and returns to
  the originating quest. Malformed public selectors and unsupported Mineflayer
  profile calls reject without dispatch.
- After that refinement: final Java suite above, **3 Python/JVM lifecycle cases
  pass** (21 deselected, 10.44 s) and **3 targeted Node tests pass** (6.9494057 s)
  for schema/Mineflayer rejection, four-unit broker admission and scoped CLI
  navigation. These are reruns/subsets, not additional independent suite totals.
- Changed Python Ruff, schema export, TypeScript generation/build, evidence
  hashes and local-link checks pass.

Commands: from `java/`, `gradlew.bat :forge1192-client:test
:forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console
plain`, with JAVA_HOME and STRATA_FTB_LIBRARY_JAR as in the input-foundation
report. Python uses `STRATA_CLIENT_TEST_JAVA` and
`STRATA_CLIENT_TEST_CLASSPATH`; the exact sixteen selected pytest suites and
commands are retained in the private verification manifest. Node uses those
variables plus `STRATA_GUARD_TEST_PYTHON`, then `npm test`; final selection is
`node --test --test-name-pattern 'recipe navigation|scoped CLI opens, navigates'
dist/tests/forge.test.js dist/tests/actions.test.js` after `npm run build`.

The initial 381-test Java run had one test failure: a failure-path assertion
called getAsInt on the intentionally null emitted-event count after reset failed.
The test now checks retained attempted charges and explicitly requires unknown
emission count in that case. The intermediate 382-test run passed in 36 s;
the final admission test and refinement produced the final 383-test result.
Initial failure logs remain private. No production certainty guarantee was
weakened to make that test pass.

Final uninstalled candidate SHA-256:
`5053fcb666060db203cb1349aaf99b83ccb929bcdfe382176dfe27ba3ec64ad9`.
The dedicated profile retains the previous minor-30 read-only JAR
`f10e7ad6…`; prior authentic read-only evidence does not qualify this candidate.

Private evidence directory:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-navigation-motor-01`.
Actual nine-hook application, native action/cancellation timing, visual effects,
final overlay visibility, GUI/input parity, overhead and process isolation remain
unrun. The current policy also rejects changed/cycling content between phases
and cannot confirm an absent/incomplete frame. Required rich/custom/empty-page
and history behavior must be qualified or extended explicitly, never guessed.
No computer use, paid inference, live game mutation, soak, capacity certification
or scientific study ran. Total Strata inference remains $0.
