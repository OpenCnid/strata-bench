# Client startup profile and retained admission failures

M0.2c.3b.3c.2a supports the positive craft/history integration under F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, T01/T06/T07/T10/T13 and G0 item 5. The source admission contract is implemented; authentic startup qualification is blocked for this protected profile.

The new 6-GiB profile passed actual pair admission, but neither fresh attempt launched Minecraft. Case01 rejected a missing executable; case02 stopped on Windows process creation before the Java preparation helper started. These are failed attempts, not startup or craft passes. No model requests were made.

## Diagnosis and implementation

The retained September 21 history-required case02 missed its 270-second client bootstrap limit at 271.078 seconds. Its startup log continued after the Nomadic Tents/JEI exception; that exception is not an established cause. The runner's thread-dump block was in a later bridge-read loop and could not diagnose this earlier failure.

A separately retained GC log matches the registered filename, PID24092 and 269.089-second final uptime. It was outside the original sealed trial and is supplemental evidence only: 334 pauses total 8.178108 seconds, maximum 172.247 ms, no full collections, and 13 concurrent mark cycles total 27.695749 seconds. Overlapping durations are not added. These observations do not establish the timeout's cause.

`PrivateReferenceClientPreparation/3` binds `hotspot-processors4-heap512-6144mib/1`. Both leased argument checks require exactly one effective CPU4 flag, `-Xms512m` and `-Xmx6144m` before the Forge main class. Duplicate, missing, conflicting, post-main and operand-only flags reject. Old schemas cannot carry the new policy; reports exclude argument and credential contents. Legacy proofs retain their original meaning.

The candidate changes the client maximum heap from 3 to 6 GiB and uses server telemetry0.3.11/history4. It is therefore not a causal comparison of heap alone. The original 270-second bootstrap, 335-second client, 360-second participant, 600-second server and D13 one-second shutdown limits remain unchanged. No mod was removed or recipe changed. About 35 GiB free memory was observed before preparation; OS resources were not reserved.

## Executed verification

The focused preparation/pair/client selection passes **91 tests, one skip** with the telemetry JVM fixture enabled:

```text
pytest tests/test_reference_preparation.py tests/test_reference_pair.py tests/test_reference_client.py -q --tb=short
```

The unchanged optional client-JVM test lacked its separate fixture classpath. An earlier overlapping source-only run passed 72 with 20 fixture skips. New negative tests caught generic ValueError handling that hid typed heap and policy faults; that was fixed before preparation. Repository-wide Ruff and whitespace checks pass.

The pinned Temurin17.0.20.101 JVM executed PrintFlagsFinal/version only, reporting four processors, 536,870,912 initial heap bytes and 6,442,450,944 maximum heap bytes. This does not prove Minecraft startup performance.

## Retained attempts

Private scopes are `2026-09-23-protected-craft-heap6-01` and `-02` under `C:/Users/Darian/.strata/evidence/`.

- Before case01 dispatch, copied helper paths were corrected to the current worktree and pins rebuilt. Session preparation first failed because the local ACL helper's Python runtime was absent. A local venv was created without package downloads, its helper verified, and the failure retained. Pair admission then rejected the removed app-install Codex executable. Its private database remains empty; no pair process or game launched. Credentials were retired. This intent was not replayed.
- Case02 uses the identical retained Codex executable hash, a fresh scope and the same hash-checked unplayed 8,609 source files / 563,327,661 bytes. All 468 pair inputs were checked. Version3 heap/session admission passed, then the native runner reported `CreateProcessWithLogonW failed: 5`. The pair retained `WRITER_JAVA_EARLY_EXIT` and an uncertain result. No Java preparation helper, server or client game launched. The retained runtime directory has an owner/system/administrator-only ACL; its causal role has not been proven.

Case02's **14/14 failure-retention checks** pass. All 12 outer processes and seven nested preparation processes are terminal without forced termination; these counts overlap. Pair lifetime was 63.969 seconds; preparation's recorded interval was 22.125 seconds. The original 39 accounting tables, client mods, client options, staged sources and pair pins remain unchanged. Session arguments were retired, and no Java process remains. The durable pair stays UNCERTAIN.

## Evidence and next action

The bounded supplemental archive is `C:/Users/Darian/.strata/evidence/2026-09-23-client-startup-result-01`:

- Seal: `663324089025e6494d221a0667d08984d0125b786206cc5ba59ce0ffa9e6ebfd`
- 423 files / 47,353,934 bytes, fully rehashed by the existing reader.
- Result: `f1b4c32a8765f8821a4d3931b81093ba3423e93825eb1e0ae0c49db70b20054e`
- Failure audit: `5519f20f75d21b70c5fadef5e4605e8c91b705df76487d9b8d0b27f29706b7c6`

It contains diagnosis, source, plans and retained failure evidence; raw game installation inputs remain separately pinned and hash-checked. The first installation-inclusive manifest exceeded the reader's 512-MiB quota and later lost an ephemeral SQLite sidecar. That rejected manifest is preserved, not claimed as a valid sealed bundle. The supplemental archive is separate.

Do not rerun the unchanged protected profile or treat Windows writer repair as a new M0 isolation prerequisite. Continue D14's development scope through independent scorer/game/clock work. A future client trial needs a fresh scope, revalidated inputs and an explicit development-profile disposition for the protected writer dependency before launch; do not silently remove its boundary or claim protected scoring. The prepared source remains unused by a game.

Original exposure remains **$1.795559 of $10**, including all unknown holds. D18 continuing approval requires no new per-run permission, while unresolved usage still blocks paid admission. Complete scoring, clocks/save custody and exact profile qualification remain open. M0 is in_progress; G0 remains fail; D14 isolation deferral and M1–M7 are preserved.
