# M0 implementation handoff

Operator-only. Updated September 22, 2026. This is an implementation continuation,
not a new design exercise. **M0 is incomplete; G0 fails; G1–G5 are not run.**
The current task is M0/G0 only. Preserve M1–M7 and their activation conditions.

[Implementation PR #5](https://github.com/OpenCnid/strata-bench/pull/5) is merged at
`303b43fd2477a44179313915cce4469116cbea16`; documentation PR #6 is also merged. The active implementation branch started
from fetched merged main `f3b009e`.

Start by reading [AGENTS.md](../AGENTS.md), [SPEC.md](../SPEC.md), the current
position and six-item closure checklist in [MILESTONES.md](../MILESTONES.md),
[STATUS.md](STATUS.md), this handoff, the [validation admission contract](operations/validation-admission.md)
and the [September 22 checkpoint report](verification/2026-09-22-session-handoff.md). Fetch origin, confirm the
actual merged main, inspect the current worktree and original accounting, and
start a fresh branch from main. Preserve all old branches, changes and private
evidence. Do not launch Minecraft merely to inspect the checkpoint.

## Delivered normal completion

M0.1d.8c and .8c.1 now pass their bounded scripted-provider evidence. Case04
uses a fresh restoration of the original unplayed world and the same sealed
worker/template/PackLock. All 29 native checks and independent reconciliation
pass: seven requests/98 fixture units/one primitive, normal 36.2536-ms worker
drain, 1,828-ms server stop-to-exit, capture and all 46 owned processes terminal.
Original accounting/template remain unchanged. Exact seals/report digest are
in [the current report](verification/2026-09-22-native-companions.md).

Retain attempts 01–03: scope rejection, removed pinned executable, then missing
adjacent tool host after Java/avatar startup. `NativeBootstrap/2` now binds and
holds all three exact-version companion binaries and rejects missing dependencies
before game launch. Native-only scripted checks pass 55/55 (11 requests); focused
source checks pass 117/3 existing privilege skips. Historical version-1 evidence
gets no retroactive qualification. No live inference occurred.

Do not rerun this successful bounded case, reuse failed instances as unplayed
baselines, rebuild unchanged software, or expand stop work. Observed lifecycle
intervals do not establish authoritative ticks/active time, clean-save custody or
a complete checkpoint. The next implementation work is the remaining G0 work below.

## Immediate remaining G0 requirements

1. Connect a short private server-verified milestone to the existing game/native
   evidence. Finish setup/team/ingress provenance and positive/negative scorer
   controls; prove that no criteria or scores reach gameplay. Existing craft
   witnesses and signed points are partial evidence, not an admissible score.
2. Finish the smallest enforceable gameplay/helper filesystem, process, network
   and tool boundary on the available hardware. A new conversation, broker tool
   list or separate desktop alone does not qualify isolation.
3. Join authoritative time/ticks, clean-save/custody and the remaining applicable
   cancellation/reconnect/recovery cases to the same qualified profile. Preserve
   all consumed costs and old outcomes. Use the existing native/game verifier and
   two-epoch reconstruction rather than rebuilding them.
4. Complete the exact E9E profile/provenance and separately identified Forge
   fallback qualification. Mineflayer/E9E remains incompatible. Finally audit all
   six SPEC 16.1 items together; a vanilla-only or local-test pass cannot close G0.

General model admission is blocked by the original hold. Continue independent
M0 implementation and authorized scripted-provider game integration. Do not
replay an ambiguous request, reuse D12, replace the allowance, assume a refund,
or reclassify synthetic replies as authentic model qualification.

## Work that is already available

- M0.1d.1/.2: reusable native/game evidence reconstruction and exact request/
  primitive-charge attribution.
- M0.1d.7/.8a/.8b: pinned/sealed vanilla execution and bounded game/agent recovery
  with retained player state/root notes, fresh epoch, stale-access rejection,
  preserved old history and cumulative costs. The successful sealed two-epoch
  pair reconciles 13 scripted calls, 182 fixture units and two primitives.
- Original vanilla acquisition, installed roles, private worker runtime and
  immutable PackLock; the controlled-worker successor is now also sealed.
- D13: the authorized 1,000-ms Java tree policy has a passing 568.994-ms sample.
  Do not resume 500-ms optimization. Other fault/profile requirements remain.

## Constraints and state

The original $10 total API-equivalent allowance remains authoritative at
C:/Users/Darian/.strata/operator/provisioning/controller.sqlite. It retains
$0.7554 unresolved plus $0.001458 settled ($0.756858 combined), two actual
requests, uncertainty and consumed D12. Read live SQLite with WAL-aware
read-only access; historical immutable reads require frozen-WAL verification.
There is no new allowance or general model admission.

Shared-desktop input stays paused. Keep credentials, game installations, raw
evidence and private evaluator material outside public source and gameplay
access. D05 sign-in, Java entitlement and EULA approval already exist; do not
ask for them again. Later N=2 identity/capacity work is outside this M0 task.

Preserve every failed 500-ms sample; the five effective-file failures; the
Mineflayer/E9E incompatibility; D12 native delivery failure; the 97.408/80-second
fresh-start failure; both E9E history/startup failures; the first sealed recovery
failure and its nonempty WAL; and the latest pre-Java baseline failure.
The milestone ledger and dated reports retain the detailed history.

## Source and private inputs

- Normal stop: [native/game runner](../tools/m0_native_game.py),
  [server owner](../tools/development_server.py),
  [worker stop policy](../src/mcbench/worker_stop.py),
  [worker control](../backends/mineflayer/src/worker_control.ts) and
  [stop verification](../evaluator/src/strata_evaluator/native_game_stop.py).
- Baseline binding/capture: [baseline import](../src/mcbench/pack_baseline.py),
  [launch](../src/mcbench/pack_launch.py), [restore](../src/mcbench/pack_restore.py),
  [worker profile](../src/mcbench/pack_worker.py) and
  [persistence](../src/mcbench/vanilla_persistence.py).
- Reconstruction: [native/game evidence](../evaluator/src/strata_evaluator/native_game_evidence.py)
  and [continuation](../evaluator/src/strata_evaluator/native_game_continuation.py).
  These are operator/evaluator code, never gameplay tools.

Private roots are under `C:/Users/Darian/.strata`. The
[checkpoint report](verification/2026-09-22-session-handoff.md#durable-authority-and-retained-private-inputs)
records exact launch, baseline, audit, recovery and failed-case references; use those
pins and verify durable state rather than recreating installations from memory.

Keep MILESTONES.md and the current handoff synchronized with code. Report
implementation, synthetic verification and authentic integration separately.
Each work item must advance a named remaining G0 outcome. Avoid unchanged test
matrices, more generic scaffolding and unrelated M1–M7 work. Ask only for inputs
that remain genuinely missing after checking the existing authorization/state.
