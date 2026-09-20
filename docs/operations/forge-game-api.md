# Structured Forge client development API

Operator-only. This document is excluded from gameplay instructions and retrieval.

The operator's shared desktop must remain usable. Routine gameplay verification
uses the scoped API, observed state and independent server evidence; desktop
clicks are not a per-action success check. Native menu/keybinding parity is a
separate qualification task. Long graphical/input tests need an isolated
graphical session; brief shared-desktop checks require an arranged window.
Current gameplay capabilities advertise screenshots:false. The optional private
frame diagnostic below is separate from that public contract; complete
unattended gameplay remains unqualified. These gaps do not permit taking desktop
input or inferring native success from the bridge's own response.

The [non-input-desktop foundation](../verification/2026-09-19-desktop-launch.md)
now has disposable process/tree/owner-crash evidence and a successful hidden
OpenGL 3.2 pixel probe. It never switches the active desktop. This is a launch
primitive and graphics prerequisite, not a qualified unattended Minecraft path
or a credential/process/network sandbox. [Guarded E9E startup](../verification/2026-09-19-desktop-client.md)
now passes in a dedicated private copy: title-screen bridge, twenty read-only
checks and confirmed process termination, with input desktop unchanged. This
uses direct JVM bootstrap from the installed official version metadata/artifacts;
it does not automate the launcher UI. Subsequent checks establish narrow
world-frame, scoped-action and saved-server evidence; see the
[current handoff](../STATUS_AND_HANDOFF.md). Full world/input behavior, reliable
guardian shutdown and production isolation remain required.

### Private operator frame requests

Start only an authorized dedicated client with `-Dstrata.privateFrameDirectory`
pointing to a new protected directory outside and disjoint from its game profile.
No frame request or output belongs in gameplay workspaces, tools or artifacts.
The separate optional `strata.private-frame.mixins.json` hook targets exact
Minecraft 1.19.2 SRG runTick/Window.updateDisplay. If absent/broken, no session
evidence appears; that is a failed prerequisite, not a capture pass.

`session.json` declares `strata/PrivateFrameSession/1`, session/source-clock IDs,
client JAR hash, policy `private-main-target-pre-display-png4/1`, and limits. The
operator may atomically publish `request-N.json`, for consecutive N=1..4:

```json
{"schema":"strata/PrivateFrameRequest/1","session_id":"<actual session UUID>","sequence":1,"expires_unix_ms":0,"expected_screen":"shadows.packmenu.ExtendedMenuScreen"}
```

The example's zero expiry is deliberately non-executable. Supply a real future
UTC deadline within ten seconds and an exact expected screen class (empty string
for no open screen). E9E's pinned PackMenu title is ExtendedMenuScreen, not an
exact vanilla TitleScreen class. Discovery of a subclass is not permission to
remove screen matching. Requests and records are fixed filenames; caller paths,
coordinates, keys or screen changes are never accepted.

At the pre-display hook, an accepted request writes `intent-N.json`, then reads
the main render target using native Screenshot.takeScreenshot, restores texture
binding/pack alignment and writes `frame-N.png` plus `frame-N.json`. Each PNG is
bounded to 1920×1080/12 MiB, four per ten-minute session, at least one second apart.
Receipt includes frame/clock/context, dimensions, PNG hash and capture elapsed
time. This is main-target imagery before display swap, excluding OS/compositor/
hardware cursor or drawing outside that target. It is not a physical F2 test.

Unsafe paths, wrong session/sequence/screen, expired or malformed requests,
disabled rendering, incompatible GL pack/texture state, excessive images or
storage failure stop the capture session. `failure.json` contains a fixed reason;
partial PNG/intent files remain unqualified. Correcting a failed request cannot
restart capture. Use a fresh authorized process/directory after diagnosis.
No camera, UI, input or world action is performed. Game API lifetime and guardian
continue separately; the operator must check missing/failed evidence and stop
its test. Complete physical-input, native reference and isolation gates remain.

### Structured gameplay observations and actions

The candidate is Forge minor 34. An exact non-consuming single-item task can now
open its ordinary JEI recipe screen through `quest_task/open`, using the same
current task-page selection and book generation/revision envelope described below.
Five exact FTB/XMod/JEI artifacts and the common current runtime/helper identity
are required; unavailable, changed or hidden ingredients reject. The callback must
produce the actual distinct RecipesGui, not just return normally.

Afterward `quest-screen --json` reports `kind:task_recipes`. Its chapter/quest IDs
refer to the originating quest. It exposes no current JEI focus or recipe-page
contents. To return, submit `quest_navigate` with `operation:close`, `selection:null`
and that fresh screen's source/generation/revision, within the full ActionBatch.
The ordinary close callback must restore the same parent book and selected quest.
`quest_navigate/back` is unsupported here; recipe history instead uses
the separate `recipe_navigate/history_back` route below.
`quest-menu`, chapter/quest navigation and manually opened/unbound recipe screens
also reject. Complete page content and authentic
native/reference qualification remain required. Task policy is
`ftb-visible-item-task-menu-or-jei-open/2`, screen policy
`ftb-own-team-book-and-task-recipes-state/2`; see
[lifecycle evidence](../verification/2026-09-19-quest-jei-lifecycle.md).

While the confirmed task recipe screen is open, `mcgame recipe-page --json`
(`recipes.page`, privately `recipe_page`) returns copied slot draw operands. It
takes no selectors. The response explicitly says `coverage:slot_header_control_draw_operands`
and `complete:false`; it is not a full page or focused recipe query. Origin IDs,
source/screen generations and screen revision accompany a canonical content hash.
Two ordered headers (category, page) contain kind, state and nullable text. Text
comes from actual draw operands; clipped/unsupported markers contain null text.
The category title may already be truncated by JEI. Do not interpret origin IDs as
recipe focus or the page label as a raw graph count. Labels are bounded to 1,024
Unicode code points / 4,096 UTF-8 bytes and included in the content digest.
Four ordered controls (`category_next`, `category_previous`, `page_next`,
`page_previous`) expose only kind and state (`enabled`, `disabled`, `clipped`).
They copy actual button draw operands in the same complete frame and participate
in the digest. Viewport filtering precedes reading flags; widget identity and
geometry remain private. No navigation input is authorized by this observation.
Policy is jei-task-drawn-slot-header-controls-empty-loop/4, native NativeRecipePage/4.
Each layout has a category ID, clipped flag and native-indexed slot rows containing
empty/unsupported markers or plain item/fluid ID and amount. No raw components,
source objects or private body metadata reach the scoped command.

Bounds are 32 layouts, 128 slots each and 32 KiB for the public response. Missing
hooks, source/screen changes, expired native frames, malformed data, digest mismatch
or overflow reject. The native 250-ms age limit applies at the native read, not
final network delivery. The broker checks its lease/deadline/fence and bound body
again after transport; stopping prevents late delivery. Stock Mineflayer rejects
this capability. Rich/custom content, page/history controls, actual hook loading,
final overlay visibility and full native/reference/clock/overhead/isolation parity
remain unverified. Header observation additionally requires the complete native
category/page/helper lifecycle, ordinary identity pose, known font and clipped
geometry. See [transport evidence](../verification/2026-09-19-jei-page-transport.md)
and [header evidence](../verification/2026-09-19-jei-page-headers.md), followed by
[control observation evidence](../verification/2026-09-19-jei-page-controls.md).

An empty `layouts` array is valid only after the native draw loop's observed
terminal false predicate, normal return and complete same-frame headers/controls.
Every true predicate must match one completed layout draw; missing or interrupted
hooks reject instead of fabricating an empty page. The hook observes existing
iterator calls without extra traversal, list inspection or public iterator data.
Native age, source, digest and body checks apply equally to empty pages. See
[empty-loop evidence](../verification/2026-09-19-jei-empty-page.md).

The [input provenance foundation](../verification/2026-09-19-jei-input-provenance.md)
is now connected to the [bounded navigation motor](../verification/2026-09-19-jei-navigation-motor.md).
The candidate has title-screen evidence in a dedicated private client copy;
authentic input/cancellation remains unverified.
Submit `recipe_navigate` inside `mcgame act --json` with `source:jei`, one enabled
`control` from the four rows, and the page's `source_generation`,
`expected_screen_generation`, `expected_screen_revision`, `expected_page_revision`.
The expected fields take the page's screen generation, screen revision and
canonical revision respectively. Coordinates, widget IDs and arbitrary keys are
not accepted. Read a fresh page before constructing the request.

Policy `jei-current-page-controls-history-fresh-frame200/2` checks current page and
native button geometry before both ordinary input phases. Mouse-down previews;
mouse-up on a later tick executes only with the intended router/button witness.
Then it waits at most 200 charged ticks for a new complete frame, within the
ten-second action deadline and tighter lease/budget bounds. Completion is input
`emitted`, including an ordinary no-op, not a claim of recipe progress. Query
`recipe-page` again for the resulting contents. Cancellation clears pending input
through the public router reset; it never executes the pending release click.
Unknown effects or failed cleanup fence further input and retain all costs.

