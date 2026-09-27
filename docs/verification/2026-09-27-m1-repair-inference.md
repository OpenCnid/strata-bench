# Repair inference attribution and closure — September 27

M1.1c.3.4 remains `in_progress`; M1/G1 and all six aggregate G1 suites remain
incomplete. The previous turn was progress, committed at `87f31f1` with retained
avatar tick evidence. This turn connects model/helper dispatch accounting to the
repair's eventual completion check without charging those calls a second time.

[RepairInference](../../src/mcbench/repair_inference.py) opens a durable window in
the existing repair-request transaction. It includes the avatar's in-flight calls
and records subsequent model/helper/retry calls in the original dispatch-intent
transaction. A private freeze uses that same database writer lock to close new
inference admission for the repairing avatar. Existing calls may still settle
from authoritative receipts; unknown usage and its original reservation remain.
There is no unfreeze/rearm method, new allowance or gameplay permission.

The audit checks owned repair scope, original opening/closing journal events,
membership against actual dispatch/settlement history, original operation lineage
and settled/uncertain state. Pre-repair calls already settled are excluded; calls
already in flight are included. Calls retain their original parents and costs.
The audit does not copy model usage into the repair tool's primitive/body charges.
`tracked_dispatches_settled` requires closed admission and every member settled;
complete repair accounting and campaign input permission remain explicitly false.

The existing [dispatch service](../../src/mcbench/inference_dispatch.py) preserves
old `InferencePreDispatchRejection/1` records. Frozen/untracked repair denials use
explicit `/2` records with their own policy. Denial commits before returning,
creates no reservation or dispatch, cannot replay, and remains readable by native
closure/export checks. Old active repairs without a window are refused rather
than retrospectively promoted to zero-call accounting.

Executed on Windows/Python 3.12.14:

- Fourteen source/controller/SQLite cases pass in
  [test_repair_inference.py](../../tests/test_repair_inference.py): root/helper/
  retry overlap, original parent and cost retention, authoritative late settlement,
  unknown holds, avatar scope, missing legacy windows, missing/changed membership
  and journal records, storage failures and concurrent dispatch/freeze ordering.
- One selected real local HTTP gateway test passes. Its controller window, native
  identity and upstream provider are synthetic. A frozen request reaches no
  upstream call, records the typed denial and permits truthful zero-dispatch
  native-envelope closure; no unknown usage is cleared.
- Sixty-three affected existing dispatch, reconfiguration and native rejection-
  export cases pass. Legacy denial semantics and consumed requests remain intact.
- Ruff passes for all changed Python files. Initial test-only multiple-statement
  style errors were corrected; all executed behavioral cases passed.

No actual model, Minecraft, shared-desktop input or native binary installation
ran. The real HTTP test is transport/accounting evidence, not Dovetail/helper
process isolation or selected-model qualification. D18/D19 remain M0-only.

Coverage: M1.1c.3.4; F03/F06/F07/F09/F11/F16, N01/N02/N04/N08; required
T01/T04/T05/T06 accounting dependency for G1. The private window, memberships and
receipts stay outside gameplay/helper contexts. The endpoint/tool catalog is
unchanged. Current installed files, original holds and authority were audited
unchanged; the final seal pointer follows below.

Next: the controller completion flow must invoke this freeze/audit and join it
to complete primitive/body interval allocation and publication evidence before
settling and restoring the original lease. Authentic play/repair/restart/restore/
resume, native-health failure and remaining contract/isolation/scorer/probe gates
are still open. This component alone cannot close T04 or G1.

Private evidence sealed:171 files/11,019,900 bytes,
SHA-256 `b31830bbdae0f03c501746924bc171b77039218cfb3841f309cb38dcefb7c511`.
All40 authority tables, eight telemetry holds and installed client/options hashes
are unchanged; final matching runtime process count0. All460 milestone IDs and
2,173 local links were checked. This pointer postdates the archived snapshot.
