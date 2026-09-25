# M1.6q.5 held materialization rechecks

Status: **implemented_unverified** for authentic paired integration. G1-G5 remain not_run.

Case05's worker projection and normal stop passed, but the finite server died
while repeated validation delayed the controller's stop. Its watchdog, forced
cleanup and unresolved writer custody remain in the
[previous evidence](2026-09-25-m1-initial-worker-projection.md).

A private fresh vanilla-server resolver now uses hashes computed through live
Windows file handles that deny writes/deletion. The hash map records the actual
verified handle contents separately from the supplied inventory dictionary;
editing that dictionary cannot invent a new digest. Closed or missing handles,
unknown paths, foreign trees, unsupported scopes and missing executable custody
refuse. The paired software owner now holds its external server executable along
with inventory metadata and the entire materialization.

Every call still opens a fresh read-only provisioning snapshot and verifies the
current profile, sealed request, lock, CAS visibility/content, acquisition report,
inventory and launch profile. Exact root membership, marker, both role layouts,
empty directories, portable names, collisions, types, sizes, hardlinks, reviewed
paths, environment and executable digest remain checked. The directory scan can
use a digest only for the exact path in a live FileLease; new files and directory
changes are still rejected. Initial acquisition still performs final path checks
under held ancestors and hashes through each retained handle. Public resolution
and unheld inventory scans retain their normal hashing path. No new model,
dispatch, isolation, native-probe or checkpoint qualification is granted.

The first focused selection passes102, skips three native symlink cases due to
unavailable privilege, and fails one closed-custody refusal-order assertion in
38.77s. Both closed custody and unsealed authority already refused, but authority
was read first. The private entry now checks custody before reading authority.
Initial source and failure remain. A subsequent selection typo named a nonexistent
test and collected no cases; its output is retained separately from verification.

```text
pytest tests/test_held_materialization.py tests/test_launch_integrity.py tests/test_inventory_directories.py tests/test_pack_launch.py -q
pytest tests/test_held_materialization.py tests/test_probe_vanilla_inputs.py tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save tests/test_probe_vanilla_runtime.py::test_both_registered_servers_stop_export_and_keep_sibling_capture_immutable -q
```

The corrected second selection passes45 in492.01s, giving134 distinct passing
cases across both selections. It covers equality with public resolution without
reopening file hashes, current authority revocation/corruption, empty-directory
addition/removal, root/file membership, missing executable custody, foreign or
closed leases, caller-mutated inventory digests, unapproved but held bytes and
hardlink mutation. Paired source/state/directory failures and both worker/server
lifecycle positives pass. Existing actual junction, handle hashing and lease
release tests pass; the three symlink privilege skips remain explicit. Ruff passes.
These are synthetic software/process cases with actual Windows file custody.

A read-only diagnostic on genuine profile02 measures public resolution4.875s,
custody acquisition7.703s and two held rechecks1.891s/1.953s. Both rechecks return
the unchanged resolution digest
011e977b1cbb34474e8c32bb870d09820454456e184627cc66423d07610b6456.
Write-open attempts on the held server and external executable are denied and
custody closes afterward. No config, game, provider or model starts. These timings
come from the retained initial source version and are diagnostics, not a latency
or operating-envelope certificate.

Fresh case06 preserves the original parent300s, writers200/170s and servers60/60s
on pinned profile02/runtime02/source world. It fails in210.41s after completing
the first server's normal stop and stopped export. Both copiers stop normally
with10/10 held processes signaled; both import receipts show exit0 and three
total/zero active or terminated Job Object processes. The first worker's exact
identity/journal/saved projection passes; its persisted normal stop/custody
receipts show seven total/zero active or terminated processes, supervisor34.7719ms
and owner93ms. The first server exits0 without force; all12 retained processes
are signaled, logs are complete and no recognized critical log signature appears.

