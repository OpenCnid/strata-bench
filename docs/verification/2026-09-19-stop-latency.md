# Rendered-client stop diagnostics — September 19, 2026

Operator-only. Scope: M0.3b.2c.3c.2b.2b.2; partial F01/F06/F09/F16,
N01/N02/N03/N04/N05/N06/N08; C09/C14/C15/C18;
T01/T03/T06/T07/T12/T13. All aggregate tests and gates remain open.
The preceding [authentic stop failures](2026-09-19-forge-readiness.md) remain
failures. No guardian bound, action policy, inference allowance or gameplay
capability changes.

## Private stop intent

[ForgeProcessGuard.stop](../../backends/mineflayer/src/forge_guard.ts) records
`guard_stop_requested` in the private hash-chained supervisor journal before
dispatching the pipe stop request. Its only value is `already_exited`; existing
sequence, source-clock, monotonic and UTC fields timestamp the record. A failed
write marks evidence unavailable while retaining the stop path and independent
lease backstop. This timestamp is intent before dispatch, not the instant of the
kernel termination call. Existing bounded failure receipts and no-false-confirmation
behavior remain unchanged. The broker fingerprint changes; the native JAR does not.

Executed Node build and the six selected guarded integration tests:

```text
npm.cmd run build
node --test --test-name-pattern="actual guarded supervisor|mismatched process grants|guarded process chain" dist/tests/forge.test.js
```

Pinned Java 17.0.20.1, Python 3.12.14 and the existing exact Forge test classpath
were enabled. Six tests pass, zero failures/skips, 36.827 seconds. The normal
drain case now checks intent ordering after executor exit and before confirmed
guardian stop, plus the existing journal hash chain. Other cases cover mismatched
grants and native/worker/parent faults. These are actual disposable processes
with synthetic game effects, not authentic Minecraft qualification.

## Disposable resource probes

Private evidence root:
`C:\Users\Darian\.strata\evidence\2026-09-19-stop-latency-01`.
It holds source/compiled fixture hashes, library/JDK/production-source pins,
individual results and raw logs. The fixture stays outside the repository and
the client JAR. It does not initialize Minecraft, use accounts or network access,
or inject input. It retains and touches configurable heap arrays; rendering cases
use a small unfocused 64×64 OpenGL window on a fresh non-input desktop. Each has
a 45-second outer lifetime and at least 2 GiB free-memory reserve beyond the
requested heap. The production `AttachedJava.terminate()` and unchanged
`WaitForSingleObject(..., 500)` decide the result. An additional held handle
observes exit without acquiring termination authority.

| Touched heap | Small renderer | Working set, bytes | Reported stop-method duration | Existing 500 ms wait |
|---|---|---|---|---|
| 0 MiB | No | 71,147,520 | 15 ms | pass |
| 1,024 MiB | No | 1,412,935,680 | 94 ms | pass |
| 3,072 MiB | No | 3,836,010,496 | 250 ms | pass |
| 0 MiB | Yes | 129,019,904 | 47 ms | pass |
| 3,072 MiB | Yes | 3,885,142,016 | 297 ms | pass |

One sample per condition. All exit 125; no desktop watchdog trigger, natural
fixture exit or input-desktop change. The operator calls the production stop
method directly, so these are not independent guardian/worker qualifications.
The initial preflight failed before launch because the Gradle classpath listed
an absent empty `build/resources/test` directory. Creating that exact empty
build directory resolved preflight; no missing library was substituted. The
failed preflight remains in the private archive.

