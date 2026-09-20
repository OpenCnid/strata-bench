# JEI category and page header operands — September 19, 2026

Operator-only; exclude this report and its evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.2b.1 is **implemented_unverified**. It adds actual category/page header operands to the
existing scoped recipe-page route. SPEC v0.2.21 / D06, Forge minor 29, policy
`jei-task-drawn-slot-and-header-copies/2`, native `strata/NativeRecipePage/2`.
Coverage is explicitly `slot_and_header_draw_operands`, still `complete:false`.
Eighteen actions remain unchanged. Authentic conformance remains unverified.

Affected coverage: F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial
T01/T03/T06/T07. This does not close a milestone or aggregate gate.

## Installed route and implementation

Inspection of the exact JEI 11.8.1.1034 artifact establishes:

- `RecipeCategoryTitle.create` builds a possibly truncated visible component,
  separately retaining the full title for a later tooltip.
- `RecipeCategoryTitle.draw` passes only that visible component to the ordinary
  `StringUtil.drawCenteredStringWithShadow` helper.
- `RecipesGui.m_6305_` draws the category title and a separate page string before
  the layout loop. The helper centers text using `Math.round`, a nine-pixel line,
  and the ordinary shadow draw. No raw recipe-count lookup is needed.

Three optional exact-target Mixins observe the native screen render, category
draw and helper argument/normal-return pairs. No private fields are reflected;
no native render/input call is replaced or invoked a second time. Require ordered
category/helper return, page/helper return, layout loop and normal screen return
within the existing Pre/Post frame. Missing/nested/repeated/reordered/wrong-owner,
changed-operand or incomplete callbacks invalidate the frame. Later helper calls
do not confer header authority. Native hook application is still unrun.

The native copier requires the known Minecraft font, identity pose and exact
public rectangle operand. It checks geometry before inspecting component/text,
then uses the pinned rounded centering and shadow extent to check viewport bounds.
Clipped rows expose no text. Rejected rich component forms carry an unsupported
marker. It copies only bounded public component text or the actual immutable page
string, never the stored full title, a recipe graph, history or raw count.

The public page adds exactly two ordered header rows, category then page. Each
contains `kind`, `state` (`text`, `clipped`, `unsupported`) and nullable `text`.
Only text rows contain content, at most 1,024 Unicode code points / 4,096 UTF-8
bytes; reject unpaired surrogates. Headers share the copied frame, content digest,
source/screen/body/lease checks and 32-KiB complete public-envelope bound. Before
return, compare copied headers again as well as slots. No new selectors or input
authority are introduced.

Java canonical serialization now explicitly encodes the restricted response's
strings, safe integers, booleans and null in RFC 8785 form. Gson's escaped U+2028/
U+2029 output alone is not a cross-language canonical digest. Actual JVM/HTTP and
scoped CLI fixtures check accented text, supplementary characters, U+2028/U+2029,
literal backslash-u text, quotes and HTML punctuation against Python/TypeScript.

Sources: [header lifecycle/filter](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeHeaders.java),
[native copier](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiHeaderCopies.java),
[frame integration](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiRenderedLayouts.java),
[page projection](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipePage.java),
[Python validator](../../src/mcbench/native_game.py),
[TypeScript validator](../../backends/mineflayer/src/native_game.ts).

## Verification

Windows; pinned JDK 17.0.20.101, Forge 1.19.2-43.4.23 and exact external FTB
Library compile-only artifact. Game/render authority in the tests is synthetic.

Initial Gradle build/test passed in 29 s. The final geometry-before-content
helper and rounding/shadow regression cases passed the repeated client
test/build/writeTestClasspath tasks: **342 Java pass**, zero failures/errors/skips,
26 s. Nine new header cases cover lifecycle, unchanged operands, incomplete frames,
missing evidence, source expiry, immutable results, invalid markers/text, Unicode,
digest binding, clipping before reads, centering/shadow and bounds.

Selected native/contracts/records/quest/recipe suites: **293 Python pass**, zero
skips, 39.16 s, including eight additional malformed-header/Unicode/marker cases.
Changed Python Ruff and TypeScript build passed. The full Node suite passed
**134 tests**, zero failures/skips, 60.653792 s, with explicit pinned JVM/classpath
and Windows guardian Python. The actual scoped CLI returned the same Unicode
header text as the synthetic JVM; malformed shapes, raw full-title fields, invalid
markers, bounds, body replacement and late delivery remain rejected.

Candidate SHA-256:
`599ad772892d30d9f8d24fae33b279b3ad28e47e4e2866d42d6758f1da43f5fc`.
Built, confirmed absent from the installed Strata JARs.

The final evidence collector verified five installed artifact pins, exact native
title/page/helper/centering bytecode, compiled injection annotations and packaged
five-hook configuration. It confirmed no bundled JEI/FTB classes, request schema
consistency, 38 source snapshots and 523 local links. Tracked `git diff --check`
passed with CRLF warnings only. Bytecode inspection cannot prove actual Mixin
application or authentic callback/render behavior.

Private installed-bytecode audits, build/test logs, JUnit, hashes, source snapshots
and verification manifest:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-labels-01`.

## Remaining scope

This captures header and slot draw operands, not every annotation or final visible
pixel. Rich/tagged/custom ingredients, category annotations, decorators/overlays
and remaining content stay .1b.2b.2; history/category/page controls stay .1b.3.
Actual Mixin loading, native frame/Font/pose/viewport behavior, reference/input/
mechanics, clocks/overhead and isolation remain .1b.4. All parent rows remain open.

No desktop recapture/input, authentic client/server/worker launch, inference, soak,
capacity or study ran in this phase. The previous read-only capture showed the
Windows Security/OpenJDK permission prompt; its operator handoff remains pending,
without inferring a fresh desktop state. Strata inference remains $0 dispatched;
the long-horizon goal remains active, M7 conditional, and the exact Mineflayer/E9E
T03/G0 failure is preserved.
