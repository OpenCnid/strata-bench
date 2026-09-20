# 2026-09-18 scoped Forge worker integration

Operator-only. Advances M0.3b.2b.2 and the local charge/clock portion of
M0.3b.2c; F01/F06/F09/F11/F16, N02/N03/N04/N05/N06/N08, C03/C09/C15/C18,
partial T01/T03/T06/T07/T12 under G0/G1/G2. No aggregate gate passes.

## Implemented behavior

- The existing supervisor/worker and allowlisted public gateway now select either
  the original vanilla Mineflayer configuration or an explicit Forge development
  configuration. There is no automatic fallback. Both use the unchanged `mcgame`
  CLI and its actor-scoped public grant. Native credentials, identity/authority
  operations and raw native transport are not exposed through that grant.
- `ForgeLane` verifies the exact native capability policy, loaded immutable
  campaign/avatar/capability/body/limit authority, source fingerprint and current
  connection generation before arming. A second broker cannot take over an
  already armed native body. A fresh higher epoch requires the old lane fenced.
- New private `authority` and `observe_bound` operations return the loaded scope
  and a snapshot tagged with body/generation on the same client thread. Wrong
  identities, generation changes, unexpected clock domains and hidden/unknown
  public fields cannot be projected as valid gameplay observations.
- The broker serializes bounded observation delivery, validates the complete
  public schema and 64 KiB ceiling, records projection before native delivery
  authority, then records the final outgoing observation. Public capture time is
  conservatively mapped from request start minus native age; cached pages retain
  the first mapping. Raw native clocks and request/response bounds remain private
  evidence. Native elapsed time is never relabeled as the gateway clock.
- Public intent is durable before the one native action POST. Lost mutation
  replies become unknown; only status is subsequently queried. Input-only native
  receipts remain `emitted`, not `completed`. Successful public receipts reference
  a fresh observation. Native cancellation/stop must confirm a healthy fenced lane
  with no active action within the worker release bound; uncertainty never claims
  release or allows another action in that epoch.
- Cumulative native attempted primitives, including arm/stop releases, reconcile
  to a durable per-authority high-water mark and the local worker counter. Status
  duplicates and higher broker epochs do not refund or duplicate those charges.
  This is not yet the controller's aggregate BudgetLedger integration.
- All compiled broker modules, public schema bytes, the package lock and native
  fingerprint contribute to capability identity. Public record schemas did not
  change. The private capability operation lists changed; older bridge builds are
  rejected rather than treated as interchangeable.

## Executed checks

Windows 11, Node 24.19.0, Python 3.12.14, Temurin JDK 17.0.20.1+1,
Gradle 8.8 / ForgeGradle 6.0.42 / Forge 1.19.2-43.4.23, official mappings.

- From `java/`, pinned `JAVA_HOME` and
  `./gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain`:
  **58 Java tests passed**, no failures/errors. New tests cover loaded-authority
  immutability and body/generation tagging on the client thread.
- From `backends/mineflayer/`, `npm run build`, then explicit
  `STRATA_CLIENT_TEST_JAVA` and `STRATA_CLIENT_TEST_CLASSPATH` with
  `node --test dist/tests/*.test.js`: **90 passed**, zero skipped, 18.785 s.
  Of 15 new Forge tests, 12 use actual Java fixture processes and HTTP. They cover
  actor/capability rejection, an exclusive native owner, stable page age,
  fresh receipts, charges across epochs, cancellation, a lost action reply,
  hidden state/body/generation rejection, an actual killed JVM, the existing CLI,
  and actual supervisor/worker processes stopping at their wall limit.
- With those explicit JVM environment variables,
  `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py tests/test_gameplay_package.py -q`:
  **21 passed**, zero skipped, 9.66 s. The allowlisted gameplay package remains
  independent of native credentials and broker implementation.
- Targeted Ruff passed. `git diff --check` passed with existing CRLF notices only.

Raw Node/Python JUnit reports and logs, Java test XML/build log, source hashes and
verification metadata are retained privately under
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-worker-01/`.
Built client JAR SHA-256:
`645ddf1b6968b1c53e5dbea0da0aa96bab7301db566a3c5710624a9a754ac5b0`.
The JAR was **not installed**. No Minecraft process, desktop interaction, account
flow or inference was launched. The fixture runtime does not implement Minecraft.

## Still incomplete

The development route is implemented but unverified against E9E. Campaign
admission remains false. All eight remaining native action kinds, authentic
registry/collision/expert recipe/container/machine/quest cases and complete
vanilla conformance remain open. M0 is not complete.

Controller input generations and repair holds, aggregate budgets/ticks/performance
and clock qualification, real OS/process/network separation, bounded evidence
archival and independent hung-client termination are unfinished. Killing the
synthetic JVM in a test demonstrates honest uncertainty; it does not establish
that the supervisor can identify and terminate a hung authentic client. Full
settings T05, native model/helper execution, soaks, teams and scientific gates
retain their original requirements. Desktop control remains paused.
