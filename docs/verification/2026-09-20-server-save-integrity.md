# Server crash detection and invalid machine fixture

September 20, 2026. Operator-only. M0.3.1a, M0.3b.3.2.4b.1/.2a;
F01/F05/F09/F11/F16, N01/N02/N04/N05/N06/N08, T01/T02/T03/T07/T10/T12/T13.
G0 and T07 remain fail. No machine-operation or clean-save pass is claimed.

## Authentic operation-05 and corrected verdict

The updated broker passes its unchanged startup phases on the real E9E profile:
bootstrap **215.441 ms**, initialization **261.020 ms**, gateway ready
**1,531.144 ms** after fork. Native client readiness takes 168.953 seconds.
This qualifies those particular startup observations, not general reliability.

Scoped API furnace opening and pickup of the existing three dust items finish
with `emitted` receipts. The single deposit becomes `unknown` with
`GAME_MACHINE_TRANSFER_UNCONFIRMED`; no deposit is replayed. Three unique native
intents, **11 charged primitives**, worker/native counters and both journal hash
chains reconcile. The player save has exactly three fewer dust and otherwise the
same inventory; no output is credited. The furnace block remains, but its block
entity is absent. The saved-machine reader correctly rejects `SAVED_MACHINE_MISSING`.
Energy and machine inventory after the crash are unresolvable.

The actual server log records a ticking-block-entity crash, a failed block-entity
save and a watchdog crash. Thermal's reconfiguration side array contains nulls.
Two crash reports and all original logs are retained. Official serverstarter
returns **exit code zero despite these failures**. The original independent
audit's early `normal_server_save: pass` field was based on that exit code; it is
explicitly superseded by `crash-postmortem.json`, without altering the original
artifact. A save announcement or launcher exit is not clean-save evidence.

The worker is eventually stopped by its outer owner with exit 125; the diagnostic
observer ends before client termination and reports no exit. No terminal guardian
receipt exists. Outer cleanup proves root termination, retired arguments,
unchanged input desktop and zero remaining Java processes, not the 500-ms
guardian contract. The sample retains **370.828 s** elapsed, its consumed/unknown
resources and all action costs. No inference or shared-desktop input occurs.

## Exact fixture diagnosis

The original setup used a `setblock` command with only an Energy NBT compound.
The pinned `Reconfigurable4WayBlockEntity.load` reads missing Facing as byte zero;
the retained baseline and later idle save both actually contain **Facing=0**,
while the block property is **north**. CoFH's side array initially contains six
valid NONE values. On activation, `updateSideCache` tries to rotate this vertical
facing to a horizontal one. None of its three horizontal rotation cases fills
the newly allocated array, then `setSideConfig` publishes that null array and
control-packet serialization crashes. Subsequent state serialization also fails.
This conclusion follows the exact installed CoFH/Thermal bytecode and the saved
fields/crash stack; no upstream API or substitute dependency is assumed.

The v1 reader's idle resource projection did not validate orientation. Its prior
limited field-reading result remains historical evidence, **not a valid operating
fixture baseline**. The affected fixture and sample are quarantined; do not repair
that save, refund resources or replay the unknown request. A separately declared
fresh development fixture must preserve native initialized NBT when provisioning
energy, validate its orientation/side modes and retain all earlier costs and
failures. Ordinary API processing still needs a fresh authoritative success case.

## Implementation and checks

- [Server log inspection](../../src/mcbench/server_health.py) recognizes bounded
  pinned vanilla/Forge crash, watchdog and core persistence-failure records.
  Reports contain codes, line/byte offsets and raw-byte hashes, not private log
  messages. Partial/oversized records and evidence quotas fail closed. Chat and
  unrelated plugin messages cannot impersonate these parsed severity/thread records.
- [Development server runner](../../tools/development_server.py) now returns
  failure for these signals even when the launcher exits zero. A normal controlled
  lifecycle is only `stopped_unqualified`; `clean_save_proven` stays false. Live
  readers must finish before a complete-log claim. This does not replace private
  telemetry, launch identity or persisted-state evidence.
- [Saved furnace policy v2](../../evaluator/src/strata_evaluator/saved_machines.py)
  requires a horizontal Facing matching the block and six side modes in the pinned
  five-value CoFH enum. Missing/wrong-type/malformed/mismatched fields reject.
  Existing missing-entity, energy, inventory and source checks remain.
- **136 focused Python checks pass (5.95 s)**: saved block/machine, server health
  and actual gameplay-package exclusion. Three real disposable Python launcher
  cases prove zero exit cannot mask a logged crash or truncated log, and that an
  ordinary stop does not claim a clean save. These are synthetic server fixtures.
  Full Ruff passes. Initial test-only failures (Windows's test-name environment
  limit and missing byte-array support in the synthetic NBT writer) are retained;
  named cases and the fixture encoder fix them without changing production bounds.
- Retrospective inspection of the actual setup and operation-01 through -04 logs
  finds no recognized critical signals. Operation-05 has **nine** matching records:
  three crash, one block-entity save failure and five watchdog records. Absence
  of these signatures alone does not establish clean saves in the earlier cases.
  V2 rejects the same original/operation-03 snapshots for invalid orientation.

Raw evidence, crash reports, bytecode inspection, source hashes and immutable
superseding audits remain outside the repository under
`C:\Users\Darian\.strata\evidence\2026-09-20-machine-reference-01`.
The crashed `e9e-machine-conformance-01` server copy remains stopped and retained.
Full mechanics, private scoring, isolation, launch/save provenance, reliable
termination and every remaining M0–M6 acceptance requirement stay open.
