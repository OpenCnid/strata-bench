# Native completion and normal worker/server stop

September 22, 2026. Operator-only. M0.1d.8c is `implemented_unverified`:
the connected source and synthetic process checks pass; a new sealed launch is
prepared. Its first attempt failed before Java/native startup. The capture-scope
fix has focused verification; post-fix authentic execution remains pending.
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

## Changed-profile baseline connection

The follow-up source connects an explicit `WorkerProfileBaseline` to the existing
restorer, held worker, native runner and offline evidence verifier. It requires
both durable sealed identities, exact installed inventory and unchanged server
configuration, while preserving the original snapshot identity. Player-history
files and a nonempty user cache reject; the imported worker requires epoch 1,
and the old-campaign recovery path rejects this import policy.
Materialization/3 and StoppedWorldBaseline/2 keep the new campaign declaration
separate from same-profile restoration. Full save/intervention qualification
remains open. SPEC 0.2.127; M0.1d.8c and its existing coverage.

Focused restoration/import verification: **29 passed**. The changed import plus
affected sealed native, retention, continuation, recovery and gameplay-package
selection: **149 passed**. This includes actual sealed SQLite/CAS/file operations
on synthetic worlds, a controlled worker fixture and offline reconstruction;
changed server/budget/Java/environment, source pins, recorded player history,
later epochs, old-campaign recovery and retired source authority reject. Counts
overlap. Ruff passes; the two existing Typer/Click warnings remain.

The actual new private request `vanilla-1192-worker-stop-20260922` is SEALED with
PackLock `cas:sha256:12e7d7542c58bec5852f2dd82923482fe448ea4481d42e692c0983bc2a5d7cbd`.
It reuses the original acquired distribution bytes and verified installed roles,
with explicit acquisition-reuse provenance; no download or allowance is created.
Nine new checks bind the new identity to retained unchanged-input evidence and
the actual controlled-runtime import. These are template provisioning checks,
not a full game or G0 qualification. The new template and imported instance are
prepared outside the public checkout. The original startup failure and snapshot
remain unchanged; both level files were independently checked for absent
embedded Player data, and the retained origin records zero avatars/native work.

Private publication audit `2026-09-22-worker-stop-launch-01`: **20 files /
2,157,744 bytes**, independently verified seal
`4b237bf00c9fc1a71b18ada6e1024580ca3daa800b2a187eabc69aa4a88db406`.
All original objects, journal entries and provisioning rows are preserved.
Only objects/outbox/provisioning add the new profile; **31 other tables** and
all original accounting/D12 state remain unchanged. The audit launches no game,
model or shared-desktop input.

The changed native/game run is prepared as `2026-09-22-m0-normal-stop-01`, using
a new declared campaign/system identity, the exact controlled runtime and
scripted replies. Its first outcome is retained below; authentic completion-to-stop verification remains pending.

## Retained attempt and stopping checkpoint

Attempt `2026-09-22-m0-normal-stop-01` ends with `SERVER_EARLY_EXIT`: the
VanillaPersistence constructor required the old restoration scope and rejected
the explicitly imported baseline with `VANILLA_TEMPLATE_CHANGED`. This happens
before Java spawn, avatar connection or native work. Absent server capture also
produced a secondary `TypeError`. All **11 owned processes** are terminal, zero
forced-terminated members; the outer process exits **1** after **45.578 s**.
All 34 authority tables and the complete prepared instance are unchanged.

The independently verified failed archive contains **247 files / 30,923,063
bytes**, seal
`c393439b6aa9fa0b6c951ee1d3d488fbe4f713767989127ff3fce37df8bfdeae`.
It retains the exact executed source, plans, preflight, error traces and failed
result. It is not a successful game run or eligible native recovery parent.

The source now shares restoration-scope selection between launch, persistence
and offline verification. The imported-baseline regression exercises the actual
capture constructor and verifies the resulting snapshot names the new PackLock
while preserving the old source snapshot. Missing server captures now produce
`M0_CAPTURE_INCOMPLETE` without replacing the original launch error. Focused
import/retention/persistence checks: **91 passed**, with the same two existing
warnings; Ruff and whitespace pass. No post-fix authentic run is claimed.

The user requested two ordered merge checkpoints and a new session. No more game
trials run before that handoff. Next revalidate the prepared new profile and run
one changed native/vanilla completion-to-stop case in a fresh evidence directory;
retain attempt 01. M0 remains incomplete and G0 fails.
