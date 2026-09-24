# Connected player instrumentation

M0.2c.1d.1; F03/F06/F09/F11/F13/F16, N01/N02/N03/N06/N08, C06/C18/C20,
partial T03/T04/T07/T09/T12/T13 and G0 items 1/3/4/6. D14 isolation deferral and
the M1–M7 roadmap remain unchanged. This report preserves failed attempts
separately from any subsequent changed-profile result.

## Prepared profile and native checks

The held worker now contains the already implemented private health module.
Its 11,724-file / 654,085,633-byte runtime passes an actual 2.453-second import;
all three owned processes terminate normally. Manifest SHA256 is
`24a54d3dfd71dca680200d60f11234988fa63ec2296c39c7a7ae4dc8ad6e355b`.
The 9,427,424-byte manifest exposed a reader mismatch: runtime manifests already
permit 16 MiB, whereas the new measurement reader used the general 8-MiB JSON
bound. The reader now uses the existing manifest-specific limit, with tests
retaining both limits and rejecting oversized inputs.

The successor vanilla lock is
`cas:sha256:8a47d30e06d698b1d7a6329dbbff2a23772523930ba0e16be4b76a96de685bd5`.
It reuses the official acquired installation and original player-free baseline
`fe6cdbcafaf3bcecce4a0ef060dfc084041aae1dd4526d9430480f47fbcaf379`.
Only the three permitted provisioning tables append; original rows and all
other authority tables remain unchanged. No installation is downloaded again.

Native preflights 07 and 08 each pass 27/27 contract checks with six synthetic
provider requests, in 21.1172 and 23.2399 seconds respectively. They are not
model or Minecraft trials. Preflight08's outer conservation assertion fails
because concurrent authorized profile publication appends outbox events.
Independent reconciliation confirms only outbox changed during that window,
with all 39 other tables and accounting unchanged. The overall profile
publication changes three permitted tables; the overlapping preflight window
changes only one. Keep the failed outer assertion, despite passing native
contract checks. No unchanged preflight was repeated to remove that failure.

Private seals:

| Artifact | SHA256 |
|---|---|
| `2026-09-24-instrumented-worker-runtime-01` | `7a4731b37924cd899500bcb144c7a376f79ef2df23f098fa5df05a74738e0e39` |
| `2026-09-24-instrumented-profile-01` | `3df3de3d4caa043b8dbf2dd2660da863b6de00e9982434b3f3aab89c7fe311a5` |
| `2026-09-24-helper-native-07` | `9551034648ab2c53e2d754ad295b961d4a65d15f78a7861476e7cf31e3961464` |
| `2026-09-24-helper-native-08` | `501e8e0f3f54e25a66bda06bfd076aafb5262addc093629c09e5715c531f3cdf` |
| `2026-09-24-instrumented-pilot-preparation-01` | `a79d06a0d73fe409fd82e6e30996b90b04ae06f8ec76034ea8a47800a0e960d3` |

## Authentic failure and repair

`2026-09-24-m0-instrumented-live-16` fails before native job creation or any
model request. The server becomes ready, but its first player connection
triggers JVM `VerifyError` at `agh.l()V`, bytecode offset 523: slot zero is TOP
at the newly inserted `ALOAD 0`. The original method's final return stack frame
discards all locals; the new avatar callback requires the player receiver there.
The earlier headless test did not force verification of this lazily loaded
player method. This is an instrumentation defect, not a model-call failure.

Outer execution takes 114.703 seconds (inner 74.344); all 21 owned processes
are terminal, with zero forced Job terminations. Worker drain is 16.7352 ms.
The server exits 126 after its crash handler and sticky in-tick clock rejection;
there is no authoritative stopped snapshot or complete clock report. Retain
`GAME_CONNECT_TIMEOUT`, `SERVER_RUNTIME_FAILURE`, and `NATIVE_MEASUREMENT_STOP`.
All 40 authority tables remain identical; exposure stays $4.849167/$10.
D19.9 was not consumed. The failed physical instance is used and is preserved.
The immutable archive contains 253 files / 55,049,165 bytes, including original
Java source and crash reports; seal
`3580fccfa1fdd03c327080aa8d77907e959f6ec069d220a86a8e5c0548ed0663`.

The agent expands original stack frames and retains the pinned player receiver
in slot zero. It rejects receiver reassignment and unexpected receiver types;
other live locals and stacks retain their original values. It copies exactly
the declared local count, not ASM's backing-array capacity. Original class
hashes, callback meaning, fail-closed policy and invocation counts are unchanged.

A new fixture uses the actual pinned Minecraft classes and original JAR code
signers, then forces method verification with `-Xverify:all` and reflection
without class initialization or a game launch. It reproduced the production
failure before the repair. Retain the fixture's initial signer mismatch, the
first repair's excess-array-capacity NPE, and the misplaced stdout assertion
corrected during test development. Final focused command:
`pytest tests/test_vanilla_clock.py tests/test_native_game_measurements.py -q`:
**70 passed in 13.41 seconds**, with both explicit installed JVM inputs set.
Focused Ruff and `git diff --check` pass.

