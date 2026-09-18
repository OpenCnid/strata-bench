# Modpack provisioning and runtime research

> Architecture update, 2026-09-18 (D01): the user selected Mineflayer as the first control backend, with structured observations/actions. Direct Codex CLI/local commands are the default (D02); MCP and app-server are optional. Full-client-first proposals and prior review conclusions below are historical. Use [SPEC.md](../SPEC.md), [MILESTONES.md](../MILESTONES.md), and the [Mineflayer decision](mineflayer-backend.md) for current contracts and gates; source findings remain supporting evidence.

Research date: 2026-09-17. Scope: actual Minecraft Java clients and servers, vanilla and expert modpacks. This is a research/design report, not an implementation or a claim that any pack has passed a launch test here. No game, launcher, Java runtime, account, or mod was installed or changed during this research.

Evidence labels used below: **Verified** means primary documentation, release metadata, or repository source was inspected. **Recommended** is a proposed design decision. **Unproven** requires a real installation or acceptance test. A repository's advertised feature is evidence of its claim, not independent validation.

## Recommendation

Use **vanilla Java 1.19.2 plus Enigmatica 9: Expert on Minecraft 1.19.2 / Forge** as the first runtime family. Start with one client, then prove two independently controlled, genuinely rendered clients. Keep E6E 1.16.5 and E2E 1.12.2 as later compatibility tiers. The numbers 2, 6, and 9 identify pack generations; do not treat them as increasing difficulty levels.

