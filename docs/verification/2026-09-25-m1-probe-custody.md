# M1.6f held pair preparation and atomic reservations

D20 continuation of M1.6a-e. M1.6f is implemented_unverified for full native/game
admission. M1.6 remains in_progress and G1 not_run. Affected:
F03/F04/F07/F08/F11/F16, N01/N04/N05/N06/N08,
C06/C12/C20/C22/C23/C24/C36, T01/T04/T06/T11/T12.
Unrelated M2-M7 work and inference authority remain unchanged.

## Delivered boundary

[ProbeCustody](../../evaluator/src/strata_evaluator/probe_custody.py) verifies
prepared pair/views through their durable verification intent, joins the complete
registered bindings, and holds the actual prepared files using Windows leases.
The files cannot be written, deleted or replaced while those handles remain
open. Whole-tree checks still detect additions, including empty directories.
This protects prepared inputs; it does not qualify gameplay OS isolation.

One-use PREPARING intent precedes lease acquisition. A single transaction then
reserves both complete arms' evaluation envelopes and worker capacity and marks
custody HELD. Any failed budget/capacity/journal step rolls back the entire
reservation transaction, records FAILED and closes file handles. No partial
team is admitted. Envelopes have identical per-member usage/pricing/metering
across arms and fit the finite registered per-probe team limits. All helpers
remain inside their root envelope and consume separately reserved model slots.

This policy reserves both arms concurrently; it does not silently assume that
half the capacity is enough for a sequential execution. The
[campaign scheduler](../../src/mcbench/controller.py) counts private pair holds
in its existing worker pool and prevents incompatible worker recertification
while those holds exist. Native/game execution and measured N=1/2/4 capacity
acceptance are separate requirements, not consequences of these reservations.

Checks join the live owner, wall and monotonic deadlines, held file inventory,
unchanged pair/views/bindings, exact resource record, current certification,
evaluation accounts, original ledger postings, open envelope markers and amounts.
Unknown usage or any discrepancy fences custody without releasing capacity or
costs. A persisted HELD row is not a live file handle. A new owner cannot inherit
it or reacquire the same pair after process death. Explicit live-owner release
is limited to preparation with zero native intents; it closes capacity/file
holds but retains every budget envelope and the consumed pair identity.
Actual launched worlds/runtimes will require a separate stopped custody proof.

Native probe execution remains closed. The new custody object grants no native
permit, broker projection, live-world equivalence, credential boundary or
RuntimeQualification. Production spending still needs applicable M1 authority.

## Executed checks

**86 distinct focused cases pass, with three existing privilege skips.** The
custody suite first passed20, then23 after adding owner-death, authorization and
durable failed-preflight coverage. Final deadline/classified-reason changes
passed six selected cases, including one new monotonic-clock case:24 distinct
custody cases. Controller/budget/file-lease regression passed56 with three
symbolic-link cases skipped because this host lacks the required privilege.
Six affected native binding/account cases also pass. Ruff and whitespace pass.

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe -m pytest tests/test_probe_custody.py -q
.venv/Scripts/python.exe -m pytest tests/test_probe_custody.py -q -k "whole_pair_holds or actual_owner_process_exit or wall_clock_rollback or journal_failure or original_ledger or failed_physical_preflight"
.venv/Scripts/python.exe -m pytest tests/test_storage_controller.py tests/test_budget_envelopes.py tests/test_launch_integrity.py -q
.venv/Scripts/python.exe -m pytest tests/test_native_probe_bindings.py -q -k "whole_pair_binding or reclassified_account"
```

Actual Windows handles deny parent write/delete attempts and a separate Python
writer. A Python owner then acquires custody and exits with code87: its handles
are released by the OS, while the durable HELD row, both envelopes and capacity
remain. Another owner cannot reacquire the pair. Other cases cover all-or-none
budget/capacity/journal failure, scheduler contention, wall-clock rollback,
changed files/accounts/resources/original ledger, unknown costs, missing markers,
unmatched envelopes and forbidden principals. These are synthetic N=1 pair,
game, capacity and native records with real file/process behavior; no Codex,
Minecraft or provider launch occurs. Initial and final sources/logs are retained.

Read-only reconstruction passes73/73 checks across six final cases plus3/3
common checks. It joins exact prepared inputs, bindings, inventories, original
envelopes, unchanged seed costs, physical denial/death evidence, classified
failure/fencing and retained holds. Every database and the producer seal remain
unchanged. No original database/WAL is modified or repaired for this audit.

Producer `2026-09-25-m1-probe-custody-01`:15,904 files,67,945,198 bytes;
seal `b8ff17ced03b78754e05f66753f8637d877ad66cf70f1939002bb27877017fce`.
Audit `2026-09-25-m1-probe-custody-audit-01`:3 files,9,777 bytes;
seal `912ea67deea212980f98e89fbbb70ac42718a32982a43d01678c5a9becfb2185`.
All40 real authority tables are unchanged. Exposure remains $4.887796/$10,
with every hold and consumed decision retained. No owned runtime remains and
no paid M1 execution occurs. D18/D19 remain M0-only.

## Remaining work

Connect this preparation owner to held world/runtime launch and stop custody,
exact bootstrap/catalog admission, scoped root/helper artifact projection and
one-way disposal. Verify actual world/body/keymap/tools/cache equivalence before
either arm starts and enforce the registered controls during local adaptation.
Do not turn HELD or an empty native profile into a launch permit. N>1 positive
pair preparation, actual native loading/projection, complete combined isolation,
T05 and protected scorer controls remain open. G1-G5 remain not_run.
