# Long-horizon implementation evidence, 2026-09-18

Operator-only. The user requested continued work through milestones rather than
another intermediate stop. A native long-running goal is active for required
M0–M6 work, retaining M7's optional activation conditions. Nothing in this report
waives acceptance gates or supplies credentials or legal acceptance. D04 below records
the user's later explicit inference authorization.

## Provisioning and streaming storage

Implemented `inventory.py`, `provisioning.py`, `pack_commands.py` and streamed
CAS import/copy methods. Commands cover candidate resolution, official acquisition
requests, receipt/evidence import, full installed inventory, bound check records,
sealing, status and fresh materialization. All state is private and durable.

Executed on Windows / Python 3.12.14:

- `uv run --frozen pytest tests/test_provisioning.py -q`: **18 passed**.
- `uv run --frozen pytest tests/test_provisioning.py tests/test_storage_controller.py tests/test_operator_commands.py -q`: **40 passed** after adding per-check identity/digest bindings and preventing an import race from downgrading later states.
- `uv run --frozen ruff check src tests tools evaluator`: passed before the final check-binding refinement; further checks are recorded below as run.

Tests use synthetic archives, executables and installation bytes. They execute
real SQLite/CAS/ZIP/filesystem/CLI code, including independent copies, immutable
request identity, quota-before-write, traversal/link/collision/privacy rejection,
wrong release/loader/origin/hash, complete inventory, bound seal requirements,
corrupt evidence, cleanup and existing-destination rejection. They do not pass T02.

Source checks: the exact official CurseForge file pages still identify E9E 1.27.0
client 8161120/server 8161123; the current official profile guide documents vanilla.
Links and operational limits are in [the runbook](../operations/provisioning.md).
Installed vanilla feasibility, actual distribution hashes, JVM/bootstrap review,
expert cold restart, conformance and deployment isolation remain unverified.

The operator supplies attested provenance and check evidence; this code does not
authenticate arbitrary pages or certify assertions merely because they parse.
Archive inspection does not execute scripts. Template sealing does not promote
an experimental profile to campaign-ready or research-qualified.

## Native process supervision and exact plugin installation

Implemented durable `NativeExec` dispatch, bounded raw JSONL ingestion, one executor,
helper ancestry/depth/concurrency, revocation-before-termination, Windows Job Object
process-tree cleanup, uncertain budget holds, classified fenced recovery and
fresh-handoff manifests. A trusted bootstrap is attached to its Job Object before
it can spawn the native job. The POSIX process-group fallback does not certify
adversarial process isolation. Neither mechanism supplies filesystem/network isolation.

Real Windows subprocess fixtures cover UTF-8/argument/environment handling, delayed
grandchild mutations, parent exit, timeout, malformed output, disk/revocation faults,
duplicates and descendants. Model event streams are synthetic. Export/resume checks
artifact references and fresh epochs; actual complete checkpoint restoration and
native helper invocation remain open.

The pinned native CLI installed Dovetail 0.4.1 into a dedicated external profile with
no credentials or inference. An initial checkout failed on Windows path length;
a short profile and child-scoped Git `core.longpaths=true` resolved it. Inspection
found that pinning the upstream marketplace alone leaves its plugin source at `main`.
`plugins.py` now creates a local marketplace whose plugin source is the exact commit
`15c306ccfef28eb5f616fadcd5fd8eac0663e361`, then uses native marketplace/plugin commands.
The actual native configuration confirms `source_type = "local"` and plugin enablement.

Actual installation evidence (private report retained outside this checkout):

- CLI 0.154.0-alpha.6.2, SHA-256 `960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`.
- Marketplace digest `3b99e85e950713026005769cbd0c1b4c44771c3291557d36af5b7530701d8b22`.
- Manifest digest `9f524b2fa638231aab2627699943983906f785b4f0330347967c99ea8e5c2c66`.
- Installed-byte tree digest `a5a2155185fd2e5f06750f0821f89c57be9d9a26de47f3b057bfd2074ac5756e`.
- Git HEAD, clean worktree, per-file source/blob/installed hashes and all eight skills checked.
- `inference_started=false`, `credential_imported=false`, `native_invocation_verified=false`.

Installation is partial T04 evidence, not proof that the model loads/invokes skills,
isolates helpers, accounts all calls or reaches a game avatar.

## D04: OAuth, Luna and the shared $10 ceiling

The user explicitly selected Codex OAuth, `gpt-5.6-luna`, and $10 total inference.
`authorization.py` and the operator configuration persist one immutable 10,000,000
microusd root ceiling. Development, training, evaluation, helpers and retries share
it; reinstalling does not reset consumed/reserved amounts. A private external store
was initialized with zero spend/reservations. Different models/auth modes and
unparented accounts are rejected. No paid/model job was dispatched.

Read-only login inspection reports ChatGPT authentication. Official Codex auth/pricing
documentation distinguishes subscription/credits from API billing; API token prices
have not been substituted for OAuth monetary conversion. Production dispatch still
requires evidence of finite all-call bounds, complete metering, credential isolation
and verified pricing semantics. The user's $10 authorization is resolved; these
technical execution prerequisites are not.

## Captured-region observation pagination

Added the additive `observe.page` method and optional opaque `cursor` to GameRequest/1
(development contract minor 2). The canonical 13 record identities remain unchanged.
CLI: `mcgame observe --cursor <next_cursor> --json`. Each page has at most 128 blocks
and entities from the original radius-16 line-of-sight capture. Capture time, dimension
and revision stay fixed. Cursors expire at 30 seconds, cache at most four regions,
reject other workers/dimensions, and never query the live world for more entries.
More than 16,384 captured entries of either kind rejects with a capacity error.

Only journaled projected entries enter the 1,024-cell planning cache. Pending pages
own cloned state; later server mutations cannot update them. Old pages cannot replace
newer knowledge. Normal page deliveries are serialized at 500 ms intervals; terminal
receipts remain prompt. Stale pages cannot satisfy the 2-second action freshness gate.

Executed after these changes on Windows 11 / Python 3.12.14 / Node 24.19.0:

- `uv run --frozen pytest -q`: **164 passed**, two existing Typer/Click deprecation warnings.
- `uv run --frozen ruff check src tests tools evaluator`: passed.
- `npm test --prefix backends/mineflayer`: **31 passed**, including strict TypeScript build.
- JSON Schema export and TypeScript generation: passed.

