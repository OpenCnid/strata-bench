# M1 held-process drain and stopped cell disposal

Operator-only. M1.3b.6, inheriting M1.3b.5 coverage: F03/F04/F07/F11/F16,
N01/N04/N06, C06/C12/C13/C18/C20/C36, partial T01/T04/T06. M1 remains
in_progress; G1 remains not_run. No filesystem/network or full isolation claim.

## Implementation and authority

[ManagedProcess](../../src/mcbench/processes.py) now observes the original held
Windows Job Object after stop. A terminal parent is insufficient: zero active
job members and a nonempty lifetime process count must be observed while the
no-breakaway job handle remains held. Observation is bounded to two seconds;
query failure, live descendants, missing parent exit or a released handle fails.
Cleanup still closes the job and streams when evidence collection fails.

The [native supervisor](../../src/mcbench/native.py) records a private
[NativeProcessDrain/1](../../src/mcbench/native_process_drain.py) only after
cleanup succeeds. The proof binds launch intent, exact profile, start time,
return code, held-job counts, observation time and a durable supervisor event.
Readback requires that same finalized job, matching private CAS bytes and event.
Legacy parent-exit assertions and POSIX groups cannot provide this Windows proof.
The proof itself settles no consumption and grants no helper or game authority.

[Stopped export](../../src/mcbench/native_export.py) may use
`native-process-fenced-cell-disposal/1` after its existing closed-participant,
complete-settled-receipt, ingress, broker-work, source and artifact checks pass.
It records unresolved call IDs as disposed, with tool_success_inferred=false.
No fabricated successful code result, refunded cost, restored session/cache or
checkpoint/restore permission is produced. Malformed, changed, duplicate and
out-of-scope source evidence still fails. Early helper retirement continues to
require per-cell proof; passing stopped_job=true alone cannot bypass this.

This resolves the named scalar-only path from the
[notification-safe drain report](2026-09-24-m1-notification-drain.md) through an
independent whole-process fence, without interpreting model-controlled text.
It does not make ambiguous scalar results valid early-retirement evidence.

## Actual outcomes and retained failure

Both fixtures use the pinned CLI0.154.0-alpha.6.2 and companion binaries,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, selected GPT-6 Luna
catalog /3, local scripted provider, fake OAuth and synthetic worker. Zero real
inference, Minecraft launches or shared-desktop input.

| Private attempt | Actual outcome |
|---|---|
| `2026-09-24-m1-process-drain-01` | Original29/48. The reused state protocol raced its peer-cell readiness check: STATE_PEER_CELL_NOT_READY. Eight requests, seven settled/one uncertain, native exit1 after24.851577s. Physical drain was recorded, but the job remains UNSETTLED with its full120,000 synthetic-unit reservation. Export refuses RUNTIME_NOT_QUIESCENT; direct drain-proof readback refuses NATIVE_PROCESS_DRAIN_NOT_FINAL. |
| `2026-09-24-m1-process-drain-02` | Changed focused fixture deliberately leaves one silent cell pending per caller, observes the helper's actual delivered final reply with bounded joins, then ends the native job. Original28/28, nine settled requests (six root/three helper),90 input/36 output tokens,126 synthetic units, two CLOSED participants/envelopes and native FINALIZED exit0 after27.197992s. |
| Independent `-02` audit |15/15 joins every raw CAS capture, authenticated ingress/admission/catalog and settled receipt; reads the held-job proof (six lifetime processes, zero active); reconstructs the committed stopped export; verifies both unresolved cell IDs remain classified as disposed rather than completed, no late owned artifact appears, and the ordinary early-retirement verifier still refuses those scalar results. |

The focused fixture is [native_process_drain_probe.py](../../tools/native_process_drain_probe.py).
It does not repeat the prior foreign-cell/state matrix to obtain a lucky pass.
The pending cells target only owned late-effect artifacts; absence alone is not
the drain proof. A separate actual Windows test starts an owned descendant that
survives its parent, observes drain refusal, then verifies zero active members
after stopping the held job.

Exact profiles: failed `-01`
`56a220dec56bc29188d115d9d99e205721dec5c3bbb58085cd1f3123794d6c11`;
focused `-02`
`2d92d5af0c21a700873d5d5ecb0d153ed4894690b53dfcacfc3d505ba2d4706b`.
All40 real authority tables and every historical hold/consumed decision remain
unchanged. Synthetic units are not dollars. No owned fixture process remains.

Private bundles under `C:/Users/Darian/.strata/evidence/` pass independent
extended-path seal and original-result readback:

| Bundle | Files / bytes | Seal SHA-256 |
|---|---|---|
| `2026-09-24-m1-process-drain-01` |3,828 /75,246,637| `8e4d2088a969c3d8a91923cfd8b7ac888356e8a85a51e07f5ef39b8f97dbd63c` |
| `2026-09-24-m1-process-drain-02` |3,838 /75,714,017| `52af71d7ae29d61e8285ee8387b5e1da7cd337fc24bb7dd3d979a6192d957ed8` |

## Checks and next work

217 focused tests pass across owned process supervision, proof/disposal,
native launch, cell/retirement, export and checkpoint. Five additional malformed
wait-argument cases then pass with all17 disposal tests:222 distinct cases.
Full Ruff and whitespace pass. Final wait-field hardening occurred after the
export was produced; the independently archived revised verifier reproduces the
same committed export. No evidence files or historical successful states were
rewritten to gain a pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_processes.py tests/test_native_process_drain.py tests/test_native_process_disposal.py tests/test_native_process_drain_probe.py tests/test_native.py tests/test_native_cell_lifecycle.py tests/test_native_retirement.py tests/test_native_export.py tests/test_native_checkpoint.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_process_disposal.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

Next verify selected-profile concurrent helpers and correct-team versus
cross-team communication, then remaining SPEC13.5 routes and actual game/credential
admission. Executable skills, capable keybindings, scorer controls and matched
probe disposal remain required. This is no G1, full recovery or soak claim.
