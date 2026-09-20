# M0 development worker

This is operator material. The worker is a manual conformance tool, with `campaign_admission=false`. It is not a campaign runner, isolated gameplay runtime, E9E-compatible backend, or G0 pass. Do not launch Codex from this checkout as a gameplay agent. Credentials, game data, grants and journals belong outside this repository.

The persistent worker owns one Mineflayer connection. `mcgame` calls use an own-avatar bearer grant over loopback HTTP; they never launch another bot. The worker validates identity, epoch, capability fingerprint, observation freshness, revisions, sequence and deadline, and persists acceptance before dispatch. The operator supervisor renews its lease every two seconds, with six-second worker expiry and a separate 2.25-second hung-worker kill threshold. Those mechanisms have not been timing-qualified against a real client or on a hung Windows process. No rendered input is used.

Worker startup now has an explicit private lifecycle: a post-import child
handshake within 2.25 seconds, guardian binding for Forge, then a separate fixed
2.25-second lane/gateway initialization limit. Genuine child event-loop pulses
maintain freshness while initializing; they do not establish avatar readiness
or extend the deadline. No public grant is written before initialization and
guardian validation succeed. Startup time consumes the overall worker wall
budget. Early child exits are journaled; receipt collection happens after stop
attempts and cannot postpone native termination. See the
[startup evidence and remaining limits](../verification/2026-09-19-worker-startup.md).

The supervisor reports `development_gateway_ready` before avatar readiness, then
`development_avatar_connected` once connected; a fresh observation is still required.
An idle transport loss also fences the epoch. A same-epoch spontaneous reconnect
cannot regain action authority. Private health distinguishes this from initial
connection startup. Bounded manual server checks use `tools/development_server.py`
with an external reviewed launch plan, verified Java hash, accepted EULA, authenticated
localhost properties, complete logs and a clean `stop` command. This utility neither
admits a campaign nor provides private console access to gameplay agents.

## Supported development surface

| Operation | Current implementation | Still required |
|---|---|---|
| Observe | Own player/inventory and window (player window 0 when no container is open), max 128 blocks/entities per page within radius 16, 64 KiB, two ordinary snapshots/sec; no NBT; opaque pages preserve capture time and region | Authentic visibility/collision/pagination conformance |
| Signals/wait | Ordered bounded player-event stream, cursor gaps, 32 events/delivery, 3 s wait, original capture age on timeout/disconnect | Authentic event freshness/load/recovery evidence |
| Move | Pinned pathfinder plans from already projected cells only; fixed level walking, no auto-dig/place/doors/sprint/parkour/equipment | General safe navigation and real-game tests |
| Look/dig | Reach and known-block preconditions; bounded cancellable operation | Actual player/server evidence |
| Equip | Select a hotbar slot or execute a fixed source/destination click sequence for main/off hand or armor; closed container and empty cursor required | Real-game acknowledgement/mechanics evidence |
| Open container | Reachable observed vanilla chest, barrel, furnace or crafting table; generic Mineflayer `openBlock` with expected window type | Other containers, machines and authentic conformance |
| Click slot | Left/right pickup and quick-move in player/crafting/furnace/generic windows; window ID/revision, native server resync, carried-stack projection and complete item-conservation checks; crafting output requires `craft` | Additional container serializers, rendered/reference parity, real server acknowledgement tests |
| Close window | Explicit `close_window` for current window ID/revision, owned cursor/grid return capacity, ordinary close, server inventory feedback and resource conservation; introduced in minor 6, current minor 7 | [Authentic vanilla player-menu smoke](../verification/2026-09-19-vanilla-menu.md) passes; external menus, merges/full inventory, cancellation and complete reference conformance remain open |
| Place | Observed support/air destination, expected held vanilla block, bounded normal placement and changed-block postcondition | Different item/block mappings, richer placement and real evidence |
| Recipes/craft | Server-unlocked recipe book only, bounded pagination; simple shaped/shapeless recipes; fixed slot routine with server resync after every click and input/output checks | NBT/remainders/custom serializers, expert recipes and real evidence |
| Use/attack/entity interaction/chat | Bounded normal inputs; use releases within its <=2 s hold; entities must have been projected and remain visible/reachable; ordinary single chat only | Real action-specific effects/server evidence; current receipts are input-only `emitted` |
| Quests | Unsupported | Tested player-accessible exact-pack projection |
| Settings/images | Unsupported, `CAPABILITY_MISSING` | Required capable settings extension and complete T05/G1 |
| Status/cancel/stop | Durable receipts, one lane, duplicate IDs return existing result, partial effects retained | Whole-system recovery and OS isolation conformance |

Cancellation conservatively closes the bot connection if an upstream operation is pending, fences further mutations and requires a new worker epoch. It never resumes an old navigation/slot action automatically. This is a partial development recovery policy, not the complete automatic reconnect contract. A terminal unknown/cancelled receipt can require resynchronization even when a public snapshot is available.

