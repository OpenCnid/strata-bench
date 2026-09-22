# Prepared JVM resource profile

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.6;
F09/F13/F16, N03/N05/N06/N08, C14/C15/C18, partial T07/T12/T13/G0.
M0 remains incomplete and G0 fails.

[Client preparation](../../evaluator/src/strata_evaluator/reference_preparation.py)
now accepts version 2 with `hotspot-active-processors4/1`. Both existing
pre-dispatch checks verify the effective `-XX:ActiveProcessorCount=4` option
under the argument-file lease. The parser distinguishes JVM options, their
operands and the Forge main class; it rejects missing/duplicate/wrong/misplaced
processor options, nested option files, alternate entry points and incompatible
escaping. Reports contain no credential values. Version 1 keeps its existing
shape. This is input verification, not OS CPU reservation or shutdown proof.

`pytest -q tests/test_reference_preparation.py`: **30 pass / 0.79 s**;
focused Ruff passes. These are synthetic source checks. The earlier combined
preparation/pair selection passed 31 with 20 explicit-JVM cases skipped;
that invocation supplies no new pair-JVM evidence.

The installed pinned Temurin JDK reports compiler/parallel-GC/concurrent-GC
worker counts of 12/13/3 by default and 3/4/1 with the new flag. The candidate
keeps G1, the 512–3072 MiB heap, client settings/mods and ordinary craft workload.
The prior authentic **513.433/500-ms failure** and all earlier samples remain.
Fewer JVM workers are a hypothesis; no shutdown remedy follows from these flags.

Private case `2026-09-21-protected-craft-cpu4-01` failed **before game launch**
with `WRITER_EXPOSURE_INSUFFICIENT`. The outer preparation allowance was 900 s;
the registered 600-s server plus 120-s cleanup reserved 720 s. Tree verification
completed at 193.219 s, leaving insufficient exposure. Pair elapsed time was
247.812 s. The resource argument passed initial admission, but no client,
Minecraft server, game action or model request was dispatched. All 10 copier
and 15 outer held processes terminated without forced cleanup. Unused session
arguments were retired. A first retirement check used the absent client field
as a required key; the corrected missing-or-null check preceded deletion and
is retained in the retirement receipt.

The prelaunch-failure audit passes 12/12: original source and dispatch inputs,
process closure, no game/score/shutdown claim, credential retirement and the
unchanged $0.756858 held/settled accounting. Its 324-file inventory SHA-256 is
`7b0c07dac9e41db125586a45ce3e132c4ffdf7ed74af212fef7905dbbc639cd7`.
The consumed failed scope must not be reused.

Case 02 was separately registered from the original unplayed source with a
**stricter 540-s server runtime limit**, retaining the 400-s client window,
120-s cleanup, 900-s outer preparation allowance and 500-ms guardian bound.
This left 240 s for protected preparation. Tree verification finished at
196.282 s and the actual E9E server launched, but startup left insufficient
time for the complete client window: `REFERENCE_PARTICIPANT_EXPOSURE`.
The pair failed at 448.156 s; server dispatch lasted 204.125 s. No client or
gameplay action ran, so the CPU hypothesis remains untested. All 29 outer,
10 copier and 14 inner held processes exited. **Forced inner cleanup/exit 125**
is retained; this is not a normal server stop. The broker retained two records
and BrokenPipeError. Unused client credentials were retired. An 11/11 failure
audit retains unchanged source/accounting; its 329-file inventory SHA-256 is
`cdf8cca52098dead5f2db9890469b2b09b9994ae7a49ff373e7ea925c9661e74`.
No Java remains. Neither consumed scope can be restarted.
Both failure audits checked the source before the following implementation
change. Their dispatch archives retain the old pinned source; the current
checkout deliberately has a different path-validation digest.

The resulting preparation work changes
[launch path validation](../../src/mcbench/launch_integrity.py) to one `lstat`
per component, removing the preliminary following `exists` query. Missing
components still cause ancestor checks; links/reparse points and unexpected
access failures still reject. No result is cached and all file hashes, ACL,
inventory, leases and deadline checks remain. This is M0.3b.2c.3c.2b.2b.2.2a.6a,
a preparation optimization whose complete runtime impact remains unverified.

The launch-integrity/preparation selection passes **68 tests, with three native
symbolic-link cases skipped because that privilege is unavailable**. A subsequent
actual Windows directory-junction rejection passes separately, including a
missing descendant and intact target after junction removal: **69 distinct
passes / three skips**. Existing deny-write/delete/replace/rename, content and
inventory controls remain in the selection; focused Ruff passes.

Private `2026-09-21-path-walk-01` compares all 8,609 retained source paths against
the archived old implementation. The same paths take 3.089 s before and 1.819 s
after, with identical output digests. This one ordered metadata-only comparison
on a warm filesystem is not whole-preparation or shutdown qualification.
Next measure and fix the remaining protected preparation/startup cost within
the registered bounds before another CPU shutdown trial. Do not keep changing
time limits or replay these failed scopes.

Original $10 authority, $0.7554 unresolved hold, $0.001458 settled usage and
consumed D12 remain unchanged. No shared-desktop input or real model request.
Every effective-file/Mineflayer incompatibility and scorer/setup/isolation,
provenance, clock and canonical recovery requirement remains open as recorded.

Final source review preserves all 316 previous milestone rows and append-only
history, adding two children. SPEC sections 3 and 16–19 remain unchanged;
1,174 local links resolve, full source/tool/test Ruff and whitespace checks pass.
