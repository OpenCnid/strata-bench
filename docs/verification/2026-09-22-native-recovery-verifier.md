# Joined native/game recovery evidence

September 22, 2026. Operator-only. M0.1d.8 remains `in_progress`; M0 is
incomplete and G0 is `fail`. M0.1d.8a and M0.1d.8b are `verified` for the
bounded sealed journal handoff and explicit two-epoch reconstruction scopes.
The changed Recovery/3 run and independent reconstruction both pass; complete
canonical checkpoint, clock, scorer and isolation qualification remain open.

Coverage: F01/F03/F04/F05/F09/F11/F16, N01/N02/N04/N06/N08,
C03/C04/C06/C12/C16/C17/C20/C24, partial T01/T02/T03/T04/T06/T07/T12/T13,
G0 items 1/2/4/6. SPEC 0.2.125 records the contracts; thresholds and M1–M7
are unchanged.

## Working verifier

[NativeGameEvidencePlan/2](../../evaluator/src/strata_evaluator/native_game_evidence.py)
requires explicit externally pinned original and continued archives. It first
reconstructs the entire original run, then performs
[preservation and continuation checks](../../evaluator/src/strata_evaluator/native_game_continuation.py):

- All old native rows, CAS bytes and ledger positions remain unchanged. Account
  limits, campaign configuration and retention policy cannot be replaced.
- Exactly one new job and its attributed operations are admitted. New root/helper
  receipts reconcile independently; original, new and cumulative costs are
  reported separately.
- All old worker actions/events and epoch counters are retained before examining
  the new epoch. New primitive charges start at the old cumulative count.
- Saved own state, source component/world, journal handoff, fresh credentials,
  old-token/epoch denial, root-note continuation and helper denial are joined.
- Current source/runtime/pack pins, normal stop and recaptured components retain
  their existing independent checks. Archived paths stay inert; report output
  cannot traverse into either source archive or the public repository.

The checker retains explicit gaps for authoritative clocks, save custody,
runtime/helper isolation, private scoring and authentic model qualification.
It cannot turn this development recovery into complete G0 acceptance.

## Recorded development recovery

The new command independently reconstructs the existing pinned worker/recovery
pair, without launching a game or provider. Original six scripted calls plus
six continued calls reconcile to **12 calls / 168 fixture units**; one original
plus one continued primitive reconcile to **two primitives**. Saved player,
root/helper controls, old native history, account limits and normal stop join.

Original execution seal:
`6ed35edb1c8241595eb78b10af3998d297b8c31d3cedf23d233d4cf4ef14f5e4`.
Recovery seal:
`48b3f5fe26be9f9eec8b6525e023d2825c08322259471453d813e0e5ba3ef97f`.
Report digest:
`83e7143ef88b9155801898b87d88d594dac5ec6fbc7027a70aaece6a6c9f5280`.
Both original archives remain unchanged. This validates Recovery/2 evidence;
it is not a substitute for executing Recovery/3 against the sealed installation.
The private audit, including its first failed command, is
`2026-09-22-native-recovery-verifier-01`: **4 files / 10,231 bytes**, seal
`045fe08f331769bbecd2d5a202c43d6646607bc684a13cd67c21b876c38bc958`.

## Sealed-profile failure retained and fixed

The first changed Recovery/3 run restores the original saved world and journal,
starts the sealed server and connects the worker, then fails
`GAME_RECOVERY_PLAYER` before native execution. The actual vanilla save has an
empty Inventory list with End element type 0; the inherited validator required
Compound type 10. The shared validator now accepts either valid empty form,
still rejects a nonempty End list, and compares the observed inventory normally.

