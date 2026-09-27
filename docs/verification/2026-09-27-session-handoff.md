# September 27 M1/G1 session checkpoint

The user requested updated documentation, a checkpoint PR merged to main and
continuation in a fresh session. This checkpoint preserves the accumulated M1
implementation; it does **not** declare M1/G1 complete. Resume through
[the current handoff](../STATUS_AND_HANDOFF.md), [STATUS](../STATUS.md),
[AGENTS](../../AGENTS.md), [MILESTONES](../../MILESTONES.md) and [SPEC](../../SPEC.md).

## Repository scope

Publication: [PR #9](https://github.com/OpenCnid/strata-bench/pull/9).
Its actual GitHub state and fetched `origin/main` establish whether it has merged.

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

Before and after these checks, all 40 authority tables matched the last sealed audit.
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
| Python default suite, before fixture corrections | 6,237 passed, 340 skipped, two failed, two existing Typer/Click deprecation warnings; 6,241.90 seconds. Both failures are retained below. The broad run was not repeated or relabeled as a clean pass. |
| Focused probe-account correction | Two cases passed in 5.12 seconds after retaining the earlier budget refusal and separately checking decoded-source import refusal. |
| Focused worker-health correction | All 29 worker-health cases passed in 1.83 seconds, including actual Node stall and initialization-failure processes. |
| Node build/default suite | 566 passed, 54 opt-in skips, 0 failures; 620 cases, 10.602 seconds test time. |
| Offline Java client | 679 tests, 0 failures/errors/skips. |
| Offline Java telemetry | 69 tests: 61 passed, 8 skipped, 0 failures/errors. |
| Java build | Offline Gradle successful in 46 seconds; existing pinned official FTB Library input, no game launch. |
| Documentation | 10 documents, 2,280 local links resolve; all 460 milestone IDs retained; both archives match prior text after relative-link relocation. |
| Ruff | `ruff check src evaluator/src tests tools` passed; both corrected test files passed the focused follow-up. |
| Final private-state audit | 40 authority tables, eight telemetry holds and two installed hashes unchanged; zero matching Java/worker/guardian processes. |
| Publication scans | 562 changed paths and 1,526 unpublished-history blobs (272,578,183 bytes) checked; no sensitive runtime filename or provider-token/private-key pattern candidates. These are bounded scans, not a universal secret-proof claim. |

Local logs and the final read-only authority/process audit are retained under
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-session-checkpoint-01`.
The retained audit scripts and logs identify the checks and exact outcomes.

Executed check commands (PowerShell; existing local dependencies):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src;tools;evaluator/src'
.venv/Scripts/python.exe -m pytest -q --tb=short
.venv/Scripts/ruff.exe check src evaluator/src tests tools
# From backends/mineflayer:
npm test
# From the repository root, with the existing pinned FTB Library JAR:
$env:JAVA_HOME='C:/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot'
$env:STRATA_FTB_LIBRARY_JAR='C:/Users/Darian/.strata/clients/e9e-noninput-01/mods/ftb-library-forge-1902.4.1-build.236.jar'
./java/gradlew.bat -p java --offline :forge1192-client:test :forge1192-telemetry:test --no-daemon --console plain
```

These commands record the checkpoint procedure; they are not instructions to
repeat unchanged suites in the fresh session.

## Retained merge-check failures and fixture corrections

The full run found `test_evaluation_account_cannot_be_relabeled_as_campaign_knowledge`
failing during setup. A separate focused run reproduced it in 0.62 seconds. The
fixture changed account creation to evaluation but the newer admission fixture
explicitly posts campaign training records; the real budget guard correctly
refused that mismatch before the intended projection assertion.

The original test now asserts that early `FORBIDDEN` refusal and absence of native
jobs or ledger postings. A separate case supplies a synthetic decoded evaluation
identity to the projection reader and requires `PROBE_IMPORT_FORBIDDEN`, without
changing durable state. Its substitution is explicitly a unit fixture, not proof
of a valid evaluation checkpoint or authentic isolation. Both checks passed;
production code and acceptance criteria are unchanged. Retain the original full
run failure and its focused reproduction rather than relabeling the broad run as
a clean pass. This is F08/F11/N02 and T01/T11 supporting coverage only.

The second failure was `test_actual_worker_initialization_failure_still_closes_measurement`.
Its direct child-IPC fixture omitted `server_kind`, which the lane now uses for
explicit backend selection. It entered the Mineflayer branch, recorded connection
failure and nine nonterminal health windows, then the unchanged ten-second test
timeout killed it. The original SQLite/WAL, lock and script are retained privately.
The fixture now explicitly selects `server_kind="e9e"`, so its intentionally absent
connection file exercises the intended early Forge initialization failure. Child
stderr/exit diagnostics are retained on failure. All 29 worker-health tests passed,
including actual Node processes; production routing and timing limits are unchanged.
This is supporting F09/F11/N03 coverage, not native Minecraft/G1 acceptance.

## Private checkpoint seal

Final evidence: **608 files / 14,788,129 bytes**, SHA-256
`c84a4b04f7a7f497f1c304fd96bf4f20d4e5c4a56f5f78afc5ea14bafa363941`. The private root contains the
full test logs and original failures, passing focused process evidence, final
source/diff snapshot, documentation/publication audits and read-only before/after
state. This public seal pointer and final changed-path count postdate the archived
document snapshot. Subsequent PR/merge metadata is separate from the sealed root;
GitHub and fetched main remain authoritative for actual publication state.

## Fresh-session release discipline

Fetch and inspect the actual checkpoint PR and main before starting a new branch.
A PR title, local branch or prepared handoff does not establish merge completion.
Recheck live processes and durable authority; never infer liveness from files or
reuse an expired job/lease. The user will resume M1 in a fresh session. The goal
must be paused for that handoff rather than marked achieved.
