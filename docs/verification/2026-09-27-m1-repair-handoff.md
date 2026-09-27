# Controller-to-worker repair handoff

M1.1c.3.2 now connects the controller's existing repair state machine to the
running Forge worker's private pause endpoint. The actual Python controller,
Node worker, Windows guardian and Java fixture demonstrate cancellation of an
active action, evidence-backed entry into RECONFIGURING, lost-reply status
reconciliation and expiry recovery. The game body and controller settings
qualification in these tests are explicitly synthetic. No authentic Minecraft,
native settings mutation, full repair/resume workflow or G1 suite is newly passed.

## Contract and durable behavior

`src/mcbench/worker_repair.py` strictly parses the private WorkerRepairGrant/1,
Plan/1, State/1 and Response/1 contracts. Only the exact loopback endpoint is
allowed. Requests/replies are bounded to4KiB, HTTP does not redirect, deadlines
are bounded, scope and complete returned plan must match, and credentials are
excluded from evidence and exception text. Pause sends one POST; malformed,
missing or refused delivery is treated conservatively as uncertain. The caller
may query status, never blindly repeat a pause dispatch.

`Reconfigurations.quiesce_worker` persists the grant digest and exact plan before
dispatch. The existing controller one-second quiescence limit includes transport,
CAS publication and entry; retries do not restart it. The response must establish
paused/released input. A private source witness and RepairStop then enter the
existing controller state machine. The worker grant itself is never placed in
the witness. A different grant, changed scope or a replacement manual stop proof
cannot take over the recorded handoff.

Uncertainty before entry retains QUIESCING and the reserved budget. A later call
queries status, even after witness-storage failure. A known failed worker or loss
of an already confirmed pause moves the controller to RECOVERY_REQUIRED, blocking
settings application. Expiry retains both controller and worker holds. The other
avatar remains READY. Native cleanup continues through the worker's existing
primitive accounting; the controller reservation remains held for later full
repair reconciliation and is not silently settled from a partial snapshot.

This is a stop-evidence producer, not final runtime admission. Its control-profile
identity comes from the controller's existing plan. Final native settings/profile
mapping, transaction ownership, actual effect checks, client restart/rejoin and
explicit resume/rollback recovery remain required. No generic metadata assertion
is promoted to physical key qualification or final isolation evidence.

## Executed verification and retained failures

Exact local profile: Windows; Node24.19.0; Java17.0.20.101; pinned existing
GameBridgeFixture, ForgeDevelopmentWorker/3 and Python guardian. JVM input/body
and controller campaign/settings are synthetic; real production transport,
worker journal, controller/CAS, cancellation and process supervision are used.

- Initial controller/HTTP and existing reconfiguration checks:44 pass.
- The first two JVM tests stopped at the fixture driver's incorrect assumption
  that CLI exit2 was always failure. This CLI returns2 for the accepted asynchronous
  action. Both original failures and their fixture directories are retained.
  The corrected driver still requires an actual accepted receipt, a live native
  action before handoff, cancellation and confirmed release afterward.
- Both corrected Python→Node→JVM runs pass. One injects loss of controller delivery
  after the actual worker reply; the next operation is status, with one durable
  worker hold and no repeated pause. The native process terminates at expiry.
- Review reproduced Pydantic accepting1/0 for Literal boolean flags. Exact raw
  booleans are now required, with a retained diagnostic and negative HTTP case.
- Affected controller/settings checks returned60 passes and one stale test
  expectation after known worker failure was strengthened to RECOVERY_REQUIRED.
  The original assertion failure is retained; the test now requires that stricter
  recovery state. The final targeted run passes all17 HTTP/controller/JVM cases,
  with no skips. These runs establish63 distinct passing cases across the changed
  path and existing reconfiguration/controls coverage, not a full T05 pass.
- Ruff passes. Initial fixture-import lint findings and the initial missing
  evidence-directory Create argument are retained. No permissions were relaxed.

Commands: `python -m pytest -q tests/test_worker_repair.py tests/test_reconfiguration.py tests/test_controls.py`;
then final changed/new cases with pinned JVM/Node environment:
`python -m pytest -q tests/test_worker_repair.py tests/test_worker_repair_jvm.py`.
The final test fixtures, logs and source snapshots are private under
`2026-09-27-m1-repair-handoff-01`. The unchanged Node regression suite was not rerun.

## Next acceptance deliverable

Bind native settings transaction/effect admission to this exact worker-owned
plan and deadline. Complete qualified adapter/commit, restart/rejoin and explicit
resume or rollback recovery, then the authentic charged gameplay repair workflow
and remaining T05 matrix. Preserve M1.1b.1's separate named Minecraft cycle,
all failures, original profile identities and the full G1 scope. M1 remains
in_progress; T01/T04/T05/T06/T10/T11 and G1 remain not_run at aggregate level.

D20 implementation authority persists. No game/model run or inference allowance
was added; D18/D19 remain M0-only. Historical telemetry holds, consumed decisions
and accounting exposure remain subject to the final read-only audit below.

Final audit: all40 authority tables unchanged at4,887,796microUSD; all five
historical capacity holds unchanged in their current WAL-aware databases; no
Java process remains. All459 milestone IDs are preserved and1,619 local ledger
links resolve. Private evidence is sealed183files/6,961,896bytes at
`d0e178efa8edb60cccc0c4855d065891689c42e5928e18c82fcfd7242b3360c8`.
The archive includes original failed JVM fixtures, final test fixtures, logs and
source/document snapshots preceding this seal pointer. No aggregate gate result
or inference authority changes.
