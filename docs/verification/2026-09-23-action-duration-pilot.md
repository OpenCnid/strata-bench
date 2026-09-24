# Public action-duration semantics and D19.2 pilot

Operator-only. M0.1d.9c; F03/F04/F06/F11/F16, N01/N02/N03/N04/N06;
C06/C09/C12/C15/C20; partial T01/T03/T04/T06/T07/T12, G0 1/4/6.
No M1–M7 expansion, isolation qualification or full G0 pass is claimed.

## Change and evidence basis

The retained D19.1 turn was accepted with `duration_ms=500`, then cancelled
about 516 ms later. The action watchdog uses the minimum of duration, absolute
deadline and worker lifetime. The pinned Mineflayer physics plugin advances
yaw at 3 radians per second, in ordinary physics ticks. Its selected target
required approximately 1.373 radians (458 ms nominally), leaving little margin
for tick scheduling and execution overhead within 500 ms.

This explains why the selected short budget was unsuitable; it does not prove
the exact packet/tick sequence of that retained cancellation. Its post-action
observation was disconnected and stale, so no unchanged-pose claim is made.

`native_piloting.py` now publishes the existing semantics: `duration_ms` is an
execution timeout, not a rotation-speed or hold-time command. The ordinary
pilot prompt and immutable public contract recommend the already-permitted
2000-ms allowance for turn and walk. Completion releases immediately. The
instructions also explain timeout fencing/disconnection and the need to check
connection state and capture age before interpreting effect observations.

No motor implementation, yaw speed, action limit, receipt check, target, route,
spend allowance or acceptance threshold changed. The LLM still chooses the
target from public observations. D19.2 / m0-pilot-09 is a fresh changed-profile
test under continuing D18/D19 authority; D19.1 is retained and never replayed.

## Verification before paid execution

`python -m pytest tests/test_native_piloting.py -q --tb=short` passes all 51
cases in 10.37 seconds. Changed-file Ruff passes. No new mirrored-string test
was added for the instruction text. Existing native/public-contract execution
tests and the actual changed pilot cover its consumption.

Fresh pinned native CLI preflight11 passes 17/17 checks with three synthetic
provider requests, zero helpers and normal finalization. The real preflight
consumer accepts it. The unmodified controlled Mineflayer bundle and fresh
restored vanilla instance pass preparation. All 39 original authority tables
remain unchanged through preparation; no model/game ran during those checks.

The original exposure before launch is $1.804133, including the full old
$0.7554 hold and D18.4 $1 envelope. The new job reserves at most $1, for a
maximum combined $2.804133 within the original $10. It retains twelve requests,
90 native seconds, 60 seconds per response, two actions of at most two seconds,
one avatar and zero helpers. No new approval was needed.

Private evidence under `C:/Users/Darian/.strata/evidence/`:

| Evidence | Seal SHA-256 |
|---|---|
| `2026-09-23-luna6-native-11` | `9596409e4d811d7ba1214e18ddeaabb193a4609d0b43e42bc1440aedb6df37f5` |
| `2026-09-23-m0-pilot-d19-02` | `1ee45052163b9c62e2ee0be7bdefba4f5211f40db042dc7c15d5d3e77c68f2db` |
| `2026-09-23-m0-pilot-live-09` | `ed421479f90977c261a3fcb8f4d8676a4465b0042ee314608e9bb0baf6b0a946` |

## Live result

The model selected and completed a turn using `duration_ms=2000`. The delivered
terminal receipt and independently read worker journal agree: sequence 1,
status completed, one emitted primitive, release confirmed, no error and no
resynchronization requirement. The journal has exactly one action and one
charged primitive. The ordered fresh public observation confirms a 78.75-degree
yaw change, target-yaw error 0.001046 radians, unchanged position and health 20.
The recorded action completed about 458 ms after acceptance; it did not hold
controls for the full two-second allowance. This is actual GPT-6 Luna choosing
a target through the native loop and Mineflayer executing it, not scripted play.

A separate read-only check of the stopped server's sole saved player also
matches the final connected observation using the existing `player_matches`
projection. The sealed player file SHA-256 is
`bedfc03cbf86ff7862f3ee3583c19bff01500a42b0afa70752150673baff9cf6`.
Saved yaw error is approximately 1.75e-11 degrees and pitch error 1.91e-7
degrees. The existing projection also checks position, dimension, health,
food and inventory. This confirms the turn reached saved Minecraft state;
it does not make the incomplete model/job checkpoint complete.

The overall pilot remains failed. At 90.384056 native seconds, the harness
stopped native execution with `runtime_hard_timeout`, exit 125. Request nine
was still streaming. Its transport diagnostic records `TRANSPORT_CANCELLED`
during `response_body`, 10,358 ms elapsed against a 60,000-ms request limit,
with 32,677 retained bytes. Together with the native stop reason, this locates
the interruption at our overall native deadline; it was not the per-request
timeout or a Minecraft action failure. No walk was submitted. The original
D18.4 cause remains unproven; this later diagnostic does not rewrite it.

Eight requests settled for $0.006746; request nine remains unresolved. Preserve
its reservation and the complete $1 D19.2 job envelope, including the settled
children without double counting. Original exposure is now **$2.804133**.
The older $0.7554 hold and D18.4 $1 envelope remain unchanged. All original rows
in the nine compared accounting/authorization/history tables, D12 and the
original $10 allowance are unchanged. Totals are 61 attempts and 58 valuations.

All 53 outer-owned processes are terminal, with no forced outer cleanup;
native's own hard timeout remains a failure. Worker drain is normal in
38.2453 ms (94 ms as observed by its owner); its seven owned processes are a
subset of the outer total. Server stop evidence is retained. The outer run
finished in 266.468 seconds. The sealed live bundle contains 4,292 files /
190,258,241 bytes, with no copied authentication cache. No complete checkpoint
or full clock/isolation qualification is claimed.

## Next resolving work

The action-duration clarification has real evidence of use and a completed
model-selected turn. Sustained turn/walk gameplay remains unproven. The next
profile must provide enough overall native time and corresponding worker/server
lifetime for both actions; changing only the per-request timeout cannot solve
the observed 90-second cutoff. Record that new bounded development profile,
retain old bounds/results and use a distinct D19.3 admission with all three
unresolved holds/envelopes retained inside the original allowance. This is an
implementation/profile change under continuing D18/D19 authority, not a new
spending allowance or a replay. Do not rerun the unchanged 90-second profile or
return to evaluator expansion as the immediate next task. M0.1d.9c remains
in_progress and G0 remains fail.
