# Private script-origin FTB field observations

M0.2c.3b.3c.6 advances G0 item 5 and its parent F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24 and T01/T06/T07/T10/T13 coverage.
Full private scoring remains unqualified.

The exact pinned FTB Teams 1902.2.14-build.123 exposes PlayerTeam.actualTeam
and TeamManager.INSTANCE as public mutable fields. A script can change the
effective team lookup without entering the observed maps. Exact Rhino
1902.2.2-build.280 bytecode identifies one Field.set site in JavaMembers.put
and two Method.invoke sites in MemberBox.invoke, including its access-retry
branch. Existing setup artifact hashes pin both dependencies.

Telemetry 0.3.11 / startup12 / history4 observes those sites before execution.
Field writes declared within the FTB Teams data package increment a sticky
counter. Read calls and unrelated field writes do not. Explicit nested
Method.invoke calls are inspected for up to sixteen steps; a deeper unresolved
chain increments a separate overflow route, which rejects private candidate
credit. No fields, values, receiver objects or reflection arguments enter
telemetry. Actual invocation stays in the original transformed class so
caller-sensitive access checks are preserved.

The startup support record requires both actual Rhino hook markers. The private
admission and importer require the complete seventeen-route history, exact
module/schema/policy agreement, monotonic counters and the sealed policy.
An observed write remains disqualifying after the original value is restored.
Policies1–3 retain their original meaning and validation; no old evidence is
upgraded. Arbitrary native/mod field instructions, method handles, pre-activation
history, complete custody and mechanical parity remain unqualified. Complete
history and scoring flags remain false.

## Source verification

The new fixtures caught an incorrect copied import and omitted startup12
initialization branches. Those were corrected before live preparation.
The final JVM-enabled affected selection passes **289 Python cases**, with one
existing explicit sandbox-group skip:

```text
pytest tests/test_script_field_history.py tests/test_team_map_history.py tests/test_global_setup_history.py tests/test_setup_history.py tests/test_setup_facts.py tests/test_setup_control.py tests/test_craft_reference.py tests/test_reference_launch.py tests/test_telemetry.py tests/test_telemetry_auth.py tests/test_telemetry_pipe.py tests/test_telemetry_clocks.py -q
```

`STRATA_TELEMETRY_TEST_JAVA` selects Temurin 17.0.20.101 and
`STRATA_TELEMETRY_TEST_CLASSPATH` points to the generated test-classpath file.
The offline Gradle test/JAR/writeTestClasspath build passes **40 Java tests**.
The existing map test also executes field checks under the single live monitor:
direct and reflected writes, static fields, primitive setters, nested reflection,
unrelated writes/reads, failed writes and excessive nesting. Repository-wide
Ruff passes. These are source and fixture checks, not game evidence.

Candidate JAR SHA-256:
`8d4e2214072eb90a493d8daddd8bde885bd15f834d7e8b560bc067aa34ebb546`.

## Authentic control

The fresh `2026-09-23-script-field-history-live-01` headless E9E 1.27.0 /
Forge 43.4.23 / Temurin 17.0.20.101 control passes **44/44 independent audit
checks**. Its sealed operator script changes/restores actualTeam directly and
through Field.set, then changes/restores the manager singleton. Six ordered
script assertions confirm the temporary lookup effects and restoration. These
are runtime assertions, not independent intermediate saved-state snapshots.
Signed telemetry retains exactly six field writes and one normal stop; every
other mutation route, including reflection overflow, remains zero. Both Rhino
hooks are present at startup, and the initial history is clear. No existing
successful map/global control was repeated.

The audit verifies the authenticated chain, exact source/runtime pins, consumed
launch authority and replay refusal, idempotent import, and unchanged original
18,225-file installation and all 39 accounting tables. The six server processes
and ten outer processes are terminal without forced termination. Server lifetime
is 163.859 seconds; outer lifetime is 167.890 seconds. The terminal callback
reports 210 server ticks and 14.886997900 seconds between the start/stop callbacks;
this does not qualify full active time, avatar ticks or save custody. No player
connection, real model request or shared-desktop input occurred.

The private seal was constructed and its complete file inventory rehashed:

- Seal: `71da47dc4e91c3afdb6d28cc6b9af4665d8cd3afe9a734aa3393f7b6c3e6f7d2`
- 317 files / 44,502,313 bytes
- Audit: `dca4300a5f0f60c67a79a11105719f9db7849857a387a035bafc57194336aad6`

M0.2c.3b.3c.6 is verified only for this script-origin observation contract.
Native/mod field instructions, method handles, pre-activation history, custody,
mechanical parity and complete private scoring remain open. Next establish the
remaining field mutation coverage under the exact pinned runtime before joining
the scorer controls with saved-resource evidence. M0 is in_progress; G0 remains
fail. Original exposure remains $1.795559; the unknown model request, budget
reservations, continuing D18 approval and later M1–M7 roadmap are preserved.
