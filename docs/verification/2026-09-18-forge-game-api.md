# 2026-09-18 structured Forge API development evidence

Historical initial read-only slice. Subsequent native action work is recorded in
[the action-lane report](2026-09-18-forge-game-actions.md); the checks below retain
their original scope and artifact identity.

Scope: M0.3/M0.3b, F01/F06/F16/N02/N04, C09/C15, T01/T03/T06/T07,
G0/G1. Operator-only; no gameplay-agent access. This is development implementation
and synthetic conformance evidence, not an authentic Forge game pass.

## Selection and delivered behavior

User reaffirmed that ordinary character control should use Mineflayer or an API.
Desktop interaction remains paused. No desktop input, game/server launch,
profile installation or inference dispatch occurred in this change.

Inspected the pinned Forge 1.19.2-43.4.23 `HandshakeHandler` source (sources JAR
SHA-256 `663e58cdde75ce06f4713cfcedea4414c39d17adcfddcfa81c6da5adcd59102f`).
`handleServerModListOnClient` validates channel and datapack-registry compatibility;
server-side channel validation rejects mismatches; registry receipt installs
snapshots with `GameData.injectSnapshot` and checks missing data before ack.
Thus acknowledging offered channel names is insufficient. D06 selects the
existing SPEC fallback, with a separate `forge_client` identity. This source
assessment does not supersede the actual failed Mineflayer login or prove a
Forge API implementation.

Implemented:

- Native client-thread filtered state in `NativeGameRuntime`, registered modded
  IDs, player inventory, exact supported native menu classes and cursor stack;
  no NBT, unopened containers, block entities, global registries or evaluator data.
- Conservative fixed-ray `GameVisibility`; immutable bounded/expiring `GamePages`
  with distinct native clock identity and capture time preserved across pages.
- Opt-in private `ClientGameBridge` and separate game request/response/connection
  schemas, sharing the existing bounded authenticated HTTP transport. One
  client-thread operation per tick; game and settings routes/schemas stay distinct.
- Strict Python operator client `mcbench.native_game`, including response projection,
  session matching, request polling, bounds and credential-safe errors.

`forge1192-structured-development/1` advertises only `capabilities` and `observe`,
an empty action list, `campaign_admission=false`, `conformance=unverified`,
`keybindings=false`, `screenshots=false`. Unsupported actions reject; they are
not stubs reported as completed. The existing gameplay package remains the scoped
Mineflayer client. No ordinary Forge action motor or worker routing is yet present.

## Executed checks

Environment: Windows 11, Python 3.12.14, Temurin JDK 17.0.20.1+1,
Gradle 8.8, ForgeGradle 6.0.42, Forge 43.4.23, official 1.19.2 mappings.
The build's existing compiler/dependency hash checks ran; no new dependency added.

1. In `java/`, with the pinned `JAVA_HOME`:
   `./gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain`.
   Final build succeeded, **39 Java tests passed**: 10 game visibility/paging/protocol
   cases plus the existing 29 settings/parser cases. Geometry and runtime ports
   are synthetic; HTTP and parser/queue execution are real local implementations.
2. Explicit JVM integration environment supplied the pinned `java.exe` and generated
   `test-classpath.txt` via both `STRATA_CLIENT_TEST_*` and `STRATA_SETTINGS_TEST_*`:
   `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py tests/test_native_settings.py tests/test_native_settings_jvm.py tests/test_gameplay_package.py -q`.
   **31 passed in 8.98 s**, including **two actual Python/Java game HTTP tests**,
   four actual settings JVM tests and gameplay allowlist packaging. No JVM tests
   were skipped. Game fixture processes contain synthetic geometry and no game
   account, server or Minecraft window.
3. Targeted Ruff over the new game client/tests and shared settings client passed.
   `git diff --check` passed (existing line-ending notices only).

The first cross-language run failed one case (29 passed): Java's nanosecond
`Instant` timestamps exceeded the public Utc fractional-digit limit. Native and
fixture serialization now truncate to milliseconds; a regression case and the
final actual Python/Java exchange passed. Earlier successful Java-only builds
did not establish this wire compatibility.

Negative coverage: occupied modded blocks and glass hide deeper cells; unknown
chunks terminate visibility; edge/corner cracks reject; inside-wall and distant
entities are hidden; pages retain frozen bytes/age/revision and reject guesses,
wrong dimensions, expiry, eviction and reset; oversized scenes reject; actions,
raw/eval/admin/settings operations reject; wrong auth/session/schema/routes and
hidden-state query arguments reject; returned NBT/private fields/malformed pages
reject in the Python projection without replay. Settings transport/recovery
regressions remain covered by the existing tests.

Built client JAR SHA-256:
`04a61c4c2a381062e2fc26be2fdf34461971ee2a788b4fe149511c568961f651`.
It was **not installed** in the live profile. Private archive
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-game-api-01/` retains selected
test reports, source/artifact hashes and the scope receipt, without connection
credentials or game files.

## Remaining gates and next work

The Mineflayer/E9E T03/G0 failure remains. The Forge candidate's authentic T03
cases are `not_run`; no pack/backend/milestone/gate is promoted. The read-only
development slice is `implemented_unverified` for live game behavior.

Next: M0.3b.2 public-contract worker routing and a durable native action lane
with lease/deadline/epoch fencing, delivery receipts, cancellation, ambiguity
recovery and charges; then M0.3b.1b ordinary player actions, and M0.3b.3 actual
modded metadata/collision/recipe/container/machine/quest/reference tests.
Client-thread watchdog behavior during a hung client, same-user isolation,
source/gateway clock mapping, real observation latency and resource overhead,
settings effects/restart and all model-host/research gates remain unverified.
