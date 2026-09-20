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
