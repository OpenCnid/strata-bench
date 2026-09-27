# Retain confirmed repair consumption before complete settlement

M1.1c.3.4 now connects the measured native repair primitive count to durable budget
exposure. Previously the controller could retain a measurement while the budget
still reflected only its smaller original reservation. This change preserves the
observed minimum even if subsequent CAS publication fails. It does not settle the
repair or publish input permission.

## Implemented behavior

`Budgets` retains bounded, immutable `BudgetConsumptionFloor/1` observations for
an existing non-envelope operation. A floor names one observed dimension and its
verified cumulative minimum; absent dimensions are not filled with inferred zero
usage. The operator caller must verify the source and original operation scope.
Repeated notifications are idempotent, changed notifications are refused, and
multiple cumulative observations use their maximum rather than being summed.

Exposure is at least the original unresolved reservation and the confirmed floor.
Nested envelopes continue to count descendants once. Known overruns remain
visible above their reservation; existing uncertainty is never cleared by a
partial observation. A later settlement or reconciliation cannot reduce a known
dimension below confirmed consumption. Unknown dimensions retain their ordinary
unknown/blocking behavior. Envelopes themselves cannot receive own-usage floors,
which would double-count their already attributed child usage. No historical
operation, allowance, exception or hold is converted or renewed.

`NativeRepairResume.measure_prepared` obtains the existing typed private worker
receipt, retains its charged repair primitives in the original operation with the
full source receipt and worker binding, then writes the separate CAS/controller
measurement. The floor commits before the potentially failing CAS operation.
The original budget reservation remains open. If the observed cost exceeds that
repair reservation, the controller refuses further repair work with
`REPAIR_BUDGET_EXHAUSTED` after preserving the evidence and observed amount.
Public actions remain held by the existing worker publication fence.

## Executed evidence

Windows; Python3.12.14, Node24.19.0, Java17.0.20.1+1. No Java/Node production code
or installed Minecraft artifacts changed. Test providers/game bodies remain synthetic.

- `pytest tests/test_consumption_floors.py tests/test_budget_clocks.py tests/test_budget_envelopes.py tests/test_reconfiguration.py tests/test_native_repair_resume.py -q`: **54 passed**.
- Cases cover unchanged unresolved reserve, idempotent/cumulative observations,
  settlement and adjustment refund refusal, actual overrun propagation through an
  open envelope, ancestor exhaustion, preservation of unknown holds, malformed
  observations, and real repair/budget stores with synthetic native replies.
  A simulated CAS failure preserves5 confirmed primitives under the original20
  reservation. A25-primitive result preserves25 and refuses further work against
  that20 reservation; neither case marks the operation settled or releases input.
- `pytest tests/test_controller_restart_jvm.py -q -k publish`, with explicit
  Java/classpath/Node environment: **1 passed, 6 deselected**. The actual Python →
  Node → Windows guardian → JVM replacement/measurement path records18 repair
  primitives in the durable floor, retains the original20 reservation, and preserves
  the exact worker receipt. The game's body and verification remain synthetic;
  this existing transport fixture still supplies a synthetic settlement reference
  for its publication/action portion. It does not certify complete controller
  settlement, the actual Minecraft profile or the full repair/resume workflow.
- Ruff and `git diff --check` pass. The first floor run retained7pass/2fail: two
  synthetic fixtures combined a current-wall resume deadline with an older
  synthetic repair clock. The fixture was corrected to its original deadline;
  production deadlines and gates were not changed. The initial pytest-fixture
  import lint finding was corrected as well.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-27-m1-repair-consumption-floor-01`.

## Remaining accounting and gate work

The measured18 primitives cover only the worker's repair interval. The earlier
opening counter is not evidence that prior gameplay was billed. Complete
settlement still requires continuous nonoverlapping attribution of prior gameplay,
actual body clocks, separately charged model/helper/retry usage, and costs through
publication. Do not add already billed inference costs again, infer zero usage
from an empty source, or turn this lower bound into a complete-consumption receipt.
Original-lease completion, full rollback/repeated repair, the public skill and
native qualification remain unfinished. The retained essential native-health
failure is unresolved. M1 remains `in_progress`; T01/T04/T05/T06/T10/T11 and G1
remain `not_run`. Coverage: F06/F09/F11/F16, N01/N02/N03/N05/N06/N08;
T01/T04/T05 and necessary T12 dependencies. No M2–M7 scope is started.

## Evidence preservation

The private bundle verifies:77files/3,885,383bytes,
SHA-256 `7665a2e6751a42f6bc0a2987a8ad67b1270697090552d3e8cad9a82a9e7f4807`. It retains the actual process fixture/journals, WAL-aware
controller database backup, exact18-primitive proof and20 reservation, source
snapshot, classpath hashes and original failure logs. All40 authority tables/eight
holds and installed client/options remain unchanged. All460 milestone IDs remain;
2,152 local links resolve and final runtime inventory is0. This public pointer
postdates the archived document snapshot.
