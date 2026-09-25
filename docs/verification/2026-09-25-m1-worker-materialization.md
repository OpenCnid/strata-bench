# M1.6q.6 borrowed worker materialization

Status: **implemented_unverified** for authentic paired integration. G1-G5 remain not_run.

Private worker preparation now borrows the complete installation lease already
owned by the paired software holder. Each resolution still reads fresh sealed
provisioning/CAS authority and scans the complete role layouts, including empty
directories, types, sizes, hardlinks and membership. Only hashes verified through
still-held file handles replace path hashing. Node is outside that installation:
its executable hash and the complete worker runtime retain their own validation.

Each member retains separate runtime and configuration leases. The complete
roster's account declarations still validate before any configuration commit.
Closing a member releases only its own resources. Closed, foreign or untyped
borrowed custody refuses; simulation, restored, Forge and own-server borrowing
are unsupported. Configuration, import/worker dispatch and stop receipts recheck
borrowed custody. Public resolution and ordinary standalone launch are unchanged.
The private server wrapper also refuses an absent lease instead of silently
falling through to ordinary resolution.

```text
pytest tests/test_worker_materialization.py tests/test_held_materialization.py tests/test_pack_worker.py -q
pytest tests/test_probe_worker_inputs.py tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save -q
```

The selections pass 88 cases in 38.79s and 9 cases in 161.938s, respectively:
97 distinct passing cases, no failures or skips. These are synthetic profiles and
controlled processes with actual Windows file custody. They cover unchanged
resolution output, no repeated installation hashing, external client hashing,
separate member leases and parent ownership, changed authority/layout/runtime,
closed/foreign/untyped custody, late custody loss before configuration/dispatch/
receipts, whole-roster account mismatch, partial configuration failure, closed
parent and retained reservations. The paired lifecycle positive still imports
both workers before servers and drains workers before each server save. Ruff and
whitespace checks pass.

A read-only diagnostic uses genuine profile02, PackLock
`cas:sha256:5c9923e81c3fa28575275911d218e8352738727e5cdb868e5b47e9ab9337cd2c`,
and the 11,725-file runtime02 manifest
`7ca5ff3d4df7f3e86485aab112db12ed6abf196b488ddef91da2f12348afa511`.
Ordinary deferred entry takes 13.672s and borrowed entry 11.078s; both produce
resolution digest `9c6e62bda58600dcba99320e305a9586082b68e44f360cdbccbee8cad784816c`.
Server and Node write-opens are denied in both cases. Child runtimes close while
the parent installation remains held, then the parent closes. No configuration,
game process, provider or model starts. These are diagnostic timings, not a
latency/capacity certificate or authentic paired acceptance.

Case06's recorded worker preparation ends at 38.656s and 51.734s after parent
acquisition; the experienced writer starts at approximately 82.557s, derived
from its retained wall timestamp and parent expiry. Its 170s window therefore
starts after the work changed here. Improving that earlier work helps parent
preparation but cannot by itself resolve the later WRITER_EXPOSURE_INSUFFICIENT
failure. No native retry was made. The next change should reduce validation
delaying normal stop within the writer window, while still requiring complete
validation before accepting the stopped export or starting the sibling.

The [case06 evidence](2026-09-25-m1-held-materialization-checks.md), all earlier
failures, original parent300s/writers200-170s/servers60-60s bounds, separate profile
identities, consumed decisions and budget holds remain unchanged. Both case06
writers remain UNCERTAIN, its world FAILED and parent FENCED. No complete-checkpoint,
clean-save, native admission, isolation or scientific-probe pass is inferred.

All 40 real accounting tables remain unchanged at $4.887796, including the old
$0.7554 and four $1 holds. No owned runtime remains and D18/D19 remain M0-only.
Coverage inherits M1.6q.5: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial T01/T02/T06/T11.
Full live-state/tool parity, native admission, authoritative clocks/disposal,
T05/T10 and remaining isolation/native-loop requirements stay open. M0/G0 and
unrelated M2-M7 are unchanged.

Private evidence `2026-09-25-m1-worker-materialization-01` independently verifies
10,776 files / 23,160,725 bytes with SHA-256
`22c284a5fd2b4b574d619b1bed0c17919683fc1822638fd5c933d0463ec48eb9`.
It retains both complete test trees, the genuine read-only diagnostic, writer-clock
analysis, 437 source files, documentation and accounting/process checks. All 417
prior milestone IDs remain (418 current); 1,644 local links resolve, progress is
append-only and prior SPEC text/JSON are preserved. This seal pointer follows the
archived documentation snapshot.
