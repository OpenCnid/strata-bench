# 2026-09-18 guarded Forge development worker integration

Operator-only. Advances M0.3b.2c.3b, with .3a refinements; partial F06/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C03/C09/C15/C18/C30, T01/T03/T06/T07/T12/T13
under G0/G1/G2. No authentic suite, release gate or milestone closes.

## Behavior

- The explicit Forge worker now requires a separate Windows Python guardian
  before the Node worker starts. Its strict configuration is versioned as
  `strata/ForgeDevelopmentWorker/2`; version 1 rejects and there is no unguarded
  fallback. Vanilla keeps its existing schema/backend. Capability minor 6 pins
  the guardian policy, Python version and eight Python implementation sources
  alongside the existing compiled broker, schema and native fingerprints.
- The private guardian grant binds an exact process identity to the canonical
  native descriptor digest and expected authority/body/capability/primitive limit.
  Windows must identify that Java PID as owner of the exact loopback listener.
  Wrong PID/listener, descriptor, authority, active owner or stale native epoch
  rejects before attachment/arming. The worker verifies the same descriptor and
  native connection generation again before arming. These are development grants;
  production controller authentication/isolation remains open.
- The Python guardian samples authenticated `identity` and `lane_status` on the
  native client thread independently of Node. Native health is sampled after a
  one-second wait between samples, with 500 ms request deadlines and a 1500 ms
  maximum stale-sample bound. Wrong identities/epochs, unhealthy evidence or
  failures stop the client. Parent renewals require a recent worker heartbeat.
  The existing held process handle, immutable deadlines and kill-on-close Job
  Object retain their no-cached-PID/whole-client-lifetime semantics.
- Parent readiness is durable before child configuration/arming. A bounded,
  exclusive, forced-to-disk `SupervisorEvent/1` JSONL log retains private
  startup/readiness/exit/fault evidence with source clock IDs and hash chaining.
  Grant contents, native tokens and challenge nonces never enter this log or
  the gameplay package. The public grant remains only URL/token/actor/epoch.
- A normal worker exit releases its native lane and closes the action journal
  before ending the dedicated Java client lifetime. Guardian failure forces
  failure of the worker session. Process termination is always distinct from
  confirmed input release or a complete clean checkpoint. A parent crash may
  leave incomplete evidence and is not reported as a clean stop.

## Executed checks

Windows 11 / Node 24.19.0 / Python 3.12.14 / Temurin JDK 17.0.20.1+1,
Gradle 8.8 with the existing Forge 1.19.2-43.4.23 fixture classpath.

- `npm run build`: TypeScript strict/unused checks passed.
- Explicit `STRATA_CLIENT_TEST_JAVA`, `STRATA_CLIENT_TEST_CLASSPATH`, and
  `STRATA_GUARD_TEST_PYTHON`, then `node --test dist/tests/*.test.js`:
  **95 passed**, zero skipped, 51.437 s. Twenty are the Forge integration group.
- Explicit Java/classpath and `uv run --frozen pytest tests/test_forge_guard.py
  tests/test_process_guard.py tests/test_processes.py tests/test_native_game.py
  tests/test_native_game_jvm.py tests/test_gameplay_package.py -q`:
  **51 passed**, zero skipped, 44.78 s. Seven new cases check actual Windows
  listener ownership, sibling rejection, authority mismatch, an already armed
  native owner and a frozen client thread while the parent continues renewals.
- `gradlew.bat :forge1192-client:compileTestJava
  :forge1192-client:writeTestClasspath --no-daemon --console plain` compiled the
  test-only frozen-thread hook. No production Java changed, JAR installation,
  Minecraft process, desktop input or account flow occurred.
- After final admission and evidence refinements (no public grant after a stop/
  guardian failure; versioned evidence frames with a source clock ID), the final
  Forge selection passed **20 Node tests**, zero skipped, 48.779 s. Its native
  freeze/worker kill/worker hang/parent kill times were **1466/45/1922/31 ms**.
- Targeted Ruff and changed-file whitespace/ledger-link checks passed. These
  changes do not claim a rerun of the entire Java or Python project suites.

The full Node run's in-flight action fault measurements were:

| Fault injected | Observed JVM exit after injection |
|---|---:|
| Native client thread frozen, HTTP server thread still available | 1430 ms |
| Node worker killed | 48 ms |
| Node worker event loop blocked | 1907 ms |
| Parent supervisor killed | 44 ms |

Each case retained one native action intent, with no replay. Normal shutdown
checked private log hashes and termination/release separation; wrong process
grants never created a public grant or armed the fixture. These individual
synthetic measurements are not latency percentiles, real game timing evidence,
or a capacity certificate.

An initial integrated normal-stop case failed: a challenge arriving before the
first worker heartbeat was discarded, so the guard expired its lease despite
later healthy heartbeats. The parent now retains that single challenge until a
fresh heartbeat permits an answer, without moving the guardian's deadline.
The normal-stop and fault cases were then rerun successfully. The failure and
fix did not weaken the lease bound or turn a failed authentic case into a pass.

Private evidence:
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-guard-integration-01/` contains
Node and Python JUnit/logs, final Forge rerun artifacts, measurements and source
hashes. Synthetic credentials/grants are not copied into this repository.

## Remaining requirements

Authentic E9E/Forge behavior and timing remain unverified; Mineflayer/E9E's actual
Forge-login rejection stays failed. Production controller generations/repair
authority, complete nested budget/tick/performance reconciliation, dedicated
launch containment including pre-existing processes, durable crash-tail recovery,
storage/archival faults and real OS/filesystem/network isolation remain open
under M0.3b.2c.2/.3c and the existing M1/M2 work. Same-user private files, listener
ownership and a Job Object are not an adversarial gameplay sandbox. Remaining
eight motors, expert recipes/containers/machines/quests, keybinding, native model,
soak/team/research and later-pack gates retain their complete scope. No inference
was dispatched; desktop control remains paused.

Sources: [implementation](../../src/mcbench/forge_guard.py),
[Node guardian adapter](../../backends/mineflayer/src/forge_guard.ts),
[worker](../../backends/mineflayer/src/worker.ts),
[operator contract](../operations/process-guard.md), and Microsoft's
[GetExtendedTcpTable](https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable)
and [MIB_TCPROW_OWNER_PID](https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid)
contracts for listener ownership.