For ordinary recipe-history Back, use the same envelope and fresh page selectors
with `control:history_back`. It invokes the pinned concrete `RecipesGui.back()`
public callback once; it does not press a key or read the private history stack.
This callback is not part of the public `IRecipesGui` interface. Empty history
keeps the screen open. A fresh complete frame is still required, even for a no-op.
Admission reserves three primitive units for callback, frame check and safety
release; additional waiting ticks charge. Page/category actions still reserve
four. No pending owned mouse gesture may coexist with Back. Physical Back-key
and native history/render behavior require separate authentic qualification.
See [history evidence](../verification/2026-09-19-jei-history.md).

Choice opening uses `quest_reward/open` under
`ftb-visible-choice-reward-menu-open/1`. Display the parent quest,
read `quest-screen`, and select an eligible `can_claim` entry from
`quest-components --chapter ID --quest ID --part rewards --after 0 --json`.
The full `act` envelope uses the current book's source/screen generation and
revision plus `selection:{query,revision,entry_id}` from that rewards page.
Only an enabled clipped exact choice-reward button is supported; this opens its
ordinary menu and performs no claim. Other reward callbacks reject.

Then `quest-menu --after 0 --json` can return `menu_kind:reward_choices`, with
`context:{chapter_id,quest_id,reward_id,title}`, empty `controls`, and visible rows
`{index,title,enabled,tooltip}`. Indices are ordinals of the projected visible rows,
not raw table indices or permission to claim. The source retains parent identity
from the qualified opening; manually opened/unbound choice screens reject.
Screen/source changes expire that binding, and current eligibility is rechecked.
Policy `ftb-current-item-choice-clipped-pages32/4` retains the separate choice
shape introduced by `/3` and includes wheel-sensitive state in its revision.
Claims, other extensions and all authentic UI/server/reference checks remain open.
See [choice evidence](../verification/2026-09-19-quest-choice.md).

The current candidate supports [item and opening-bound choice Back/scroll](../verification/2026-09-19-quest-choice-controls.md)
under `ftb-current-item-choice-menu-back-wheel/2`, superseding item-only `/1`. Read
`mcgame quest-menu --after 0 --json`, then include this action in a full fresh
`mcgame act` envelope, copying the actual source/menu generation and revision:

```json
{"kind":"quest_menu","operation":"scroll","direction":"down","source":"ftb_quests","source_generation":1,"expected_menu_generation":1,"expected_menu_revision":1}
```

Those identity numbers are illustrative. Use `up` for the opposite wheel step,
or `operation:back` with `direction:null`. Item menus require a visible enabled
Back button; choice menus invoke the ordinary Backspace/onBack callback and still
report empty `controls` because they have no visible Back button.
There is no arbitrary scroll amount, submission or choice selector. Each scroll
is one native step with normal clamping, including boundary no-ops. Temporary
logical hover targets the clipped panel and is restored; wheel dispatch does not
move the OS pointer. Ordinary Back may restore it through FTB's native callback.
Back confirms return to the same parent book and quest. Require an exact supported
menu, released modifiers, ungrabbed mouse, idle survival player and empty carried/
crafting/result state. Choice actions also reject held physical mouse buttons.
Changed source/menu/parent/reward/layout and a scrollable outer menu reject.
The item route rejects attached scrollbars; the choice route requires its exact
vertical scrollbar and confirms both value and panel offset, including native
negative-maximum behavior when content fits. Refresh the observed menu
revision after a gesture; do not replay an uncertain request. Authentic UI and
resource conformance remain unverified. Other extension menu routes remain open.

The current candidate also accepts `quest_task/open` in a full `mcgame act`
envelope. First display the quest through `quest_navigate`, read `quest-screen`,
then read `quest-components --chapter ID --quest ID --part tasks --after 0 --json`.
Copy that page's `{query,revision,entry_id}` into `selection`, and use the book's
source/screen generation and revision. Only an actually visible, enabled exact
item-task button can open its ordinary bounded item-alternatives menu or the
single-item JEI candidate route described above. Other task callbacks and empty
display lists currently reject. This does not submit items or claim rewards.
The [initial task-opening evidence](../verification/2026-09-19-quest-task-open.md)
records the superseded item-only policy `/1`; both routes remain unqualified.

The current book lifecycle is available through `mcgame quest-screen --json`
and full `mcgame act` envelopes. `quest-screen` takes no selector and returns
closed/book/task-recipes kind, visible selected or originating chapter/quest IDs, source/screen generations
and revision. It rejects unknown GUI contexts rather than labeling them closed.

For `quest_navigate`, set `operation` to `chapter`, `quest`, `back` or `close`;
copy `source_generation`, `expected_screen_generation` and
`expected_screen_revision` from that current screen response, with
`source:ftb_quests`. The required `selection` is null for Back/Close. For a
chapter/quest, supply `{query,revision,entry_id}` from a permitted catalog page;
a chapter selection uses the root query and a quest selection uses its chapter.
The exact selected entry must still be visible, and a quest's details accessible.
Refresh the selection's catalog query after reading a different chapter or the
root catalog: changing that focus invalidates the previous catalog revision.
For example, after inspecting a chapter's quests, read the root page again before
selecting a chapter. Recheck that the intended entry remains in the refreshed
page, then construct the action; do not reuse or automatically retry a stale batch.
Back leaves details first and closes from overview; Close returns to gameplay.
Selecting the current chapter preserves native behavior, including a possible no-op.

The initial context supports the exact non-editing book opened from gameplay,
with no previous screen, context menu, active drag/selection or hidden details
panel. Opening/navigation require idle inputs, no server container and empty
carried/crafting/result slots: FTB close calls Minecraft's container close.
Other task/menu routes, prior-screen contexts, occupied crafting state and
scrolling remain required follow-up work. `emitted` confirms local UI state only;
neither GUI rendering parity nor server/resource success is established.
See [navigation evidence](../verification/2026-09-19-quest-navigation.md) for
policy `ftb-own-team-book-state-navigation/1`, Forge minor 22 and remaining gates.

The Forge candidate can open the ordinary own-team quest book through `mcgame act`
with this action inside the existing full `ActionBatch` envelope:

```json
{"kind":"quest_ui","operation":"open","source":"ftb_quests","source_generation":1,"expected_catalog_revision":1}
```

The numbers above are illustrative. First query `mcgame quests --after 0 --json`
without a chapter selector, then use its actual `source_generation` and `revision`.
Obtain a fresh ordinary observation and current lease/control/capability values
for the batch. A stale catalog or any open GUI rejects before dispatch. The exact
FTB source must allow opening: own team, no editing, quests enabled and team unlocked.
Inputs/modifiers and hands must be idle, with no server container or carried stack.
An `emitted` receipt confirms the local opening only. Cancellation preserves an
already opened screen, charges and journal; an uncertain result requires explicit
resynchronization and must not be blindly replayed. Opening is separate from the
`quest_navigate` and `quest_task` actions above; submissions and claims remain required.
Policy `ftb-own-team-open-screen-cas/1` was introduced in Forge minor 21 and remains **unqualified**;
[opening evidence](../verification/2026-09-19-quest-open.md) distinguishes synthetic
motor/transport tests from pending loaded-pack behavior. Stock Mineflayer rejects it.

Current-menu item alternatives are available in the unqualified candidate:

```text
mcgame quest-menu --after 0 --json
```

The exact FTB item-alternatives screen must already be open. This operation does
not open a menu, scroll it, navigate recipes or submit items. It returns only
items intersecting the current clipped viewport, normal tooltips and visible
Back/Submit control state. The native item list also contains off-screen items;
their stack/name/tooltip readers are not called. Release Shift/Control/Alt and
disable advanced item tooltips for this declared normal-tooltip policy.

`quest_menu` uses `ftb-current-item-choice-clipped-pages32/3`. Version 2 introduced wheel-sensitive item-layout revisions; version 3 adds the distinct choice response above. Its query has
only `source:ftb_quests` and `after`; no arbitrary task, team or screen selector.
Results carry context, source/menu generations, revision, visible entries,
controls and next cursor. Preserve revision across pages and restart pagination
after a screen/layout/content change. An enabled control is the UI's display
state and grants no input authority. Unknown screens/layouts and context menus
reject explicitly. Limits and remaining authentic qualification are in the
[item-menu report](../verification/2026-09-19-quest-item-menu.md).

