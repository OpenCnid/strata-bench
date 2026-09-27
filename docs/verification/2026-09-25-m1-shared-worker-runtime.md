# M1.6q.15 pair-owned immutable worker runtime

**Successor verification:** [native11](2026-09-25-m1-worker-pair-native.md)
passes the named actual vanilla N=1-per-arm paired reference under original
bounds. This child is now verified for that scope; full G1 remains open.
Earlier status/results below are preserved history; sealed archives unchanged.

Status: implemented_unverified for authentic paired gameplay integration.
105 source cases and one authentic preparation-only case pass; G1-G5 not_run.

The registered pair now enters a private HeldWorkerRuntimePool before its member
contexts. The pool owns immutable runtime leases keyed by exact normalized
manifest path and expected SHA-256. The first member performs complete manifest
validation and retained-handle hashing. A later member with the same reference
checks live custody and current tree membership before borrowing the held
runtime. A different reference must undergo its own complete acquisition and
cannot inherit the old reference's verification.

Member configurations, account bindings, state directories, processes and stop
receipts remain separate. Fresh provisioning authority, materialization, launch
command, account and dispatch checks remain in their existing paths. The pair's
ExitStack closes member contexts/processes before releasing the pool; failures
follow the same order. Standalone workers continue to own their runtime directly.
There is no global/persistent cache, gameplay-facing pool API or new permission.
Original parent/writer/server deadlines and resource/cost reservations remain.

This change targets the repeated runtime acquisition measured by
[Q14](2026-09-25-m1-worker-entry-phases.md). It does not explain native10's
148.437-second first-entry delay or promote any historical failed attempt.

Focused verification command:

```text
pytest tests/test_worker_runtime_pool.py tests/test_worker_bundle.py tests/test_probe_worker_inputs.py tests/test_pack_worker.py tests/test_probe_worker_runtime.py -q
```

The tests use synthetic software/accounts/processes and actual Windows file
leases. New cases cover borrowed custody surviving member exit, pool closure and
one-use lifetime, changed reference, added member, closed lease, altered reference
metadata, invalid owner and independence of separate pools. The paired positive
also asserts member cleanup callbacks run while runtime custody is still held.
Existing input and runtime suites retain account/authority/failure/deadline and
owned-stop checks. Authentic preparation follows terminal source checks and a fresh
authority/source audit; no fresh game trial is selected yet.

Coverage inherits M1.6q.14: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Full live matched-state/tool policy, native probe admission,
authoritative clocks/disposal, T05/T10 and root/helper isolation remain open.
M0/G0 and unrelated M2-M7 remain unchanged. D18/D19 remain M0-only; no paid
inference authority is inferred.

Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-shared-worker-runtime-01`.

Source session3141 finishes with104 passes and one failure in660.87s. The
ownership tracking test still patches the constructor in pack_worker after the
acquisition helper moves to worker_bundle. Preserve that failure and tested
source. Updating only the test import makes its focused rerun pass0.71s, with
production code unchanged.105 distinct source cases pass, no skips; two existing
Typer warnings remain. No unchanged broad suite is repeated.

The unchanged preparation-only test from Q14 then runs once against this changed
implementation in fresh private storage. Session8976 passes66.16s. It uses
actual pinned profile02 software/save/account declarations with synthetic
agent/protocol/capacity/budget records and blocked process dispatch.

| Measured phase | Q14 baseline seconds | Q15 seconds |
|---|---|---|
| First worker entry | 14.499 | 15.578 |
| Second worker entry | 14.629 | 4.787 |
| Whole preparation through cleanup | 59.711 | 51.673 |

There is exactly one complete bundle acquisition in Q15 (8.651 seconds); the
second member borrows its still-held exact runtime. These individual cProfile
samples are diagnostic evidence, not a performance envelope or an explanation
of native10's148.437-second delay. Every member still performs fresh authority,
materialization, launch/settings and account/configuration checks. All handles
close, configurations remain separate, worker states stay empty, the parent is
FENCED, resources and synthetic budgets remain reserved, and no world/writer
tables or game/model processes are created.

Selection records443 source pins and all40 real authority tables unchanged at
$4.887796. No M1 paid allowance is created. Next perform final source/custody and
host-capacity checks before selecting one fresh changed paired-worker integration
attempt under the original300/200-170/60-60s bounds. All historical native01-10
failures and consumed inputs remain. Full G1 is still incomplete.

Final audit passes443 current source pins,427 unique milestone IDs with all426
prior IDs retained,1,689 local links, append-only history, prior SPEC text/JSON
preservation, Ruff and whitespace checks. All40 real authority tables remain
unchanged at$4.887796; no owned runtime remains. No native11 is selected yet.

Q15 evidence is sealed and independently verified:14,391 files,78,805,077 bytes,
SHA-256`b1a146fb9ef69eacd32f7cffeccd1ce24130e16ff559e6f6dd4b380f97cb18b0`.
Source failures/correction, both source runs, authentic preparation, complete
private fixtures and final audits are retained. This seal pointer follows the
archived documentation snapshot. Sealing57176 is terminal/pass; use fresh
storage for the next attempt and never alter this root or native01-10.
