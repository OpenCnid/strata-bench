# Exact E9E Forge server software preparation

M0.3a.4a is **verified** for software preparation: the operator command derives
and copies 103 files (146,083,419 bytes) from exact publisher sources, retaining
four explicitly excluded installer intermediates. Ten independent integration
checks and 99 focused tests pass. E9E remains **ACQUIRED**, M0 in_progress and
G0 fail; complete role inventory and sealing are still open.

Coverage: M0.3a.4/.4a, F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T13 and G0 item 2. This advances the installed-file provenance
dependency identified after the loaded-role/Create control. M1–M7 and D14's
isolation deferral remain unchanged.

## Implementation and actual evidence

[forge_runtime.py](../../src/mcbench/forge_runtime.py) and the operator
`pack prepare-forge-server-libraries` command join the exact Forge installer,
retained Mojang metadata/bundle and stopped server libraries. They do not run
an installer or game. The 66 unique Forge-declared dependencies match their
published SHA-1/size values. Minecraft dependencies and unpacked server match
the bundle's verified members; shared declarations retain both sources.
MCP mappings match the declared ZIP member, Mojang mappings match the release
metadata, launch arguments match installer members, and slim/extra/patched
outputs match the installer's declared hashes. No generated hash is invented
from the installed file it is supposed to verify.

Exactly four original files are retained in the exclusion inventory:
merged mappings, the SRG renaming intermediate and two split caches. Their
hashes preserve what was observed; they are not copied or declared to have
qualified provenance. Unknown or missing content rejects. Full file counts,
byte limits, safe paths, links/hardlinks, content conflicts and source/copy
changes are checked. Existing/partial destinations cannot be reused.

The official Forge installer was downloaded from its exact versioned Maven
URL and checked against its published SHA-1, without execution:

- SHA-256: `5e801fb105951a4cea7d9b57edaea4a5d22b83107822f099167c95179a7e93a1`
- SHA-1: `06c46a5371b1c6b22c7b88f17d50a95beb867c07`

Private bundle `2026-09-23-e9e-inventory-01` retains the capture, metadata,
source, copied software, all exclusions, command outputs and before/after
authority digests. Its ten audit checks pass: all 107 original library files,
source artifacts and all 39 original authority tables remain unchanged;
the complete prepared tree matches all 103 expected file digests. E9E stays
ACQUIRED. No model, game, installer or shared-desktop input was used.

Three private driver failures are retained: a mistaken SQLite column name,
a no-op module invocation, and a missing package `__main__` entry. All happened
before software preparation. The corrected driver invokes the actual Typer
entry point and succeeds; no failed destination or game instance was replayed.

| Evidence | SHA-256 |
|---|---|
| Complete private seal: 136 files, 153,446,973 bytes | `77a8de50b7c0689a0e2e0a1508229f77b21ceaffdfe14da623ab8b83a5d3a1e9` |
| Integration audit: 10/10 | `9ab0f8c11f8d9fdb0f64c940730fcecdf6e16994d9aedd98de74d782d184a914` |

## Verification and remaining work

Executed `python -X utf8 -m pytest tests/test_forge_runtime.py tests/test_vanilla_runtime.py tests/test_vanilla_artifacts.py tests/test_provisioning.py -q`:
**99 passed in 17.93 seconds**, with two existing Typer/Click deprecations.
The 18 new cases cover source/installed corruption, incomplete/unsafe trees,
independent copies, interruption/source changes, occupied output and command
integration. Ruff passes for the changed Python files. Synthetic test archives
are explicitly separate from the authentic retained-installation preparation.

This does not establish complete license review, live custody, cold startup of
the prepared subset, both role inventories, PackLock or mechanics/scoring.
The existing E9E cold-start and consumer evidence keeps its original profile.
Next join the exact client/server mod manifests, vendor overrides, selected
client/Java/assets software, generated settings and explicit state exclusions
into complete role preparation, then feed the existing inventory/seal consumer.
Do not repeat unchanged successful game controls or the LLM pilot.

Original committed/reserved exposure remains **$2.831942 of $10**. Every D19
hold persists; no accounting rows or model costs changed. The LLM-driven
Mineflayer turn/walk pilot remains verified for its named development profile.
