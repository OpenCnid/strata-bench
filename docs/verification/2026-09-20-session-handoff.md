# Session checkpoint: documentation and merge verification

September 20, 2026. Operator-only. This report covers the accumulated source
checkpoint in [PR #2](https://github.com/OpenCnid/strata-bench/pull/2) and its
documentation handoff. It does not qualify a production deployment or release
gate. M0 remains in progress, G0 fail, G1–G5 not_run.

## Documentation and scope

SPEC v0.2.59, AGENTS, README, MILESTONES, BUILD_PLAN and the current handoff
now agree on D11: original $10 total estimated experimental usage, no outside
Strata model experiments, explicit runtime migration still required, and no
user-supplied VM or exact OAuth-billing proof prerequisite. The new
[status index](../STATUS.md) separates implemented/synthetic/authentic evidence;
the [admission contract](../operations/validation-admission.md) defines the next
source deliverable and its negative cases. The historical design review points
to the current handoff. Existing dated failures and append-only history remain.

Affected accounting/boundary coverage: M0.1c.1c.2/M0.1c.2b.2,
F03/F04/F07/F11/F16, N01/N02/N04/N06, C06/C12/C20,
partial T01/T04/T06/T07/T12 and G0 items 1/6. No F/N/T/G requirement, M0–M6
deliverable, M7/extension condition or numerical acceptance threshold changed.

## Executed checks

Environment: existing Windows development checkout; Python 3.12.14,
Node 24.19.0, pinned Windows x64 Temurin 17.0.20.1+1, existing locked packages
and exact official FTB Library artifact outside the repository. No new
installation, game launch, live model experiment or desktop input occurred.

| Check | Actual result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | 1054 passed, zero skipped, 124.96 s; two Typer/Click deprecation warnings |
| `npm test --prefix backends/mineflayer` | Build and 178 tests pass, zero skipped, 104.142 s test duration |
| Gradle client/telemetry tests and `writeTestClasspath` | Final build succeeds in 33 s; XML reports 469 client + 14 telemetry tests, zero failures/errors/skips |
| `.venv/Scripts/python.exe -m ruff check src evaluator/src tests tools` | All checks passed |
| Installed `.venv/Scripts/mcbench.exe --help` with complete output capture | Exit 0 |

Python and Node ran with `STRATA_CLIENT_TEST_JAVA` pointing at the pinned JVM,
`STRATA_CLIENT_TEST_CLASSPATH` at the generated client test-classpath file,
the corresponding `STRATA_SETTINGS_TEST_*` values and
`STRATA_GUARD_TEST_PYTHON` pointing at this checkout's Python. Gradle used the
pinned `JAVA_HOME` and external `STRATA_FTB_LIBRARY_JAR`; it verified build inputs.
See [README](../../README.md) for commands. These include process/JVM fixtures
and compiled gameplay package exclusion, not actual game or model qualification.

The first full Java run failed four of 469 client cases and stopped before
telemetry. Three crafting-lane fixtures omitted the new server-confirmed
baseline; the manual-grid fixture still expected the former immediate rejection
of a delayed empty preview. The two test files now provide explicit baseline
feedback, verify no premature fill/take, require the charged fresh preview read
and still reject wrong output. Cancellation, budget exhaustion, deadline and
retained-resource assertions remain. Runtime code and thresholds were unchanged.
The failed log is retained; the final run exercises the entire Java suite.

An initial CLI-help check incorrectly piped output through a truncating consumer,
causing a Windows output-stream error. Complete file capture exits 0; no CLI
source change was needed. Gradle's existing deprecation warning remains.

The September 19 merged baseline had 738 Python, 166 Node and 445 Java tests.
Those counts remain historical and are not substituted for this checkpoint's
checks. No GitHub Actions workflow or clean-machine qualification is supplied.

Raw logs remain outside public source under
`C:/Users/Darian/.strata/evidence/2026-09-20-session-handoff-01`:
`pytest.log`, `node.log`, `gradle.log`, `gradle-corrected.log`, `ruff.log`
and `cli-help.log`. Public reports contain bounded findings only.

## Publication and continuity

The current handoff replaces stale sequential next-action paragraphs with one
restart procedure and explicit exit evidence. Historical detail remains in Git,
the milestone progress log and dated reports. Credentials, game installations,
raw evidence and private evaluator instances remain outside the repository and
gameplay package. The private evaluator's source is public operator source;
gameplay runtime isolation remains separately unqualified.

Publication review inspected all 555 tracked/new candidate files and 1083 local
Markdown links: every local target exists; every F01–F16/N01–N08, M0–M7,
T01–T17 and G0–G5 ledger row remains represented. The existing append-only
progress history is an unchanged prefix. `git diff --check` passes, with known
CRLF-to-LF notices. The only binary is the pinned Gradle wrapper, whose SHA256
matches `java/build-inputs.json`. No sensitive-path candidates or high-confidence
private-key/service-token/JWT patterns were found. This heuristic review is not
a complete secret/security audit. Inventory results are retained privately in
`publication-review.json`; no raw evidence was added to the source checkpoint.

A successful source merge does not waive the actual loopback leak, failed
500-ms shutdown, five effective-file findings, incomplete live accounting,
scorer provenance or other required acceptance cases.
