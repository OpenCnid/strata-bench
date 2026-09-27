# M1.6q.13 imports before writer acquisition

**Successor verification:** [native11](2026-09-25-m1-worker-pair-native.md)
passes the named actual vanilla N=1-per-arm paired reference under original
bounds. This child is now verified for that scope; full G1 remains open.
Earlier status/results below are preserved history; sealed archives unchanged.

Status: implemented_unverified for authentic paired integration. G1-G5 not_run.

Complete worker imports now run after durable pair admission, whole-scope storage
and namespace checks, and native-input custody, before either writer is acquired.
The parent deadline includes this work. Each normal owned-stop receipt is flushed
before marking its member imported. Current configuration/runtime/account/source
checks remain, and later execution requires the same preparation and writer-plan
digest. Early failures clean owned import processes/logs; running failures still
clean workers before server-writer unwind. The server-only path remains supported.

HeldPackWorker's private preflight deadline accepts only finite numbers for import
mode. It is checked after input revalidation, immediately before process creation.
Waits also check the original parent bound before and after completion. Original
writer/server windows remain unchanged. Imports grant no gameplay/native probe
authority and do not release resource or cost reservations.

```text
pytest tests/test_worker_preflight_deadline.py tests/test_pack_worker.py tests/test_probe_worker_runtime.py -q
pytest tests/test_probe_world_copies.py tests/test_probe_vanilla_runtime.py::test_both_registered_servers_stop_export_and_keep_sibling_capture_immutable tests/test_probe_vanilla_runtime.py::test_pair_runtime_reserves_whole_scope_before_any_server -k 'not actual_native' -q
```

Main78 cases pass849.16s; copy/server17 pass386.93s, with one authentic opt-in
case explicitly deselected.95 distinct passes, no skips/failures; two existing
Typer warnings remain. Tests use synthetic processes with real Windows custody.
They verify both import receipts before each writer, no writer roots on import
failure, changed authority, parent expiry/copier refusal cleanup, late deadline
refusal before process creation, stopped exports and unchanged reservations.
Ruff/whitespace pass; source hashes captured during the suites remain unchanged.

One changed native10 attempt uses actual profile02 vanilla software/workers and
the retained UUID-bound world, with synthetic agent/protocol sources and zero
model calls. Preparation and dispatch checks verified all95 passes,441 source
pins, original world/helper/binding pins, free port25565, sufficient resources,
no owned runtime and unchanged durable authority. Its one-use input is
`cf3aadb467a40cc6085ddeb3c5fafcceda3fb7a69a82ead9b27fa1a7830f58ea`.

**Native10 fails233.02s** (JUnit231.798s), with PROBE_WORLD_DEADLINE before durable
world-copy admission. No import, copier, server or gameplay worker is dispatched.
The parent is FENCED; resources remain reserved. There is no world-copy row and
no writer-preparation table, and the fresh external evidence parent is empty.
Both configuration files exist but their worker state directories remain empty;
no preflight output directories exist. The new import ordering was not reached.

Recorded parent preparation spans211.969s. The first worker-input entry takes
148.437s; the second11.094s. Software input preparation takes20.468s. Five shared
software checks total15.062s and seven parent checks8.531s; intervals overlap and
must not be summed as exclusive campaign time. At admission, the remaining parent
window cannot cover the original first200s writer. Parent300s, writers200/170s
and servers60/60s remain unchanged. The cause of the long first entry is unknown.

Independent failed-attempt audit verifies the actual empty dispatch scope,
durable fencing/retained resources, all441 unchanged source pins, no owned runtime
and all40 real authority tables unchanged at$4.887796. D18/D19 remain M0-only;
no M1 paid authority is inferred. All prior cases01-09 and consumed decisions
remain; native10 must not be replayed or rerun unchanged.

Next isolate the first HeldPackWorker input-entry delay with read-only phase
profiling under fresh diagnostic custody, preserving both native10 timings.
Resolve the named preparation bottleneck before selecting another game trial.
Component speedups and synthetic ordering checks do not prove full paired timing.

Coverage inherits M1.6q.12: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Full live matched-state/tools, native admission,
authoritative clocks/disposal, T05/T10 and complete root/helper isolation remain
open. M0/G0 and unrelated M2-M7 remain unchanged.

Private evidence is sealed under `C:/Users/Darian/.strata/evidence/`:

| Archive | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-prewriter-imports-01` | 14,502 / 45,604,709 | `bfc91309dbe73cada303beac38afd7ab5ac6c5a75f408409bc91022075ad24e2` |
| `2026-09-25-m1-worker-pair-native-10` | 669 / 44,767,353 | `2ae54226446f86ea7334735d4a74dd1e24551015631663dccf9dcc48e30bd45b` |

Both bundles independently verify. They retain complete source/test/native
artifacts, failed-attempt audit, authority/process checks and timing records.
Final documentation audit preserves all424 prior milestone IDs, addsM1.6q.13,
checks1,679 local links, append-only progress and unchanged prior SPEC text/JSON.
These seal pointers follow the archived documentation snapshot. Never mutate
either sealed root or any earlier evidence archive.
