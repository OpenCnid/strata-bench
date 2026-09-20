# Explicit EMI crafting discovery

September 20, 2026. Operator-only. M0.3b.3.2.4b.2d / G0 item 3; partial
F01/F05/F06/F09/F16, N01/N03/N04/N06, T01/T02/T03/T07/T10/T12/T13.
Implementation evidence is separate from the pending authentic craft.

The previous native run collected the three processed ingots, then JEI returned
a valid empty furnace recipe page. Installed EMI 1.1.24's PluginCallerMixin
explicitly skips jei:minecraft recipe registration, while retaining categories
and runtime callbacks. The retained client log also shows its effectively empty
vanilla registration and EMI's ordinary crafting recipe load. This is a source
selection compatibility issue, not evidence that the server has no expert recipe.

Forge capability minor 36 adds explicit source=emi for crafting item queries.
JEI requests retain their own route; no source is silently substituted. Both
Python/public schemas, generated TypeScript/validators and scoped CLI transport
carry the source into the existing recipe selection and craft validation.

The adapter requires loaded EMI artifact SHA256
`1f3902eae8d9e6a4c719a7c176d9f9deee12ec0487cf8a05a61c2d3ecf32d43d`.
It calls the public focused/index APIs and the pinned public loaded/hidden/disabled
predicates. Manager/index/connection changes fence the result. Targets and every
nonempty projected alternative must be indexed and neither hidden nor disabled.
Only the exact standard EmiCraftingRecipe, EmiShapedRecipe and EmiShapelessRecipe
classes qualify; their displayed inputs, shape and output must match the supported
plain native recipe. Custom/rich definitions remain unsupported. There is no
manager-wide recipe enumeration, transfer hook, crafting grant or UI replacement.

The existing 512-match/32-row/32-KiB/100-ms cooperative projection limits remain,
with a 65,536-stack index bound. Upstream calls cannot be preempted by that local
timer; authentic timing and the failed guardian bound remain separate gates.

Executed verification: pinned Forge compilation/reobfuscation and selected
Java definition/query/selection/crafting checks pass; TypeScript generation/build,
five focused Node transport/capability checks and two explicitly enabled
Python-to-JVM source-query cases pass. One unselected-by-environment JVM Node
authority case reports an explicit skip and is not counted as a pass. Targeted
Ruff passes. No broad suite rerun.

The installed candidate is SHA256
`ff5fbf54e9bbf9fb6aa9b69f8bd9636593b34b7efb082957273008b7cc351751`.
The predecessor and prelaunch client log are preserved. Operation-03 uses the
same saved world and materials under epoch 3, without repeating processing or
collection, resetting resources or increasing existing exposure limits. Its
public source query may wait up to ten seconds for ordinary EMI startup; only
read-only source-unavailable results are polled. Mutations are not replayed.
The actual result is pending; all prior failures and costs remain.

## Authentic results and remaining execution failure

Operation-03 delivered the exact 3x3 expert furnace recipe through explicit EMI,
including the empty center and the five andesite/three polished andesite inputs.
The ordinary crafting table opened. The craft failed REVISION_CONFLICT after
partial grid inputs; its unknown receipt and all 25 primitives remain. No furnace
was made. The save accounts for the original materials in the player plus four
dropped item entities totaling five andesite.

Forge minor 37 separates changing derived result previews from owned-slot/cursor
continuity for non-result clicks, then adds a charged fresh full server-output
barrier after manual grid completion. The partial first-row slab preview motivated
this change, but the original exact received/current difference was not logged.
Operation-04 recovered the old drops through ordinary pickup and reached explicit
EMI discovery again, but crafting failed after its first ingredient. Thus this is
not a qualified repair. Its 16 primitives and unknown receipt remain; all resources
again reconcile, with five andesite dropped and no furnace. No mutation was replayed.

The four corrected-fixture operations retain 80 primitives and 1823.891 s.
Operations 03/04 narrowly satisfy the unchanged guardian bound; prior failures
remain part of aggregate T07/G0. Exact machine processing/collection and EMI
discovery are narrow authentic successes; crafting and complete gate qualification
remain failed/incomplete. Next diagnostic adds bounded private source locations
without exception messages or data, before any further Forge craft attempt.

## Operation 05 and the next feedback candidate

