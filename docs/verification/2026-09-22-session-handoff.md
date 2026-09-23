# September 22 M0 checkpoint and session handoff

Operator-only. The user requested an implementation merge followed by a separate
documentation merge, then a fresh session focused on completing M0/G0.
**M0 is incomplete; G0 is fail; G1–G5 are not_run.** No further game trial runs
after the requested stopping point.

## Git checkpoint

[Implementation PR #5](https://github.com/OpenCnid/strata-bench/pull/5) merged
source `ca5e6739de6d4bb9c594d861f74eb71e3df1852b` into main at
`303b43fd2477a44179313915cce4469116cbea16`, September 23, 02:24:04 UTC
(September 22 locally). Fetched origin/main agrees. The source branch retains
31 commits after the PR #3/#4 checkpoint
`c2161a6e79cea0c668ab993df149ab1ed5af119b`.

The separate documentation branch starts from that fetched implementation
merge. Fetch origin/main after the documentation merge before continuing.
No hosted status checks were configured on PR #5. Local verification below
is not a hosted CI claim.

## What this implementation checkpoint delivers

- Reusable native/game receipt reconstruction and explicit two-epoch recovery
  verification, preserving old native/CAS/ledger/worker history and cumulative
  usage. The successful sealed pair reconciles 13 scripted calls, 182 fixture
  units and two real primitives.
- Actual official vanilla intake, installed-role/runtime provenance, sealed
  PackLock and pinned worker/server launch, followed by bounded native execution
  and saved game/root-artifact recovery with fresh scope and stale-access denial.
- Continued private setup/history and source/custody work, with all scorer,
  isolation and full provenance limitations retained.
- D13's explicitly approved 1,000-ms Java tree policy, with a passing
  568.994-ms sample. All previous 500-ms failures remain failed.
- Operator-owned normal worker drain and server stop/lifecycle evidence, plus
  explicit baseline import after a worker-only profile change. This last
  connected behavior remains implemented_unverified for authentic execution.

These claims have different scopes. Real vanilla gameplay used scripted model
replies. Neither that gameplay nor source checks qualify live-model delivery,
complete scorer/isolation, authoritative clocks/save custody or G0.

## Latest attempt and exact next action

The controlled runtime and successor vanilla profile are prepared and sealed.
Attempt `2026-09-22-m0-normal-stop-01` failed before Java/avatar/native startup:
the persistence constructor rejected the imported-baseline scope with
`VANILLA_TEMPLATE_CHANGED`; the outer result is `SERVER_EARLY_EXIT`.
Missing server capture also produced a secondary `TypeError`.

All 11 owned processes are terminal, none forced-terminated; outer exit 1 after
45.578 seconds. The complete prepared instance and all 34 original authority
tables compare unchanged. The failed archive retains the exact executed source,
plans, traces and result; it is not a successful game run or recovery parent.

The source fix now shares scope selection between launch, capture and verifier.
Its regression exercises the imported-world capture constructor and binds the
new snapshot to the new PackLock while retaining the source snapshot identity.
Missing capture now fails with `M0_CAPTURE_INCOMPLETE`. The final focused
selection passes 91 cases. **No post-fix authentic run is claimed.**

Next revalidate the prepared profile/instance, then run one changed headless
native/vanilla case with scripted replies, fresh output/worker scope and owned
cleanup. Prove native closure → worker drain → normal server stop/capture →
independent reconstruction. The instance was unused by any game process and
verified unchanged; it can be revalidated without rebuilding the installation.
Do not rerun occupied case-01 output or one-use scripts.

After that bounded result, continue the remaining connected private scorer/setup,
enforced isolation, authoritative clocks/save/recovery and E9E profile requirements.
Use the [six-item G0 checklist](../../MILESTONES.md#m0-closure-checklist--spec-161);
do not expand unrelated M1–M7 work or restart completed verifier/accounting matrices.

## Executed merge verification

Windows; Python 3.12.14, Node 24.19.0, pinned Temurin 17.0.20.1+1 JDK.
The existing exact FTB Library artifact and cached locked build inputs remain
outside source. No clean-machine build or new installation is claimed.

| Check | Actual result |
|---|---|
| Full Python, `python -m pytest -q` | **2,822 passed, 3 skipped**, zero failures, 760.72 s; two existing Typer/Click warnings |
| Skipped-case inspection | Three `test_path_check_rejects_native_links_including_missing_descendants` variants skip because native symbolic-link creation privilege is unavailable; no pass or privilege change is claimed |
| Full Node, `npm test --prefix backends/mineflayer` | **196 passed**, zero failures/skips, 96.863 s; Java/process fixtures enabled |
| Java client and telemetry tests | **469 + 31 = 500 passed**, zero failures/errors/skips; offline Gradle build succeeds in 44 s, 8 tasks executed/3 up-to-date |
| Fresh JVM fixture classpaths | Both writeTestClasspath tasks succeed |
| Ruff and CLI load | `ruff check src evaluator/src tests tools` and `mcbench --help` exit 0 |
| Whitespace/publication | `git diff --check` passes; 820 tracked/new files, 1,853 local Markdown links, no broken links or credential/private-artifact flags |
| Ledger conservation | Previous append-only progress log and all M1–M7 rows preserved |

Java verification ran first, then Python, then Node, avoiding overlapping
timing-sensitive suites. JVM/native Windows fixtures were explicitly enabled;
the three symlink skips were separately identified. The only tracked binary is
the pinned Gradle wrapper. No Minecraft, model request or shared-desktop input
was started by these checks.

Private logs and the exact command script are in
`C:/Users/Darian/.strata/evidence/2026-09-22-session-checkpoint-01`.
The full suite checks source `ca5e673`; documentation follow-up does not
change that executable source or the acceptance thresholds.

The separate documentation audit covers eight changed Markdown files and
1,778 local links across 821 tracked/new files, with no broken links or
credential flags in the changed documents. Every numbered SPEC section,
the complete coverage/gate tables, all M1–M7 rows and the old append-only log
are unchanged. Whitespace validation passes. The broad source suites were
not repeated for this documentation-only follow-up.

## Durable authority and retained private inputs

Authority:
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`, account
`authorization:validation-2026-09-18`, authority digest
`7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`.

Original allowance: **$10 total API-equivalent**. Two actual requests retain
**$0.7554 unresolved + $0.001458 settled = $0.756858**. Uncertainty remains;
D12 is consumed. General model admission remains blocked. No refund, replay,
rearming or new allowance is authorized. Since the controlled-profile publication,
all 34 authority tables compare unchanged through merge verification. Publication
itself added only new objects/outbox/provisioning records; every old row was retained.

Private artifact names below are relative to
`C:/Users/Darian/.strata/evidence/`; never mount them into gameplay.

| Artifact | Exact pin / disposition |
|---|---|
| `2026-09-22-worker-stop-launch-01` | 20 files / 2,157,744 bytes; seal `4b237bf00c9fc1a71b18ada6e1024580ca3daa800b2a187eabc69aa4a88db406`; new profile publication and baseline preparation |
| `2026-09-22-m0-normal-stop-01` | 247 files / 30,923,063 bytes; seal `c393439b6aa9fa0b6c951ee1d3d488fbe4f713767989127ff3fce37df8bfdeae`; failed pre-Java attempt, immutable |
| `2026-09-22-worker-stop-runtime-01` | Seal `2974d34f38c85513ca060e5155461138fe0566681d5f355124aeae5bdf1b18d0`; actual import only, not game stop |
| `2026-09-22-m0-restored-baseline-01` | Successful original sealed native run; seal `2a584f1daf02c83053176410f51ca275af25dd4a97addbcff132ef6679a642bc` |
| `2026-09-22-m0-sealed-recovery-02` | Successful bounded continuation; seal `2be1d6eecc05d8c6eccc03a7c951f5fbf803385e1fa05b7304155972c67400e0` |
| `2026-09-22-m0-sealed-recovery-01` | Failed first recovery and nonempty WAL retained; never read its main DB as frozen or use it as a parent |
| `2026-09-22-m0-sealed-worker-01/run/server/stopped-instance` | Original no-avatar baseline; snapshot `fe6cdbcafaf3bcecce4a0ef060dfc084041aae1dd4526d9430480f47fbcaf379`; original fresh-start 97.408/80-second failure remains |

Prepared runtime:
`C:/Users/Darian/.strata/runtime/vanilla1192-worker-stop-01/runtime.manifest.json`,
SHA-256 `dce7f4f2ba11f42f3387d60e6cd1449409f7323aa895ad060bbc4a4e86c28710`.
It contains 11,723 files / 654,081,296 bytes. Its preparation/import is complete;
do not rerun its one-use script or rebuild unchanged bytes.

Prepared template/instance:
`C:/Users/Darian/.strata/runtime/vanilla1192-worker-stop-launch-01/template`
and sibling `instance`. Binding:
`C:/Users/Darian/.strata/evidence/2026-09-22-worker-stop-launch-01/restored-binding.json`.
New request `vanilla-1192-worker-stop-20260922`, PackLock
`cas:sha256:12e7d7542c58bec5852f2dd82923482fe448ea4481d42e692c0983bc2a5d7cbd`.
Original PackLock
`cas:sha256:d85894fca48ae58a95679d713e6d3c30a4cd154ed8a98a00d744ff07afda80a2`
and old campaigns are unchanged.

The source worktree is
`C:/Users/Darian/.codex/worktrees/978a/minecraft-benchmark`; the main checkout
is `C:/Users/Darian/Desktop/codex/minecraft-benchmark`. Preserve both and all
earlier worktrees. Recheck live process/accounting/Git state in the next session.

Retain the five effective-file failures, Mineflayer/E9E incompatibility, D12
native-delivery failure, every 500-ms sample, E9E history/startup failures,
scorer/setup/ingress gaps and all later roadmap requirements. See the
[normal-stop report](2026-09-22-native-normal-stop.md),
[recovery report](2026-09-22-native-recovery-verifier.md),
[D13 report](2026-09-21-d13-shutdown.md), and
[validation admission contract](../operations/validation-admission.md).
