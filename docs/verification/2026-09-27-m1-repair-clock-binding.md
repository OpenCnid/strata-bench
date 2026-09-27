# Bind live clock evidence to the owned server and repair body

M1.1c.3.4 now connects the live clock reader to the existing private pipe launch
owner and stores a controller witness against the original native repair.
Signed data from a terminal process, a reused PID, changed launch/setup, foreign
avatar or mismatched repair cannot supply that witness. This is implemented but
unverified in Minecraft. It does not settle a budget or grant input permission.

## Implementation

`BoundClockSource` consumes the existing `TelemetryPipeBroker`, validated launch
plan and sealed setup. It reads the broker's WAL-aware SQLite state read-only;
only `DURABLE` records after the broker's fsync can cover the requested cursor.
Before and after reading the authenticated prefix, the original retained Job
member handle must be live and match the recorded PID, creation time and image.
No PID discovery or new process adoption occurs. The declared world, game,
module hash, online mode and port must match the existing launch binding.
The prefix's signed startup identity must independently equal that binding.

The complete registered roster is retained privately. Unknown avatar UUIDs are
refused. The current local profile derives the native body fingerprint from
the exact numeric loopback endpoint and registered player UUID, matching the
existing native body policy. Other endpoint aliases are not guessed equivalent.
Launch, setup, authority and boot form an immutable source identity. Synthetic
launch mode remains explicit; neither authentication nor this join qualifies
filesystem/process isolation or the Minecraft profile.

`RepairClockEvidence.capture` uses the original controller lease, repair plan,
native handoff and reserved budget. It requires exact campaign/epoch/full roster
agreement and checks the current private native body identity against both the
admitted target and registered player. Captured marks are bounded, immutable CAS
witnesses; distinct marks require increasing cursors on the same source. A retry
retains its original observation times and rejects changed source bytes. Mode,
scope, roster, body or evidence failures cannot create a mark. The budget and
input hold remain unchanged. These evaluator/operator services have no gameplay
or helper tool route and expose no credentials or scoring feedback.

## Executed evidence

Profile: Windows; Python3.12.14; Java17.0.20.1+1, using the unchanged compiled
telemetry0.3.19 test classpath from the preceding live-clock source change.

- `pytest tests/test_bound_clocks.py tests/test_live_clocks.py -q`, with explicit
  `STRATA_TELEMETRY_TEST_JAVA`/`STRATA_TELEMETRY_TEST_CLASSPATH`:34 pass. Actual
  Windows/JVM handle checks and the live Java/Python clock case were enabled.
- The new retained-handle case reads a valid signed prefix while its actual JVM
  is alive, observes normal exit, then rejects that same prefix with
  `CLOCK_SOURCE_PROCESS`. Its telemetry, setup and pipe lifecycle are synthetic;
  it does not claim a production pipe or Minecraft integration pass. The final
  focused invocation also retains the exact private receipt and exit/refusal.
- Source/contract cases cover terminal/uncertain/nondurable state, PID reuse,
  signaled/missing handles, closed/deadline/dead-thread sources, changed
  launch/world/roster/boot, and signed but mismatched native identity/avatar data.
- The existing controller/native repair fixture now exercises the real capture
  service with synthetic native replies. It checks profile/campaign/epoch/roster/
  body refusals, original-plan binding, increasing cursors, immutable retries and
  unchanged reservation/input fencing. This is not the complete repair workflow.
- Ruff and `git diff --check` pass. The initial lint-only lambda style failure
  was corrected; no behavior or acceptance criterion was changed to pass a test.

Private evidence is in
`C:/Users/Darian/.strata/evidence/2026-09-27-m1-repair-clock-binding-01`.
No Minecraft run, installation, model call or new spending authority occurred.

## Remaining acceptance dependency

A periodic sample may have been generated before the controller began reading
it. A live owned producer and matching body do not eliminate that timing gap.
The witness therefore retains `sample_generation_after_read_start_proven=false`,
`complete_repair_accounting=false`, `consumption_settled=false` and
`campaign_permission_published=false`.

Next implement a bounded, single-use producer barrier on the existing private
telemetry channel: persist the request, deliver it once, and obtain a complete
callback sample made after the producer observes that request. Reconcile uncertain
delivery by retained status, never by renewing or replaying the request. Bind the
result to the original repair boundaries. Then reconcile prior-gameplay allocation,
body/model/helper charges and publication tail, settle durably, and complete the
original-lease resume. A received old sample must never substitute for that barrier.

M1 stays `in_progress`; T01/T04/T05/T06/T10/T11 and G1 stay `not_run`. Other T05
workflow/rollback/skill/launcher/native qualification gaps and the essential
native-health failure remain open. Coverage: F06/F09/F11/F16;
N01/N02/N03/N04/N06/N08; T01/T04/T05/T06 and necessary T12 dependencies.

## Evidence preservation

The private bundle is sealed and verified: 32 files, 2,527,143 bytes,
SHA-256 `afab36b82d9880c7479144f30b73fcbffc5fc7b6a45ede0a4f1d66b6b84fe0e7`. It retains changed source/documents, focused test logs,
the actual retained-JVM receipt, reused classpath hashes and before/after audits.
All 40 authority tables, eight telemetry reservations and installed client/options
hashes remain unchanged. All 460 existing milestone IDs remain represented;
2,141 local documentation links resolve. Final runtime inventory is empty.
This public seal pointer postdates the archived document snapshot.
