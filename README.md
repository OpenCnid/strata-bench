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
| Native Codex adapter | Actual pinned CLI/plugin/root/helper, skill/supporting-file reads, learned activation/export and connected vanilla smoke with scripted replies | Live-model game integration, full helper/isolation and authentic joint recovery qualification |
| Inference accounting | D11 estimates/migration, nested envelopes, distinct requests, deduplicated receipts and uncertain holds; one authentic D12 receipt reconciled offline | Original unknown hold blocks general admission; native reply delivery failed and changed transport remains live-unqualified |
| Restricted native broker candidate | Pinned caller/tool projections, scoped artifact writes, executor-only real worker forwarding and clean helper admission | Full runtime/file/process/network conformance and live-model game qualification; raw canary failures remain |
| Evaluator source | Private telemetry, saved-state/resource witnesses, campaign/source-bound scorers and synthetic controls/probes/reporting | Authenticated source/setup/team admission, authoritative live scoring, matched experiments and confirmation |

Authentic evidence includes selected vanilla mechanics and separate Forge modded
block, machine processing/collection and expert furnace crafting. The approved
[D13 shutdown policy](docs/verification/2026-09-21-d13-shutdown.md) now allows
1,000 ms and has a passing 568.994-ms sample; all old 500-ms failures remain
recorded. Private scorer/setup controls, full isolation, authoritative clock/save
evidence and remaining profile/recovery qualification still block G0.
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
without the opt-in environment they may skip. The checkpoint ran them enabled:

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

Obtain the FTB Library artifact from the official exact pack outside this repo;
its hash is enforced. No game or modpack binaries are distributed here. See the
[Forge build runbook](docs/operations/forge-telemetry.md) and
[settings extension runbook](docs/operations/forge-client-settings.md) for build
inputs and limitations. A clean-machine build has not been qualified.

See the [session checkpoint verification](docs/verification/2026-09-22-session-handoff.md)
for current merge checks and the historical baseline. These are local contract,
process and fixture checks; they do not substitute for real integration gates.

## Operator boundaries

This is public **operator/design source**, not a gameplay-agent workspace.
Never give gameplay agents or helpers this checkout, evaluator source, design
documents, private logs, credentials or sealed instances. The allowlisted
[gameplay packager](src/mcbench/packaging.py) exports only the scoped CLI and
sanitized keybinding skill; packaging alone is not runtime isolation.

Game installations, account caches, raw runs and private evaluator instances
stay in separate protected storage. The authorized validation configuration is
Codex OAuth / `gpt-5.6-luna`, with the original **$10 aggregate API-equivalent
estimated usage allowance**, including helpers/retries (D04 clarified by D11).
The user confirms no outside experiments. D11 migration preserves the original
authority. Two actual requests now account for $0.7554 held plus $0.001458
settled ($0.756858 combined); D12 is consumed and general admission remains
blocked. Native reply delivery failed despite successful offline receipt recovery.
This is not an OAuth bill or exact subscription-quota conversion. A VM is optional; an enforceable game,
evaluator and credential boundary remains required. See the
[validation admission contract](docs/operations/validation-admission.md).

Operational entry points: [provisioning](docs/operations/provisioning.md),
[worker](docs/operations/development-worker.md),
[Forge API](docs/operations/forge-game-api.md), and
[operator commands](docs/operations/operator-core.md).
