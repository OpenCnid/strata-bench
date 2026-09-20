# Native settings crash trial blocked by recurring CTM startup failure

2026-09-20. Operator-only. M1.1a.2.3c.2b.1 and B10; partial
F01/F06/F09/F16, N01/N02/N03/N04/N06/N07/N08, C04/C10/C11/C14/C18,
T02/T05/T07/T13. The attempted authentic sample **fails before the planned
settings boundary**. The boundary and recovery cases remain unrun.

After published source `bb224486cb94b6e64ec732fb267547c9628cbdef`, the stopped
dedicated E9E client receives the tested crash-fixture artifact, SHA256
`6332576ea722a9ab49255cb0187851b22e4e9f4fb8e42f70dbbdc19eb723f051`.
The previous minor-34 bytes, SHA256
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`,
are preserved privately. All mods, Java, libraries and operator sources are
hashed in the fresh plan. There is no game operation/capability change; the
new artifact still requires a new native fingerprint and authentic evidence.

The first of six separate planned crash/recovery pairs selects
`apply_runtime_written`. The title-only probe is meant to capture prepared
journal/native-changed/disk-original state and exit 86 before recovery. Existing
480-second client, 280-second readiness and five-second API limits remain.
Only this first crash client actually launches; no recovery or later pair runs.

The client exits at startup with Windows code 4294967295 (signed -1), not 86.
Total procedure time is 84.157 s. During texture resource loading, exact
`CTM-1.19.2-1.1.6+8.jar` throws a HashMap Node-to-TreeNode ClassCastException
at `ResourceUtil.lambda$getMetadata$1`, source line 64. The crash occurs on a
resource worker before the title-screen probe. This repeats the signature in
the [earlier retained CTM sample](2026-09-19-native-quest-cancel.md).

There is no armed report, reached-boundary report or settings journal. The
broker contains only its original plan. Options remain byte-for-byte original,
SHA256 `38b89fb282ee5c4cc0ecd9d3180dbc76b43a9aa7624e1d970ece9a07fda03833`.
The held process signals; the independent guardian confirms PROCESS_EXITED;
Java count is zero, input desktop unchanged, and protected temporary arguments
are retired. No server/world, physical input or inference occurs.

The independent startup audit retains a fail result and confirms the absent
transaction, unchanged file and terminal cleanup. Audit SHA256:
`5e183c90b9dd122f4e487a714247701791844d7cb2ac301f58df76ad9af9796c`.
The initial strict UTF-8 log read rejected a native-encoded byte; the audit
therefore uses exact ASCII signature bytes without altering the original log.
Plans, runners, client logs/crash report and audit remain external under
`C:\Users\Darian\.strata\evidence\2026-09-20-settings-crash-native-01`.

The installed CTM SHA256 is
`4a44e793ec6fb015dbfc02258b6bdb14151e1c42e9968990f1b322b864d381cd`.
Read-only `javap -p -c` inspection confirms its static metadata cache is a plain
HashMap. The get/put/clear operations are unsynchronized, including a null-valued
negative-cache write on the failing path. This is consistent with the upstream
[open concurrency issue #176](https://github.com/Chisel-Team/ConnectedTexturesMod/issues/176),
rechecked September 20. An exact interleaving was not captured; the concurrency
explanation remains an evidence-backed diagnosis, not a proved repair.

Do not repeat the unchanged trial to seek a pass, remove CTM, substitute another
mod or treat the synthetic fixture as native evidence. Next inspect exact
upstream/artifact loading and supported executor controls, then record and test
an explicit compatibility remedy with its own pinned profile. All prior failed
samples remain; B10 now affects the settings crash matrix as well as startup
reliability. G0/T07 remain fail; complete T05 and G1–G5 remain not_run.
