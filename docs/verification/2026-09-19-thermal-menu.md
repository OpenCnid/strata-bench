# Initial Thermal GUI observation adapter — September 19, 2026

Operator-only evidence summary. **Implemented but unverified in Minecraft.**
M0.3b.3.2.1 advances F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06.
M0.3b.3.2 is split into observation, transactions, other discovery and authentic
reference children; none of the required modded-operation scope is removed.

## Delivered behavior

The Forge candidate's capability minor 14 declares
`thermal-current-gui-energy-fluid-base-slots/1`. `NativeThermalMenu` follows the
currently open exact furnace/crucible menu's public `tile` field, after checking
thread, body, screen, menu registry ID, class, layout, runtime version and three
loaded JAR hashes. Fixed public getters read the same energy storage and crucible
output tank used by the installed GUI. It neither searches other block entities
nor exposes a reflective API to gameplay.

`window.machine` contains RF stored/capacity and zero furnace tanks or one
crucible tank, with capacity and nullable namespaced fluid/amount in mB. Tagged
fluids, invalid bounds, unknown types/builds and changed context reject. Active
base and player slots preserve their native indices; augment-panel entries are
omitted before reading their contents. Unknown entries are not labeled empty.
Python, generated JSON/TypeScript and worker validation reject extra fields,
wrong kinds, tank layouts, type mismatches, invalid numeric types and overcapacity
values. Existing snapshots may omit the nullable new field.

These are current client GUI values, not server-authoritative machine evidence.
They participate in existing snapshot/window revisions. No freshness exception
was added for processing; changing energy/fluid can invalidate a pending action.
Machine slot mutations fail before input instead of entering the existing
static-resource inventory motor. Explicit close retains its guarded own-inventory
path, but native Thermal close has not been executed. Processing-aware slot
verification, machine controls/progress, augment panels and other required
mechanic adapters remain open.

## Exact installed-source inspection

Inspected the dedicated E9E 1.27.0 distribution with JDK 17 `jar`/`javap`, including
the Thermal Core JAR nested in Thermal Foundation. No game JAR is added to source
or redistributed in the client artifact; the optional adapter uses fixed public
members and existing Forge/Minecraft compile dependencies.

| Artifact | SHA-256 |
|---|---|
| `thermal_expansion-1.19.2-10.3.1.25.jar` | `ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c` |
| `thermal_core-1.19.2-10.3.0.9.jar` | `20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5` |
| `cofh_core-1.19.2-10.3.1.48.jar` | `1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d` |

Their `mods.toml` runtime versions are 10.3.1, 10.3.0 and 10.3.1 respectively.
Inspection caught an initial candidate guard using filename build suffixes as
runtime versions; it was corrected before any client deployment. Matching only
the shortened labels would not pin the required builds, so missing/changed bytes
also reject. This does not seal the entire pack or establish process isolation.

Installed bytecode confirms the furnace's input/result/charge layout, the
crucible's input/charge layout, separately bound augment/player slots, GUI energy
storage and crucible output tank 0. The furnace output is `FurnaceResultSlot`, not
`SlotCoFH`; that exact distinction is checked. Public upstream
[crucible GUI source](https://raw.githubusercontent.com/CoFH/ThermalExpansion/1.19.x/src/main/java/cofh/thermal/expansion/client/gui/machine/MachineCrucibleScreen.java)
and [container source](https://raw.githubusercontent.com/CoFH/ThermalExpansion/1.19.x/src/main/java/cofh/thermal/expansion/inventory/container/machine/MachineCrucibleContainer.java)
support the API investigation; installed bytes are the build authority. This is
source inspection, not GUI parity or real transaction evidence.

## Executed checks

Environment: Windows x64, Temurin JDK 17.0.20.1+1, pinned Forge 43.4.23/Minecraft
1.19.2 build; Node 24.19.0 and the repository's frozen Python environment.

| Check | Actual result | Scope |
|---|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | 182 tests pass; no failures/errors/skips; final build 24 s | Nine new pure projection/pin/bounds/context/layout tests; native bridge compiles, effects synthetic |
| `npm test` with pinned Java/classpath/guardian environment | 116 pass, no skips/failures, 44.697 s | Full Node suite; actual local CLI/HTTP/JVM transports use synthetic bodies |
| Final `npm run build` then `node --test dist/tests/contracts.test.js dist/tests/forge.test.js` | 30 pass, no skips/failures, 43.656 s | Final byte-pin guard/capability revision; synthetic effects. JVM guard exit measurements 471/47/1757/42 ms for native freeze/worker kill/worker hang/parent kill, not Minecraft timings |
| `pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py -q` | 96 pass; 18 JVM cases initially skip because shell lacked opt-in variables | Contracts/projection and synthetic responses |
| `pytest tests/test_native_game_jvm.py -q` with pinned Java/classpath | All 18 previously skipped cases pass, 21.73 s | Actual Python/Java/HTTP; synthetic game effects |
| Ruff on changed Python files; schema export and TypeScript generation; `git diff --check` | Pass | Development validation; ordinary line-ending warnings only |

The Python set therefore has 114 distinct passing cases after the explicit JVM
run. A successful JVM transport does not validate `NativeThermalMenu` against a
live machine. The new schema test covers both empty and filled tanks, and rejects
raw component canaries; it is not an OS-isolation test.

Final built client SHA-256:
`f34f6c2e786f02dbe6c97693cceab50c540d8621c054c68df8c532121dd55ec6`.
The candidate is **not installed**. The live E9E client still has the earlier
read-only build `c2218c6c…`. A fresh read-only screen capture again showed the
Windows Security/OpenJDK network permission prompt; no desktop input was sent.
The pending operator handoff remains necessary under the computer-use skill.
No server/gameplay worker was launched, and no Strata inference was dispatched.

Private raw evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-thermal-menu-01`:
build/test logs, test XML, exact metadata/bytecode inspection, selected source
copies and `verification.json`. No auth cache or bridge descriptor is copied.

## Remaining acceptance

M0.3b.3.2.1 remains `implemented_unverified`. Next implement .2's ordinary machine
transactions with explicit handling of processing/charging between replies; keep
.3's custom categories/ingredients/quests and .4's live/reference checks visible.
When the permission prompt is handled, deploy the candidate and test connected
JEI/expert craft, GUI visibility, native controls/cancellation and machine effects
against actual server evidence. All earlier movement/placement/menu/settings,
host/isolation/budget/soak/capacity and research gaps remain. T03/G0 retain the
failed Mineflayer/E9E result; no aggregate suite, milestone or release gate closes.
