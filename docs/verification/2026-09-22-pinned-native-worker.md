# Pinned worker in the native vanilla path

September 22, 2026. Operator-only. M0.1d.7 connects the prepared worker to the
existing native Dovetail/root/helper/broker path. M0 remains incomplete and G0
fails; the original model allowance and every earlier failure remain intact.

## Implemented behavior

[`HeldWorkerBundle`](../../src/mcbench/worker_bundle.py) checks an expected
descriptor hash, exact profile/paths, complete file membership, finite sizes,
hardlinks and hashes. It holds the descriptor and every selected runtime file
against writes/replacement. Membership is checked before either worker launch
and after owned shutdown. New files can be detected; this is not a general
filesystem/process/network isolation boundary. Descriptors are bounded at
16 MiB and the unchanged 12,000-file/1-GiB lease limit includes the descriptor.

[`M0NativeGameSmoke/3` and `M0NativeGameRecovery/2`](../../tools/m0_native_game.py)
select the pinned bundle and reject a separate Node override. The runner holds
it before output/game startup, launches both preflight and gameplay from it,
and derives compiled-worker source pins from the actual bundle. Process cleanup
precedes lease release even on an exception. Successful receipts require all
three owned process groups to have exited with zero active processes before
the final inventory check. This is not a shutdown-deadline qualification.
Older plan versions retain their original scope.

`HeldWorkerRuntime/1` records the descriptor hash, byte/file counts, exact
launch arguments and owned-stop observations. The [read-only evidence
verifier](../../evaluator/src/strata_evaluator/native_game_evidence.py) joins
that receipt to the retained descriptor, worker capability/lock/schema hashes
and versioned intent. Archived OS paths never authorize reads. External runtime
byte archival and full isolation remain explicit gaps; the separately sealed
private worker bundle retains those software bytes.

Pinned recovery additionally requires the source run's exact runtime hash,
archived descriptor and held-through-stop receipt. It preserves the existing
fresh-epoch, token, saved-player, worker-journal, native-notes and cost checks.
The scripted bounded look now turns relative to the public observed yaw,
allowing visible rotation on successive continuations without private state.

## Source verification

**121 distinct focused cases pass.** The initial selection passes 107 cases;
seven new receipt cases and seven descriptor/recovery cases are then added.
The final affected selection passes 43 cases in 4.49 s. Real Windows file locks
protect synthetic software; runner cleanup and archive tampering use fixtures.
Changed/missing/extra/aliased files, substituted launches, altered descriptors,
live children, wrong capabilities and changed recovery identity reject.
Focused Ruff and whitespace checks pass.

```powershell
python -m pytest -q tests/test_worker_runtime.py tests/test_worker_bundle.py tests/test_native_game_evidence.py tests/test_native_game_retention.py tests/test_native_game_recovery.py tests/test_gameplay_package.py
python -m pytest -q tests/test_worker_runtime.py tests/test_native_game_recovery.py
```

The first command ran before the fourteen additional cases; the second covers
the final affected code. Counts distinguish distinct cases from repeated checks.

## Authentic pinned-worker execution

One changed-profile headless vanilla trial passes **29/29 native checks**.
The relocated worker authenticates with the existing licensed account, receives
native root/helper/broker requests and completes one bounded action. All
**11,722 runtime files / 654,076,586 bytes**, plus the descriptor, remain held
through owned stop. The three outer process groups each report return code 0
and zero active processes. Joint stopped components contain **28 state files**.
No shared-desktop input or live model request occurs.

The reusable evidence verifier reports reconciliation `pass`: six scripted
calls, 60 fixture input tokens, 24 fixture output tokens and **84 synthetic
fixture units**. These are not new API-equivalent charges. Original authority
still has the $10 cap, $0.7554 unresolved hold and $0.001458 settlement; all 34
tables match before/after. All 69 source-server files remain unchanged and no
Java process remains. The outer game interval is **199.765 s**; the complete
invocation including runtime preparation is **307.704 s**. Neither establishes
complete tick/performance accounting or G0 clocks.

Private run: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-pinned-worker-01`.
Complete seal: **4,389 files / 213,650,852 bytes**, SHA-256
`6ed35edb1c8241595eb78b10af3998d297b8c31d3cedf23d233d4cf4ef14f5e4`.
External read-only report content digest:
`35a9892c9407ff1309ed0179fb2688793efc6af98d6dfccc834082957db465aa`.
Executed source was archived before subsequent recovery-only checks and
descriptor-size hardening. No original trial bytes were changed.

## Recovery and remaining gates

The changed `M0NativeGameRecovery/2` trial passes **35/35 native checks**. It
uses the same pinned runtime, matches the saved player before continuing,
rejects the old token and epoch, preserves the original action row and records
one fresh action. The root reads its retained note and writes its continuation;
the helper cannot read that history. Cumulative costs remain **12 scripted
calls / 168 fixture units**, with two total primitives and no refunded usage.
The new native/world components stop and recapture normally, again with all
11,722 runtime files held through zero-active owned stops.

Independent read-only audit passes **28/28 checks** across both sealed bundles.
It reparses the six new wire usage receipts, preserves the old ledger prefix
and account limits, checks retained/new note bytes and root/helper lifecycle
digests, joins the old/new worker action rows and returned receipt, verifies
fresh saved orientation and the new stopped snapshot, and rechecks runtime
identity and owned-stop evidence. This supplements the first-run reusable
verifier; its single-epoch command does not claim general multi-epoch recovery
reconstruction.

Recovery outer interval: **198.875 s**; complete invocation: **222.031 s**.
All 62 source-instance files and 34 original authority tables remain unchanged;
no Java remains. Private recovery:
`C:/Users/Darian/.strata/evidence/2026-09-22-m0-pinned-recovery-01`.
Seal: **4,424 files / 213,229,768 bytes**, SHA-256
`48b3f5fe26be9f9eec8b6525e023d2825c08322259471453d813e0e5ba3ef97f`.
The separate read-only reports/audits remain under
`C:/Users/Darian/.strata/evidence/2026-09-22-m0-pinned-worker-audit-01`.
That audit set is sealed separately: **16 files / 1,371,483 bytes**, SHA-256
`f28f99c98c000d20a0997112ea4c068871d0a5a37a059fa1ae0bcda0cad41c0e`.
The documentation audit preserves every previous ledger ID and append-only
entry, adds M0.1d.7, leaves M1–M7 and SPEC sections 3/15–19 unchanged, and
checks 1,247 resolving local links.

M0.1d.7 is verified for this exact scripted development execution/recovery
scope. No unchanged native/game pair rerun is needed. Next bind the selected
worker/server launch and configuration/update policy into the actual PackLock,
then inventory-bound server custody and canonical checkpoint recovery. Existing
sealed before/after state can support further read-only clock evidence without
a new game run.

Actual PackLock sealing, inventory-bound server custody, complete canonical
checkpoint/recovery, authoritative scorer/setup, full clocks and isolation
remain required. The original vanilla request is VERIFIED/unsealed. E9E and
the five effective-file failures remain unresolved. D13 retains the approved
1,000-ms policy and all historical 500-ms failures retain their old outcomes.
General model admission remains blocked by the original hold; D12 is consumed.
No unrelated M1–M7 work is advanced.

Coverage: M0.1d.7/M0.3a.2, F01/F03/F04/F09/F11/F16,
N01/N02/N04/N06/N08, C03/C04/C06/C12/C16/C17/C20,
partial T01/T03/T04/T06/T07/T12/T13 and G0 items 1/2/4/6.
