# Live native clocks for repair accounting

M1.1c.3.4 now has a callback-clock producer and authenticated prefix reader that
work while the server process continues. The actual JVM/Python check observes
three successive server ticks with avatar callback totals 1, 1, 2 across a
synthetic disconnect/reconnect. The same JVM remains alive during every read and
then stops normally. This resolves the terminal-only source dependency in code;
it does **not** finish repair settlement, qualify Minecraft or close G1.

## Exact scope

The existing Forge clock counts server and player callbacks independently of the
health stream's end-of-tick connected-player roster. Telemetry 0.3.19 declares
`ServerStarted/20` and `server-event-monotonic-samples/1`, and emits a private
`ServerClockSample/1` immediately after each existing health sample. The snapshot
is made on the clock's owning server thread after a complete tick. Taking one
does not reset, close or mutate the cumulative counters. Incomplete/off-thread
callbacks still invalidate the clock. The terminal `ServerClock/1` is preserved.

The pipe and full inspector recognize the declared version, require health/sample
adjacency and retain the existing authenticated private transport. The full
inspector reconciles sample ticks/work/wall and monotonic avatar callback counts
through the terminal record. Legacy profiles keep their identities and receive
no inferred callback samples.

`evaluator/src/strata_evaluator/live_clocks.py` reads an explicit bounded cursor
through the original MAC chain, verifies campaign/epoch/boot/sequence, and requires
the selected prefix to end at a complete callback sample. It retains the exact
prefix hash and authentication receipt. Later appends do not change that receipt;
truncated requested input fails. It never turns a prefix into a clean-stop report.
It does not inspect unrelated scoring payload semantics or qualify process
identity, roster ownership, current freshness or full repair coverage. Its
`complete_repair_accounting`, active-time and roster-qualification flags stay false.

The live reader is evaluator/operator code, outside gameplay/helper catalogs. No
new game-facing network route, secret, administrative action or scoring feedback
was introduced. Increased private telemetry volume remains within the existing
quota enforcement; authentic overhead/parity needs the changed profile's evidence.

## Executed checks

Windows; Python 3.12.14; pinned Java 17.0.20.1+1; offline Forge 1.19.2/43.4.23 build.

- `gradlew -p java --offline :forge1192-telemetry:test --tests '*ServerClockTest'`:
  10 tests pass, including continued sampling, disconnect/reconnect, immutable
  returned values, incomplete ticks, thread ownership and historical failures.
- `:forge1192-telemetry:writeTestClasspath :forge1192-telemetry:jar`:
  compilation and reobfuscated candidate JAR build pass. Nothing was installed.
- Focused `test_live_clocks.py`, `test_telemetry_pipe.py`, `test_telemetry_auth.py`,
  `test_telemetry.py`, `test_telemetry_clocks.py`: 109 pass, one opt-in integration
  skip, four deliberately deselected integration tests. These exercise signed
  growing prefixes, completed-stream compatibility and corrupt/missing/reordered/
  rollback evidence; synthetic sources remain labeled.
- Explicit `STRATA_TELEMETRY_TEST_JAVA` and `STRATA_TELEMETRY_TEST_CLASSPATH`, then
  `pytest tests/test_live_clocks.py -q -k actual_java`: one actual process check
  passes. Production Java clock and Python verifier; synthetic callbacks,
  signing authority and startup facts. This is not an authentic Minecraft run.
- Ruff passes for changed Python sources/tests; `git diff --check` passes.

The first combined Python check retained 38 passes and one fixture setup error:
the shared legacy pipe fixture received an already-upgraded synthetic plan.
Fixture construction order was corrected; no production requirement changed.
The initial audit path lookup and UTF-8 documentation-read errors caused no
durable authority mutation. All historical game failures and held amounts remain.

## Remaining join

The controller still must bind admitted server/roster identity and timely sample
cursors to the repair, reconcile body exposure and model/helper consumption,
allocate prior gameplay without overlapping charges, include the publication
tail, settle durably and restore the original worker lease. Periodic samples alone
do not prove precise repair start/end coverage. Generic completion remains fenced.
The complete rollback/skill/launcher workflow, essential native-health failure,
authentic qualification, and other T01/T04/T05/T06/T10/T11 requirements remain open.

Coverage: F06/F09/F11/F16; N01/N02/N03/N04/N06/N08; T01/T04/T05/T06 plus necessary
T12 accounting dependencies. M1 stays `in_progress`; all six G1 suites and G1 stay
`not_run`. D20 permits this source/scripted work; no paid inference, new allowance,
changed health threshold or unchanged Minecraft rerun occurred.

Private source/build/test evidence:
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-live-repair-clocks-01`.

Final audit preserves all460 milestone IDs, checks2,135 local links and confirms
all40 authority tables unchanged at4,887,796 microUSD, eight existing telemetry
holds unchanged, installed client JAR/options unchanged and zero owned runtime.
Private source/build/test archive2026-09-27-m1-live-repair-clocks-01 verifies:
37files/2,568,834bytes, seal
`52d0dc4a246f28412ff1455be633080203c2450798040e5b92527b00cc711efa`.
This pointer follows the archived source/document snapshot; that archive is
immutable. M1/G1 and authentic live-clock/repair settlement qualification remain open.