The failed run remains sealed: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-sealed-recovery-01`,
**297 files / 48,850,668 bytes**, seal
`e10339b3058eb24805687f8771c0c12b00378c8511395ef2edc19e394e37daed`.
Outer duration **85.640 seconds**; all **21 owned processes** are terminal.
Worker cleanup was forced, with return code 125; the server exits normally.
`M0_CAPTURE_INCOMPLETE` and the non-frozen worker journal/WAL remain retained.
No native execution or new model request occurred. All 34 original authority
tables and the pristine template remain unchanged. This run is still failed.

## Source verification

Windows, Python 3.12.14, Node 24.19.0, `PYTHONPATH=src;evaluator/src;tools;tests`,
`PYTHONDONTWRITEBYTECODE=1`:

- Existing native evidence/retention/recovery/sealed selection: **107 passed**.
- New continuation selection initially reported **1 failure / 31 passes**:
  the result accidentally returned per-action history under the retained-history
  field. The dedicated retained-history variable fixes that report bug.
- Final continuation plus saved-recovery selection: **80 passed**, including
  old-row removal/change, refund, uncertainty, unreported usage, extra jobs,
  unauthorized schema/policy/account changes, counter reset, handoff/source
  mismatch, output traversal and empty-inventory controls.
- The initial actual-archive inspection failed because it expected an error's
  request ID at the response top level. It now checks the actual nested error
  contract, including the null request ID for pre-authentication rejection.
  That failed command log remains retained alongside the successful audit.
- Ruff passes. Existing Typer/Click deprecation warnings remain in the earlier
  affected selection.
- Final documentation review validates all 1,272 local links in the five changed
  Markdown files, preserves the complete previous progress-log prefix and all
  M1–M7 rows, and leaves SPEC sections 3 and 15–19 unchanged. Whitespace passes.
  A fresh read-only authority comparison again preserves all 34 tables;
  fetched main remains `c2161a6e79cea0c668ab993df149ab1ed5af119b` and no Java
  process is present. No unchanged game or broad test matrix was repeated.

## Authentic sealed continuation and independent reconstruction

The second attempt uses a new instance after the empty-inventory fix, restoring
the same successful parent with its original campaign baseline and costs:

- Server readiness **22.803 seconds**, within the unchanged 80-second bound.
- **35/35 native checks**: saved own state restored, old token/epoch rejected,
  retained root note read and continued, helper history denied, one new bounded
  look action completed without replay, then normally stopped and recaptured.
- **Six new scripted calls / 84 fixture units**. Together with the original
  seven calls / 98 units, cumulative usage is **13 calls / 182 fixture units**,
  with **two cumulative primitives**. No real model request occurred.
- Independent reconstruction preserves **378 old native rows in 42 tables**,
  **18 old ledger rows**, all prior CAS bytes, original account limits and
  campaign/retention configuration. It reconciles all six new game request
  preimages, five scoped observations, receipts and new saved state.
- **46 owned processes**, all normally terminal, with zero active or forced
  terminations; all logs complete. **27 state files / 13,866,981 bytes** captured.

Execution: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-sealed-recovery-02`,
**3,961 files / 121,423,632 bytes**, seal
`2be1d6eecc05d8c6eccc03a7c951f5fbf803385e1fa05b7304155972c67400e0`.
Stopped snapshot:
`7b72dd71c92a67f3d5a32b25f8cf54280fc33c0671df80dcad9b4409e5fc2d62`.
Native component:
`cas:sha256:9bbdee084252c6a57d4c701be5fa83b679264e1a6be86c3b7f0263687134faf4`.
Independent audit: adjacent `2026-09-22-sealed-recovery-audit-01`,
**3 files / 9,499 bytes**, seal
`c1241b7a38584f19811243ffbded565c34aeea9a44244132f46080da569e13ae`;
report digest `c568dad7e683feb34a20a1ea2a7bb0eaa001914ab9be15341207fc06d0c602fd`.
All 187 archived executed source files match their pre-run pins. Both the
original baseline and failed first recovery seal independently reverify.

All **34 original authority tables** and the pristine software template remain
unchanged. The original **$10 API-equivalent allowance** retains **$0.7554 held
plus $0.001458 settled**, uncertainty true and D12 consumed. Shared-desktop
input stayed paused; no Java remained at the post-run check.

## Remaining acceptance work

Measured spans remain distinct: outer wrapper **265.172 seconds**, native runner
**222.188 seconds**, server **209.640 seconds**, native lifecycle **22.713 seconds**.
These overlapping spans are not additive. The runner currently waits for the
worker's configured wall deadline after native closure before stopping the
server. Next connect a coordinated stop to the same profile and record the
authoritative game/avatar intervals and save boundary. These components still
report `clean_save_proven: false` and `complete_checkpoint: false`.

Then close the remaining private scorer/setup, isolation and E9E/provenance
requirements. Authentic model qualification remains blocked by the old hold.
No prior failure, old 500-ms sample, effective-file failure, Mineflayer/E9E gap
or D12 delivery failure is removed. D13's passing 1,000-ms normal-stop sample
remains separate; no threshold changed here. M0 is incomplete and G0 fails.
