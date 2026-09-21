# Native setup observations and registered pack-team checks

September 20, 2026. Operator-only. M0.2c.3b.3; F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5.
M0 stays in progress, G0 fails and G1–G5 are not run.

## Implementation

Telemetry 0.3.5 adds `SetupCapture`, private `NativeSetupSnapshot/1` records and
the declared `native-e9e-setup-observation/1` capability in `ServerStarted/6`.
It reads the native dedicated-server game modes, difficulty, hardcore flag,
world command permission, command-block/RCON enablement and operator levels.
A counter records observed Forge `CommandEvent` attempts, including failed
attempts; raw command text, arguments, account names and credentials are omitted.
This counter does not cover all direct mod/admin/world mutation routes.

Exact installed KubeJS, Rhino and FTB Teams artifacts gate the optional pack
observations. The code reads the loaded KubeJS `BuiltinKubeJSPlugin.GLOBAL`
mode flags and startup/server script-error counts. It does not execute JavaScript
or infer loaded mode from a file. For an acting player it reads the existing FTB
player-to-actual-team mapping, team ID/type, member IDs and rank; member output
is sorted and bounded at 128. Unknown artifacts, missing managers/teams or
unsupported values remain explicitly unavailable.

The inspected installed bytecode matters: `TeamManager.getId()` creates an ID
when absent, so it is deliberately excluded. The selected UUID overload of
`getPlayerTeam` only reads the existing map and `actualTeam`. All reflective
classes/methods are fixed in source; no caller supplies names or code. Startup
requires the manager to belong to the same native server. No team is created.

The first completed server tick emits a startup point. Each craft begin/end
has a preceding point on the same server thread. The private importer verifies
startup timing, exact adjacency, actor/transaction/tick scope, no duplicates and
monotonic command count. Existing resource checks remain: the extra record
between callback and end is accepted only as a fully validated end observation;
arbitrary sequence gaps still fail. The thirteen top-level records are unchanged.

`PrivateCraftReferencePlan/2` explicitly registers each agent's expected native
team. Its complete digest enters the existing seal/authority. Version-2 imports
require the new source capability and points. Normal/inconsistent/erroring pack
mode, administrator/creative/command exposure, wrong/invited/missing teams,
missing membership, changed points and unavailable startup manager produce no
candidate output. Distinct transactions remain distinct; identical imports
remain idempotent. Version-1 plans and old signed streams stay separately
readable, without retroactive native-team qualification.

Neither matching points nor the registered native team proves continuous
history, fixture correctness, absence of direct admin modification, file/process
isolation or mechanical parity. No `Scorer` state is updated. Reports retain
`continuous_history_proven=false`, `setup_mechanics_qualified=false` and
`scoring_eligible=false`.

## Corrections and focused verification

Review found that version-5 startup parsing accepted launch observations but
excluded craft boundaries through a stale class allowlist. The parser now
accepts the supported startup-model family and a signed version-5 resource
regression passes. This does not change the earlier empty launch-reference
result or retroactively prove a version-5 authentic craft.

The module's prior `mods.toml` still reported 0.3.2 while the version-0.3.4 JAR
and telemetry payload used 0.3.4. The Gradle resource task now expands the module
version from `project.version`; the new built JAR was inspected and reports
0.3.5. Historical artifacts and their mismatch remain retained.

Windows x64 / Python 3.12.14 / pinned Temurin 17.0.20.1+1 / Gradle 8.8 and
ForgeGradle 6.0.42:

| Check | Actual result |
|---|---|
| Affected setup/reference/resource/telemetry/authentication/launcher Python run | 156 pass, 1 test-expectation failure, 23.54 s; failure expected `Fault` where Pydantic wraps the rejected roster in `ValidationError` |
| Final native setup suite after that expectation fix and startup-manager/two-transaction controls | 29 pass, zero skipped, 4.79 s; actual JVM signer included |
| Targeted telemetry Gradle compile/test/classpath/JAR | Build succeeds in 27 s; 25 XML tests, zero failures/errors/skips |
| Built module metadata | Expanded 0.3.5, no unresolved template |
| Targeted Ruff / whitespace | Pass |
| Compiled gameplay package exclusion | 1 pass, 0.30 s |

