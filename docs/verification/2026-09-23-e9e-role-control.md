# Exact E9E roles and Create configuration consumers

**Result:** M0.3.2b.5 is verified for its bounded role/consumer contract.
Authentic output records 234 loaded mods, all six config roles and six correct
Create getter reads. Corrected offline reconstruction passes 18/18 checks.
The original 44/45 audit remains a sealed parser/catalog failure; no game replay
was needed. Complete E9E profile admission and G0 remain open.

M0.3.2b.5 addresses the remaining role/legacy findings behind G0 item 2 and
private setup/profile admission. Coverage inherits F01/F05/F10/F16,
N01/N03/N04/N06/N08, C03/C04/C18/C24 and partial T01/T02/T10/T13.
The previous actual LLM/Mineflayer pilot and Sophisticated Core control remain
verified. No unchanged successful game or model run is repeated here.

## Implementation

[e9e_role_control.py](../../evaluator/src/strata_evaluator/e9e_role_control.py)
implements a fixed operator-only producer and strict private consumer together.
The producer binds Create 0.5.1.i, Sophisticated Core 0.6.4.730 and the official
Create overlay. It records the complete loaded ModList and the six previously
selected config registrations. For Create, it verifies registered SERVER
source/spec/data identity, loaded status, exact current raw values and absence
of the three legacy paths, then calls each current getter twice and rechecks
the raw state. Getter cache initialization is disclosed; there are no settings
writes, saves, reloads or guessed migrations.

| Current path | Required raw and getter value |
|---|---:|
| `logistics.defaultExtractionTimer` | 8 |
| `schematics.schematicannon.schematicannonShotsPerGunpowder` | 400 |
| `schematics.schematicannon.schematicannonDelay` | 10 |

The legacy paths remain `logistics.defaultExtractionLimit`,
`schematics.schematicannon.schematicannonGunpowderWorth` and
`schematics.schematicannon.schematicannonFuelUsage`. Absence does not establish
equivalence to current settings. The five historical strict file failures remain
retained, and the old 263/268 file result is not rewritten.

The catalog hashes top-level mod JARs, recursively declared JarJar children and
one exact reviewed custom-loader resource without extraction. Paths, nesting,
counts and bytes are bounded; duplicate ZIP
names, unsafe child paths and changing inputs reject. Metadata declaration is
distinct from actual loading. Runtime IDs/filenames must match catalog content;
identical embedded copies retain every candidate path. Different bytes under
the same matching identity reject. No unique physical parent is invented.
Forge/Minecraft sources remain subject to the independent bootstrap/lock evidence.
An empty runtime archive-root path is accepted only when every content match is
nested; the result explicitly marks that path unavailable. Empty top-level or
platform paths reject. This does not invent a physical path or authenticate
the runtime by filename alone.

Private ingestion requires exact record shape, source identities, ordered unique
loaded IDs, six registrations, expected raw/getter values and absent Inventory
Sorter. It accepts Rhino's `8.0` encoding only as the exact required numeric value;
booleans, strings, fractional differences and inconsistent cached values reject.
Raw observations and actual loader paths stay private. Parsing and catalog
matching alone cannot authenticate a process, certify transitive acquisition,
qualify mechanics or award score credit.

## Source and local preflight

The initial stopped E9E server catalog contains 261 top-level/nested entries
with 243 declared mod-ID occurrences and no Inventory Sorter declaration.
Two pairs contain identical embedded bytes under different parent JARs; both
candidate paths are retained. These are static observations, not a loaded-mod
or complete distribution claim.

The first catalog preflight rejected actual `META-INF/jars` entries because the
implementation assumed `META-INF/jarjar`. It now accepts the safe relative path
explicitly declared by metadata. Both layouts and traversal rejection are tested.
No game was launched for this failed preflight.

The standalone JVM fixture uses the actual pinned Rhino, Forge and Create
`CLogistics`/`CSchematics` classes and getters, with synthetic in-memory config
registration, tick events, ModList and an AllConfigs facade. The final fixture
passes the complete producer-body/private-parser check: six getter reads and
exact raw/legacy assertions. It does not exercise real loader discovery or the
AllConfigs/ModList source endpoints, and does not replace authentic integration.

Retained fixture failures exposed escaped/CRLF endpoint matching in the test,
Rhino access to a package-private immutable-list implementation, and integral
numbers serialized as decimals. The producer now copies metadata into a public
ArrayList; the parser checks exact numeric values while preserving their original
wire representation. An attempted bitwise canonicalization did not change
Rhino's encoding and was removed. All setup corrections occurred in private
synthetic memory/files, never in the original installation.

