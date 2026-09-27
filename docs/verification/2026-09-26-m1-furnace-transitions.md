# Native furnace start and refund boundaries

M1.5b.7 is implemented_unverified for authentic integration. This required
M1.5/T10 dependency inherits F10/F16, N01/N04/N06/N08, C12/C18/C24 and
T01/T06/T10. Full G1 remains not_run. Owners: GI/RS/QA.

The pinned Thermal machine starts a process by assigning its base processing
step and adding the previous remaining progress to the resolved recipe energy.
Negative overshoot can therefore shorten the next process. When the native
server tick stops after completion, it passes the negated remaining progress
to storage before processOff clears progress. Storage clamps the refund at
capacity. Individual processing debits cannot establish these transitions.

Telemetry0.3.17 / ServerStarted18 adds the distinct private
`thermal1192-native-furnace-transitions/1` profile. Four noncancelling hooks
observe processStart entry/return and the single native tickServer refund call
before/after. They do not replace game methods or alter resource quantities.
Require exact native caller/server thread, same live tile/level/position/tick,
mutually exclusive capture frames and complete pairing. Start additionally
requires stable internal recipe/registration and base step. Unsupported states
emit typed refusals; pairing/lifetime/emission failures cannot silently clear
an incomplete capture. Completion and processing hooks keep their prior schemas.

The new transition state permits zero previous max/step for an initially idle
machine; the older completion/processing state requirements remain unchanged.
Both boundaries retain full plain-slot/empty-augment and noncreative storage
facts. The reader verifies exact progress carry or actual clamped RF refund,
unchanged unrelated state and no signed-integer overflow. A refund has no
invented recipe/player attribution. An accepted start is not a completion.

Startup18 and exact artifact support are required in both private pipe and
offline ingestion. Transactions share the existing duplicate fence and start
registration generations cannot roll back. Complete authenticated streams are
required; unsupported/missing profiles and partial streams reject. A separate
16,384-transition quota fails without returning a partial report. Native
refusals and invalid arithmetic retain their original sequence/reason and earn
no accepted refund. Reports keep debit and refund totals separate; they do not
infer net recipe energy or machine lifetime/continuous-window authority.

Verification executed:

- Python:244 pass,4 existing native opt-in skips. The selection covers
  `test_machine_transitions`, `test_machine_energy`, `test_machine_registration`,
  `test_machine_capture`, `test_telemetry`, `test_telemetry_pipe`,
  `test_setup_control` and `test_gameplay_package`. The56 new transition cases
  cover initial/carry starts, zero/positive/capacity-clamped refunds, unrelated
  mutations, wrong authority/profile, overflow, signed-stream import, refusal,
  duplicate/generation/quota fences and online private receipts.
- Offline Gradle tests and reobfuscated jar build pass.13 selected Java cases
  pass with no failures/skips: FurnaceTransitionBytecodeTest3,
  FurnaceTickBytecodeTest3, FurnaceCaptureBytecodeTest2, FurnacePhasesTest4 and
  RecipeRegistrationBytecodeTest1. The three new cases inspect the pinned
  installed processStart arithmetic, exact refund call and compiled injection
  targets/counts. They do not execute transformed Forge.
- The original operation07 seal verifies; current authenticated inspection of
  its412 signed records exactly matches its archived inspection. No older
  profile or evidence is migrated. An initial read-only audit used the wrong
  report key `events` after comparison/copying and raised KeyError; retained
  diagnosis uses the actual `records` key. No sealed material changed.
- Focused Ruff and whitespace checks pass. All40 durable authority tables
  remain unchanged at4,887,796microUSD. No game/model dispatch, new allowance,
  artifact installation, consumed-decision replay or deadline change.

Candidate jar:139,585bytes, SHA-256
`8a18fb6205e31a770609fef7232cb4f24235711809673f0fb8966121121fc21f`.
Private source/build/test archive: `2026-09-26-m1-furnace-transitions-source-01`.

Next prepare a fresh protected reference with criteria sealed before launch
that exercises both nonzero carried progress and a nonzero final refund.
A two-item ordinary furnace trajectory is the source-backed candidate; it
requires its own bounded checker/plan binding and authentic verification.
Keep prior operation07 and all failed/consumed references unchanged. Then bind
complete operating intervals and machine lifetime, setup/team/loaded producer,
negative/alternate controls, overhead/parity and isolation. The remaining
keybinding, native-host and probe G1 contracts are still required. Raw resource
witnesses remain unscorable; D18/D19 remain M0-only.

Final audit verifies804 source pins,450 unique/preserved milestone IDs and1,874
local links, unchanged40 authority tables at4,887,796microUSD, exact installed
client/server pins and no owned runtime. Private archive40files/2,767,172bytes
verifies under seal `b0ff2833d925db85c7d65f82df7a6a90b0a74972922ad5a807c7d5d323bde06a`.
This pointer follows the archived document snapshot; the archive is unchanged.
Authentic transition integration and full G1 remain not_run.
