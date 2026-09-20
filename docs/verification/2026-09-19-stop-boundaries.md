# Guardian job-call and wait timing — September 19, 2026

Operator-only. Scope: M0.3b.2c.3c.2b.2b.2; partial F01/F06/F09/F16,
N01/N02/N03/N04/N05/N06/N08; C09/C14/C15/C18;
T01/T03/T06/T07/T12/T13. No milestone or aggregate gate passes here.
Prior [stop failures and external measurements](2026-09-19-stop-latency.md)
remain retained. Previous goal turn made progress through implementation and
new authentic failure evidence; it was not an impasse or an unchanged wait.

## Private timing implementation

[AttachedJava](../../src/mcbench/process_guard.py) records its own QPC start,
clock resolution and relative job-call/wait boundaries, plus separate job and
wait outcomes. The existing job termination and single 500 ms kernel wait are
unchanged. Success, timeout, wait error and job error have distinct values;
exceptions still propagate. Timing describes Python call boundaries and includes
scheduling/wrapper overhead, not kernel-internal execution.

The [Forge guardian](../../src/mcbench/forge_guard.py) enables a private
`termination_timing` event under `job-call-wait-qpc/1`, queued only after owned
guardian handles are closed. Pipe backpressure cannot precede the stop/cleanup
attempt. The base guardian emits no new event, preserving its existing consumer
contract. A process crash can still leave no terminal timing record; absence
is missing evidence, never a zero-duration stop.

The [Node supervisor](../../backends/mineflayer/src/forge_guard.ts) checks exact
fields, bounded numeric/string types, timestamp order and compatible outcomes.
It rejects unknown/duplicate diagnostics and requires a signaled timing outcome
plus the existing separate confirmed-stop receipt. The timing event alone never
claims termination, input release or a clean checkpoint. No raw exception,
argument, credential or path enters this diagnostic. Broker/Python fingerprints
change; public gameplay capabilities, native client JAR and all deadlines remain.
SPEC v0.2.31 records this private contract without changing any release threshold.

## Executed checks

Private root:
`C:\Users\Darian\.strata\evidence\2026-09-19-stop-boundaries-01`.
Pinned Python 3.12.14, Java 17.0.20.1, Node 24.19.0 and existing Forge test
classpath. No model calls, Minecraft launch or OS input in these fixture checks.

```text
python -m pytest tests/test_process_guard.py -k "stop_timing or timing_output" -q
python -m pytest tests/test_process_guard.py tests/test_forge_guard.py -q
npm.cmd run build
node --test --test-name-pattern="actual guarded supervisor|mismatched process grants|guarded process chain|guardian failure|malformed guardian|termination diagnostic|termination timing" dist/tests/forge.test.js dist/tests/forge_guard.test.js
```

- Six new Python timing/failure-order cases pass (0.14 s; 18 deselected).
- Both Python guardian modules pass: 33 tests, no skips/failures, 30.01 s.
  This includes those six cases, not 39 unique tests. Disposable JVMs exercise
  identity/ownership/expiry, parent/pipe faults, descendants and native freezes.
- Node build passes. Ten selected Node tests pass, no skips/failures, 36.902 s:
  six guarded process integrations, two retained failure-record cases and two
  new timing validation/journal cases. Normal drain verifies ordered timing and
  confirmed-stop evidence; malformed/contradictory/extra-field cases fail closed.

An additional private owned-unsignaled-event probe calls the unmodified Windows
500 ms wait five times and measures with QPC. All return `WAIT_TIMEOUT` after
514.7751, 500.8545, 500.1985, 511.4938 and 515.3868 ms. No early timeout appears
in this small probe; this does not establish a general timer guarantee or explain
the real client's failure. See [the official wait contract](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

## Authentic trial

Fresh `worker-01/` uses official E9E 1.27.0 / Forge 43.4.23, unchanged native JAR
`06f2998073e179c34610db7465e772125232140a9ac7980b45e9fdf7dfa9ac1c`,
the existing dedicated copy and separate non-input desktop. It has new scope,
authority and broker pins, the corrected public checker and retained independent
read-only exit/memory observer. The 4 GiB heap, 854×480 window, 480-second client
bound and 90-second worker bound remain. Cached-session lifetime is checked
before launch; protected substituted arguments are retired after stopping.

The trial **passes its bounded operator procedure**, including a confirmed
worker-owned guardian stop. It is the first passing combined scoped-worker/API/
normal-stop trial in this non-input-desktop sequence. This is a narrow procedure
pass, not complete action conformance or reliable-shutdown qualification.
Previous failed stops remain failures; the behavior change here is diagnostics,
so the successful sample does not show that the cause was repaired.

Readiness: 209.906 s, no identity retry. Seventeen public CLI calls pass look,
known-terminal deduplication, active-use cancellation/confirmed release and
post-fence rejection. Dig returns `emitted`; no independent block/resource
effect proof. Three actions retain 13 primitive charges: look emits two, dig
three, cancelled use seven, plus the separate safety event. Resynchronization
is required after cancellation; no uncertain mutation is replayed.

The executor and supervisor both exit 0. Private guardian evidence records:

| Boundary/outcome | Measured result |
|---|---|
| Job termination call returns successfully | 1.2930 ms after the QPC start |
| Process wait begins | 1.2980 ms after start |
| Process wait returns `signaled` | 491.1453 ms after start |
| Time inside the wait wrapper | 489.8473 ms |
| Configured kernel wait limit | unchanged 500 ms |
| Separate terminal receipt | termination confirmed; release false; resync required |

The independent held-handle observer brackets exit at 464.4048–491.0198 ms
after the guardian's QPC start. It has 108 records, 97 memory samples and a
maximum nominal 10 ms wait-call span of 189.1885 ms elsewhere in the run.
This wider scheduling variability remains evidence, not a hidden measurement
exclusion. The last pre-call sample has working set 5,434,118,144 bytes, peak
5,434,146,816 bytes and private commit 6,477,004,800 bytes. No memory sample
falls inside termination in this run. The earlier 5.744 GB sample failed, but
these few uncontrolled-load observations cannot establish a memory/latency
relationship or cause. The guardian's existing coarse `termination_wait_ms`
reports 485 ms; its GetTickCount64 quantization remains distinct from the QPC
call-boundary measurements.

The roughly 10 ms remaining wait margin and retained earlier failures prevent
a reliable-stop claim. The main measured time in this successful sample is in
waiting for process exit, not the job termination call. The next resolving work
is to capture the same direct boundaries on a failed sample and identify the
resource/OS contribution, while independently progressing game-state references.
Do not reinterpret the older failures or widen their deadline.

Client exit 125 is confirmed before outer cleanup, without a desktop watchdog
trigger; total client/check 314.875 s. Server saves/stops normally in 509.390 s,
exit 0 and complete logs. Both 854×480 PNGs pass CRC/zlib/scanline decoding;
three saved-player comparisons pass for rotation, position and dimension.
Evidence includes 29 native journal frames, eight supervisor events and 327
telemetry records. Collector validates chains, SQLite and primitive settlement.

All game processes are stopped, the input desktop and original CurseForge
profile are unchanged, and temporary arguments are retired. No shared-desktop
input, inference or campaign admission. Full actions, block/resource references,
physical input/focus, isolation, soaks, capacity and all existing M0–M6 gates
remain open. M7 remains conditional.
