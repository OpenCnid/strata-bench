# Strata

**A Minecraft benchmark for long-horizon agent adaptation.**

Strata studies whether experience retained by a fixed agent improves later play,
separately from better equipment, changed worlds or additional inference. The
target system uses [Dovetail](https://github.com/OpenCnid/dovetail-codex) in the
native Codex loop, with typed `mcgame` commands to a persistent game worker.
Mineflayer is the first backend; the separately identified Forge extension is
the authorized development fallback for exact E9E compatibility work.

**Status: implementation in progress. M0 is incomplete and G0 fails.** The active
work is M0/G0 only; the complete later roadmap remains in SPEC and MILESTONES.
Narrow authentic vanilla and separate Forge checks have passed. Exact E9E's
Mineflayer handshake failed, and fallback evidence remains a separate backend
qualification. G1–G5 are not_run.

The implemented development harness gives GPT-6 Luna filtered observations and
typed game tools. The model chooses its targets and actions; Mineflayer executes
the bounded motor commands and returns observations and receipts. A separate
helper can review public evidence. Authentic pilots have turned and walked with
joined model costs and saved-player evidence. Test scripts prepare fixtures and
check outcomes; scripted-provider tests are labeled separately. See the
[latest reconciled pilot evidence](docs/verification/2026-09-24-action-refusal-evidence.md).
Live15 passed actual turn/walk/helper play. Live18 later verified a refused
sequence and model-corrected turn with complete evidence, while retaining its
failed two-action goal. Next assemble exact G0 profiles and child dispositions.
This is a short integration slice, not autonomous expert-pack completion.
[September 24 checkpoint](docs/verification/2026-09-24-session-handoff.md).

- [Current review and next-session handoff](docs/STATUS_AND_HANDOFF.md)
- [Current status](docs/STATUS.md): M0 closure gaps and evidence index
- [Specification](SPEC.md): complete target contract and acceptance gates
- [Milestone ledger](MILESTONES.md): coverage, decisions, failures and evidence
- [Project instructions](AGENTS.md): implementation and verification process
- [Build plan](BUILD_PLAN.md) and [research](research/): supporting design evidence

The [native/game implementation](docs/verification/2026-09-22-native-recovery-verifier.md)
connects actual Dovetail/root/helper/broker execution to a pinned vanilla worker.
Bounded sealed recovery restores player state and root notes, rejects stale
access and preserves usage; reusable verification reconstructs both epochs.
Model replies are scripted. The [changed normal-stop case](docs/verification/2026-09-22-native-companions.md)
now passes native completion, worker drain, server stop/capture and independent
evidence reconstruction. All prior failures remain; full G0 qualification is open.

## What is implemented

| Component | Current scope | Qualification still required |
|---|---|---|
| Python operator services | Strict records, storage/journals, grants, controller state, budgets/clocks, checkpoints, artifacts and communication | Integrated production lifecycle, isolation and complete restoration |
| TypeScript worker and CLI | Filtered observations, scoped actions, durable action lane, cancellation, fencing and process supervision | Complete vanilla/modded mechanics and reliability |
| Forge 1.19.2 extension | Structured state/actions, settings transactions, quest/JEI/Thermal adapters, private frame/reference diagnostics | Full menu/mechanics/input parity, T05 keybindings and reliable shutdown |
| Native Codex adapter | Pinned CLI/Dovetail, actual GPT-6 Luna gameplay, delivered helper reply and accounting; scripted recovery separately retained | Full helper/isolation and authentic joint recovery qualification |
| Inference accounting | Actual root/helper receipts, nested envelopes, deduplication and retained uncertainty; D18/D19 fresh-job admission | General campaign admission and exact subscription billing unqualified; no refund or replay of unknown requests |
| Restricted native broker candidate | Pinned tool projection, scoped artifacts, actual executor-only game forwarding and clean-context helper delivery | Full runtime/file/process/network conformance deferred under D14; raw canary failures remain |
| Evaluator source | Private development craft milestone and controls; joined action/refusal, source/lock, stopped player, costs and clocks | Full setup/scientific scoring authority, isolation, matched experiments and confirmation |

Authentic evidence includes selected vanilla mechanics and separate Forge modded
block, machine processing/collection and expert furnace crafting. The approved
[D13 shutdown policy](docs/verification/2026-09-21-d13-shutdown.md) now allows
1,000 ms and has a passing 568.994-ms sample; all old 500-ms failures remain
recorded. Final exact-profile assembly and child dispositions keep G0 open.
Full gameplay/helper isolation is deferred to M1/G1 under D14; selected private
development scorer and measured clock/save joins are already evidenced.
Complete campaign clocks, capacity and canonical recovery remain unqualified.
Separate-desktop rendering preserves desktop usability but does not establish
filesystem/process/network isolation.

## Local development

Pinned development versions are Python **3.12.14**, Node **24.19.0**, and the
Windows x64 Temurin **17.0.20.1+1** JDK for Forge. Python and Node dependencies are
locked. Java builds also verify compiler, wrapper, Forge cache and dependency
hashes; the current Java build profile is Windows-specific.

From the repository root:

```powershell
uv sync --frozen
npm ci --prefix backends/mineflayer
npm run build --prefix backends/mineflayer
uv run --frozen mcbench --help
uv run --frozen python -m ruff check src evaluator/src tests tools
uv run --frozen python -m pytest -q
npm test --prefix backends/mineflayer
```

Cross-language process tests require the pinned JVM and generated test classpath;
without the opt-in environment they may skip. Historical checkpoints ran selected
JVM fixtures enabled; September 24 merge checks record their actual skips separately:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot'
$env:STRATA_FTB_LIBRARY_JAR = 'C:\path\to\official-E9E\mods\ftb-library-forge-1902.4.1-build.236.jar'
Push-Location java
.\gradlew.bat :forge1192-client:test :forge1192-telemetry:test :forge1192-client:writeTestClasspath :forge1192-telemetry:writeTestClasspath --no-daemon --console plain
Pop-Location
$env:STRATA_CLIENT_TEST_JAVA = Join-Path $env:JAVA_HOME 'bin\java.exe'
$env:STRATA_CLIENT_TEST_CLASSPATH = (Resolve-Path java\forge1192-client\build\test-classpath.txt).Path
$env:STRATA_SETTINGS_TEST_JAVA = $env:STRATA_CLIENT_TEST_JAVA
$env:STRATA_SETTINGS_TEST_CLASSPATH = $env:STRATA_CLIENT_TEST_CLASSPATH
$env:STRATA_TELEMETRY_TEST_JAVA = $env:STRATA_CLIENT_TEST_JAVA
$env:STRATA_TELEMETRY_TEST_CLASSPATH = (Resolve-Path java\forge1192-telemetry\build\test-classpath.txt).Path
$env:STRATA_GUARD_TEST_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
$env:STRATA_WRITER_TEST_SID = (Get-LocalUser -Name CodexSandboxOffline).SID.Value
$env:STRATA_WRITER_TEST_GROUP = (Get-LocalGroup -Name CodexSandboxUsers).SID.Value
uv run --frozen python -m pytest -q
npm test --prefix backends/mineflayer
```

The Windows writer tests also require the existing local sandbox identity/group
named above; those commands resolve them and do not create accounts.

Use this checkout's synchronized `.venv` for the isolated Python guard. Its
`-I` invocation ignores `PYTHONPATH`; borrowing another worktree's interpreter
can load that worktree's editable package and correctly fail source-identity
checks. Verify the import before enabling those fixtures:

```powershell
.venv\Scripts\python.exe -I -c "import mcbench.forge_guard; print(mcbench.forge_guard.__file__)"
```

Obtain the FTB Library artifact from the official exact pack outside this repo;
its hash is enforced. No game or modpack binaries are distributed here. See the
[Forge build runbook](docs/operations/forge-telemetry.md) and
[settings extension runbook](docs/operations/forge-client-settings.md) for build
inputs and limitations. A clean-machine build has not been qualified.

See the [session checkpoint verification](docs/verification/2026-09-24-session-handoff.md)
for current merge checks and the historical baseline. These are local contract,
process and fixture checks; they do not substitute for real integration gates.

## Operator boundaries

This is public **operator/design source**, not a gameplay-agent workspace.
Never give gameplay agents or helpers this checkout, evaluator source, design
documents, private logs, credentials or sealed instances. The allowlisted
[gameplay packager](src/mcbench/packaging.py) exports only the scoped CLI and
sanitized keybinding skill; packaging alone is not runtime isolation.

Game installations, account caches, raw runs and private evaluator instances
stay outside this public repository. D17 selects Codex OAuth / `gpt-6-luna`.
The original **$10 aggregate API-equivalent allowance** includes helpers/retries;
exposure is **$4.887796**, preserving the old $0.7554 hold and four full $1 failed-job
envelopes. D18/D19 authorize necessary bounded fresh M0 jobs with all unknown
amounts reserved and prior jobs terminal/fenced. Recheck durable authority before
spend. D12 and used pilots stay consumed; no replay, refund or new allowance.
These estimates are not an exact OAuth bill or subscription conversion.

D14 defers full isolation qualification to M1/G1; development evidence remains
isolation-unqualified and cannot establish protected scoring or scientific
validity. Shared-desktop input remains paused. See the
[validation admission contract](docs/operations/validation-admission.md).

Operational entry points: [provisioning](docs/operations/provisioning.md),
[worker](docs/operations/development-worker.md),
[Forge API](docs/operations/forge-game-api.md), and
[operator commands](docs/operations/operator-core.md).