The changed agent SHA256 is
`66f4b618962b5aa2eb64ee4ae5cbc74b1647a6648f4eacda0d13125f34662697`.
The worker runtime and installation profile are reused unchanged. A new physical
instance and campaign scope distinguish the corrected attempt; the unused native
job authority remains D19.9. No model response is replayed or refunded.

## Changed authentic run: movement and accounting pass, completion fails

The corrected module passes actual avatar connection. Live16b executes a
model-selected 45-degree turn and 1.072751-block walk, then delivers one
clean-context helper reply. Thirteen of fourteen native checks pass; only
`native_completed` fails. After 16 settled requests the gateway refuses further
requests with `GATEWAY_REQUEST_LIMIT` (two refusal records), and native exits 1.
The finite cap behaves correctly; this is not a provider transport failure.
The original run remains failed, including its missing final model response.

All 16 requests settle for **$0.015015**: 15 root requests / $0.014415 and one
helper request / $0.000600. Both envelopes close without double charging.
Thirty game calls and 33 broker calls settle; two actions emit 22 primitives.
The independent stopped player matches the latest public observation. The
527,955-byte private report publishes and its 16 wire captures match their
original bytes. D19.9 is now consumed; combined exposure is **$4.864182/$10**.
The old $0.7554 hold and four full $1 failed envelopes remain reserved.

Outer execution takes 343.047 seconds. All 54 owned processes are terminal,
with no forced Job termination and complete logs. Worker drain is 38.2577 ms;
the server stops normally and captures its stopped state. These observations
do not claim a complete campaign checkpoint or full save-custody qualification.
The immutable archive contains 4,073 files / 217,794,748 bytes, including
80 scoped CAS objects and all current-job broker workspace references; seal
`2bbcbf9564cd34694e44b89fa448a78b2c74d4f756187402ca4d94be0d0176bc`.
Changed module seal:
`a5cc1f6c7a6b0a1c2d7f4c61d05057681c277d841d3a01e817d8cd448d9d6943`.
Fresh preparation02 seal:
`e3a4189ea6796d9676299e745cc54e513f7ee9c01272a2aab5b91c6ee89effcc`.

The stored measurement reader also refuses `NATIVE_TIMING_ORDER`: avatar-ready
and native-start share one monotonic clock quantum, as do worker-close and
server-stop-request. Ordered events need nondecreasing timestamps, not strictly
increasing timestamps. The reader now retains equal adjacent marks and genuine
zero-duration segments, while rejecting backward timestamps and incorrect
sequence/event order. It never invents elapsed time. The final clock/measurement
selection passes **71 tests in 13.89 seconds**.

Read-only reconstruction with that correction independently verifies:

- 5,097 actual server ticks, 4,971 avatar callbacks joined to the saved player,
  37.2135615 seconds of tick work and 273.4450963 seconds of callback exposure.
- 252.5399031 seconds of worker coverage with a terminal window, 8.672 CPU-user
  seconds, 2.938 CPU-system seconds and a 274,964,480-byte sampled RSS peak.
- 302.875 seconds of wrapper time, partitioned without loss; nested server
  299.266, worker 254.516 and native-harness 248.640 seconds are not added.
- All distinct root/helper receipts, 33 tool-call durations and exact valuation
  records, with all 40 live authority tables unchanged by reconstruction.

This audit does not rewrite the failed run or pass the strict successful-pilot
consumer. Its report digest is
`cbe8eb5f2c6e67e1109dd0f15602f42007a258e68972cdb5e922e1a4f3d5f1a5`;
the 9-file / 673,081-byte audit seal is
`e1f970b1291006ce8b428198ceacd60f4d711b61ff4cc98e543ed142ac39eb63`.
Private root: `C:/Users/Darian/.strata/evidence/2026-09-24-instrumented-pilot-audit-01`.

The helper pilot prompt now puts request budgeting first: batch permitted reads
and bounded status polling, reserve requests for the helper and final answer,
use a bounded completion wait, then answer from recorded public evidence.
Targets and actions remain model-selected; no private coordinates, route or
success answer is supplied. Limits remain 16 combined requests, 240 native
seconds, one helper and $1 within the original $10. Existing prompt/admission/
retention checks pass **116 tests in 27.98 seconds**. Native preflight09 passes
**27/27**, with six synthetic requests and normal 19.909944-second native closure.
This verifies the changed native contract, not improved real-model completion.

## D19.10: normal native completion, partial gameplay

Preflight09's sealed consumer accepts the changed source:
`269de7e72d0ed33e726dc203b538d77d0a6b04b3d83fec82cea94e9c90eb7306`
(3,762 files). Preparation03 reuses the worker, installation profile and corrected
clock module, with a fresh player-free physical instance and campaign; all 40
authority tables remain unchanged during preparation. Its seal is
`e6c3a205084eb732449657f8b3e88cd819e7ca6bad206ef582bfeb7a46afd28c`.

