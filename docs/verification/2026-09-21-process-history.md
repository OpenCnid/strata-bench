# M0 complete retained process-history verification

September 21, 2026. Operator-only. M0.2c.3b.3b.3b.1 and
M0.2c.3b.2b.3.2; F09/F13/F16, N01/N02/N04/N05/N06/N08,
partial T01/T07/T08/T13 and G0. M0 remains incomplete.

## Decision and implementation

The [protected reference failure](2026-09-21-authentic-writer-preparation.md)
captured a successful Windows query with 19 assigned processes but 18 list
entries, despite a 256-entry buffer and 94 already retained handles. The run
remains UNCERTAIN. Its final complete termination cannot retrospectively prove
what was known at the failed observation or erase the interrupted action.

The private reference supervisor now declares
`complete-retained-job-history/1`. `WindowsJob.observe_members` remains strict
by default; only the private `OwnedCli` explicitly enables the new verification
path. This changes the implementation's process-evidence policy, not gameplay
affordances, process quotas, deadlines, terminal requirements or the 500-ms
guardian threshold. No request or game action is replayed.

An incomplete successful list query can continue only when:

1. Counts are ordered and within the original 256-process quota, listed PIDs
   are valid/distinct, and every listed process is already retained.
2. A separate query on the **same held Job** reports lifetime TotalProcesses
   exactly equal to the distinct, previously membership-validated retained
   handles. Assigned and active counts must fit that history; a reported
   limit-induced termination rejects the proof.
3. Every retained process handle still supports a valid signal-status query.
4. The supervisor durably publishes the anomaly and independent measurements
   before continuing. Publication failure or the 64-record journal limit is
   sticky and blocks further admission.

No later PID-list retry, unseen PID lookup, new handle, guessed death or
active-count equality substitutes for complete history. Final termination
still requires Job active count zero and equality of lifetime total, retained
handles and signaled handles, with complete logs and the original watchdog.
The exact proof records are included in the terminal report.

Microsoft defines TotalProcesses as the Job's lifetime association count,
including exited processes and failed associations due to limits. It defines
ActiveProcesses separately. Those semantics support the independent count
check; they do not establish the cause of the original incomplete list.
[Accounting structure](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information),
[process-list structure](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list).

## Focused verification

Windows x64 / Python 3.12.14 / Temurin 17.0.20.1+1, existing pinned JVM fixtures.
Private evidence: `2026-09-21-process-history-01`.

- `tests/test_process_history.py` and `tests/test_processes.py`: **40 pass**.
  Complete-history positive; strict-default rejection; missing handle, unseen
  or undercounted history, foreign/duplicate entries, quota, invalid handles,
  accounting failure and limit termination negatives. Publication/quota
  failures remain sticky. A real nested Windows Job test injects an incomplete
  list while leaving native handles/accounting intact, and verifies normal
  full termination. This is API-response fault injection, not a natural kernel
  mismatch reproduction.
- `tests/test_reference_pair.py`, `tests/test_writer_custody.py` and
  `tests/test_protected_reference.py`: **51 pass**, with explicit pinned server
  and client JVM fixture profiles. Includes the actual non-input-desktop
  guardian fixture, failure retention, hard deadlines, interrupted coordination
  and missing-history rejection. No skipped selected cases.
- Standalone production `OwnedCli` with actual nested Windows Jobs: injected
  incomplete-list positive publishes one proof; withholding an actual retained
  handle rejects with no proof. Both stop **10/10** normally in 0.469 seconds,
  with complete logs, unchanged source pins and the same 20-second maximum.
  The rejected fixture restores its withheld test handle only for cleanup;
  its failed observation remains a rejection.
- Ruff passes. The initial Ruff invocation caught imported pytest-fixture
  shadowing; the explicit fixture annotation fixes that lint issue. Tests had
  not run in that rejected invocation.

These 91 distinct checks and two native cases prove only the named contracts.
No model or Minecraft was launched by them; no desktop input or outside process
was targeted. They do not qualify broad isolation, recovery or scoring.

## Changed authentic reference

Fresh private `2026-09-21-protected-craft-live-04` used unchanged initial
case-01 source inputs and a new scope/workspace/grant. Case 03's saved world,
interrupted action and authority remain retained. Server/client/participant,
copy and guardian limits were unchanged; only the supervisor policy changed.

Full protected preparation verified at 153.656 seconds. The real server/private
pipe bound successfully and the owned client joined. All seven ordinary
operations, the expert furnace resource witness, native actor/team/mode points,
independent saved inventory/chest/drop checks and source pins pass. All **80
primitive charges reconcile**, with no unknown requests. There are **288
complete authenticated records / 5,700 sampled server ticks**.

The run nevertheless **fails**. Guardian wait-to-signal is **500.1327 ms**
against **500 ms**; whole call-to-check is 500.9600 ms. Its independent held-handle
observer sees the same signal at **500.1326 ms**, with a last unsignaled wait
ending at 494.7770 ms. Keep the original timing, faults and failed verdict. The
root's sampled memory at 242.0199 ms into the wait was 2,268,536,832 working-set
bytes / 5,676,453,888 private bytes; this is a diagnostic observation, not proof
of the cause. No timeout allowance or measurement start was changed.

Pair status is UNCERTAIN after 648.313 seconds; client startup/total are
193.031/285.344 seconds. Normal terminal histories are preparation **10/10**,
inner server **14/14**, outer server **29/29** and client **118/118**, with no
forced outer stop and no Java remaining. Credentials were retired and the
ordinary input desktop was unchanged. No incomplete list occurred, so this
actual game run produced **zero reconciliation proofs**; the injected native
cases above remain the evidence for that branch.

The complete trajectory audit fails **4/32**: paired lifecycle, guardian,
protected lifetime closure and candidate import. Its other 28 checks pass.
A separate **18-check failure audit passes**, verifying those retained failures,
cleanup, costs and `CRAFT_PROTECTED_REFERENCE_UNQUALIFIED` import rejection.
The private saved copy is a stopped reference, not a qualified game/agent
checkpoint or scored run. No failed case is retroactively relabeled.

Next investigate the exact shutdown/resource path with finite owned native
fixtures and the preserved memory/exit observations. Make a relevant source or
explicit resource-profile change before another game trial; do not repeat this
profile unchanged. Preserve every earlier failed 500-ms sample, five
effective-file failures, Mineflayer/E9E incompatibility, sibling-read/loopback
failures, and remaining setup/scorer/provenance/recovery requirements.

Read-only preflight at 10:58:04 UTC retains the original $10 model allowance and
unresolved $0.7554 reservation counted once. Token/call figures are bounds, not
measured usage. This operator reference makes no model call and uses no shared
desktop input. All original failures, scorer/provenance/recovery requirements,
M0–M6 scope and M7/extension conditions remain. G0 fails; G1–G5 are not run.

Final evidence inventory rehash verified all 497 retained files (109,887,903 bytes);
manifest SHA-256 is `3250619b0ddaaaf184c3b1c54c3cb91832532f8074587dde7ed282311e70f5ad`.
The two residual SQLite WAL files are empty. Source validation confirms 289 unique
milestone IDs, 1,078 local links and unchanged append-only prior history.
