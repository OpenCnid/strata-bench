# M1.6q.9 held-parent path validation

Status: implemented_unverified for authentic paired integration. G1-G5 not_run.

Read-only profile02/runtime02 worker entry, with the exact materialization lease,
completed in30.250s under cProfile. FileLease acquisition accounted for18.492s;
11,762 safe calls8.339s and263,150 stat calls expose repeated ancestor validation.
Intervals overlap and profiling overhead prevents direct comparison with native
deadline timings. No configuration writes, game/model dispatch or runtime left
held. The initial diagnostic script shadowed stdlib profile; its failed output
is retained separately from the corrected successful diagnostic.

Implement a post-acquisition check of every held parent, then fresh per-file
link checks and hashing through each retained native handle. Keep final membership
checks and no cross-call filesystem cache. Native entries are opened without
following reparse points; directory access participates in sharing checks.

The initial source suite retained two failures (104 passes/3 skips): zero-access
directory handles did not deny removal before any child opened. FILE_LIST_DIRECTORY
fixes that custody gap. All five targeted cases pass, followed by106 passes/3
symlink-privilege skips in44.00s across launch integrity, worker bundles and pack
workers. Ruff passes after correcting two test formatting findings.

Changed-profile read-only entry takes25.063s under the same profiler, with the
identical resolved launch digest. FileLease falls18.492s to12.465s, stat calls
263,150 to121,679. Both runtime/server write-opens are denied; no configuration
writes or dispatch occurred, and owned custody closed. This diagnostic is not
an authentic pair timing pass. All four paired lifecycle source checks pass in
177.73s. Fresh native09 passed110 source cases/three declared skips,438 unchanged source
pins, unused inputs and fresh host/accounting checks. Original300/200-170/60-60s
bounds remain. Its actual failed result is retained below.

```text
pytest tests/test_launch_integrity.py tests/test_worker_bundle.py tests/test_pack_worker.py -q
pytest tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save tests/test_probe_worker_runtime.py::test_post_stop_validation_failure_refuses_export_and_sibling -q
```

Native09 uses genuine profile02/runtime02/source-world inputs and synthetic
agent/protocol/capacity fixtures, with zero model calls and no gameplay actions.
Input pin `962387de9ced95a65307d1a2778fd8fc56ac8fd0bca0d8982d82f8397aea12cb`.
It fails202.19s total (JUnit case200.869s): inner PROBE_WORLD_DEADLINE is retained
alongside outer PROBE_WORLD_CLOSE_UNCERTAIN. Both protected copiers exit0 with
10/10 held processes signaled, complete logs and no force. Both worker imports
have persisted exit0/three-process receipts, zero active/terminated children.

The first start performs full preflight, ending179.110s after parent acquisition,
then refuses the aggregate120s server exposure against all remaining reservations.
No server or gameplay worker dispatches; no observation or stopped world export
is claimed. Both writers remain UNCERTAIN, world FAILED and parent FENCED with
all reservations held. The native audit passes for this failed scope, preserving
all source, directory layouts, terminal receipts and prior cases01-08.

Diagnostic intervals: worker inputs27.125s, eight software checks42.469s,
13 parent checks18.517s, one full pair check10.219s. They overlap and are not
campaign clocks. The read-only profile identifies two role layout scans5.813s,
including repeated membership checks. Next compose membership validation around
complete private two-role resolution, retaining fresh authority and full lexical,
file-type/size/hardlink/layout/source checks. No larger reservation or unchanged
rerun is selected.

All438 source pins match. All40 real authority tables remain unchanged at
$4.887796, preserving the old$0.7554 and four$1 holds and every consumed decision.
No owned runtime remains; D18/D19 do not authorize M1 inference.

Coverage inherits M1.6q.8 F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Complete live matched-state/tool parity, native admission,
authoritative clocks/disposal, T05/T10 and full root/helper isolation remain
open. Three symlink-privilege skips cannot qualify those missing routes.
M0/G0 and unrelated M2-M7 remain unchanged.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-held-parent-phase1` | 12,564 / 6,175,831 | `83761e8a41111b3367d7ca1b80e35c662772d6ae61299a35854ee7106c3c40a8` |
| `2026-09-25-m1-held-parent-phase2` | 12,564 / 6,198,557 | `e230fe40a8beee5d6f45a660de52cb2a72fef4866f702170523ad32e5e735c70` |
| `2026-09-25-m1-held-parent-checks-01` | 1,930 / 11,839,556 | `578b4b0b29deded585bb624ed70bfc3215839af36405a77d7437fa2c5f11ad09` |
| `2026-09-25-m1-worker-pair-native-09` | 684 / 47,132,251 | `0cdd369f44624b8925efa74ac8e894e3d0bcfbe77c09b7482e5c82d5d25f6698` |

All four archives independently verify. Complete test subtrees were copied with
byte equality and directory preservation to stay within per-archive file limits.
The assembly proves every27,052 original evidence files represented; the working
profile-01 directory remains retained unsealed. All420 prior milestone IDs remain
(421 current),1,658 local links resolve, progress is append-only and prior SPEC
text/JSON are unchanged. These seal pointers follow the documentation snapshot.
