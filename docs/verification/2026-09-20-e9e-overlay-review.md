# Exact E9E overlay diagnostics and stopped-installation review

Date: 2026-09-20. Scope: M0.3.2a, partial F01/F05/F10/F16,
N01/N04/N06/N08, C03/C04/C24; T01/T02/T10/T13 and G0 remain incomplete.
This is operator-only code/static-artifact evidence, not a live game trial.

`inspect_e9e_mode` now records bounded differing TOML key paths and source/target
SHA-256 digests for failed comparisons. Byte comparisons record the two digests.
It emits no config values, performs no writes and preserves every existing check,
error code and acceptance result. No role exclusion or migration was introduced.

The stopped dedicated E9E 1.27.0 installation still has **263 passing checks out
of 268**, with the same five failures below. The original and diagnostic reports
have identical ordered check/result/code/success-digest tuples. The file result
remains fail; the inspector's aggregate gate remains not_run and G0 remains fail.

| Retained finding | Evidence from exact installed artifacts | Remaining qualification |
|---|---|---|
| Missing server `bhmenu-client.toml` | BHMenu 2.4.3 registers its CLIENT config from client setup through a Dist.CLIENT branch. The dedicated client's effective TOML contains all overlay values. | Loaded role registration/config evidence and complete role applicability review. |
| Missing server `nomoreworldsettings-client.toml` | No More World Settings 1.1 is present only in the client inventory; its main class registers CLIENT config. The client's effective TOML contains all overlay values. | Loaded role evidence and complete provenance. |
| Missing `inventorysorter-server.toml` | No `inventorysorter` mod ID occurs in top-level or declared JarJar mod descriptors in either inspected role: 261 server / 267 client JAR records. | Full locked distribution/loaded-mod reconciliation; static metadata alone cannot prove all code consumers. |
| Missing `sophisticatedcore-server.toml` | Sophisticated Core 0.6.4.730 registers COMMON and CLIENT configs. Its common overlay exists and passes the existing file check. The old server list is not equal to the current common list. | Loaded common values, consumer behavior and source-backed disposition of the legacy overlay. |
| Create server TOML mismatch | The exact three missing paths are `logistics.defaultExtractionLimit`, `schematics.schematicannon.schematicannonGunpowderWorth` and `schematics.schematicannon.schematicannonFuelUsage`. Create 0.5.1.i defines `defaultExtractionTimer` and `schematicannonShotsPerGunpowder`; the cannon consumer uses the latter. | Loaded spec/data and mechanics evidence; no guessed key rename or value conversion. |

The two client files differ in bytes from their overlays but have no differing
overlay TOML values; comments/formatting do not fail the existing subset rule.
The historical server list has 129 entries, compared with 145 in the current
Sophisticated Core common overlay. All old IDs occur in the latter, but 16 raw
values differ: fourteen storage toggles and two pump strings spelled `alse`.
The installed parser splits each entry and calls `Boolean.valueOf(String)`;
this explains how those two strings are interpreted by that code, without
certifying a loaded value or changing vendor bytes. The original client and
server archives contain exactly the inspected common, legacy-server and Create
overlay bytes. This is not evidence of accidental local editing, nor authority
to merge the incompatible settings.

Read-only `javap -c -p -constants` used the pinned Temurin 17.0.20.1+1 tool on
the exact JARs. JAR, class and disassembly hashes, declared nested-mod inventory,
archive provenance and stopped-file reports are private in
`C:\Users\Darian\.strata\evidence\2026-09-20-e9e-overlay-review-01`.
No proprietary classes, config copies, worlds or raw evidence are committed.
No server/client was launched, installation edited, shared input used or paid
inference dispatched for this work.

Verification: `uv run --frozen python -m pytest -q tests/test_pack_modes.py
tests/test_gameplay_package.py` passes **15 tests**, zero skips, 1.06 s, with two
existing Typer/Click deprecation warnings. Tests preserve failure results,
quoted-key/type/list semantics, byte binding, no config-value export, quotas
and unchanged fixture files. Ruff on both changed Python files and
`git diff --check` pass. An initial new-test snapshot incorrectly used the
installation inventory API on its synthetic world directory; the expected
private-content rejection produced 14 passes/one failure. The test was corrected
to hash its own temporary fixture files; production privacy checks were unchanged.

Next: capture private loaded Forge registration/spec/data evidence with strict
bounds and source identity, retain unresolved absence/migration cases, then
complete cold-restart/player-reference/quest/expert-mechanic assertions. Static
review and local tests cannot close T02, T10, G0 or an entire pack milestone.