Pagination tests use synthetic geometry/state and the real local gateway/CLI. Tests
cover no skipped/duplicate entries, immutable timestamps/bytes, cursor expiry/eviction,
dimension/worker separation, planner admission only after journaling, stale revisions,
disconnects and cursor/method confusion. Initial build caught an unused import and
passed after its removal. Authentic visibility, mechanics and all aggregate gates
remain unrun.

## Explicit inventory control (development minor 3)

Added `inventory_motor.ts`, with fixed
source/destination clicks for equipment, left/right pickup and quick-move. Every click
is followed by the pinned `_syncWindow` full server response. Completion checks the
carried stack, target stack and conservation of item identity/count/metadata/NBT;
unrelated metadata is never projected to the agent. Crafting previews are not counted
as owned output and require the explicit craft action to take them. Unknown window
serializers reject. An uncertain partially executed sequence is never automatically
continued or rolled back.

The optional `Window.cursor_item` field exposes ordinary player-held cursor ID/count
with the same empty component allowlist. SPEC and generated schemas were updated;
the profile fingerprint/minor distinguishes this added public field. The native
inventory plugin already decodes carried items in `window_items`, but ignores
`set_slot` with window/slot -1. `inventory_feedback.ts` decodes that player-only
cursor update and advances the window revision. No general packet proxy is exposed.

Executed: **39 Node tests passed**, **55 Python contract/record tests passed**, lint
passed. Eight added inventory cases cover known stack arithmetic, off-hand/armor
swaps, empty/full cursor/slots, server rejection, extra items/NBT changes, cancellation,
window replacement and server cursor revision signals. The server is synthetic;
successful library prediction alone is deliberately insufficient. Initial test builds
exposed narrower-than-runtime upstream declarations; fixture typing now matches the
inspected pinned implementations. No authentic inventory/mechanics pass is claimed.

Directly pinned `prismarine-item` 1.18.0 (already present transitively) for the scoped
cursor decoder. npm reports the same six moderate authentication-chain findings (B09).

## Bounded gestures and uncertainty

Development minor 4 adds actual normal-method use/attack/entity/chat dispatch. These
four actions report `emitted`, never `completed` based solely on sending input. The
gateway retains a fresh result observation and duplicate-ID history. Entity targets
must refer to actually delivered identities, be within three blocks and pass fresh
LOS/reach checks after turning; reused IDs, hidden targets and wrong dimensions reject.
Chat permits one ordinary Unicode message, excluding commands/control characters and
the pinned client's implicit >256 UTF-16-unit splitting. The exact 1.19.2 data reports
`chatCommandsQueuedToMainThread=false`; queued-command profiles are explicitly rejected.

Use holds at most two seconds. Owned input state survives unrelated upstream flag
resets, release is charged during cancellation, and the connection is fenced if release
evidence cannot be recorded. Failed local stopping is `unknown` with unconfirmed release.
These changes do not replace authentic server-effect or watchdog/capacity validation.

Executed full suites: **165 Python tests / 48 Node tests passed**, lint, strict generated
operator/evaluator TypeScript and `git diff --check` passed. Added fixture cases exercise
the real adapter methods with a synthetic Bot, no network or authentication. Cancellation
released locally within 250 ms in the fixture; this is not the real T07 timing gate.

## Qualification bootstrap without campaign admission

`NativeLaunch.purpose` now distinguishes conformance work from campaign work and is
included in profile identity. Conformance calls require development charging and the
three essential real prerequisites (isolation, protected provider credentials, bounded
complete billing) before any model dispatch. They can then establish the remaining
plugin/helper/interrupt evidence. Campaigns still require all six proofs. Cross-purpose
proof reuse and helper lineage changes reject. This resolves a circular requirement to
already have a passed model-invocation test before being allowed to run that test.

Executed `pytest tests/test_native.py tests/test_records.py -q`: **44 passed**;
schema generation and lint passed. The new proof-parser tests use synthetic private
attestations and start no process/model. No essential live prerequisite has been certified.

## Bound checkpoint snapshots and streamed restoration

Clean-stop proof version 2 binds checkpoint identity and the exact world plus all
agent snapshot references. Old version-1 proofs require a new complete-boundary
attestation; none are silently upgraded. Commit rejects secret paths, case collisions,
file/parent collisions and mismatched snapshot sets. Large world blobs are verified
and copied with bounded memory, with verification again during staged copying.
Native artifact export/resume now binds the complete campaign/agent namespace.

Executed `uv run --frozen pytest tests/test_checkpoints_artifacts.py tests/test_native.py -q`:
**32 passed**; `uv run --frozen ruff check src tests evaluator/src` passed. The added
fixtures prohibit whole-blob reads, corrupt a blob between preflight and copy, verify
no failed destination is published and retain an independent previous restore.
Mixed agent/future-state, world, identity, legacy-proof and path/secret negatives
reject. These are local filesystem/synthetic snapshot tests, not authentic T08
complete game-and-agent restore evidence.

## D05: actual acquisition and interrupted profile preparation

The user authorized Codex to prepare both dedicated CurseForge profiles and E9E
server files. Actual bytes are outside the repository under
`C:/Users/Darian/.strata/downloads/`. No game, credential or live data is published.

| Artifact | Actual acquisition | SHA-256 |
|---|---|---|
| E9E client 1.27.0, 12,667,677 bytes | Official file 8161120; distribution's own URL redirects to `https://mediafilez.forgecdn.net/files/8161/120/Enigmatica9Expert-1.27.0.zip` | `04ece07ebd0ff973ea055195d7577194cc363feeb44cf973670218d89437922e` |
| E9E server 1.27.0, 12,668,057 bytes | Official page's download API redirects to `https://mediafilez.forgecdn.net/files/8161/123/Enigmatica9ExpertServer-1.27.0.zip` | `4667d8b9e430abb5306590350daab3d67c06ef0655a5a1feeb2f9eb19cecbeb7` |
| ServerStarter 2.4.0 | Exact official release URL in distributed `start-server.bat` | `70bec2771fd000209a8778b8457f231bf8e6244bb3d8dba6bb739c3662e099b4` |
| Current official CurseForge bootstrap installer, 3,022,768 bytes | Official site's standalone link; valid Authenticode Overwolf Ltd signature | `3e1bd2c1196cad683567cc13d394f80ccd4e2037c7cceca34569be1ab79b06de` |

