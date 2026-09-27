# Owned repair clock consumption — September 27

M1.1c.3.4 remains `in_progress`; no aggregate G1 suite closes. The preceding
publication-boundary turn was progress: committed and verified at `20f863e`.
This change connects the existing causal clock evidence to retained budget
consumption. It does not complete the public gameplay repair workflow.

[RepairClockEvidence](../../evaluator/src/strata_evaluator/repair_clocks.py) now
revalidates two stored causal marks against the held server source and original
repair/body/clock/worker scope. It uses the repaired avatar's actual callback
delta, not a sum of sibling usage, health-roster counts or inferred 20Hz time.
Missing UUID entries in a validated cumulative callback sample mean no callbacks
yet for that UUID; a missing sample never supplies a zero origin.

The first accounting opening is immutable. A later closure extends the same
cumulative interval; duplicate reads charge once and overlapping extensions take
the cumulative maximum. Changed origins, reversed intervals, unowned/terminal
sources, changed receipts and noncausal marks are refused. The original reservation
stays held, including unknown dimensions. The witness and tick floor commit in
one transaction; an overrun remains recorded before further work is refused.
Storage failure cannot advance the accounting cursor, and settlement cannot
refund those observed ticks. All complete-accounting, settlement and input-
permission claims remain false.

Executed on Windows, Python 3.12.14 and Java 17.0.20.1+1:

- Nine distinct signed-fixture/controller cases pass in
  [test_repair_clock_consumption.py](../../tests/test_repair_clock_consumption.py):
  delta, reservation preservation, idempotency, no-refund settlement, overrun,
  cumulative extension/origin/reversal, storage failure and five evidence/source
  negatives. The normal case observes one tick under a ten-tick reservation;
  extension observes three cumulatively, not four.
- Selected actual `test_clock_barriers.py -k 'actual_jvm and True'`: one pass,
  nine deselected. The real Windows Job, Java production clock/spool, named pipe,
  authenticated telemetry and controller/budget databases join two actual Java
  avatar callbacks to two retained ticks. Zero reserved ticks produces
  `REPAIR_BUDGET_EXHAUSTED` after retaining the evidence and exposure. Input
  authority remains absent. Normal JVM exit and broker shutdown complete.
- Offline `:forge1192-telemetry:compileTestJava` and changed-file Ruff checks pass.
  Only the Java test fixture gains an optional avatar UUID sample command;
  production Java and installed game files are unchanged.

The actual pipe test still uses synthetic game callbacks/setup/native body and
explicitly unqualified token-peer substitution. It does not prove Minecraft
integration, OS isolation, authoritative campaign active time or complete repair
coverage. These limitations are preserved in its private proof.

The initial seven fixture cases failed before the new method was reached: their
synthetic ACK cursor equaled the health event being generated, which the existing
clock validator correctly rejected. The fixture now preserves causal receipt
ordering; no validator, deadline or acceptance threshold was relaxed. Failures
are retained with the subsequent focused results. No game or model call ran.

Coverage remains M1.1c.3.4, F06/F09/F11/F16, N01/N02/N03/N04/N08, the
T01/T04/T05/T06 G1 dependency and its necessary measured-consumption support.
Private clock/source material stays in evaluator/controller storage. All historical
profile identities, failures, consumed decisions and reservations remain retained.

Next: bind continuous prior-gameplay and complete repair interval allocation,
model/helper consumption and publication tail before settling and completing the
original controller lease; qualify the authentic play/repair/restart/restore/resume
workflow. Native-health failure and final T01/T04/T05/T06/T10/T11 gaps remain.

Private evidence sealed:62 files/4,044,298 bytes,
SHA-256 `a87878072c57d8cfd28306ee0119437b1bca7c2e17009956a65b1c8602308329`.
All40 authority tables, eight telemetry holds and installed client/options hashes
are unchanged; final matching runtime process count0. All460 milestone IDs and
2,166 local links were checked. This pointer postdates the archived snapshot.