The compiled implementation files, public schemas and dependency lock are hashed into the capability manifest. Node and direct dependencies have exact pins; `package-lock.json` pins transitive packages and integrity hashes. The authentication chain pins uuid 11.1.1 through an override; the 2026-09-18 npm audit has zero findings, with CommonJS consumer and buffer-bound regression evidence. No optional auto-combat/auto-eat plugin is enabled.

Mineflayer capability minor 7 uses `exact-body-pose-motion-ground-dimension/1`:
unchanged position heartbeats do not invalidate an observation. Actual body,
position/orientation/motion/ground/dimension changes still do, independently of
inventory/window/health changes. The two-second capture-age limit still applies;
waiting while idle never refreshes an old observation. [Authentic CLI checks](../verification/2026-09-19-body-revision.md)
cover idle heartbeat acceptance and actual-turn/age rejection. Full host and
movement-state conformance remain open.

## Local verification and schema generation

Use the root README commands. Python is managed by uv; if an interrupted initial uv installation leaves the minor-version alias unavailable, supply `uv sync --python <absolute-path-to-the-installed-3.12.14-python.exe> --frozen`. No system Python replacement is needed.

After contract edits:

```powershell
uv run --frozen python tools/export_schemas.py
npm run generate --prefix backends/mineflayer
npm test --prefix backends/mineflayer
```

All thirteen canonical records now have Python models and separately deployed JSON schemas/TypeScript bindings, plus the local request envelope. Full T01 remains open, including complete cross-record references and integration. The worker consumes only its public game schemas; operator/evaluator bindings remain outside its source tree. Gateway semantic checks supplement JSON Schema.

## Authorized manual game validation

First obtain the exact official installation/acquisition evidence and an authenticated Java Edition identity, with terms acceptance completed by the operator. This implementation does not install Minecraft, change server configuration, accept terms, acquire accounts or start servers. Run `mcbench conformance preflight --target vanilla` and retain unresolved conditions. E9E preflight includes all ten compact cases and remains blocked; selecting E9E in the development worker is rejected.

Prepare a dedicated external state directory, protected Microsoft auth cache and operator-only configuration file. The operator initializer below creates/checks a dedicated cache, rejects the repository, and binds one opaque account label to a verified Java profile. The Windows helper uses the pinned operator Python 3.12.14 in the repository's `.venv`; it creates a protected directory with native ACL APIs and verifies owner/current-user+SYSTEM grants on every child. It does not change Windows or PowerShell security policy. POSIX mode/owner checks are separate. These permissions do not isolate processes running as the same operator. Actual adversarial gameplay isolation remains an independent gate.

Create the parent directory outside this checkout, then run:

```powershell
node backends/mineflayer/dist/src/operator_auth.js --cache D:/strata-private/account-cache --account avatar-1 --prepare-only
node backends/mineflayer/dist/src/operator_auth.js --cache D:/strata-private/account-cache --account avatar-1 --timeout-ms 300000
```

The second command requests Microsoft device sign-in and prints only a private `operator-login.json` path. The operator opens its HTTPS URL and enters its user code manually. It never sends a password to Strata. Raw provider errors, refresh tokens, device tokens and the actual profile identity are absent from command output. `operator-result.json` and credentials remain in the protected directory. The initializer starts no server, Minecraft connection or model. A hard timeout exits the dedicated process because upstream polling has no complete cancellation API. A leftover `auth.lock` intentionally blocks retries; verify the recorded process has exited before manually removing that lock. Never remove a lock for a live initializer/worker.

The worker uses the exact same provider/cache policy, rejects device-code requests, checks the bound account and signed-chat certificate, and prevents authentication from connecting after a control fence. Corrupt caches, hardlinks, reparse paths, changed account identity and weakened ACLs fail closed. Atomic cache writes never fall back to the dependency/source directory. Use the same opaque account label in the worker's `username` field.

For a separately authorized native Forge startup, `authenticateAccount` accepts an optional final `minimumLifetimeMs` argument (0–3,600,000; default 0). A positive minimum suppresses only a near-expiry Minecraft token from the provider's cache view and rechecks the returned expiry. Account/profile/certificate checks still apply. Keep an expiry-only operator receipt and recheck it immediately before launching: server preparation can consume the remaining lifetime. `sessionExpiresAt` reads a JWT claim to restrict reuse; it does not authenticate that claim. Unknown expiry or a short returned lifetime rejects. See the [authentic expired-session finding](../verification/2026-09-19-desktop-worker.md); do not confuse this startup check with full credential recovery or isolation qualification.

The native Forge candidate also gates initial connected readiness on current-listener
tag and recipe synchronization, a later unobstructed world frame and a matching
admission tick. A title-screen bridge can exist before this; its connected identity
and observations reject `GAME_INITIAL_SYNC_PENDING` until the body qualifies.
Do not arm based on TCP join, descriptor creation or an early frame alone. Ordinary
menus preserve qualification after admission; disconnect resets it. See the
[readiness implementation and evidence](../verification/2026-09-19-forge-readiness.md).
No operator runner may extend action/guardian deadlines to hide startup latency.

The illustrative configuration below is not an acquisition receipt or authorization:

