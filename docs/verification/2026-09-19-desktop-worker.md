# Separate-desktop Forge worker integration — September 19, 2026

Operator-only. Private logs, game/account identities, tokens, native/public grants,
saved player data and images remain outside gameplay workspaces and the public
repository. Scope: M0.3b.2c.3c.2b.2b and M0.2g.1; partial F01/F06/F09/F16,
N01/N02/N03/N04/N05/N06/N08; C02/C09/C15/C18; T01/T03/T06/T07/T12/T13.
No milestone or aggregate release gate passes here.

The operator integration runner composes the existing
[desktop launcher](../../src/mcbench/desktop_process.py),
[worker](../../backends/mineflayer/src/worker.ts) and
[Forge guardian](../../src/mcbench/forge_guard.py). Startup stays fenced under
the desktop's bounded lifetime and kill-on-close job. Once native identity and
authority are available, the worker owns the single independent Forge guardian
and only then arms its scoped action lane. It does not attach a competing base
guardian. Planned checks use the public CLI, with no native/admin mutation token,
OS input, desktop switch or model inference.

## First attempt: session expired before client launch

Private root: `C:\Users\Darian\.strata\evidence\2026-09-19-forge-worker-live-01`.
Exact profile: official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23, Java
17.0.20.1, Node 24.19.0, Python 3.12.14. The dedicated copy retains client JAR
234c2d5689386e9f7799a3605fb84776d52e72e73f2e82cc891343a4a4c5ebae,
97 bootstrap pins, 4 GiB heap, 854×480 window, 30 FPS limit, muted sound and
pauseOnLostFocus:false. The original CurseForge profile is unchanged.

The server started normally, but the client disconnected before authenticated
login and never created its connected bridge. The runner reached its 280-second
startup deadline and stopped the owned client. Total client/check time was
284.516 seconds; server saved/stopped normally in 405.563 seconds, exit 0, complete
logs. The input desktop stayed unchanged. There were no worker, action or image
checks in this attempt and no inference.

The token had only 88.480 seconds remaining when arguments were prepared. Server
startup consumed that interval; it had already expired 50.928 seconds before the
client launched. The client logged profile-key retrieval failures; a subsequent
authenticated profile GET returned HTTP 401. The earlier successful world run
had no such profile-key errors. Expiry is directly established; the generic
client exception alone would not establish the cause. The failed attempt remains
archived and cannot count as a guardian/action pass.

## Lifetime repair and verification

[session_lifetime.ts](../../backends/mineflayer/src/session_lifetime.ts) implements
an optional 0–3,600,000 ms minimum-lifetime policy in the trusted
[authentication seam](../../backends/mineflayer/src/authentication.ts). A positive
minimum filters a near-expiry Minecraft token from the provider's cache read,
without resetting or deleting Microsoft/Xbox credentials. The pinned provider
then uses its ordinary refresh flow. Returned expiry is rechecked after provider
work and before account binding. Malformed/unknown expiry and an insufficient new
lifetime fail closed. Decoding an expiry claim does not authenticate a signature
or replace existing profile, account and certificate checks. The default vanilla
path remains unchanged. Native startup callers must also recheck the remaining
lifetime immediately before launch; the low-level desktop launcher has no
credential authority.

Actual checks before and after this repair:

- `npm test` before the repair: 136 tests, 111 pass, 25 explicitly skipped,
  zero failures, 5.577 seconds. With the pinned JVM/Python fixtures enabled,
  `node --test dist/tests/forge.test.js`: all 37 pass, no skips/failures,
  64.343 seconds. Twelve overlap the earlier suite; counts are not additive.
  These are synthetic contracts/process fixtures, not real Minecraft timing.
- `npm run build` after the repair passed. The targeted compiled
  authentication, authentication-dependency and session-lifetime tests passed:
  14 tests, no skips/failures, 5.670 seconds. Cases include malformed/expired/near
  expiry, provider-return recheck before binding, account mismatch, cancellation,
  certificate decoding and the real pinned token manager's refresh decision.
  No live credentials are used by these tests.

## Fresh-session retry: joined, first API read unavailable

`retry-01/` retained 86,206,333 ms of session lifetime at client launch.
The server recorded authenticated login and join, with no profile-key retrieval
error in the client log. The first 5-second identity read returned
GAME_OBSERVATION_UNAVAILABLE before a worker could start. Its transport-level
cause was not retained and cannot be assigned conclusively. The private driver's
world_joined:false means its verification did not finish; it does not override
the server's actual join record.

Client/check elapsed 209.953 seconds; the outer owned job stopped the client,
and the server saved/stopped normally in 386.000 seconds. Input desktop unchanged;
session arguments retired after process absence. One native journal profile frame
exists, with no arm/action/guardian event. The telemetry spool has 200 complete
records. This resolves the expired-login symptom for this run, not native API
readiness or the full credential recovery gate.

## Diagnostic retry: client-thread work prevents completion

`retry-02/` retained 85,619,670 ms of session lifetime at launch. It kept the
same client/broker bytes as retry-01 and used new scope/authority/private grants.
Six bounded read-only identity probes each failed after 5 seconds. All 456
recorded HTTP exchanges (six POSTs and 450 GETs) returned valid `accepted`
responses; none completed. HTTP transport remained responsive while the
client-thread jobs were pending. No mutation was repeated or dispatched.

One explicitly recorded, bounded `jstack` attachment ran after the first failed
read, before any worker or action lane was armed. At that instant, the render
thread was RUNNABLE inside `Shapes`/`SupportType`/`BlockBehaviour` cache building,
called through `Blocks` and `ClientPacketListener` while handling
`ClientboundUpdateTagsPacket`. HTTP executor threads were idle/waiting for work.
This demonstrates client-thread tag/block-cache initialization during the sampled
failure. One stack sample does not prove that the same method occupied the full
30-second probe interval. The earlier retry's exact unavailable cause remains
unproven; this evidence must not be retroactively substituted for it.

Client/check time was 262.000 seconds; server saved/stopped normally in
444.078 seconds, exit 0 and complete logs. There was one native journal profile
frame, no arm/action/guardian event, and no game-image capture. Input desktop
unchanged; client absence confirmed and temporary session arguments retired.
The telemetry inspector validates 249 records and approximately 19.76 sampled
server TPS. All three worker-trial server boots retain the six expert furnace
recipe assertions; these do not verify player crafting or modded mechanisms.

All three clients/servers are stopped. Collectors retain bootstrap hashes, native
journal framing, protected directories, source snapshots and, for retries, all
33 compiled broker modules. A zero-entry guardian stream is `not_run`, not a
successful chain check. The first collector invocation lacked the evaluator
import path; the corrected operator-only invocation succeeded. No game check
was rerun to repair that collection issue.

Next: source-audit initial tag/recipe synchronization and gate native startup
readiness on the completed same-connection initialization plus an unobstructed
render. The existing first-render barrier alone permits a bridge to be published
before subsequent client-thread initialization finishes. Keep real action and
guardian limits unchanged, then repeat the bounded scoped worker test. The
readiness repair is not implemented by this change.

Subsequent work is tracked in [initial synchronization readiness](2026-09-19-forge-readiness.md).
It preserves these three failed attempts and introduces a separately hashed
candidate; later evidence must not be attributed to this earlier client build.

All 19 advertised actions, expert recipes/machines, GUI/keybinding parity, native
host/helpers, isolation, full accounting, soaks, simultaneous capacity and research
gates remain open. A successful bounded subset will not qualify the whole backend.
