# Sealed native launch: implementation and retained startup failure

September 22, 2026. Operator-only. M0.1d.8 remains `in_progress`; M0 is
incomplete and G0 is `fail`. This extends the existing native/game runner;
it does not qualify a new successful native action or joint recovery.

Coverage: F01/F03/F04/F09/F11/F16, N01/N02/N04/N06/N08,
C03/C04/C06/C12/C16/C17/C20, partial T01/T03/T04/T06/T07/T12/T13,
G0 items 1/2/4/6. SPEC 0.2.122 adds private execution/capture contracts.
The later roadmap and acceptance thresholds are unchanged.

## Implemented behavior

[M0NativeGameSmoke/4](../../tools/m0_native_game.py) connects the existing
Dovetail/native root/helper probe to HeldPackWorker and DevelopmentServer/4.
It binds the actual PackLock and expected worker runtime, checks preregistered
retention against that lock, and rejects literal server/worker overrides.
The generated configuration is held before the server changes the fresh
instance. Exact pack/profile/inventory bytes and both resolved commands are
retained beside the existing native/game evidence.

[Inventory-bound persistence](../../src/mcbench/vanilla_persistence.py) accepts
an exact pristine sealed template without a world. It rejects preexisting files
and empty world directories, holds immutable software and both installed and
actually executed Java trees, then captures declared mutable state after normal
complete owned-process termination. StoppedVanillaSnapshot/2 binds the original
inventory and pack seal. Unknown state, modified software, unexpected Java files
and incomplete process history reject. External-writer exclusion and
authoritative clean-save qualification remain false.

[Reusable verification](../../evaluator/src/strata_evaluator/native_game_evidence.py)
joins retained pack bytes, commands/settings, generated configuration, owned
worker exits and [retained components](../../evaluator/src/strata_evaluator/native_game_retention.py).
Archived absolute paths remain data. For the fresh-player profile, the initial
scoped observation replaces a nonexistent prior player save; final own
position/orientation must match retained server NBT. Legacy profiles keep their
existing semantics. Full multi-epoch sealed recovery is not yet implemented.

## Authentic result: startup failed

Environment: Windows, Node 24.19.0, Python 3.12.14, private pinned Java 17,
vanilla 1.19.2, sealed two-CPU JVM command. Original PackLock:
`cas:sha256:d85894fca48ae58a95679d713e6d3c30a4cd154ed8a98a00d744ff07afda80a2`.
The plan selected the existing scripted provider; no model request occurred.
Shared-desktop input remained paused.

The single changed-profile run **fails `SERVER_START_TIMEOUT`**. Java needed
**97.408 seconds** to reach readiness against the **80-second** bound, excluding
17.952 seconds of preceding preparation. The server's own `Done` interval is
86.704 seconds and measures a different startup span. Worker import passes,
but no gameplay worker, avatar or native agent starts. This is not evidence of
successful gameplay or native delivery in the sealed profile.

The pending stop request is processed after world generation. Server exit is
normal, logs are complete and all **14 owned processes** are terminal with zero
forced terminations. The independent audit verifies a narrower stopped-server
component: **20 state files / 12,001,195 bytes**, no saved player, matching
inventory/PackLock and complete owned-process history. `M0_CAPTURE_INCOMPLETE`
and `WORKER_RUNTIME_STOP_UNCERTAIN` remain in the failed outer result because
there is no native component or launched gameplay worker. This component is not
a complete or qualified joint checkpoint.

Private immutable evidence:

- Directory: `C:/Users/Darian/.strata/evidence/2026-09-22-m0-sealed-worker-01`.
- Bundle: 213 files / 34,440,790 bytes; seal
  `ef1699be5b76b983e3cdef87cc6b0f25d3d02ff2f5e1f2efa50f7c3ba5931db1`.
- Stopped manifest:
  `fe6cdbcafaf3bcecce4a0ef060dfc084041aae1dd4526d9430480f47fbcaf379`.
- `failure-audit.json`, `execution.json`, plans/results, logs and source snapshot
  retain the failure. The current verifier independently rechecks this bundle
  and stopped component without launching Minecraft.

All 34 original authority tables and all 4,097 original role files are unchanged.
A subsequent read-only authority comparison also matches the archived after
state exactly. The original allowance remains $10 API-equivalent: $0.7554 held
plus $0.001458 settled, uncertainty true and D12 consumed. No replay, refund,
reset or additional allowance occurred.

## Source and synthetic verification

Commands use `.venv/Scripts/python.exe`, `PYTHONPATH=src;evaluator/src;tools;tests`
and `PYTHONDONTWRITEBYTECODE=1` on Windows. These are source/synthetic/process
checks, not authentic game acceptance:

| Executed selection | Result |
|---|---|
| `pytest tests/test_vanilla_persistence.py tests/test_worker_runtime.py -q` | 68 passed, 11.82 s. |
| `pytest tests/test_sealed_native_game.py tests/test_vanilla_persistence.py tests/test_native_game_retention.py -q` | 84 passed, 29.18 s, before six additional verifier cases. |
| `pytest tests/test_sealed_native_game.py tests/test_native_game_retention.py -q` | 48 passed, 4 failed, 25.56 s: the new synthetic observation fixture replaced required state fields. Corrected to preserve the complete schema. |
| `pytest tests/test_sealed_native_game.py -q`, after fixture correction | 17 passed, 11.60 s. Includes resolved-schema, initial/final state and tampered join controls. |
| Ruff over all seven changed Python source/test files | All checks passed. |

Two existing Typer/Click deprecation warnings remain. An earlier attempt at
the final selection lost tool output during context transition; its outcome
is unknown and is not counted as a pass. The observed rerun and correction above
establish the reported result. The trial's archived source precedes final
offline verifier hardening and extra tests; those later edits have source
evidence only. The NBT join fixture explicitly substitutes a synthetic decoder;
it does not claim binary NBT or authentic save qualification.

## Next implementation

Implement explicit restoration into a new sealed-template materialization,
binding the retained no-avatar stopped world as a declared baseline. Preserve
the failed fresh-generation profile; never treat its mutated instance as fresh,
silently copy an unverified world, increase its bound or repeat it unchanged.
The same mechanism is needed for subsequent sealed game/agent recovery with
fresh epochs and preserved costs. Baseline preparation must remain distinct
from scored gameplay and full checkpoint qualification.

Then collect changed-profile connected execution and recovery evidence. Earlier
development action/recovery remains valid for its
[recorded scope](2026-09-22-pinned-native-worker.md). D13's 1,000-ms shutdown
sample already passed; this startup failure is separate. Scorer/setup,
authoritative clocks/save custody, isolation, E9E mechanics and authentic model
delivery remain open. All old 500-ms, effective-file, Mineflayer/E9E and native
delivery failures are preserved. No user input is required for the next source
implementation; the M0/G0 goal remains active.
