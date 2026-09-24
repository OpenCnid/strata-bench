# Reproduced Forge runtime JARs

M0.3a.4c is **verified** for reproducing and importing the required client and
server SRG JARs. All 15 actual audit checks and 92 focused tests pass. This
corrects the earlier classification of the server SRG file as an expendable
installer intermediate: actual FML launch-handler bytecode selects SRG and
extra JARs for both roles. The previous 103-file server subset remains valid
as a partial preparation, with its original exclusions and evidence retained.
It is not a complete runnable server library tree.

Coverage: M0.3a.4/.4c, F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T13 and G0 item 2. M0 remains in_progress and G0 fail.
E9E remains ACQUIRED. D14 isolation deferral and M1–M7 remain unchanged.

The [producer](../../src/mcbench/forge_derivation.py) reads the exact official
Forge installer and retained Mojang metadata. It checks processor JARs and
dependencies, MCP mappings, Mojang mappings and declared slim-JAR hashes.
Installed merged/SRG files are comparison targets, never generator inputs.
The original sealed vanilla inventory supplies all 316 Java files. Windows
file leases hold all 356 source/runtime paths throughout four fixed offline
processor executions; each has a 120-second deadline, 1-GiB heap and bounded
logs. No installer, Minecraft, model request or desktop input executes.

Actual MERGE_MAPPING and ForgeAutoRenamingTool executions took 2.437, 7.907,
2.000 and 6.063 seconds. Each exited zero with four total owned processes,
zero active processes and zero forced terminations. Both merged mappings and
both SRG JARs match the installed bytes exactly. A final process inspection
found no Java or Javaw process.

| Runtime artifact | Bytes | SHA-256 |
|---|---:|---|
| Client SRG | 17,332,865 | `844f5333e261c3bf6a4b99c9fa3872e7beb913d087d0d759c08b3a6d236e0179` |
| Server SRG | 12,943,367 | `18c6084b06a112d1480dfd6c37d5ed92c9f8feaba3d8159719e0197813fef97a` |

The [existing provisioning consumer](../../src/mcbench/provisioning.py)
imports these two outputs without rerunning processors. It checks acquisition,
plan, installer, role, process completion and file bindings before importing
either file. The resulting private FileEntry rows are usable by role assembly;
they do not assert a complete role or a license portfolio review. Reimport is
idempotent. Changed files, cross-request/receipt bindings, failed processes,
active descendants and malformed accounting reject.

Private bundle `2026-09-23-forge-derived-runtime-01` retains the initial and
import source versions, commands/results, bytecode review, 356 held input
copies, generated files, accounting snapshots and audit. The directory name
retains the preparation date; final review and documentation are September 24.

| Evidence | SHA-256 / CAS digest |
|---|---|
| Seal: 405 files, 280,894,708 bytes | `5ed2e358e94355842f388383344107bd413dd1f702b61db1490942904c987fcf` |
| Audit: 15/15 | `5b0ea6a7f3d2cc236ff63ffc2150f5f9d515b34ab8b611d1f064aa5f66b71bbe` |
| Acquired derivation result | `1ba8ee5b02b676cf1132555dfd4fd736aff57529234fd5827adfa39f4cae07d2` |
| Imported role artifacts | `e242c7fafa6c0d276c9628fdb2bb5ea99f15396053aec57f6ebbe2e0308ad5d0` |

All 37 non-artifact authority tables and every previous artifact/event row are
unchanged. Only five artifacts and five events append: plan, derivation result,
two JARs and import result. Exposure remains **$2.831942/$10**, including all
old holds. No unresolved request was replayed, refunded or settled.

Executed `python -X utf8 -m pytest tests/test_forge_derivation.py tests/test_forge_runtime.py tests/test_e9e_content.py tests/test_provisioning.py -q`:
**92 passed in 26.69 seconds**, with two existing Typer/Click deprecations.
Changed-file Ruff passes. Earlier source checks retained two synthetic failures
from Windows extended-path normalization, then one from briefly lagging Job
Object accounting after root exit. Normalized lease paths and a bounded
two-second terminal reconciliation fixed these before the authentic run.
There was one successful authentic derivation; it was not repeated for import.

Next assemble the complete client software/Java/assets and server software
with vendor content, harness and effective settings; resolve remaining license
and role exclusions, then use existing inventory and seal admission. Remaining
G0 host/helper, profile, recovery, scorer and clock/cost joins stay open.
The verified GPT-6 Luna/Mineflayer turn-and-walk pilot is unchanged.
