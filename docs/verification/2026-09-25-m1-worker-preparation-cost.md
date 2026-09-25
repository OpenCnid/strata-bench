# M1.6q.1 worker preparation cost and preserved custody

Status: **implemented_unverified** for authentic paired-worker integration.
Both authentic attempts fail with PROBE_WORLD_DEADLINE. The original M1.6q
failure remains retained; its
300s parent, 200/170s writer and 60/60s server windows remain unchanged.

Batch preliminary ancestor discovery within one FileLease construction and the
worker manifest preflight. Keep final per-file link checks after parent handles
are held, retained-handle hashing, hardlink/size/path limits, exact tree membership
and exception cleanup. No filesystem cache survives a call. A new Windows
junction-swap test substitutes an identical-byte tree after preliminary checking;
the final path check refuses it and releases all acquired handles. Separate tests
reject changed bytes or membership between manifest construction and lease entry.

HeldPackWorker now supports deferred configuration creation. Resolve each member
once and retain its runtime while checking both complete arm rosters. Hold and
recheck all account declarations before committing any configuration. Commit is
one-use, rechecks runtime and fresh configuration/state paths, verifies the exact
configuration hash and holds its bytes. Failed commit closes its own custody and
retains partial evidence. Import, worker and server dispatch all refuse before
commit. Final parent, software, binding, account and runtime/configuration checks
remain. Ordinary callers retain immediate configuration creation; no wire/profile,
accounting allowance, game affordance or native probe admission changes.

Focused verification uses synthetic packs/processes with actual Windows file
leases. With PYTHONPATH=src;tools;evaluator/src:

```text
pytest tests/test_launch_integrity.py tests/test_worker_bundle.py tests/test_pack_worker.py -q
pytest tests/test_pack_worker.py tests/test_probe_worker_inputs.py -q
pytest tests/test_probe_worker_runtime.py -q -k 'test_complete_pair or import'
```

The selections pass92/26.74s,57/210.82s and2/60.91s:108 distinct passing cases.
Three symbolic-link cases skip because the required Windows privilege is absent;
the actual junction cases pass. Six unchanged lifecycle failures are deselected
in the last selection. Existing write/delete/replace/parent-rename denials,
8,300 native handles beyond the CRT limit, late hash failures and long paths pass.
New deferred cases cover dispatch refusal, exact config custody, duplicate commit,
occupied/missing state, occupied configuration, changed hash/runtime and cleanup.
Late-arm account mismatch still creates no configuration. Partial commit preserves
the first file and releases own leases. Success/import-failure lifecycle cases
retain stop ordering, first-arm export custody and parent holds.

Read-only cProfile of the same authentic sealed profile after path batching,
before deferred configuration, measures server8.422s and client23.937s, versus
8.188s/33.687s before. Client safe calls fall from35,207 to11,756 and Windows stat
calls from648,551 to342,122. The resolved server digest is unchanged. These are
instrumented diagnostic costs, not admission latency certification. No config,
worker, game or model is created by the diagnostic.

The changed authentic case uses fresh roots and bindings to the same corrected
worker/profile02 and genuine identity-case02 stopped world. Agent/protocol/capacity
fixtures remain synthetic; no model calls or full native/scientific probe claim.
Case02 fails in118.32s at stage(0), immediately before first copier dispatch.
It passes the earlier world preparation preflight that refused case01, records
one world-copy intent row, then marks that row FAILED. The row has no arm results;
native/worker evidence directories remain empty. Both identity-bound configs
exist, with no copier, import, worker, server or model dispatch. Teardown fences
the parent and retains resource/cost reservations. Do not reinterpret the later
refusal or faster preparation as successful paired integration.

A read-only failure audit checks these facts, the435 captured source files,
absence of owned runtime and all40 unchanged real authority tables. Exposure
remains$4.887796, including the old$0.7554 and four$1 holds. Consumed decisions
remain consumed; D18/D19 still supply no M1 inference authority.

The changed case and diagnostic are sealed and independently verified:

| Store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-worker-pair-native-02` | 659 / 46,052,552 | `9e805a13a0e8a19353587db20798579b36e430206df451857336cc2485a3d420` |
| `2026-09-25-m1-worker-resolution-cost-02` | 10 / 199,132 | `37722bbbbd216c49a6713ccfb622bd42a74966ef8f21c80e1aa608d80d227519` |
| `2026-09-25-m1-worker-path-batching-02` | 12,994 / 14,694,126 | `c344f835d76de3ba02c36a88cf7517955705ae92256691cdbab3a11609e8253d` |
| `2026-09-25-m1-worker-deferred-config-01` | 6,299 / 16,036,255 | `326cbb0e6ca7c82ce971b3ebee189a967eb03fec33e78245e4d6334cbb0339ae` |

The first path-batching archive seal fails EVIDENCE_INVENTORY: ordinary Windows
path enumeration omitted one deliberately long-path fixture. The extended-path
verifier detects the missing entry. Preserve that original store and failed seal;
copy and byte-compare all12,992 files with extended paths into store02, retaining
the failed manifest/inventory as nested evidence. Seal and independently verify
the complete copy. No test/source file is changed or excluded to obtain the pass.
Deferred fixtures, source versions, logs/XML and native failure remain separate
bounded archives. Final source audit matches435 native-input source files; docs
QA preserves412 previous IDs, adds M1.6q.1, retains append-only progress and prior
SPEC/JSON fixtures, and resolves1,618 local links. Ruff and whitespace checks pass.
These final seal pointers follow the archived documentation snapshot.

Next inspect the remaining preparation checks, including repeated full software
resolution and validation between the first preflight and copier dispatch. The
read-only profile still spends7.379s scanning both installed layouts under
cProfile. Preserve every authoritative read, source/link/hash/handle/membership
check and finite window; measure a relevant correction before another authentic
attempt. No unchanged rerun is warranted by this failure.

Coverage inherits M1.6q: F01/F02/F04/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36, partial T01/T06/T11.
Full live body/tool/policy parity, native admission, clocks/disposal, T05/T10 and
remaining isolation/native-loop evidence remain open. G1-G5 remain not_run;
M0/G0, earlier failures/profile identities and unrelated M2-M7 are unchanged.
