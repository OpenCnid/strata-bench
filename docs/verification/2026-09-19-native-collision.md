# Loaded Forge collision-shape probe

Operator-only. SPEC v0.2.33; M0.3b.1b.2b.2b.2 in_progress;
F01/F06/F16, N01/N02/N06; C09; partial T01/T03. No aggregate gate passes.

The existing [ClientCollisionProbe](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientCollisionProbe.java)
has 13 cases that previously could not run in plain JUnit because the loaded
Forge transformations were missing. Original failure and synthetic planner tests
remain in the [route-planning report](2026-09-19-forge-route-planning.md).

A fresh dedicated title-client launch completed with exact E9E 1.27.0,
Minecraft 1.19.2, Forge 43.4.23, pinned Temurin 17 and installed minor-34
b2a91155... JAR. Reviewed installed official launch arguments omit server/port;
only the existing private collision-probe property and read-only bridge are
enabled. No world join, action authority, OS input or inference. Cached session
lifetime, 97 bootstrap pins, options and JAR are checked. Independent guardian,
300-second outer lifetime and existing stop bounds remain.

Cases cover native air/stone/three slab shapes, waterlogged rejection, age limit,
old/future/incorrect-ID/unknown-ID/missing-cell rejection and a constructed level
route using actual native block shapes. This is loaded-runtime integration on
constructed state, not authentic observed-world motion or complete modded
geometry. All 13 cases pass on the loaded Forge client.

Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-native-collision-01`.

## Executed result

All 13 native shape/constructed-route checks and 20 read-only API checks pass.
The descriptor was ready at 160.828 seconds; total procedure 164.812 seconds.
Capabilities expose no actions, and ten observations reject GAME_NOT_CONNECTED.
The listener belongs to the held client PID. Base guardian confirms termination
with reported 344 ms wait; this is its existing coarse-clock measurement, not
new QPC/strict timing proof or qualification of the failing world-client path.

The collector verifies all 97 bootstrap pins, unchanged options/JAR, six source
snapshots and three private script/template hashes, exact policies and 13 case
names, probe digest, no authority/action journal, argument retirement and zero
Java processes. Input desktop unchanged. Private latest game log is retained.
Loaded JAR SHA-256:
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
Probe SHA-256:
`f915dc513e474a4e03c0cef19c182276a6ac362e1e58c68ed7fd685ca78270a4`.

This resolves the earlier missing loaded-runtime prerequisite for these exact
vanilla block implementations. Actual walking, interrupted controls, observed-map
filtering, modded blocks, steps/jumps/vertical transitions and full geometry
remain required under the parent children. The prior plain-JUnit failure and
world-client shutdown failures are retained. No native code changed in this
probe; no desktop input, server launch or inference occurred.
