# Native effect and restart evidence producer

M1.1c.3.2 now derives per-binding ControlCheck evidence from captured native
effect observations and a restart-persistence check from the controller's adopted
replacement witness. The connected controller/worker/guardian/JVM test consumes
both kinds of generated evidence before commit and rollback. Body/input remain
synthetic in that integration test; the remaining checks still come from its
explicitly synthetic producer. This is partial verification integration, not a
full qualified adapter, complete T05 or G1 pass.

## Declared predicates and durable capture

NativeEffectExpectation/1 binds the exact effect request, settings fingerprint,
initial/settled screen, required and forbidden openings and bounded movement.
It supports named screen-transition, unchanged-screen, sneak-hold and horizontal
movement predicates. The evaluator requires complete observed settlement,
active-window states, exact request/profile and the declared positive/negative
effects. Sneak needs an actual held observation and released final state.
Movement evidence establishes the declared horizontal displacement, not a
direction or general navigation claim. Raw observation `verified` and `committed`
flags stay false; verdicts explicitly grant neither qualification nor resume.

Before capture, register one immutable complete expectation manifest for all
binding/context/stage slots in the control plan. Missing slots, duplicate slots,
changed expectations or replacement IDs cannot become an easier second attempt.
The producer binds the current admitted native descriptor and complete pending
keymap head, records one durable dispatch intent, then sends effect-start once.
Uncertain delivery or failed witness publication permits only effect-status
reconciliation. Failed outcomes and their raw sources remain terminal evidence;
they cannot be rerun or relabeled to obtain a pass.

Each per-binding ControlCheck references the immutable declaration and captured
result/verdict in operator CAS. The producer preserves simulation labels and
uses the existing repair deadline/budget/hold. It does not advertise a gameplay
tool or create a qualified input pool. Declared predicates still need reviewed
consumer/profile qualification; matching a caller's predicate alone does not
establish that it is the correct intended effect.

Restart-persistence requires the durable ADOPTED record and its exact source,
original/successor binding, checkpoint, worker stop/replacement proof, native
continuation, retained worker/native holds and expected complete keymap. The
native head's revision/digest must match the pre-restart checkpoint; that digest
binds native runtime metadata/values and complete options bytes. A fresh read
must match the adopted head. The producer never substitutes a restart label or
new instance ID for independent process ownership evidence.

Generic intended/competing summaries, complete essential-controls/release
verification, the remaining binding/context matrix and final qualified projection
are still required. The new per-binding and restart checks do not fabricate those
missing parts of the aggregate verification bundle.

## Executed checks

Base63e0905; Windows, Python3.12.14, Node24.19.0 and Java17.0.20.101; existing JVM
fixture compiled at66babdb. Private root: `2026-09-27-m1-effect-evidence-01`,
operator/SYSTEM protected before execution. No Minecraft or model call, no
installed artifact change and no paid or unchanged broad-suite rerun.

- Predicate/identity/expectation tests:21 pass. Wrong or missing effects, inactive
  window, competing screens, movement bounds and incomplete settlement cannot
  pass. Foreign plan/request/revision/stage/fingerprint is rejected. Ambiguous,
  duplicate, contradictory or unbounded expectations are refused.
- Failure/custody tests:2 pass. Failed effects remain failed, failed publication
  reconciles via status, incomplete manifests fail, changed declarations fail,
  and a failed check prevents native commit without another effect-start.
- Connected actual controller/worker/Windows guardian/JVM check passes first with
  a produced binding effect and lost effect-start reply. The expanded restart
  producer check passes, then its added falsified-proof cases pass. The final
  test rejects false old-terminal evidence, resume, altered head/options hashes,
  changed original binding and erased simulation identity. It consumes produced
  binding/restart evidence through existing complete-proof validation, commits,
  rolls back and confirms both Java trees terminal. Other checks remain synthetic.
  The three unchanged restart-loss cases were deselected.
- Full private bundle verification succeeds for native04 and native02. The new
  evaluator reproduces all13 named native04 effects using that original driver's
  declared expectations and exact recorded request/profile. It also preserves
  native02's original settled-screen mismatch under its original expectation.
  This is retained authentic data on the historical profiles, not a new run or
  promotion to the current runtime's qualification. Raw samples, original
  results and seals are unchanged.
- Changed-file Ruff and whitespace checks pass. Preparation included one
  nonexistent Java filename lookup, corrected using the actual file inventory;
  no state changed. A settings-source lookup initially selected the wrong line
  range, then read the exact digest implementation. No failed game run occurred.

Affected: M1.1c.3.2, F06/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08; native settings,
input evidence, controller references, private CAS, clocks, accounting and audit.
M1 remains in_progress; complete T01/T04/T05/T06/T10/T11 and G1 remain not_run.

Next complete qualified control projection and the complete authentic verification
bundle, real launcher orchestration, full consumption/settlement and explicit
resume, then verify the entire Minecraft repair workflow and remaining T05 cases.
T01 references, matched probes, protected scoring and exact-profile native/runtime
isolation qualification remain on the unchanged G1 closure path. Unrelated M2-M7
work stays excluded. D20 persists; D18/D19 inference authority remains M0-only.

Final WAL-aware audit: all40 authority tables unchanged at4,887,796microUSD;
all five historical256MiB telemetry holds unchanged. No Java or owned fixture
process remains. All459 milestone IDs preserved; all1643 local ledger links resolve.

Private evidence sealed171files/4,025,368bytes at
`c1bc4e6879e94c84cbd9c8cc54bb11c580de20e57996a90a0d9fdd4cd40cc3b0`.
It retains test/capture journals, exact retained-bundle classifications,
source/document snapshots before this pointer and durable/process audits.
