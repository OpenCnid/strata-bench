# M1.5b.9c native replacement attempt and retained failures

Operation15 fails. The checker stops before placement because it expects grass
but the delivered support is dirt. Separately, the client guardian exceeds the
unchanged 1,000ms bound. All outer processes eventually terminate, but that does
not repair the guardian failure. No replacement window or protected score is
verified. M1.5b.9c/M1 remain in_progress and T10/G1 remain not_run.

## Bound scope and actual execution

Base b1cbab7; unchanged E9E 1.27.0 / Forge 43.4.23 separate structured client,
minor 45/policy 4 client 31facc27 and telemetry 0.3.18/startup 19 module 061712ce.
[Fixture preparation](2026-09-27-m1-replacement-preparation.md) retains all 8,609
source pins, the exact two-item chest patch and the original 5,000 RF furnace.
The supplied replacement carries 20,000 RF. The V5 first-start-through-first-
refund rule and its machine-plan digest remain unchanged:
`ca9e94888dac60d97cf680f2257c4d35b08f1c75184cc94f507e648e453b0a5d`.

The initial proposed participant/server limits exceeded launcher contracts.
Before dispatch, a distinct record binds worker 60s, client 340s and pair 350s
within existing participant 360s/server 600s caps. Bootstrap 270s, guardian
1,000ms, 1,000 primitives and 256 MiB/100,000 telemetry events remain unchanged.
All 569 pair inputs and eight audit scripts are pinned before a single fresh
session and dispatch. No installed artifact or implementation source changed.

The first 15 requests emit once, with 65 primitives, 143 native records and
91 CLI calls. They withdraw supplies, clear the observed grass in front,
process two items until the original furnace stops, recover one ingot and the
unfinished input, equip the pickaxe, remove the furnace and equip the replacement.
No placement request is created. The next read finds minecraft:dirt at
(-51,6,13), and the checker fails PLACEMENT_SUPPORT_CHANGED. Safety stop succeeds.
The original fixture had grass_block at that coordinate; the precise cause/time
of its change is not established by this evidence.

## Terminal and evidence disposition

| Observation | Actual result |
|---|---|
| Native reference/control | fail |
| Pair duration | 684.782s |
| Public requests / placement requests | 15 / 0 |
| Guardian | timeout; tree proof not started |
| Independent conservative root-exit interval | 1038.4428–1068.2396ms |
| Outer retained/signaled client / server histories | 206/206 / 29/29 |
| Outer forced cleanup / remaining owned runtime | none / none |
| Server stop | exit 0, stop sent, no forced server stop |
| Pair/protected/preparation/dispatch rows | all UNCERTAIN |
| Current telemetry reservation | RESERVED, 268,435,456 bytes, actual settlement null |

The independent held-process observer corroborates an actual exit beyond one
second; its later terminal observation does not turn the guardian into a pass.
Session arguments retire and the input desktop is unchanged. The full signed
stream authenticates and contains a clean-stop record: 1,455 records /
9,739,789 bytes, 1103 furnace ticks,
52 processing calls, two starts, one completion and one removed lifetime.
There is no replacement lifetime and no final refund. These are diagnostic
observations from a failed reference, not accepted protected-window evidence.

The stopped saved copy confirms dirt support and air at the former furnace
position. Player delta is one ingot, two dust, one diamond pickaxe and one
furnace item. The unplaced replacement retains 20,000 RF. These selected saved
resources do not claim a complete game/agent checkpoint.

The pre-pinned failed-reference audit passes: the actual V5 store rejects import
with CRAFT_PROTECTED_REFERENCE_UNQUALIFIED, creates no receipt and changes no
outbox event. Seal cursor 9 precedes reservation 12 and the original plan bytes
are preserved. All 91 public command outputs omit private diagnostic markers.
The separate failure audit passes while retaining the native and guardian fail.
Success audits/publication remain unexecuted.

Operation15's full 256 MiB reservation remains held. Operation10's separate
256 MiB hold is also preserved: two distinct unresolved reservations, no refund
or consolidation. All 40 accounting authority tables remain unchanged at
4,887,796 microUSD, including all historical inference holds/consumed decisions.
There were no model calls and D18/D19 remain M0-only.

## Correction and next resolving action

A separate candidate checker makes one exact source change: the delivered support
at the same coordinate may be grass_block or dirt. It retains the air-destination
check and the native placement motor's exact support identity, reach and hit-face
checks. It changes no action, recipe, resource, lifetime selection, time limit or
acceptance condition. The original failed checker and all prelaunch hashes stay
intact. The corrected checker compiles, but native execution remains unverified.

The guardian delay is unresolved. A read-only comparison finds approximately
8.080 GB last pre-stop working set here, versus 8.141 GB in passing operation14;
handle counts are 2,120 and 2,121. Both have incomplete region censuses and one
resource query overlapping the guardian interval. This is not causal evidence
for a memory or observer remedy. No heap/GC change, timing waiver, repeated old
memory/graphics suite or new native run follows from this comparison.

Next run the corrected full control once under a fresh identity only after
complete prior binding and durable/process rechecks. It must meet every original
replacement/resource and guardian/terminal criterion. Any new pass cannot erase
operation15's failure or establish a general shutdown remedy. Wider scorer
controls/authority, isolation/native-host, keybinding and matched probes remain
required for G1.

Private roots: 2026-09-27-m1-furnace-operation-15 and
2026-09-27-m1-replacement-native-preparation-01 in the operator evidence store.
All original evidence, unused success scripts and source-only next-refusal review
are retained. No raw game, credentials or evaluator data is published.

## Final audit and sealed evidence

The final failure audit passes: 569 original inputs and prelaunch scripts are
unchanged, all 457 milestone IDs and append-only history survive, and 1,783 local
links resolve. Both distinct 256 MiB holds and all 40 authority tables verify.
The original native/guardian failures remain fail and replacement remains unrun.

The native bundle contains 711 files / 116,897,875 bytes, with seal
`d23c20a1170469458cb956289b7e8894cdf6f32d7ebd08a0c2bf39163909db56`.
The preparation bundle contains 34 files / 3,388,118 bytes, with seal
`7f1ebec8f40da05e859dd74fd764ef0c4725484b1332de1a0b196de577046835`.
Both verify. The preparation contains pre-seal document snapshots; this public
seal pointer was added afterward without rewriting either archive.
