# M1.6q registered worker lifecycle and retained pre-dispatch failure

Status: **implemented_unverified**. Thirty-one distinct focused source cases
pass. The first authentic-input paired-worker attempt **fails** before any
copier, worker import, worker or server dispatch: `PROBE_WORLD_DEADLINE`.
No authentic paired-worker readiness, initial-state match or G1 pass is claimed.

`held-pair-protected-vanilla-worker-reference/1` connects complete registered
worker input custody to the existing saved-body paired server reference. It keeps
both rosters' account declarations, configurations and runtimes held. Validate
fresh disjoint output namespaces, reserve worker runtime bytes and328MiB/member
for four existing64MiB logs, bounded64MiB state and configuration/receipts. Check
state inventory limits at lifecycle boundaries; this is not a general hard disk
quota for arbitrary untrusted processes. Parent resource/cost envelopes remain
held throughout. Import every worker before either finite server window starts.

For each registered arm, start its complete requested roster, validate each
grant's destination scope, and request only bounded ordinary observations. Every
worker must remain alive at the observation barrier. The flag is deliberately
`complete_roster_observed_connected`: these observations do not prove simultaneous
current connectivity or full all-N readiness. Drain workers with the existing
scoped one-use normal stop before server stop/save. Keep the first arm's stopped
worker state and evidence immutable through the sibling. Failures terminate all
remaining owned workers before outer writer cleanup, retain cleanup errors and
fence the pair without releasing reservations. The new entry point exposes no
model, action, continuation or native probe dispatch capability.

The private `registered-worker-initial-own-projection/1` join requires normal
owned preflight/worker receipts, the expected saved UUID, a single epoch and
spawn identity, zero accepted actions/primitives, and the exact delivered
observation after its private identity event. Use WAL-aware read-only SQLite and
close reader handles. Compare dimension, pose, health, food and occupied
inventory item/count projection to the registered saved body. Reject changed,
foreign, ambiguous, example-labeled or active/mutated evidence. Item tags,
selected slot, game mode, abilities, effects and other unprojected live fields
remain outside this projection. `live_initial_state_verified`, native admission,
authoritative clocks and disposal stay false/unqualified.

The reference's agent/protocol/capacity fixtures are explicitly synthetic even
when game inputs and workers are authentic. Real worker observations keep their
own non-example identity. A matching label alone never authenticates a producer.
This distinction was corrected before the authentic attempt; the earlier source
version and its passing logs are retained.

Source verification uses actual private pair construction, configuration/account/
runtime/source file custody, strict SQLite reading and stopped-export handling,
with substituted process, JVM and transport results. Run with
`PYTHONPATH=src;tools;evaluator/src` and fresh private basetemp/XML:

```text
pytest tests/test_probe_worker_observation.py tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save -q
pytest tests/test_probe_worker_runtime.py -q
pytest tests/test_probe_worker_inputs.py tests/test_probe_vanilla_runtime.py::test_both_registered_servers_stop_export_and_keep_sibling_capture_immutable -q
pytest tests/test_probe_worker_observation.py tests/test_probe_worker_runtime.py tests/test_probe_worker_runtime_native.py -k 'not test_worker_failure or example' -q
```

Selections pass14/38.45s,7/207.66s,9/167.35s, and16/66.18s. The last includes
one explicit opt-in native skip and six deselections; overlapping cases are not
double counted.31 distinct cases pass. Failures covered include late import,
foreign grant, changed own state, early worker exit, missing stop receipt,
authority loss between arms, example observations, absent/duplicate/out-of-order
identity, changed journal delivery, old epochs and action/primitive activity.
The positive verifies imports precede both servers, workers stop before save,
the first worker export denies writes through the sibling, and holds remain.
These tests are not authentic game or OS process-isolation qualification.

The new opt-in native test binds a fresh request to the already sealed corrected
worker/profile02 and genuine identity-case02 stopped world. It generates fresh
registered body declarations before committing pair fixtures. No old source or
missing native configuration reference is backfilled. Reuse the verified Java
helper only after matching its full source hashes. Host memory/disk/port and
process checks pass; the real controller is read WAL-aware and read-only.

Executed `pytest tests/test_probe_worker_runtime_native.py -q` with the pinned
`STRATA_PROBE_WORKER_REFERENCE` input and hash. The attempt fails in178.93s at
the existing world deadline preflight. Complete worker configuration preparation
left insufficient parent time for the first writer's200s window. Parent300s,
writer200/170s and both server60s limits remain unchanged. Both identity-bound
configurations exist; worker directories and native evidence parent remain
empty, and no world-copy row was inserted. Teardown fences the parent and leaves
capacity/cost holds reserved. A read-only failure audit verifies these facts and
435 source-file matches; it does not turn the failed attempt into a pass.

A separate read-only diagnostic resolves the same sealed server and client once
each, without writing a worker configuration or starting anything. Under cProfile,
server resolution takes8.188s and client33.687s. Client resolution includes25.250s
in worker invocation resolution,17.151s entering runtime custody and7.703s in
runtime manifest construction.35,207 individual `safe` calls and648,551 Windows
stat calls show repeated path validation; server layout scanning also contributes.
Profiler overhead is included: these are diagnostic measurements, not admission
latency certification. The first diagnostic script shadowed Python's `profile`
module and failed during import; its source/error remain retained. Rename the
script and use a fresh worker-state directory for the corrected read-only measurement.

Next reduce repeated validation while preserving every source hash, link check,
live file lease, authoritative binding and rejection path. Then repeat this
specific authentic case after that relevant implementation change. Do not enlarge
the finite windows or seek an unchanged successful rerun. Full live body/tool/
policy matching, native admission, authoritative clocks, one-way disposal, T05,
protected T10 controls and remaining isolation/native-loop evidence remain open.

Coverage: F01/F02/F04/F07/F08/F09/F16, N01/N02/N03/N04/N05/N06/N08,
C06/C20/C23/C24/C36; partial T01/T06/T11. G1-G5 stay not_run. M0/G0, previous
profile identities/failures and unrelated M2-M7 are unchanged. All40 real authority
tables remain unchanged at$4.887796 exposure, with the old$0.7554 and four$1
holds and consumed decisions preserved. No M1 paid inference authority is inferred.

Private evidence stores are sealed and independently verified:

| Store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-probe-worker-runtime-01` | 6,798 / 26,179,360 | `5c325b62eb4d75c9fd5bc60357e6f8f94e9e84df2b381e7d6720a3c07033be1a` |
| `2026-09-25-m1-worker-pair-native-01` | 657 / 44,663,039 | `0eba0d649438eecee9d647e5cea48524226d7cca3d914b4df7e91a8eeab6fdfc` |
| `2026-09-25-m1-worker-resolution-cost-01` | 14 / 227,016 | `ce76fc191572e81a690867353f7840173d4b7715ea3d420d8959931cb86df7d1` |

The source store retains all selections/XML, source versions,435 source files,
final accounting/process checks, docs and audits.434 code/tool/lock files match
the attempted native run; subsequent SPEC additions preserve all fixture JSON.
Documentation QA preserves411 prior milestone IDs, adds M1.6q, retains append-only
progress and prior SPEC text, and resolves1,613 local links. Focused Ruff and
whitespace checks pass. These final seal pointers follow the archived docs snapshot.
Sealing/auditing the native failure does not certify a successful native run.
