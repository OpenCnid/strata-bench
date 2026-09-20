# Immutable JEI slot draw copies — September 19, 2026

Operator-only; keep this report and its evidence outside gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.2a is **implemented_unverified**. The internal render
reader now returns immutable copied primitives, never mutable JEI layout data.
This advances the current-page foundation; it does **not** implement or advertise
a public recipe-page observation. SPEC v0.2.19 records D06's extension. Public
Forge minor 27, eighteen actions and existing policies remain unchanged.

Affected coverage: F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial
T01/T03/T06/T07. No aggregate gate or authentic compatibility claim changes.

## Source and behavior

Inspection of the exact installed JEI 11.8.1.1034 shows that RecipeSlot.draw
selects an optional displayed ingredient, passes a present value to drawIngredient,
then draws its overlay. Selection is cached/cycled inside JEI. Reading a mutable
layout later is not a capture of the earlier draw operand.

The new optional slot Mixin observes normal slot-draw begin/end, the return of
the ordinary displayed-ingredient getter, and the actual typed operand at
drawIngredient entry. It invokes no additional selection getter. Selection
returns outside that slot's own draw are ignored, including category queries.
Within a draw, require one selection and exactly one matching operand when
nonempty. A missing hook cannot become a false empty slot.

The existing outer draw wrapper preserves its one native call and original
exception. It now brackets the slot-copy lifecycle. Only the layout's bounded
public slot list, in native order, can contribute. Missing/repeated/nested/wrong
or unfinished callbacks invalidate the whole frame. Its complete Pre/loop/Post,
screen/runtime/origin/dimensions, 100-ms frame and 250-ms age fences remain.

Before category/content reads, reject a wholly off-screen layout. Before reading
slot role or ingredient, require the slot rectangle wholly inside both its layout
and viewport. Omit clipped slots, set an explicit clipped flag and retain native
indices. This rectangle check is not proof of final-pixel visibility through
decorators or overlays; that remains an authentic qualification requirement.

Immutable copies contain category ID and slot index/role plus an empty or
unsupported marker, or plain item/fluid registry ID and positive amount. Require
the exact JEI TypedIngredient implementation and public ingredient visibility.
Its inspected type/value fields are final; no private fields are read at runtime.
Unknown wrappers/types and tagged components receive an unsupported marker with
no raw ingredient payload. No alternate-ingredient stream, recipe graph, NBT,
tooltips, private quest predicate or transfer hook is read/exported.

Bounds: 128 expected slots per layout, 32 layouts, and 32 KiB for the aggregate
copied-layout JSON array including commas/brackets. Malformed/oversized data and
mixed copied/uncopied frames reject, never truncate. Immutable records copy their
lists; constructing JSON produces new objects. No transport exposes these copies
yet, and a future public envelope must apply its own complete-response bound.

Sources: [slot lifecycle/data](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeSlots.java),
[native copies](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiSlotCopies.java),
[slot hooks](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/mixin/JeiSlotDrawMixin.java),
[frame capture](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeRenderCapture.java),
[native lifecycle](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiRenderedLayouts.java),
[new cases](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameRecipeSlotsTest.java).

## Verification

Windows; pinned JDK 17.0.20.101, Forge 1.19.2-43.4.23, exact external FTB Library
compile-only dependency and pinned JEI API. Executed in `java/`:

```text
gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
```

Initial build/tests passed in 26 s. Review added selection-outside-draw handling
and failure invalidation/array punctuation accounting; the next build passed in
26 s. Final off-screen-layout and exact-wrapper guards and geometry assertions
were then compiled and tested: **326 Java pass**, zero failures/errors/skips,
25 s. Existing Gradle/Java deprecation warnings remain.

Twelve new cases cover immutable native order, observed empty selection, missing
operand hooks, wrong/duplicate/unselected operands, selection authority, clipping
before any role/content reader, native-index retention, unsupported markers,
identity/order/completeness, nested/failed callbacks, invalid data/bounds, mixed
frames and byte limits. These are synthetic renderer/ingredient callbacks.

The collector verifies all five installed FTB/XMod/JEI hashes, installed method
and operand paths, exact TypedIngredient getter shape, compiled hook ordering,
packaged Mixin config and no bundled FTB/JEI classes. Bytecode inspection and
compilation do not exercise actual Mixin application or authentic rendering.

The final collector passed with 19 source snapshots and 515 local links. Tracked
`git diff --check` passed with CRLF warnings only.

No public Python/TypeScript/schema/transport change occurred, so those suites
were not rerun. Their retained results are 262 Python and 131 Node pass from
the [task lifecycle evidence](2026-09-19-quest-jei-lifecycle.md).

Candidate SHA-256:
`5e134a386a81de9dda28e41ca51972e3e37e716bf45fdd4a5617a83a499e987d`.
Built, **uninstalled**. Private logs/JUnit, installed/candidate bytecode, hashes,
source snapshots and verification manifest:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-01`.

## Remaining scope

Parent .1b.2 remains in_progress. Child .2b retains category/page labels, rich/tagged/
custom ingredients, decorators/overlays and all remaining displayed content. Child
.2c retains complete native/Python/TypeScript/scoped CLI transport, source/body/
lease/content/schema fences and explicit coverage/capability identity. Prior .1b.3
retains history/category/page controls; .1b.4 retains authentic hook/frame/input,
overhead/mechanics and isolation qualification. The native-copy candidate alone
does not establish readable full-page parity or a release gate.

No desktop capture/input, real client/server/worker launch, inference, soak,
capacity test or study ran in this phase. The last observed Windows Security
prompt still has an outstanding operator handoff; no fresh state is inferred.
Strata inference remains $0 dispatched. The long-horizon goal remains active;
M7 conditional and exact Mineflayer/E9E T03/G0 failure retained.
