# Bounded worker bootstrap and initialization

Operator-only. SPEC v0.2.33; M0.3b.2c.3c.2b.2b.2.1 in_progress;
F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08; C02/C09/C15/C18;
partial T01/T03/T06/T07/T12/T13. No aggregate gate passes.

The [previous real startup failure](2026-09-19-outline-target.md) remains failed:
guardian lease expired after fork, before any public grant, action database or
native action intent. The child formerly emitted its first heartbeat only after
all imports, lane initialization and gateway setup. Exact historical slow phase
and OS contribution are unknown; the missing startup signal is a source finding.

[worker.ts](../../backends/mineflayer/src/worker.ts) now forks before attaching the
Forge guardian, with no config/token/authority supplied until post-import
bootstrap and guardian validation succeed. [WorkerStartup](../../backends/mineflayer/src/worker_startup.ts)
enforces strict private IPC order/types, a 2,250 ms bootstrap deadline, a separate
fixed 2,250 ms initialization deadline, 200 ms renewal freshness and existing
2,250 ms heartbeat-loss termination. Genuine child event-loop pulses every
100 ms can maintain freshness but cannot extend startup deadlines or publish a
gateway. Native guardian health checks and the 500 ms kernel stop wait remain.
Overall worker wall accounting begins before fork and includes preparation.

Early child exit is now journaled even when no gateway exists. Phase events
contain only policy, elapsed time and bounds. Malformed, duplicated or reordered
messages fail closed. Before the Forge guardian attaches, the enclosing launch
owner remains responsible for the still-fenced client; this development change
does not establish full production launch or process/network/account isolation.

[workerLane](../../backends/mineflayer/src/worker_lane.ts) loads Mineflayer's
runtime/data dependencies only for explicit Mineflayer selection. Forge remains
a separate backend. Compiled-module fingerprints change; native minor 34 and
its installed JAR, action policies and existing public schemas are unchanged.

Build and five lifecycle tests pass. The first complete Forge/guardian/lifecycle
run had **56 pass / two fail** in 97.154 s: hung and malformed bootstrap were
rejected but lacked exit evidence, because cleanup closed the journal before
child exit arrived. Preserve that failed run. Cleanup now stops the child/native
guardian first, then waits at most 500 ms for the child exit receipt before
closing evidence. Missing receipt is an explicit failure, not a fabricated exit;
this wait cannot precede or delay native termination. Bootstrap rejection also
has a rejection handler for cleanup entered before the main await is installed.

The affected process suite then passed **13 tests**, no skips/failures, 58.741 s:
seven new delayed/hung/crashed/malformed startup cases, normal drain, mismatched
grants and four retained active-process faults. Synthetic JVM exit measurements
after native freeze / worker kill / worker hang / parent kill were 1,020 / 30 /
1,831 / 20 ms. The compiled gameplay-package exclusion/CLI test passed in 0.21 s.
These use synthetic game behavior and cannot replace the fresh real E9E case.
After adding the rejection handler for pre-await cleanup, the three early
bootstrap failure cases passed again in 7.006 s; no unrelated suite was rerun.

Fresh authentic `worker-01` uses the unchanged b2a91155… minor-34 native JAR,
new broker capability digest and 34 pinned compiled modules. Its previous
native/body identity is checked again before arming. Ten private harness files
are pinned; a stopped-boundary before-copy retains five selected save files,
17,633,406 bytes. Cached authentication succeeded without interaction. Existing
480-second client / 90-second worker / 1,000 primitive and guardian bounds stay.
The authentic trial has completed; its startup passed and its overall result failed. See the separated results below.
Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-worker-startup-01`.

## Authentic result and retained failures

World readiness passed at 167.0 seconds with zero identity-read failures. Private
startup phases are ordered: worker fork, post-import bootstrap (748.3134 ms),
guardian start/readiness, initialization, gateway (1,916.7829 ms from worker
start). Initialization took 280.2607 ms. Both startup deadlines passed. The child
completed its bounded lifetime with exit 0; no startup fault occurred.

The public negative checker passes: one observed-air dig ends unknown with
confirmed release and required resynchronization; the fenced lane rejects a
subsequent action. There is one action, no native action intent, two safety
release primitives, and no private diagnostic in public CLI results. Independent
stopped saves match all 256 before/after delivered IDs and all 128 selected
states remain unchanged. Saved position/rotation/dimension checks pass; selected
inventory fields are unchanged. These are selected references, not complete
resource conservation or authoritative causal scoring.

The offline negative audit **fails** its expected typed-code check: the private
event contains UNCLASSIFIED_NATIVE_FAILURE. Source inspection found that
NativeGameClient wraps mutation errors as NativeOutcomeUnknown while discarding
the underlying fault. Earlier injected-error tests bypassed that transport.
The historical lost code cannot be recovered or asserted as PRECONDITION_FAILED;
the [transport repair](2026-09-19-native-diagnostics.md) needs fresh evidence.

Shutdown also **fails**: job termination call succeeded in 1.0723 ms, but the
unchanged 500 ms kernel wait returned timeout after an observed 511.7797 ms.
The guardian records PROCESS_STOP_UNCONFIRMED, and the supervisor exits 1.
The independent observer later saw exit roughly 670 ms after the guardian's
QPC measurement start; later absence does not turn the failed wait into a pass.
Client procedure elapsed 284.891 seconds; server saved/stopped normally, exit 0,
complete logs at 439.969 seconds. No desktop watchdog intervention occurred.
Temporary arguments were retired and zero Java processes were verified.

Two 854x480 game PNGs passed CRC/zlib/scanline decoding and visual inspection:
world, bow, HUD and vegetation, with no operator desktop or loading/error screen. Startup-audit records
startup pass separately from diagnostic/overall/shutdown failure; its original
unexecuted all-success audit template is retained. Native candidate, deadlines,
public capabilities and inference spend remain unchanged. Full startup and
shutdown qualification, T03/T07 and all aggregate gates remain open.
