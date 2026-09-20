# Native startup world connection — September 19, 2026

Operator-only; keep live records, account/connection material and images outside
gameplay contexts and the public repository. M0.3b.2c.3c.2b.2a, partial
F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08; C02/C09/C15/C18;
T01/T03/T06/T07/T12/T13. No aggregate gate or milestone closure.

**Fourth authentic run passed the bounded read-only world check.** The dedicated
E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 client joined through native startup,
served structured observations and produced two private world images on its
non-input desktop. Three preceding failures are retained below. Ordinary actions,
the scoped worker and its full Forge-aware guardian remain unqualified here.

## Implemented behavior

Components: [bridge lifecycle](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientGameBridge.java),
[render readiness](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameStartupReadiness.java),
[endpoint identity](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameBodyEndpoint.java),
[native runtime](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeGameRuntime.java),
[guardian events](../../src/mcbench/process_guard.py) and
[desktop wrapper](../../src/mcbench/desktop_client.py).

The pinned mapped Minecraft startup invokes ordinary ConnectScreen.startConnecting
after resource loading for native --server/--port arguments, without installing
TitleScreen. ClientGameBridge now initializes at either a disconnected title or
after an unobstructed world RenderTick.END for the same complete
player/level/connection tuple. Loading overlays, open screens and noRender
cannot establish world readiness; a changed level/player/connection invalidates
the prior render. This does not add an automatic join operation to the game API
or worker. The render-stage barrier does not certify future frame latency.

That native path passes null saved-server metadata. GameBodyEndpoint policy
server-metadata-or-resolved-tcp/1 preserves the existing menu-joined endpoint,
and falls back to the actual numeric TCP peer and port for native startup.
IPv6 is bracketed; no DNS lookup or fabricated ServerData occurs. Absent,
unresolved, non-TCP and invalid-port peers or corrupt metadata reject. The
endpoint and authenticated player UUID remain private hash inputs.

The Java process guardian now retains a bounded typed fault code in its failure
event; unexpected exceptions keep a generic code, without exception text. The
DesktopJava wrapper validates and journals that failure without treating it as
confirmed termination. Existing wall, challenge and 500 ms termination-confirmation
limits are unchanged. The full Forge-aware worker guardian is not exercised here.

## Verification and retained first failure

- Initial Java test/build passed: 415 tests, zero failures/errors/skips, 32 s.
  After endpoint repair, full Java test/build passed: 420 tests, zero
  failures/errors/skips, 33 s. Five endpoint tests cover preserved metadata,
  IPv4/port separation, IPv6, absent/unresolved/non-TCP/zero-port peers and corrupt
  metadata. These are synthetic contract tests, separate from game evidence.
  The subsequent readiness build passed 424 tests, zero failures/errors/skips,
  in 29 s. Four synthetic lifecycle cases cover missing renders, obstructed or
  partial joins, explicit clearing and replacement of each native body object.
- Python initially reported 9 passed / 15 skipped because the disposable-JVM
  classpath was missing. After supplying the pinned classpath, all 18 process
  guardian tests passed in 19.14 s. All six desktop-client tests passed in the
  first invocation, including typed-failure retention and rejection of extra
  private fields. Disposable JVM tests do not certify Minecraft shutdown timing.
  The compiled gameplay-package exclusion/CLI check also passed (1 test, 0.28 s);
  it does not establish runtime OS isolation.
- The first client used c82257b6… and native loopback startup. The server recorded
  authenticated login and join, and the bridge was created. Its identity request
  returned GAME_NOT_CONNECTED because the old identity implementation required
  saved-server metadata. The raw driver's world_joined:false means its identity
  verification did not complete; independent server records prove the actual join.
  That discrepancy is explained, not overwritten.
- First shutdown returned PROCESS_GUARD_FAILED without a retained specific cause.
  The owned PID was subsequently confirmed absent; this cannot retrospectively
  establish the guardian's timing or a successful terminal receipt. Client
  elapsed 191.719 s; input desktop unchanged. The server saved/stopped normally
  in 396.937 s, exit 0, no forced termination, complete logs. No game actions,
  worker, inference or campaign ran.

The first endpoint-repaired retries used candidate SHA-256
51d9b43b8e6bccf741697beb69ea16d83c92455e6fd8940e6e0aaf0a9f93112f.
Public native capability minor 33 and screenshots:false remain; candidate bytes
and the private identity policy distinguish this run. The original CurseForge
profile remains minor 30 / f10e7ad6… . The dedicated copy has a 4 GiB heap,
854×480 window, 30 FPS limit, muted master sound and pauseOnLostFocus:false.
That last setting is recorded engineering configuration, not physical-input
conformance or a campaign-policy waiver.

