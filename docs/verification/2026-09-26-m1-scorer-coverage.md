# M1.5 exact-profile scorer audit and machine resource contract

M1.5a's coverage audit is complete. M1.5b's completion-resource verifier is
implemented_unverified for authentic capture. M1/M1.5 remain in_progress;
T10/G1 remain not_run. This is required G1 work under D20, not an M3 study.

## Exact evidence and remaining acceptance

The existing [D14 report](2026-09-24-development-milestone.md) proves a private
development calculation, not protected scoring. Reverification of its sealed
positive report confirms one furnace output under history5, while every setup,
isolation, scientific and scoring qualification flag is false. The headless
negative uses history6 and yields zero output with the same false flags. These
are different exact profiles; the negative has no player/craft and cannot show
rejection of an otherwise valid tainted craft. Neither is upgraded by this audit.

| T10 obligation | Existing evidence | Required G1 evidence still missing |
|---|---|---|
| Reachable registered fixtures and valid trajectories | Actual E9E shaped furnace craft; authentic saved Thermal processing/collection; synthetic scorer positives | Every supported fixture on its complete protected profile, authoritative setup/team/resource source and correct private result |
| At least two valid strategies where available | Synthetic alternate recipe accepted; ordinary craft layout witness supports mirrored/offset recipes | Actual distinct valid strategies for the selected fixtures, with documented applicability |
| Idle and fake success text | Headless zero-output report; schema/text/raw-callback synthetic refusals | Connected protected fixture controls and private outcome/nonleakage joins |
| Duplicate events | Durable source/transaction conflict checks and idempotent authentic development import | Complete protected producer-to-score replay/duplicate controls |
| Gifted output and admin spawn | Synthetic source/resource checks; setup command history observations | Otherwise-valid authentic tainted craft/machine controls that earn no protected predicate |
| Incomplete/unstable machine | Synthetic contiguous-window calculator; saved processing evidence | Authenticated machine lifetime, input/output/energy/fluid provenance and continuous registered tick window, including interrupted/unstable negatives |
| Wrong recipe and normal mode | Synthetic predicate/witness checks; native expert setup points/history | Same-profile actual wrong recipe/mode trajectories excluded by protected scorer |
| Wrong team | Registered roster and native FTB point checks | Actual wrong-team trajectory denied without unproven attribution or leakage |
| Blinded fixture IDs and private criteria | Private stores/reports; package allowlist | Connected runtime/helper/client/probe/error/log boundary with positive permitted play |
| Read-only instrumentation overhead/mechanics parity | Inspected hooks and component timing; historical authentic telemetry | Declared exact-profile instrumented/reference mechanics and overhead verification, preserving all failed samples |

The stock scorer's `MachineEvent/1` accepts development counters. No authenticated
machine-consumption adapter exists. Saved before/after RF/items cannot establish
a causal processing window. The retained [machine evidence](2026-09-20-machine-crafting.md)
still includes its unknown deposit, failed guardian and separate collection;
none is replaced with a scoring pass. M1.5 retains all T10 controls above plus
the F04/F10/F16, N01/N04/N06/N08, C12/C18/C24 and T01/T06 dependencies.

An initial source-only concern about public event visibility was ruled out:
`GameEvent` already restricts visibility to evaluator, and a direct schema check
rejects public visibility. Existing tests reject text and raw craft callbacks.
No scorer edit or defect-fix claim is made for that concern.

## Source-backed completion boundary

Installed artifact SHA-256 values match the earlier exact-build inspection:

| Artifact | SHA-256 |
|---|---|
| Thermal Expansion10.3.1.25 | `ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c` |
| Nested Thermal Core10.3.0.9 | `20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5` |
| CoFH Core10.3.1.48 | `1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d` |

Private `javap -p -c` output covers exact MachineBlockEntity, MachineFurnaceTile,
FurnaceRecipeManager, IMachineRecipe and EnergyStorageCoFH. Two earlier guessed
class names fail and their outputs remain; one javap invocation returns0 despite
a class-not-found diagnostic. Complete inspection requires empty stderr and all
selected classes. No game classes are loaded or game process started.

