# M0 authentic-size protected preparation

September 21, 2026. Operator-only. Partial M0.2c.3b.2b.3.2;
F04/F09/F10/F13/F16, N01/N04/N06/N08, C12/C24,
partial T01/T06/T07/T10/T13 and G0. M0 remains incomplete.

## Implementation

The complete E9E candidate contains 8,609 files / 563,288,796 bytes, including
the explicit telemetry 0.3.6 replacement and a new loopback port. The 104-file
world comes from the preserved initial fixture, with no new supplied resources
or setup commands. Original source and installation archives remain retained.
This continues the [protected pair](2026-09-21-online-reference-pair.md).

`FileLease` now retains native Windows handles and hashes through those same
handles with `ReadFile`, avoiding the CRT descriptor ceiling. Deny-write/delete
sharing and ancestor handles remain; partial failures close acquired handles,
and closed leases reject rechecks. The online preparation profile stops its
completed copier after the exact bound receipt, before the full content/ACL
audit, while original input/staging/workspace custody remains held. No server
can start before that audit passes. Offline ordering is unchanged.

Known declared pins supply input/staging inventories directly; retained-handle
hashing verifies the expected digests rather than replacing them with observed
bytes. This removes redundant by-name hashes. Full tree/content/ACL checks
remain mandatory. Monotonic phases and separate pre-admission time are recorded.
The private server's TEMP/TMP point into its workspace for the official
bootstrap's child JVM. No additional gameplay/network-isolation claim follows.

Limits remain: 12,000 files, 1 GiB, 20-second copier/22-second supervisor,
900-second preparation, 600-second server plus 120-second cleanup,
400-second participant and **500-ms guardian**. No threshold was relaxed.

## Verification and retained failures

Windows x64, Python 3.12.14, pinned Codex CLI and Temurin 17.0.20.1+1.
Private bundles: `2026-09-21-protected-craft-live-{01,02,03}` and
`2026-09-21-authentic-writer-profile-01`.

- Preparation/custody tests: **30 pass** before final inventory optimization.
- Native file-lease tests: **16 pass**, including 8,300 simultaneous files,
  multi-chunk hashing, denied writes/deletion, late-hash cleanup and closed leases.
- Final preparation tests: **21 pass**, including changed declared bytes and
  conflicting runtime pins. These suites overlap: **48 distinct passing checks**.
- Ruff and diff checks pass. These focused checks are source/native-file
  evidence, not authentic gameplay acceptance.
- Case 01: `OSError(24)` before pair reservation/native dispatch. Unused session
  arguments retired; original failure preserved.
- Case 02: all 8,609 files copied/verified, normal 10/10 preparation termination.
  `WRITER_EXPOSURE_INSUFFICIENT` then refused the server gate; outer 15/15 stopped
  normally, no producer settings/client/game/model dispatch. Authority remains
  reserved and UNCERTAIN; unused session arguments retired.

Changed case 03 verified the full tree at **154.266 seconds** into preparation;
pre-admission validation took another 17.406 seconds. Copier return was at
92.188 seconds, normal 10/10. The remaining unchanged server window fit.
Actual E9E/telemetry 0.3.6 launched through held custody and the private pipe.
Independent held-process/token and authenticated native identity binding passed;
signing keys stayed in the operator broker. Readiness took 163.252 seconds after
reference launch, leaving the complete client window. The owned client joined,
opened the supplied chest, withdrew both ingredients, closed it and opened the
crafting table on the separate non-input desktop.

The pair then aborted on `PROCESS_MEMBER_INVENTORY_UNAVAILABLE`, phase
`client_monitor`: **incomplete_list, 19 assigned / 18 listed / 94 retained,
no Win32 API error**. The buffer already has 256 slots. Microsoft documents the
two counts and incomplete lists; this does not establish why this observed
mismatch occurred. A concurrent-exit explanation remains an inference.
[Process-list structure](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list),
[query contract](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject).

Pair status remains UNCERTAIN after 570.094 seconds of dispatch lifetime.
Outer server/client terminate **29/29 and 94/94**, complete logs, zero active,
no forced outer stop. Inner server stops normally **14/14** after cooperative
stop. The broker closes with **203 authenticated records / 4,069 sampled server
ticks**, no completed craft witness. Client abort cleanup retires temporary
session arguments; no Java remains and the ordinary input desktop is unchanged.
The guardian raw report remains fail with empty timing/fault arrays; this case
provides no measured 500-ms sample.

An independent **20-check failure audit passes**, confirming those facts,
unchanged pinned inputs, exact stopped saved-byte preservation and
`CRAFT_PROTECTED_REFERENCE_UNQUALIFIED` import rejection. This is a passing audit
of a failed run. The saved world is not a qualified game/agent checkpoint.
Cost reconciliation rejects `COST_ACTION_INCOMPLETE`: the frozen worker retains
**16 primitive charges**, five emitted receipts and one interrupted executing
receipt. These are partial counts, not a reconciled total; preserve all costs
and journals without replay/refund. The positive trajectory audit was not run
against this incomplete case.

Private evidence manifest: 938 files / 184,588,856 bytes; SHA-256
`680e978d9b9dee7d2a02e206ca0ca89e8c2b21ac8513c7d6e5b29b495428f0d6`.
Source inputs are separately fully pinned/audited; ephemeral Python caches and
SQLite shared-memory/WAL files are excluded. Later source-validation records
are separate. Initial documentation validation hit a default-codepage decode
error; explicit UTF-8 resolved it. A faulty subsequent line-ending pass
truncated owned documentation; those files were restored from HEAD and this
change reapplied before final history/link checks. Code and evidence were unaffected.

## Remaining work

Next qualify process enumeration on bounded native nested-process cases before
another authentic launch. An incomplete list cannot pass simply because a later
list looks complete. Any reconciliation requires independent complete retained
handle/Job-history evidence, preserved anomaly records and unchanged quotas,
deadlines and terminal requirements. This failed case cannot be relabeled.

Sibling-read/original loopback failures, all failed 500-ms samples, five
effective-file failures and Mineflayer/E9E incompatibility remain. Full
setup/history, joint scorer controls, parity/nonleakage, provenance and recovery
remain required. The read-only preflight at 10:23:06 UTC retained the original
$10 authority and unresolved $0.7554 exposure, counted once. Token/call figures
are reservations, not measured usage. No model request, allowance reset, refund
or shared-desktop input occurred. M0 incomplete; G0 fail; G1–G5 not_run.
