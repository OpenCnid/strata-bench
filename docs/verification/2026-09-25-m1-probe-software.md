# M1.6i sealed software for paired vanilla preparation

D20 continuation. Affected F01/F04/F08/F09/F11, N01/N04/N05/N06/N08,
C12/C22/C23/C24, T01/T06/T07/T11. M1.6i is implemented_unverified for
authentic software/native game integration; M1.6 remains in_progress and G1
not_run. M0/G0 and unrelated roadmap work remain unchanged.

The optional `held-pair-sealed-vanilla-inputs/1` path connects the existing
read-only sealed-pack resolver to the held two-arm copier. The pack lock must
match the pair's committed common identity. Both output plans contain exactly
the reviewed immutable server software plus every registered state file;
software paths, hashes, sizes, source arms and Java identity are checked.
World paths retain their names. Only the six vanilla mutable files may map from
`external/` to the actual server root, and all six plus `world/level.dat` are
required. Unknown external state, imported session locks, unsupported world
files and sealed empty software directories refuse before writer intent.

The entire sealed materialization and its inventory metadata remain under
actual Windows file leases through both writer continuations. Resolve again
under custody, before use, and before success. The copier sees explicit files,
not the broad ancestor used for path containment. Operator/private manifests,
client files and provisioning data are excluded from its copy map. Storage
accounting includes the held software plus both source/destination copies.
Unlaunched close, single-use pair identity, failure fencing and retained
resource/cost holds preserve the preceding policy's semantics.

Tests exposed an existing writer-plan containment defect: ordinary and extended
Windows spellings of one directory compared as unrelated paths. Writer plan
validation now normalizes all source, input, workspace and evidence paths before
testing containment. Matching spellings still validate; a spelling change
cannot permit an output beneath its source. Serialized plan identity is unchanged.

## Verification and retained failures

**52 distinct focused cases pass.** Tests use synthetic sealed pack bytes,
synthetic checkpoint/probe records and substituted writer execution. The pack
resolver, checkpoint registration, coordinator and Windows file leases are real.
They cannot qualify a Minecraft or native probe run. Twenty new cases cover
software/state mapping and rejection, scope, held writes, callback failure,
Windows path aliases and restored-object refusal;32 existing affected writer/
copy cases also pass. Ruff and whitespace checks pass.

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe -m pytest tests/test_probe_vanilla_inputs.py tests/test_probe_world_copies.py tests/test_writer_preparation.py -q -x -k "not actual_native_pair"
# Eight passing cases above were retained; continue remaining cases after
# correcting the single error-code expectation instead of rerunning them.
.venv/Scripts/python.exe -m pytest tests/test_probe_vanilla_inputs.py tests/test_probe_world_copies.py tests/test_writer_preparation.py -q -x -k "not actual_native_pair and not exact_sealed and not changed_software and not pack_identity"
.venv/Scripts/python.exe -m pytest tests/test_writer_preparation.py -q -k probe_software_cannot_accept
```

The first command retains8 passes/one failed assertion; the second passes43
in365.70s; the final newly added restored-object case passes1. These are52
distinct passing cases, with no claim that the original failing command passed.

The first fixture attempt refuses SPENDING_CEILING_REQUIRED. The second refuses
PROBE_PACK_MISMATCH because its original checkpoint fixture generated an unrelated
pack. The fixture now registers its finite probe ceiling and selects its sealed
pack before any checkpoint commit. A third attempt passes the positive case
and one refusal, then exposes the Windows spelling issue in a negative test.
The fourth attempt passes eight cases, then retains a wrong expected error in
the mutated-template test: the resolver correctly reports
PRIVATE_INSTALLATION_CONTENT before a generic materialization mismatch. Only
that test expectation changes. Retain every attempt; no committed source was
relabeled or rearmed.

Two existing native writer plans from the successful M1.6h capture pass the
normalized containment check without modification or native rerun.

Read-only reconstruction passes29/29 checks on the sealed positive case. It
joins pair/pack/world identity, canonical plan digest, complete compiled source
inventories, both13-file destinations and every source/copy byte, explicit
unlaunched discard, retained200 synthetic units and both arms' capacity holds.
The prepared owner is FENCED after fixture teardown. No archived absolute path
is followed outside the sealed bundle, and the original database/seal remain
unchanged. All40 real authority tables equal the preceding checkpoint and the
before/after snapshots; exposure stays $4.887796/$10. No owned runtime remains.
The final evidence collector initially stopped before sealing because an empty
PowerShell pipeline produced no process file; explicit array serialization fixed
the collector. This did not repeat any execution or change a test verdict.

| Private evidence store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-probe-software-01` | 8,318 / 33,267,914 | `91684c51ecd30e542058bee31e07e10e06f9c05feb556ab34b6c9f804e84b42e` |
| `2026-09-25-m1-probe-software-audit-01` | 3 / 6,261 | `b217ffd42bf53122181f723e7ed7e87d9a6780cecc32008fd1b8194bf3d8a5f0` |

No Minecraft, native writer or model is launched by this verification. No M1
spending authority is inferred. Actual protected software copying, capable
server/worker launch, complete initial state equivalence, native probe admission,
stopped export and one-way disposal remain required. Sealed empty-directory
support is explicitly refused by this candidate, not omitted or declared passed.
