# Witnessed empty JEI layout pages — September 19, 2026

Operator-only; exclude this report and its private evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.2b.2a is **implemented_unverified**. SPEC v0.2.25,
D06, Forge minor 33, NativeRecipePage/4 and page policy
`jei-task-drawn-slot-header-controls-empty-loop/4`. Nineteen actions and navigation
charges are unchanged. No aggregate test or release gate closes.
Coverage: F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial
T01/T03/T06/T07/T12. Rich/custom/overlay content remains .2b.2b; native parity .1b.4.

The pinned installed JEI 11.8.1.1034 draw method contains one ordinary iterator
predicate call site, one layout draw per positive result, and normal return
after the terminating false. The [layout hook](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/mixin/JeiLayoutsDrawMixin.java)
wraps that predicate with exactly one original call and unchanged result/exception.
It observes private renderer/iterator identity and the boolean, without extra
iteration, list-size queries, private fields or recipe-graph lookup. The existing
nine Mixin classes remain; the layout Mixin now includes this additional hook.

[Render capture](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeRenderCapture.java)
requires each true predicate to match exactly one completed copied layout draw,
then a false predicate and normal renderer end. Missing, repeated, replaced,
late, incomplete and overflowing evidence invalidates the frame. Empty frames
also require two headers and four controls before full-frame completion.
Zero-layout pages preserve source/screen/origin, private frame stamps, canonical
digest, age and size limits; `complete:false` still declares partial coverage.
An absent frame remains an error. The new policy/schema rejects old identities.

Java/Python/TypeScript validators accept zero through 32 layouts with all other
guards unchanged. The actual JVM/HTTP/scoped CLI fixture navigates from a populated
page to a synthetically empty page and returns through history Back, preserving
charges and duplicate handling. Its game/history/render effects are synthetic.

Verification: Windows, JDK 17.0.20.101, Forge 1.19.2-43.4.23 and exact external
FTB Library compile-only artifact, using the previous history report's commands.

- Gradle client test/build/writeTestClasspath: **405 pass**, zero failures,
  errors or skips, 38 s. Ten added tests cover empty/full transitions, missing
  predicates/draws, replaced identities, incomplete returns, headers/controls,
  frame expiry, immutable copies and content digests. Existing render fixtures
  now supply the explicit loop witness; original lifecycle negative cases remain.
- Sixteen selected Python public/native/quest/recipe suites: **330 pass**, 41.45 s.
- Full Node suite: **136 pass**, zero failures/cancelled/skipped/todo, 76.4166114 s.
  Transport tests reject stale digests, old policy/schema and incomplete empty
  envelopes. Scoped CLI exercises the empty-page transition and Back.
- Ruff, schema export/agreement, TypeScript generation/build, compiled hook
  inspection, artifact/source hashes, local links and diff checks pass.

Uninstalled candidate SHA-256:
`4db8ae89f0e095653eee8a05f745409073f1196f495e8796291a53c3030d8171`.
The installed minor-30 read-only candidate remains `f10e7ad6…`. Private logs,
installed/compiled bytecode, source copies and executable evidence collector:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-empty-page-01`.

Actual Mixin application, reachable empty native pages, final overlay visibility,
native navigation/cancellation timing, mechanics/reference parity and isolation
remain unverified. Local bytecode inspection proves neither a loaded hook nor
rendered behavior. No desktop input, game launch/mutation, inference, soak,
capacity certification or scientific study ran. Strata inference remains $0.