The actual processing tick debits RF separately. `processFinish` validates inputs
before output resolution, then consumes inputs; a failed validation returns
without a completed operation. Recipe validation can refresh the selected recipe,
so the proposed begin capture belongs **after successful validation**. Native
automatic transfers/charging occur outside this completion bracket. This is why
a completion's output must not be assigned an inferred energy or sustained-time
credit.

[machine_witness.py](../../evaluator/src/strata_evaluator/machine_witness.py)
checks three private GameEvent boundaries: begin after successful validation,
outputs resolved, inputs resolved. Require one exact campaign/epoch/boot/tick,
consecutive sequences, transaction/dimension/position/recipe digest, no guessed
player actor, and the fixed unaugmented furnace profile. Verify exact input loss,
output gain and native effect order; preserve complete stack component identity
for the charge slot and unchanged process/RF/augment state. Refuse unsupported
probabilistic/tagged recipes, active augments, malformed/expanded layouts and
changed unrelated resources. This bounded first adapter does not remove later
fluid/augment/energy or alternate-strategy requirements.

The returned resource witness pins original event/recipe digests. Producer,
setup/team, sustained operation, energy, fluid and score flags remain false;
the private records are rejected by the current scorer. These auxiliary payloads
do not add a canonical top-level record or any gameplay endpoint.

Executed source verification:

- `pytest tests/test_machine_witness.py -q`: final53 pass in0.55s.
- `pytest tests/test_gameplay_package.py -q`:1 pass in0.54s, actual compiled
  client allowlist and ungranted-command denial. This is not runtime isolation.
- Changed-file Ruff and whitespace checks pass.

The first38 cases error during fixture construction because a tuple is not a
JSON payload value. Original source/JUnit/output remain. Positions now use a
bounded JSON list; corrected38 pass. Additional malformed-state checks and
distinct underconsumption behavior produce the final53. Do not sum overlapping
runs. No authentic machine capture, producer hook, ingestion or score is claimed.

Next implement exact loaded-code/thread/caller/recipe/lifetime capture for this
bracket and authenticate it through owned private telemetry. Then join per-tick
RF/operating history, registered setup/team/cutoff and complete T10 controls;
never turn the development calculator or current witness into score authority
by accepting caller-provided qualification booleans.

## Historical archive preservation

Positive development archive165files verifies with its original seal
`c8eee854b28d0c449808077e6cbb6922ee428b0c12ce77e9d61b7273989196cc`.
Negative archive's original329files and seal remain unchanged, but one added
`__pycache__/authority.cpython-312.pyc` makes its current folder fail the exact
inventory check. The cache is retained; its creator/cause is unknown. An exact
copy of the original inventory verifies at
`C:/Users/Darian/.strata/evidence/2026-09-24-development-negative-01-original-sealed-copy`
under the original seal
`6743b2fc6f2945965eab54c9c2c37f0eb22bc75108dccf741813b30213d89e82`.
Use that copy for EvidenceBundle reads. Do not claim the original directory is
inventory-valid, delete the extra or rewrite the original seal. The preservation
receipt initially fails RFC8785's integer limit for nanosecond timestamps;
decimal strings correct receipt serialization after the copy already verifies.
No game replay follows either evidence-handling correction.

New private source/audit evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-26-m1-scorer-admission-01`.
No paid inference authority changes. M0/G0, all historical profiles, failures,
holds and consumed decisions remain unchanged; unrelated M2-M7 are untouched.


Final audit passes463 source pins,437 unique milestone IDs,1,736 local links,
append-only history and54 distinct focused cases. All40 real authority tables
unchanged at$4.887796; no owned runtime/model/game dispatch. Source/audit archive
47files/7,235,005bytes, seal
78cf77ca8e620c6f0c2ed82fa8a9c644e6f2ceab6a16a40aabec73e023b60bdf.
This pointer follows the archived documentation snapshot. No authentic machine
capture or protected scorer qualification; T10/G1 not_run.