`winget install --id Overwolf.CurseForge --exact --source winget --silent --disable-interactivity`
verified its separate installer hash and installed version **0.220.1-9343**, an older
package-manager build. Its actual executable is under
`C:/Users/Darian/AppData/Local/Programs/CurseForge/`. Updating it remains unverified.
Automatic approval review rejected a combined download/launch command with only
“blocked by policy.” A safer download-only command succeeded. The user then opened
CurseForge, but the native UI tool reported a physical Escape stop on the next
window discovery. No further native UI action was attempted.

Actual server archive manifest: Minecraft **1.19.2**, **forge-43.4.23**, release
**1.27.0**, 232 listed mod files; ZIP has 10,569 entries / 28,290,821 expanded bytes.
Read both distributed start scripts, server setup YAML and server guide without
executing them. The YAML pins the matching client archive and Forge installer
template; the batch script requests ServerStarter 2.4.0. The official Enigmatica
Java guide specifies Temurin 17 for this Minecraft generation. Java is not installed
yet, and the bootstrap has not run or accepted the Minecraft EULA.

Both actual ZIPs currently fail `inspect_archive` with `PRIVATE_INSTALLATION_CONTENT`:
eight members below `overrides/config/jei/world/`, including one `bookmarks.ini`, match
the broad `world` filename guard. This is an actual acquisition compatibility finding,
not a passed import. Inspect vendor-supplied configuration versus mutable runtime state
before a scoped policy correction; never remove the official members silently.
Both dedicated CurseForge profiles, complete mod downloads/installed inventory,
expert restart assertions and all T02/T03 game evidence remain pending.

## D05 resumed: actual profiles and install-only bootstrap

The user explicitly resumed desktop interaction. The official CurseForge app created
`Strata Vanilla 1.19.2` at `C:/Users/Darian/curseforge/minecraft/Instances/Strata Vanilla 1.19.2`
and imported the exact downloaded client ZIP at
`C:/Users/Darian/curseforge/minecraft/Instances/Enigmatica9Expert`; its UI name is now
`Strata E9E 1.27.0`. Vanilla has no mod loader. E9E metadata and UI show Minecraft
1.19.2 / Forge 43.4.23 / 232 mods. Actual client inventory matches all 232 manifest
files; all 226 shared server mods have identical SHA-256, with no missing/extra files.
The default directory names are retained; the profile metadata was changed through UI.

Temurin 17.0.20.1+1 x64 JRE was installed through the official winget package. Its
`java.exe` SHA-256 is `1977f302375adbb920d41dac65c7e22eb9c2ed8e1e8d6258964154ff16f14406`.
Source review of ServerStarter tag 2.4.0 at commit
`cea06f62f96efae422621414b187016a6f5af6c1` established its explicit `install` mode.
The actual archive's start scripts and YAML select the same pinned bootstrap.
The bounded Windows Job Object run used `java -jar serverstarter-2.4.0.jar install`
in `C:/Users/Darian/.strata/servers/e9e-1.27.0`, with `false` supplied at the EULA
prompt. Exit 0, successful Forge installer output, lock metadata and loader files
were verified. No EULA file was accepted and no game/world was started.

Private evidence under `C:/Users/Darian/.strata/evidence/2026-09-18-provisioning/`:
`e9e-install-plan.json`, stdout/stderr logs, `e9e-installed-mods.json`,
`e9e-client-mods.json`, and `e9e-bootstrap-tree.json`. The latter inventories
18,121 files / 572,768,937 bytes. Fifteen bootstrap filenames retain URL encoding;
comparison normalizes URI names only, retaining actual filenames in evidence.
Six of the distribution's eleven configured client exclusions occur in the 232-file
manifest, producing 226 server JARs. Complete role inventory/provenance and cold
restart/expert assertions are still required before sealing or T02 completion.

The official vanilla server was downloaded from the URL in CurseForge's Mojang
version metadata. SHA-1 `f69c284232d7c7580bd89a5a4931c3581eae1378` and SHA-256
`b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96` were recorded;
it is prepared at `C:/Users/Darian/.strata/servers/vanilla-1.19.2/server.jar`.
The installed vanilla client SHA-1 also matches the Mojang metadata:
`055b30d860ead928cba3849ba920c88b6950b654`.

Both official E9E archives include the same initial 52-byte JEI bookmark at
`overrides/config/jei/world/local/New_World/bookmarks.ini`, SHA-256
`5e7d6cda8873a16651e84c1306716b53eff5ccb7aa95139796a7f1552e485448`.
It is immutable vendor initial state, not player-learned state. `pack_policies.py`
now records exactly eight allowed paths with kind/content checks. Default scanning
stays closed; altered bookmark content, unlisted paths and private/credential paths
still reject. The same rule applies at archive, installed inventory and materialization.
No official content was deleted. The actual receipt is ACQUIRED under private
`C:/Users/Darian/.strata/operator/provisioning`, request `e9e-1270-20260918`,
receipt `cas:sha256:02d3c5f17f21c95f1f840d03b88e48d620ad783a8a344354e6df0060da680795`;
it is not a sealed or game-qualified profile.

Executed `uv run --frozen pytest -q`: **176 passed** (two Typer deprecations),
including **20 provisioning tests**. Python lint passed. No inference calls,
gameplay, EULA acceptance, authenticated reference run or expert cold restart occurred.

## Authentication dependency and credential-cache remediation

