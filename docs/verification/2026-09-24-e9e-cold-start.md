# Installed E9E server initialization and cold restart

M0.3a.4g is **verified** for the named headless development profile: first
initialization of a fresh independently copied server role, normal stop, and cold
restart of that same world. Both boots pass their lifecycle/telemetry checks.
Full E9E profile admission remains open; M0 is in_progress and G0 fail.

| Boot | Recorded elapsed seconds | Server ticks | Signed events | Normally terminal owned processes |
|---|---:|---:|---:|---:|
| Initial world | 203.094 | 202 | 18 | 3/3 |
| Cold restart | 147.734 | 202 | 18 | 3/3 |

Both fresh telemetry authorities authenticate independently and bind the observed
Java executable, process start, module, game/world paths and online port to held
Job Object members. They report expert mode, zero KubeJS startup/server errors,
and the same expert furnace recipe: five andesite plus three polished andesite
produce one furnace. Selected loaded values match across boots: Create SERVER
values 8/400/10, and all 145 entries of Sophisticated Core COMMON `enabledItems`.
These are config snapshots, not new getter or player-crafting evidence. Retain the
previous qualified getter/role/craft controls for the remaining profile join.

Coverage: M0.3a.4/.4g, F01/F05/F16, N01/N04/N06/N08, C03/C04/C24;
partial T01/T02/T07/T13, G0 item 2. No M1–M7 advancement. D14 isolation deferral
continues; this evidence is explicitly isolation-unqualified.

## Implementation and actual inputs

[The operator helper](../../tools/e9e_cold_start.py) implements
`e9e1270-installed-forge-cold-start/1`. It directly invokes the reviewed installed
Forge 1.19.2-43.4.23 argument file, with four processors and 2G/5G heap. It does
not execute ServerStarter or a Forge installer. Fixed pins:

- Installed `win_args.txt`: `083c60331e7cdd9c76f73a3131f86e1f8b5454fa1a531f59e2d9748c27923c30`.
- Java executable: `1977f302375adbb920d41dac65c7e22eb9c2ed8e1e8d6258964154ff16f14406`.
- Telemetry 0.3.13: `0067aba399598ed6d9482398ea051aff24fcaa1fb1499fe7d546d915d5df6625`.

The private driver resolves the retained initial-role result
`6d741d2274414e72ddf85c2538dc20bc7306a3f3b07190ec1fe3bcef71888a68`,
verifies all 8,819 server files and 1,108 directories, creates a fresh independent
copy, and verifies the same complete layout before launch. Both boots use that
copy; no player history or old reference world is imported. Java, libraries,
mods and KubeJS startup/server scripts are held against writes. Credentials are
not inherited; the private telemetry key and config stay outside the game tree.
Only the operator `stop` command is sent. No gameplay policy or agent action is
scripted by this helper. The real GPT-6 Luna/Mineflayer pilot remains separate,
already verified evidence and was not repeated.

The profile requires loopback online port 25603, existing EULA acceptance,
standard world path and disabled RCON/query/command blocks. It permits 300 seconds
before stop, ten seconds after bound startup with readiness required, a 120-second
normal drain and a 425-second outer watchdog. These are provisioning limits;
no D13 emergency-stop or complete-save qualification is inferred.

After each normally terminal boot, the driver retains a leased full inventory,
all new/changed files, removed-path list, and the strict effective-file report.
Boot one has 8,896 files, 165 changed/new files (22,978,262 bytes); boot two has
8,899 files, 168 changed/new files (22,661,191 bytes). Each removes the same 29
initial generated Emendatus Enigmatica biome-feature files. Those removals remain
explicit source dispositions; they are not silently dropped from final inventory
work. Unchanged files remain bound to the original prepared-role evidence.

## Retained findings and independent reconstruction

Independent reconstruction passes **24/25** checks. The raw whole-config-byte
equality assertion remains **fail**: one of 7,102 config paths changes,
`config/byg/backups/last_working_configs_backup.zip`. A separate **3/3** comparison
shows all 38 ZIP members have identical names/content and the entire archive
becomes byte-identical after zeroing only each local/central header's four DOS
time/date bytes. The common normalized SHA-256 is
`8e1aedc93b1eb5a81cafe56d6e901fb1e31acc09e004586dbc9084da0ae943e0`.
The other 7,101 config files are byte-identical. This exact generated backup
metadata disposition is not a general config exclusion or a rewritten test pass.
No game replay was used to investigate it.

The strict effective-file inspection remains **263/268**, with the same five
historical findings on each boot:

- Missing dedicated-server targets for `bhmenu-client.toml` and `nomoreworldsettings-client.toml`.
- Three absent legacy Create keys; current loaded values are recorded separately.
- Missing `inventorysorter-server.toml` and legacy `sophisticatedcore-server.toml`.

Existing role/consumer evidence informs their eventual admission disposition;
this run does not silently suppress them or claim the full file gate passed.
The authenticated streams reconstruct identically, expert mode/recipe and selected
loaded configs persist, all six held processes terminate normally, and all 39
original authority tables are unchanged. No model request or inference charge
occurred. E9E stays ACQUIRED; exposure remains **$2.831942/$10**, with every old
hold and unresolved full envelope retained.

## Focused checks and evidence

```text
python -X utf8 -m pytest tests/test_e9e_cold_start.py -q --disable-warnings --maxfail=2
# 13 passed in 11.46 seconds
ruff check tools/e9e_cold_start.py tests/test_e9e_cold_start.py
# pass
```

[Tests](../../tests/test_e9e_cold_start.py) cover exact preflight, wrong pins/mode,
existing world/output, overlap, EULA/online/RCON/duplicate properties, actual owned
Python normal stop, early exit and bounded watchdog failure. They use synthetic
profile/telemetry fixtures and do not stand in for the two actual Forge boots.
The first local result was 11 pass/1 failure: Windows extended-path representation
was being returned as a launch path. Preserve the checked canonical command path;
12 pre-live cases then passed. A post-live source follow-up records forced-stop
and error codes and joins watchdog cleanup; its added synthetic fault case brings
the final count to 13. Both exact executed and final follow-up sources are retained;
normal successful live behavior was unchanged, so it was not replayed.

Private bundle `2026-09-24-e9e-cold-start-01`: **384 files / 70,240,363 bytes**.
Full bounded bundle readback passes. It retains source, both grants/streams/logs,
config/world deltas, inventories, actual execution, failed original audit, exact
backup comparison, and before/after authority snapshots. Pins:

- Seal: `9830a2836a8b159b25eec6991162b3594a94c65f15882b97fe929d36a7666c5f`.
- Original 24/25 audit: `eb1c7601e99a19965a68f6bf7abf1f5db10e8abc5527a85b667135cefc813efd`.
- Backup comparison: `f5c9bdd4a3d192b88d7fc7d411955ba96a6f323e983c93bf93e79b6e973f50a5`.

Next qualify the remaining client effective-config role and connect this server
initialization evidence, prior loaded-role/getter controls and exact generated
file dispositions to final E9E inventory/profile admission. Preserve both stopped
world snapshots and the now-unused working instance; do not repeat these successful
boots or the LLM pilot unchanged. Complete the remaining six-item root/helper,
scorer, recovery and authoritative clock/save/cost joins before closing G0.