The normal Strata gameplay path is the scoped `mcgame` API and Mineflayer worker.
Exact E9E rejected that worker's vanilla-style login. Decision D06 selects the
fallback already allowed by SPEC 8.1/16.1: a separate `forge_client` backend inside
the authentic Java client, whose loaded Forge/mod implementations perform their
own channel negotiation and registry synchronization. Desktop input is not this
API's transport. A successful Forge client launch does not prove its game API.

Candidate identity: `forge1192-structured-development/1`, MC 1.19.2, Forge 43.4.23,
Java 17. This profile is **unqualified and cannot admit campaigns**. It currently
defaults to authenticated read-only `capabilities`, `identity`, `observe`, `observe_bound`, `recipes`, `recipe_query`, `quests`, `quest_text`, `quest_components`, `quest_menu` and `quest_screen`.
An explicit private authority additionally enables a durable development action
lane for look, dig, block interaction, inventory clicks, item use, entity attack/
interaction, chat, placement, equipment, bounded level walking, single-recipe crafting
and explicit menu close, plus ordinary quest-book opening and navigation. Connection management,
settings, raw packets/eval and administration remain unsupported.
The separate settings endpoint retains
its own schema, token, session and qualification.

The [September 19 authentic connected check](../verification/2026-09-19-forge-connected.md)
joined exact E9E and exercised private read-only pages, quest content and Thermal
recipe discovery. It did not arm a worker or qualify ordinary actions/render hooks.
The server saved and stopped normally; the client remains read-only.

## Build and explicit activation

Use the pinned build in `java/` with the compiler/artifact checks enabled:

```powershell
$env:STRATA_FTB_LIBRARY_JAR = 'C:\path\to\official-E9E\mods\ftb-library-forge-1902.4.1-build.236.jar'
.\gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
```

Set `STRATA_FTB_LIBRARY_JAR` (or Gradle property `strataFtbLibraryJar`) to the
already acquired official Library artifact. The build checks SHA-256
`1ba0d7fa626ddb2e3c31e77e20b573ca79eb92e7667cca5b9a3e985fc22d1592` before
compilation. Missing input reports `FTB_LIBRARY_API_REQUIRED`; different bytes
report `FTB_LIBRARY_API_HASH_MISMATCH`. The public `TooltipList` extension API is
compile-only; no FTB classes are bundled in the candidate. This explicit local
artifact input records the exact-version Maven endpoint's 403 limitation without
substituting another library. Java settings builds use the same client module
and prerequisite. Keep the artifact outside the repository and agent workspace.

After authorized deployment into a dedicated exact-pack client, set JVM property
`strata.gameBridgeDirectory` to a preexisting absolute operator-private directory
outside the game profile. The extension initializes at the title screen, binds
only `127.0.0.1` on an ephemeral port, and creates `game-connection-<uuid>.json`.
That file contains a bearer credential: never return it to a gameplay agent or
include it in evidence. The host must establish actual filesystem/process/network
isolation; loopback binding alone is not a same-user security boundary.

Building does not install or launch the JAR. Deployment into a dedicated profile
is a separate operator step. No connection or game action is automatically initiated.

The operator client reads the descriptor without printing its credential:

```powershell
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json capabilities
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json observe
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json observe --cursor OPAQUE_CURSOR
```

`identity` returns a private hash binding the actual server address and player
UUID, plus a client connection generation. It does not return those raw identifiers.
It requires an already connected client; automatic connection is not implemented.

These native operations remain private operator/broker commands. The scoped worker
now has an explicitly selected Forge route using the same public `mcgame` commands;
it does not expose native authority or credentials to gameplay. See below.

## Wire and observation contract

`POST /v1/game` queues `strata/NativeGameRequest/1` with exact fields `schema`,
`request_id`, `session_id`, `deadline_unix_ms`, `operation`, `args`. An observation
has `args={"cursor":null}` or a previously returned opaque cursor; capabilities
has `args={}`. Use `GET /v1/game/<request_id>` to poll the existing request.
Session mismatch, expired deadlines, duplicate-ID changes and unknown fields
reject. HTTP transport is shared with settings: strict duplicate-key parsing,
32 KiB request and 512 KiB response ceilings, eight normal pending requests,
two reserved urgent cancellation/stop requests, 64 cached
receipts, fixed Host/auth checks, Origin rejection and bounded HTTP workers.
Shared transport faults retain their existing `SETTINGS_*` codes; game-specific
validation faults use `GAME_*`. One operation drains per client tick, with urgent
work before normal work and before the motor, on the owning client thread at tick
START, before Minecraft polls ordinary held inputs.
No HTTP thread accesses Minecraft objects. Accepted inputs wait an additional
tick before dispatch, leaving a cancellation opportunity after durable acceptance.

`NativeGameSnapshot/1.state` uses the existing public `StructuredState` shape.
IDs come from actual registered Minecraft/Forge objects. Inventory slots use
the player inventory-menu indexes (46 slots). Containers currently require an
exact supported native class: player inventory, chest, furnace or crafting menu.
Non-player containers must also be the menu displayed by the current container
screen. Unknown/custom serializers fail with `GAME_CONTAINER_UNSUPPORTED`; this
does not establish even those native classes' authentic conformance. Carried
stacks are projected, but item components are an empty allowlist: no raw NBT,
block-entity contents, seed, global registries, hidden quests or the global recipe manager are exported. The separately queried visible FTB catalog is described below.
Recipe discovery uses the separate player-unlocked book and focused JEI queries described below.

Observation policy `opaque-voxel-fixed305-radius16/2` casts 256 fixed sphere rays
plus 49 fixed downward rays. Unloaded cells terminate a ray. Every occupied cell,
including glass and unqualified modded air-like blocks, occludes further cells;
edge/corner ties stop traversal. Each ray has at most 96 cell reads. Only the
three native air IDs are transparent. Entity identities/positions are projected
only within 16 blocks, outside occupied/occluded cells and when not invisible to
the player. Coordinates are never accepted as arbitrary observation queries.
Entity IDs combine the network ID with a salted UUID digest; the salt changes
when the connection/body or observation authority resets. A recycled network ID
cannot authorize input against a replacement entity, and raw entity UUIDs are
not exposed. Captures privately bind the selected hotbar slot: a selection change
invalidates action preconditions even when the projected inventory is unchanged.
All pages retain that same selection fence; it is not an extra public state field.

Each immutable captured region contains at most 16,384 cells/entities and yields
pages of at most 128 each. Four scenes are cached for at most 30 seconds. Guessed,
expired, evicted, different-dimension or pre-reconnect/respawn pages reject.
No later-page request scans new geometry. Native capture time begins before the
scan; all pages retain the same revision, source clock and capture time, with
increasing age. Repeated reads and observation timestamps do not increment the
state revision; changed projected state does. `captured_elapsed_ms` is **not** gateway `captured_mono_ms`:
complete clock mapping/transport uncertainty qualification remains worker
integration work. Yaw/pitch use the existing Mineflayer radians convention.
For a saved-player reference, Minecraft stores degree axes: public yaw is
`radians(180 - savedYaw)` modulo `2π`, and public pitch is `radians(-savedPitch)`
wrapped to `[-π, π)`. Convert units and axes before comparing; an intended
five-degree effect threshold is `π/36` radians.

Native movement preparation now separates captured BlockState values from a
bounded delivered map. Only a page whose delivery journal entry has been forced
can promote its listed cells; unseen pages cannot populate route knowledge.
Whole-page validation precedes promotion, and failure fences the lane. Captured
scenes are limited to four; delivered cells to 1,024, with newer-capture ordering,
unchanged age on re-delivery and reset on body/connection change or rearming.
Private BlockState values are not exported. The map has no raw-world fallback.
[Delivery authority tests](../verification/2026-09-19-forge-delivered-map.md)
cover the knowledge boundary. The level-walking planner consumes a
copied delivered-state collision view: 16-block radius, 512 expansions, 4,096
lookups, 64 waypoints and 20 ms computation limit. It checks swept body clearance
and full continuous support; missing, old, fluid-bearing or unqualified geometry
rejects. Its explicit native block allowlist is still unverified in the loaded
pack. Steps and jumps reject. The development `move_to` motor now connects this
planner to ordinary controls, interruption and charged ticks; authentic effects
and cancellation timing remain unverified.

For the opt-in native shape probe, set the operator JVM property
`-Dstrata.collisionProbeDirectory=<absolute-existing-private-directory>` outside
the repository and game profile. It runs 13 read-only checks after client loading
and writes a bounded, forced `collision-<uuid>.json` with source JAR hash and case
results; it neither joins a world nor grants input authority. This probe remains
unrun. [Planner evidence and probe limits](../verification/2026-09-19-forge-route-planning.md).

The connection fingerprint hashes loaded mod artifacts, Java/OS identity and the
development capability policy. It is not a sealed PackLock or proof of exact-pack
support. Source/schema and pack-lock verification remain admission prerequisites.

