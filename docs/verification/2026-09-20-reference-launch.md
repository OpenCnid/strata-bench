# Owned sealed-reference launcher

September 20, 2026. Operator-only. Scope: M0.2c.3b.2; F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13, G0 item 5.
M0 remains in progress, G0 fails and G1–G5 are not run.

## Implemented behavior

The private `strata_evaluator.reference_launch` CLI consumes the existing sealed
reference's one-use preflight reservation and journals intent before dispatch.
It launches through the existing no-breakaway, kill-on-close Windows Job Object
bootstrap. Failure, partial execution and missing evidence remain uncertain;
there is no automatic restart or replacement grant.

Production mode admits only the inspected official E9E 1.27.0
serverstarter 2.4.0 artifact and configuration digest. The configuration uses
the existing 2–5 GiB headless server profile, current working directory and
PATH-selected Java, with autoRestart and ramDisk disabled. Caller-supplied
arguments or changed bootstrap/configuration pins reject before reservation.
This is an explicit narrow profile, not an arbitrary YAML semantic validator.

The launcher verifies and holds Windows deny-write leases on pinned executable,
module, complete JRE/mod/library/server-script/startup-script inventories,
bootstrap/configuration, private launch authority/key/plan and process bootstrap.
It re-enumerates selected trees while running. Inputs are operator-only and the
child receives a minimal explicit environment. Existing file/inventory/process
quotas and guard thresholds remain unchanged.

Telemetry 0.3.4 emits `ServerStarted/5`. Its PID, process creation time,
executable, actual game/world/module paths, loaded module digest, online mode
and port are native observations, not values copied from the launch plan.
The controller authenticates this record and compares its identity with the
retained OS handle of a member of its own Job Object. Holding the handle avoids
trusting a reused PID. The complete stream must preserve the same startup
identity and terminate normally; all observed Job members must be signaled and
account for the Job's total member count. Logs remain bounded and private.

Craft-reference import accepts a tracked launch only after its durable STOPPED
record matches the actual spool and startup observation. An uncertain dispatch
cannot fall back to weaker untracked admission. Historical untracked imports
retain their prior report shape and remain unqualified. No scorer state or
credit is created. The thirteen public record types are unchanged.

This does not exclude concurrent writes to the mutable world/configuration,
qualify general process isolation, establish native setup/admin/team facts,
prove a clean recovery set or pass the 500-ms guardian requirement. The complete
owned setup authority and scoring controls remain open.

## Focused verification

Windows x64, Python 3.12.14, pinned Temurin 17.0.20.1+1 and Gradle 8.8 /
ForgeGradle 6.0.42. Synthetic JVM fixtures use the actual production signing and
native process observation code; they do not run Minecraft.

| Executed check | Result |
|---|---|
| Reference launcher, fixture seal, authentication, telemetry and process Python suites | 104 pass, zero skipped, 19.63 s |
| Additional production bootstrap-admission negatives | 3 pass, 18 deliberately deselected, 0.60 s |
| Targeted telemetry Gradle tests/classpath/JAR | 22 XML tests, zero failures/errors/skips; candidate 0.3.4 built |
| Compiled gameplay package exclusion | 1 pass, 0.36 s; evaluator files remain excluded |
| Targeted Ruff and whitespace checks | Pass |

Executed Python commands used the existing private Python environment,
`PYTHONPATH=src` and explicit `STRATA_TELEMETRY_TEST_JAVA` /
`STRATA_TELEMETRY_TEST_CLASSPATH` pointing to the pinned JVM and generated test
classpath. The affected command was:

```text
python -m pytest tests/test_reference_launch.py tests/test_craft_reference.py tests/test_telemetry_auth.py tests/test_telemetry.py tests/test_processes.py -q
python -m pytest tests/test_reference_launch.py -k real_pack_profile -q
python -m pytest tests/test_gameplay_package.py -q
gradlew.bat :forge1192-telemetry:test :forge1192-telemetry:writeTestClasspath :forge1192-telemetry:jar --no-daemon --console plain
```

