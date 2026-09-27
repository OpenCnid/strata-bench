# M1.6q.7 paired stop ordering

Status: **implemented_unverified** for authentic paired integration. G1-G5 remain not_run.

The paired coordinator now requests normal server stop before its complete pair
recheck. The stop method retains its scoped writer custody check; the complete
check runs during bounded drain, before capture/export acceptance or sibling
dispatch. Workers have already drained. Validation failure still fences the pair
and retains every reservation. A stop request cannot qualify an export. No
deadline, profile, pre-dispatch check or required acceptance condition changed.

```text
pytest tests/test_probe_worker_runtime.py tests/test_probe_vanilla_runtime.py::test_both_registered_servers_stop_export_and_keep_sibling_capture_immutable tests/test_probe_vanilla_runtime.py::test_failed_first_server_fences_pair_and_never_starts_sibling -q
```

All22 selected source cases pass in601.28s, with no failures/skips. Positive
checks require complete validation after stop and before capture. Revoked account,
changed member binding and lost software custody at the stop boundary prevent
the export and sibling launch while retaining fenced reservations. Existing
import/receipt/grant/state/stop/early-exit/history/between-arm cases still pass.
These use synthetic processes and profiles with actual Windows file custody.
Ruff and whitespace checks pass; they do not prove authentic paired readiness.

Fresh native07 passes pre-dispatch verification of437 source pins, unused inputs,
host capacity/port and unchanged real accounting. Input pin:
`3f4eacc7bf236e2e58cd5f67c057692bf0f74a68790627bb5a1f94c09e19decb`.
It retains genuine profile02/runtime02/source-world identities and the original
parent300s, writers200/170s and servers60/60s limits. Agent/protocol/capacity
fixtures remain synthetic; no model or gameplay actions are requested.

The trial fails221.33s before dispatching the second server:
WRITER_EXPOSURE_INSUFFICIENT, with outer PROBE_WORLD_CLOSE_UNCERTAIN. Both copiers
stop normally with10/10 owned processes signaled; both imports have persisted
exit0 receipts with three total/zero active or terminated processes.

The first worker verifies the exact delivered observation/journal, authenticated
saved-player identity and own-state projection. Its persisted normal stop/custody
shows seven total/zero active or terminated processes, supervisor50.4249ms and
owner109ms. The first server exits0 without force; all12 held processes signal,
logs complete and no watchdog appears. Its stopped export verifies27 files and
13,625,307 bytes, manifest
`6eaba97360e32786954833cfe7bc768db88c64c983fab304b63899452bab7f1e`.
Complete-checkpoint and clean-save-proven flags remain false.

The second arm records launch intent but starts no server or worker. Both writer
rows remain UNCERTAIN, world FAILED and parent FENCED, with all holds retained.
Preserve [case06 and earlier failures](2026-09-25-m1-held-materialization-checks.md)
and [q6 preparation evidence](2026-09-25-m1-worker-materialization.md); no unchanged
retry or widened time window follows this failure.

New diagnostic intervals place the first readiness at163.672s, stop request at
186.188s and held export at198.157s after parent acquisition. The stop method
takes0.109s. The complete check then takes8s; finish/capture takes3.969s. Five
composed pair checks total37.171s. Thirteen software checks total46.299s and19
parent checks total17.892s overlap other intervals; these are not additive totals
or authoritative campaign clocks. Both worker inputs total24.297s before writer
acquisition. The first stop now precedes validation, but overall execution still
does not fit the second writer's reservation.

Source inspection identifies repeated runtime membership validation: member
binding/file checks recheck each runtime, then imported/stopped phase receipts
recheck it again. Next compose these checks and inspect adjacent full preflight
checks, retaining exact current authority, runtime/config/account membership,
process phases and export validation at every required boundary. Do not replace
those contracts with a cached success flag or a larger deadline.

The audit joins both copier/import records, first worker identity/journal/stop,
normal server terminal history and stopped snapshot; all437 source pins match.
All40 real authority tables remain unchanged at$4.887796, with the old$0.7554 and
four$1 holds and consumed decisions intact. No owned runtime remains. D18/D19
remain M0-only; no M1 inference authority is inferred.

Coverage inherits M1.6q.6 F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36, partial T01/T02/T06/T11,
plus partial T07 stop/failure ordering. Full matched live state/tool parity,
native admission, authoritative clocks/disposal, T05/T10 and remaining isolation
and native-loop requirements remain open. M0/G0 and unrelated M2-M7 are unchanged.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-pair-stop-order-01` | 8,029 / 28,975,169 | `3c811f3e2e55a0406f0f54088aaab9f6edc5b44e8e2ac1c41cf5cfbe2fe3b94b` |
| `2026-09-25-m1-worker-pair-native-07` | 728 / 66,074,382 | `b0dfdd7a688a572424e4745a2d5442b861cb1dd1af0898bed086d64680a975d7` |

Both archives independently verify with extended Windows paths, preserving the
complete source tests, native failure, directory layouts, raw results and audits.
All418 prior milestone IDs remain (419 current); 1,650 local links resolve,
progress is append-only and prior SPEC text/JSON are preserved. Seal pointers
follow the archived documentation snapshot.
