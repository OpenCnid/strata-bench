# Guarded unattended E9E startup — September 19, 2026

Operator-only. M0.3b.2c.3c.2a is implemented_unverified for full production use.
SPEC v0.2.27; F01/F05/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
C02/C04/C09/C15/C18; partial T01/T02/T03/T06/T07/T12. No aggregate gate passes.

**Actual startup passed:** exact installed E9E 1.27.0 / Minecraft 1.19.2 /
Forge 43.4.23 / Temurin 17.0.20.101 reached its title-screen native bridge on a
fresh non-input Windows desktop in 171.266 s. Ten capability reads and ten
expected GAME_NOT_CONNECTED observations passed. The native loopback listener
belonged to the held Java PID. Input desktop remained Default. Independent
guardian stop confirmed termination in 329 ms; total elapsed 175.172 s. The held
owned process was subsequently confirmed absent. No world/server connection,
game action, input injection, launcher UI automation or inference occurred.

[DesktopJava](../../src/mcbench/desktop_client.py) uses the existing suspended
non-input-desktop launcher and an independent Java challenge guardian. Kernel
job ownership begins before Java user code; the second guardian attaches after
launch and before readiness is returned. The caller must pump fresh challenges.
A stalled caller cannot renew the 1.5-second guardian lease. This is the base
Java lifetime guardian, not full Forge-aware native-health/worker qualification.

The private directory receives an exclusive 64 KiB bounded, forced-to-disk launch
journal and exact held-process grant. Journal records omit arguments, environment
and challenge nonces. Its elapsed_monotonic_ns field stores the local monotonic
clock reading (arbitrary epoch); only differences are elapsed durations. Guardian
terminal evidence explicitly reports release_confirmed:false and requires_resync.
Forced process termination is not a clean game checkpoint. Desktop/job placement
does not establish filesystem/process/network/credential isolation.

Four disposable real-JVM tests passed in 7.37 s: normal stop with unchanged input
desktop and nonce-free evidence, stalled-caller lease expiry, guardian crash with
no false successful stop, and invalid startup. The fixture creates no windows,
inputs, network connection or Minecraft state. The explicit gameplay bundle
exclusion test passed in 0.31 s. Ruff passed. Original tests/logs remain private.

The live test used a new private client copy containing 9,862 copied files from
the dedicated official CurseForge profile. Existing saves, logs, crash reports,
account/server-list caches and launcher-instance metadata were not copied. Expert
configuration/scripts/resources were retained. The new copy loaded candidate
minor 33, SHA-256 4db8ae89f0e095653eee8a05f745409073f1196f495e8796291a53c3030d8171.
The original CurseForge profile remains on minor 30, SHA-256
f10e7ad6ddbbf48df176183cc4e0dc60891a50d2528858ceb452b2c96a6aa625.
Options in the copy set master sound to zero, max FPS 30 and fullscreen false;
requested window size 854×480 and maximum heap 4096 MiB. These are explicit
development-run settings, not a benchmark performance certificate.

The launch script used the installed official parent/Forge version JSON,
Windows rules, Forge library overrides, 93 classpath entries and original
BootstrapLauncher/forgeclient arguments. Required libraries, assets index,
logging configuration and game JAR matched recorded upstream SHA-1 values;
SHA-256 pins were retained. This is direct JVM bootstrap, separately labeled
from the original official launcher UI workflow. There were no new downloads or
replacement launcher product. Full transitive PackLock/provenance remains open.

Initial preparation rejected the base versions/1.19.2/1.19.2.jar because it does
not match the Mojang download digest and lacks the signature manifest. Its cause
was not established. The Forge profile's forge-43.4.23.jar exactly matches that
official client digest (SHA-1 055b30d860ead928cba3849ba920c88b6950b654) and was
used. The mismatched file was not modified; retain it as a vanilla-client
provisioning/lock finding. No already-recorded vanilla server/Mineflayer result
is invalidated by this client-file finding.

The first cached-session preparation failed before authentication due to an
incorrect local compiled-module path. Corrected dist/src imports, then reused
the Java-owning account's protected cache successfully. No login prompt was
automated. Session arguments went only to a separately ACL-protected operator
directory; the temporary argument file is retired after the run. Account tokens,
profile identifiers and raw game logs are never included in this public report.
The game log also contains certificate-expiry/update/optional-class warnings;
successful title startup does not qualify those external integrations.
The evidence collector initially expected no saves directory; Minecraft created
an empty one at startup. Corrected the check to require zero entries. No world
save or prior-world content exists in this client copy.

Private scripts, source hashes, dependency/copy inventory, failed attempts,
guardian events, API outcome and logs:
`C:\Users\Darian\.strata\evidence\2026-09-19-desktop-client-01`.
Dedicated stopped client:
`C:\Users\Darian\.strata\clients\e9e-noninput-01`.

Remaining .2b/.1b.4 work: bounded private game-only frame evidence, native render
and focus/pointer/physical-key qualification, authenticated world/worker/action
integration with independent server evidence, full native-health guardian,
resource/storage bounds and real security principals. Title-screen capabilities
do not prove JEI hooks executed, complete observations, mechanics or cancellation.
All M0–M6, T03/T05 and release gates retain their existing scope and limitations.
