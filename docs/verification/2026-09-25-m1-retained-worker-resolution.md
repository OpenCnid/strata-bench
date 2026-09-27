# M1.6q.2 retained worker-resolution custody

Status: **implemented_unverified** for authentic paired-worker integration.
Cases01 and02 remain failed with PROBE_WORLD_DEADLINE. Their original finite
300s parent,200/170s writer and60/60s server windows remain unchanged.

The private launcher now retains the exact runtime opened during sealed worker
resolution through configuration and owned cleanup. Previously resolution closed
that runtime and the launcher opened/hashed it again. Both paths still perform
the complete authoritative PackLock/provisioning read, installed layout and
executable checks, worker manifest validation, final per-file link checks under
held parents, held-handle hashing and membership checks. No validation result is
cached across calls. Public read-only resolution returns the same JSON and closes
its handles; it creates no configuration. No profile/wire identity or gameplay
capability changes. Default and deferred configuration semantics remain intact.

Context-managed resolution closes its runtime on validation failure, later server
resolution failure, configuration failure, normal return and exceptional owned
cleanup. Whole-roster account checks still precede every configuration commit.
The launcher does not gain native probe admission or full isolation authority.

Focused synthetic verification with actual Windows file leases:

```text
pytest tests/test_pack_launch.py tests/test_pack_worker.py tests/test_probe_worker_inputs.py -q
pytest tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save tests/test_pack_forge.py::test_full_seal_materialize_resolve_relocates_every_path_without_credentials tests/test_pack_restore.py::test_restoration_is_exact_new_instance_and_connects_held_worker_and_recapture -q
```

The selections pass90/161.85s and3/41.22s,93 distinct cases. New cases prove the
same runtime remains held without close/reopen until launcher exit, worker and
server resolution failures release it before config/process creation, and both
public resolver paths release handles without config writes. Existing strict
path/profile/configuration failures, deferred no-dispatch, owned cleanup, late
account mismatch and whole-pair lifecycle ordering pass. Separate Forge and
restored-worker examples retain their behavior; these are synthetic software/
process tests, not authentic Forge or isolation qualification.

A no-dispatch diagnostic uses the same authentic profile02 with fresh empty
state and an unwritten configuration path. With cProfile, deferred launcher
entry takes23.844s and the complete enter/receipt/close sequence24.891s. The
profile records one runtime lease construction;11,725 files/654,090,742 bytes and
manifest7ca5ff3d4df7f3e86485aab112db12ed6abf196b488ddef91da2f12348afa511 remain
pinned. A write-open is denied while held; runtime closes afterward. No worker,
game, provider or model runs, no configuration is created, and all40 real
authority tables remain unchanged. Profiling costs are diagnostics, not an
admission latency certificate.

Fresh authentic paired-worker case03 uses the same pinned worker/profile/world
and unchanged windows. Low-overhead test-only intervals record parent/software/
worker preparation and lifecycle events, including failures, then write after
the attempt. Nested intervals may overlap and are not authoritative campaign
clocks. Agent/protocol/capacity fixtures remain synthetic; no model calls or
full native/scientific probe claim.

Case03 fails in176.62s after both protected copiers and both worker imports, before
any server launch intent. Both copied374 files/239,730,374 bytes and162 directories;
each copier has a normal10/10 retained-process stop, zero active/terminated Job
Object processes, complete logs and no forced stop. Both import stdout logs report
vanilla_runtime_loaded with the pinned capability digest and avatar_created=false.
The implementation checked worker import job receipts in memory, but did not
persist them. Do not claim a retained full import-job proof from stdout alone.
No gameplay worker, server, provider or model starts.

The experienced writer retains PROBE_WORLD_DEADLINE after both initial-state holds;
the outer initial writer and world row report PROBE_WORLD_CLOSE_UNCERTAIN. The
coordinator's aggregate pre-server window check cannot fit120s of requested
server lifetime into the remaining writer lifetime. Keep both error levels.
Both writer rows/custody remain UNCERTAIN, the world row FAILED and parent FENCED,
with every capacity/cost hold retained. Normal copier termination does not turn
uncertain writer custody into disposal or a successful paired reference.

The diagnostic intervals show worker preparation13.875s/13.734s. Ten software
checks total60.546s;15 parent checks total12.594s, overlapping software checks.
Both initial states are held at140.250s/145.625s from acquisition start, and later
checks run through159.437s. Total measured acquisition-to-return time is161.843s.
Do not sum overlapping intervals or substitute these test diagnostics for
authoritative campaign clocks.

The read-only failure audit joins435 source files, both retained copier receipts,
the import logs, failed world/writer state and unchanged real accounting. All40
tables remain unchanged at$4.887796 with the old$0.7554 and four$1 holds and
consumed decisions intact. No owned runtime remains. D18/D19 do not authorize
M1 inference spending.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-worker-pair-native-03` | 676 / 47,064,244 | `af573320a7f2b26eca76223a17dfbe48d1f5eed82f4db2cc69a4e14aa0c554e7` |
| `2026-09-25-m1-retained-worker-cost-01` | 9 / 108,142 | `4bde799e42161e4ab9b80289b492dc829eedf04158611ea5cf125ec1ca23f735` |
| `2026-09-25-m1-retained-worker-resolution-01` | 8,610 / 21,603,962 | `3bfff7b9648c5a9d0974b64d6c9fa756c93b60a8d7f2059c6e93c532d291664b` |

All three bundles are sealed and independently verified using extended Windows paths.
The source store retains all93 passing cases, fixtures/logs/XML,435 source files,
final authority/process checks and documentation audit.413 previous milestone IDs
remain (414 current);1,623 local links, append-only progress, prior SPEC/JSON,
Ruff and whitespace checks pass. Final seal pointers and the clarification below
follow the archived documentation snapshot.
Next address repeated full software validation while protected writers are held,
especially the coordinator check followed by worker-custody checking the same
software again. Preserve authoritative state reads, exact held bytes/membership,
failure paths and original deadlines. Also persist import ownership receipts and
surface the already-retained inner refusal at the coordinating boundary before
another changed authentic case. The nested writer/world records already retain
both errors; that evidence is not missing.
No unchanged retry, larger window or gate reduction is supported by case03.

Coverage inherits M1.6q F01/F02/F04/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial T01/T06/T11.
Full live body/tool/policy parity, native admission, clocks/disposal, T05/T10 and
remaining isolation/native-loop evidence remain open. G1-G5 stay not_run. M0/G0,
historical failures, profile identities, holds and unrelated M2-M7 are unchanged.
