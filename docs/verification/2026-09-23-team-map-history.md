# Private FTB team-map mutation observations

M0.2c.3b.3c.5 advances G0 item 5 and its parent F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24 and T01/T06/T07/T10/T13 coverage.
The actual changed-profile map control is verified below; full private scoring remains unqualified.

Pinned FTB Teams 1902.2.14-build.123, SHA-256
`2233122cfddfccafd5f4840ae63a556edd7088ad15e177fb1288367adef142f7`,
exposes its underlying rank map through getRanked(NONE), player map through
getKnownPlayers, team map through getTeamMap/getTeams and lazy name cache through
getTeamNameMap. Exact javap inspection shows one HashMap in TeamBase construction,
two LinkedHashMaps in TeamManager construction and one HashMap in the name-cache
getter. Direct map writes need not enter existing command/team hooks.

Telemetry 0.3.10 / ServerStarted/11 / NativeSetupHistory/3 replaces those exact
allocations with observers before aliases escape. Linked maps retain insertion
order. HashMap and LinkedHashMap methods and mutable views share checked entry
wrappers; retained entries, iterators, arrays and view removals cannot bypass
the write callback. Detached clones remain ordinary independent maps. The
existing KubeJS global observer uses the same view implementation and retains
its three-key filter.

The name cache is armed after the getter populates it, avoiding mutation counts
for lazy initialization caused by reads. Arming is irreversible and visible
across threads. Startup support reads the existing cache without populating it
and checks actual rank/player/team/cache instances. Fifteen fixed routes and
exact startup/history/module/policy joins feed private admission and candidate
rejection. Legacy policy1/2 evidence remains readable with its original scope.

Public scalar fields, including PlayerTeam.actualTeam, direct reflection,
pre-activation writes, full mechanical parity and custody remain unqualified.
No complete-history or scoring flag is enabled. The intended fresh headless
control will directly change and restore all four map roles, and also exercise
the refactored global observer. This is a changed-profile operator diagnostic,
with no model/player/desktop input, not unchanged-pack equivalence.

Initial verification: 68 focused Python cases pass with one unconfigured JVM
skip; Ruff passes. The offline Gradle test/reobfuscated-JAR build passes all
40 Java tests. The map test now checks both backing-map types, exposed mutation
methods/views, detached copies, linked order, retained aliases and lazy arming.
The subsequent JVM and authentic evidence is recorded below.

The full JVM-enabled focused selection passes 246 Python cases in 40.04 seconds with one existing explicit sandbox-group skip. All 40 Java cases and Ruff pass. The subsequent authentic control uses fresh private evidence `2026-09-23-team-map-history-live-01`.

## Authentic changed-profile result

The new E9E 1.27.0 / Forge 43.4.23 / ServerStarter 2.4 / Temurin
17.0.20.101 instance used telemetry 0.3.10 JAR
`d474ca93e5bf8c1074bd1b4077372dc5c9d23c64f99e63d78f76adad2c9f3e07`,
loopback port 25594 and the existing 2–5 GiB/300-second runtime/120-second
stop/600-second outer bounds. A sealed script performs direct modifications to
all four map roles after the clear startup observation. It verifies temporary
player lookup loss through entry-iterator removal, team lookup loss through the
values view, membership insertion through the raw rank map and name-lookup loss
through the lazy cache; each original effect is restored. It also exercises the
changed global observer with its prior six-write mode roundtrip. These are
script-observed effects, not independent saved-state snapshots or a new craft.

The independent stopped-run audit passes **44/44**. The actual native instances
report supported hooks. Terminal history retains exactly eight team-map writes,
six global writes and one ordinary native stop. All other routes, off-thread
counts and overflow remain zero. Both mutation reasons remain in the private
report after restoration; no full-history/scoring flag is enabled. Separate
signed synthetic craft tests prove these observations reject an otherwise valid
candidate and reject missing hooks or a mismatched sealed policy.

The server and outer runner stop normally after 139.859 and 143.687 seconds.
All six retained server and ten outer processes are terminal without forced
cleanup. Seventeen signed records preserve 206 actual server ticks and
14.390166800 callback seconds. All 206 ticks occur before the final health
sample; there is no invented tail tick or avatar/active-time claim.

All 18,225 original installation files, 1,542 immutable runtime files,
104 sealed fixture files and 39 original accounting tables match. No model,
player or desktop input was used; committed/reserved exposure remains
$1.795559 under the original $10. Consumed-grant and same-evidence relaunch
checks reject without dispatch. No live attempt failed or replayed in this increment.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-23-team-map-history-live-01`.

| Artifact | SHA-256 |
|---|---|
| Audit | `64e0a3aa3880677c2077bdec860a63a4f07f90827e3962312624bad101efeeca` |
| Authenticated stream | `6c9f33e9662f8d9007d9055614f47b40979f43f43225732476b844f267602188` |
| Complete seal: 327 files / 44,522,004 bytes | `a2b0dad4c2517da3b971ddc85e4fb8b3acf08fcfbb0065093ced19e8a12087fd` |

M0.2c.3b.3c.5 is verified only for these map-observation and control behaviors.
Complete setup continuity, scalar fields/reflection, custody, parity and scorer
qualification remain open. The next distinct integration gap is the changed
native/worker cleanup path under a scripted transport failure, preserving D18.4's
failed paid run and all unresolved usage. Do not repeat these successful setup
controls unchanged. M0/G0 remains incomplete; M1–M7 are unchanged.