Focused verification:

```text
pytest -q tests/test_e9e_role_control.py tests/test_e9e_config_consumer.py
ruff check evaluator/src/strata_evaluator/e9e_role_control.py tests/test_e9e_role_control.py
node --check <private generated role-control.js>
```

The final selection passes 38 Python tests; Ruff and syntax checks pass. The initial unused-import
Ruff failure is corrected. The telemetry 0.3.13 JAR is unchanged and is not rebuilt.

## Authentic output and retained parser failure

`2026-09-23-e9e-role-live-01` records one complete result with no script errors.
All 234 loaded IDs are unique; the four legacy/client-only config names are
unregistered, Sophisticated Core COMMON is loaded and Create SERVER is loaded.
The current Create values are 8/400/10 both before and after six matching getter
reads. All three legacy keys are undeclared and absent. No settings are migrated.

The initial audit rejects seven empty nested archive-root path strings before
catalog reconciliation, retaining **44/45** checks. This is a parser/catalog
failure; the complete getter output is present. All six retained server/ten
outer processes stop normally in 163.812/167.750 seconds. The callback clock
records 207 ticks/14.9488879 seconds, without full active-time/avatar qualification.
Original 18,225 files, 1,542 runtime inputs, sealed fixture and all 39 accounting
tables are unchanged. No player, shared-desktop input or model request occurred.

Original failed bundle seal:
`d6e885fc185d80d2b08251245b76dd8c59c0fd179fa810f57bc26a2f3f557734`
(344 files/44,545,853 bytes); audit:
`0dc2d51157dac3cbe0aa01b8c1a750bde0eb73536fbd6465fef46f38d34e1ab4`.

## Corrected offline reconstruction

The stopped output identifies one additional custom-loader case:
Crash Assistant's `IDependencyLocator` explicitly loads
`META-INF/jarjar/crash_assistant-forge.jar` through its own code source and a
`jij:` filesystem root. It is not a JarJar metadata entry. Exact pinned bytecode,
service registration and nested bytes were inspected without executing that code.
The catalog permits only this reviewed outer/child hash pair:

- Outer: `11674636141f3be9ea22c8b274e58380f33169c2e4f5e9605cf6865f467d90a9`
- Child: `6d034fcb47eda3cd10b2e05c741058e7641015ce7ca7f675aff9692df454631c`

The corrected catalog has 262 entries and binds all 232 non-platform loaded IDs.
Forge and Minecraft remain in separate bootstrap evidence. The seven empty
roots each bind exclusively to nested content, with explicit unavailable-path
status; identical SpectreLib copies retain both parent candidates. Inventory
Sorter is neither loaded nor declared. This is server-role evidence; it is not
a substitute for complete client-role or acquisition reconciliation.

`2026-09-23-e9e-role-reconstruction-01` passes **18/18** checks against the complete
sealed original bundle. It verifies that the producer body is unchanged, the
catalog adds only the reviewed nested child, all original/runtime inputs and
stopped Create config still match, original accounting is identical, and no Java
process remains. The 44 passing original checks and its failed result are
retained. The new parser consumes the same original log and leaves profile,
mechanics and score authority unqualified. No new game/model run was launched.

Reconstruction seal:
`e2a53cd73d16505935ce604729074b93094e1c86e3dfb6920e9a5e9d9d96d305`
(11 files/325,398 bytes); audit:
`518c59e207ced370f51a0b60d2b1bd70603298220bbbd1c759d5a76e453cb166`.
Both bundles are private under `C:/Users/Darian/.strata/evidence/`; bytecode,
vendor files, generated controls and raw loader paths are not published.

## Remaining scope

The durable E9E acquisition is still **ACQUIRED**, while the three vanilla
templates are SEALED. Next complete exact client/server installed-file provenance
and role inventories, then connect the retained file findings and current loaded
evidence to profile admission. Do not repeat this capture or the successful
consumer, handle or model pilot unchanged. Exposure stays **$2.831942 / $10**
with every unresolved amount reserved under D19.

Complete role/distribution reconciliation, source-backed legacy disposition,
expert mechanics/parity, profile sealing and qualified private scoring remain
open. D14 defers full isolation qualification to M1/G1. M0 is in_progress, G0
remains fail, and M1–M7 are preserved.