Timing limitation: this Python 3.12.14 Windows runtime maps `monotonic` to
`GetTickCount64`, with reported resolution 15.625 ms. The table retains those
coarse observations. It does not claim millisecond accuracy. `perf_counter`
uses `QueryPerformanceCounter`, reported resolution 100 ns, and is used by the
subsequent diagnostic observer. Resolution is not scheduling accuracy. The
production kernel wait is unchanged. See [Python's clock documentation](https://docs.python.org/3.12/library/time.html#time.get_clock_info)
and [Microsoft's timing guidance](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps).

Larger heaps correlate with longer exit in these five samples; the small
renderer also adds time in the paired endpoints. This motivates measurement
of the real client, but does not identify its failure cause. Windows job
termination initiates termination of associated processes, while process
objects become signaled on exit; a retained observation handle does not itself
keep a process running. See [TerminateJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject)
and [process termination](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process).

## Authentic observer trial

Fresh `worker-01/` reuses the previously tested native candidate
`06f2998073e179c34610db7465e772125232140a9ac7980b45e9fdf7dfa9ac1c`
and corrected public checker, with new immutable authority/scope and newly pinned
broker bytes. The official E9E 1.27.0 / Forge 43.4.23 setup, 4 GiB heap,
854×480 client, 480-second outer lifetime and 90-second worker lifetime remain.
The session lifetime is checked before launch. No OS input, inference or
campaign admission. The original CurseForge profile is untouched.

The diagnostic observer owns a read-only held handle to the exact Java process.
It uses 10 ms kernel waits and one-second memory samples, records when private
supervisor events become visible, and retains wait-call intervals and clock
metadata. It has a 480-second bound and 1 MiB record quota. It cannot renew
leases, send game actions or stop the client. Scheduling/file-visibility delays
remain explicit; observed intent is not a kernel-call timestamp. Only the
unchanged guardian decides whether its 500 ms exit confirmation passes.

The trial **fails** overall, reproducing `PROCESS_STOP_UNCONFIRMED` at the
unchanged 500 ms wait. Native readiness took 165.328 seconds with no identity
retry. Seventeen public CLI calls pass the bounded look/known-terminal-dedup,
active-use cancellation/release and post-fence rejection checks. Dig is only
`emitted`; independent block/resource proof remains open. Three actions account
for 13 primitive charges: look emits two, dig three, cancelled use seven, plus
the separate charged safety event. Cancellation requires resynchronization;
no uncertain action is replayed. The executor exits 0 normally; the supervisor
exits 1 because termination was not confirmed in time.

The new private intent event has `already_exited:false`. The failed receipt is
510 ms later on that supervisor's source clock. The independent observer retains
108 records, including 96 memory samples, in 21,028 bytes:

- Last memory sample before observed intent: working set 5,744,234,496 bytes,
  peak working set 5,792,108,544 bytes, private commit 6,670,872,576 bytes.
- At approximately 443 ms after the observer sees intent, working set has fallen
  to 368,365,568 bytes and private commit to 440,885,248 bytes. The process is
  still unsignaled at that sample.
- The final false-wait start and first true-wait return bracket exit within
  15.359 ms, approximately 474.474–489.833 ms after **observed** intent. This is
  not elapsed time since the actual termination call. Intent can become visible
  after dispatch, and the maximum nominal 10 ms wait-call span observed across
  the run is 78.998 ms. Scheduling and journal visibility prevent using this
  trace to overturn the guardian's failure or claim sub-500 ms termination.

The trace establishes substantial process resource release before eventual
exit. It does not isolate memory teardown, GPU/driver work, pending I/O or another
kernel wait as the cause. Direct timing at the existing job-call and wait
boundaries is the next resolving measurement; do not repeat an unchanged trial
or relax its bound to manufacture success.

The client exits 125 before outer cleanup; no desktop watchdog fires. Total
client/check time: 269.797 seconds. Server save/stop completes normally, exit 0,
404.672 seconds total, complete logs. Original profile unchanged, input desktop
unchanged, temporary arguments retired. No live client/server remains.

Both 854×480 PNGs pass independent CRC/zlib/scanline decoding and visual
inspection. They show the ground/vegetation, bow and ordinary HUD before and
after the scoped checks. Three independent saved-player comparisons pass for
rotation, position and dimension. These do not prove block/resource effects,
physical input parity or quest scoring. The evidence includes 28 native journal
frames, nine supervisor events and 274 telemetry records; reconciliation and
hash-chain checks are retained by the collector.

Full real action/resource, rendered input/focus, failure-path, isolation and
repeated shutdown qualification remain required. Same-user desktop placement
does not establish a security boundary. No aggregate T01–T17/G0–G5 result changes.