Operation 05 again discovers the exact EMI expert recipe but fails unknown craft `8177553c-c197-4ef2-be49-c65ac4986de5` with REVISION_CONFLICT. The new private source-location log identifies GameInventory.Steps.tick:68: its verified server reply differs from the current owned view. The precise differing state was not captured. Two intents, 38 primitives and 397.703 s remain charged; aggregate 118 primitives/2221.594 s. Saved player plus drops preserve all inputs: five andesite and three polished andesite dropped, three ingots owned, no furnace. Machine remains empty at 8000 RF. All processes terminal, arguments retired; unchanged guardian bound passes narrowly at 445.1679 ms, without superseding earlier failures.

Minor 38 implements one fixed charged refresh only if the reply matches the full predicted owned post-state and the current view is exactly the pre-click owned state. It never repeats the click; repeated or unrelated changes still fail. Non-quick-move replies additionally preserve every unaffected owned slot. The final fresh server-output barrier remains. Bounded private diagnostics record mismatch classifications/slot indices. Thirty-four focused Java Inventory/Grid/Crafting checks and the build pass (23 s); TypeScript build and the capability identity check pass. This candidate is not authentically qualified, and no causal diagnosis beyond the logged failure location is claimed.

## Operation 06: unrelated backpack state

Candidate `ccd0aa4edd54147aa31b3aabea7ab20638a927cbf76390631389a550a7366655`
failed craft `19988bff-d5ca-4714-bef3-84964c706b5c` with REVISION_CONFLICT.
The reply exactly matches the predicted transfer; current cursor and ingredient
also match. Only owned slot 45 differs, containing the existing Sophisticated
Backpacks backpack. Current state is not the exact pre-click state, so the new
reacquisition rule correctly does not activate. This does not establish the
cause of the backpack metadata change.

Independent saved-state audit preserves full player-plus-drop NBT counts:
five andesite dropped, polished andesite and three ingots owned, no furnace;
machine empty with 8000 RF. Two intents, 29 primitives and 401.844 s remain
charged. Aggregate: 147 primitives/2623.438 s. No mutation replay or refill.
Client/server terminal, arguments retired; guardian 475.203/500 ms passes
narrowly while previous timing failures remain.

The pinned Forge network serializer sends item share tags, while the bridge's
current private identity includes full saved capability state. This is a
source-backed distinction, not yet evidence that it caused this failure.
The next diagnostic retains at most 128 component snapshots of at most 16 KiB
each and logs at most 16 changed field paths/types/hashes on a mismatch. It
exports no component values or gameplay observations and does not change
acceptance. Candidate `5432b56ef6a6fa6d7cd6f1d68116df22e3a147da4a5c586738455f9a608e4351`
compiles/reobfuscates successfully; operation 07 is in progress on the same
saved resources with a distinct scope/epoch. No inference or desktop input.

## Operation 07 and exact metadata restoration

The bounded diagnostic identifies `slot45/tag/contentsUuid`: absent in the
confirmed server reply, an int-array UUID in the later client state. Native
craft b0e405b3-9d02-426f-adb0-439be5d6b285 fails REVISION_CONFLICT; the public
checker ends LEASE_EXPIRED. All original full-NBT player/drop resources reconcile,
with both ingredients dropped and no furnace. Retain 45 primitives/398.735 s;
aggregate 192/3022.173 s. All processes terminal and arguments retired. Guardian
384.7081/500 ms passes narrowly; earlier failures remain. Pinned BackpackWrapper
can create this UUID when initializing its inventory handler, but the originating
caller is not established. The field is in the ordinary tag: switching to share
tags alone would not remove the observed disagreement and was not implemented.

Minor 39 permits one charged fixed read when only untouched client components
differ, sharing the existing per-click refresh allowance. IDs/counts/positions,
cursor and clicked stack must remain exact. Both the renewed server reply and
current view must satisfy the ORIGINAL full component identities and predicted
transfer before another click. No field is stripped, no stack rewritten, no
mutation repeated, and no deadline/budget increased. Persistent client drift or
changed server metadata still rejects. This is recovery to the same acceptance
state, not acceptance of changed metadata.

Executed: Java Inventory/Grid/Crafting 35 checks pass, no failure/skip, pinned
build/reobfuscation 22 s; TypeScript build and named Forge capability test pass.
The first Node selector matched no cases and is not evidence. Operation 08 uses
candidate `5424bfd7d7d75d2149321e4edeb8d2d2d7c9f1345d740c6989bb034975758c18`
on the same saved resources, fresh epoch/scope, no inference or desktop input.
Its authentic outcome is pending.