```json
{
  "schema": "strata/DevelopmentWorker/1",
  "purpose": "manual-conformance",
  "server_kind": "vanilla",
  "host": "127.0.0.1",
  "port": 25565,
  "username": "operator-selected-account",
  "auth_cache": "D:/strata-private/account-cache",
  "state_directory": "D:/strata-private/manual-worker",
  "campaign_id": "development-1",
  "agent_id": "avatar-1",
  "epoch": 1,
  "lease_id": "operator-issued-unique-lease",
  "max_wall_ms": 300000,
  "primitive_limit": 10000
}
```

These are per-development-worker bounds, not campaign/team/model budgets. Initialize account authentication through an authorized operator procedure first; the worker does not forward device login codes to agents. Missing auth cannot be treated as a successful connection.

```powershell
npm run build --prefix backends/mineflayer
node backends/mineflayer/dist/src/worker.js D:/strata-private/development-worker.json
```

The supervisor reports a private grant-file path. Give the isolated client identity access only to its own grant, never the enclosing operator state/auth directory. A protected copy may be used at the client boundary. Process/filesystem/network/credential isolation has not yet been implemented or certified; do not run model-generated code under the operator identity. `mcbench package-gameplay <repository> <new-destination>` produces a standalone allowlisted CLI/skill bundle after compilation. This packaging is not an isolation certificate.

In a second operator terminal, set `STRATA_GAME_GRANT` to that file path, then:

```powershell
node backends/mineflayer/dist/src/cli.js capabilities --json
node backends/mineflayer/dist/src/cli.js observe --json
node backends/mineflayer/dist/src/cli.js observe --cursor <next_cursor> --json
node backends/mineflayer/dist/src/cli.js recipes --after 0 --json
node backends/mineflayer/dist/src/cli.js wait-events --after 0 --json
node backends/mineflayer/dist/src/cli.js look-at --x 1 --y 64 --z 0 --json
node backends/mineflayer/dist/src/cli.js action-status --request-id <returned-action-id> --json
node backends/mineflayer/dist/src/cli.js stop-all --json
```

`move-to` uses the same coordinate flags and an optional `--timeout-ms`. Wrappers take a fresh scoped observation and never retry a stale or timed-out mutation. `act --json` reads a complete ActionBatch from stdin. Keep its ID and query status after any transport uncertainty. Exit codes: 0 successful read/terminal completion, 2 accepted/executing, 3 gameplay/action failure or uncertain/cancelled result, 4 transport/preflight rejection. JSON status is authoritative. Wrapper action IDs also go to stderr so a missing HTTP response does not lose the identifier.

Recipe pages include only server-unlocked IDs; unsupported entries are labeled.
Spatial pages retain the original state revision and capture time. Cursors expire
after 30 seconds or eviction from the four-region cache; `STALE_OBSERVATION` requires
a new observation. A new page never refreshes hidden state or expands its region.
Only projected pages enter the bounded planning cache; a page older than two seconds
cannot authorize an action. Take a fresh observation before acting on old knowledge.
`craft.count` requests that many executions of one recipe, without acquiring or
crafting its ingredients. The selected current window must have an empty grid,
empty cursor and free output destination. Every slot click and server-resync
emission consumes the primitive allowance. A partial craft can leave real changes;
uncertain results fence the worker rather than retrying the recipe.

`use_item`, `attack`, `interact_entity` and `chat` currently return `emitted`: input
was sent and a result observation is attached, but no gameplay effect is asserted.
Never replay these requests automatically. The CLI returns exit 0 for this known
input delivery; inspect JSON status rather than treating the exit code as game success.
Chat is at most 256 UTF-16 units to avoid the pinned client's implicit splitting;
Unicode is allowed. Commands and control/newline characters reject before emission.
Entity actions recheck the observed identity, reach and LOS after turning. Held-use
release remains charged during cancellation; insufficient ordinary budget cannot
prevent the local safety release. Full authoritative effect tests remain required.

## Recovery and evidence

The private SQLite journal uses WAL and `synchronous=FULL`. It retains complete accepted envelopes, acknowledgement transitions, delivered observations, ordered public signals and charged primitive intents/ticks. An exclusive executor lock prevents a second worker from owning the same directory. A new launch requires a strictly increasing epoch and a fresh lease/grant. Unresolved old requests become `unknown`; their costs are retained. Old IDs never redispatch. Public signal cursors continue across restart; missing in-memory history is explicitly a gap.

After an abnormal stop, the lock is intentionally left in place. The operator must establish that the old supervisor and bot are terminated, fence their network/account access, preserve evidence, and then remove only that instance's executor lock before starting a higher epoch. Never remove a live executor lock. Journal corruption or a disk error is not repaired by dropping rows. Full snapshot/resume, controller ownership, retained wall/tick budgets, report reconstruction, and 1/8/24-hour reliability remain M2 work.

`mcbench doctor` fingerprints the installed CLI and inspects `exec --help` only. `mcbench inspect-events <private-jsonl>` totals documented turn usage with cursor deduplication; model-call counts, nested coverage and prices remain unknown. Neither command loads Dovetail, starts inference, verifies helper boundaries, or permits a paid campaign. App-server and MCP remain optional future adapters.
