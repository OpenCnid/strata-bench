# Private persisted Thermal furnace reference

September 20, 2026. M0.3b.3.2.4b.1; F01/F05/F06/F11/F16,
N01/N04/N06, C04/C09/C18, partial T01/T03/T10/T13 and G0 items 3/5.
**Implemented; authentic prepared baseline verified, operating-machine test pending.**

The evaluator now reads selected Thermal furnace state independently of client
receipts, using the existing bounded Anvil/NBT reader. It requires matching
persisted block/entity IDs and coordinates, unique base inventory slots, plain
item quantities, RF energy and typed process/active fields. Missing, packed,
orphaned or duplicate machines reject. Components, extended counts, augment
overrides and unsupported fluid/capability data reject explicitly. No entity
absence becomes an empty machine or a successful observation.

Source inspection uses the installed Thermal Expansion 10.3.1.25, nested Thermal
Core 10.3.0.9 and CoFH Core 10.3.1.48 bytes pinned in the
[native menu report](2026-09-19-thermal-menu.md). Actual `javap -p -c` evidence
establishes `ItemInv`, omitted-empty-list behavior, byte slot/count fields,
`Energy`, `Active`, `Proc`, `ProcMax` and `ProcTick`. Extended IntCount is a
distinct unsupported encoding. Initial guessed package names were rejected by
javap; the actual JAR entries supplied the inspected class names. No game APIs
were inferred from those failed lookups.

`python -m pytest tests/test_saved_blocks.py tests/test_saved_machines.py -q`
passes **102 tests in 1.01 s**, including 23 new synthetic saved-machine cases.
Full Ruff passes after four test formatting errors were corrected. These are
save-format checks, not evidence of machine processing. Private raw evidence:
`C:\Users\Darian\.strata\evidence\2026-09-20-machine-reference-01`.

A protected copy of the prior clean-stopped E9E development profile retains
18,214 source files with copied-byte hashes. A setup-only boot executes six
fixed, individually journaled operator commands with no connected client, then
stops normally in 181.109 s. Neither console access nor fixture instructions
are granted to gameplay. The original selected world region still matches its
preparation hash. This is development fixture administration, not a scientific
sample or player accomplishment.

The immutable saved baseline contains an empty Thermal furnace with 20,000 RF
and a nearby chest containing three `emendatusenigmatica:iron_dust`. These are
explicit setup resources. The first offline audit rejects an authentic empty
`ForgeCaps` compound. Inspection confirms it contains no entries; the reader now
accepts that exact empty compound and continues rejecting nonempty capabilities.
The failed audit is retained and no server setup or command is replayed.
Corrected independent audit `baseline-audit-02.json` passes against the same
saved bytes, with zero Java processes and no client joins. The final relevant
suite, including actual gameplay-package exclusion, passes **103 tests in
1.21 s**; full Ruff passes.

Baseline selected-region SHA256:
`1c3b7c2d674a9e233248d16606cc30d5c1c6776dd64c67e0f7d9da1879d25952`.
Private machine-reference SHA256:
`4a47f0ca9321874d17e485c0626bebc11a4d38588717d431af5aa048105ff2c0`.
Server-result SHA256:
`6339bf8bcf7a5aad2213a41b360e329933e3e66030ae5b9066f261df124c48d1`.

The private command is `python -m strata_evaluator.saved_machines --world
<stopped-copy> --dimension <id> --point <x> <y> <z> --output <private-report>`;
synthetic inputs additionally require `--is-example`. Output has the normal
private digest envelope and explicitly false flags for proven artifact binding,
snapshot consistency, causal credit, registry membership and scoring provenance.
The caller must supply separate authentic launch/clean-stop/setup evidence.
No commands, server handles or evaluator data enter gameplay capabilities.

Next run a prepared private conformance copy with fixture-provided energy and
input resources, collect a clean saved baseline, operate the ordinary machine
through scoped API actions, and reconcile the final machine/player state.
Prepared energy is not ordinary energy-supply qualification. Full crafting,
machine routing/fluid/augment support, gifts/negative scorer controls and all
remaining M0/G0 requirements stay open. Existing worlds and failures are retained.

The first operating trial fails before worker admission: the private harness
mistakenly supplied the settings fingerprint for the game bridge. Those identity
domains differ; NativeGameRuntime also hashes its full capability contract.
The owned listener reports game fingerprint
`7cc46243b1f430042632cb9b0e61fa82ea3f49d8f9dd56ae7fbbd6b36f4e1fb5`.
The failed sample is retained, with zero native mutation intents, unchanged
furnace/chest resources, normal server save, zero Java and retired launch args.
It consumed 404.516 s of development elapsed time, which remains recorded.
A fresh attempt pins that actual game identity and recomputes capability/authority
digests before launch; it retains the prior sample, current world state, 90-second
worker, 1,000-primitive and 500-ms guardian bounds. No ambiguous action is replayed.
