# Private native setup mutation observations

September 21, 2026. Operator-only. M0.2c.3b.3c; partial F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, T01/T06/T07/T10/T13 and G0 item 5.
M0 remains incomplete, G0 fails, and G1–G5 are not run.

Telemetry 0.3.7 / startup payload 8 adds a bounded sticky monitor with eight
required native mixins and 25 exact entry selectors. Pinned Forge 43.4.23 SRG
and FTB Teams 1902.2.14-build.123 bytecode was inspected directly. Native actor
mode changes, operator add/remove/reload, command permission, world mode and
difficulty, FTB deserialization/creation/reload and party operations are observed.
Counters record entry attempts, including unsuccessful or reversed operations;
they are not a count of distinct successful mutations. A mode setter with the
same current mode adds no mode-change observation. No game state is changed.

The fixed counter map cannot grow with input. Synchronized updates retain
off-thread observations; saturation stays explicit and disqualifies candidates.
The monitor activates once during server startup and cannot reset or resume.
It emits history immediately before each existing setup point and before stop.
The private parser verifies exact scope/adjacency, monotonic counters, complete
route keys, startup and terminal records. Resource witnesses explicitly validate
the added end-history record; arbitrary sequence gaps are still rejected.
Any taint, even after a craft, rejects the entire reference's candidates.

Ordinary shutdown is separately observed: an exact parsed `stop` attempt must
reach Minecraft's pinned native stop body with the same source object and
server thread. Both counters remain. Only one such terminal pair is allowed;
additional commands, unmatched stop entries and stop followed by later setup
cannot be treated as normal management. This does not prove the shutdown time.
The existing private pipe transport/identity check also applies to startup 8.
Legacy signed module versions retain their original requirements and report
shape; no old seal or stream is rewritten or given retroactive history credit.

This does **not** cover every mutation route. Inspected FTB bytecode exposes
public `PlayerTeam.actualTeam`, manager maps and mutable team state; KubeJS
`GLOBAL` is another unmediated map. Direct/reflection/mod/file writes, setup
before monitor activation, protected writer custody and instrumentation parity
remain separate gaps. Runtime support explicitly reports complete-route coverage
false; continuous history, setup qualification and scoring stay false. No raw
command text, credentials or new gameplay affordance is exported.

Executed source verification on Windows / Python 3.12.14 / pinned Temurin
17.0.20.1+1 / Gradle 8.8:

- Initial affected Python selection: 187 pass, six optional native cases skipped,
  22.20 s. Enabling the pinned JVM then passes the five signer/sealed-roster
  cases in 4.76 s; these use fabricated event contents.
- After native-stop correlation, focused history/pipe selection: 55 pass,
  two unrelated/explicit cases deselected, 8.75 s. Includes all 12 mutation
  categories reversed between matching points, after-craft taint, omissions,
  reordering, foreign scopes, rollback, overflow, unsupported hooks and unsafe
  native-stop combinations. Two new pipe transport checks pass separately.
- Gradle builds the reobfuscated JAR and passes the focused monitor tests;
  the current monitor suite has four tests, zero failures/errors/skips.
- Offline ASM target audit checks compiled selectors against actual pinned
  dependency bytecode. The initial seven-mixin/24-selector audit passes and a
  deliberately wrong dependency JAR fails. The final eight-mixin/25-selector
  audit passes. This verifies method availability, **not** Mixin application.
- Final signed-history JVM and gameplay-package/canonical-record selection:
  30 pass, 1.73 s. Full repository Ruff and whitespace checks pass. The remaining
  skipped case from the initial selection requires a separate native sandbox
  group opt-in; this unchanged peer-denial case is not claimed as rerun evidence.

Source/fixture artifacts stay private in
`C:/Users/Darian/.strata/evidence/2026-09-21-setup-history-01`.

## Authentic changed-module startup and stop

One fresh headless E9E 1.27.0 / Forge 43.4.23 reference used the reviewed official
bootstrap, existing accepted EULA, online mode, loopback port 25589 and the
unchanged 2–5 GiB JRE 17 profile. Only the private clone's telemetry module,
port and one-use scope changed. The owned launcher retained the existing
300-second run ceiling, 10-second ready interval and 120-second graceful stop
bound. No client, model request or desktop input occurred.

The actual CLI completed normally in 149.359 s; the owned server interval was
145.656 s. Independent audit **33/33 passes**: exact native process/game/world/
module binding, all eight hook markers present, supported pinned setup artifacts,
loaded expert mode and survival/no-admin startup facts, complete signed history,
normal stop and all six retained processes signaled. No Java remained. All
18,225 original source files and 1,540 immutable launch files rehashed unchanged.
The 104-file sealed world remains independent of the new save. One-use relaunch
was rejected, and identical import added no event.

The stream contains 16 signed records, 211 final / 207 sampled server ticks and
two history records. Terminal counters contain exactly one observed command and
one correlated native stop handler; all other mutation counters remain
zero, with no off-thread attempt or overflow. This is authentic hook application
and clean lifecycle evidence. No avatar, craft or deliberate mode/operator/team
mutation occurred. It cannot qualify those authentic controls, scoring, protected
writer custody, instrumentation parity, full-route history or the 500-ms client
guardian.

Private bundle:
`C:/Users/Darian/.strata/evidence/2026-09-21-setup-history-live-01`.

| Artifact | SHA-256 |
|---|---|
| Telemetry 0.3.7 JAR | `ea112c9e2cd9d5573a407a5e7a35cb075425ba7b1408e24ecc5a6c219cd2a93e` |
| Signed stream | `8ed153d10996db923ff6b584623fbec1a9bf0057f1080584c142418f11147725` |
| Independent audit | `ab746435583a9127628889e79e14af8073df4bce3e743addcf10d9e5a84107d5` |

Read-only accounting at 23:26:31 UTC confirms the original $10 authority,
$0.7554 unresolved hold plus $0.001458 settled ($0.756858), two requests and one
valuation. Uncertainty remains true and D12 remains consumed. Token totals still
include reservations; they are not measured total usage. No model request was
made or replayed. All earlier shutdown, effective-file, isolation and Mineflayer/
E9E failures remain unchanged.

Next implement and exercise preregistered private mutation controls against this
changed profile, then close unmediated setup/write routes and the remaining
protected custody, shutdown and joint recovery requirements. Matching clean
startup/stop observations cannot replace those controls. M0/G0 stays open.
