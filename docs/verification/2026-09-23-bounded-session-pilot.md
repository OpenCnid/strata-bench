# Bounded native session and D19.3 pilot

Operator-only. M0.1d.9c; F03/F04/F06/F11/F16, N01/N02/N03/N04/N06;
C06/C09/C12/C15/C20; partial T01/T03/T04/T06/T07/T12, G0 1/4/6.
M0 remains in_progress, G0 fail; M1–M7 unchanged.

## Measured problem and change

D19.2 completed the model-chosen turn, including stopped server state, but
native's overall 90-second deadline cancelled request nine after 10.358 seconds
of its 60-second response window. No walk was submitted. Its full $1 envelope,
the earlier full $1 failed envelope and old $0.7554 hold remain reserved.

Fresh D19.3 and later admissions now declare at most 180 native seconds. Older
decisions remain 90 seconds and cannot admit the longer profile. Public prompt,
native launch, preflight transfer and durable reservation bind the declared
duration. Twelve requests, zero helpers, $1 per job, the original $10 allowance,
60-second response cap and two actions each bounded by 2000 ms remain unchanged.
The model chooses every target from its public observations.

The sealed worker lifetime is 360000 ms and server lifetime 440 seconds, inside
the existing outer 600-second watchdog. Baseline import policy /2 permits only
the declared worker lifetime change alongside reviewed client/runtime changes;
all other worker settings, installed inventory and server profile are unchanged.
The existing controlled worker bundle and official vanilla installation are
reused without rebuilding or downloading. Imports remain new unplayed campaign
baselines, not recovery or complete checkpoints. Legacy policy /1 remains strict.

## Source verification

`python -m pytest tests/test_native_piloting.py tests/test_pilot_budget.py
 tests/test_luna6_pilot_budget.py tests/test_pack_baseline.py
 tests/test_pack_restore.py tests/test_sealed_native_game.py
 tests/test_worker_stop.py -q`: 225 pass in 110.13 seconds. Changed-file Ruff passes.
These are synthetic contract/integration tests, not autonomous gameplay.
They include real sealed-store restoration and offline consumption for the new
policy, rejection of altered primitive/server budgets and unsupported durations,
and preserved earlier decision bounds and retained unknown amounts.

## Profile publication

Fresh `vanilla-1192-pilot180-20260923` sealed successfully with PackLock
`cas:sha256:8732b0704fdaff54f7ca4fde3e6eccc628c3878ac43c00f4d39631054340e1c2`.
The baseline import passed live shared validation. No game/model process or
new acquisition was used. All original rows were preserved; only provisioning,
objects and outbox appended, while 36 of the 39 compared tables and every
accounting/allowance value remained unchanged. The existing runtime was reused.

Private publication bundle `2026-09-23-pilot180-profile-01`, 15 files, seal:
`31bc73d686fb3698b2fffabc50cdf6d72168990600b3d3dacd46928d3c331bce`.

## Preflight and admission

Pinned native CLI preflight12 passes 17/17 checks with three synthetic provider
requests, zero helpers and normal native finalization. The actual preflight
consumer accepts the 180-second profile. Fresh input preparation passes all
identity/profile/baseline checks with all 39 durable authority tables unchanged.
Before dispatch, committed/reserved exposure is $2.804133. This run's separate
$1 reservation gives a maximum $3.804133 within the original $10.

| Private evidence bundle | Seal SHA-256 |
|---|---|
| `2026-09-23-luna6-native-12` | `1a6a17075f30df466fc35fb5edf9396316cb465567fee2d8eaa5d02b196f5223` |
| `2026-09-23-m0-pilot-d19-03` | `caf2b0262d9610168b3202d0a09e409ffa6f88693972d9f13748135de81ac314` |

## D19.3 live result

All eight real GPT-6 Luna requests settled for $0.009098. Native finalized
normally, exit 0, after 85.009247 seconds. This run did not reach the old
90-second boundary, so it does not independently test survival beyond it.
The model chose and completed a 30.9-degree turn, with one emitted primitive,
released controls, target yaw error 0.001112761 radians and health 20 unchanged.
The journal, fresh observation and stopped server's saved player agree. Saved
player SHA-256: `543f3365fead2bb2c432a83e81df2b80fab640c36cd3df6709386cdba074224a`.

No walking action was submitted. The model ended voluntarily, saying its
observations did not establish a safe level target. Thus native/accounting
completion passes, but the complete turn/walk pilot remains fail. All 53 owned
processes are terminal without forced termination. Normal worker drain was
42.7849 ms, 94 ms as observed by its owner; outer elapsed time was 252.375 s.
The native/worker two-action journal join correctly remains false for one action.

Exposure is $2.813231, including every previous hold. No new unknown amount was
created. Original rows in nine accounting/history tables, consumed D12 and the
$10 authority are unchanged. Totals: 69 attempts, 66 valuations, $0.067473 in
settled valuations (do not add held-envelope children to exposure a second time).
Live bundle `2026-09-23-m0-pilot-live-10`: 4327 files / 195358335 bytes, seal
`c57629be3eb5cd7958dcbfca55b274d5befd2e2ceee68a140a71c7036d276102`.

