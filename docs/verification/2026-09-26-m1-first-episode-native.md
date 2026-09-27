# M1.5b.9a native first-episode negative control

The negative control passes: operation13 completes two authentic furnace
episodes, and the actual V5 store rejects the selected first episode despite
a later sufficient episode. M1.5b.9a is verified for this named control only.
M1.5b.9/M1 remain in_progress; T10/G1 remain not_run.

## Prior contract and exact profile

Source6c9843d; unchanged V5 machine plan from operation12, including the first
start through its first subsequent refund and minimum84 ticks, two outputs and
8,000 RF net. The machine-plan digest remains
`ca9e94888dac60d97cf680f2257c4d35b08f1c75184cc94f507e648e453b0a5d`.
New private control criteria are sealed before launch: first one-item episode,
then a separate two-item episode; expected selected output zero and
MACHINE_OPERATING_DURATION. No after-the-fact change to the registered rule.

Reuse E9E1.27.0 / Forge43.4.23, separate structured Forge client minor45/policy4
(31facc27), telemetry0.3.18/startup19 (061712ce), the same8,609-file fixture,
20,000 RF initial furnace and three supplied dust. This is a scripted authentic
reference, with no model call, Mineflayer compatibility or full isolation claim.
All565 inputs are pinned. Existing client335s/worker45s/participant360s/server600s,
bootstrap270s and guardian1,000ms limits are unchanged; launch8/protected3 retains
256 MiB/100,000 events. Historical failures and operation10's hold remain.

The changed checker uses only the scoped ordinary game CLI. It collects three
dust, places one, returns the remaining two to an owned slot and collects the
first output. It then places the two remaining dust, collects two later outputs
and closes the machine. No admin/evaluator route, synthetic producer event,
replay or resource reset occurs. Prelaunch audit scripts and their hashes are
retained separately from gameplay/helper contexts.

## Authentic evidence

17 operation checks, 17 actual V5 import checks and the independent
episode/capacity/terminal audits pass. The full stream has 2,075 authenticated
records and 1,648 complete native furnace ticks, with three completions,
126 processing calls, three starts, two refunds, actual unload and clean stop.
All134 processing/completion/transition children join their original tick traces.

| Episode | Ticks | Outputs | RF debited | RF refunded | Net RF | Registered selection |
|---|---:|---:|---:|---:|---:|---|
| First | 42 | 1 | 4,032 | 32 | 4,000 | Rejected: duration below84 |
| Second | 84 | 2 | 8,064 | 64 | 8,000 | Cannot replace the selected first episode |

The store retains three completion candidates but returns zero selected output,
candidate_complete=false, no window witness and MACHINE_OPERATING_DURATION.
The plan is prior-registered: seal cursor9 precedes reservation
12; actual import cursor2112, with idempotent reopening.
The actual first-episode rejection is preserved on both raw comparison and
registered inspection. No best-episode search or credit borrowing occurs.

An explicitly unregistered, read-only comparison of the later exact interval
passes with two outputs. Its plan and result are archived with prior-registration
and scoring flags false. It is a selectivity control, never a new grant, rewrite
of the original plan or protected result. The first episode is a completed but
insufficient operation; this does not claim a mid-cycle interruption or
underfunding control.

The12 unique actions use 44 primitives across 121 native frames and
83 CLI calls. Saved inventory gains three ingots, no dust remains, and the
furnace is empty/inactive with8,000 RF. Both episodes' source recipe, resource,
RF, progress and lifetime joins pass. Pair 668.219s; guardian
841.9155ms. Complete retained terminal histories:
client190, server29; no forced cleanup, session retired,
no owned runtime. All four lifecycle rows STOPPED and the launch remains consumed.

Capacity settles atomically at 14,676,085 bytes, releasing
253,759,371 unused bytes from this reservation only. All40 controller
accounting tables remain unchanged at4,887,796 microUSD. D18/D19 remain M0-only.
No game artifact/source implementation was changed and no unchanged test suite
was rerun. Native preflight diagnostics, extra reacquisition and early-abort
branches were not exercised and gain no claim.

## Verification and remaining gate

Executed private procedures: audit_operation.py, inspect_reference.py,
audit_processing.py, audit_intervals.py, audit_capacity.py, audit_terminal.py
and audit_diagnostic.py, using the workspace Python with explicit source paths.
The diagnostic result is not_run; all named acceptance audits pass. They verify
complete signed evidence and actual stopped SQLite/import/save state. Their
prelaunch hashes, transcripts and frozen database are retained. No private
runtime material is committed.

Native underfunding, interrupted/replaced/refused/unstable machine controls,
remaining scorer negatives/alternatives, full setup/team/loaded-code authority,
fluid/automation provenance, telemetry overhead/parity and protected scoring
remain open. So do G1's native-host/helper isolation, keybinding and matched
probe contracts. No positive run is repeated or old reference upgraded. Next
advance those named native negative boundaries; full G1 is not passed.

Private evidence roots are2026-09-26-m1-furnace-operation-13 and
2026-09-26-m1-first-episode-native-preparation-01 in the operator evidence store.

## Next resolving native control

Read-only reinspection of the sealed [exact Thermal bytecode](2026-09-26-m1-scorer-coverage.md) identifies a concrete low-energy interruption case. After a processing call, insufficient RF invokes processOff, which clears unfinished progress without refund. A new fixture with5,000 RF and two supplied inputs is predicted to complete one item, stop after52 funded ticks with8 RF/one input remaining, and have no final refund. This is a source-based prediction, not executed evidence. Prepare and seal that distinct fixture before testing MACHINE_OPERATING_REFUND_MISSING. Ordinary caller checks do not establish reachability of a partially funded processTick call; preserve that synthetic case and require separate native applicability evidence. Replacement/refusal and all wider gates remain open.

## Final audit and immutable archives

Final audit passes565 source pins,455 milestone IDs,1,767 local links, original
operation10/12 seals and all40 unchanged authority tables. Original operation10
retains its256 MiB hold. Diff check passes; no implementation/artifact changes.

- Operation13:707 files/140,994,506 bytes; SHA-256
 `694f4cfbea2e11df7192e34a64e025fb9ccc7a320b6b3ed6471c257ca6f6d1c0`.
- Preparation:19 files/3,395,676 bytes; SHA-256
 `218e8e8867a3e6e21ee1412e95dc8a060a3d8b846b3824110dd84e94c41fe179`.

The archived documentation snapshot precedes this seal-pointer addition.
