# M1 essential-control input dependency — bounded mouse callbacks

September 27, 2026; base `970db49`. Windows, Node24.19.0, Python3.12.14,
Java17.0.20+101, pinned Forge1.19.2-43.4.23 and official E9E FTB-library compile
artifact. Private root:
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-essential-input-01`.

## Outcome and limits

Default attack/use bindings could not be exercised by the keyboard-only input
engine. The candidate now routes bounded left/right mouse-button gestures through
Minecraft's ordinary `MouseHandler.onPress` callback, preserving its key mapping
and Forge input behavior. The existing key session owns modifiers, deadlines,
charged emissions, release and cleanup. The Java HTTP coordinator now carries
explicit device release evidence and visible swing/use/button activity into the
Python evaluator. This is implemented but unverified in Minecraft.

Actual JVM/HTTP and controller/worker/guardian/restart checks pass with synthetic
body/input. They do not execute the Minecraft callback hook. Local swing and
held-item-use predicates do not establish server damage, item consumption, mod
compatibility, intended binding semantics or complete essential-control coverage.
The new JAR is built and archived but not installed. No game/model run occurred.

Affected M1.1b/M1.1c.3.2; F06/F09/F11/F16, N01/N02/N03/N04/N05/N08;
T01/T04/T05/T06 and G1. M1 remains in_progress; complete
T01/T04/T05/T06/T10/T11 and G1 remain not_run. Unrelated M2-M7 is untouched.

## Implementation

- `KeyInputSession.Request` explicitly distinguishes keyboard and mouse devices.
  Existing keyboard constructors remain keyboard. Only mouse buttons0/1 are
  admitted; modifier keys use ordinary keyboard callbacks. Press modifiers first,
  release the button before modifiers, and retain all existing safety cleanup,
  fixed two-second maximum, clock, context and accounting checks. Unsupported
  buttons fail before emission. Failure cannot become a release receipt.
- `MouseInputInvoker` names the exact pinned 1.19.2 callback `m_91530_(JIII)V`.
  Local mapped-JAR signature and MCP-to-SRG mapping were inspected before use.
  The hook is inert until an owned private session calls it; no OS mouse input,
  cursor repositioning, pointer-lock acquisition or raw public input API is added.
- Native admission requires no held mouse buttons. Mouse press requires the
  actual callback hook, active original window/body/connection, no GUI and an
  already grabbed mouse. Missing prerequisites return typed refusal. Release
  remains available after context loss and cleanup verifies buttons are up.
  Direct GLFW mouse polling/custom consumers and GUI pointer operation are not
  qualified by this implementation.
- The settings consumer allowlist includes the actual vanilla attack/use mapping
  objects; their current keyboard or mouse representation drives the gesture.
  Protected mappings remain unmodifiable. Unknown consumers/scancodes remain
  unsupported. No setting is rebound merely to make a test possible.
- Native policy `native-window-key-mouse-callback/4`, `NativeSettingsEffects/4`
  and `NativeInputRelease/2` preserve older identities. New receipts include
  device, code, modifier, reverse release order and callback/clear confirmation.
  New visible states add local swing and button/pointer-lock observations.
  Strict Python readers reject missing activity, device/code confusion, mixed
  profile/receipt versions, invalid booleans and wrong release order. Earlier
  `/2` and `/3` results remain readable only under their original contracts.
- `NativeEffectExpectation/2` adds declared local `attack_swing` and
  `item_use_hold` predicates. Require a new observed swing or item-use hold from
  an inactive baseline, actual held button for mouse gestures, original grabbed
  context and released buttons at settlement. Item use must settle released.
  All previous screen/window/movement bounds remain. No result qualifies input,
  grants resume or implies an essential-control pass. The matrix producer joins
  mouse receipts to planned mouse keys rather than accepting keyboard aliases.

## Executed checks and retained diagnostics

- Offline Gradle `:forge1192-client:test --tests '*KeyInputSessionTest'
  --tests '*SettingsEffectRunTest' :forge1192-client:writeTestClasspath`:
  51 session and18 effect cases pass with zero skips. Mouse cases cover both
  buttons/modifiers, invalid buttons, uncertain press/release and timeout.
- Existing Python wire/producer tests after the production changes:88 pass
  (`unit-01.log`), preserving old profiles and immutable matrix behavior.
- New device/activity cases:26 initially pass; two legacy-expectation rejection
  assertions initially fail because Pydantic wraps the expected typed failure in
  ValidationError. Correct only the expected exception superclass; both pass
  (`device-01.log`, `device-02.log`). No production validation was relaxed.
- Rebuild the changed fixture with `:forge1192-client:writeTestClasspath`.
  `pytest tests/test_native_settings_effects_jvm.py`: six pass (`http-01.log`).
  New attack/use examples traverse production Java coordinator/session/journal/
  HTTP with a synthetic input port, consume primitives, expose held/released
  activity, pass only declared predicates and roll back exact original options.
  Existing baseline, lost-response/status and process-death recovery pass.
- `pytest tests/test_controller_restart_jvm.py -k None`: one pass/three unchanged
  loss variants deselected (`connected-01.log`,11.15s). The complete declared
  keyboard effect matrix survives actual guarded JVM replacement, `/4` decoding,
  produced summaries/restart evidence and native commit/rollback. Body and the
  independent essential-control proof remain synthetic.
- Offline `:forge1192-client:jar`/`reobfJar` passes (`jar-01.log`). Archive
  673,276-byte candidate SHA-256
  `d4799f8239d0b852327d7aa9218388806d75f41f993d793423f332afd96c14e0`.
  ZIP inspection confirms the named invoker/config and no fixture/test classes.
  Packaging is not native hook execution or qualification.
- Ruff for changed Python files and `git diff --check` pass.

Preparation diagnostics: the guessed SettingsRepairAdmission.java and
NativeGameFingerprint.java names were absent; inspected actual source/mapping
paths instead. These did not alter source or authorize an execution retry.
No installed client artifact or historical evidence was changed.

## Next acceptance work

Implement the complete prior-declared essential-control case manifest and source
producer: movement/inventory/attack/use plus fixed Escape and actual host recovery
controls, before and after restart in applicable contexts. Escape is not a fake
persisted KeyMapping; host recovery must use its actual scoped control path.
Missing natural prerequisites remain unverified_context. Connect these checks to
the qualified settings projection, then run authentic complete repair/restart/
rollback and resume with full accounting. Preserve the remaining T05 context/
modifier/hold/failure/isolation matrix and T01/T04/T06/T10/T11 before G1 closure.

All40 authority tables and the five historical capacity holds are unchanged.
D18/D19 remain M0-only; no M1 inference authority, spending, refunds or consumed
permission reuse. Final audit and immutable private custody follow below.

## Sealed custody

Private bundle:311 files /6,179,650 bytes, SHA-256
`027a82e8c38d7e1fb38c0c70500f5301b0ff2c99944f8cc548b359d67e356454`.
Retains source/base/diff,505 compiled-input hashes, candidate JAR, JUnit XML,
actual fixture process journals, all failed/passing logs and durable-state audits.
A final source-only javadoc clarification occurred after compilation; executable
Java is unchanged. All40 authority tables/five holds unchanged at4,887,796microUSD;
459 milestone IDs preserved,1,650 local ledger links resolve. Zero owned/Java
processes remain. This public seal pointer was added after immutable sealing.
