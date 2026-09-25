# M1.6q.12 protected persistence preparation

Status: implemented_unverified for authentic paired integration. G1-G5 not_run.

The read-only diagnostic uses native09's retained initial tree as data under
fresh FileLease custody. It independently verifies the sealed native09 bundle,
current public launch binding and original provenance. It never constructs a
live ProbeVanillaSession, reopens a writer job, changes configuration or launches
a game/model. Initial measurements: source-tree validation1.047s,
directories/settings0.109s, VanillaPersistence initialization8.797s. Three
snapshots account for4.802s; the final snapshot discards all its hashes and keeps
only tree membership before the final lease hashes selected files again.

`vanilla_persistence._immutable_lease` now enumerates fresh root membership,
requires it to equal the previously checked selected files within those roots,
and enforces the same root/count/file-size/aggregate-size limits. FileLease still
hashes every selected file through newly retained handles and rechecks membership
after acquisition. This also rejects an unselected file added after layout
validation instead of recording it as a tree member without its own held handle.
Failure cleanup and stopped capture remain unchanged. No public skip option or
cross-call cache is introduced.

```text
pytest tests/test_persistence_membership.py tests/test_vanilla_persistence.py tests/test_pack_restore.py -q
pytest tests/test_persistence_membership.py::test_file_added_after_enumeration_refuses_and_closes_partial_custody tests/test_probe_saved_body_runtime.py::test_body_profile_preserves_pair_custody_and_stopped_exports tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save -q
```

The initial run retains58 passes and one failed new assertion in25.82s. That
assertion compared ordinary Windows paths with canonical extended paths before
reaching the injected mutation. Correcting the expected path made the case
exercise the intended late-addition refusal and handle cleanup. The second run
passes all3 cases94.53s, giving61 distinct passing cases and no skips. Retain the
original failure, source and logs. Initial Ruff also found an unused import;
it was removed. Final Ruff/whitespace pass; two existing Typer warnings remain.
These tests use synthetic saves/process responses and real Windows file custody.
They cover late additions/removals/byte changes, external-Java additions,
post-enumeration mutation, stopped capture/restore and the relevant pair paths.

One changed read-only diagnostic runs after tests terminate. Persistence takes
6.781s versus8.797s; snapshots fall from three to two. Tree/settings components
are unchanged and measure1.203s/0.125s. Both diagnostics deny two write-opens,
close all leases and leave the input tree unchanged. The complete persistence
state (including its lease inventory) has identical digest
`ca7690b66712210751f87f734f54d9d24c7d0ecd37ddb56f0cfa82ecaf78c1ee`.
The input snapshot digest remains
`21dd1c6b6a171dff072905adf37a36f0fe4b8829a2fe6ede289be53075286c09`.
These are instrumented component timings, not complete paired-runtime evidence.

All40 real authority tables remain unchanged at$4.887796; no owned runtime.
No native10 trial is selected or run. Preserve native01-09 failures, consumed
inputs, all budget holds, and parent300s/writers200-170s/servers60-60s bounds.
D18/D19 remain M0-only. No inference spending authority is added.

Next inspect worker-import ordering: current preparation imports both workers
after both finite writer windows begin, although those imports need no server.
Determine whether the existing parent-owned runtime/configuration custody can
support imports before writer acquisition, while preserving original parent
clocks, durable stop receipts, full pre-dispatch validation and no replay.
Resolve that dependency before choosing another full paired attempt; do not
assume the component speedup alone establishes sufficient window capacity.

Coverage inherits M1.6q.11: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Full live matched-state/tools, native admission,
authoritative clocks/disposal, T05/T10 and complete root/helper isolation remain
open. M0/G0 and unrelated M2-M7 remain unchanged.

The first final-audit script refused SOURCE_SCOPE because it omitted the
intentional SPEC addition from its changed-file allowlist. Preserve that script
and failure. Correct the allowlist to exactly SPEC plus vanilla_persistence.py;
the separate audit still requires every previous SPEC byte and JSON example to
remain unchanged after removing the new explanatory paragraph.

Final audit passes. Private evidence is sealed at
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-protected-preparation-01`:
4,243 files / 12,231,390 bytes, SHA-256
`0d9152df0ba37c3d9081b31c0b715001f1d4179ecc99ba89c74797dd14ea4067`.
Independent bundle verification passes. It contains440 source files, both
diagnostics and exact state inventories, initial/final tests and failed audit,
fresh authority/process checks and documentation snapshot. All423 prior
milestone IDs remain, M1.6q.12 is added,1,674 local links pass; progress remains
append-only and prior SPEC text/JSON are preserved. This pointer follows the
archived documentation snapshot. Never mutate the sealed root.