Loaded artifact hashing policy `forge-loaded-file-and-jarjar-bytes/2` reads the
actual bounded bytes of Forge Union/JarJar entries as well as host files. The
pinned JarJar provider does not implement `toRealPath`; these read-only loaded
paths must not pass through the host options/journal writer's path validator.
All writable paths still require the default host filesystem. See the
[authentic startup regression](../verification/2026-09-19-forge-live-api.md).

For an explicitly prepared read-only client, the operator can run
`uv run --frozen python tools/check_forge_observations.py --connection <private-descriptor>
--evidence <new-private-directory> --phase disconnected` at the title screen,
and `--phase world` after joining the dedicated server. `--phase transport`
checks credential/Origin/Host/session/deadline/schema rejection without mutations.
Each run preserves its checker source/hash. The checker neither
joins nor enables actions. Its raw result bundle is private and is not a complete
T03, visibility/isolation or latency qualification.

## Remaining work before gameplay

The public worker now supports confirmed asynchronous `Backend.stop()` with a
250 ms bound, waits before acknowledging stop/cancel, and drains before journal
closure. Rejection/timeout fences the epoch and prevents a clean-stop claim.
[Synthetic worker evidence](../verification/2026-09-18-worker-release.md) covers
that prerequisite. [Scoped Forge routing](../verification/2026-09-18-forge-worker.md)
now has actual worker/Java/HTTP tests using a synthetic runtime, not Minecraft.

- Connect the development worker to controller input generations and repair holds.
  Qualify observation clocks/uncertainty and reconcile local native charge counters
  into aggregate budget and performance ledgers. The Windows process guardian now
  provides independent termination with synthetic process evidence; authentic
  interruption timing, complete launch containment and deployment isolation remain open.
- Full movement geometry/conformance and authentic player-accessible crafting. The nineteen
  implemented action kinds still need authentic effect,
  interruption and mod-hook conformance. Unknown modded menu,
  recipe/machine/quest serializers require explicit adapters and evidence.
- Actual private transport isolation, clock/resource accounting, keymap boundaries,
  gameplay packaging, paired arm identity, live Forge join and every exact E9E
  compatibility/reference case. Settings and rendered-input conformance remain
  separate required work; this API cannot pass those tests.

See [initial observation evidence](../verification/2026-09-18-forge-game-api.md)
and [native action evidence](../verification/2026-09-18-forge-game-actions.md).

## Explicit scoped development worker

For operator startup, the exact 1.19.2 client supports native `--server` and
`--port` arguments. This path performs ordinary authenticated connection after
resource loading and skips installing a title screen. The opt-in game bridge
therefore initializes either at a disconnected title screen or after an
unobstructed world RenderTick.END with the same non-null native player, level
and connection. An open screen, overlay or disabled rendering cannot establish
world readiness; replacing any body component invalidates the prior render.
Partial joins/loading remain inert. The bridge does not itself initiate a join or add a gameplay connection
command. The separate-desktop development profile uses `pauseOnLostFocus:false`
in its private copy; this engineering setting must be pinned and qualified with
the complete motor/focus policy before campaign use.

Private body binding preserves the existing saved-server endpoint when present.
Native startup supplies no saved-server entry, so policy
`server-metadata-or-resolved-tcp/1` uses the live connection's numeric TCP peer
and port in that case, with brackets for IPv6. It performs no DNS lookup and
rejects absent, unresolved, non-TCP or invalid-port peers and malformed existing
metadata. The endpoint and authenticated player UUID feed the private body hash;
neither is added to gameplay observations. A startup join and a successful body
hash do not establish complete server, credential or network isolation.

The operator prepares the dedicated client/bridge; the worker does not launch,
join, install, authenticate or drive desktop controls. A bridge without action
authority remains read-only. Obtain its native fingerprint and body identity
privately, then compute the exact broker capability digest from the built code:

```powershell
node backends/mineflayer/dist/src/worker.js --forge-capabilities NATIVE_FINGERPRINT
```

Use that digest in the private native authority described below, with the intended
campaign/avatar/body, an immutable expiry covering the worker's wall limit and
the same primitive limit. Authority is loaded when the bridge starts; changing
its file does not modify a running lane. A changed authority cannot reuse its
old native journal. Restart/rejoin and use the fresh session descriptor after
deployment; never bypass a stale-authority/journal rejection by discarding costs.

The following is an operator configuration shape, not an installation or launch
instruction. Keep the actual file, connection descriptor and state directory
outside the source/gameplay trees under a protected operator identity:

```json
{
  "schema": "strata/ForgeDevelopmentWorker/2",
  "purpose": "manual-conformance",
  "server_kind": "e9e",
  "backend": "forge_client",
  "pack_version": "1.27.0",
  "connection_file": "C:\\private\\strata\\bridge\\game-connection-ID.json",
  "process_guard_file": "C:\\private\\strata\\guard-avatar-1.json",
  "guard_python": "C:\\private\\strata-runtime\\Scripts\\python.exe",
  "native_fingerprint": "REPLACE_WITH_NATIVE_SHA256",
  "body_fingerprint": "REPLACE_WITH_PRIVATE_BODY_SHA256",
  "state_directory": "C:\\private\\strata\\worker-avatar-1",
  "max_wall_ms": 60000,
  "primitive_limit": 1000,
  "campaign_id": "development-campaign",
  "agent_id": "avatar-1",
  "epoch": 1,
  "lease_id": "operator-issued-lease"
}
```

Run `node backends/mineflayer/dist/src/worker.js C:\private\strata\worker.json`.
Version 2 requires the private [Forge process guard grant](process-guard.md), a
Python 3.12.14 interpreter with the matching operator package, and Windows. Old
Forge worker version 1 configurations reject; there is no unguarded fallback.
The guardian owns the explicitly granted dedicated Java client lifetime, so the
client also terminates when this worker session ends. Its remaining lifetime at
readiness must cover the requested worker wall limit plus 2250 ms of shutdown
reserve; an insufficient grant rejects before worker arming. Startup does not
launch a client or modify its live profile.

The supervisor creates a separate `grant-EPOCH.json` containing only the public
gateway URL/token and campaign/avatar/epoch. Supply that grant through
`STRATA_GAME_GRANT` to the existing `mcgame` CLI. The native bearer descriptor
must never be supplied as a gameplay grant. The old vanilla development config
still selects Mineflayer; no failure automatically selects the other backend.

Startup checks the loaded `authority`, native policy/fingerprint, current body
and generation, durable counters, and a fenced native lane before arming a fresh
epoch. `observe_bound` captures body/generation and state on one client thread;
the broker validates and journals the public projection before granting actions
against it. A public observation's capture bound is request-start minus native
age, retained across its pages; local/native clock samples remain distinct.
Only terminal action status generates public event signals on this candidate.

The nineteen native action kinds are available through full public ActionBatch
requests; `look-at` uses the existing CLI wrapper and `recipes --after 0` queries
the unlocked book. Quests, settings, screenshots and raw/admin operations reject. Native receipts
remain input-only `emitted`; the broker supplies a fresh result observation and
keeps unknown counts/uncertain release explicit. Cancellation fences the epoch;
neither renewing the old lease nor resubmitting an old request resumes it.
Local native charge high-water marks survive broker epochs and include safety
releases. Controller-wide accounting/isolation and authentic conformance remain
required before campaign admission.

## Opt-in native action authority

Before the bridge initializes, the private directory may contain
`game-authority.json` with exactly the `strata/NativeGameAuthority/1` schema and
fields `campaign_id`, `agent_id`, `capability_digest`, `body_fingerprint`,
`expires_unix_ms`, `primitive_limit`. Use the strict Python `GameAuthority` model.
The operator must bind these to the intended body and public worker identity;
that admission integration is still unfinished. The authority cannot be edited
to increase limits and reopen the same journal: its identity is bound into the
journal header alongside the native software fingerprint. It never enables
campaign admission or signals qualification.

The optional lane opens `game-actions.jsonl` under a process file lock. It starts
fenced, including after a restart. Use `lane_status` to obtain a fresh
`fence_token`, then `arm` with `epoch`, `lease_id`, `lease_until_unix_ms` and
`expected_fence_token`. An epoch must increase; a lease lasts at most six seconds.
`renew` takes the lease fields without the fence token and cannot revive expiry.
Every new arm/fence rotates the token, so a lease request queued before stop-all
cannot reopen input afterward. Actual worker identity/grant ownership is the
future scoped broker's responsibility, not established by this private token.

After arming, request a fresh observation. `deliver` accepts `observation_id`,
`snapshot_id`, `state_revision`; the designated broker must call it only after
durably recording the agent's actual observation delivery. The native journal
retains the snapshot bytes. Only those delivered IDs, at most two seconds old,
can authorize an action. This operator endpoint is not itself proof of model
delivery. At most 16 current deliveries are retained as input authority; evidence
is not silently deleted from the journal.