The verified E9E candidate release is **1.27.0**, with [client file 8161120](https://www.curseforge.com/minecraft/modpacks/enigmatica9expert/files/8161120) and [server file 8161123](https://www.curseforge.com/minecraft/modpacks/enigmatica9expert/files/8161123), dated May 28, 2026. Its source tag records Forge **43.4.23**. This is enough to identify a candidate, but not a complete artifact lock: actual archives, resolved files, hashes, Java build, launcher version, and runtime behavior still need verification. [Tagged instance metadata](https://github.com/EnigmaticaModpacks/Enigmatica9/blob/d6bed3a552de25b3bc211856fcd276fbb35d1c43/minecraftinstance.json).

For the Windows MVP, use **the official CurseForge app for initial installation/import and account setup**; the user confirmed CurseForge + Forge during the research. Do not assume a documented unattended CurseForge CLI. The harness should adopt and validate a prepared installation; later provisioning can automate supported paths after they are demonstrated. **Prism is only a possible future optional adapter**, not a substitution for the user's selected workflow.

## Installer, loader, and game runtime are separate

**Verified:** Enigmatica's installation guide names the CurseForge app and GDLauncher as supported launchers. A launcher obtains a pack and launches Minecraft; Forge is the mod loader inside that installation. A server pack is not a playable graphical client. Forge documentation distinguishes the physical client, physical dedicated server, and logical server; a single-player client contains its own logical server. [Enigmatica installation](https://wiki.enigmatica.net/main/help-desk/guides/installation), [Forge sides](https://docs.minecraftforge.net/en/1.19.x/concepts/sides/).

There is a documentation freshness trap: the Enigmatica installation page says CurseForge is unavailable on Linux, while current CurseForge documentation lists Linux support on official Ubuntu distributions. Do not repeat the old platform limitation as current fact. Windows is the recommended first target because it matches the user's host and proposed onboarding, not because CurseForge has no Linux version. [Current CurseForge getting started](https://support.curseforge.com/support/solutions/articles/9000193488).

**Recommended:** keep four independently versioned adapter boundaries:

1. Artifact provisioner: obtains and verifies the actual distribution and its dependencies.
2. Launcher adapter: creates/adopts an instance, chooses Java/account, starts and supervises the process.
3. Game/control adapter: connects the chosen observation/action interface to that client.
4. Pack adapter: verifies expert mode, interprets quests and recipes, and validates progression.

A successful launcher process exit, open window, server socket, or Forge handshake alone is insufficient proof of a ready, controllable expert-pack run.

## Compatibility and support matrix

All rows remain **unproven by execution in this workspace**. The tiers below are recommended delivery order, not existing support claims.

| Profile | Verified family and candidate artifacts | Java baseline | Mode/progression evidence | Proposed support tier |
|---|---|---|---|---|
| Vanilla Java | Pin 1.19.2 for initial comparison; acquire official client/server metadata and hashes during implementation | 64-bit Java 17 | Vanilla survival settings and task predicates | Tier 0: control, launch, capture, restart, snapshot baseline |
| E9E | Minecraft 1.19.2, Forge; candidate pack 1.27.0, client 8161120, server 8161123; source tag Forge 43.4.23 | 64-bit Java 17 | KubeJS mode file, expert recipe and FTB Quests checks | Tier 1: first expert-pack acceptance target |
| E6E | Minecraft 1.16.5, Forge; verified candidate pack 1.12.0, client 6881856, server 6881857, Forge 36.2.39 | 64-bit Java 8 per Enigmatica guidance; newer Java is a separate tested variant | Official `/mode expert` and `/mode normal`; KubeJS mode file and quest state | Tier 2: separate control/loader compatibility gate |
| E2E | Minecraft 1.12.2, Forge; official release 1.92, client 7611218, server 7611227 | 64-bit Java 8 | Separate Expert distribution; legacy scripts and Better Questing conventions require a distinct adapter | Tier 3: legacy compatibility and progression gate |

Sources: [Java guidance](https://wiki.enigmatica.net/main/help-desk/guides/java), [E6E client 1.12.0](https://www.curseforge.com/minecraft/modpacks/enigmatica6expert/files/6881856), [E6E server 1.12.0](https://www.curseforge.com/minecraft/modpacks/enigmatica6expert/files/6881857), [E2E client 1.92](https://www.curseforge.com/minecraft/modpacks/enigmatica2expert/files/7611218), [E2E server 1.92](https://www.curseforge.com/minecraft/modpacks/enigmatica2expert/files/7611227).

E2E's older 1.90h release remains a verifiable historical candidate and explicitly records Forge 14.23.5.2860; current repository settings also record that loader. Do not present 1.90h as the newest release, or automatically infer that every future E2E release uses that exact loader. [1.90h metadata](https://www.curseforge.com/minecraft/modpacks/enigmatica2expert/files/5198802), [inspected settings](https://github.com/EnigmaticaModpacks/Enigmatica2Expert/blob/d9decf5ca09fc573010a0dd0053fbc34c0591a6d/settings.cfg).

## Expert mode must be proved

**Verified:** E6E's official page documents switching modes with `/mode normal` and `/mode expert`. Inspected E6 source reads `mode.json`, defaults to `normal` when absent, and assigns expert flags and a quest marker. E9 has both startup and server scripts reading the same mode setting, also defaulting to normal, and updates FTB quest mode markers when a player logs in. [E6E official description](https://www.curseforge.com/minecraft/modpacks/enigmatica6expert), [E6 mode source](https://github.com/EnigmaticaModpacks/Enigmatica6/blob/edf25e0f50ce6b8ff052f7d10ff3c748bb90eafe/kubejs/server_scripts/enigmatica/kubejs/packmode.js), [E9 startup mode source](https://github.com/EnigmaticaModpacks/Enigmatica9/blob/b633d20e43a1329cd7a19ea1a2825d6660e19a49/kubejs/startup_scripts/packmode.js), [E9 server mode source](https://github.com/EnigmaticaModpacks/Enigmatica9/blob/b633d20e43a1329cd7a19ea1a2825d6660e19a49/kubejs/server_scripts/packmode.js).

**Recommended:** prepare mode before creating the baseline world, then perform a cold restart. The release-specific adapter must validate the effective mode from runtime evidence, a known expert-only recipe difference, and the expected quest markers. Keep the client and server configuration consistent where required. The inspected source establishes why a missing mode file can silently select normal; it does not prove that an arbitrary release ZIP lacks its expert preset. Do not change modes during a scored run. For E2E, install the actual Expert release and validate its recipes/quests instead of inventing an E6-style switching command.

**Unproven:** precise release-specific mode migration behavior, whether a reload suffices, and all world/quest side effects. E9 startup scripts make cold restart the conservative contract. Administrative setup commands belong in provisioning evidence and must not silently become agent capabilities.

## Server packs and reproducible acquisition

**Verified:** Enigmatica's server guide says to obtain the server files, extract into an empty non-synchronized folder, install the appropriate Java, and run the supplied platform script. It describes EULA acceptance and a restart workaround. It also recognizes older ServerStarter layouts. [Server installation](https://wiki.enigmatica.net/main/help-desk/guides/server-installation).

The pack families differ:

- E2E's inspected source has `ServerStart.bat`, `ServerStartLinux.sh`, `settings.cfg`, and a server guide describing those launchers. [E2E guide](https://github.com/EnigmaticaModpacks/Enigmatica2Expert/blob/d9decf5ca09fc573010a0dd0053fbc34c0591a6d/SERVER_GUIDE.txt).
- E6/E9 have `server_files_expert/start-server.bat`, a shell counterpart, and `server-setup-config.yaml`. Their inspected scripts obtain ServerStarter 2.4.0. The YAML handles Forge installation, the CurseForge manifest, client-only exclusions, and JVM launch configuration. E6's launch form uses the Forge JAR; E9 uses Forge's generated OS argument file. [E6 server files](https://github.com/EnigmaticaModpacks/Enigmatica6/tree/7abe331f98d98b7b39132796c19ad1f2f1504a28/server_files_expert), [E9 server files](https://github.com/EnigmaticaModpacks/Enigmatica9/tree/d6bed3a552de25b3bc211856fcd276fbb35d1c43/server_files_expert).

**Critical source/distribution distinction:** the E6 source tag `1.12.0` resolves to `7abe331f98d98b7b39132796c19ad1f2f1504a28`, but its checked-in expert server YAML points at an E6E 1.11.0 archive. E9 tag `1.27.0` resolves to `d6bed3a552de25b3bc211856fcd276fbb35d1c43`, but its checked-in YAML points at E9E 1.26.0. Packaging may update those references, but that transformation was not verified. Therefore **inspect the actual distributed server ZIP and its resolved manifest before approving any lock**. Also, E6 moving master currently points at E6E 1.13.0 while the inspected CurseForge main file is 1.12.0. Neither cloning master nor selecting a source tag alone reproduces a published pack. [E6 tagged YAML](https://github.com/EnigmaticaModpacks/Enigmatica6/blob/7abe331f98d98b7b39132796c19ad1f2f1504a28/server_files_expert/server-setup-config.yaml), [E9 tagged YAML](https://github.com/EnigmaticaModpacks/Enigmatica9/blob/d6bed3a552de25b3bc211856fcd276fbb35d1c43/server_files_expert/server-setup-config.yaml).

**Recommended artifact contract:** produce a machine-readable lock containing:

- Pack project ID, exact release/file IDs, client and server archive hashes, acquisition source/time, and any source revision used as evidence.
- Minecraft version and distribution hashes; loader exact version and installer hash; all libraries/natives; Java vendor/build/architecture/hash; launcher version/hash.
- Every mod's project/file ID where available, filename, cryptographic hash, client/server role, and provenance. Record permitted omissions explicitly; client/server folders need not be byte-identical.
- Hashes of scripts, configs, default configs, quests, datapacks, resource packs, mode settings, and approved harness modifications. Record resolution, GUI scale, language, render/simulation distance, key bindings, resource-pack order, JVM flags, OS, and GPU driver separately as runtime configuration.
- World baseline/snapshot ID; seed and world-generator settings; difficulty and gamerules; account/UUID mapping without credentials; exact task specification and observation/action capability profile.

Resolve dependencies once, verify them, then run from a sealed local installation. Each run gets its own writable instance and world path. Preserve source manifests alongside the fully resolved inventory. No automatic updates or fallback to “latest.” Provisioning retries must be idempotent and resumable, and a missing exact artifact is an explicit failure rather than permission to substitute another version.

### Retrieval restrictions that affect implementation

**Verified platform behavior:** CurseForge authors can disable third-party distribution; the platform says its third-party API then withholds project/file access. API availability and a project's license are separate controls. The REST model exposes `allowModDistribution` and file/version information, but API metadata alone is not permission to redistribute a full installed game. [Distribution toggle](https://support.curseforge.com/support/solutions/articles/9000207877), [CurseForge REST API](https://docs.curseforge.com/rest-api/).

The official June 10, 2026 announcement states that direct `edge.forgecdn.net` downloads require a valid API key starting **July 16, 2026**, with unauthenticated requests returning 401. That date is past as of this report. It recommends the `x-api-key` header, and says the official app/website handle this for users. Actual enforcement against a test download was not probed here. Old server bootstrap scripts that fetch naked CDN URLs need a compatibility test against the current service. [CurseForge CDN authentication announcement](https://blog.curseforge.com/introducing-api-key-authentication-for-curseforge-file-downloads/).

**Recommended:** support official launcher acquisition, authorized API acquisition, and an explicit user-supplied artifact import path. A denied/missing URL yields an actionable acquisition state, not a guessed CDN URL, unauthorized mirror, or secret borrowed API key. Keep private keys out of prompts, launch logs, and URLs. Distribute the harness, manifests, and permitted original adapters separately from Minecraft and restricted third-party artifacts. Minecraft's EULA distinguishes distributable mods from redistributing a modded copy of the game; this report records that source requirement rather than offering a legal opinion. [Minecraft EULA](https://www.minecraft.net/en-us/eula).

## Launching and authenticated identities

**Verified optional alternative:** Prism documents CLI arguments for application root (`--dir`), instance (`--launch`), account profile (`--profile`), server (`--server`), and ZIP import (`--import`). The documented `--alive` writes a launcher heartbeat file; it does not prove Minecraft or a world is ready. These controls make Prism a plausible future launcher adapter, but importing a pack and any required manual downloads still need validation. [Prism CLI](https://prismlauncher.org/wiki/getting-started/command-line-interface/), [Prism modpack import](https://prismlauncher.org/wiki/getting-started/download-modpacks/).

**Recommended Windows/CurseForge MVP workflow:** user completes official account login and any required EULA interaction; the provisioner validates the selected installed instance; the launcher adapter starts it through a verified supported flow; the supervisor locates the actual Java child process and rendered surface; the game adapter reports its handshake and readiness. If no reliable unattended launch path is proved, initial startup stays an explicit assisted step rather than a fabricated automation guarantee. Subsequent crash recovery must accurately report when renewed login or launcher interaction is required.

Authentication is a first-class resource: maintain a credential-free account slot ledger with profile identifier, UUID, last successful validation, availability, and current lease. Require unique valid identities for simultaneous participants in the same authenticated cooperative server. Validate account concurrency and token renewal with the selected launcher before claiming N-client support. Do not assume one authenticated account can supply arbitrary independent concurrent players. Store tokens in the launcher's supported secure location or a dedicated secrets mechanism, never in experiment archives. Treat a private offline test topology as a separate explicitly chosen configuration, not an automatic workaround for absent authorization or licenses.

Suggested lifecycle: `defined -> acquiring -> needs_user_action | resolved -> staged -> launching -> connecting -> validating -> ready -> running -> draining -> checkpointed -> stopped`, with typed `failed` and `recovering` transitions. Attach per-phase deadlines, process-tree identifiers, stable run/client/server IDs, structured failures, and cleanup ownership. A launcher can exit while its game continues, and server wrappers can restart children, so supervising only the initial PID is insufficient.

Readiness requires: expected game/loader/pack fingerprint; successful mod/script load; correct expert mode; world loaded; intended player identity connected; a fresh non-loading rendered frame; a small observable input round trip; and the initial benchmark predicate. Distinguish startup failure, authentication failure, pack mismatch, mode mismatch, control/capture failure, and game failure.

## N clients, worlds, and capacity

**Recommended independent-run topology:** N actual rendered clients with N independent writable instances and N world states. Prefer one dedicated server per independent experiment when the supported adapter benefits from authoritative state capture; alternatively an integrated server per client is a separately validated profile. Cloning a stopped baseline gives stronger initial-state equivalence than regenerating only from the same seed. Never mount one writable world into multiple independent servers.

**Recommended cooperative topology:** N actual rendered clients connect to one matching dedicated server and share one world. Each has its own identity, inventory, observation stream, action queue, and recorded contribution; teams/quest sharing are explicit experiment settings. A synthetic spectator camera, fake player, or server-side companion does not fulfill the requirement for N independently rendered player clients. The topology must be included in scores: shared-world assistance cannot be silently compared against isolated-world results.

The runtime scheduler, not the LLM loop, owns capacity. Admission uses measured CPU, RAM, GPU/VRAM, capture/encoding, storage I/O, network, and account slots. Include launch-time peaks and chunk-generation spikes. Each client has a frame/input latency objective; each server has a tick-time objective. Queue excess requests and report `requested`, `admitted`, `running`, and `queued` counts instead of promising unlimited agents.

**Verified sizing guidance, not a concurrency benchmark:** Enigmatica recommends 6 GB minimum / 6.5 GB recommended for E2E and E9 clients; its table lists E6 at 5/6 GB without a separate expert row. Server guidance says typically 4–8 GB. Eight 6.5 GB client heaps alone are 52 GB, before native memory, GPU allocations, OS, capture, inference, or servers. These values do not establish a safe N on the user's computer. [Memory guidance](https://wiki.enigmatica.net/main/help-desk/guides/allocating-memory).

Prove simultaneous control with both clients moving and interacting while unfocused, receiving fresh independent frames, and avoiding keyboard/mouse cross-talk. Multi-window visibility alone does not prove independent input. Measure process RSS, frame time, capture age, action acknowledgement latency, server tick time, and crashes at N=1, then N=2; increase only after those pass. Maintain a calibrated host capacity profile and reserve headroom.

## Persistence, recovery, and reproducibility limits

**Recommended:** a durable run record links the artifact lock, world snapshot, player/quest state, agent memories, scheduler state, pending action IDs, logs, and observation/action trace. Server state can include data outside the primary region files; snapshot the complete declared mutable boundary, including pack-specific team/quest/progression data and relevant root-level files. On first support of a pack, audit writes during a controlled session to discover that boundary.

Make stopped, fully flushed snapshots the initial reliable baseline. For later live checkpoints, require a pack-specific consistency barrier and verified save completion; copying arbitrary live files is not an atomic snapshot. A cooperative snapshot covers the whole shared world and all participants at one checkpoint epoch. Save the baseline before benchmark play. Restore into a fresh writable run directory, then validate inventory, position, quest state, machines, teams, and expected world contents before resuming.

After a crash, retain failure artifacts, terminate the owned process tree cleanly where possible, restore the last valid checkpoint, and mark the interruption and lost work. Do not replay unacknowledged craft/place/transfer actions blindly: reconcile state first. Bound restart attempts and separate deliberate resets from unexpected failures. Agent memory and game checkpoint epochs must match, or the agent can remember progress that the restored world no longer contains.

Same seed, same files, and recorded actions improve repeatability but do not establish bitwise deterministic Minecraft. Tick scheduling, threads, multiplayer timing, mods, random streams, and rendering can diverge. Claim reproducible initial conditions and auditable trajectories; report seed/snapshot sets, repeated trials, success distributions, wall time, and game time. Any claimed deterministic subprofile needs its own empirical evidence.

## Existing AI systems and evidence limits

| Project | Primary-source evidence | Relevance and limit |
|---|---|---|
| Mindcraft | FAQ explicitly excludes mods that change game mechanics | Useful vanilla comparison; not a ready expert-pack backend. [FAQ](https://github.com/mindcraft-bots/mindcraft/blob/develop/FAQ.md) |
| MineMind | Repository claims a Forge 1.20.1 server-side companion, FTB quest extraction, registered modded blocks, RecipeManager crafting, and live tests on Reclamation | A concrete modpack-aware design lead. README labels it early alpha, with machine automation, reward auto-claim, other quest systems, and configurable multi-pack profiles unfinished. No inspected evidence proves E2E/E6E/E9E compatibility or N rendered clients. [Repository](https://github.com/Boyan253/minemind) |

MineMind's reported success is mining/crafting and quest progression on a specific different pack, not proof of expert-pack completion. Its author makes broad comparisons to other agents; those comparisons are not adopted here as independent facts. The useful architectural lesson is runtime registry/recipe/quest integration, while this task still needs the separate full-client runtime. This scoped search did not establish an existing drop-in system satisfying all requested runtime properties; absence from this search is not proof none exists.

## Dependency and acceptance gates for the SPEC

1. **Distribution gate:** use the confirmed CurseForge + Forge workflow; acquire the precise E9E client/server files through supported paths; verify actual server ZIP references, Java and Forge builds, all hashes, and a cold install with no hidden mutable upstream dependency. Test old ServerStarter against current acquisition rules. Deliver a lock and acquisition report.
2. **One-client gate:** launch vanilla 1.19.2 and E9E; show a real rendered client; load/join the intended world; exercise movement, camera, inventory, GUI interaction, block break/place, and a modded interaction. Verify expert mode with both recipe and quest evidence. Log provenance and measured readiness.
3. **Two-client gate:** prove independent action/capture isolation, unique identities, bounded latency, and process ownership. Run once with separate worlds and once with a shared world. Capacity failure must queue or reject predictably.
4. **State gate:** checkpoint, stop, restore, and verify representative inventory, player location, quest/team data, and a modded machine's state. Inject client crash, server crash, connection loss, and control loss. Bound retries and preserve evidence.
5. **Progression gate:** verify a reproducible early expert task involving an altered recipe and a quest transition; then a machine-dependent multi-step milestone. Declare unsupported recipe/GUI/quest families explicitly. These are adapter acceptance tasks, not evidence that a model can complete the whole pack.
6. **Scale gate:** increase N only under measured frame/input/tick budgets; publish capacity on specified hardware, with shared versus isolated topology and local versus remote inference distinguished.
7. **Compatibility gates:** repeat the relevant gates for E6E and E2E with their own Java, loader, quests, and controls. An adapter compiling or joining a server is insufficient. Do not describe them as supported until the evidence exists.

The eventual SPEC should assign ownership to each gate, define pass/fail artifacts and timeouts, make assisted onboarding states explicit, and separate promised MVP capabilities from experiments and later compatibility tiers.
