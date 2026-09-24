# Recorded gameplay failures and cost reconstruction

M0.2c.1d.2; F06/F09/F11/F13/F16, N01/N02/N03/N05/N06/N08;
partial T03/T07/T12/T13, G0 items 4/6. M0 remains in_progress and G0 fail.
D14 and all M1–M7 work remain unchanged. No new Minecraft or model run occurred;
original exposure remains $4.878100/$10, including every unresolved reservation.

## Implemented behavior

Live17 submitted action sequence 3 while the worker expected 1. The worker
correctly refused it, but allocated acknowledgment sequence 1 before the
acceptance transaction checked the action sequence. Its later valid action
therefore produced acknowledgments 2/3/4. This is a journal defect independent
of the model's bad sequence choice and failed two-action goal.

`Journal.accept` now invokes its receipt factory inside the acceptance
transaction, after sequence validation. A refused sequence allocates nothing;
a failed insert/event write rolls receipt allocation and intent back together.
Both Mineflayer and the existing Forge caller use this shared contract. The
Forge error/fencing policy is unchanged. Local tests verify refusal followed by
one accepted/executed/released action with contiguous receipts, duplicate
deduplication, and rollback before dispatch on injected storage failure.
Implementation digests change; existing held runtimes are not rewritten and do
not constitute real-game qualification of the fix.

The reusable private `inspect_completed_pilot_costs` reader now reconstructs
normally completed, settled native jobs even when their recorded gameplay goal
failed. It reuses the complete clock/snapshot/worker/receipt consumers, requires
normal native exit and retains original checks, run status and result digests.
It explicitly does **not** certify gameplay success or action-effect joins.
Unknown usage, incomplete stops, changed measurements, foreign scope, malformed
checks and invalid durations remain errors. The successful-pilot reader keeps
its stricter requirements. No action, prompt target or private route is supplied
to the model by this change.

## Actual retained evidence

Read-only live17 reconstruction passes **12/12** checks: 14 distinct requests,
$0.013918 API-equivalent estimate, 18 broker calls, 5,355 server ticks and 5,235
avatar callbacks. The failed walk, failed original action join and original
receipt gap remain. The strict successful-pilot reader still refuses it. All
40 durable authority tables remain identical.

Private archive `2026-09-24-completed-pilot-costs-01` contains eleven files,
455,826 bytes. Seal:
`edbfd7534307611745e0fe5b60099d0d3b6bec5bfcb8a807f81a2c0f39f9027c`.
Report SHA256:
`c76d3ccbf19e527167822ca5a29d5b105cd82e642d35c70539ce6f4ec24db2e9`.
Original live17 seal remains
`79a76d2d0b97aeea31864d9b37d58509c276e753ce2da352fb0dc80d2c6bfca8`.

Read-only vanilla cancel/reconnect lineage audit rehashes all twenty referenced
artifacts and the original audit source, preserving its thirty passing checks
and raw fail/fail/fail/pass checker outcomes. Against the held instrumented
worker, 27 root compiled modules match, eight differ and two were added
(`worker_control.js`, `worker_health.js`). Adapter, navigation, observation,
inventory, crafting and pagination modules match. Actions/journal changed for
private primitive-charge traces in commit `2ca102e`; runtime, capability and
authentication/Forge dependencies still have distinct pins. These are related
profiles, not a declaration of identical or automatically qualified profiles.

Corrected lineage archive `2026-09-24-g0-lineage-audit-02` seal:
`74e744ac23adcdb222e32f778234250e0b611e48e82b59dd84da0822d18c89f3`.
The first audit's recursive inventory accidentally counted six generated schema
modules as new root modules. Its separate seal remains
`09ab3f599042a65cc0b1a66ac6bb81fbb8093320aaf5a029cc989815b63492f9`;
artifact/hash and authority checks passed in both audits. The corrected audit
compares only direct children of `dist/src`.

## Exact six-outcome review