`act` takes `args={"batch":<public ActionBatch>}`. Native validation checks exact
public fields/types, non-example structured mode, scope/capability, epoch/lease,
sequence, revision, deadline and supported action. Current player state and target
preconditions are checked again before dispatch. An accepted batch is journaled
and forced before any ordinary input; each primitive intent is forced before its
native invocation. `action_status`/`cancel` take `request_id`; `stop_all` takes no
arguments. Cancellation has reserved transport capacity and fences a referenced
request even if it overtakes that request's queued acceptance.

The nineteen implemented motors require a live survival player in the bound body:

- `move_to`: plan only through delivered states; walk a level route with ordinary
  forward input and yaw, with at most 30 seconds. Neutral startup/re-press waits,
  walking and coasting ticks are charged; settle before turning. Require ordinary
  input classes, a standing/grounded non-sprinting body and auto-jump/toggle-sprint/
  toggle-crouch disabled. Recheck short corridors and delivered age, own state,
  input agreement, health/absorption, collision, displacement and progress. Stop
  on failure, deadline, cancellation or exhaustion; preserve momentum and incurred
  effects. No implicit block edits, resource actions, sprint, teleport or position
  snap. Precision may fail/time out. [Motor evidence and remaining native cases](../verification/2026-09-19-forge-movement.md).
- `look_at`: set ordinary player camera yaw/pitch; no teleportation.
- `dig`: validate a delivered block ID, ordinary reach and native outline hit;
  aim, start destruction, continue on client ticks, then release. No direct
  `destroyBlock`, raw packet or server-admin call.
- `interact_block`: validate the same block/reach/hit conditions, aim and use the
  main hand through `MultiPlayerGameMode.useItemOn`. The actual item/block effects
  still require authentic conformance.
- `click_slot`: validate the supported open menu, window revision and slot;
  invoke normal pickup/quick-move through `handleInventoryMouseClick`, then request
  full server contents and verify cursor/slot changes and conservation. Predicted
  local slots do not finish a step. Generic clicks reject crafting preview slots;
  only the separate checked crafting motor may take a recipe output.
- `equip`: use the requested player-menu source slot (5–45) and exact item ID,
  with an empty cursor and no non-player container. A source hotbar slot can be
  selected directly for the main hand; otherwise fixed pickup/destination/optional
  return clicks place the item and return displaced contents to the source. Each
  click waits for full server contents and rechecks menu identity, slot permissions,
  capacity and item/component conservation before any subsequent click. No inventory
  search, item acquisition or drop fallback is performed.
- `place`: require both the support block and its adjacent air cell in the delivered
  page, the named held `BlockItem`, Forge reach and the requested face as the native
  ray hit. Aim, recheck after the Forge input hook and use normal `useItemOn`.
  Replaced support/occupied destination/wrong face/hidden cells reject. This initial
  policy uses air destinations and normal main-hand use; it does not implicitly
  crouch or promise placement against an interactive block instead of that block's
  ordinary use effect. Nonstandard items, replacement behavior and exact-pack
  placement effects remain qualification work, with input-only receipts.
- `use_item`: explicitly select main/off hand; trigger normal `useItem` once,
  respecting the Forge input hook and normal swing result. A zero hold is a tap;
  an ongoing use can hold for at most 2000 ms, bounded by the action deadline.
  Each active held tick is charged. Completion, changed item/hand/selected slot,
  lost gameplay context, cancellation or exhaustion stops the continuation.
  The tick-START motor and a Forge use-input cancellation hook prevent the native
  held-key loop from starting a second item use; release clears the owned-input
  state. Release follows ordinary item mechanics: cancelling a held bow may fire
  its arrow and consume ammunition. Cancellation ends the continuation; it does
  not undo effects or refund resources. The [minor-34 E9E trial](../verification/2026-09-19-outline-target.md)
  retains one consumed arrow and the released projectile as a narrow authentic
  example. Actual custom mod polling/hold behavior remains unverified.
- `attack` / `interact_entity`: require an ID in the delivered page, recheck its
  current salted identity/type/visibility, use Forge-adjusted attack/interaction
  reach and the nearest native ray hit, aim, then recheck before the gesture and
  after the Forge input hook. Entity interaction uses main-hand `interactAt` with
  ordinary `PASS` fallback to `interact`; attack uses normal `attack`. Respect
  cancellation and swing policy. No automatic repeat or target substitution.
- `chat`: call the normal signed-chat path, including its existing Forge hook.
  Reject commands, empty/blank strings, control/format-code characters, malformed
  surrogate pairs and strings over Minecraft's 256 UTF-16-unit network limit.
  Unicode text is supported within that bound; no command-dispatch API is called.

- `craft`: execute one named, unlocked recipe 1–64 times through ordinary recipe-book
  placement and confirmed slot clicks. Require the requested window/revision and
  exact supported 2×2 inventory or 3×3 crafting menu, empty grid/result/cursor,
  server-confirmed ingredients and output, and distinct empty own-inventory slots
  for output and remaining items. No acquisition, recipe chaining or implicit drop.
  See the detailed discovery/execution policy below.

- `quest_ui` / `open`: open the own-team FTB quest book once using the observed
  root catalog source/revision and exact local screen confirmation.

- `quest_navigate`: select a visible chapter/quest from its catalog page or use
  ordinary back/close, bound to current source/screen state. Confirm only the local
  UI transition; see the navigation policy at the start of this runbook.

- `quest_task` / `open`: invoke the selected visible item-task button once and
  confirm its actual item menu and parent book. Submission and claims are separate.

- `quest_reward` / `open`: open the observed eligible choice reward through its
  ordinary button, retaining parent/source binding for read-only choice projection.
  It cannot select a choice, claim a reward or expose raw reward-table fields.

- `quest_menu`: one ordinary item-menu Back or up/down wheel gesture, using the
  current source/menu generation and revision. Confirm local state only.

- `recipe_navigate`: one enabled category/page control or ordinary history Back
  in the currently observed, origin-bound JEI screen. Match page/screen/source
  revisions and await a fresh frame. Category/page actions use preview/execute
  and reserve four primitive units; Back uses its public callback and reserves
  three. No implicit repeated-page search or private history access.

- `close_window`: explicitly close the named current window/revision. Establish
  room for carried items and crafting-grid inputs before dispatch; use ordinary
  screen/player close and await full server player-inventory contents. Verify empty
  cursor/grid and exact owned-resource conservation. Chest/furnace contents remain
  in their container and are not queried after close. Do not attach this operation
  implicitly to movement or replay it after a lost reply. [D07 checks](../verification/2026-09-19-menu-close.md).

All actions except slot clicks/equipment/crafting/menu close/quest navigation/task opening/choice opening/item-menu controls/recipe navigation require no open screen. Non-player menus must actually
be displayed. Native release stops destruction/use, releases registered key
mappings, clears cached logical movement input, drains bounded click queues and
resets any owned JEI pending gesture without executing it;
physical momentum remains. This is not a proof of arbitrary mod
polling or OS input parity. Action receipts are `accepted`, `executing`, `emitted`,
`cancelled`, `failed` or `unknown`, never fabricated `completed` results. Every
terminal result requires a fresh observation. Unknown outcomes or cancellation
fence input; a fresh epoch/token/delivery is needed before further action.

The absolute wall cutoff is immutable, with a local monotonic cutoff and action
deadlines as additional bounds. Primitive limits count durable attempted motor
invocations conservatively; look, aim, click, start/continue destruction and the
combined safety release are declared units, not raw network-packet counts.
Motor policy `durable-intent-client-thread-nineteen-actions/2` additionally counts
one unit per discrete use/entity/chat gesture and each subsequent held-use tick.
A gesture includes its ordinary Forge input hook, permitted swing and the native
interaction-at/`PASS` fallback, or tap release. Aim and final safety release are
separate units. Inventory clicks, fixed refresh requests and each active tick
waiting for menu feedback are separately charged. Each active movement decision,
including neutral startup/coasting, is a charged unit. Recipe-book fill is also a
separate charged invocation, as are explicit menu close and each quest UI callback. A targeted wheel gesture includes logical hover restoration as one charged invocation. Recipe navigation charges preview/execution or the history callback, plus each fresh-frame wait tick. Capability minor 34 identifies this policy, explicit
recipe/crafting and navigation/collision/movement policies and observation revision 2;
old native capabilities reject instead of silently acquiring the new behavior.
Uncertain attempts are not refunded. A release reserve is kept during ordinary
dispatch; safety release still runs on exhaustion or evidence failure. Missing
release/accounting evidence makes the lane unhealthy and disallows more input.
These native counters do not replace the aggregate tool/body/model budget ledger.

