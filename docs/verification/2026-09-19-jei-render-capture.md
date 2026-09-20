# Task-bound JEI render provenance — September 19, 2026

Operator-only; exclude this report and its evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.1 is **implemented_unverified**. This is the private
render-provenance foundation for current recipe-page observation, not an implemented
public page reader. It advances F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15
and partial T01/T03/T06/T07 under D06. No aggregate test or release gate closes.
SPEC v0.2.18 records the instrumentation; public Forge minor 27, eighteen actions,
and the previous task/screen policies remain unchanged.

## Implemented behavior

The prior audit established that public IRecipesGui has no current-page getter.
The new optional Mixin targets the exact installed JEI 11.8.1.1034
`RecipeGuiLayouts.draw` loop. It wraps the loop's ordinary public
`IRecipeLayoutDrawable.drawRecipe` call, invokes that method once with the same
receiver and arguments, and records the layout only after normal return. It
does not intercept input or inspect private parent, focus, recipe-list or page
fields. Missing/unapplied hooks cannot publish a frame.

The capture arms only after the task-opening adapter confirms the actual screen,
all five artifact pins and retained origin/runtime/source identity. Forge render
Pre clears any previous completed frame. A matching Post can complete the capture
only after one matching, normally completed layout loop. Runtime unavailability,
screen/source changes and tick validation clear the capture.

`GameRecipeRenderCapture` retains at most 32 opaque private identities in native
order. Duplicate/overflow/null identities, nested/repeated loops, wrong returns,
missing hooks, empty/partial frames, changed screen/runtime/origin/dimensions,
frames over 100 ms, clock regression and reads older than 250 ms reject with
`GAME_RECIPE_RENDER_UNAVAILABLE`. No truncation or reuse of an earlier complete
frame after an incomplete one. The returned internal list is immutable.

The layout **objects themselves remain mutable**. They are not JSON, public
observations, recipe definitions or proof of visible pixels. The next adapter
must copy/filter displayed contents at render time and establish clipping,
overlay and ingredient semantics. It must not read later object state as though
it were a frozen past frame. No public transport currently calls the internal
reader; no additional game affordance is advertised.

Source: [capture](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeRenderCapture.java),
[native binding/events](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiRenderedLayouts.java),
[draw hook](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/mixin/JeiLayoutsDrawMixin.java),
[configuration](../../java/forge1192-client/src/main/resources/strata.jei-render.mixins.json),
[synthetic cases](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameRecipeRenderCaptureTest.java).

## Verification

Windows, pinned JDK 17.0.20.101, Forge 1.19.2-43.4.23, exact installed FTB Library
compile-only dependency and pinned JEI public API. Executed in `java/`:

```text
gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
```

**314 Java tests pass**, zero failures/errors/skips; build completed in 28 s.
Ten new cases use synthetic renderer events and identity objects. They cover
complete-frame boundaries, aborted/missing/duplicate/repeated hooks, native order,
immutability, context replacement, dimensions, clocks, limits and no opaque-object
content inspection. Existing Gradle/Java deprecation warnings remain.

The private collector checks the exact installed JEI hash and bytecode target,
the candidate wrapper's one native call followed by capture, Mixin manifest/config
packaging and absence of bundled FTB/JEI implementation classes. This inspection
does **not** execute the Mixin transformer or authentic rendering.

Collector passed: 15 source snapshots and 510 local links checked, alongside
the JUnit and artifact/bytecode checks above. Tracked `git diff --check` passed
with CRLF warnings only.

Python and Node suites were not rerun: no public schema, transport, policy or
action change occurred. Their last retained results remain 262 Python and 131
Node pass from the [lifecycle report](2026-09-19-quest-jei-lifecycle.md).

Candidate SHA-256:
`17203aab532914c12e5762edae6dcc9c7f6e8b76af42503d18cfe02a28a56ab4`.
Built, **uninstalled**. Logs/JUnit, installed/candidate bytecode, source snapshots
and verification manifest are under
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-render-capture-01`.

## Remaining work and live state

Child .1b.2 retains copied visible-page contents/labels and strict public transport;
.1b.3 retains recipe-history/category/page controls; .1b.4 retains authentic
Mixin loading, exact frame/GUI/input parity, overhead/mechanics and isolation.
Other custom categories/ingredients, quest routes/resources and machine/reference
requirements remain unchanged. Public close still uses the previous ordinary
origin-bound lifecycle. These hooks alone satisfy none of those gates.

A fresh read-only computer-use capture again showed the Windows Security/OpenJDK
network prompt over E9E. No desktop input was sent. The existing operator handoff
remains pending. No real client/server/worker launch, inference, soak, capacity or
study ran in this phase. $0 Strata inference dispatched; the long-horizon goal
remains active, M7 conditional. Exact Mineflayer/E9E T03/G0 failure is retained.
