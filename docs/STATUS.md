# Strata current status

**M1 is in progress. G1 is not complete.** M0 is verified; G0 passes only
its named D14 development feasibility slice. All six complete G1 suites below
remain `not_run`; component checks do not close their acceptance contracts.

This is the September 27 source/documentation checkpoint for continuation in a
fresh session. Read [the handoff](STATUS_AND_HANDOFF.md) and
[checkpoint verification](verification/2026-09-27-session-handoff.md). The
[ledger](../MILESTONES.md) remains the detailed source of progress and decisions.

## What changed since M0

M0 demonstrated model-selected bounded gameplay through Mineflayer, including
turn/walk/helper play. M1 is building the contracts and trust boundaries needed
to make that gameplay a valid benchmark: agent/helper isolation, verified control
repair, complete accounting, protected scoring and matched disposable probes.

There is real partial progress: native boundary/control evidence, a narrow
[authentic Curios repair/restart/restore cycle](verification/2026-09-27-m1-settings-cycle-plan.md),
owned repair/restart/resume services, retained inference closure, immutable
publication evidence and continuous body-tick reservations. The latest three
implementation checkpoints are `b483f4d`, `c1d3055` and `07737f3`.

## Immediate completion target

One connected authentic workflow: **play → diagnose conflict → owned pause →
repair → restart and verify effects → account → commit or verify restoration →
resume play**. Complete wall/disconnected-time allocation, original-lease
controller completion and restored rollback remain missing. The successful
component/process tests use synthetic producers where their reports say so.

The last authentic essential-controls attempt failed with
`PROCESS_NATIVE_HEALTH_TIMEOUT`. Its cause remains unproven; preserve the failure
and diagnose it before a relevant changed trial. No threshold relaxation or
unchanged rerun is selected. See [retained failure](verification/2026-09-27-m1-essential-native.md).

| G1 suite | Required remaining completion |
|---|---|
| T01 contracts | Final-profile references/admission, path boundaries, strict schemas and cross-language coverage. |
| T04 native host | Selected skill, integrated game/settings/probe profile, helper permissions, interruption/resume and every-call accounting. |
| T05 keybindings | Complete public repair/resume/restore workflow, effects/context/modifier/failure cases and authentic extension qualification. |
| T06 isolation | Integrated root/helper filesystem, process, network, credential, tool, cross-agent and probe-disposal boundaries. |
| T10 scoring | Protected admission plus complete positive/negative/alternative-strategy controls and mechanics/overhead parity. |
| T11 probes | Complete initial/transient matching, native admission, clocks, exact cache resets and one-way canary exclusion. |

## Authority and runtime state

D20 authorizes M1 implementation and scripted conformance, including required G1
dependencies. Unrelated M2–M7 work remains outside scope. D17 selects GPT-6 Luna.
D18/D19's $10 allowance is **M0-only**; it does not authorize M1 paid verification.
Known exposure remains $4.887796, retaining the old $0.7554 hold and four full
$1 failed-job envelopes. Eight separate telemetry holds remain unresolved.
Revalidate the durable ledger and process inventory before new execution.

Shared-desktop input remains paused. Installations, raw runs, credentials and
private evaluator data stay outside this repository and every gameplay/helper
context. Separate folders or conversations are not isolation proof.

## Evidence and history

- [Latest continuous body-tick evidence](verification/2026-09-27-m1-body-tick-window.md): 51 affected source checks and one actual JVM/private-pipe case; complete repair accounting remains false.
- [Publication boundary](verification/2026-09-27-m1-publication-receipt.md): immutable controller/worker join, with synthetic game/settlement producers.
- [Inference closure](verification/2026-09-27-m1-resume-inference.md): pending tracked calls prevent native resume; original costs and failure history remain.
- [Opening exact-profile audit](verification/2026-09-24-g1-coverage-audit.md) and [MILESTONES](../MILESTONES.md): full coverage beyond the immediate workflow.
- [Archived status history](archive/2026-09-27-m1-status-history.md): all earlier progress text and evidence pointers, retained without promoting failed or incomplete results.
