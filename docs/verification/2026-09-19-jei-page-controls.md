# JEI navigation-control draw operands — September 19, 2026

Operator-only; exclude this report and its evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.3a is **implemented_unverified**. SPEC v0.2.22 / D06,
Forge minor 30, policy `jei-task-drawn-slot-header-controls/3`, native response
`strata/NativeRecipePage/3`. Coverage is `slot_header_control_draw_operands`,
still `complete:false`. The eighteen action kinds are unchanged.

Affected coverage: F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial
T01/T03/T06/T07. No aggregate gate or milestone closes.

## Implementation and native basis

The exact installed JEI 11.8.1.1034 RecipesGui draws four GuiIconButtons in order:
next category, previous category, next page, previous page. A sixth optional
exact-target Mixin observes each native render's HEAD/RETURN. It neither replaces
nor repeats native rendering or input. Require four distinct objects after the
header lifecycle and before layouts, unchanged geometry/flags, identity pose and
the existing complete Pre/Post frame. Missing, repeated, nested, changed, late
or incomplete evidence invalidates the frame.

[GameRecipeControls](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeControls.java)
copies immutable private widget/rectangle operands. Check containment before
reading flags. Each public row contains only kind and state; contained buttons
are enabled when native active and visible both permit input, otherwise disabled.
Clipped rows reveal no flags. Native GuiIconButton rendering itself does not
skip drawing merely because the input-visible flag is false.

The copied controls share the page's origin/source/screen/body authority, age,
canonical digest and 32-KiB bound. Before delivery, compare the private copied
controls again as well as headers and slots. Python and TypeScript strictly
validate exactly four ordered rows, enum strings, no extra fields and digest.
No input selector, geometry or widget object is exported.

Installed input bytecode also establishes that Screen mouseClicked previews with
SIMULATE, while mouseReleased uses EXECUTE. The ordinary router tracks a pressed
handler and clears it on unfocus. The required .3b motor must preserve this
sequence and cancellation cleanup. It is **not implemented** by this observation.
History Back (.3c) remains distinct from Close-to-quest; rich/custom/overlay
coverage and authentic qualification (.1b.4) remain required.

## Verification

Windows, pinned JDK 17.0.20.101, Forge 1.19.2-43.4.23 and the exact external
compile-only FTB Library artifact. These tests use synthetic game/render authority.

- Gradle client test/build/writeTestClasspath: **350 Java pass**, zero failures,
  errors or skips, 26 s. Eight new control tests cover ordered immutable copies,
  missing/nested/duplicate draws, changed operands, clipping before reads, malformed
  geometry/state, freshness, poisoning and digest/private-field behavior.
- Selected native/contracts/records/quest/recipe suites: **301 Python pass**,
  zero skips, 39.66 s, including eight additional strict-control negative cases.
- Full Node suite: **134 pass**, zero failures/skips, 62.0797557 s. Actual JVM/HTTP
  and scoped CLI fixtures return the controls; malformed shapes, raw widget fields,
  ordering, enum coercion, digest, body replacement and late delivery reject.
- Changed Python Ruff and TypeScript build pass.

Candidate SHA-256:
`f10e7ad6ddbbf48df176183cc4e0dc60891a50d2528858ceb452b2c96a6aa625`.
It was deployed for a separate authentic check after these tests. Deployment or
successful startup alone does not verify frame hooks or page parity.

Private logs, installed-bytecode audits and verification material:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-controls-01`.
Authentic deployment evidence is separately retained in
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-live-01`.

The user completed the Windows Security prompt; a fresh capture confirmed its
absence. No inference, soak, capacity certification or study ran in this phase.
The long-horizon goal remains active, M7 conditional, and the exact
Mineflayer/E9E T03/G0 failure remains unchanged.
