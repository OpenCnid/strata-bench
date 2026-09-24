# Private worker resource measurements

M0.2c.1c implements the missing executor measurement producer and consumers for
G0 item6. It is **implemented_unverified** for authentic gameplay qualification.
The real LLM/Mineflayer pilot remains verified under its original profile;
these new measurements cannot be retroactively attributed to that run.
Coverage: F09/F11/F13/F16, N03/N06, C18, partial T07/T09/T12/T13.
M0 remains in_progress/G0 fail; M1–M7 and D14/D18/D19 are unchanged.

## Implementation and limits

[WorkerHealth](../../backends/mineflayer/src/worker_health.ts) starts before
backend initialization and ends after lane close, including failed initialization.
The existing FULL SQLite journal stores nominal1Hz windows and the final partial
window. Real monotonic boundaries and cumulative CPU retain delayed execution;
the producer never fills a stall with invented samples. CPU includes all threads
in this executor process, excluding its parent and other processes. RSS/heap,
external memory and array-buffer values are samples, not continuous maxima.
Node's10-ms-resolution delay histogram provides per-window count/min/mean/p50/
p95/max; these percentiles are never combined into a fictitious global p95.
The explicit1023-window bound exceeds the admitted600-second worker limit.

The startup record contains only projected campaign/avatar/epoch identifiers,
runtime identity and measurement policy. It does not copy private worker settings.
Metrics have no gameplay route. Startup journal failures reject initialization;
periodic write failures stop sampling and request worker shutdown. Missing final
evidence remains incomplete after abrupt termination. The terminal record closes
measurement, not gameplay success or clean-save qualification.

[The strict consumer](../../src/mcbench/worker_health.py) checks stream shape,
scope, sequence, contiguous monotonic windows, terminal placement, CPU continuity,
memory consistency and histogram ordering. It rejects malformed/unknown versions.
The native launcher, stopped native/vanilla verifier and Forge cost/restart reader
consume the records. Held/hashed worker membership makes the stream mandatory for
the new worker; legacy cost scopes retain null when no measurements exist. The
native verifier independently reconstructs and compares any recorded summary.

Remaining limits: pre-import/post-close time, parent/descendant resources,
disk/network I/O, between-sample memory peaks, histogram reset/journal overhead,
instrumentation overhead controls, actual server/avatar clocks and real-game
profile qualification. No TPS/MSPT/tick estimate is derived from client physics,
nominal20Hz or saved-world counters. Server native callback clocks remain a
separate existing Forge measurement with their recorded limitations.

## Verification

`npm run build` passes. Focused Node selection covers worker health, startup,
operator stop and action lanes:57/57 pass, final5.742s. The Python selection covers
worker health, native evidence, cost/restart joins, worker bundle/stop, retention,
continuation/recovery and sealed game binding:314/314 pass in40.10s, with two
existing Typer/Click deprecation warnings. Ruff and `git diff --check` pass.

The first Python invocation referenced a nonexistent test filename and collected
no tests. The corrected initial selection passed128. The broader selection had
210passes/four failures: the actual worker initialization test exposed structural
scope spreading of the full WorkerConfig (including its schema); three existing
retention fixtures lacked the current helper-budget decision field. The producer
now projects exactly three scope fields, and the fixture supplies the real
admission shape without weakening production validation. The corrected affected
selection passes75/75. These earlier results remain history, not claimed passes.

The private audit at
`C:/Users/Darian/.strata/evidence/2026-09-24-worker-health-01` passes14/14.
It runs actual Node24.19.0 instrumentation under a deliberately synthetic CPU/
event-loop workload. Measured interval2.4870375s; largest delay1.315962879s after
a1.3s stall. The late period and terminal partial window are retained, exactly
three windows are emitted, and CPU/memory are positive without double counting.
This is instrumentation evidence, not Minecraft performance evidence.

The audit reopens the externally sealed successful live15 capture read-only:
legacy health is unavailable; requiring the new profile rejects it. Its original
seal stays unchanged. All40 durable authority tables match the preceding
checkpoint before/after; exposure remains$4.849167/$10, including every old hold.
No model request, game process, credential copy or shared-desktop input occurs.
Archive:24files/255589bytes; seal
`5b3ccec1b15c59ec092922847e24ee17151cc7b2f3bcc28c8547765df6c3940c`.
It contains the actual stopped SQLite, report, driver, source pins and authority
digests. The original successful pilot is not copied or modified.

## Next bounded work

Complete the authoritative vanilla server/avatar clock producer and its consumer,
then bind both measurement changes to a fresh controlled runtime/profile and
qualify one changed connected case. Preserve the existing successful pilot and
all failed runs. Reconcile the remaining G0 item4/6 joins against exact M0 scope;
full isolation remains deferred under D14 and later soak/capacity work stays in
its named roadmap milestones.
