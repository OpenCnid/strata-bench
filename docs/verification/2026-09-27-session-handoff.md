# September 27 M1/G1 session checkpoint

The user requested updated documentation, a checkpoint PR merged to main and
continuation in a fresh session. This checkpoint preserves the accumulated M1
implementation; it does **not** declare M1/G1 complete. Resume through
[the current handoff](../STATUS_AND_HANDOFF.md), [STATUS](../STATUS.md),
[AGENTS](../../AGENTS.md), [MILESTONES](../../MILESTONES.md) and [SPEC](../../SPEC.md).

## Repository scope

At preparation, `origin/main` was PR #8's merge commit
`215c4e0d01f0602c91504ad631dc2343ffc9f354`; GitHub independently reported PR #8
merged. `codex/m1-g1-isolation` contained 141 subsequent implementation commits,
ending at `07737f3`, across 556 changed files before this documentation refresh.
The checkpoint PR carries that implementation plus these docs. A documentation
commit alone on the old main would omit the code needed by the next session.
Preserve commit history so dated evidence/source references remain resolvable.

The current status and handoff are now concise. Their complete prior contents
remain in [status history](../archive/2026-09-27-m1-status-history.md) and
[handoff history](../archive/2026-09-27-m1-handoff-history.md), with relative links
adjusted for their archive location. MILESTONES retains all original IDs,
requirements, gates, failures and append-only progress. README and BUILD_PLAN
no longer imply that M1 has not begun. No acceptance contract was reduced.

## Acceptance and next work

M0 is verified; G0 passes only its named D14 development feasibility slice.
M1 is `in_progress`. G1 and complete T01/T04/T05/T06/T10/T11 remain `not_run`.
There is no qualified complete settings/runtime/isolation/scorer/probe profile.
The opening [G1 audit](2026-09-24-g1-coverage-audit.md) remains the baseline;
the ledger and current handoff record subsequent exact-profile evidence.

M1.1c.3.4 is the immediate integration work: complete wall/disconnected-time
allocation and consumption settlement, original-lease controller completion,
verified restored rollback and the authentic play/repair/restart/resume workflow.
Frozen inference closure, immutable publication retrieval and continuous
body-tick reservations are implemented with their stated source/process scopes.
They explicitly do not certify full accounting or grant campaign permission.

The narrow Curios cycle passed on its own profile. The later essential-controls
native04 attempt remains failed with `PROCESS_NATIVE_HEALTH_TIMEOUT`; its cause
is unproven. Preserve its six charged primitives, incomplete first effect,
normal-stop failure and successful bounded tree termination as separate facts.
No unchanged retry or relaxed timing policy is authorized by this handoff.
Final native host/skill, isolation, scorer and probe gates remain required after
the immediate repair work. Unrelated M2–M7 work remains outside scope.

## Latest sealed implementation evidence

| Checkpoint | Scope | Private seal SHA-256 |
|---|---|---|
| `b483f4d` | [Inference-gated native resume](2026-09-27-m1-resume-inference.md); 285 files / 9,591,768 bytes | `295aaaede79d6c26db9ba6bab48ce4ae1b51e6bf18bba6511216a309e31f7376` |
| `c1d3055` | [Publication boundary retrieval](2026-09-27-m1-publication-receipt.md); 151 files / 6,305,414 bytes | `96e14ce9f863bd9e6f4796685e03cc16c72e177710b76a1deda02d20a2c179fe` |
| `07737f3` | [Continuous body-tick window](2026-09-27-m1-body-tick-window.md); 58 files / 4,293,003 bytes | `61717c2c1283d35f92df46dd90635822ca0e47acf120672b776952939d849e85` |

The seals retain failures as well as passing evidence. The previous focused
body-tick check passed 51 source cases and one actual JVM/private-pipe case.
That process case uses synthetic game/setup/roster/token qualification and does
not establish pre-request repair coverage. It is not Minecraft/G1 acceptance.

## Authority and runtime custody

D20 remains the M1/G1 implementation/scripted-conformance authority. D17 selects
`gpt-6-luna`. D18/D19's original $10 allowance remains M0-only; this checkpoint
does not authorize M1 paid inference, another allowance, account changes or
new experiments. The authority database is private at
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`.

Before these checks, all 40 authority tables matched the last sealed audit.
Exposure was 4,887,796 microUSD, preserving the old 755,400 hold and four full
1,000,000 failed-job envelopes without double charging settled children. All
consumed pilots/decisions remain consumed. Eight separate 256-MiB telemetry
reservations remain `RESERVED` with unknown actual bytes. The handoff lists
their exact private scopes and installed-file hashes. No private data is copied
into gameplay/helper contexts or published in this PR.

## Checkpoint verification

These are merge checks for the accumulated source checkpoint, not G1 outcomes.
No paid inference or Minecraft run is selected. Optional integration skips
remain unrun; prior exact-profile evidence is not replaced with a broad claim.

| Check | Result |
|---|---|
| Python default suite | Running; final result will be recorded before merge. |
| Node build/default suite | 566 passed, 54 opt-in skips, 0 failures; 620 cases, 10.602 seconds test time. |
| Offline Java client | 679 tests, 0 failures/errors/skips. |
| Offline Java telemetry | 69 tests: 61 passed, 8 skipped, 0 failures/errors. |
| Java build | Offline Gradle successful in 46 seconds; existing pinned official FTB Library input, no game launch. |
| Ruff | `ruff check src evaluator/src tests tools` passed. |
| Initial publication scan | 556 implementation-diff files checked; no sensitive runtime filenames or provider-token/private-key pattern candidates. This is a bounded scan, not a universal secret-proof claim. |

Local logs and the final read-only authority/process audit are retained under
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-session-checkpoint-01`.
Final documentation/link/ID checks and publication/merge state follow below.

## Fresh-session release discipline

Fetch and inspect the actual checkpoint PR and main before starting a new branch.
A PR title, local branch or prepared handoff does not establish merge completion.
Recheck live processes and durable authority; never infer liveness from files or
reuse an expired job/lease. The user will resume M1 in a fresh session. The goal
must be paused for that handoff rather than marked achieved.
