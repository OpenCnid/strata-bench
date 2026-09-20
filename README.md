# Strata

**A Minecraft benchmark for long-horizon agent adaptation.**

Strata studies whether experience retained by a fixed agent improves later play,
separately from better equipment, changed worlds or additional inference. The
target system uses [Dovetail](https://github.com/OpenCnid/dovetail-codex) in the
native Codex loop, with typed `mcgame` commands to a persistent game worker.
Mineflayer is the first backend; the separately identified Forge extension is
the authorized development fallback for exact E9E compatibility work.

**Status: implementation checkpoint, not a runnable research MVP.** M0–M5 have
partial implementations, M6 remains required later work, and M7 is conditional.
Narrow authentic vanilla and E9E checks have passed; every aggregate release
gate remains open. Exact E9E's Mineflayer handshake failed, and Forge fallback
evidence does not convert it into a Mineflayer pass.

- [Current review and next-session handoff](docs/STATUS_AND_HANDOFF.md)
- [Specification v0.2.33](SPEC.md): complete target contract and acceptance gates
- [Milestone ledger](MILESTONES.md): coverage, decisions, failures and evidence
- [Project instructions](AGENTS.md): implementation and verification process
- [Build plan](BUILD_PLAN.md) and [research](research/): supporting design evidence

## What is implemented

| Component | Current scope | Qualification still required |
|---|---|---|
| Python operator services | Strict records, storage/journals, grants, controller state, budgets/clocks, checkpoints, artifacts and communication | Integrated production lifecycle, isolation and complete restoration |
| TypeScript worker and CLI | Filtered observations, scoped actions, durable action lane, cancellation, fencing and process supervision | Complete vanilla/modded mechanics and reliability |
| Forge 1.19.2 extension | Structured state/actions, settings transactions, quest/JEI/Thermal adapters, private frame/reference diagnostics | Full menu/mechanics/input parity, T05 keybindings and reliable shutdown |
| Native Codex adapter | Pinned process lifecycle, Dovetail installation inspection and usage parsing | Actual model/plugin/helper execution, complete accounting, credential and network isolation |
| Inference accounting | Atomic reservation plus dispatch intent, receipt deduplication and uncertain-cost holds | Qualified OAuth transport, finite call exposure and real USD conversion |
| Evaluator source | Private telemetry import, saved-state readers, synthetic scorers/probes and analysis/reporting | Authoritative live scoring, matched experiments, power pilot and confirmation |

The latest authentic E9E evidence includes paired mayapple removal, a short level
walk, basic quest navigation and cancellation before route arrival, checked
against independent saved server state. Separate-desktop rendering keeps the
operator desktop usable; it does not provide filesystem/process/network
isolation. See the [handoff](docs/STATUS_AND_HANDOFF.md) for exact limits.

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
.\gradlew.bat :forge1192-client:test :forge1192-telemetry:test :forge1192-client:writeTestClasspath --no-daemon --console plain
Pop-Location
$env:STRATA_CLIENT_TEST_JAVA = Join-Path $env:JAVA_HOME 'bin\java.exe'
$env:STRATA_CLIENT_TEST_CLASSPATH = (Resolve-Path java\forge1192-client\build\test-classpath.txt).Path
$env:STRATA_SETTINGS_TEST_JAVA = $env:STRATA_CLIENT_TEST_JAVA
$env:STRATA_SETTINGS_TEST_CLASSPATH = $env:STRATA_CLIENT_TEST_CLASSPATH
$env:STRATA_GUARD_TEST_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
uv run --frozen python -m pytest -q
npm test --prefix backends/mineflayer
```

Obtain the FTB Library artifact from the official exact pack outside this repo;
its hash is enforced. No game or modpack binaries are distributed here. See the
[Forge build runbook](docs/operations/forge-telemetry.md) and
[settings extension runbook](docs/operations/forge-client-settings.md) for build
inputs and limitations. A clean-machine build has not been qualified.

The September 19 checkpoint passed **738 Python, 166 Node and 445 Java tests**,
with no skips, plus Ruff. These are local contract, process and fixture checks;
they do not substitute for the specification's real integration gates.

## Operator boundaries

This is public **operator/design source**, not a gameplay-agent workspace.
Never give gameplay agents or helpers this checkout, evaluator source, design
documents, private logs, credentials or sealed instances. The allowlisted
[gameplay packager](src/mcbench/packaging.py) exports only the scoped CLI and
sanitized keybinding skill; packaging alone is not runtime isolation.

Game installations, account caches, raw runs and private evaluator instances
stay in separate protected storage. The authorized validation configuration is
Codex OAuth / `gpt-5.6-luna`, with a **$10 aggregate ceiling**. No Strata inference
has been dispatched: live monetary bounds and isolation remain unqualified.

Operational entry points: [provisioning](docs/operations/provisioning.md),
[worker](docs/operations/development-worker.md),
[Forge API](docs/operations/forge-game-api.md), and
[operator commands](docs/operations/operator-core.md).