The first stopped snapshot verifies27 files/13,699,033 bytes with manifest
f59188f9530fdcc721ebe406f8bcdae0a14bbb507b8a87046ac1c7b9d7664cd7.
Its complete-checkpoint and clean-save-proven flags remain false. The offline
audit's first copy omitted empty directories and failed VANILLA_CAPTURE_CHANGED;
its script/output remain. Correct directory-preserving evidence copying verifies
the original unchanged export. This is an audit-copy correction, not a new game
attempt or a changed native failure.

After the first stopped export, the second launch intent is recorded, but
WRITER_EXPOSURE_INSUFFICIENT refuses dispatch because its complete60s server
window cannot fit the remaining writer reservation. No second server or worker
starts. The outer error remains PROBE_WORLD_CLOSE_UNCERTAIN. Both writer rows
remain UNCERTAIN, world FAILED and parent FENCED, with every reservation held;
normal first-server termination does not prove full pair completion or disposal.
Cases01-05 remain failed, with no larger bounds or unchanged retry.

Initial-state holds occur110.406s/115.734s after parent acquisition, first launch
intent122.531s and ready159.578s. Normal stop is requested184.703s and the stopped
export is held189.703s; the second pre-launch software check ends192.906s.
Thirteen software checks total42.095s;19 parent checks total16.441s overlap them.
Worker input preparation still costs13.515s/13.062s because each public worker
resolver independently validates the same materialization before its own runtime.
Next connect already-held materialization custody to those private member
resolutions, retaining fresh authority, separate member/runtime/config/account
custody, whole-roster admission and all unchanged bounds. Also retain the distinct
normal-stop, stopped-export and complete-checkpoint claims. These timings are
diagnostic intervals, not authoritative campaign clocks or additive totals.

The failure audit matches436 source pins, both copier/import records, worker
identity/journal/stop/custody, the normal server terminal record, stopped snapshot
and fenced reservations. All40 real authority tables are unchanged at$4.887796,
with old$0.7554/four$1 holds and consumed decisions intact. No owned runtime
remains; no model call or M1 inference authority. Agent/protocol/capacity fixtures
are synthetic; authentic game/worker input does not confer native admission or
scientific-probe qualification.

Coverage inherits M1.6q F01/F02/F04/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial T01/T06/T11,
plus F05/partial T02 inventory integrity. Full live-state/tool parity, native
admission, clocks/disposal, T05/T10 and remaining isolation/native-loop evidence
stay open. Historical failures, profile identities, holds, consumed decisions,
M0/G0 and unrelated M2-M7 remain unchanged. D18/D19 do not authorize M1 inference.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-worker-pair-native-06` | 727 / 66,138,754 | `d79517c17ac0ec42a8274667aad2fb5c4785421e4825549cbd79e5f2780caa38` |
| `2026-09-25-m1-held-materialization-phase1` | 12,109 / 6,649,123 | `8b9778ba319b278b2706ef4308ae0b23194a0580c764b607bf0ddd18625d796f` |
| `2026-09-25-m1-held-materialization-phase2` | 11,069 / 31,893,950 | `b21c296dda4590227630eb3d6098b69106103a12b06212264d73b61cf6119265` |
| `2026-09-25-m1-held-materialization-checks-02` | 475 / 7,189,489 | `22aefffda03738a9c0725c90fecfb3c48c8e5cb7fe102e0efe44658145c250bf` |

All four bundles independently verify with extended Windows paths. The original
checks-01 working evidence exceeds one bundle's file quota and remains intact.
Byte-verified assembly represents all23,647 original files:12,107 first-selection
test files,11,067 second-selection test files and473 remaining source/log/document
files. Empty directories are preserved; the main bundle pins both full test parts.
No fixture or failure is excluded. Assembly/copy metadata and directory manifests
account for the additional files/bytes in the sealed rows above.
All416 prior milestone IDs remain (417 current),1,639 local links resolve, progress
is append-only and prior SPEC/JSON are preserved. Seal pointers follow the archived
documentation snapshot.
