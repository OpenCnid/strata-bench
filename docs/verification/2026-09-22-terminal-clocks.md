# Terminal native callback clocks

September 22, 2026. Operator-only. M0.2c.1b; F09/F11/F13/F16,
N01/N03/N06/N08, C18/C20, partial T01/T07/T12/T13 and G0 item 6.
M0 remains incomplete and G0 fails.

Telemetry 0.3.8 / ServerStarted/9 binds
`server-event-monotonic-cumulative/1`. The producer records monotonic callback
exposure, completed server ticks, observed tick work and actual server-side
PlayerTick END events. It retains counts across disconnect/reconnect by UUID
without inventing events for absent players. Same-thread ordering, complete tick
pairs, one avatar callback per UUID per server tick and a 64-UUID bound fail
closed; clock rollback and protocol faults invalidate subsequent closure.

A single terminal ServerClock/1 precedes terminal setup history and stop. The
private reader verifies module/policy, exact final tick, terminal order, strict
counts, UUID bounds and consistency with sampled health totals. Both owned-launch
and existing cost reports retain the reconstructed record. Legacy health avatar
fields still mean connected presence at server boundaries; older spools retain
their original missing-terminal meaning. Overlapping cumulative and sampled
clocks are never added together.

This interval begins at clock activation inside ServerStarted and ends inside
ServerStopped. It excludes process/pre-startup and post-callback time, including
any remaining exit work. It does not establish admitted active time, complete
roster mapping, save custody, isolation, instrumentation parity or complete
project accounting. Canonical records, gameplay tools and acceptance thresholds
are unchanged.

Source verification on pinned Windows/Python 3.12.14/Temurin 17:

- Offline `:forge1192-telemetry:test :forge1192-telemetry:build
  :forge1192-telemetry:writeTestClasspath` passes, 39 Java tests and no skips;
  23-second build, 11 tasks. Eight new clock tests cover tail/idle/reconnect,
  actual event counting, signed nanoTime wrap, rollback, thread/order faults,
  incomplete closure and quota rejection.
- Connected clock, telemetry/authentication/pipe, cost/restart, history/control,
  owned-launch and package selection: 243 passed, one skipped, 48.64 seconds.
  The production accumulator/signing/owned-JVM fixture joins 22 fabricated ticks
  and two avatar events, preserves the two-tick terminal tail, stops normally
  and refuses replay. This is a synthetic event source, not Minecraft.
- The additional version-9 pipe transport matrix passes: final pipe selection
  16 passed, one skipped, 1.56 seconds; two cases are new beyond the combined
  run (245 distinct focused passes). The skipped peer/token case requires an
  explicitly supplied existing Windows sandbox group.
- Initial Python selection: 89 passed, one failed, three opt-in skips. Its
  integral-float fixture canonicalized the value to an integer before signing;
  the corrected fractional fixture and separate uncanonicalized integral-float
  wire test both reject. Production numeric validation did not change. Four
  test-only Ruff semicolon findings were corrected; full Ruff passes.

## Authentic headless reference

Fresh `2026-09-22-terminal-clock-live-01` uses the original E9E 1.27.0 / Forge
43.4.23 source clone, official ServerStarter 2.4, pinned Temurin JRE
17.0.20.101 and the new telemetry 0.3.8 JAR
`c614e4cd936357ec85131b6065ff4aea3dcfdc17507cde141fa79f7e4275d285`.
The existing online loopback profile uses port 25592, unchanged 2–5 GiB heap,
300-second runtime, 120-second cleanup and 600-second outer limit. No participant,
model request or desktop input was used.

The reference stops normally: 152.875 seconds server-runner exposure and
156.890 seconds outer exposure, six held server and ten outer processes all
terminal, no forced stop. Its 17 authenticated records contain 207 completed
server ticks, 15.902282599 seconds of callback exposure and 1.530240106 seconds
of observed tick work. All 207 ticks happened before the last health sample;
there is no invented additional tail tick. Callback time outside the health
intervals is 5.594290899 seconds, covering the separately observed startup/tail
remainder. The terminal clock agrees exactly with the owned launcher report.
Avatar event counts are empty. Signed history has only the one native stop;
there is no craft candidate or score.

The reviewed independent audit passes 38/38 checks, preserving 18,225 original
files, 1,541 immutable runtime files, the 104-file sealed fixture and all 34
original accounting tables. The first audit retained 36/37: it expected a later
relaunch-denial code, while the launcher correctly rejected the existing evidence
directory first (`REFERENCE_EVIDENCE_PATH`). A separate consumed-grant preflight
then rejected `CRAFT_GRANT_ALREADY_USED` without a process or new event. Both the
original audit and review remain in evidence; no game replay occurred.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-22-terminal-clock-live-01`.

| Artifact | SHA-256 |
|---|---|
| Reviewed audit | `35836b9349d7aca6a459345c3368819ca9fe75bd492a421c8360f39fb778a7d0` |
| Authenticated stream | `6a1174a1e1fe9ed2cb2d391bb0b7b7f922b1dde6b78ea6afa6910d81d331e753` |
| Complete seal: 294 files / 44,106,116 bytes | `c7b9218f1fea9501aeb5f2e8ceb57c105d5964e80a5fc7d3ad010fd326b0524e` |

M0.2c.1b remains **implemented_unverified** for its complete contract: source and
headless server callback evidence pass, but authentic avatar callbacks, admitted
roster/active-time and full timeline joins remain unqualified. Do not repeat this
unchanged headless reference. D14 now defers isolation qualification to M1/G1 and
prioritizes direct observations/actions and actual LLM piloting. Original unknown
model usage and consumed D12 remain unchanged; no new model dispatch occurred.