Live17 completes native execution normally, with one delivered helper reply and
14 settled requests: 13 root requests / $0.013458 and one helper / $0.000460,
**$0.013918 API-equivalent total**. It fails the two-action movement goal.
The model first submits action sequence 3 instead of 1 and receives OUT_OF_ORDER;
it then queries the outer RPC ID and receives ACTION_UNKNOWN. The public contract
already specifies `last_action_seq + 1` (1 when null) and the batch request ID.
The model subsequently corrects both fields and completes one look action with
confirmed release. It has used both permitted action submissions and never walks.
This is retained model behavior, not a transport or clock failure.

The whole-trajectory checker remains 10/14: the ordered turn/walk and full
accepted-action join fail. Its conservative early return does not report the
later turn as a whole-trajectory pass. A separately labeled accepted-action
component audit verifies that actual turn: 1.8928095738 radians, zero translation,
target yaw error 0.0002626926 radians, unchanged health and one charged primitive.
It excludes the rejected attempt only from that component calculation; the
original attempt, errors, request charges and failed overall result remain intact.

All 53 owned processes terminate normally, with complete logs, zero forced Job
terminations and 32.8000-ms worker drain. Outer duration is 356.547 seconds;
native process lifetime is 204.101746 seconds. The stopped player matches the
latest observation. The 184,376-byte report and all 14 wire captures rehash.
The corrected timing consumer now produces the stored measurement report:
5,355 server ticks, 5,235 avatar callbacks, 286.9603855 callback seconds,
40.404256 seconds of tick work and 265.5871978 worker-health seconds with its
terminal window. Wrapper time is 315.718 seconds; nested server/worker/native
harness spans are 312.235 / 267.594 / 261.735 seconds, not additive.

Independent reconstruction exactly matches that stored report and all 18
broker-call durations, validates native exit 0 and every valuation, and verifies
that the strict successful-pilot consumer still refuses this failed goal. All
40 live authority tables remain unchanged by the audit. Its initial assertion
incorrectly compared an estimate to `actual_charge_microusd`, which is correctly
null; audit02 retains that failure. The corrected audit03 checks the explicitly
labeled estimate and preserves null actual subscription billing.

| Artifact | SHA256 |
|---|---|
| Live17, 4,062 files / 216,625,111 bytes | `79a76d2d0b97aeea31864d9b37d58509c276e753ce2da352fb0dc80d2c6bfca8` |
| Independent component/cost/clock report | `fea101b08416d1848e0d92c1d969c318db371bfd53dcd7878ec8ad5816718da1` |
| Audit03 seal | `3d544f189004652e9d308147b10b1a44c9d80673fbe1c9be797b35272baf6867` |
| Retained audit02 assertion-failure files | `8e2a380587ce0bc296ed0129ea9579ff94249bfefd61dc33501b777669abe5db` |

Audit02 retains its authority input, exception and explicit correction context;
the failed script was not copied before editing. Audit03 retains its complete
successful audit source. Neither audit launches a game or repeats a model call.

D19.10 is consumed; combined exposure is **$4.878100/$10**, with every prior
hold and row preserved. This turn's two paid pilots total 30 settled requests /
$0.028933; the first Java-failed attempt dispatches none. Shared-desktop input
stays paused. No new per-run approval is needed under continuing D18/D19.

## Acceptance disposition and next action

M0 remains in_progress and G0 remains fail. Item 6 now has authentic connected
server/avatar/worker/native/helper measurements and independent cost/time
reconstruction, including retained failed outcomes. Full strict successful-pilot
qualification is not claimed for live16b or live17. Live15's earlier full
turn/walk/helper success stays separate; none of these runs is silently replaced.

The next action is a read-only six-outcome scope and lineage audit: determine
which remaining clauses require a new integration result, versus the full
contract/reliability work assigned to later gates. In particular, SPEC16.1 item4
names bounded cancellation, release, reconnect/resynchronization and no duplicate
mutation; it does not by itself demand the whole T07 canonical-checkpoint/soak
matrix. The recorded vanilla cancellation audit and Forge pair04 preserve the
selected mechanics, while pair04's 508.2221/500-ms shutdown failure stays failed
and D13's separate 568.994/1,000-ms result retains its own profile. The current
gateway settings-rejection/CLI fixture passes once in 886.117 ms, with
CAPABILITY_MISSING for `controls.apply`; this is not a full T05 pass.

Do not launch another paid pilot merely to replace bad model play with a passing
sample. First name any missing G0 evidence and explain why the retained results
do not resolve it. Preserve D14, all failures, the original allowance and the complete
M1–M7 roadmap. Do not rebuild the unchanged worker, installation or clock module.

Final source/document review: repository Ruff and whitespace checks pass;
1,573 local links resolve, all 368 previous milestone IDs and 51 later-roadmap
rows remain, and the old append-only progress log is an unchanged prefix.
