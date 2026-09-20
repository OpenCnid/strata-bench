# Authentic cancellation before route arrival

Operator-only. SPEC v0.2.33. M0.3b.1b.2b.2c.2 in_progress;
F01/F06/F09/F16, N01/N02/N03/N05/N06/N08, C09/C15/C18,
partial T01/T03/T07/T12/T13. No aggregate gate passes.

The [prior quest/cancel trial](2026-09-19-native-quest-cancel.md) passed public
cancellation/release/fencing but failed its stronger reference predicate: the
saved player was already within the destination tolerance. This fresh trial
preserves that failure and current saved position. It uses the same exact E9E
1.27.0 / MC 1.19.2 / Forge 43.4.23 / pinned Java / native minor34 artifact,
34 compiled broker modules and 97 launch pins. No runtime behavior changed.

The scoped checker reads at most four immutable public observation pages within
eight seconds. Only pages no older than 1,900 ms enter its map, respecting the
worker's 2,000 ms delivery-authority bound. Pages must have matching dimension,
position and revision. A fresh root observation then authorizes the action.
Unknown cells, unsupported ground and occupied foot/head cells remain barriers.
A bounded six-step cardinal search selects a delivered target at least 2.75
blocks away. It does not read private saves, expand the authorized scene, invoke
native/operator APIs or modify the fixed movement planner. If no such route is
observed, the trial records that condition rather than inventing terrain.

After public displacement over 0.05 blocks, request cancellation once; require
cancelled/released/fenced behavior and reject a fresh action in that epoch.
Private settling snapshots and independent stopped player/region copies follow
the public checker, with no feedback into gameplay. Saved displacement must
exceed 0.03 blocks, saved target distance must remain above the unchanged 0.2
tolerance, and saved/native position and settling differences stay below 0.02.
These references do not establish complete resource conservation or checkpointing.

Bounds remain client 480 s, worker 90 s, action five seconds, 1,000 primitives,
server 600 s plus normal-stop grace and guardian process wait 500 ms. No game
restore, desktop input or inference. Production isolation, complete movement/
physics cases, timing envelope and prior CTM/render/shutdown failures remain open.

Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-native-cancel-01`.
Actual findings, including failed and unexecuted cases, follow below.

## First attempt: no qualifying straight-line target

`worker-01` reaches the authentic world in 166.125 s without startup read retries.
Four immutable pages contain 128 blocks each, at ages 151/719/1317/1930 ms.
The first three enter the checker's map; the fourth exceeds its predeclared
1,900 ms cutoff. No permitted target meets 2.75-block straight-line separation.
An offline check including all 512 already-delivered cells still finds none.
The checker fails with OBSERVED_LONG_ROUTE_UNAVAILABLE, eight public calls,
zero action intents and two charged safety releases. Cancellation is not_run.

All processes stop; server normal save/stop 419.329 s, client procedure 266.828 s,
arguments retired and zero Java verified. Selected saved position and inventory
are unchanged; startup and this one shutdown sample pass. Reference aggregation
remains fail because the required movement did not run. Two PNGs decode; this
does not qualify visual completeness. The failed sample is retained intact.

A distinct follow-up case selects a path with at least three observed cardinal
steps, at least two blocks of endpoint separation and at most six steps. This
measures the available route with turns rather than assuming a straight corridor;
the prior public pages contain such a path. That is a disclosed development
target-selection change, not a runtime/motor change or a pass for the unavailable
straight-line case. No terrain is cleared or fabricated. All cancellation,
saved-stop, release, settling, charge and timing predicates remain unchanged.
Fresh live pages must establish the route again; the offline selector check is
not authentic movement evidence.

## Unexecuted second case and fresh third trial

The second server was confirmed live on continuation, but the operator had not
launched its client and insufficient startup time remained in its bounded window.
Requested normal stop rather than starting a doomed client: exit 0, complete
logs/save, 491.062 s elapsed. This is an operator orchestration delay, `not_run`
for gameplay, not a client failure or pass. No client/action/intent was started;
temporary arguments were retired and zero Java processes checked. Its preparation
and terminal result remain under `worker-02/unexecuted-audit.json`.

Fresh `worker-03` uses the same bent-route checker, runtime and predicates. A
bounded paired-launch driver starts the client immediately after server readiness
(116.781 s), retaining process handles and exclusive evidence files. It does not
change the server/client/action/guardian limits. Five selected stopped-save files
were copied before and after; these are reference inputs, not a complete checkpoint.

The actual client reaches world readiness in 174.891 s without read retries.
Thirteen scoped CLI calls pass, including the intentional stale-lease rejection.
Four public pages yield 384 admitted cells. They establish a three-step path,
3.1428304737 blocks including initial centering, with target (-51.5, 7, 9.5).
The checker observes movement then cancels once; receipt is cancelled/released/
requires-resync, fenced observation is disconnected, and a new mutation fails
with LEASE_EXPIRED. One native intent and 20 charged primitives reconcile across
five usage records; no duplicate intent or native-call failure appears.

All eight independent saved-player checks and all thirteen reference audit
checks pass. Saved position changes from (-50.5, 7, 11.3571695263) to
(-50.5, 7, 11.5673095110): 0.2101399846 blocks of movement, outside the unchanged
0.2-block destination tolerance. Cancellation occurs during initial centering;
this is not evidence that the complete bent route was traversed. Two private
snapshots 600 ms apart settle and agree with the stopped save within 0.02 blocks.
Selected inventory fields agree and 256 delivered block IDs match independent
before/after region decoding. Full resource/mechanics conservation remains open.

End-to-end cancellation CLI time is 359 ms, including process/transport work;
this does not qualify the distinct 250 ms responsive-worker target. Bootstrap
808.4997 ms and initialization 370.4133 ms meet their separate 2,250 ms bounds;
total gateway readiness is 4,279.869 ms. Guardian job termination takes 1.0146 ms;
the unchanged 500 ms wait signals after measured 451.9577 ms. That is one pass,
not reliability certification or a reversal of prior timeouts.

Client procedure passes in 275.969 s; server normally saves/exits 0 in 393.344 s.
Both 854x480 PNGs decode and were visually inspected: terrain, rain, vegetation,
held item and HUD are present. No menu, physical-input or universal first-frame
claim follows. Both process drivers are terminal, arguments retired and zero
Java processes verified. No shared-desktop input, state restore or inference.
Full movement/geometry, UI, isolation, clocks/resources and all release gates
remain open; this resolves the narrow positive cancellation-before-arrival case.
