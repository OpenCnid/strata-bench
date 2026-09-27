# Controller-to-native repair admission

M1.1c.3.2 now connects the controller's actual immutable repair plan to native
settings admission. The connected Python controller, Node worker, Windows guardian
and JVM settings service pass both ordinary and lost-reply cases, followed by
native apply, raw key observation, rollback and process expiry. The body, settings
qualification and input are synthetic. This is a completed admission connection,
not a qualified gameplay repair/commit/restart/resume workflow or complete G1 suite.

## Implemented behavior

`native_control_plan.py` defines the exact private NativeControlTarget/1 and
translation. Pin controller profile/fingerprint/policy and native game/settings/
body identities. The complete plan backup must match the native binding set,
runtime values and unambiguous persisted values. Every physical-key record must
agree with its encoded Minecraft string. Require mutable changed bindings and
the actual before value; preserve native revision/digest separately from the
controller revision. Include the complete planned map for competing and essential
control checks, subject to native consumer restrictions. No encoding establishes
a tested key pool or effect qualification.

`Reconfigurations.admit_native` first obtains actual worker pause evidence. It
checks the existing plan, current adapter state and reserved budget, then persists
the translated admission and a digest of the actual private descriptor before
one bind request. A subsequent call queries status only, including after lost
delivery. Different credentials, profile targets or plans cannot take over the
consumed intent. A private source witness records the returned admission; bearer
credentials are excluded. Confirmation rechecks original ownership and deadline.

Known native recovery, a wrong body, late reply or failed witness publication
retains controller recovery. Uncertain initial delivery retains intent and can
only reconcile status while its original authority remains live. Neither path
releases the worker hold or reserved budget. The teammate remains READY.

Once native admission is recorded, the older generic adapter cannot substitute
its own forward write. A real worker handoff also cannot finish through the older
controller-only readiness proof. The qualified adapter and explicit worker resume
producer remain required; these guards prevent a false end-to-end success while
those implementations are incomplete. Native apply/effect/rollback in the connected
tests are explicit private calls under the resulting admission.

## Executed verification

Profile: Windows, Node24.19.0, Java17.0.20.101 and the existing compiled
SettingsEffectsBridgeFixture/ForgeDevelopmentWorker/3. No game artifact was changed
or installed, no Minecraft run was launched, and no model call occurred.

- Initial collection failed because the new test imported WorkerRepairResponse
  instead of the existing WorkerRepairReply class. The original log remains.
  Correcting that fixture import produced58 passing affected controller/worker/
  reconfiguration tests.
- The two new actual controller→worker→native JVM runs pass, with no skips. One
  loses delivery after the real bind response; the next operation is status and
  the native journal contains exactly one admission. The full planned patch is
  applied, a raw effect observed, original options restored and the owned process
  terminated at expiry. No selected-skill or authentic Minecraft claim follows.
- Two additional publication/deadline fault cases pass in the final13-case
  translation/handoff suite. Failed evidence publication and late replies retain
  recovery; no generic adapter write or controller-only resume is permitted.
- A read-only bytecode comparison checks all129 registered key encodings against
  the exact local Minecraft1.19.2/Forge43.4.23 mapped artifact. The keysym table
  agrees exactly. Artifact SHA256:
  `7498eb8ce73745150b3e3eed8aba0911a16466498cde970995d0036abf2b4dec`.
  This verifies encoding only, not physical input or mod consumer behavior.
- Ruff passes. The initial unused-import lint finding and two Windows wildcard/
  nonexistent source-path search diagnostics are preparation history, not runtime
  acceptance failures. They did not change validation or trigger a game rerun.

Commands: `python -m pytest -q tests/test_native_control_plan.py tests/test_worker_repair.py tests/test_reconfiguration.py`;
`python -m pytest -q tests/test_native_control_plan_jvm.py` with pinned Java/classpath/
Node environment; final `python -m pytest -q tests/test_native_control_plan.py`.
Distinct fixture directories, original collection failure, logs and source are
retained privately under `2026-09-27-m1-native-controller-01`.

## Scope and next acceptance

Affected: M1.1c.3.2, F06/F09/F16, N01/N02/N03/N04/N05/N08 and the settings,
lease/deadline, evidence and budget contracts. T01/T04/T05/T06 depend on this
connection; complete T01/T04/T05/T06/T10/T11 and G1 remain not_run. M1 remains
in_progress. No public keybinding capability or native qualification is promoted.

Next finish the qualified adapter's transaction verification/commit, worker
restart/rejoin and explicit resume or recovery, then authentic charged gameplay
repair and the remaining T05 matrix. Preserve existing authentic preplay evidence,
the full scorer/probe/isolation work and unrelated M2-M7 exclusions.

D20 implementation authority persists. D18/D19 inference authority remains
M0-only. Historical failures, profile identities, budget holds and consumed
decisions remain intact; final durable/process and evidence audits follow below.

Final audit: all40 authority tables unchanged at4,887,796microUSD; all five historical256MiB capacity holds unchanged in current WAL-aware databases. No Java or owned test worker/guardian remains. All459 milestone IDs preserved and1,625 local ledger links resolve.

Private evidence sealed479files/15,121,550bytes at
`ae295fff6d26279bf8c2a2bc5056397cbe1176a67ea96a241a432cda77aac35f`.
The archive retains original collection failure, final fixtures/logs, bytecode
comparison, durable/process audits and source/document snapshots before this pointer.