`dig` and `interact_block` use `observed-outline-centers64-local16/1`. After the
existing delivered-ID/context/freshness checks, the native player-context outline
is collected into at most 64 positive-volume finite boxes within local [-16,16].
Distinct component centers are ordered by eye distance and X/Y/Z. Only centers
inside the current native pick range are raycast; the ordinary OUTLINE hit must
be on the requested block. Empty/occluded/unreachable/unsupported shapes reject.
There is no assumption that a partial block contains its cell center, no route
search, and no input until these checks pass. The old mayapple failure and the
candidate's separate qualification are retained in the
[paired reference report](../verification/2026-09-19-paired-block-reference.md).

The broker privately records `native_action_call_failed` under
`native-call-failure-after-fence/1` after its existing release/fence attempt.
It includes request/epoch/action sequence, act/status phase, time and an allowlisted
fault code; unrecognized errors become `UNCLASSIFIED_NATIVE_FAILURE`. The private
transport carries that sanitized code through its mutation-unknown wrapper;
validated rejection, malformed response and transport loss all retain unknown
mutation semantics. The code is never a proof of non-emission or retry authority. No raw
message, stack or arbitrary code is serialized. The public action still requires
resynchronization and cannot be replayed. Diagnostic storage failure remains an
evidence fault and cannot precede the release attempt.
See [gesture implementation and synthetic evidence](../verification/2026-09-18-forge-gestures.md).

### Explicit menu close

D07 in SPEC 8/9 adds `close_window` with `window_id` and
`expected_window_revision`, carried in the existing single-action envelope. Use
`mcgame act` with that envelope; both Mineflayer and Forge advertise this capability.
Unknown fields, stale window/revision, unsupported menus and insufficient safe
return capacity reject. No menu close is hidden inside another action.

Policy `explicit-close-own-inventory-feedback-conservation/1` retains own armor,
main/hotbar and offhand items plus the carried stack and temporary crafting inputs.
It excludes the recipe result preview and persistent chest/furnace storage. Model
return capacity by merging compatible items and filling empty main/hotbar slots;
an existing offhand stack can merge, but an empty offhand slot is not an implicit
equipment destination. Candidate stacks are bounded to 64, with exact private
component/NBT identity and actual native/pinned item capacity. Unknown larger or
custom menu mechanics remain unsupported until qualified.

The Forge port invokes the displayed container screen's ordinary `onClose`, or
ordinary player close for inventory-menu zero without a screen. Screen/menu,
selected slot and native body continuity are fenced. Full own-inventory feedback
must follow and agree with applied client state; returned cursor/grid must be empty,
owned resources conserved and armor unchanged. The fixed refresh has the same
ordering/no-causal-nonce qualification limits as other inventory operations below.

Mineflayer uses its pinned ordinary `closeWindow` method, then `_syncWindow` on the
player inventory. It captures the open menu's current player-inventory region
before the pinned method copies it, so stale local inventory does not fabricate a
loss or gift. It never rereads the closed container. Close, refresh and active
50-ms feedback-wait iterations are charged; the native motor charges its own client
wait ticks and final release. Cancellation, budget stop, replacement menu or failed
feedback cannot reopen or replay the closed window. Public receipts remain `emitted`
with observation/recovery requirements, not an authoritative server-success claim.

Forge capability minor 11 / native thirteen-action policy and Mineflayer capability
minor 6 identify this addition. Exact live cursor/grid returns, mod close hooks,
ordering/resource effects and stop timing remain unverified on both profiles.

### Player-unlocked recipes and fixed crafting

Discovery policy `player-book-exact-shaped-shapeless-pages32/1` reads the actual
client recipe-book collections, checks the player's known set before inspecting
each definition, and checks the selected object against the active recipe manager.
An exact ID lookup checks the known set first. It does not substitute a vanilla
database, infer a recipe chain or enumerate hidden recipe solutions.

The initial adapter accepts exact native ShapedRecipe/ShapelessRecipe classes,
their matching registered serializers and simple vanilla ingredients. It exports
namespaced item alternatives, dimensions and output ID/count only. Unknown/custom
serializers, special recipes, tagged outputs and excessive definitions become
explicit `{recipe_id,supported:false}` entries. No raw NBT/capability data is
exported. Actual unlocked-source semantics, mod hooks and expert effects are still
unqualified; the focused JEI candidate below adds discovery, while custom serializers remain required adapter work.

Pages contain at most 32 entries and 32 KiB, with a visible-catalog revision and
integer `next_cursor`. Inspect at most 10,000 book entries and retain at most 4 MiB
of projected definitions. Pages are sorted by recipe ID. A changed revision means
the caller must restart pagination; integer cursors do not promise a frozen catalog.
The native private `recipes` operation accepts only `{after}` and binds its response
to body fingerprint/connection generation on the client thread. The public scoped
broker validates that binding, journals the source and returns only revision,
recipes and next cursor. Both clients reject malformed/extra fields.

Crafting policy `known-recipe-book-fill-single-output-remainders/1` uses normal
`handlePlaceRecipe(menuId, recipe, false)` once per requested execution. The grid
must initially be empty; autofill is limited to the specified recipe. After actual
full-menu feedback, every nonempty ingredient slot must contain exactly one item,
all non-result resources must be conserved, and the requested recipe must match
the grid/result. Derive native remaining items from an isolated copy of that grid;
never mutate the real menu to calculate them. Reserve a separate empty own-inventory
slot for output and each remainder, with capacity/permission checks before taking
the output. This conservative motor currently rejects storage arrangements needing
merges or rearrangement, even if a more elaborate player sequence could succeed.

An ordinary result pickup must receive server feedback proving exact output,
ingredient consumption and remaining stacks. Confirm each output/remainder transfer
before proceeding. Recheck recipe object/definition/known status, menu and selected
slot throughout. The 10-second action limit applies to the entire request, including
waits/repetitions. Cancellation/exhaustion may leave a filled grid or carried result;
preserve those effects and charges. No rollback, refund, retry or auto-cleanup is
inferred from a missing reply. Receipts stay input-only `emitted` with a fresh
observation; authentic server/reference evidence is still required to assert recipe
success. The full-menu refresh has no causal nonce and retains its qualification
limits below. [Implementation and synthetic checks](../verification/2026-09-19-forge-crafting.md).

### Focused JEI discovery candidate

Forge capability minor 12 initially added `jei-visible-crafting-item-focus-pages32/1` using
the public common API for the installed JEI **11.8.1.1034**. The API is compile-only;
the mod JAR does not bundle JEI. Gradle verifies the downloaded API and explicitly
pins the Forge-transformed API bytes. A missing, different or unready JEI runtime
rejects the query; there is no recipe-manager enumeration fallback.

The scoped command is:

```text
mcgame recipe-query --item minecraft:furnace --role output --after 0 --json
```

`input` asks for uses of the chosen item. Requests specify exactly source `jei`,
category `minecraft:crafting`, one namespaced item, input/output role and integer
cursor 0–512. The native plugin requires a connected player, JEI-visible focus
item and visible crafting category. It uses the default non-hidden focused recipe
lookup, never `includeHidden`, all-ingredient enumeration or transfer/cheat hooks.
Definitions require the same exact native serializer/ingredient checks as the
book source, plus JEI visibility for every projected ingredient alternative and
output. Unsupported visible definitions return only their ID, support flag and
book status. Hidden candidates are not identified or inspected by the projection.

At most 512 matching candidates are inspected; pages contain at most 32 recipes
and 32 KiB including query metadata. The projection and native lookup check a
100 ms cooperative time limit. This cannot preempt a blocking upstream JEI call;
authentic client timing/guardian conformance remains open. Runtime replacement or
body/connection changes during a query reject the result. Runtime generation,
focus changes, visible definitions and book-status changes invalidate the catalog
revision. A changed revision requires restarting pagination.

Private replies bind body fingerprint and connection generation. The broker checks
them, journals the source, and exports only the query echo, source generation,
policy, revision, entries and cursor. Strict Python/TypeScript clients reject
extra fields, mismatched queries/policies, malformed recipes and invalid cursors.
The public endpoint retains avatar/campaign/epoch/grant checks. Stock Mineflayer
does not implement this JEI operation and returns `CAPABILITY_MISSING`.

`craft_authority=discovery_only` means the player has not unlocked that recipe in
the book. `recipe_book` records current book membership; `supported` independently
describes definition support. Neither value promises executable crafting or
changes resource/menu/revision checks. An omitted/null source selection still
requires the book route; D09's explicit manual selection is described below.
Minor 16 supersedes that query policy with the extension below. Loaded-pack
JEI/UI parity and expert execution remain unverified.
[Discovery evidence](../verification/2026-09-19-jei-query.md).

### Focused Thermal recipe discovery

