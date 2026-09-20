# 2026-09-18 asynchronous worker release evidence

Operator-only. M0.3b.2b.1 advances F06/F09/F16, N02/N05/N08,
C09/C15 and partial T01/T07 under G0/G1/G2. No aggregate gate closes.

The existing public worker previously treated any return from `Backend.stop()`
as confirmation, including an unresolved promise. The backend contract now
permits asynchronous release and requires resolution only after confirmation.
The action remains pending and excludes new mutations while release is pending.
The gateway awaits cancel/stop-all; an idle stop also fences queued future actions.
Concurrent cancellation, stop and close share the same pending release and retain
one terminal receipt. A cancellation during normal completion prevents a success
receipt. Late upstream execution cannot emit another ordinary primitive.

Release is bounded at 250 ms, matching SPEC 8.1. A rejected, hung or synchronously
blocking release produces `unknown`, `INPUT_RELEASE_FAILED`, unconfirmed release
and a fenced/disconnected worker. A late resolution cannot rewrite that receipt.
The bound does not establish external termination of a hung JVM or Node process;
the separate supervisor and authentic timing evidence remain required.

Worker shutdown now drains the asynchronous lane before closing its journal.
Unconfirmed release or failed terminal evidence rejects clean close and causes
the worker's shutdown handler to exit nonzero. A journal-write failure retains
the accepted/executing intent for unknown-on-recovery; no input replay is added.
Capabilities advance to contract minor 5, pin the changed source and expose the
`confirmed-local-release/2` policy. There is no record-schema change.

Executed on Windows 11 / Node 24.19.0 / Python 3.12.14:

- `npm test` from `backends/mineflayer`: TypeScript build and **74 tests passed**,
  zero skipped, 5.271 s test runtime. This was before the final clean-close and
  journal-failure refinements below; it is not a claim of a final full-suite run.
- After those refinements: `npm run build`, then
  `node --test dist/tests/actions.test.js`: **29 passed**, zero skipped, 4.622 s.
  Eight added cases cover delayed confirmation, cancel/stop/close contention,
  rejection privacy, timeout/late completion, blocking stop, journal failure,
  idle/queued stop fencing and actual HTTP response timing/failure.
- `uv run --frozen pytest tests/test_gameplay_package.py -q`: **1 passed**.
- `git diff --check`: passed; existing CRLF normalization notices only.

Tests use synthetic backends, actual SQLite, HTTP and scoped CLI subprocesses.
They do not establish Minecraft/Forge release, mechanics or isolation. No Java
code/JAR changed; no desktop input, game launch, profile change or inference ran.
Private command/result metadata and final source hashes are in
`%USERPROFILE%/.strata/evidence/2026-09-18-worker-release-01/verification.json`.

M0.3b.2b stays in progress. Next is .2b.2: private native transport, asynchronous
observations and delivery receipts, full batch/actor/body/capability binding,
explicit backend selection and native/public receipt reconciliation. The current
public worker still selects Mineflayer only. Aggregate native charges/clocks,
controller grants/repair holds, external hung-client termination, remaining native
motors and authentic exact-pack tests remain separate unfinished children.
