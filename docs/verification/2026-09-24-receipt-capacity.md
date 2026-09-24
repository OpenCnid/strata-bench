# Reserved receipt storage and settled delivery

M0.1d.9d.1 fixes the concrete receipt-storage failure retained in D19.6.
The changed source passes 391 focused tests and a fresh pinned native preflight
26/26. The authentic case confirms the storage fix but fails at separate response
and report-object limits before walking or helper creation.
M0 stays in_progress and G0 fail.

Coverage: F04/F11/F16, N01/N02/N08, C09/C18/C20, partial T04/T07/T12/T13,
G0 items1/6, with D14 isolation deferral and M1–M7 unchanged.

## Implementation and bounds

[storage_capacity.py](../../src/mcbench/storage_capacity.py) declares
`operator-receipt-capacity/1`: a finite **128 MiB** private operator audit
allowance. The former 20 MiB default is retained for gameplay/other ordinary
namespaces; explicit pack storage bounds remain separate. Explicit larger
operator write arguments cannot bypass the new operator ceiling. This is a
recorded operator storage allocation, not an inference allowance or evidence
retention change. No old bytes or unresolved charge holds are removed.

[native_pilot_trial.py](../../tools/native_pilot_trial.py) checks 48 MiB of
logical headroom and a 64 MiB free-disk margin before Java, worker or model
startup. This read-only check is not a whole-run reservation. Each new model
request separately reserves its maximum 256 KiB receipt in an immediate writer
transaction before inference dispatch. Ordinary CAS puts and file imports count
outstanding reservations; overlapping root/helper calls get separate slots.

Persistence consumes the slot in the same transaction as the immutable object
reference. A failed write rolls back consumption. Reservation records survive
restart; no timeout silently releases unknown work. A slot allocated for an
attempt rejected before forwarding is released. Crashes/uncertain forward paths
retain their slot for explicit recovery. Logical slots protect cooperating CAS
writers; external disk exhaustion still causes a failed write. Full disk/recovery
qualification under N08 is not claimed by these tests.

[inference_transport.py](../../src/mcbench/inference_transport.py) adds
`durable-settled-receipt-before-delivery/1`. Both supported wire media and the
native normalized stream are bounded and withheld until the receipt is stored
and its actual usage settles. Malformed or partial evidence remains private and
unsettled. A downstream delivery failure preserves the known settled cost,
records a bounded diagnostic, and cannot replay the provider request or
redeliver its output on an idempotent status check. This closes the D19.6
ordering gap in which native delivery preceded failed receipt persistence.

## Executed checks

```text
python -m pytest tests/test_receipt_capacity.py tests/test_inference_transport.py
  tests/test_native_oauth.py tests/test_helper_pilot_budget.py
  tests/test_luna6_pilot_budget.py tests/test_pilot_budget.py
  tests/test_native_piloting.py tests/test_native_helper_piloting.py
  tests/test_native_tool_projection.py tests/test_native_admission.py
  tests/test_native_game.py tests/test_storage_controller.py tests/test_provisioning.py -q
391 passed in 85.95s
```

Eight receipt-capacity cases cover separate agent/operator limits, simultaneous
writers/restart, file-import contention, fsync failure rollback, disk margin and
helper denial, rejection before provider contact or monetary reservation,
near-full durable/settled delivery, and known-cost delivery failure/no replay.
The final explicit-override assertion was rerun: 8/8 in1.90s. Earlier selections
passed49 and91; these overlapping counts are not added. Ruff passes. One
initial test formatting failure was corrected before qualification.

Private `2026-09-24-helper-native-05` uses the pinned native CLI/Dovetail with
synthetic model/worker replies: **26/26**, six settled requests, six consumed
receipt reservations, two closed participants and normal FINALIZED/exit0 after
20.123300 seconds. Root/helper requests deliberately overlap. The live preflight
consumer accepts the changed source. Zero paid requests/game processes; all
39 original authority tables are unchanged. Full archive readback passes:
3,764 files, seal
`ff9d517b5fad5590a5a94831a977902e997a73ab917194455d3d96d94e3f7fb3`.