Capability minor 16 uses `jei-visible-crafting-thermal-item-fluid-focus-pages32/2`.
The crafting query shape stays unchanged. Thermal queries accept exactly one
`item_id` or `fluid_id`, with category `thermal:furnace` or `thermal:crucible`,
source `jei`, input/output role, and cursor 0–512. For example:

```text
mcgame recipe-query --category thermal:crucible --fluid minecraft:lava --role output --after 0 --json
mcgame recipe-query --category thermal:furnace --item minecraft:iron_ingot --role output --after 0 --json
```

Require the exact loaded JEI, Expansion, Thermal Core and CoFH Core JAR hashes,
matching JEI runtime version, exact category/recipe classes and a connected body.
Only JEI's non-hidden focused lookup supplies candidates. Read the public JEI
layout's two input/output slots; do not enumerate the global recipe manager.
Every alternative must be visible, plain, bounded and supported. Nonsimple or
non-vanilla input predicates, tagged item/fluid stacks, unknown ingredient types,
duplicate alternatives and other layouts are unsupported. This initial adapter
does not implement CoFH counted/custom predicates or other mod categories.

A supported machine row contains `recipe_id`, `supported:true`, `category`,
`energy_rf` (positive integer or null), two `slots`, `output_tooltip` and
`craft_authority:discovery_only`. Each slot contains `role` and sorted unique
`ingredients`. An item alternative is `{kind:item,item_id,count}`; a fluid
alternative is `{kind:fluid,fluid_id,amount_mb}`. The furnace has item input/output;
the crucible has item input/fluid output. Bounds are 64 input alternatives, one
output, item count 1–64 and fluid amount 1–2,147,483,647 mB.

The furnace tooltip is null or `{kind:chance|additional_chance,percent:0..99}`,
matching the installed callback's absolute value, fractional part and truncated
integer percent. Do not interpret it as an exact raw probability. Null energy or
tooltip means no corresponding display, not zero energy or guaranteed output.
Undisplayed XP, raw chance sign/precision, custom predicates and components are
not projected. The crucible has no output chance tooltip.

Machine rows cannot be `craft` selections; they grant no automatic transfer,
operation or production claim. Existing 512-match, 32-row/32-KiB, cooperative
100-ms, body/source and revision bounds remain. Category and ingredient kind
participate in revision identity. Reloads/focus changes require fresh pages.
[Implementation and synthetic evidence](../verification/2026-09-19-thermal-recipes.md)
does not establish authentic JEI/UI, timing, effects or server/reference parity.

### Visible FTB quest catalog

Forge capability minor 17 adds `quests.list`, implemented by the native `quests`
operation under `ftb-visible-chapters-quests-own-team-pages32/1`:

```text
mcgame quests --after 0 --json
mcgame quests --chapter 0123456789ABCDEF --after 0 --json
```

The chapter code above is illustrative; use an ID from the actual chapter page.
The query is exactly `{source:"ftb_quests",chapter_id:null|"UPPERCASE16HEX",after:0}`.
Root pages contain visible chapters; a chapter query contains its visible quests.
The bridge pins all three FTB artifact hashes, rejects editing mode, and checks
that `ClientQuestFile.self` belongs to the current player. It uses the public
visible-chapter, quest-visibility and own-team progress APIs. There is no team
selector. Hidden entries are filtered before IDs, titles and progress are read.

Each row has exactly `kind`, `entry_id`, `title`, `progress_percent`, `completed`,
`startable` and `details_visible`. The last two are null for chapters and boolean
for quests. A visible quest can still have inaccessible details; the flag follows
FTB's `hideDetailsUntilStartable` and own-team `canStartTasks` rules. Descriptions,
task/reward definitions, dependency graphs and quest mutations are not implemented
by this catalog. They remain required follow-on work, not implicit capabilities.

Bounds: 4,096 inspected entries, 32 rows/32 KiB per page, 1,024 Unicode code points
and 4 KiB per title, 4 MiB across the collected projection, and a cooperative
100-ms time limit. The response retains query echo, source generation, content
revision and next cursor. A replaced file/team/player/connection, editing mode,
unknown/hidden chapter, invalid field or missing artifact rejects the page.
Native body/connection identity is checked privately and omitted from public
results. Changing visible content or chapter focus changes revision. Callers
must not combine pages across different revisions or source generations.

This is a read-only, unqualified candidate. The pinned native APIs have been
inspected, but tests use synthetic FTB data; actual loaded reflection, UI hiding,
team switching and timing remain unverified. Stock Mineflayer has no FTB source
and rejects this query with `CAPABILITY_MISSING`. No inference or quest completion
is initiated by discovery. See [verification](../verification/2026-09-19-quest-catalog.md).

### Readable quest text

Forge capability minor 18 additionally exposes `quests.text`, backed by native
`quest_text` and `ftb-visible-own-quest-plain-text-pages32/1`:

```text
mcgame quest-text --chapter 0123456789ABCDEF --quest FEDCBA9876543210 --after 0 --json
```

Replace both illustrative codes with IDs from visible catalog pages. The exact
query fields are `source:ftb_quests`, `chapter_id`, `quest_id` and `after` (0–512).
Both IDs are exactly sixteen uppercase hexadecimal characters. No team selector
or raw object query is available. Visibility and detail access precede content
reads. If description text is still locked, the result has
`description_visible:false`, empty lines and no next cursor; the ordinary
subtitle can still be present. A hidden or detail-locked quest rejects the query.

The response contains query, source generation, policy, revision, title,
subtitle, description visibility, ordered lines and next cursor. A line is
`{kind:text,text:STRING}`, `{kind:page_break,text:null}` or
`{kind:unsupported,text:null}`. The last form explicitly preserves an unrepresented
rich/interactive/image line; it does not expose raw JSON, hover actions or URLs.
Plain color/style is reduced to text, while translations and keybinding labels
use ordinary client component text. Unknown component types, deep/cyclic/shared
component trees and interactive styles are unsupported. An unsupported subtitle
rejects the query rather than returning an empty subtitle.

At most 512 lines are projected, with 32 lines/32 KiB per response. Titles and
subtitles have 1,024-code-point/4-KiB limits; lines have 4,096-code-point/16-KiB
limits and 2 MiB aggregate. Source/visibility is checked again after reading.
Content/focus/source changes advance revision; cursor changes alone do not.
The 100-ms cooperative timer cannot preempt a blocked native parser. Source,
body, lease and query checks are the same private broker safeguards as the
catalog. No task/reward definitions, dependency graph, guide/rich content or
quest mutation is implied. These retain required child work and authentic
qualification. See [text verification](../verification/2026-09-19-quest-text.md).

### Visible task and reward displays

Forge capability minor 19 adds `quests.components`, backed by native
`quest_components` and `ftb-visible-own-quest-task-reward-tooltips-pages32/1`:

```text
mcgame quest-components --chapter CHAPTER_CODE --quest QUEST_CODE --part tasks --after 0 --json
mcgame quest-components --chapter CHAPTER_CODE --quest QUEST_CODE --part rewards --after 0 --json
```

Use exact sixteen-character uppercase IDs from the visible catalog. The query
has exactly `source:ftb_quests`, `chapter_id`, `quest_id`, `part` and `after`.
The adapter requires the same non-editing own-team source and parent visibility/
detail access. Blocked or invisible-auto-claim rewards have no public row;
their identifiers, titles and tooltip readers are never invoked.

Each row has `entry_id`, `kind`, `title`, `tooltip`, `task` and `reward`. The
irrelevant role field is null. Task state is `{completed,optional,progress_label}`;
progress is a normal UI-formatted string or null when the UI has no progress
label. Hidden numbers produce the displayed percentage without exact counts.
Reward state is `{claim_state:can_claim|cannot_claim|claimed,team_reward:BOOL}`
for the current player. It is a client display status, not authoritative proof
of a claim or a guarantee a later claim succeeds.

Tooltip lines are plain text or explicit `unsupported` markers with null text.
The bridge extends the public FTB `TooltipList.add` hook; it does not read the
class's private backing list. Public task header/body and reward display calls
use normal item tooltips, with Shift/Control/Alt required released before/after
capture (`GAME_QUEST_MODIFIER_ACTIVE` otherwise). Debug timestamps, raw server
commands/NBT and player/team selectors are omitted. Unsupported task/reward
classes reject explicitly. No submission, claim or image rendering is invoked.

Bounds: 512 inspected entries, 32 rows/32 KiB per page, 64 tooltip lines and
16 KiB per complete entry, 4 MiB aggregate and a cooperative 100-ms timer.
Native callbacks can block despite that cooperative timer; timing still needs
qualification. Rows sort by ID; source/query/part/content changes advance
revision, cursor changes alone do not. Body/connection identity remains private.
Item-alternative/choice menus, extension types, full rich content and ordinary
quest interactions remain required follow-on work. Actual loaded callbacks,
normal-tooltip parity, claim/team transitions and isolation remain unverified.
See [component evidence](../verification/2026-09-19-quest-components.md).

