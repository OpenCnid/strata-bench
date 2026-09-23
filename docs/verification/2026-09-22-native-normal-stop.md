# Native completion and normal worker/server stop

September 22, 2026. Operator-only. M0.1d.8c is `implemented_unverified`:
the connected source and synthetic process checks pass; the changed runtime
still needs a new sealed launch identity and authentic native/game execution.
M0 remains incomplete and G0 is `fail`.

Coverage: parent M0.1d.8 requirements/contracts, plus N03; partial
T01/T02/T03/T04/T06/T07/T12/T13 and G0 items 1/2/4/6. SPEC 0.2.126 records
the explicit profile. No later roadmap work or acceptance threshold changes.

## Connected behavior

The previous sealed recovery has a 22.713-second native lifecycle while the
server runs 209.640 seconds: after native closure, the runner waits for the
worker's 180-second wall budget. That successful old run and its limits remain
in [the recovery report](2026-09-22-native-recovery-verifier.md).

[WorkerRuntimeBundle/2](../../src/mcbench/worker_bundle.py) now pins the explicit
operator stop policy and command argument. The
[held launcher](../../src/mcbench/pack_worker.py) opens the operator pipe only
for the actual worker; preflight remains noninteractive. The
[parent worker](../../backends/mineflayer/src/worker.ts) uses
[a single bounded command](../../backends/mineflayer/src/worker_control.ts) to
request its existing child drain, stop renewals and measure child exit.

The [native runner](../../tools/m0_native_game.py) persists
[stop intent](../../src/mcbench/worker_stop.py) before sending once, validates
the exact receipt and complete normal owned exit, then requests one normal
server stop. Malformed/duplicate/stale/premature/oversized commands, incomplete
input, uncertain writes, forced exits and missed drain bounds cannot pass.
No gameplay or helper command surface is added. The new runtime changes pins;
old runtime bytes, PackLocks and recovery identities remain immutable.

[Server lifecycle evidence](../../tools/development_server.py) flushes spawn,
ready, stop-command attempt/write, exit and snapshot boundaries. The
[read-only verifier](../../evaluator/src/strata_evaluator/native_game_stop.py)
joins those events to the exact worker/owner receipts and server request,
checks order and the existing server deadline, and reports the observed spans.
It does not infer ticks from elapsed time or claim authoritative active time,
clean save, writer exclusion or a complete canonical checkpoint.

The worker uses the existing 2,250-ms drain allowance from receipt of the
operator request, with a separate five-second outer exit allowance. The server
retains its 120-second normal stop window. These development lifecycle bounds
do not replace D13's separate 1,000-ms Java emergency tree gate or reclassify any
old 500-ms failure.

## Executed source and synthetic verification

Windows, Python 3.12.14, Node 24.19.0; existing locked dependencies.
`PYTHONPATH=src;evaluator/src;tools;tests`, `PYTHONDONTWRITEBYTECODE=1`.

- `npm run build --prefix backends/mineflayer` passes; Node worker-control and
  startup selection: **19 passed**, zero skipped.
- Initial worker-stop/bundle selection: **42 passed**. This includes real owned
  Node/child processes using synthetic fixtures: normal drain succeeds and a
  deliberately hung child fails with retained intent and no replay.
- Affected pack/native evidence/sealed/continuation selection: **138 passed**.
- Stop/server-lifecycle/runtime/sealed/controlled-launch/gameplay-package
  selection: **88 passed**. Real owned synthetic console processes separately
  exercise operator-requested and wall-deadline stop, with exact lifecycle
  events and normal exit. No Minecraft or real save is claimed for them.
- Refactored archived-runtime and new controlled-runtime selection:
  **13 passed**. The new policy, exact argv, stop intent/reference and downgrade
  controls are exercised. Final changed stop/runtime negative selection:
  **15 passed**, including missing control module and malformed process counters.
  These selections overlap; their counts are not added.
- Ruff and whitespace checks pass after correcting two initial statement-style
  findings and the test fixture's import style. Existing Typer/Click warnings
  remain. The gameplay package still contains only the scoped CLI, errors,
  package metadata and sanitized skill; operator control stays outside it.
- Documentation checks validate **1,288 local links**, preserve the old progress
  log as an unchanged prefix and all M1–M7 rows, and leave SPEC sections 3 and
  15–19 unchanged. No Java process remains at the final check.

## Actual private runtime preparation and import

The changed private runtime is prepared with **11,723 files / 654,081,296
bytes** and manifest SHA-256
`dce7f4f2ba11f42f3387d60e6cd1449409f7323aa895ad060bbc4a4e86c28710`.
It resides at
`C:/Users/Darian/.strata/runtime/vanilla1192-worker-stop-01/runtime`, with the
manifest beside it. The explicit v2 policy and preflight import pass while
the runtime is held. All **three owned processes** exit normally, with zero
active or forced-terminated members. Import and its owned checks take
**2.500 seconds**; this excludes preparation time.

The actual capability digest is
`0a522b153be9c2aba8dc21d9560c7fd6194bcd9ce90eebaeef35efb2b475f492`.
Original runtime bytes and all executed worker source pins remain unchanged
through copying/import. All **34 original authority tables** compare exactly
before/after; original accounting and consumed D12 remain unchanged. No avatar,
game server, authentication callback, actual model request or shared input is
started by this import.

Private audit `2026-09-22-worker-stop-runtime-01`: **9 files / 9,258,582 bytes**,
seal `2974d34f38c85513ca060e5155461138fe0566681d5f355124aeae5bdf1b18d0`.
Its complete inventory independently verifies. The archived manifest pins the
external software files; those installation bytes remain in the private runtime
directory, not the small audit archive or public source.

## Remaining integration and acceptance

Bind the prepared runtime to a new reviewed sealed launch identity, and
exercise one changed native/vanilla run. Preserve the
original sealed profile and campaign baseline; do not swap new bytes into it
or silently resume under changed worker identity. The old successful execution
and recovery pair must not be repeated unchanged.

Authoritative server/avatar ticks and active intervals, clean-save custody,
private scorer/setup controls, isolation, E9E qualification and authentic model
integration remain open. The original $10 API-equivalent allowance retains
$0.7554 unresolved plus $0.001458 settled; D12 is consumed and general model
admission remains blocked. No game, actual model request or shared-desktop
input ran for this source change. M0 incomplete; G0 fail; goal remains active.
