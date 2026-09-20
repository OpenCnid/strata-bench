# 2026-09-18 Windows Java process guard foundation

Operator-only. Advances M0.3b.2c.3a; partial F09/N01/N02/N05/N08,
C15/C30, T01/T06/T07 under G0/G1/G2. M0 and all release gates remain open.

This report preserves the standalone foundation's scope. Subsequent worker and
native-health integration is recorded [separately](2026-09-18-forge-guard-integration.md).

## Implemented

- A private, strict, expiring grant names the exact Java process identity. A held
  Win32 handle is validated against PID, full-precision creation FILETIME,
  executable path and on-disk image hash before Job Object assignment. The guard
  never reopens a cached PID to terminate it. Identity inspection is read-only.
- Exclusive per-process ownership rejects a second guard without disturbing the
  first. A kill-on-close Job Object ends the dedicated client lifetime when the
  guardian crashes. New descendants are contained; pre-existing descendants
  remain a launch-integration requirement.
- A separate process monitors a 1500 ms challenge/response lease and immutable
  monotonic wall/authority deadlines. Fresh nonces prevent queued or replayed
  heartbeat messages from prolonging a stopped supervisor. Pipe input and output
  use bounded queues and separate threads, so blocked IO does not hold the guard
  control loop. Root termination is checked through the held handle.
- Explicit stop, malformed/oversize messages, EOF, heartbeat timeout, expiry and
  normal root exit all end ownership and terminate the job. Diagnostic receipts
  distinguish process termination from input release and always require resync.
  These are not clean checkpoints or a complete durable audit trail.

Source: [guard](../../src/mcbench/process_guard.py), shared
[Windows Job Object wrapper](../../src/mcbench/processes.py),
[fault tests](../../tests/test_process_guard.py), and a test-only Java
[process fixture](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/ProcessGuardFixture.java).
The fixture creates no Minecraft runtime, account session, window or desktop input.

## Verification

Windows 11 / Python 3.12.14 / Temurin JDK 17.0.20.1+1. Pinned Gradle 8.8
compiled the new test-only Java fixture with the existing exact Forge classpath:

```text
gradlew.bat :forge1192-client:compileTestJava :forge1192-client:writeTestClasspath --no-daemon --console plain
```

With explicit `STRATA_CLIENT_TEST_JAVA` and `STRATA_CLIENT_TEST_CLASSPATH`,
the focused guard suite passed **17 tests**. The final selected regression run
passed **24 tests**, zero failures/skips, in 23.73 s (17 guard, six shared process
wrapper, one gameplay-package exclusion test):

```text
uv run --frozen pytest tests/test_process_guard.py tests/test_processes.py tests/test_gameplay_package.py -q -o junit_family=xunit1 --junitxml=<private>/python-tests.xml
```

The silent-supervisor/hung-JVM case exited **1516 ms** after the unanswered
challenge; its termination wait was **16 ms**. EOF, guardian crash, malformed
lease, replay and oversized input cases exited **15, 16, 32, 15 and 15 ms** after
injection respectively. These are individual synthetic measurements, not latency
percentiles or authentic operating-envelope evidence. Targeted Ruff passed;
`git diff --check` passed with existing CRLF notices only.

Cases include correct identity, wrong creation/image/path, stale exited identity,
replacement process mismatch, non-Java rejection, strict grant/expiry checks,
second-owner denial, silent supervisor with hung JVM, EOF, guardian crash,
malformed/replayed/oversize lease messages, continued fresh heartbeats, explicit
stop, immutable deadlines, normal root exit, sibling survival, post-attachment
descendant termination/no late effect and bounded output backpressure.

The first run had **2 failed / 13 passed**: the tests incorrectly expected a
nonzero exit status after kernel kill-on-job-close. Windows returned zero for
forcibly terminated fixtures. The assertions now use confirmed process exit;
the guard's separate `release_confirmed=false` semantics were retained. A second
owner and expired-attachment case plus normal-exit coverage were added before
the focused **17 passed** run. No failing authentic test was converted to a pass.

Private evidence root:
`%USERPROFILE%/.strata/evidence/2026-09-18-process-guard-01/`.
It contains the final pytest log/JUnit (including measured fault-to-exit times),
source hashes and verification metadata. No process grants or credentials are
copied into repository evidence.

## Limits and next action

This is an **implemented but unverified** foundation for authentic deployment.
It is not wired to the Node worker/native bridge; that remains M0.3b.2c.3b.
Native listener/session-to-process binding, independent client-thread health,
startup containment, durable stop evidence, aggregate costs, real-game stop
timings and actual OS/process/network isolation remain open (.3b/.3c/.2c.2).
Timing assertions use the 2250 ms outer bound on dedicated synthetic processes;
they are not a capacity or Minecraft conformance certificate. The new test-only
fixture was compiled; no mod JAR was installed or production Java source changed.
No Minecraft launch, desktop interaction, inference spend or gate closure occurred.

API contracts checked against Microsoft's
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes),
[QueryFullProcessImageNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew),
[AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
and [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) documentation.
