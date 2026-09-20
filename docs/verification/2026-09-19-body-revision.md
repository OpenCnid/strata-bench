# 2026-09-19 Mineflayer body revision and authentic CLI checks

Operator-only. M0.2h.1 advances; M0.2h.2 native host/complete freshness conformance
remains open. Affects F01/F03/F06/F09/F16, N01/N02/N03/N06, C09/C15,
T01/T03/T04/T07. No aggregate gate or milestone closes.

## Defect and correction

The pinned Mineflayer 4.39.0 physics plugin sends a position packet each second
while idle and emits `move` for that packet. Strata incremented its state revision
unconditionally for every `move`. That invalidated a previously delivered
observation even when the body had not changed. The preceding [vanilla menu
run](2026-09-19-vanilla-menu.md) showed repeated revision increments while its
visible position stayed unchanged and a CLI action rejected before acceptance.
There was insufficient event-level telemetry to attribute that individual rejection
exclusively to the heartbeat; the unconditional heartbeat invalidation is directly
established by the pinned source and regression test.

[Body revision tracking](../../backends/mineflayer/src/body_revision.ts) now copies
and compares exact body identity, dimension, position, yaw/pitch, velocity and
ground state. Physics ticks, actual/forced movement and spawn events sample that
state; fresh snapshots sample it before recording their revision. Identical
heartbeats do not increment it. Tiny changes, rotation without displacement,
ground/motion changes, replacement bodies and returning to previous coordinates
still invalidate old authority. Invalid numeric values cannot compare equal to
a stable valid body. Disconnect removes the event listeners.

Inventory/window/cursor/health/recipe revisions remain independently fenced.
No stale observation receives a new capture timestamp, and no comparison uses
rounding or movement tolerance. Existing state/control/capability/epoch/sequence,
two-second age, deadline and single-lane checks remain unchanged. No automatic
refresh-and-retry of a mutation was introduced.

Mineflayer capability minor **7** advertises body policy
`exact-body-pose-motion-ground-dimension/1`. The tested capability digest is
`58470703e79269e91d0b00dafa1d2f9e09ce843fc05c7256c45d35bc0ea6e836`.
The separate Forge native motor and JAR were not changed or deployed.

## Executed checks

- TypeScript build passed. **34 focused Node tests passed**, including four new
  body-tracker cases and a real ActionLane regression covering unchanged heartbeat
  acceptance, changed/returned pose rejection and expired capture age.
- Full explicit-JVM/guardian `npm test`: **112 passed**, zero failures/skips,
  **47.531 seconds**. Game effects in these tests remain synthetic. No Java
  source changed; the existing compiled test fixtures were reused.
- `uv run --frozen pytest tests/test_gameplay_package.py -q`: **1 passed**,
  **0.41 seconds**. The allowlisted client still excludes operator/backend code.
- Authentic official vanilla 1.19.2 / online loopback / survival / Node 24.19.0 /
  Mineflayer 4.39.0, using the existing dedicated world and account. All calls
  used the scoped `mcgame` CLI, including a separate process per observation and
  action. The checker waited 1.1 seconds after an observation to cross an idle
  heartbeat, then successfully closed the player menu with that same observation.
- An actual `look_at` changed the body orientation. Reusing the prior observation
  with the next sequence correctly returned `REVISION_CONFLICT` before acceptance.
  Waiting 2.1 seconds on a new idle observation correctly returned
  `STALE_OBSERVATION`. No failed request was automatically replayed.
- Empty close, cursor seed return, crafting-grid seed return and duplicate
  receipt checks then passed through the CLI. **Eight accepted actions**:
  four closes, three slot clicks and one look. Two additional requests were the
  expected freshness negatives. Their accepted/primitive totals are retained in
  the private journal. The report's 38 assertions include repeated connection checks.
- The bounded official server reached readiness and stopped normally after
  **96.813 seconds**, exit 0, complete logs, no force. Read-only inspection of its
  final saved player NBT found exactly the original one wheat seed in hotbar slot
  0, no other items, survival mode and non-operator status.

The server/JVM/dependency identities match the [preceding official vanilla
run](2026-09-19-vanilla-menu.md); the server JAR hash was checked before launch.
No desktop input, model inference, admin gameplay command, item grant or campaign
admission occurred. E9E's pending Windows Security prompt was not operated.

## Evidence and remaining qualification

Private build/test logs and source hashes:
`%USERPROFILE%/.strata/evidence/2026-09-19-body-revision-01/`.
Private server plan/readiness/logs/clean-stop result:
`2026-09-19-body-revision-server-01/` under that evidence root.
Private checker source, capabilities, requests, observations, receipts, journal
and final saved-inventory inspection: `2026-09-19-body-revision-live-01/`.
Credentials, grants and account identifiers remain outside the source repository.

This fixes the demonstrated idle-heartbeat invalidation and provides a narrow
authentic CLI check. Real movement/knockback/dimension/death transitions, full
container/reference cases, native Codex/Dovetail command execution, complete
accounting/isolation/recovery and the rest of T03/T04 remain unqualified. The
original Mineflayer/E9E failure remains recorded; no fallback pass or MVP claim.
