# Native furnace processing RF capture

M1.5b.6 is implemented_unverified for authentic integration. This required
M1.5/T10 dependency advances F10/F16, N01/N04/N06/N08 and C12/C18/C24;
complete T01/T06/T10/G1 remain open. Owners: GI/RS/QA.

The exact pinned `MachineBlockEntity.processTick` debits storage before reducing
remaining progress. Its two returns are zero when no work remains, otherwise
the configured progress step. `EnergyStorageCoFH.modify` clamps negative energy
to zero and bypasses negative modification for creative storage. Therefore the
returned step is not necessarily measured RF. `tickServer` can refund overshoot
after completion and also charges/transfers outside this bracket. Neither
recipe cost nor a completion/save delta proves processing debit or net cost.

The new private producer uses telemetry0.3.16 / `ServerStarted/17` and
`thermal1192-native-furnace-process-tick/1`. Existing phases/2 completion records
remain distinct. Two noncancelling hooks observe entry and both original returns.
Require the real dedicated-server thread/caller, exact furnace tile/level/position/
tick, unchanged internal recipe and registration, and bounded plain inventory with
empty augments. Capture RF/capacity/noncreative storage, progress/max/step/active,
full base-slot identity and actual return. Unsupported state emits a typed refusal;
broken pairing/lifetime terminates rather than silently dropping evidence.

The Python reader checks exact debit/progress arithmetic and unchanged unrelated
state. With positive remaining work, the step reduces progress while actual RF
debit is min(stored RF, step). With nonpositive work both remain unchanged and
return is zero. Overshoot and partial funding remain visible. Each witness retains
the original event digest, sequence, tick, scope, registration and recipe digest.
No actor, completion, continuous interval, net recipe charge or score is invented.

Online/private inspection admits these records only under startup17 and supported
artifact identity. Unknown/mixed profiles, guessed actors, duplicate transaction
IDs and registration-generation rollback reject. Complete authenticated framing
is required before offline results return; a partial stream fails. Inspection
rejects above16,384 processing records without returning a partial report, in
addition to existing stream quotas. Native refusals and invalid arithmetic retain
their source sequence/reason and earn zero accepted debit. Raw captures remain
outside the gameplay package and scorer; loaded-code, setup/team, sustained
operation and protected-score flags remain false.

Verification executed:

- First focused Python selection:94 pass across new energy, machine reference and
  registration cases. The second selection covers changed reader/pipe paths,
  legacy capture, setup control and gameplay packaging:159 pass,4 native opt-in
  skips. Across both selections there are211 distinct passing cases and4 skips.
  The44 new energy cases cover full/partial/zero RF, progress overshoot, inactive
  first tick, zero-work return, exact state, bad authority/profile, signed-stream
  integration, online duplicate rejection, quotas and no invented completion.
- Offline Gradle selected tests and reobfuscated jar build succeed.10 Java cases
  pass with zero failures/skips, including3 new exact installed-bytecode/hook
  checks. Private artifact pins are supplied for native bytecode inspection.
  This is not execution of transformed Forge or authentic producer qualification.
- Additional `javap` inspection follows SimpleMachineRecipe's inherited getters:
  output/input lists are read, chance lists are copied, and recipe energy reads
  machine properties. This supports the observer design; runtime mechanics parity
  and overhead still require authentic measurement.
- The sealed operation06 archive verifies. Current reader reconstruction matches
  its original235-record authenticated inspection exactly. No older evidence or
  reference is migrated/replayed as a new launch.
- Initial test formatting produced30 lint findings; formatter relocation then
  required fixture import/parameter annotations. Retained initial source/log and
  corrected focused Ruff/whitespace checks preserve that history. No acceptance
  check was removed to make the tests pass.

Final review also fences completion entry while a processing capture is open,
matching the reciprocal processing-entry guard. The10 selected Java cases and
offline jar build pass after that change; overlapping runs are counted once.
The earlier candidate remains archived separately from the final artifact.

Candidate telemetry jar:137,147bytes, SHA-256
`7f0c0d8e9b5e8c179bd48a983bcf45ee32acea87f965c08136b761be1b089d27`.
The installed game artifacts are unchanged. No game/model run, new inference
allowance, deadline extension or consumed-reference reuse occurs here.

Next bind this changed producer artifact into one fresh protected reference and
verify actual processing records, completions, private import and termination.
Then join refunds/charging/resource provenance and continuous intervals with
registered setup/team and loaded producer qualification. Full T10 alternate and
negative controls, parity/isolation, keybinding/native host/probe G1 requirements
remain; prior operation failures and operation06's narrow positive scope persist.

Private source/evidence root: `2026-09-26-m1-furnace-energy-source-01`.
D18/D19 remain M0-only, with all existing holds/decisions preserved.

Final audit verifies799 source pins,449 unique/preserved milestone IDs and1,863
local links, unchanged40 authority tables at4,887,796microUSD, all327 prior game
jar pins and no owned runtime. Private archive1,254files/12,732,244bytes verifies
under seal `72c0fb09ff116335de4cfc72596475bc58a484269e0dc2feefbc10cb9291b281`.
This pointer follows the archived document snapshot; the archive is unchanged.
