# 2026-09-19 authentic Forge API startup and observations

Operator-only. Scope: M0.3b.1a and loaded-artifact identity shared with M1.1a.2;
partial F01/F05/F06/F16, N01/N04/N06, C04/C09/C10, T01/T02/T03/T06
under G0/G1. No campaign or release gate is qualified by these checks.

The user explicitly renewed desktop authorization on September 19. The dedicated
CurseForge E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 profile was launched
through its official launcher with the previously pinned Temurin 17.0.20.1+1
runtime and 4096 MiB maximum heap. The original discovery-only extension and
profile/options files were backed up privately. No account authentication was
automated, no logs were uploaded and no model inference was dispatched.

## Live failure and correction

The first launch used the previously tested ten-action JAR
`05f8c300aeda0a1a1bc3851fc907fa67a80255f9b19a36f944abfa5a5f2e5119`,
with only `strata.gameBridgeDirectory` enabled and no action authority. It
crashed before creating the endpoint: `SettingsFiles.safeExisting` called
`toRealPath().equals(...)` while fingerprinting a loader-supplied mod artifact.
The pinned Forge JarJar provider's `PathPath.toRealPath()` returns null. Its
normalization semantics also differ from host filesystem paths. This is a
Strata startup defect, separate from the earlier Mineflayer/Forge login failure.

[ArtifactFiles](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ArtifactFiles.java)
now hashes the actual bytes of regular loader-supplied host, Union and JarJar
entries, with a 512 MiB streaming bound and typed rejection of unsupported
providers. It never reconstructs host paths from archive URIs or basenames.
Union backing validation is bounded. Virtual paths are accepted only in this
read-only loader-artifact helper; options/journal writes explicitly reject
non-default filesystems. This does not establish a sealed installation or
malicious-mod/process isolation. Both settings and game fingerprints include
the changed hashing policy.

## Executed software verification

- Pinned Gradle client tests/build/reobfuscation/classpath generation: **91 Java
  tests passed**, zero failures/errors/skips. Six new cases exercise exact-byte
  host/Union/nested-Union/JarJar hashing, the real null-real-path behavior,
  preservation of the writable-file boundary, unsupported providers and
  missing/directory/relative/oversized input rejection.
- The initial provider test run exposed a missing test-only Java module opening;
  the authentic Forge launcher already supplies it to SecureJarHandler. Two
  subsequent regression iterations exposed fixture-root and JarJar normalization
  assumptions. Their failures are retained in the private logs; none were live
  successes. Final test configuration opens `java.lang.invoke` to the test
  classpath only, mirroring the pinned provider's runtime requirement.
- `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py
  tests/test_gameplay_package.py`: **27 passed**, zero skipped, 19.00 seconds,
  with the explicit pinned Java/classpath. JVM cases use synthetic game state.
- Targeted Ruff and `git diff --check` passed (existing CRLF normalization
  warnings only). No unrelated Node or full Python suite rerun is implied.

Corrected built/deployed JAR SHA-256:
`c2218c6c9ae2e1e4a7e6f216d9fd16f084404d38bcebf0f47ccca17a24f462ce`.

## Authentic read-only checks

[Operator check](../../tools/check_forge_observations.py) uses only capabilities,
identity, observation and unsupported lane-status queries. It checks strict typed
responses, disabled mutation authority, disconnected errors, bounded immutable
pages, body/generation identity, old-page age, guessed-cursor rejection and fresh
capture identity. It records private raw results and round-trip times, excluding
connection credentials. Passing these cases does not prove hidden-state filtering
against server geometry, actual action effects, latency targets or isolation.

The corrected client reached its actual title screen (240 loaded mods) and
created the private endpoint. Six live assertions passed: a typed capabilities
response, empty action authority, unsupported lane status, and disconnected
identity/observation/bound-observation errors. This six-assertion check passed
again from the multiplayer menu while still disconnected.

Ten transport assertions also passed, including the three capability/read-only
assertions and seven raw HTTP negative cases: missing/wrong credentials, browser
Origin, foreign Host, wrong session, expired deadline and settings/game schema
confusion. The first transport-check attempt had a Python variable-shadowing
error before sending any raw negative requests; it is retained as a checker
failure. The corrected check passed and was repeated with the exact checker
source/hash included in its private result bundle. No negative request contained
a gameplay mutation. These are transport-boundary results, not OS isolation.

Connected observation tests were **not run**. A Windows Security firewall dialog
for OpenJDK appeared over the multiplayer screen and blocked the direct-connection
click. The operator requested that the user handle it, as required by the
computer-use skill; no security setting or dialog button was automated. The
client remains at that screen, with read-only API authority. No world was joined.

Both bounded server attempts reached ready and stopped normally: the first after
the startup crash (exit 0, 150.515 seconds), the second while the security prompt
remained unresolved (exit 0, 245.031 seconds). Both retained complete logs and
used ordinary stop without forced termination. No gameplay action or inference
was dispatched. Restart the local server after the dialog is cleared, then run
the connected checks; movement/crafting implementation can continue independently.

Private evidence: `%USERPROFILE%/.strata/evidence/2026-09-19-forge-live-api-01/`.
The `bridge/` subdirectory contains a credential and must never be exported.
Crash/game logs, deployment receipts, raw observations and test XML remain private.
The historical Mineflayer/E9E T03/G0 failure remains. Native movement, crafting,
complete placement, expert recipes/machines, controller/aggregate accounting,
isolation, keybinding effects, host integration, soaks, capacity and research
gates remain open.
