# M1.2b native settings request parity

The actual Java NativeSettingsProtocol now rejects empty before/after binding
values at request admission, matching Python NativePatch. The shared corpus
reproduces two failures on the original Java source; both are fixed. This closes
a named T01 translated-settings defect without advertising gameplay settings.
M1.2b/M1 remain in_progress; T01/T05/G1 remain not_run.

Affected F06/F16/N01, SPEC8/9/10/16, M1.1a.2.2 and M1.2b. Base39a0b3e.
[Java validator](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeSettingsProtocol.java),
[shared corpus](../../tests/fixtures/native_patch_semantics.json),
[Python cases](../../tests/test_native_patch_semantics.py), and
[Java cases](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/NativePatchSharedContractTest.java).

## Actual checks

The 22 shared cases cover valid ASCII binding strings, empty/overlong/unchanged
values, one-to-32 change cardinality, revision range/types, digests, IDs and unknown
fields. They compare the actual Python patch model and Java request validator;
no simulated game effect is treated as authentic. Java's original run has20
passes/two failures, exactly the empty before/after cases. Source, log and XML
are retained. After the fix all22 pass, plus five SettingsHttpBridgeTest cases.

Python: pytest tests/test_native_patch_semantics.py tests/test_native_settings.py
passes37 cases. With the freshly generated test classpath and pinned Java17,
pytest tests/test_native_settings_jvm.py passes all four explicit integration
cases: transaction/query/dedup/rollback, crash/new-session recovery, foreign-edit
refusal and lost-acknowledgement handling without a repeated write. The production
Java store/HTTP and Python client run; the binding runtime is synthetic. These
are41 distinct Python and27 final Java cases, no skips. Existing Gradle
8.8 deprecation warnings remain. Changed-file Ruff and whitespace checks pass.

Java command: gradlew.bat --offline :forge1192-client:test --tests
io.github.opencnid.strata.client.NativePatchSharedContractTest --tests
io.github.opencnid.strata.client.SettingsHttpBridgeTest
:forge1192-client:writeTestClasspath. Uses the previously acquired, hash-checked
FTB library and cached locked dependencies. No download, installed game artifact
replacement, game process or model call. Application class bytes changed; old
native evidence does not qualify this new build. A future authentic profile
must pin its complete artifact and integration evidence.

## Dependency reconciliation and next deliverable

The remaining full T01 native/settings surface depends on T05's unfinished
capable extension. The current native settings client advertises supported=false
and receipts remain committed=false. Source-bound Curios writes, cold readback
and two real crash boundaries have historical evidence; intended/competing
ordinary-input effects remain M1.1b/not_started. Repeated generic contract audits
cannot supply that missing behavior.

Next implement M1.1b's qualified ordinary-input/effect boundary, beginning with
the exact source-bound Curios consumer and its competing controls. Build the
complete T05 case matrix around the actual input path, contexts/modifiers,
release/timeout, persistence/restart and rollback before selecting authentic
cases. Preserve protected/unknown consumers, unsupported key/backend refusals,
action fencing, charged reconfiguration and isolated client ownership. Existing
shared-desktop input pause remains; use the authorized isolated native route.
No unqualified commit or general keybinding support may be advertised.

T01 remains open for remaining reference-bearing services, path cases and final
translated native/settings reconciliation against that resulting interface.
Existing checkpoint/skill/probe reference code and evidence are carried forward;
this report does not claim new coverage for them. Then complete matched probes,
consolidate T10 and qualify final T04/T06 before G1. This refines dependency order
in the [closure path](2026-09-27-m1-closure-path.md), not acceptance scope.

D20 implementation authority persists. D18/D19 remain M0-only spending authority.
Retain all original failures, decisions and three distinct telemetry holds.
Final custody/accounting checks and the private evidence seal follow below.

Final audit: nine changed-file pins, 458 preserved milestone IDs, 1,820 local
links, all40 authority tables unchanged/4,887,796microUSD and all three original
256MiB holds preserved. Prior seals verify; zero Java processes remain. Archive
2026-09-27-m1-settings-contracts-01 verifies at27files/1,835,659bytes, seal
`9ca72bfa5a155df007407d222c63ac63710558376a7143e6c4b9fc38675d467c`.
This pointer follows the archived documentation snapshot. T01/T05/G1 not_run.
