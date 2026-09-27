# Worker-owned native settings admission

M1.1c.3.2 now binds the private native settings transaction and effect route to
the same fixed worker repair plan. A connected Python/Node/Windows guardian/JVM
test pauses the actual worker, binds the plan, applies one patch, observes a key
effect, rolls back exactly and confirms expiry cleanup. Body, settings and key
input in this test are synthetic. The separately sealed Minecraft preplay cycle
remains its own evidence; this change does not complete the gameplay repair
workflow or any aggregate G1 suite.

## Behavior and limits

The explicit `strata.settingsRepairOwner=true` mode requires the private effects
profile. NativeSettingsRepairAdmission/1 pins WorkerRepairPlan/1, the settings
fingerprint, exact revision/digest-bound patch and permitted effect bindings.
Native admission requires the same campaign/avatar/epoch/lease, a healthy fenced
lane, known completed/cancelled actions and unchanged connection generation.
It journals admission before enabling forward work. Duplicate identical binds
return state; changed plans cannot extend expiry or replace the patch.

Both wall and monotonic deadlines apply. Changes of body/connection, interruption,
expiry and reopening retain recovery; a new executor epoch or omitted mode flag
cannot rearm the held lane. Effects must name the admitted plan and binding, and
pending checks must name its transaction. Actual effect verdicts remain false.
The existing preplay route rejects owned admission without its explicit mode.

After expiry, compare-and-swap rollback of the owned transaction remains possible
as bounded cleanup. It records settings restoration and charged native primitives,
retains recovery and never returns gameplay authority. Resume is always false.
The Python client strictly joins the complete returned admission and retains the
transaction ID on uncertain binding delivery; it does not replay mutations.

This endpoint trusts its private operator caller to supply the reviewed native
translation. It does not reconstruct the full controller ControlPlan from its
digest. Controller-to-native profile/patch translation and durable handoff still
need implementation. Native state must be joined separately: a worker pause alone
cannot certify that the native repair remains live. Qualified commit, restart/
rejoin, explicit resume, final isolation and authentic gameplay repair remain open.

## Executed checks

Profile: Windows, Node24.19.0, Java17.0.20.101, offline pinned Gradle dependencies,
ForgeDevelopmentWorker/3, production Python/Java HTTP and journal code with the
SettingsEffectsBridgeFixture synthetic body/settings/input. No installed game
artifact changed and no Minecraft or model call was launched.

- Initial Java compilation and focused NativeRepairAdmissionTest,
  SettingsEffectAdmissionTest, SettingsEffectRunTest and GameActionLaneTest pass.
- A subsequent targeted Java run passes NativeRepairAdmissionTest and
  SettingsStoreTest. Its NativeSettingsProtocolTest selector matched no separate
  test class; no such result is claimed. The final changed admission suite passes,
  including rejection of connection drift before binding the old lease.
- Initial affected Python/native-effect/JVM checks:51 pass. Final
  `python -m pytest -q tests/test_native_repair_admission_jvm.py`:5 pass, no skips.
  These cover exact patch/effect ownership, expired forward work plus rollback,
  recovery with the mode flag removed, separate preplay rejection and the actual
  worker-to-native path with guardian cleanup. The tests use retained fresh
  fixture directories rather than overwriting prior evidence.
- Ruff passes on all three affected Python files. An initial duplicate-target
  patch-tool rejection occurred before editing and is retained as a preparation
  diagnostic; it is not a runtime result. No test failure occurred in these runs.

Commands use `java/gradlew.bat -p java --offline :forge1192-client:test` with the
named class selectors, the existing pinned Java/classpath/Node environment and
the pytest command above. All logs and fixture artifacts are private in
`2026-09-27-m1-native-repair-admission-01`.

## Remaining acceptance and authority

Affected scope: M1.1c.3.2, F06/F09/F16, N01/N02/N03/N04/N05/N08, settings/lease/journal/budget
contracts and T01/T04/T05/T06 with G1. M1 remains in_progress; complete
T01/T04/T05/T06/T10/T11 and G1 remain not_run. No new public settings capability,
protected scoring authority, scientific claim or unrelated M2-M7 work is added.

Next implement the controller-native translation and durable admission join,
then qualified commit, worker restart/rejoin, explicit resume or recovery and
the authentic charged gameplay repair workflow. Preserve the remaining T05
context/modifier/hold/failure/isolation matrix and the other G1 suites.

Read-only WAL-aware checks show all40 authority tables unchanged at
4,887,796microUSD and all five historical256MiB capacity holds unchanged. D20
implementation authority persists; D18/D19 remain M0-only inference authority.
Original failures, consumed decisions and prior profile identities remain intact.

Final source review preserves all459 existing milestone IDs; all1,622 local ledger links resolve. No Java process remains. The first empty process-list pipeline created no file; the explicit array audit records an empty list without rerunning any game or test.

Private evidence sealed:162files/3,111,857bytes,
`fb5fe112785d0415f31d434d41c04c8d6ab47c37e9a72d574d2657785494eee0`.
The archive includes source/document snapshots before this seal pointer, logs,
JVM result XML, retained synthetic fixtures and read-only accounting audits.