## Observation and terrain diagnosis

The model read two pages before its turn, then only the first page of the
post-turn observation. That page remained truncated. The second earlier public
page contained a ground candidate with clear body/head cells. An operator-only
stopped-world inspection found raised terrain on two cardinal sides and missing
level support on the other two. This first suggested an unsuitable start, but
that cardinal check alone cannot rule out a diagonal route.

A separate offline invocation of the exact pinned planner reconstructed only
previously delivered public block IDs (default block states, no raw-world access
during planning). It found a one-step diagonal route from the second public
page. Motor/physics feasibility is still untested. The diagnosis explicitly
supersedes the initial categorical baseline interpretation; no new baseline or
private target is supplied to the gameplay model. Supplement
`2026-09-23-pilot-terrain-diagnosis-01`, seven files, seal:
`13bec5097b22dd5cf92d4fec18ae8092e38570b1a8cc995ccd03440d44aa2d09`.

Public instructions now clarify that a fresh post-turn observation starts at
page one. When it is incomplete, inspect further pages before declaring no safe
route; report observation/budget incompleteness separately. The model still
chooses its own target from returned cells. No coordinates, hidden map, route
program, motor change or acceptance relaxation was added. All 53 native-piloting
source tests pass after this instruction change (11.43 s; included in the 225
distinct cases above). Fresh native13 passes 17/17 checks with three synthetic calls, zero helpers
and normal native finalization. The real consumer accepts it. Input preparation
preserves all 39 original authority tables and the sealed template. The distinct
D19.4 / m0-pilot-11 run executed under D18/D19, with maximum reserved aggregate
exposure $3.813231. Its actual result follows.

| Follow-up private evidence | Seal SHA-256 |
|---|---|
| `2026-09-23-luna6-native-13` | `1496f4a3b49faa098a9f75b30effde59395fab68e477904bcbc7dbb53c2c9e70` |
| `2026-09-23-m0-pilot-d19-04` | `c8454ac08503b856aec89deddc0a23a2e2d8437398d6e20ec87978df786f2911` |


## D19.4 live result and remaining input error

All nine real GPT-6 Luna requests settled for $0.009413. Native finalized
normally, exit 0, in 96.464657 seconds, beyond the prior 90-second
boundary. The longer session profile allowed this complete native conversation.
The model chose both actions itself; no target or route was scripted by the
operator. Its 108.45-degree turn completed with one primitive, released controls
and a fresh observed yaw error of 0.000262693 radians. Health remained 20.

The walk was submitted and accepted for execution, then failed with
`PATH_BLOCKED` before emitting any movement primitive. The model selected feet
position (-64.5,80,25.5), which falls in cell (-65,80,25), while citing support at
(-64,79,25). That cited support's top-center is (-63.5,80,25.5), the avatar's
current position. The submitted target's support cell was absent from its fresh
128-cell public page; body/head air alone did not prove support. The page was
still truncated. This mismatch is recorded in `input-diagnosis.json`, joined to
the actual model message, action and delivered observation. No transport failure
occurred. The model stopped and accurately reported `PATH_BLOCKED`; no blind
replay occurred. The full turn/walk acceptance remains fail.

This fresh run spawned at a different position from D19.3, despite using the
same restored world baseline. No identical-spawn or matched-route claim is made.
The previous offline diagonal candidate is specific to D19.3 and was never
provided to this model. Pagination instruction delivery is implemented and
native-tested, but this run did not exercise page consumption: it believed its
first page sufficed and made the coordinate error instead.

The final public pose, dimension, health, food and inventory match the stopped
server's sole saved player. Player SHA-256:
`00ccf4ad84483c30f20fb6d0dbe807d9d483800932dccf759c0760ca58db4dbc`.
All 53 owned processes are terminal with no forced termination. Worker drain is
normal at 26.9465 ms; outer elapsed time is 228.625 seconds. The two-action
successful-journal join remains false because the walk failed. No complete
checkpoint, isolation qualification, scientific learning or full G0 pass follows.

Original exposure is **$2.822644 / $10**, with every old unresolved hold/envelope
unchanged and no new unknown usage in either fresh run. Original rows in all nine
compared accounting/history tables and D12/allowance remain unchanged. Totals are
78 attempts, 75 valuations and $0.076886 in settled valuations. The two fresh
runs together cost $0.018511 API-equivalent.

`2026-09-23-m0-pilot-live-11`: 4371 files / 198517274 bytes, seal
`5e221b4b9cd4b64748815e4353bc9abc364713c168e981f19a1285d0ecbaf685`.

Next: improve sanitized coordinate-construction and target-recheck guidance so
the model chooses an observed support tile, computes its top-center correctly
(including negative coordinates), and verifies that exact target's support,
body/head and nonzero displacement. Preserve model target selection and the
existing motor/map boundary. Use fresh native preflight and a distinct D19.5
admission after that relevant change; do not retry unchanged, script the route,
feed private coordinates, or ask again for standing D18/D19 permission.
