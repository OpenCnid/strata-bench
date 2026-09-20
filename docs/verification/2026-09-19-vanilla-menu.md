# 2026-09-19 authentic vanilla player-menu checks

Operator-only. Partial M0.2e / M0.3b.1b.2b.1c.2, F01/F06/F09/F11/F16,
N02/N03/N05/N06/N08, C09/C15 and T03/T07/T12 evidence. No milestone or
aggregate gate closes. This follows the [D07 implementation checks](2026-09-19-menu-close.md).

## Exact execution scope

Ran the existing official vanilla 1.19.2 dedicated server on authenticated
loopback, survival/normal, with its existing world and Java-owned account. No
desktop input, item grants, operator gameplay commands, world edits or model
inference. The player was not an operator. Its one wheat seed came from prior
ordinary gameplay; the test did not add resources or alter recipes.

- Official server JAR SHA-256:
  `b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96`.
- Temurin 17.0.20.1+1 Java executable SHA-256:
  `1977f302375adbb920d41dac65c7e22eb9c2ed8e1e8d6258964154ff16f14406`.
- Node 24.19.0, Mineflayer 4.39.0, protocol 1.68.0 and locked dependencies;
  `vanilla-development/1`, capability minor 6, digest
  `2385e8d560a5e444a59a1d65557fe82bc94a1fa2309e1750da2185524eb82af0`.
- `tools/development_server.py` verified Java/EULA/online/loopback settings and
  launched with a 600-second limit, Job Object, disk reserve and bounded logs.
  It reached readiness and stopped normally at **337.032 seconds**, exit 0,
  complete logs, no forced stop. All three bounded worker supervisors exited 0.

## Observed behavior and retained attempts

| Case | Result | Evidence and limit |
|---|---|---|
| Explicit close of player inventory with empty cursor/grid | pass | Accepted once, terminal `emitted`, four charged primitive events; full inventory feedback received. |
| Duplicate completed close request | pass | Identical terminal receipt, no second accepted action or additional primitive events in the journal. |
| Pickup a seed onto cursor, then explicit close | pass | Ordinary slot click, visible carried seed, close empties cursor and preserves owned seed count. |
| Put that seed in the 2x2 crafting grid, then explicit close | pass | Ordinary clicks populate slot 1; close clears grid/cursor and returns the seed to own inventory. This is return of an input, not successful crafting. |
| Final persisted inventory | pass | After clean shutdown, read-only server player-NBT inspection found exactly one wheat seed in hotbar slot 0, no other items, survival mode. |
| External containers/full inventory/mod hooks/cancellation/reference parity | not_run | Remain required; this player-menu smoke does not cover them. |

Attempt 1 was rejected before acceptance because the operator checker used a
`+00:00` timestamp instead of the contract's `Z` form. Corrected the checker,
retained its report and stopped that worker's authority. No game action was
accepted or charged in that attempt.

Attempt 2 used the scoped CLI. Empty close, duplicate handling and seed pickup
passed; the subsequent cursor-close request received `REVISION_CONFLICT` before
acceptance. The checker stopped safely. Two actions and six primitive events
remain in that journal. This exposes a live freshness sensitivity when launching
a separate CLI process between observation and action; fencing was not relaxed.

Attempt 3 used the same scoped loopback API directly, avoiding per-call process
startup. No raw bot, packet, hidden-state or admin interface was available to the
checker. It completed six actions: three ordinary slot clicks and three closes,
with **18 primitive events**. All 31 recorded assertions passed, including repeated
connected-state checks. Every terminal action confirmed release without requesting
resynchronization. No uncertain mutation was retried. Each fresh worker started
only after the prior authenticated connection was confirmed absent; old fenced
supervisors were allowed to exit at their bounds. Separate journals and every
attempt's consumed costs remain retained: **24 total primitive events**.

## Evidence and remaining limits

Private server plan/readiness/logs/stop result:
`%USERPROFILE%/.strata/evidence/2026-09-19-vanilla-menu-server-01/`.
Checker source, public requests/observations/receipts and reports are in
`2026-09-19-vanilla-menu-01/`, `-02/` and `-03/` under that evidence root.
The third directory also retains all worker journal copies, source hashes,
the saved player file and a bounded inventory-only result. Credentials, grants,
account identifiers and world data remain private.

Final saved inventory provides authoritative post-stop resource evidence. It
does not provide a time-resolved server trace of each click, an independent
rendered reference, item-component/stack-merge/full-capacity coverage, interrupted
close/reconnect behavior or generic/crafting-table/furnace/chest qualification.
The production CLI freshness concern remains open; the direct API test is
identified separately. Complete aggregate accounting and isolation are unqualified.

E9E's separate Forge client still awaits user handling of its Windows Security
prompt. Its new JAR remains uninstalled and no connected Forge close test ran.
The original Mineflayer/E9E failure remains T03/G0's recorded failure. The broader
implementation, keybinding, native host, reliability, capacity and research gates
remain required. **$0 Strata inference was dispatched.**