### Explicit manual crafting from a visible recipe

Forge capability minor 13 declares `visible-recipe-manual-grid-feedback-search4096/1`.
The existing `craft` action accepts an optional `recipe_selection` object with
the exact query returned by `recipe-query`, its `source_generation` and `revision`.
The action still needs the recipe ID/count, current window ID/revision and full
observation/action envelope. Copy the metadata from the selected page; do not
guess, refresh or replace it after an action rejection. Omitted/null selection
uses the existing unlocked recipe-book routine. Mineflayer rejects a non-null JEI
selection before emitting any crafting input.

Native preparation repeats the focused query and checks its initial revision,
generation and selected visible supported ID before looking up that native recipe.
Throughout execution it rechecks the query's current visibility, source generation,
selected object and exact definition. Recipe-book membership may change after a
successful craft, so that flag alone does not invalidate continuation. A source
reload, changed/hidden recipe, shifted page omitting the recipe, changed menu/body
or altered definition fails closed. These repeated reads consume real execution
time; the action's ten-second deadline is unchanged.

The fixed allocator uses only the 36 main/hotbar slots in the currently supported
2x2 player or 3x3 crafting menu. It backtracks at most 4,096 visits to allocate one
set of ingredients, preserving shaped blanks and component identity. Every input
performs a normal left pickup, right place-one and optional left return to its
original slot, with full server feedback after each click. Non-result slots and
cursor must exactly match the planned state; even a resource-conserving unrelated
rearrangement stops continuation. The derived result preview may change while the
grid fills; only the selected final recipe/result can be taken.

The existing output/remainder checks then verify consumption, store output and
return containers without dropping, quick-moving or recipe chaining. Clicks,
refresh requests and feedback-wait ticks consume the existing primitive budget.
Cancellation, uncertain feedback or exhaustion retains the current cursor/grid
and charges; no rollback or blind replay occurs. Empty grid/cursor and conservative
output/remainder capacity checks remain prerequisites. Full inventories needing
merges/rearrangement and custom serializers remain unsupported pending extension.
This motor has synthetic mechanics/real transport evidence only; loading its
candidate at the title screen does not verify crafting.
[Manual crafting evidence](../verification/2026-09-19-manual-craft.md).

### Initial Thermal menu observation

Forge capability minor 14 introduced `thermal-current-gui-energy-fluid-base-slots/1`;
minor 15 adds D10's machine transfer and input-fence policies below.
An open exact Thermal furnace or crucible can supply `window.machine` with RF
energy stored/capacity and, for the crucible, one output tank with capacity and
nullable fluid contents in mB. This is the client GUI view; it is not an
authoritative machine-operation result. These values remain in snapshots and
capture revisions. D10 excludes passive energy/tank values from the window input
revision and live input comparison, so they cannot prevent ordinary close or
slot actions. All slots/cursor/window identity, body/control/generation/lease,
latest captured observation and two-second age checks remain. Unknown machine
policies cannot use this explicit versioned exception.

The bridge requires Expansion 10.3.1.25, nested Thermal Core 10.3.0.9 and CoFH Core
10.3.1.48, exact menu/screen/tile classes, registered type and known layout. It
follows only the current menu's public tile field and fixed public getters. No
world-wide tile search or arbitrary reflective member is exposed. The existing
private native fingerprint hashes loaded artifact bytes; version checks are not
a substitute for the still-required sealed pack lock. This adapter additionally
requires the three exact JAR hashes in `GameMachineMenu.ARTIFACTS`. Their runtime
metadata reports 10.3.1 / 10.3.0 / 10.3.1 respectively, omitting build suffixes;
the byte checks preserve the precise installed build identity.

`window.slots` omits all augment-panel slots, retaining native slot numbers;
omitted slots must not be interpreted as empty. Base slots and the player's 36
main/hotbar slots are emitted only when active. The adapter excludes raw fluid
components, rejects tagged fluids, and has no progress, controls or augment
panel API. Ordinary left/right pickup/place and machine-to-player quick-move use
`thermal-visible-slot-owned-transfer-feedback/1`: one normal player click,
conserved/scoped immediate prediction, then actual applied full server feedback.
The exact predicted cursor and all 36 owned slots must match that feedback and
current state. Independent processing or charging may advance machine storage;
the receipt does not attribute production to the click. Predictions alone cannot
confirm transfers. Invalid predictions still await resynchronization, and no
already-emitted input is replayed. Hidden augment entries are masked before motor
or feedback stack readers run. The unchanged static-resource motor serves the
ordinary vanilla menus. Explicit close retains its guarded own-inventory path.

Native CoFH player-to-machine quick-move includes augment slots. That route and
direct hidden-slot clicks reject before input pending .3.2.2b's panel/routing
qualification. Use ordinary pickup/place for the initial insertion route. This
limitation is retained as required implementation work. Actual Thermal slot,
close/feedback ordering and GUI parity remain unqualified.

Build, contract and synthetic projection results are recorded in
[initial Thermal menu evidence](../verification/2026-09-19-thermal-menu.md) and
[transaction evidence](../verification/2026-09-19-thermal-transactions.md). Deployment,
rendered parity, server synchronization, full routing/controls and energy/fluid
operation remain M0.3b.3.2.2/.4. This does not qualify E9E or close T03/G0.

### Fixed open-menu feedback

Minecraft 1.19.2 predicts inventory clicks locally and may send no reply for a
correct prediction. An internal, fixed refresh sends an outside-slot `PICKUP_ALL`
no-op (`slot=-999`, `button=0`, `stateId=-1`, no changed slots) for the already
validated current menu. The pinned native handler skips transfer for that negative
slot and refreshes all contents on the impossible state ID. These fields cannot
be chosen through the gameplay API; raw-packet/admin access remains unavailable.
This implementation basis comes from the pinned native handler, not a live
no-effect proof. Only the exact Thermal menus above have an added scoped adapter;
other custom menus remain unsupported.

A bounded native listener captures only full contents for that pending menu.
After Minecraft applies the packet on its own thread, the bridge compares those
server contents with the applied menu and supplies them to the fixed motor.
Only one callback per request is retained; replaced menus, stale request tokens,
malformed contents and unapplied replies cannot authorize another click. Private
item comparisons include serialized components/Forge capabilities, bounded to
16 KiB per item, but public component summaries remain empty.

Inventory uncertainty survives cancellation and epoch rearming. A cancelled
request cannot resume; a valid late server reply may reconcile the underlying
state. Until reconciliation, fresh mutations reject with `GAME_MENU_RESYNC_REQUIRED`.
Missing feedback or a replaced menu may require a new connection and classified
recovery; do not reset journals or replay the action to clear this condition.
The normal server-content response is not a nonce-bearing causal acknowledgement:
receipts remain `emitted`, not proof that a particular action caused a game result.
Authentic ordering, no-op behavior, item effects and recovery remain unverified.
See [placement/inventory evidence](../verification/2026-09-19-forge-inventory-placement.md).

The journal has a 128 MiB/approximately 10,000-frame development ceiling and
reserves terminal space before accepting input. Exhaustion/corruption fences
instead of dropping records; archival/rotation and full long-horizon resource
admission remain open. Recovery converts unfinished intents to `unknown` and
retains attempted charges. An identical request returns its prior status even
after expiry; altered payloads using the same ID reject. No pending input is
replayed automatically, and game/agent checkpoint restoration is not implied.

Operator arguments can be supplied as a reviewed JSON file:

```powershell
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json lane_status
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json arm --args C:\private\broker\arm.json
uv run --frozen python -m mcbench.native_game --connection C:\private\broker\game-connection-ID.json act --args C:\private\broker\action.json
```

The Python client sends one POST and only polls its transport request afterward.
An uncertain mutation raises `GAME_OUTCOME_UNKNOWN` with its request/action IDs;
query action/lane status, stop/fence and resynchronize rather than blindly repost.
No inference, autonomous game connection, desktop input or live profile change
is performed by these build/test commands.

The [Windows process guard](process-guard.md) verifies that the native loopback
listener belongs to the granted Java process, checks native authority and a
fenced lane, then monitors authenticated client-thread identity/health reads
independently of Node. The worker binds the same descriptor digest and connection
generation before arming. Startup and termination evidence is retained privately
in `supervisor-EPOCH.jsonl`; no process grant, guardian pipe or native credential
is added to the gameplay package. [Synthetic integration evidence](../verification/2026-09-18-forge-guard-integration.md)
does not establish live Minecraft timing, controller authority, complete process
tree containment or filesystem/process/network isolation.
