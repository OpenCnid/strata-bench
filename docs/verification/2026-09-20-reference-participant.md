# Bounded private client coordination for the M0 craft reference

September 20, 2026. Operator-only. M0.2c.3b.3b.1, supporting F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5.
M0 remains in progress, G0 fails and G1–G5 are not run.

## Implemented behavior

The owned server launcher previously stopped within 60 seconds after its native
binding/readiness point. The existing separate-desktop client needs a longer,
explicitly bounded startup/action window. `PrivateReferenceLaunch/2` registers
one external operator participant, a 1–420-second window and a fresh private
terminal-report path. It retains the 600-second server exposure and 120-second
maximum graceful stop. The entire window must fit after boot; late startup
cannot silently shorten it. Version 1 retains its original timing contract.

`reference_participant.py` publishes fresh readiness only after server/native
process binding and durable readiness journaling. The receipt binds instance,
setup, launch plan, boot, participant, challenge and expiry. Windows atomic
non-replacing publication prevents partially written receipts from appearing as
ready. A completion receipt must match that readiness and the exact bounded JSON
report. Private read/link/quota checks and deny-write leases preserve the report
and receipt through server termination. The launcher copies exact report bytes
and journals the terminal coordination state before sending the single stop.

Missing, foreign, failed, malformed, changed or late completion retains an
uncertain dispatch after bounded server cleanup. Premature completion and a
window that no longer fits also fail without a ready grant. Existing one-use
launch reservation and import guards remain in effect. There is no retry,
restored inventory, renewed telemetry grant or scoring write.

The external driver independently owns and bounds its client/worker through the
existing desktop/guardian facilities. This change does not spawn that driver,
prove its execution, certify its shutdown or establish same-user isolation.
`participant_execution_verified=false` and `scoring_eligible=false` remain
explicit even for a successful coordination receipt.

## Verification actually run

Windows x64, Python 3.12.14, existing Temurin 17.0.20.1+1 test JVM and unchanged
production telemetry signer/`OwnedLaunchFixture` classes:

- Initial `test_reference_participant.py` + `test_reference_launch.py`:
  **40 pass**, zero skipped, 20.07 seconds.
- Final participant suite with added premature/full-exposure/hardlink cases,
  plus `test_craft_reference.py`: **58 pass**, zero skipped, 15.03 seconds.
- Focused Ruff initially reported four imported-pytest-fixture shadowing
  annotations; these were corrected. Final focused Ruff passes.
- Compiled gameplay-package exclusion: **1 pass**, 0.32 seconds. Whitespace
  checks pass. No Java fixture remains after the process audit.

Actual JVM cases verify bound readiness, complete/missing/foreign/failed
completion, all held server processes terminal, no forced stop for the normal
completion/timeout/failure paths, uncertain import rejection and denied replay.
Additional cases exercise pre-dispatch invalid paths/exposure/versions, report
hash/size/missing/malformed failures, deadline expiry during validation, Windows
write denial through close, hardlink rejection and non-replacing publication.
The JVM is a synthetic event fixture, not Minecraft or a client craft.

The private bundle `2026-09-20-reference-participant-01` retains final test output
and a read-only prerequisite inspection. The actual stopped world has survival
player state, four furnaces, zero andesite and zero polished andesite. Its existing
FTB player-team file records the expected player team and owner rank; this is
registration input, not an observed native actor/team trajectory. A fresh,
declared ingredient setup and complete clean-stop seal are required before the
new craft. No game/model/shared input was used for these checks.

Read-only durable accounting still has the original 10000000-microUSD allowance,
755400 microUSD held once, one migration, zero valuations and uncertainty.
No request was replayed, settled, refunded or newly dispatched.

## Still required

Execute the changed sealed version-2 client craft with the registered native team,
then retain its native before/after points and required positive/negative controls.
Keep its external client lifecycle evidence separate from server coordination.
Do not rerun the unchanged startup-only reference. Concurrent mutable-file
ownership (.3b.2b), complete setup/mutation history, mechanical parity, isolation
and protected scorer admission remain open. The unresolved $0.7554 usage hold,
all 500-ms shutdown failures, five effective-file failures, loopback failures
and Mineflayer/E9E incompatibility remain unchanged.
