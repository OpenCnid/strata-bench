# Sealed worker journal recovery handoff

September 22, 2026. Operator-only. M0.1d.8a is `implemented_unverified` for
the connected sealed recovery profile; M0.1d.8 remains `in_progress`, M0 is
incomplete and G0 is `fail`. No new Minecraft or model run occurred.

Coverage: F01/F03/F04/F05/F09/F11/F16, N01/N02/N04/N06/N08,
C03/C04/C06/C12/C16/C17/C20/C24, partial T01/T02/T03/T04/T06/T07/T12/T13,
G0 items 1/2/4/6. SPEC 0.2.124 records the development handoff contract;
acceptance thresholds and M1–M7 are unchanged.

## Implemented behavior

[The worker journal handoff](../../src/mcbench/worker_journal_restore.py)
copies the exact externally pinned stopped database into an empty destination.
It checks scope, terminal actions, ordered charges, remaining primitive
allowance and SQLite storage compatibility. Old grants are excluded. Source
files remain unchanged; the copied journal stays held until one launch attempt.
Construction failure consumes that handoff, so it cannot cause a blind retry.

[HeldPackWorker](../../src/mcbench/pack_worker.py) permits this explicit handoff
after the import preflight has exited normally with no active or forced children.
Its restored receipt requires an actual normally stopped worker.
[M0NativeGameRecovery/3](../../tools/m0_native_game.py) connects that launcher to
[the existing native recovery runner](../../tools/native_game_recovery.py).
It requires a fully reconstructed Smoke/5 parent and the same pack/runtime,
original campaign baseline, saved player and native component, with a fresh
epoch and lease. The source world is independently archived before startup.
Existing native-state/cost retention and stale-token/epoch checks remain.

The complete recovery verifier is still unfinished. It must compare the entire
old journal/ledger prefix, independently reconcile the new epoch, and join
cumulative costs, retained artifacts, saved player and new stop evidence.
Current single-epoch reconciliation must not be made to pass by removing history.
This profile has not yet been executed against Minecraft.

## Source and interoperability checks

Windows, Python 3.12.14, Node 24.19.0; `PYTHONPATH=src;evaluator/src;tools;tests`
and `PYTHONDONTWRITEBYTECODE=1`:

- `pytest -q tests/test_worker_journal_restore.py`: final **44 passed**.
  Includes an actual Node Journal opening of a synthetic restored database:
  epoch 2, old action unchanged, one retained charge, zero new actions.
- `pytest -q tests/test_native_game_recovery.py tests/test_pack_worker.py tests/test_native_game_retention.py`:
  **102 passed**, including scope/pack/source mismatch, stale grants, strict
  profile fields, interrupted construction and normal-stop receipt controls.
- The earlier affected selection passed all **17 sealed native tests**. The
  gameplay-package check also passes; operator modules are excluded.
- Ruff and whitespace checks pass. Two existing Typer/Click warnings remain.

The first combined selection reported **1 failure and 68 passes**. Its Python
fixture inserted JSON as SQLite BLOB values, which actual Node cannot parse as
JSON text. The fixture now uses the actual TEXT storage form, and production
admission explicitly rejects BLOB action/event JSON. This is interoperability
verification with synthetic data, not authentic recovery evidence.

## Read-only inspection of actual retained evidence

The new source loader successfully reconstructs the existing
[sealed native baseline](2026-09-22-restored-native-baseline.md), then accepts
its exact worker journal: **one epoch, one action, 62 events, one primitive**.
It verifies the unchanged parent seal and all **34 original accounting tables**.
Nothing is restored or launched during this inspection.

Both initial inspection failures remain retained:

1. `WORKER_JOURNAL_NOT_STOPPED`: the source contains an empty WAL and a
   32,768-byte SHM. Admission now follows the existing frozen-database rule:
   reject pending WAL/rollback data; retain, hold and record inert remnants in
   the source, without copying them into the fresh worker state.
2. `sqlite3.OperationalError: invalid uri authority: %3F`: normalize Win32
   extended paths for SQLite URI opening, using the existing evidence reader's
   behavior. The new regression check passes.

Private inspection evidence, including both failures and the successful third
attempt: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-sealed-recovery-source-01`,
**10 files / 28,953 bytes**, seal
`ff0a03a3c1d0872f065ff65bf893530b7d46020ec1a73277d079868beb7831bd`.
The original source seal remains
`2a584f1daf02c83053176410f51ca275af25dd4a97addbcff132ef6679a642bc`.

The original $10 API-equivalent allowance remains $0.7554 held plus $0.001458
settled, uncertainty true, D12 consumed. General model admission remains blocked.
Fetched main is still `c2161a6e79cea0c668ab993df149ab1ed5af119b`; existing branch
and changes were preserved. No Java process was present during inspection.

Next finish reusable reconstruction across both epochs, then qualify one
changed sealed recovery run. Full save custody/clocks, scorer/setup,
runtime/helper isolation, E9E compatibility and authentic model qualification
remain required. D13's passing 1,000-ms normal-stop sample and every old 500-ms,
effective-file, Mineflayer/E9E and native-delivery failure remain unchanged.
