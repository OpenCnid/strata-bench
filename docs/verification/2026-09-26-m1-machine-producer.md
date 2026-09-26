# M1.5b.1 native furnace producer candidate

From `63cd6f1`, implement the native producer and private ingestion for the
machine-completion gap identified by the [T10 audit](2026-09-26-m1-scorer-coverage.md).
M1.5b.1 is **implemented_unverified for authentic capture**. M1.5/M1 remain
in_progress; T10/G1 remain not_run. This is only the G1-required M3.1b dependency.
No unrelated M2-M7 work, game dispatch, model call or spending change occurs.

The real controller's40 tables match the prior checkpoint at$4.887796. All old
holds and consumed decisions remain. D18/D19 still authorize M0 only. No owned
runtime exists before or after this source work; Gradle/test processes terminate.
Private raw evidence stays outside gameplay/helper packages and Git.

## Native facts and implementation

Read actual installed bytecode for the exact Thermal Core, Expansion and CoFH
artifacts already pinned by M1.5b. The complete inspection has empty stderr;
inspect the additional internal recipe, manager, inventory and augmentable
classes rather than guessing an API. `SingleItemRecipeManager` constructs a
`SimpleMachineRecipe`, whose resolved input/output/chance/energy facts lack the
public recipe ID. Its resolved output-chance getter accounts for native modifier
and negative-chance semantics. Do not assign a recipe ID from output identity.

[FurnaceCapture](../../java/forge1192-telemetry/src/main/java/io/github/opencnid/strata/telemetry/FurnaceCapture.java)
and its [Mixin](../../java/forge1192-telemetry/src/main/java/io/github/opencnid/strata/telemetry/mixin/FurnaceCaptureMixin.java)
observe `MachineBlockEntity.processFinish`. Entry starts a lifetime; it does not
read an unresolved recipe. The three snapshots surround `resolveOutputs` and
`resolveInputs` after successful `validateInputs`; the latter refreshes the
current recipe. Both original returns close the lifetime. A failed validation
or unsupported narrow profile produces a private refusal, not fabricated output.
Missing/out-of-order callbacks, nesting or changed machine lifetime fail closed.

The producer checks dedicated-server thread, actual caller classes/method,
same exact furnace instance/level/position/tick and native recipe object. It
pins all three installed artifacts, requires the hook marker, reads bounded
plain stacks and empty augments, and records resolved native recipe facts.
It invokes only fixed read accessors; no setter, game command, transfer, game RNG
draw or recipe execution is added. Read-only overhead/parity still needs actual
measurement. Broader recipe, metadata, augment and fluid requirements remain.

New module `strata-forge1192-telemetry/0.3.14`, startup `ServerStarted/15`, policy
`thermal1192-native-furnace-phases/1`. Existing history6 and clock policy remain
unchanged. Raw `NativeFurnaceCompletion/1` contains exactly three states and the
resolved internal facts; `NativeFurnaceRefusal/1` retains typed failures. Both
have empty actor lists and explicit false score/recipe-registration/loaded-code
authority. They are not silently converted into M1.5b's normalized boundary
events, and no scorer schema is widened.

[Strict private models](../../evaluator/src/strata_evaluator/machine_capture.py),
[offline inspection](../../evaluator/src/strata_evaluator/telemetry.py),
[owned-pipe ingestion](../../evaluator/src/strata_evaluator/telemetry_pipe.py)
and the existing startup-prefix verifier recognize only the new declared
profile for machine records. They reject changed/missing pins, old/unsupported
profiles, guessed actors, unknown fields, promoted authority and duplicate
transactions. Existing HMAC/sequence/boot/quota/receipt controls remain. This
implements ingestion; it does not prove authentic integration.

## Executed checks

- Offline Java compile, focused `Furnace*` tests and reobfuscated module build
  pass. Six Java cases: four synthetic phase/lifecycle cases and two installed
  bytecode/compiled-hook checks. Actual pinned `processFinish` has the expected
  validation branch, exact ordered native calls and two returns. All six run,
  none skipped. This is not an actual transformed Forge execution.
- Final Python selection `tests/test_machine_capture.py`,
  `tests/test_script_field_history.py`, `tests/test_gameplay_package.py`:
  **79 pass,3 opt-in native cases skipped**,12.04s. Signed synthetic complete/
  refusal streams, new startup and private prefix, online duplicate/refusal/
  legacy/unsupported/actor/transport controls, historical history4/5/6 and actual
  compiled gameplay package exclusion pass. The package check is not isolation.
- Initial selection also retains **47 passing unchanged telemetry/pipe cases**
  and one opt-in native skip. Those cases are not rerun. Together there are
  **126 distinct passing Python cases**, plus six Java cases. Four opt-in native
  skips are explicitly not evidence of authentic capture.
- Focused Ruff and `git diff --check` pass.

The first Python run had75 passes,1 skip,1 failure and1 fixture error: missing
arguments to the existing scorer registration helper and reference-plan fixture
mutation before the older pipe fixture initialized. Correct argument use and
fixture order; next run has29 passes and1 failure from swapped fixture tuple
positions. Correct that destructuring and add the remaining refusal/profile
cases; final selection above passes. Preserve all outputs/JUnit and earlier test
source. No production gate was weakened to make these tests pass.

Private source/evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-26-m1-machine-producer-01`.
Gradle uses the existing pinned Java17 toolchain, `--offline`, selected
`Furnace*` tests and `jar`; no new installation or account authority is used.
Exact argv/outputs, installed API inspection and built-module hash are archived.

## Required next evidence

First bind the selected internal recipe to its native registration without
guessing an ID, and authenticate the actual transformed producer/callback.
Then use one fresh, bounded protected-server reference with exact module/input/
process custody and preserved failure disposition. Verify genuine resource
effects and refusal paths through the owned pipe before connecting a scorer.
Full continuous machine operation, RF/fluid use, setup/team history, all T10
controls, overhead/mechanics parity and the other G1 gates remain required.
Historical development evidence, paired-capture failures, archive incidents,
old profiles and all consumed decisions remain unchanged.

Final audit:474 source pins,438 preserved unique milestone IDs,1,753 local
links,126 distinct Python passes and6 Java passes; four native opt-in skips.
All40 real authority tables unchanged at$4.887796; no owned runtime/model/game
calls. Source/evidence archive62files/2,640,219bytes, seal
bb2dd188df41fc6369e0acb3a4d3d01ad560542ae5cedf566334c77702cd20ed.
Module0.3.14 SHA25655477d9e33adfaf89d4c0b0ea42219b5e7120b72a5fdc19009356c1cee226d26.
This pointer follows the archived documentation snapshot; authentic capture,
registration/loaded-code authority and full G1 remain unverified.
