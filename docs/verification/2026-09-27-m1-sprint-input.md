# Essential sprint input before authentic qualification

M1.1b/M1.1c.3.2 remain in_progress. Inspection found a necessary missing positive
case: the prior single-binding motor could press sprint but could not supply
forward movement at the same time. A full essential-controls pass therefore
could not be obtained from that path. This change adds a bounded source-bound
sprint/forward gesture before selecting the next authentic qualification run.
No full T05 or other G1 suite is closed; G1 remains not_run.

Affected contracts: F06/F16, N01/N02/N05/N06, SPEC8.2 ordinary effects and essential
controls. Existing lane exclusion, cancellation, expiry, cleanup charges and
protected keymap requirements remain binding. T12 accounting implications remain
a required dependency, with full repair settlement/resume still incomplete.

## Supported candidate behavior

Policy `native-window-key-mouse-sprint-companion/6` resolves the actual vanilla
sprint and forward KeyMapping objects. Both must be keyboard keysyms with no
configured modifier; the current screen must be in-game. Keys must be distinct,
and forward cannot itself be a modifier. Unsupported arrangements refuse before
pressing. No remapping, arbitrary key list, helper tool or shared-desktop input
is introduced.

The ordinary callback/polling session presses sprint then forward with the
appropriate held modifier flag when sprint uses Ctrl/Shift/Alt. It releases
forward before sprint and clears logical input. Both callbacks, held ticks and
cleanup are charged. The existing three-event safety reserve covers two key-up
callbacks and logical cleanup. Callback/journal failure, cancellation and timeout
still attempt complete cleanup; an ambiguous release cannot become a pass.

NativeSettingsEffects/5 retains single-device receipts and additionally admits
NativeInputRelease/3 with both physical keys and reverse release order. Older
effect profiles reject paired receipts. The essential manifest resolves its
forward companion before dispatch; capture and offline reconstruction join both
keys to the immutable plan. Directed motion and newly observed held sprint are
still required. Generic binding summaries reject an unverified companion.
NativeSettingsProjection consumes /6 qualification separately from /5; neither
profile gains qualification merely from this implementation.

## Executed evidence

Private root: `2026-09-27-m1-sprint-input-01`, operator/SYSTEM only. Python3.12.14,
Node24.19.0, Temurin17.0.20+101 and the pinned offline Forge1192 dependencies.

- Initial offline Gradle compile fails because a reassigned modifier variable
  is captured by a lambda (`java-01.log`). Replace it with one final expression;
  retain the original diagnostic. No native run occurred on that failed build.
- Offline `:forge1192-client:test --tests '*KeyInputSessionTest' --tests
  '*SettingsEffectRunTest' :forge1192-client:writeTestClasspath` then passes
  69 input-session and18 effect-run cases, no skips (`java-02.log`). New cases
  cover order, accounting/callback failures, invalid companions, cancellation
  and timeout, alongside changed shared-motor regressions.
- Affected Python wire/effect/essential tests, new paired-input tests, real
  JVM/HTTP fixture cases and the selected connected restart test pass161 cases,
  with three unchanged restart-loss variants deselected (`affected-01.log`,
  26.24s). Actual coordinator/session/journal HTTP produces a paired receipt,
  visible synthetic sprint/movement, exact identity joins and owned rollback.
- Extend the connected controller/Node/Windows guardian/JVM case to declare and
  capture sprint before and after actual process replacement. It passes once
  (`connected-02.log`,14.76s), three unchanged loss variants deselected. Four
  essential cases now pass in this fixture: Escape and sprint at both stages.
  Missing cases remain unverified_context; the full essential proof, game body
  and qualification reports remain synthetic. Commit/rollback does not resume.
- Offline `:forge1192-client:jar`/reobfuscation passes (`jar-01.log`). Archive
  674,241-byte candidate SHA-256
  `e2c718506b078f529e92fd25e31068af7377b079e1b591b2488bf98f9797c41d`.
  It is not installed or authentically qualified. Changed-source Ruff and
  `git diff --check` pass.

## Next acceptance work

Prepare the exact /6 native essential-control qualification procedure, with
declared movement directions, natural or declared public-preplay prerequisites,
actual attack/use, sprint, inventory/Escape, required contexts and independent
destructive recovery. Include same-server restart and owned restoration. Inspect
the prior authentic cycle driver and reuse its licensed client/server/process
custody, while preserving its /2 evidence and all failed samples. Do not merely
repeat its narrower Curios cycle and call the new profile qualified.

Then consume authentic qualification in the connected gameplay repair workflow,
complete real launcher orchestration, all cost/clock joins and explicit resume.
Retain the remaining T05 cases and full T01/T04/T06/T10/T11 closure work. No
Minecraft/model run, new inference allowance, installed artifact modification or
historical hold release occurred. D18/D19 stay M0-only; unrelated M2–M7 remains
outside scope. Final durable audit/sealed custody follow below.

## Sealed custody

Private archive:404 files /7,469,054 bytes, SHA-256
`9bfd717a64614749fd305ac2156aa8c77fd61909d3bd93d8f3852a027beaea97`.
Contains source/base/diff,534 compiled-input hashes, candidate JAR, JUnit XML,
failed/passing logs, actual fixture journals and private qualification inputs.
All40 authority tables and five historical holds are unchanged at4,887,796microUSD.
All459 milestone IDs are preserved and1,661 local ledger links resolve. Installed
client/options pins are unchanged, the candidate contains no fixture/test classes,
and zero owned/Java processes remain. This pointer follows immutable sealing.