| G0 item | Evidence and remaining scope |
|---|---|
| 1 | Actual native GPT-6 Luna/Dovetail root/helper and model-selected Mineflayer actions pass the [named development pilot](2026-09-24-native-wire-report-bounds.md). D14 leaves full isolation to M1/G1. |
| 2 | Official installations and the [sealed Forge bootstrap](2026-09-24-sealed-forge-bootstrap.md) pass their named profiles; Mineflayer's exact E9E incompatibility remains unsupported. |
| 3 | [Vanilla mechanics](2026-09-20-vanilla-mechanics.md), [modded machine/expert craft](2026-09-20-craft-witness.md) and actual model navigation have evidence. Their distinct profile lineage must remain explicit in the final gate record. |
| 4 | [Vanilla cancellation/reconnect](2026-09-20-vanilla-reconnect.md) proves release, fencing, preserved receipts and no duplicate mutation. [Forge restart](2026-09-20-forge-reconnect.md) retains the old shutdown failure; the separate [D13 normal-stop case](2026-09-21-d13-shutdown.md) passes its authorized policy. Stock Mineflayer settings rejection is tested. The new atomic acceptance correction still needs its named runtime disposition. |
| 5 | [Private development milestone](2026-09-24-development-milestone.md) has positive/negative controls in its declared D14 scope. Scientific scorer authority and full nonleakage remain unqualified. |
| 6 | The reusable reader now reconstructs actual root/helper costs and measured intervals independently of gameplay success. It preserves failed action joins; complete action/effect reconciliation and the final exact-profile gate assembly remain open. |

SPEC 16.1 item 4 requires the bounded cancel/reconnect trajectory. It does not
require the entire canonical checkpoint/fault/soak matrix: complete T07/T08
remain G2 under 16.2 and roadmap M2. Full T05 is G1. Earlier ledger language
requiring wholesale canonical recovery/isolation for G0 was overbroad; this
review corrects that wording without changing any requirement, threshold,
historical failure or later milestone status.

Next resolve the narrow accepted/refused-action evidence join and qualify the
changed acceptance runtime if used in the closing profile. Preserve unknown
outcomes conservatively; do not turn absence of a journal row into proof of
zero effects. A paid repeat is unnecessary merely to obtain a successful goal.

## Verification

- `npm run build`: pass.
- `node --test dist/tests/actions.test.js`: 37 pass, including the two new
  refusal/rollback regressions. The invocation also named a nonexistent
  `forge_lane.test.js`; the separately selected Forge tests below supply its
  actual coverage.
- `node --test dist/tests/forge.test.js`: 13 pass, 43 opt-in JVM/guard skips.
- Python `test_native_game_measurements.py`: 44 pass in 14.57 s.
- Python `test_native_game_evidence.py test_native_game_retention.py`: 78 pass
  in 15.42 s. One additional strict-success compatibility case passes in 0.98 s (44 deselected). Total 123 distinct focused Python cases.
- Initial targeted JVM fixture failed before its connection because a historical
  classpath lacked `GameBridgeFixture`. Initial offline classpath build refused
  the omitted FTB Library binding. With the existing official hash-checked JAR
  supplied, `:forge1192-client:writeTestClasspath --offline --no-daemon` passes
  in 23 s; existing deprecation warnings remain. Neither failure launches Minecraft.
- Corrected `node --test --test-name-pattern='actual JVM bound observations'
  dist/tests/forge.test.js` with the pinned Java 17.0.20.101 runtime and freshly
  generated fixture classpath: one pass in 1.814 s. This is an actual JVM with
  synthetic game effects, not an E9E run. Total 51 distinct Node cases pass.
- Full repository Ruff and `git diff --check`: pass. All 1,559 local links in
  the changed status/specification/ledger/report set resolve. All 368 prior
  milestone IDs remain, with one new child (369 total); 51 M1–M7 rows and the
  entire previous append-only log prefix remain unchanged.

Synthetic fixtures test journal/consumer behavior, not authentic game mechanics.
The actual evidence here is read-only reconstruction of previously sealed runs.