Final changed-document validation resolved 898 local links. Targeted Ruff and
`git diff --check` passed after the final source/docs changes.

The actual JVM positive case binds the retained process/world/artifact, stops
normally, imports its three signed records and rejects reuse. Wrong world,
hung shutdown, missing final record, early exit, input substitutions and signed
identity mismatches fail without replay. The empty JVM fixture fabricates no
craft candidate or score.

Two initial test failures are retained privately. A forced-stop sample was
initially classified by incomplete process history before lifecycle failure;
the failure ordering now reports lifecycle first, while retaining all process
evidence and success requirements. An early exit can precede native identity
observation, so its test now permits the applicable typed missing-evidence
failure. Neither change permits success or relaunch for these samples.

Private synthetic/build evidence:
`C:/Users/Darian/.strata/evidence/2026-09-20-reference-launch-01`.

## Authentic changed-profile reference

One actual CLI run used a fresh private clone of the already stopped E9E 1.27.0 /
Minecraft 1.19.2 / Forge 43.4.23 reference. Changes were telemetry 0.3.3 → 0.3.4,
loopback port 25568 → 25570, setup-bound authority v2 and the new owned launcher.
There was no client connection, setup command, model request or shared-desktop
input. The existing 2–5 GiB JRE 17 profile and official bootstrap were retained.

Preparation copied the complete 104-file selected world into the independent
private seal and pinned 1,540 immutable software files. It retained a manifest
of 18,226 original source files. After execution the independent audit rehashed
every recorded original source and immutable launch file: all unchanged.
The new clone's ordinary server save remains separate from the sealed baseline.

The actual native PID/start/executable matched its retained OS handle. Native
game/world/module paths, module digest, online mode and port matched the plan.
All six Job members were retained and signaled; active count was zero. The
server stopped normally without forced termination, retaining 13 signed records,
209 final server ticks and 207 sampled ticks / 10.3133128 sampled seconds.
Launcher elapsed time was 216.437 s; the surrounding CLI took 221.235 s.
These wall times include startup/stop work and are not replaced by sampled tick
time. This was not a 500-ms guardian trial.

The complete stream joined the stored seal and launch record. It contained no
craft witness or connected-avatar tick, produced zero candidate output and
remained unscorable. Identical import created no new event; a second dispatch
attempt was denied before a process could start. The audit's 19 checks passed
and no Java process remained. This qualifies only the named launch-binding
reference, tracked as M0.2c.3b.2a; full .3b.2 stays in progress.

Private bundle:
`C:/Users/Darian/.strata/evidence/2026-09-20-reference-launch-live-01`.

| Pin | SHA-256 |
|---|---|
| Telemetry 0.3.4 JAR | `fb587b17128111ead0f5ee85808728fd84aae5ccde09f01aeddbbf9c5ef3ed17` |
| Reviewed serverstarter 2.4.0 JAR | `70bec2771fd000209a8778b8457f231bf8e6244bb3d8dba6bb739c3662e099b4` |
| Reviewed bootstrap YAML | `4759535f6bb6559dc3486a7a51ff1fbe270880f054877caba395e19c8af4d92a` |
| Signed stream | `e06d6260b768109c0cd8de6122766c288188235ed9264e3f4e6d35b6d1f0ca1c` |
| Independent audit | `5387799309b5b1da260e7b3d74c586b12dbd5e6495eeb8f2f1cf36aa8601b966` |

Continue with native setup/admin/mode/pack-team facts and authentic scorer
controls (.3b.3), plus exclusion of concurrent mutable-world/config writers
(.3b.2b). Neither signatures nor registered supporting-file hashes prove those
facts. Do not repeat this unchanged launch-reference trial.

The original allowance was rechecked read-only: schema 2, $10 cap, one migration,
one UNSETTLED request, zero valuations and $0.7554 aggregate held once. No reset,
refund or model dispatch occurred. Preserve all original 500-ms failures,
five effective-file failures, loopback failures and Mineflayer/E9E incompatibility.
M0–M6 remain required; M7 and other extensions retain activation conditions.
