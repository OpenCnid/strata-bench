# M1.1c.3.2 â€” Native release receipts and complete effect summaries

September 27, 2026. Base `16deeef`; Windows, Python3.12.14, Node24.19.0,
Java17.0.20+101 and the pinned offline Forge1.19.2 build. Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-release-evidence-01`.

## Outcome and scope

The actual Python controller â†’ Node worker â†’ Windows guardian â†’ JVM path now
consumes all four declared binding/context/stage effect checks, intended/competing
summaries, explicit local key-release receipts and adopted-restart persistence
before native commit and owned rollback. The JVM fixture uses synthetic game
body/settings/input. The one remaining generic essential-controls proof is
synthetic. This verifies connected evidence plumbing, not Minecraft control
semantics, pool qualification, full repair/resume or T05/G1.

Affected: M1.1c.3.2, F06/F09/F11/F16 and N01/N02/N03/N04/N05/N08;
T01/T04/T05/T06 and G1. M1 remains in_progress. Complete
T01/T04/T05/T06/T10/T11 and G1 remain not_run. No M2-M7 work, game/model execution,
installed client update or inference spending occurred.

## Implementation and invariants

- `KeyInputSession` exposes a release receipt only after all reverse-order key
  releases and cleanup returned successfully through the existing charged safety
  path. Failed callbacks, failed clear or failed journaling cannot yield one.
- `SettingsEffectRun` journals one `input_release` before the first settled
  `released` observation and emits `NativeSettingsEffects/3`. The receipt binds
  key, modifier, release order and callback/clear confirmation. It describes local
  callback and logical/polling cleanup, not physical OS input or verified effects.
- Native input policy becomes `native-window-key-callback-polling/3`, preserving
  the previous identity and requiring new authentic qualification. No new public
  tool/capability, gameplay rearm, raw key access or second input writer is added.
- Python preserves `/2` reading for historical effect predicates but rejects it
  as release evidence. `/3` enforces one receipt, ordering, reverse modifier
  release, no subsequent held state, strict booleans and existing trace quotas.
- `NativeEffectEvidence.effect_checks` consumes the entire immutable manifest and
  terminal stored witnesses under the existing owner/profile locks. It validates
  CAS bytes within the plan's evidence budget, re-evaluates declarations, checks
  exact proof/transaction/settings identities and joins each receipt to the
  actual planned GLFW key/modifier. Missing, foreign, reinterpreted or old-schema
  evidence cannot generate passing summaries. Failed outcomes stay failed.
- All required binding checks and three summaries are returned. The method does
  not generate essential-controls or restart proof, qualify intended semantics,
  waive an empty effect category or authorize resume. The existing independent
  restart producer supplies adopted process/settings evidence.

## Executed verification

1. Offline Gradle `:forge1192-client:test --tests '*KeyInputSessionTest'
   --tests '*SettingsEffectRunTest' :forge1192-client:writeTestClasspath`:
   38 input-session and18 effect-run cases pass; zero skipped/failing.
   `java-01.log` and retained JUnit XML. Includes modifier order, callback/clear/
   journal failure, timeout, cancellation and release-before-settlement.
2. `pytest tests/test_native_settings_effects.py tests/test_native_effect_evidence.py`:
   81 pass (`unit-01.log`), including legacy preservation and malformed/missing/
   duplicated/reordered release receipts. These ran before adding matrix tests.
3. `pytest tests/test_native_effect_evidence.py -k complete_matrix`:
   seven pass (`matrix-01.log`). Missing case, legacy result, wrong physical key,
   failed effect, forged verdict and foreign witness are rejected or retained as
   failures. A passing matrix supplies no essential-control proof.
4. Expanded `pytest tests/test_controller_restart_jvm.py -k None` initially
   failed with LEASE_EXPIRED (`connected-01.log`): the longer test driver had not
   renewed its controller lease during effect capture. No repair deadline was
   extended. Add normal controller heartbeats between bounded operations;
   changed test passes (`connected-02.log`,11.09s). Four declared effects are
   captured across actual old-JVM termination/new-JVM adoption. Charged auxiliary
   inventory gestures prepare each synthetic context; no direct state reset.
   One deliberately lost effect reply reconciles by status with one dispatch.
   Missing matrix, changed declarations and six corrupted adopted-witness cases
   refuse; successful matrix/restart evidence feeds native commit/rollback.
   Original source/admission, same worker, reservation and fixed repair expiry
   remain intact; old/new processes terminate. Three unchanged restart-loss
   variants were deselected rather than rerun.
5. `pytest tests/test_native_settings_effects_jvm.py`: four pass (`http-01.log`),
   exercising production Python/Java HTTP with `/3`, pending/baseline effects,
   duplicate/status reconciliation and actual process-death recovery. Synthetic
   input/body remain explicit.
6. The added missing-essential commit case initially expected the wrong typed
   error. The controller correctly returned EFFECT_VERIFICATION_FAILED before
   native commit (`missing-essential-01.log`); correcting that assertion passes
   (`missing-essential-02.log`). The complete new matrix cannot substitute for
   the still-required essential-control evidence.
7. Ruff for the five changed Python files and `git diff --check` pass.

Preparation diagnostics retained: two guessed Java paths were absent, Windows
`rg` literal wildcard operands failed, and an initial multi-file patch did not
match mixed line endings. The first documentation insertion also stopped on a
nonunique historical table header; it was corrected to target only current
position. No test result was discarded. The lease failure is
retained rather than counted as a successful original run.

## Remaining acceptance work

Essential-control preservation needs prior-declared ordinary-input observations
for Escape, movement, inventory, attack/use and host recovery controls, in their
applicable contexts. Existing sneak/forward observations cannot replace this
set. Qualify the projection and finite key pool; complete the authentic repair
bundle, actual launcher, all consumption/settlement and explicit resume/recovery.
Then complete remaining T05 context/modifier/hold/failure/isolation cases and
T01/T04/T06/T10/T11 before G1 assembly. Historical native04 and native02 stay on
their original profiles; they are not promoted to this new policy.

D18/D19 remain M0-only. All40 authority tables and five historical capacity holds
were rechecked unchanged; no new allowance, refund or replay. Final audit and
source/evidence custody are recorded alongside the sealed private artifacts.

## Sealed custody and final audit

Private bundle:372 files /6,485,270 bytes; SHA-256
`2349042c11805f38bc2c04301f3e1ef8065f90e252c5503bf0b3c7c49c3bb08b`.
Contains source snapshot/diff/base,503 compiled-input hashes, actual JVM/worker
journals and test artifacts, every retained failure, JUnit XML and before/after
authority/process audits. All40 authority tables and five holds unchanged;
4,887,796microUSD exposure unchanged. All459 milestone IDs preserved;1,646 local
ledger links resolve. Zero owned/Java processes remain. The private seal is
immutable; this public seal pointer was added afterwards.