Final targeted Ruff and whitespace checks pass; 909 changed-document local links
resolve. A read-only accounting check retains the original $10, $0.7554 hold,
one migration, zero valuations and uncertainty. No Java/Python server or fixture
remains after the audit. The model request was not replayed or refunded.

The affected command was `python -m pytest tests/test_setup_facts.py
tests/test_craft_reference.py tests/test_craft_witness.py tests/test_telemetry.py
tests/test_telemetry_auth.py tests/test_reference_launch.py -q`; the final focused
command was `python -m pytest tests/test_setup_facts.py -q`. Both used the explicit
pinned Java/classpath opt-in. Gradle ran `:forge1192-telemetry:test`,
`:forge1192-telemetry:writeTestClasspath` and `:forge1192-telemetry:jar` with
`--no-daemon --console plain`.

The initial native positive case exposed the extra-record resource sequencing
gap; the implementation now validates that record rather than dropping resource
scope checks. A negative fixture initially rolled ticks backward before its
intended adjacency check; the fixture now preserves tick order so it exercises
the intended rejection. Both failures remain part of the development record.

Synthetic mode flags, rosters, saves and events are fabricated. The actual JVM
signer exercises production framing, claim and MAC code; it is not a Minecraft
or FTB team test. Evidence stays private in
`C:/Users/Darian/.strata/evidence/2026-09-20-native-setup-01`.

## Authentic startup reference

One actual operator CLI run used a fresh private clone of the stopped owned
reference, changing server telemetry 0.3.4 → 0.3.5, loopback port 25570 → 25572
and the one-use private scope. The official E9E 1.27.0 / Minecraft 1.19.2 /
Forge 43.4.23 bootstrap and existing JRE 17 2–5 GiB headless profile remained
pinned. No client, model, setup command or shared-desktop input was used.

The signed native startup point observed:

- Loaded expert mode, expert=true, normal=false; zero startup/server script errors.
- Default and world survival mode, normal difficulty, hardcore=false.
- World commands, command blocks and RCON disabled; no operator levels and
  zero observed command attempts at that point.
- The installed FTB team manager bound to the actual server. No actor was
  connected, so no actor-specific team, rank or craft was observed.

The independent audit compared those server facts with the sealed `level.dat`,
server properties and operator-list copies. All 27 checks passed. The actual
process/world/module binding passed; all six owned Job members terminated
normally. The stream retained 14 signed records, 208 final / 206 sampled ticks
and 10.2690427 sampled seconds. Launcher elapsed 194.687 s; surrounding CLI
199.000 s. The 104-file world seal remains independent from the new save;
all 18,225 original source files and 1,540 immutable launch files were rehashed
unchanged. Identical import added no event and a second dispatch was denied.
No Java process remained.

Private bundle:
`C:/Users/Darian/.strata/evidence/2026-09-20-native-setup-live-01`.

| Pin | SHA-256 |
|---|---|
| Server telemetry 0.3.5 JAR | `8464ee7d9e9020a8fe22af1138d150a6e32d1e0bdce36767f9e27e071d3b4caa` |
| Signed stream | `70e3ed2f6f74403719122ecfcdfaef283f26dcf3b8f55c72d5b9b476c1e4416f` |
| Independent audit | `6f4ab9fdcb7c7f86d85bdafad4148da08d614cf9d35ae8dc4dc8f8a993f4eb0b` |

This verifies the named startup observations only. Actor-specific native FTB
lookup, actual before/after craft observations and version-2 joint controls still
need an authentic client trajectory. The headless reference uses the existing
version-1 fixture plan and earns no candidate or score. Source/synthetic tests
exercise version 2; they are not authentic team evidence. Client configuration
diagnostics remain pinned to the earlier 0.3.2 profile and are not qualified by
this server-only module change.

Next continue M0.2c.3b.3 with a sealed version-2 client craft reference and its
positive/negative controls; retain .3b.2b's mutable-file ownership gap, complete
setup/mutation-history proof, instrumentation parity and isolation requirements.
Do not repeat the unchanged startup trial. Keep the unresolved $0.7554 model
hold, all 500-ms failures, five effective-file failures, loopback failures and
Mineflayer/E9E incompatibility. M0/G0 and the full required M0–M6 / conditional
M7 scope remain unchanged.
