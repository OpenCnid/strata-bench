# M1.6q.3 composed worker checks and retained failure evidence

Status: **implemented_unverified** for authentic paired-worker integration.
M0/G0 remain closed at their recorded scope; G1-G5 remain not_run.

The paired coordinator validates shared software/parent custody once per composed
check, then all member bindings, account/config/runtime files and process phases.
An identity guard requires the same software holder in both components. Ordinary
standalone member checks still include the full software check. No cross-call
cache, validation bypass or new dispatch authority is introduced. Import receipts
are flushed and fsynced before phase advance; persistence failure prevents server
dispatch. A final duplicate preparation check is composed with the existing
post-initial-state check before any physical server dispatch. Returned uncertain
writer results surface their first retained inner error while preserving the
outer close refusal, fencing and reservations.

Inventory scanning removes a duplicate preliminary ancestor walk for files;
`file_hash` still checks the file and every ancestor immediately before hashing.
Directory, file-type, hardlink, quota, name/collision, review and digest checks
remain. An actual Windows junction replacement between metadata and hashing is
rejected. This change does not establish a new isolation or latency certificate.

Focused synthetic verification uses actual Windows leases and junctions:

```text
pytest tests/test_provisioning.py tests/test_inventory_directories.py tests/test_probe_worker_inputs.py tests/test_probe_worker_runtime.py tests/test_probe_world_copies.py -q
pytest tests/test_probe_worker_runtime.py tests/test_probe_vanilla_runtime.py -q -k 'test_complete_pair or software_scope or test_both_registered_servers'
```

The first selection passes92 and skips one explicitly opt-in native copier case
in536.41s. After the software-holder identity guard, the second passes3 with26
deselected in84.64s:94 distinct passing cases overall. The initial source version
is retained separately. Coverage includes one full software check per composed
check, both import receipts before server intent, receipt-write failure, changed
binding/runtime/software holder and retained inner-error/fencing behavior, plus
existing member/worker/server lifecycle negatives. Ruff and whitespace pass.

A no-dispatch diagnostic on genuine profile02 resolves the server in7.312s under
cProfile, versus the earlier8.422s diagnostic. The resolved digest remains
011e977b1cbb34474e8c32bb870d09820454456e184627cc66423d07610b6456.
It creates no config, worker, game or model. Profiling overhead is included.

Fresh authentic case04 retains the pinned profile02, worker runtime02 and stopped
world from the [identity reference](2026-09-25-m1-worker-identity-native.md).
Parent300s, writers200/170s and servers60/60s are unchanged. Agent/protocol/capacity
fixtures remain synthetic; authentic game/runtime input does not qualify native
probe admission or a scientific comparison. Cases01-03 remain failed.

Case04 fails in224.54s with inner PROBE_INITIAL_OBSERVATION and outer
PROBE_WORLD_CLOSE_UNCERTAIN. It reaches both protected copiers, both worker imports,
the first server's readiness and one genuine connected worker observation. Each
copier has a normal10/10 retained-process stop. Each now-persisted import receipt
records exit0, three total Job Object processes, zero active/terminated processes,
held runtime manifest and held-through-stop custody. Both copies contain374 files,
239,730,374 bytes and162 directories. The second server/worker never starts.

The first observation has ordinary player inventory window0, type
minecraft:inventory, no cursor item or machine. The verifier requires window=None
and rejects it. Other predicates in that initial observation check pass; the
journal has zero actions/primitives and identity before delivery. Separately,
schema validation adds the optional machine:null field that raw delivery omits.
The first offline audit's exact equality assertion fails JOURNAL_JOIN on that
one difference; its script/failure and both records are retained. The corrected
audit checks the difference explicitly and does not claim a successful runtime
join. Saved/live own-state comparison is not reached by this native attempt.

The worker supervisor records a normal41.1524ms drain. Complete worker Job Object
receipt and owner stop result were checked in memory but not persisted before
the subsequent verifier failure; the supervisor receipt is not equivalent proof.
The server requires forced exit125, with all12 held processes signaled, no active
Job Object processes, complete logs and no cleanup errors. Both writer rows are
UNCERTAIN, world FAILED and parent FENCED; every capacity/cost hold remains.
This is failed integration, not normal server stop or verified disposal.

Initial-state holds occur at125.234s/130.828s from parent acquisition; first
launch intent at140.047s and server ready at178.937s. Twelve software checks total
65.562s across this longer path;18 parent checks total15.501s overlap them. These
test-only intervals are diagnostics, not campaign clocks or additive totals.

The failure audit matches435 captured source files and all40 real authority
tables. Exposure remains$4.887796 with the old$0.7554 and four$1 holds and consumed
decisions intact. No owned runtime remains. No model call or M1 spending authority
is inferred from D18/D19.

Next reconcile the ordinary inventory-window predicate and exact journal
representation with the pinned worker contract. Persist normal worker stop and
job custody before later validation can fail. Add focused negative coverage and
only then consider a changed authentic case; keep current failure and windows.
Full live body/tool/policy matching, native admission, clocks/disposal, T05/T10
and remaining isolation/native-loop evidence stay open.

Coverage inherits M1.6q F01/F02/F04/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial T01/T06/T11,
plus F05/partial T02 inventory integrity. Unrelated M2-M7 are unchanged.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-worker-pair-native-04` | 696 / 48,958,109 | `888e625609285786e7120197f64ea2378e22d191f00302837aed6aaec6616360` |
| `2026-09-25-m1-worker-composed-cost-01` | 8 / 69,342 | `71d1b59ac5243697dac667a414cedccb8f025ae1e38b1713b75493a8b29626fb` |
| `2026-09-25-m1-worker-check-composition-01` | 9,968 / 42,915,288 | `484d1d594059edb7b04dc9505be85c0cd9aa92aa369633e26cbe39522c818a5b` |

All three bundles independently verify with extended Windows paths. The source
store includes94 distinct passing cases, fixtures/logs/XML,435 source pins and
final authority/process checks. All414 prior milestone IDs remain (415 current),
1,629 local links resolve, progress remains append-only and prior SPEC/JSON are
preserved. These seal pointers follow the archived documentation snapshot.
