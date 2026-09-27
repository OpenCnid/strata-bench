# Owned gameplay-worker repair pause

M1.1c.3.2 now implements a private pause boundary in the running Forge worker.
The named native Curios repair/restart/rollback cycle remains verified separately
in [M1.1b.1](2026-09-27-m1-settings-cycle-plan.md). This change connects the first
part of that workflow to worker ownership; it does not yet perform settings
repair, restart, commit or resume through the worker. M1 remains in_progress;
T01/T04/T05/T06/T10/T11 and G1 remain not_run at aggregate level.

## Contract and enforcement

The new opt-in `strata/ForgeDevelopmentWorker/3` manual-conformance profile
requires `operator-owned-fixed-repair-pause/1`. Older `/2` workers retain their
existing behavior. The worker writes a separate private repair grant with a
distinct random bearer and loopback port. The public capability manifest still
reports keybindings unsupported; gameplay packaging contains neither the repair
module nor its grant. The repair HTTP route accepts only strict bounded pause
and status requests. No raw native connection or token is returned.

The request binds campaign/avatar/epoch/lease, transaction, plan digest and fixed
expiry within the original worker lifetime. A durable SQLite hold precedes any
handover. The lane waits for an already pending renewal, cancels current input,
requires confirmed release and a known terminal receipt, then checks the exact
body/connection generation and fenced native epoch. New gameplay requests are
refused; repeated action requests still return their original receipts. Native
usage continues through the existing high-water accounting, with no refund or
extra lifetime. Plan changes and expiry extensions are refused.

Expiry, stop, lost native ownership or parent loss causes cleanup and retains
the consumed hold. Journal reopening at a higher epoch refuses pending repair
recovery. There is deliberately no hold deletion or resume operation: qualified
native settings admission, transaction outcomes, restart/rejoin identity and
fresh observation/keymap publication remain the next implementation dependency.
The plan digest is a bound identifier here, not proof that the native settings
transaction or an effect plan has been admitted.

Review found two failure paths and corrected them before the affected regression
run: failed durable intent must actively release an existing motor, and close
must await pending pause work before disposing of its journal. Focused fixtures
exercise both. The initial TypeScript state-narrowing build failure is retained
as a diagnostic excerpt; it was corrected with a post-await live-state check.

## Verification and limits

Exact environment: Windows, Node24.19.0, pinned Java17.0.20.101, production
GameBridgeFixture HTTP/lane runtime with synthetic game body/input, and the
existing Python Windows process guardian. No Minecraft or model run was selected.
The existing native04 Minecraft result is not reused as verification of this
changed worker profile.

Executed checks:

- `npm run build --offline`: passes.
- Focused `node --test --test-name-pattern='repair|Forge capabilities'` over
  `forge.test.js` and `worker_repair.test.js`: passes. Cases cover strict scope,
  fixed expiry, pending renewal, active cancellation, unknown acknowledgment,
  storage failure, close/read race, retained holds, separate endpoint credentials
  and real worker/guardian cleanup after deadline or parent loss.
- Affected Forge/action/worker lifecycle regression: 132 cases pass with no skips
  in 107.5s, including the actual Windows guardian and JVM failure tests. Command:
  `node --test dist/tests/forge.test.js dist/tests/worker_repair.test.js dist/tests/actions.test.js dist/tests/worker_startup.test.js dist/tests/worker_control.test.js dist/tests/worker_health.test.js`.
- Gameplay and worker packaging: `python -m pytest -q tests/test_gameplay_package.py tests/test_worker_bundle.py`:
  18 cases pass. The explicit gameplay source allowlist remains unchanged.

Private logs and source snapshots live under the operator-only
`2026-09-27-m1-worker-repair-01` evidence root. Synthetic process tests are not
authentic Minecraft effect evidence or complete filesystem/process/network
qualification. An endpoint bearer is not a substitute for the final runtime
isolation profile.

## Remaining acceptance work

Connect the existing controller/settings adapter to this worker-owned pause,
bind actual transaction/effect outcomes, implement safe restart/rejoin and
explicit resume or rollback recovery, then verify the complete charged gameplay
repair workflow on its exact profile. Preserve all remaining T05 context,
modifier, hold, unsupported-key, concurrency, crash and isolation cases.
Reconcile affected T01 bindings and final T04/T06 profiles; the full closure path
and unrelated M2-M7 exclusions remain unchanged.

D20 authorizes this implementation. D18/D19 remain M0-only inference authority;
this change uses no new model spending. Preserve all historical failures,
consumed decisions and five separate telemetry holds.

Final read-only audit confirms all40 authority tables unchanged at4,887,796
microUSD, all five historical reservations unchanged in their current WAL-aware
databases, and zero Java processes. All459 milestone IDs are preserved and1,616
local ledger links resolve. The evidence archive contains30files/2,462,176bytes,
seal `0fb98c77aef06a71c515614fafaf1a85d3aa440c8ec66a7068e87718acc1aab8`.
It includes source/doc snapshots before this seal pointer, build/test logs and
authority/process audits. The final strengthened HTTP quota test passes; it does
not change the production code exercised by the affected regression suite.
