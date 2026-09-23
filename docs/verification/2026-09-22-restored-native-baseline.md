# Restored sealed baseline and connected native action

September 22, 2026. Operator-only. M0.1d.8 remains `in_progress`; M0 is
incomplete and G0 is `fail`. The restored baseline now supports a real native
root/helper/action run with independently reconstructed evidence. Subsequent
joint game/agent recovery remains unimplemented for this sealed profile.

Coverage: F01/F03/F04/F05/F09/F11/F16, N01/N02/N04/N06/N08,
C03/C04/C06/C12/C16/C17/C20/C24, partial T01/T02/T03/T04/T06/T07/T12/T13,
G0 items 1/2/4/6. SPEC 0.2.123 adds explicit restoration contracts;
acceptance thresholds and the later roadmap are unchanged.

## Working implementation

[Operator `pack restore-world`](../../src/mcbench/pack_commands.py) takes an
exact pristine sealed materialization, a stopped snapshot plus externally
pinned digest, and a new destination. [Restoration](../../src/mcbench/pack_restore.py)
joins the original durable PackLock/inventory, holds both source trees, copies
the sealed software and all saved state, preserves empty world directories,
creates a new empty session lock, excludes diagnostics, verifies staging and
atomically publishes. Source and existing targets are never overwritten.
Failed staging is retained and cannot be reused.

[RestoredPackLaunchBinding](../../src/mcbench/pack_launch.py) and Materialization/2
explicitly name the restoration. Launch checks the exact restored server state
and pristine client. The old fresh-materialization path still rejects runtime
state. [Stopped capture](../../src/mcbench/vanilla_persistence.py) accepts this
verified restored layout and retains its existing software/JRE leases and
complete owned-process termination requirement.

[M0NativeGameSmoke/5](../../tools/m0_native_game.py) and DevelopmentServer/5 use
the same native Dovetail/root/helper/broker and Mineflayer worker path. They bind
the source snapshot to preregistered StoppedWorldBaseline/1, archive its complete
bytes before startup, and reject a baseline containing saved player state.
The [reusable verifier](../../evaluator/src/strata_evaluator/native_game_evidence.py)
joins those archived bytes, both sealed launch commands, generated worker
configuration, receipts and final saved state. Archived absolute paths remain
data. This baseline starts a fresh development campaign; it does not discard
an existing agent history or refund costs.

## Authentic execution and independent reconstruction

Environment: Windows, Python 3.12.14, Node 24.19.0, pinned private Java 17,
vanilla 1.19.2, two-CPU sealed JVM command. The original PackLock remains
`cas:sha256:d85894fca48ae58a95679d713e6d3c30a4cd154ed8a98a00d744ff07afda80a2`.
No shared-desktop input or real model request occurred.

The actual operator restore command exits zero and independently passes the
restored-launch check. Its source is the normally stopped, no-avatar component
from the [failed fresh startup](2026-09-22-sealed-native-startup.md). That whole
run still fails at 97.408/80 seconds; its immutable evidence is unchanged. The
mutated failed instance was not reused or relabeled fresh.

One changed headless baseline run then succeeds:

- Java readiness **32.487 seconds**, within the unchanged **80-second** bound.
- **29/29 native checks** pass. The avatar joins and completes one bounded look
  action, with one independently traced primitive and matching final server NBT.
- **Seven scripted calls / 98 synthetic fixture units**, split across the native
  root and scoped helper interface. They are not API-equivalent spending or
  evidence of authentic model reasoning/full runtime isolation.
- **46 owned processes**, all terminal with parent exit zero and zero forced
  terminations. Normal worker/server stop and complete logs are retained.
- **26 stopped state files / 13,530,363 bytes**, joined to native component
  `cas:sha256:fc73e7131bd75b500b7c3c2b1d4704ac7629bd50bb042367b03752fa30610bee`.
- The independent `strata_evaluator.native_game_evidence` command reports
  `reconciliation: pass`, `G0: fail`. It verifies baseline and pack joins,
  helper/root closure, all seven call receipts, six game request preimages,
  the primitive trace, scoped observations, saved player and stopped components.

Outer owned-wrapper time is 294.985 seconds; the native runner records
240.469 seconds. These measured spans do not qualify missing authoritative
avatar/server ticks, active intervals or performance series.

Fresh template materialization adds exactly one expected journal event. All
33 other authority tables remain unchanged. Restore and gameplay then leave
all 34 tables unchanged; the final read-only comparison matches. The original
$10 API-equivalent allowance remains $0.7554 held plus $0.001458 settled,
uncertainty true, D12 consumed. No reset, refund, replay or new authority.

## Retained private evidence

- Execution: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-restored-baseline-01`,
  **3,885 files / 119,713,412 bytes**; seal
  `2a584f1daf02c83053176410f51ca275af25dd4a97addbcff132ef6679a642bc`.
- Baseline snapshot:
  `fe6cdbcafaf3bcecce4a0ef060dfc084041aae1dd4526d9430480f47fbcaf379`.
- New stopped snapshot:
  `f3bebf7e8b2f252e9b0615841085e01600a0e456fb40524973780936afc48015`.
- Independent audit: adjacent `2026-09-22-m0-restored-baseline-audit-01`,
  **3 files / 8,677 bytes**; seal
  `35607bfea75c4a327c4141ca26395eedf3b59bfe0d70e21148414fcb4d4095f1`.
  Reconstructed report digest:
  `5cc65f5f7cf1eb474779c4e8f6427c2b70fdff9eacd9a93a77f02a06ffd92b8d`.

The exact executed source is archived and hash-matches its pre-run pins. Both
the previous failed bundle and this successful bundle independently reverify.
Installations, account caches, raw evidence and evaluator records remain private.

## Source verification and remaining work

Windows `.venv/Scripts/python.exe`, `PYTHONPATH=src;evaluator/src;tools;tests`,
`PYTHONDONTWRITEBYTECODE=1`:

- Initial restoration fixture produced 14 setup errors (`IDEMPOTENCY_CONFLICT`):
  it tried to change a previously verified synthetic inventory. A separate
  correctly initialized fixture fixed setup; production idempotency stayed intact.
- `pytest tests/test_pack_restore.py -q`: **14 passed**, 27.48 seconds.
- `pytest tests/test_pack_restore.py tests/test_pack_launch.py tests/test_sealed_native_game.py tests/test_native_game_retention.py tests/test_vanilla_persistence.py -q`:
  **133 passed**, 81.77 seconds, including the added complete baseline archive
  and independent verifier join. Two existing Typer/Click warnings remain.
- `pytest tests/test_gameplay_package.py -q`: **1 passed**, 0.44 seconds; the
  delivered gameplay bundle excludes operator code and evidence.
- Ruff over the changed Python source/tests and whitespace checks pass.

These source/synthetic/process checks remain separate from the authentic run.
The fixtures exercise changed state/software/client/marker/session lock,
wrong source/pack hashes, extra files/directories, overlap, staging failure,
no replay, source preservation, held-worker launch, recapture and offline joins.

Next connect the successful captured game state, native root/helper state and
existing costs to a fresh-epoch sealed recovery, with old token/epoch denial
and no action replay. Preserve the original campaign baseline and every prior
ledger row. Do not repeat this unchanged successful baseline run. Full save
custody, canonical recovery, authoritative clocks/resources, scorer/setup,
runtime isolation, E9E mechanics and authentic model reply qualification remain
open. D13's prior 1,000-ms normal-shutdown sample is unchanged; no historical
500-ms/effective-file/Mineflayer/native-delivery failure is removed. The M0/G0
goal remains active, with independent implementation work and no pending user input.