A current recheck of native04 found an additional 32,768-byte SQLite SHM and
empty WAL, created by later read-only access to its WAL-mode database. Every
original sealed file still matches; its current full-directory check fails
EVIDENCE_INVENTORY. Both sidecars and this finding are retained in native05;
original native04 is untouched. Native05 is checkpointed into DELETE journal
mode before sealing to avoid subsequent read-only sidecars. This does not
reinterpret the old full-directory failure as a pass.

## Authentic changed case

Fresh D19.7 / m0-pilot-14 was prepared and executed once under existing D18/D19.
Preparation preserved all 39 authority tables and passed the new headroom check:
20,938,057 used bytes, zero reserved receipt bytes, 50,331,648 required bytes,
134,217,728 operator quota. Preparation seal:
`9e4a03f3084a9fe1fd83d31906577cb526be7b2552b9c84137faa913caed2f9a`.

The live case **fails**, while confirming that the previous shared-quota failure
is fixed. Seven requests settle for **$0.006619** and the model completes a
**45-degree turn** with unchanged health20 and a fresh matching observation.
No walk or helper is completed. Request eight exceeds the separate 256 KiB
wire-response limit after41,921ms of its60,000ms allowance. Its **261,906-byte**
prefix is now durably retained, with no fabricated usage or replay. It contains
778 tool-input delta events and only3,059 total delta characters; wire framing
can therefore exhaust this limit for ordinary native tool code. The next request
is rejected with METERING_UNKNOWN before forwarding. Eight receipt slots are
CONSUMED and the rejected request's unused slot is RELEASED; no pending storage
reservation remains. The failed model request's monetary hold remains.

A secondary retained failure occurs while publishing the native result: the
reconstructed **322,961-byte** report exceeds the unchanged **262,144-byte**
per-object default. The live result/journal publication does not complete.
The outer result records ARTIFACT_QUOTA, forced_worker_cleanup=true,
WORKER_LAUNCH_STOP_UNPROVEN and WORKER_RUNTIME_STOP_UNCERTAIN; worker exit125
is not a normal-stop pass. The server stops normally. All53 outer-owned
processes are terminal (zero Job-terminated processes), but that does not repair
the failed worker-stop qualification. Owner elapsed286.703s; inner246.375s.

The stopped read-only audit invokes the actual report reader with a capture-only
CAS, reconstructing its bytes without publishing or modifying the original
accounting. An initial audit assumed primary-key enumeration was request order
and failed; its source/error remain alongside the corrected explicit UNSETTLED
lookup. The reconstructed report is labeled post-run evidence, not a live result.
The archive seeds receipt closure from actual job operation IDs, preserving all
seven complete wires and the incomplete eighth response.

D19.7 is consumed. Its full **$1 envelope stays reserved**, including settled
charges without double counting; total exposure is **$4.831942/$10**. All
predecessor accounting rows, D12, original allowance and older holds persist.
The only added table is the receipt-capacity reservation ledger. There is no
new allowance, refund, rearming or permission request.

Private archive `2026-09-24-m0-helper-live-14`: **3,983files /197,671,879bytes**,
seal **`bf91e5498f73ac493a1f1ad54619d0ff380ad45a670f4584871d27c5d643b6bb`**,
complete EvidenceBundle readback passes. It includes source pins, the full stopped
controller snapshot, reconstructed report, failed outer result and46 scoped CAS
objects. Eighty-nine external refs are listed explicitly; this is not a complete
game distribution. The stopped native credential copy is removed.

M0.1d.9d.1 is verified for this bounded storage/settled-delivery contract, with
source/native overlap and authentic root/prefix evidence. It does not close the
parent helper case or full N08. Next M0.1d.9d.2 must align native wire/report
limits with real tool output, retain oversize failures, and ensure result-write
failure cannot bypass worker shutdown/final evidence. Qualify those changed
paths before any new paid dispatch. Existing successful installation and
zero-helper gameplay cases need no replay. Remaining G0 items1/4/5/6 stay open.
