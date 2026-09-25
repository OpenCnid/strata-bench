# M1.6q.8 runtime check composition

Status: implemented_unverified for authentic paired integration. G1-G5 remain
not_run. Source contracts pass; fresh native08 fails before runtime dispatch.

Every member lifecycle check validates runtime custody once: directly in HELD/
RUNNING phases, or through its full owned-stop receipt in IMPORTED/STOPPED.
Unknown phases refuse; a new check always revalidates. Preparation-only input
checks retain complete runtime/config/account validation. Standalone lifecycle
checks retain shared software/parent validation and software identity matching.

The first session performs complete pair validation and then tests the complete
aggregate server exposure against all current parent/writer deadlines, before
any dispatch. This replaces the adjacent earlier full check; no admission bound
is widened and preflight time remains charged. Later starts still fully check.
All35 focused source cases pass in791.39s with no skips/failures. These cover
actual Windows runtime custody in every member phase, repeated checks, changed
authority/configuration, post-stop failures, whole-pair reservation and reduced
parent/either-writer windows after preflight. Processes/profiles are synthetic.
Ruff/whitespace pass; two Typer deprecation warnings remain.

```text
pytest tests/test_probe_worker_phases.py tests/test_probe_worker_inputs.py tests/test_probe_worker_runtime.py::test_complete_pair_imports_before_servers_then_workers_drain_before_save tests/test_probe_worker_runtime.py::test_post_stop_validation_failure_refuses_export_and_sibling tests/test_probe_vanilla_runtime.py::test_complete_pair_window_is_checked_after_full_preflight_before_first_dispatch tests/test_probe_vanilla_runtime.py::test_joint_preflight_revalidates_after_first_session_before_either_dispatch tests/test_probe_vanilla_runtime.py::test_changed_authority_at_launch_boundary_never_dispatches_next_server tests/test_probe_vanilla_runtime.py::test_pair_runtime_reserves_whole_scope_before_any_server tests/test_probe_vanilla_runtime.py::test_second_arm_missing_launch_helper_refuses_before_either_server -q
```

Fresh native08 passed438 source pins, all40 real authority tables, host
capacity/port and one-use input checks. It retains profile02/runtime02 and the
source world from [identity-native02](2026-09-25-m1-worker-identity-native.md), with
input pin `c1b41556b9ce1da4cab218141cf9dfbf6db10b3185322e3c88bc5ff15ff89cc8`.
The original parent300s, writers200/170s and servers60/60s limits remain.
Agent/protocol/capacity fixtures remain synthetic. No model calls occurred.

The trial fails125.69s total (JUnit case124.398s), with PROBE_WORLD_DEADLINE
before the first copier/writer is admitted. Parent preparation lasts103.906s;
its last check ends103.500s, leaving less than the first writer's required200s.
No writer table or row exists, the external writer evidence parent is empty,
both worker state directories are empty and no worker import evidence exists.
Configurations were prepared, but no copier, import, server or worker launched.
The world row is FAILED, parent FENCED and resource reservations remain held.
Runtime check composition was not reached, so this result neither validates its
authentic timing nor replaces [case07's failed lifecycle](2026-09-25-m1-pair-stop-order.md).

Recorded diagnostic intervals include one26.875s software preparation,
two worker preparations totaling36.235s, five software checks totaling25.094s
and eight parent checks totaling10.095s. These intervals overlap and are not
additive costs or authoritative campaign clocks. Earlier case07's worker inputs
totaled24.297s; this variation is retained, not used to justify a lucky rerun.
Next profile pre-writer preparation without dispatch and reduce repeated work
under continuously held custody. Preserve fresh authority/layout/account checks,
original deadlines, all eight failed cases and all consumed reservations.

The scope-specific early-refusal audit passes: exact438 source pins, empty
runtime destinations, failed/fenced/unreleased durable state and all40 real
authority tables unchanged at$4.887796. No owned runtime remains. The prepared
post-dispatch audit was not run because no such evidence exists; it is retained
alongside the early-refusal audit. No M1 paid authority is inferred from D18/D19.

Coverage inherits M1.6q.7 F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Complete matched live state/tool parity, native admission,
authoritative clocks/disposal, T05/T10 and the remaining native/isolation
requirements stay open. M0/G0 and unrelated M2-M7 remain unchanged.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-runtime-check-composition-01` | 9,364 / 32,685,057 | `1af8a31b6d387ad7bbf67cd18862dcfa9a6a384e4af2672f93825f2766da3455` |
| `2026-09-25-m1-worker-pair-native-08` | 666 / 46,119,790 | `694dc4a2fcb7f10be95c6294de4132db2e0adc89b40ee001769fa6069b2e9ec8` |

Both archives independently verify with extended Windows paths. All419 prior
milestone IDs remain (420 current); 1,655 local links resolve, the progress log
is append-only and prior SPEC text/JSON are preserved. Seal pointers follow the
archived documentation snapshot. The authentic attempt remains failed.