The second run (the repaired candidate) returned GAME_OBSERVATION_UNAVAILABLE
on the initial 500 ms identity request. That code can represent a transport,
deadline or decoding failure; its exact cause was not recorded and remains
unproven. Client elapsed 185.219 s; the guardian confirmed requested-stop
termination in 469 ms with input desktop unchanged. Server save/stop passed in
406.704 s, exit 0, no forced termination. This retained failure is not proof that
the endpoint repair failed or passed.

A third run keeps the same client bytes and uses the existing API's 5 s read
deadline for startup identity, with private transport diagnostics and an active
caller pumping its independent lifetime guardian. Later reads are separately
checked at 500 ms. No action/guardian/campaign limit is increased. The third run
completed the identity request and established the native body at 171.594 s.
Its subsequent capabilities request returned GAME_OBSERVATION_UNAVAILABLE after
5,015 ms, so the world checker ran zero assertions and no images were captured.
Client logs still showed recipe/book/JEI startup work. This supports a readiness
concern, not a proven diagnosis of every preceding unavailable response.
Guardian stop passed in 422 ms; client elapsed 177.922 s. Server save/stop passed
in 374.953 s.

A fourth trial adds the same-body unobstructed-render startup barrier, candidate
234c2d5689386e9f7799a3605fb84776d52e72e73f2e82cc891343a4a4c5ebae.
It completed the following checks:

| Check | Actual result |
|---|---|
| Native startup and identity | pass; ready in 186.219 s |
| Connected observations | pass; 2,745 assertions, 20 pages, 2,489 block records, no entities |
| Transport rejection cases | pass; 10 assertions |
| Ten subsequent identity reads, each with a 500 ms deadline | pass; 47–156 ms |
| World images | pass; two 854×480 PNGs, 377,992 / 377,914 bytes; capture work 86.9496 / 68.0227 ms |
| After server save/stop | pass; six disconnected/read-only assertions |
| Server | normal save/stop, 380.781 s total, exit 0, complete logs |
| Base lifetime guardian | requested-stop termination confirmed in 453 ms; no input-release or clean-checkpoint claim |
| Client and operator state | 211.484 s total; owned PID confirmed absent; active desktop unchanged; session arguments retired |

The observation assertions are structural, pagination, identity/freshness and
negative checks, not complete visibility or game-mechanics qualification.
Independent PNG CRC/zlib/scanline decoding passed; distinct colors were 6,617
and 6,714. Both images were actually inspected: grass and trees under a starry
sky, crosshair, held bow, hotbar, health/food HUD and minimap, without an open
screen or loading overlay. Structured state reports twilightforest:twilight_forest,
health 20 and food 20; the full health/food HUD is consistent with those values.
That narrow consistency observation is not the complete independent-reference
suite. No operator desktop content appears. The main-render-target capture still
excludes the OS compositor and hardware cursor.

All four servers recorded authenticated login/join and subsequently saved/stopped
normally. All four clients are absent and their temporary argument files retired.
There was no gameplay mutation, worker/host dispatch or inference. The successful
trial supports the render-readiness repair while preserving the earlier failures
and the unknown precise cause of the second unavailable read. The first failed
guardian stop remains unresolved, despite three subsequent passes.

Private evidence root:
C:\Users\Darian\.strata\evidence\2026-09-19-desktop-world-01,
with repaired runs under retry/, attempt-03/ and attempt-04/. Exact official bootstrap pins, arguments
without account substitutions, private runtime arguments, logs, saved images,
tests, source snapshots and collector are retained there; credential-bearing
arguments stay in separate protected credential directories and are retired
after confirmed process absence. Final inventory verifies source/artifact hashes,
bootstrap pins, local documentation links and tracked diff whitespace; the
machine-readable verification.json records the exact counts and remaining gates.

Next: connect bounded non-input startup to the worker-owned Forge guardian and
native action authority, then execute scoped CLI actions/cancellation and
world/menu/machine reference checks. Retain full native input/focus/pointer,
graphics-state/overhead, authentic resource and security-principal gates. A
read-only world view cannot qualify those contracts. All required M0–M6 remain
open; M7 remains conditional; no Strata inference has been dispatched.