The [upstream UUID advisory](https://github.com/advisories/GHSA-w5hq-g745-h8pq)
identifies 11.1.1 as a patched CommonJS-capable release. Source inspection of both
installed consumers found standard `uuid.v4()` calls. The exact override retains
Minecraft protocol 1.68.0 and removes the two vulnerable UUID versions;
`npm ls uuid --all` shows 11.1.1 for both consumers. `npm audit --json` reports
zero findings. Actual consumer-module loading and UUID v3/v5/v6 supplied-buffer
rejection are covered in `authentication_dependencies.test.ts`.

The operator initializer uses prismarine-auth 3.1.1 with the same live/Nintendo
Microsoft flow as pinned minecraft-protocol. Its cache factory replaces upstream
FileCache's reset-on-corruption and directory fallback with explicit rejection and
atomic private writes. One account label is bound to the verified Java profile;
changed identity, absent profile/certificate, cancelled result or device prompt
in a worker prevents connection. Supported protocol custom-auth callbacks retain
the pinned upstream session/certificate handoff. All of these files and the ACL
helper are hashed into the backend identity; no cohort has been started.

Windows ACL creation/verification uses native CreateDirectoryW with an explicit
protected security descriptor, then owner/DACL/ACE checks for the current operator
and SYSTEM only. Existing weakened ACLs, NULL/missing DACLs, hardlinks and reparse
paths reject. The first PowerShell-file implementation was blocked by local script
policy; the final implementation uses the existing pinned Python runtime directly
and changes no security or execution policy. Tests verified real Windows directory
and child permissions, including a deliberately added Everyone read grant. This
does not prevent another process with the same operator identity from reading the
cache; adversarial filesystem/process/network isolation remains unqualified.

`npm test --prefix backends/mineflayer`: **58 passed** after correcting two synthetic
gesture fixtures to initialize the new authentication cancellation controller.
`uv run --frozen pytest tests/test_gameplay_package.py -q`: **1 passed**, and the
public bundle contains no auth initializer/cache/provider code. Python/helper lint
and diff whitespace checks passed. Microsoft token/profile tests use synthetic
providers and create no remote account/session. A separate real initializer
request produced an operator device-code prompt in the protected external cache;
completion and actual Minecraft server authentication remain pending.


## E9E expert-mode preparation inspection

The actual client/server distributions have `defaultmode: expert` in
`config/configswapper.json`; the missing initial root `mode.json` is not evidence
that the intended release defaults to normal. Reviewed ConfigSwapper source commit
`21ba0bfedeabcc54dec93f304e69c7e61b683330` selects that default and writes mode state
in its constructor, then reapplies overlays after loading/server start. Its build
version is 3.2 and the installed JAR timestamp is 2023-04-04T23:32:51+0200, agreeing
with the source commit date; no reproducible-build equivalence is claimed.

The inspector binds six actual files and 260 overlay files / 574,683 bytes to
release hashes. Overlay inventory digest:
`aec96aed5745b8681f8e12d8e1e85ce60ddee39e417fbda5e95d30aa655b538b`.
Both actual role setup reports contain eight passing file checks, with no initialized
mode, loaded-runtime claim, or passed game gate. They are stored outside the repo
as `e9e-server-mode-setup.json` and `e9e-client-mode-setup.json` in the existing
private provisioning evidence directory. Twelve synthetic tests passed for scope,
no mutation, normal/unknown/duplicate/malformed JSON, altered release/extra overlay,
TOML subset/type/list/quoted-key semantics, exact non-TOML replacement, missing and
malformed effective config, hardlinks, traversal and bounded files. The command
returns exit 2 on file failure and never changes aggregate T02 from `not_run`.

Explicit expert initialization before baseline creation, cold restart, loaded
config, actual furnace recipe, correct quest/team state and player/reference parity
remain open. See the release-specific operator procedure for exact IDs and paths.
The worker device authentication request timed out; no authenticated worker, game,
model invocation or EULA acceptance resulted.


## First authenticated vanilla server/worker evidence

The user explicitly accepted the Minecraft EULA and authorized both file edits.
The Java-owning account completed worker authentication in the separate private
`avatar-1-java` cache. A prior account had no Java entitlement; no account switch
was silently applied to an existing bound profile. Corrected the pinned provider's
inaccurate certificate type declaration using its actual runtime decoder, then
verified real profile/certificate availability without printing their contents.

Private evidence directory: `C:/Users/Darian/.strata/evidence/2026-09-18-vanilla-boot-01/`.
The reviewed launch plan uses the verified official server JAR and pinned Java,
loopback port 25565, online authentication, survival/normal, manual seed 713371337,
view/simulation distances 10 and 2 GiB maximum heap. No model or scored campaign
was launched. The server reached readiness, accepted an authenticated worker and
cleanly stopped at 484.969 s, exit 0, with all dimension-save messages and no force.

Initial scoped observations included live coordinates, health, inventory slots
and captured-region pagination. Look and grass-dig acknowledgements completed;
these alone do not establish independent authoritative resource/mechanics parity.
Two movement failures before emission exposed missing `game.minY` in the filtered
planner facade. The uneven-terrain regression now covers that upstream branch.
An explicit development intervention stopped the old worker; process and network
checks proved it gone before the stale lock was removed. The same journal was
reopened at epoch 2 with fresh grant/connection/observations and retained primitive
costs. A pre-acceptance revision conflict was retained, then a new movement completed
with 18 motor events. Cancelling a return movement after 150 ms took 20.709 ms round
trip, retained 3 events, closed the connection and required resync. Duplicate action
submission returned its terminal cancellation receipt without redispatch.

The evidence directory includes both epoch capability manifests, request/receipt
files, delivered observation pages, cancellation timing, plan, stdout/stderr and
summary. Actions SQLite remains in the separate protected worker directory. No
server/private evaluator outcome, Minecraft username, credentials or game bytes
are published here. Manual reconnection is not automatic recovery qualification;
one responsive cancellation does not qualify the complete watchdog envelope.
Full recipe/craft/container/resource/LOS/recovery/scoring/host cases remain open.

The exact E9E startup follows immediately. Root `mode.json` is explicitly expert
before world creation in the server and dedicated client. The only bootstrap YAML
change disables autoRestart; the original is preserved and both source-supported
launch path and changes are in a private CAS review. No content-mod or recipe changes.
E9E stdout currently reports expert recipe processing, but full mode/recipe/quest/
team checks, cold restart, independent player reference and API conformance remain
unrun. Logs remain private at `C:/Users/Darian/.strata/evidence/2026-09-18-e9e-boot-01/`.

Verification after changes: **190 Python**, **63 Node** tests passed; strict worker
build and lint passed. The initial interactive bootstrap fixture exposed a Windows
CPython finalization race; its corrected process lifecycle passed all 22 process/
native tests and the actual vanilla clean stop. No inference calls or charges.


## E9E cold restart, file findings and authentic compatibility failure

Both bounded exact E9E boots reached readiness and cleanly stopped with all dimension
save messages: exit 0, complete logs, no force, 259.469 s and 359.203 s. Private
reports are under `C:/Users/Darian/.strata/evidence/2026-09-18-e9e-boot-01/` and
`.../2026-09-18-e9e-boot-02/`. Effective inspections after both stops gave **263 pass,
5 fail**, with no check/result/hash differences. Four target files are absent:
`config/bhmenu-client.toml`, `config/nomoreworldsettings-client.toml`,
`world/serverconfig/inventorysorter-server.toml`, and
`world/serverconfig/sophisticatedcore-server.toml`. The Create overlay expects absent
`logistics.defaultExtractionLimit`, `schematics.schematicannon.schematicannonGunpowderWorth`
and `schematics.schematicannon.schematicannonFuelUsage`. No vendor config was deleted
or changed to suppress these findings. Primary config/recipe/quest/reference acceptance
remains incomplete and no template was sealed.

The actual authenticated unextended Mineflayer handshake was rejected because the
server requires Forge. The exact Forge 43.4.23 sources JAR from the official Maven
repository was reviewed (SHA-256
`663e58cdde75ce06f4713cfcedea4414c39d17adcfddcfa81c6da5adcd59102f`). The operator-only
FML3 decoder implements bounded wrapper/mod-data/mod-list parsing. Four synthetic
negative/positive tests pass, including invalid UTF-8, noncanonical/oversized varints,
duplicate IDs, trailing/truncated data, FML2 confusion and unsupported channels.

A separate bounded operator probe first recorded unsupported `quark:main` login data.
A second passive probe received the FML3 offers without acknowledging unknown channels
or submitting a client mod-list claim: **233 mods, 111 channels, 39 registries and two
custom datapack registries**. It deliberately disconnected before spawn. This proves
metadata decoding against the actual distribution, not registry installation, Forge
join or any machine/recipe/container mechanic. Raw payloads are private evidence only.
`mineflayer-handshake-diagnostic.json`, `fml3-offer-diagnostic.json`,
`fml3-offer-diagnostic-02.json`, `effective-mode.json` and the cold-restart comparison
retain successes and failures. T03/G0 now explicitly fail on the handshake requirement;
remaining compact cases and complete expert acceptance remain unrun. All game processes
were stopped after these bounded checks; no inference was spent.


## Read-only Forge telemetry and runtime expert recipe evidence

- Added `java/forge1192-telemetry` and the private Python spool inspector. Exact
  Forge 43.4.23 / official 1.19.2 mappings build with Temurin JDK 17.0.20.1+1,
  ForgeGradle 6.0.42 and hash-pinned Gradle 8.8. Installed the matching JDK under
  existing dependency/provisioning authorization. Wrapper, compiler, eight
  Forge-managed inputs, dependency versions and Maven verification hashes are
  pinned; the final JAR hash is
  `745d47d2fdad6d6b426c31b2d9b9e3494bfe9a86e12b77541a4f97ca7817c26d`.
- The module has no commands, client channels or state setters. It writes bounded
  evaluator-only boot/tick/recipe/raw-craft records through a durable single writer.
  Raw callbacks explicitly cannot score. Private inspection rejects sequence/scope/
  boot/clock corruption, partial tails and missing clean stop. Same-user filesystem
  checks are not a qualified isolation boundary or authenticated transport.
- Actual instrumented E9E runs 01/02/03 all reached readiness and exited 0 after
  clean stops, with complete logs and no forced termination: 184.422 / 184.454 /
  184.391 seconds. Run 01 exposed missing resource metadata; added `pack.mcmeta`
  and retained the original JAR/logs. Runs 02/03 used identical final JAR bytes:
  67/63 records, 1296/1228 observed server ticks, distinct boot IDs and identical
  runtime recipe snapshots. Their six exact furnace assertions pass: expert
  shaped 3x3 recipe, one furnace output, five andesite plus three polished andesite,
  empty center, and no vanilla furnace recipe. No player joined these runs.
- These are M0.3.2/M3.1a partial runtime checks, not player crafting, quest/team
  verification, private predicate provenance, reference parity, overhead, a soak
  or a G0/T02/T03/T10 pass. The instrumented installation has a separate identity;
  no vendor content mod or recipe was removed/replaced. Added instrumentation is
  retained in the development server and private evidence, not in a sealed pack.
- Source review of exact Forge key handling exposed an earlier planner error:
  UNIVERSAL/custom contexts and different modifier lists were treated as disjoint.
  Corrected conservative physical/context conflicts, including modifier-key
  activation and unknown keysym/scancode aliases. Five regression cases pass;
  actual client effect/restart T05 remains open (M1.1/C10/C11).
- Verification: `uv run pytest -q` **209 passed**, two existing Typer deprecations;
  `uv run ruff check src evaluator tests tools` passed; exact Gradle build passed,
  **5 Java tests passed**; `git diff --check` passed with line-ending notices.
  SPEC section 16 now points to this ledger rather than its stale initial
  documentation-only execution statement. No acceptance case was removed.
- Evidence: `C:/Users/Darian/.strata/evidence/2026-09-18-e9e-telemetry-{01,02,03}/`,
  private spool under `.strata/telemetry/e9e-development-{01,02,03}/`, and
  [runbook](../operations/forge-telemetry.md). Affected F01/F05/F06/F10/F16,
  N01/N03/N06/N08, C04/C10/C11/C18/C24. All server processes stopped; no model
  inference/spend. Next: actual Forge settings extension, provenance adapters,
  telemetry identity/supervisor integration and the retained compatibility gates.


## Forge client binding discovery foundation

- Added the separately identified `java/forge1192-client` module and
  [runbook](../operations/forge-client-settings.md), splitting M1.1a into
  discovery (a.1, implemented_unverified) and native transactions (a.2, not_started).
  Actual effects/restart/isolation remain M1.1b. No keybinding capability is advertised.
- Discovery executes on the client thread after mod loading and emits one bounded
  optional operator snapshot: runtime/default keys, modifiers, native/custom
  contexts, labels, stable owner/translation/occurrence IDs, persisted key fields
  and ambiguity. Explicit mapped vanilla Options references survive reobfuscation;
  arbitrary reflection/translation prefixes do not establish mod ownership.
  Unknown owners, all mutations, tested keys and restart claims remain disabled.
- Missing first-launch options files yield explicit unknown persistence without
  creating/editing options. Four synthetic Java options/identity tests passed;
  exact Forge reobfuscated build succeeded under existing locked dependencies.
  Client JAR SHA-256: `6947930421e1c4d5b52481517e3197fe861658e9d2951cce2a567a1be787851f`.
- Confirmed no Java client was running, added only this instrumentation JAR to the
  dedicated E9E development profile, and retained the binary plus preparation
  receipt under `.strata/evidence/2026-09-18-e9e-client-discovery-01/`. No vendor mod
  changed. The profile is now instrumented; this is not a sealed baseline or a
  live settings pass. Native desktop control remains paused after the user's
  Escape; an explicit resume question is pending. No UI operation or client launch
  occurred during this work. Continue native transaction/evidence work while waiting.
- F06/F16/N01/N06 and C10/C11 advanced partially. T05/G1 remain not_run. The latest
  Python full run remains 209 passes; telemetry Java 5 plus client Java 4 passed
  separately. All game processes are stopped, inference spend remains zero.

## Desktop recovery and actual client discovery

The user clarified that no physical Escape was pressed and explicitly authorized
continued desktop testing. After earlier repeated stop errors, a fresh supported
Node REPL reset, `@oai/sky` import and application listing succeeded. UI navigation
and inputs then worked through two actual client launches. No helper binary,
private protocol or alternate UI automation was used. The earlier stop signal's
cause remains unknown; the earlier attribution to a user Escape is not established.

Environment: dedicated CurseForge E9E 1.27.0 profile, Minecraft 1.19.2, Forge
43.4.23, Temurin JRE 17.0.20.1+1, existing 4096 MiB maximum heap, and unchanged
instrumentation JAR `6947930421e1c4d5b52481517e3197fe861658e9d2951cce2a567a1be787851f`.
The pinned `javaw.exe` hash is
`326c477cf91039f50f4ffb507801972882ea09546bd9e2c9f36e9d32a5aa7a97`.
Both boots reached the rendered title screen, which reported 240 loaded mods.
No world was entered. Ordinary Quit was selected for both boots; each game's
process and Crash Assistant monitor exited before final logs were archived.
These operator checks used no model inference or additional account sign-in.

First export SHA-256:
`368bba2f9de2e81241b7ed478a2f92e6eb5357b07164792dc53f5a4515fc4262`.
It contains 253 bindings: 34 explicit vanilla references, 219 unresolved mod
owners and 31 custom/unknown contexts. There are no ambiguous occurrence or
persisted-name flags. Its options file existed but contained zero key lines,
so all 253 persisted values correctly remained unknown. The sampled rendered
Controls matched WASD, Space, left Shift/Control, mouse attack/use, and unbound
Curios. No key was reassigned. Controls/Options Done caused the game itself to
save 253 key fields. The saved options SHA-256 was
`014fdfa01069c51629c331df769c611b778bf0479460ef58b833326573001949`.

Second export SHA-256:
`9f72f6d7e7ebe7f35505d652f7cd41ee31943b6d7e2d67d9d4b1b80883b575fa`.
Six cold-restart assertions passed: stable identifiers; unchanged runtime/default/
owner/context fields; all 253 persisted values known; all runtime values equal
their persisted values; saved options hash equals the second snapshot's hash;
and all unqualified capability flags remain disabled. This is operator cold-boot
discovery/persistence evidence, not a worker-controlled transaction/restart or
in-game input-effect pass.

The new [operator audit](../../src/mcbench/client_discovery.py) validates bounded
diagnostic records and leaves authentication, effects and gate qualification
explicitly false/unrun. It detects corrupt identities, duplicate/unknown fields,
unsupported authority claims, backend/context inconsistencies and options-file
changes, without copying unrelated options values. The actual module CLI audited
both live files successfully. Executed:

```text
uv run --frozen pytest tests/test_client_discovery.py tests/test_controls.py tests/test_gameplay_package.py -q
28 passed (13 new audit cases)
uv run --frozen ruff check src/mcbench/client_discovery.py tests/test_client_discovery.py
All checks passed
git diff --check
pass (existing line-ending normalization warnings only)
```

Private evidence resides in
`C:\Users\Darian\.strata\evidence\2026-09-18-e9e-client-discovery-01\`:
raw exports and audits, `cold-restart-comparison.json`, matching launch receipts,
saved options, two final logs, Controls/title screenshots, stop receipts and
`evidence-hashes.json`. Logs and game files remain outside the repository.

Retained findings: opening Controls emitted GL `65540: Invalid scancode -1`;
source attribution and uninstrumented parity remain unresolved. CurseForge
regenerates Launcher Java settings on each Play, so the pinned executable and
diagnostic property were restored through UI and compared before the second boot.
Opening the executable without CurseForge's managed directory showed a different
login context; it was closed without authentication input. No cache was copied.

M1.1a.1 remains `implemented_unverified`: mod ownership, complete fingerprints and
remaining discovery failure paths are open. Native CAS, input release/effects,
tested physical pool, worker-managed repair/restart, cross-client isolation and
charged in-play continuity remain M1.1a.2/M1.1b. T05/G1 remain `not_run`; the actual
Mineflayer/E9E handshake failure remains T03/G0 `fail`. All game processes stopped.

## Native settings transaction core and desktop pause

M1.1a.2.1 now implements the Java private transaction store, strict journal parser,
profile lock and owned-field file writer. Its receipts distinguish prepared,
applied-pending-verification, rollback-prepared, rolled-back and rollback-conflict.
No commit operation or gameplay capability is advertised. Restarts replay journal
state, never the forward mutation. Pending snapshots cannot consume recovery
headroom. Corrupt/partial/blank journal frames and repeated profile headers fail
closed; expected revisions, duplicate request identities and protected bindings
are checked before mutation. Owned-field writes preserve unrelated bytes and
line endings, including rejecting Unicode separators that could otherwise confuse
the options parser and patcher.

M1.1a.2.2 now has a compiled native adapter limited to Curios' exact JAR and public
registration object. It uses mapped client-thread setters/reset/release and hashes
loaded mod artifacts. M1.1a.2.3 has a development-only title-screen round-trip
probe, but **no actual game execution yet**. Curios must initially be unbound;
F13 is used only as a settings-encoding sample before immediate rollback. It is
not in a tested physical-key pool. The prior discovery-only JAR remains installed.

Executed on Windows 11, pinned Temurin JDK 17.0.20.1+1, Gradle 8.8,
ForgeGradle 6.0.42 and Minecraft 1.19.2 / Forge 43.4.23:

```text
.\gradlew.bat :forge1192-client:test :forge1192-client:build --no-daemon --console plain
BUILD SUCCESSFUL; 24 tests, zero failures/errors
git diff --check
pass; existing tracked-file line-ending warnings only
```

The 20 transaction tests use a **synthetic runtime** with real Windows temporary
files and profile locks; the four existing options-parser tests also pass. Cases
include stale revisions, protected/duplicate/unsupported bindings, exact retries,
interruption between runtime and file writes, reopen/recovery, foreign runtime
and file changes, lock contention across journal roots, profile identity,
corrupt tails, quota rejection before mutation, non-client-thread rejection,
strict JSON and Unicode line boundaries. They do not establish actual Minecraft
effects, OS input release, cross-client isolation or power-loss durability.

Final development JAR SHA-256:
`b4001b77c3a54fb754b4c21af255008550287d7960b9e885f4eb2c45e388cb8b`.
Private build log, JUnit XML, JAR and hashes are retained at
`C:\Users\Darian\.strata\evidence\2026-09-18-native-settings-unit-01\`.
The installed profile still uses discovery JAR
`6947930421e1c4d5b52481517e3197fe861658e9d2951cce2a567a1be787851f`.

The supported desktop helper again listed windows, restored CurseForge and
opened its managed Minecraft Launcher. Before launching the game or installing
the new JAR, the user explicitly paused desktop control because they were using
the computer. No further desktop calls were made after that message. This pause
is distinct from the earlier unexplained stop-state report. Background source,
tests and documentation continued; no model inference was dispatched.

Remaining: actual native transactions and interrupted recovery, qualified foreign
writer exclusion/CAS and durable filesystem deployment, physical/effect/context
checks, worker-managed restart, controller/CLI integration, charged repair and
cross-client isolation. T05/G1 stay `not_run`; T03/G0 retain the Mineflayer/E9E
failure. Resume desktop work only when the user resumes it; other implementation
can continue under the active long-horizon goal.

## Transaction-aware private bridge: JVM/HTTP evidence, synthetic runtime

M1.1a.2.4 adds a private native protocol and session-fenced loopback transport
backed by the same Java transaction store, plus the Python operator client/CLI.
Explicit transaction IDs persist across HTTP requests and JVM restarts. Request
IDs identify transient accepted/completed/failed transport responses; recovery
queries the durable transaction ID rather than replaying a forward write.

The native client integration is opt-in via `strata.settingsBridgeDirectory`.
It remains restricted to title-screen development and advertises `supported=false`.
Its random per-boot bearer/session descriptor is private credential material,
never an evidence artifact. HTTP threads authenticate/validate/queue only; client
ticks dispatch. The protocol limits body size, response size, pending jobs and
cached responses; deadlines are rechecked using monotonic time before dispatch.
Queries while a transaction is pending do not consume recovery journal headroom.
There is no verified commit operation or gameplay settings capability.

Executed with pinned JDK 17.0.20.1+1 / Gradle 8.8 / Forge 43.4.23, Windows 11:

```text
.\gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
BUILD SUCCESSFUL; 29 tests; zero failures/errors

uv run --frozen pytest tests/test_native_settings.py tests/test_native_settings_jvm.py tests/test_controls.py tests/test_client_discovery.py tests/test_gameplay_package.py -q
47 passed in 6.04s

uv run --frozen ruff check src/mcbench/native_settings.py tests/test_native_settings.py tests/test_native_settings_jvm.py
All checks passed
```

The Python integration command explicitly set `STRATA_SETTINGS_TEST_JAVA` to the
pinned JDK's `bin/java.exe` and `STRATA_SETTINGS_TEST_CLASSPATH` to the generated
`java/forge1192-client/build/test-classpath.txt`. Without those explicit inputs the
JVM tests are skipped; a default Python run must not claim they were exercised.

The five Java HTTP tests exercise actual local HTTP and production protocol/store
with a synthetic runtime: auth/session/schema rejection, body/queue/deadline
limits, exact and reordered-request deduplication, changed-request conflict,
pending inspection, rollback, exception redaction, browser-Origin rejection and
shutdown fencing. The four Python/JVM cases launch the actual test JVM and cover:

- Apply/status/dedup/rollback with actual runtime/file agreement and exact restore;
  Controls refuses this unqualified snapshot with `CAPABILITY_MISSING`.
- Kill/reopen the test JVM: a fresh session recovers the pending journal without
  assuming commit or repeating the forward write.
- Foreign options edit: rollback fails closed and preserves the foreign bytes.
- Discard a real POST acknowledgment: Python reports uncertainty, sends no second
  apply, queries the transaction, then rolls it back.

The 15 Python-only cases cover strict request/response validation, connection
identity, one-POST polling, uncertain response handling, forbidden external
addresses/invalid ports, duplicate/nonfinite JSON and credential redaction. A
follow-up library-boundary redaction fix was tested by rerunning those **15 tests**
successfully; targeted Ruff and `git diff --check` also passed. This later narrow
rerun does not imply another full 47-test run.

Final JAR SHA-256:
`2ce213d9a0866fb9ba83d1957d33965bea63dab9f31d0c3be16f8528b6d96cc5`.
The JAR inventory excludes synthetic fixture/test classes. The installed JRE
lists `jdk.httpserver@17.0.20.1`; authentic Forge loading of the new transport is
still unverified. Private evidence archive:
`C:\Users\Darian\.strata\evidence\2026-09-18-native-settings-bridge-01\`.
It contains JUnit XML, the JAR, four synthetic transaction journals, the executed
command/result summary and hashes. No connection descriptors or credentials were
copied. The source/gameplay packaging allowlist continues excluding operator
Python modules and private connection material.

No desktop tool was used after the user paused it. No game process was launched,
new JAR installed, account used or model inference dispatched. These real process
and transport tests use **synthetic keys**, so they do not pass native Minecraft
transactions/effects, physical input, worker restart, full isolation or T05/G1.
The public Controls workflow still needs its qualified discovery projection,
effect/restart provider, verified commit, reconfiguration/accounting integration
and scoped gameplay CLI. M1.1a.2.4 is `implemented_unverified`; T03/G0 retain the
authentic Mineflayer/E9E failure. Continue those implementation paths, keeping live
desktop work paused until the user resumes.

## Host settings fencing and evidence validation

M1.1c.1/c.2 strengthen the Python settings workflow; these are operator services,
not a qualified Minecraft control capability. A version 2 plan binds its avatar,
profile, requested controls, metadata/pool policy, original keymap and required
effect matrix. Profile file locks exclude cooperating controller processes using
the same operator database, while persistent SQL holds survive crashes and failed
rollback. Legacy active plans without profile authority block admission rather
than being silently upgraded or replayed. Actual subprocess tests exercise normal
and crash release of the Windows operation lock.

The workflow corrects two previous discrepancies against SPEC 8.2: new repairs
cannot bypass a failed rollback, and an unrelated concurrent edit cannot be
accepted as a successful restore. Only transaction-owned fields may be restored;
foreign state remains unchanged and input requires operator recovery. Metadata
or qualification drift, stale plans, changed idempotency intent and failed final
release also prevent commit. No-change plans do not write or restart a client.

Every changed control and potential competitor requires transaction/plan-bound
checks before and after restart. GUI coverage includes chat; unknown/universal
contexts conservatively include game, GUI and chat. The workflow reads actual
content-addressed proof and source bytes, checks hashes and exact identities,
and enforces a 64 KiB proof-object / 32 MiB transaction-read allowance. Missing,
replayed, duplicate, malformed or unverified-context checks fail. Production
rejects example proofs; explicit simulation mode persists in its database and
cannot reopen as production. These structural checks do not authenticate a
physical-effect producer or prove that Minecraft performed an effect.

Executed on Windows 11 / Python 3.12.14:

```text
uv run --frozen pytest tests/test_controls.py tests/test_controls_fencing.py tests/test_storage_controller.py tests/test_checkpoints_artifacts.py -q
87 passed in 5.70s

uv run --frozen pytest tests/test_native_settings_jvm.py -q
4 passed in 5.57s
```

The separate JVM command explicitly supplied the pinned JDK and generated test
classpath described above. It retained the native bridge's unsupported-capability
rejection and synthetic transport/recovery checks; it did not run Minecraft.

Final review then reproduced a stale committed-rollback retry bug: the first
attempt rejected a newer revision, but changing the phase to failed lost the
original revision guard. A reopened-database regression and a no-drift release
retry regression initially yielded **two failed, 36 deselected in 0.33s**.
Failed receipts now preserve the committed revision through every retry. Matching
key values cannot authorize undoing a newer revision. Ambiguous post-restore
failure remains fenced pending operator resolution.

After that correction:

```text
uv run --frozen pytest tests/test_controls.py tests/test_controls_fencing.py -q
52 passed in 1.59s

uv run --frozen ruff check src/mcbench/controls.py src/mcbench/control_lock.py src/mcbench/storage.py tests/test_controls.py tests/test_controls_fencing.py
All checks passed
```

No full Python/Java rerun is implied. Private archive:
`C:\Users\Darian\.strata\evidence\2026-09-18-settings-workflow-01\`.
It contains the final synthetic transaction database, ten example proof/witness
blobs, source hashes, an artifact hash inventory and a command/result summary
transcribed from observed tool output. It contains no connection credentials.
The [workflow contract](../operations/settings-workflow.md) records the private
adapter/evidence interface and remaining production work.

Outstanding: qualified native adapter and verified commit, authenticated real
effect/restart producer, per-avatar reconfiguration/action-lease integration,
time/cost charging, public patch/CLI projection, isolation and cross-client
conformance. T05/G1 remain `not_run`; T03/G0 retain the authentic Mineflayer/E9E
failure. Desktop interaction remains paused by the user. This work launched no
game, changed no installed profile and dispatched no model inference.

## Per-avatar repair coordination: synthetic service integration

M1.1c.3.1 connects the private controller, settings workflow, CAS, budget ledger
and clock ledger. `Reconfigurations` requires a before-start immutable repair
policy, a planned settings transaction and a reserved tool-budget operation.
Requesting repair durably fences only that avatar's controller input authority.
A bound release receipt is required before RECONFIGURING; a typed fresh
post-settings observation and settled costs are required before a new input
generation/lease is issued. Cognitive probes reject repair. Failures, stale
readiness, UTC/monotonic expiry, owner changes and unknown/overrun budgets keep
input fenced. Recovery permits rollback without replaying uncertain writes.

Controller startup read grants survive readiness; `act` requires ready avatar
authority. Replacing an input-bearing grant revokes the previous one. Whole-team
readiness cannot bypass a pending repair. Profile reservations and tool-budget
operation IDs cannot be reused across competing repairs. These checks apply to
the controller API; the development Mineflayer gateway still uses its separate
grant and does not consult these new records.

Clock interval ingestion retains the normal whole-team active/reserved exposure
and actual supplied tick counts during repairs. Separate attribution records
identify holds active at ingestion; they neither double count exposure nor claim
exact repair-boundary timing. Duplicate ingestion retains the original tag.
Authoritative telemetry coverage and automatic all-call settlement are not yet
implemented. Synthetic usage is explicit in the retained simulation database.

Executed on Windows 11 / Python 3.12.14, with synthetic settings and worker proofs:

```text
uv run --frozen pytest tests/test_reconfiguration.py tests/test_storage_controller.py tests/test_budget_clocks.py -q
50 passed in 5.50s

uv run --frozen pytest tests/test_reconfiguration.py tests/test_controls.py tests/test_controls_fencing.py tests/test_storage_controller.py tests/test_budget_clocks.py tests/test_checkpoints_artifacts.py -q
122 passed in 8.29s
```

The expanded run includes settings success/rollback, controller grant scope,
concurrent profile requests, interrupted verification, controller takeover,
database reopening, fixed probe policy, clock attribution, scoped reservations
and retained budget overruns. Two later regressions check readiness that expires
during a slow adapter read and pre-ready/legacy authority. Their focused suite
passed **32 tests in 2.43s**. A final correction preserved read-only startup grants
through readiness, followed by:

```text
uv run --frozen pytest tests/test_reconfiguration.py tests/test_storage_controller.py -q
52 passed in 4.81s

uv run --frozen pytest tests/test_gameplay_package.py -q
1 passed in 0.30s

uv run --frozen ruff check src/mcbench/controller.py src/mcbench/reconfiguration.py src/mcbench/clocks.py tests/test_reconfiguration.py
All checks passed
```

No full Python or other-language rerun is implied. Private archive:
`C:\Users\Darian\.strata\evidence\2026-09-18-reconfiguration-01\`.
Three final test databases and their synthetic CAS objects preserve a completed
repair, clock attribution and interrupted-write rollback. The archive includes
source/artifact hashes and a command/result summary transcribed from observed
output, not raw pytest logs. No account credentials or native connection files
were copied. Gameplay packaging still contains only the explicit client allowlist.

Remaining: actual worker lease/cancellation transport, authenticated and qualified
stop/readiness producers, native verified commit/effects/restart, exact telemetry
coverage and all-call charges, public patch/CLI projection, terminal-campaign
repair resolution and full isolation. See the
[operator workflow](../operations/settings-workflow.md). This is partial service
integration and does not pass T05/T07/T11/T12 or G1. T03/G0 retain the authentic
Mineflayer/E9E failure. Desktop control remains paused; no game process, live
profile modification or inference dispatch occurred.
