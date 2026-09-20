# Private Forge telemetry development module

`java/forge1192-telemetry` compiles against Minecraft 1.19.2 / Forge 43.4.23.
It is separate server instrumentation, not a replacement client/backend. Its
installation changes the instrumented environment identity. No Mineflayer E9E
compatibility, scorer correctness, isolation, overhead or mechanics-parity pass
follows from loading it.

The module registers no commands, custom channels or player payloads, and changes
no recipe, registry, block, inventory, quest or machine state. On a dedicated
server it activates only with the operator environment variable
`STRATA_TELEMETRY_CONFIG`, pointing outside the game installation to a private JSON
file. Integrated servers remain inactive. The supervisor must keep configuration,
spool files and the server process outside gameplay-agent access; path checks alone
are not a same-user isolation boundary.

The strict `strata/ForgeTelemetryConfig/1` fields are `campaign_id`, positive
`epoch`, `spool_directory` (existing absolute private directory), `max_bytes`
(64 KiB–1 GiB per boot), `max_events` (1–1,000,000 per boot) and `recipe_ids`
(at most 64 unique namespaced identifiers), plus `schema`. There is no target
URL, console command or arbitrary reflective method in the configuration.

Each boot creates a new UUID-named JSONL file and emits `mcbench/GameEvent/1`
records with evaluator visibility. A bounded 256-record queue feeds one writer;
each record is forced to disk before advancing the durable cursor. Backpressure,
write errors, quotas and a two-second drain failure surface as instrumentation
errors. A supervisor must stop/quarantine on these errors or missing heartbeats;
this development module does not establish the full campaign fault policy.
The file importer rejects partial tails, sequence gaps, mixed scopes/boots,
decreasing ticks, malformed payloads and missing clean-stop records.

Health samples are approximately 1 Hz based on monotonic wall time. They contain
observed server ticks, per-account connected avatar ticks, vanilla's rolling
average MSPT, heap and GC counters, and the previous durable cursor. The measured
Forge START-to-END interval is labeled `observed_tick_work_ns`: it is not a claim
to include every instruction around those hooks. TPS can be computed from actual
sampled ticks/wall time. Startup and the final subsecond tail are separate from
sampled intervals. A server stall prevents sampling and must remain a gap.

Requested recipe snapshots come from the loaded server recipe manager, including
shaped dimensions, output and ingredient alternatives. Raw craft callbacks carry
`score_eligible=false` because they do not yet establish consumption, exact recipe,
team/setup or gift/admin provenance. The private scorer rejects these schemas.
Machine/energy/fluid and quest/team adapters remain required work.

Build using the pinned Temurin 17.0.20.1+1 JDK:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot'
cd java
.\gradlew.bat :forge1192-telemetry:build --no-daemon --console plain
```

The wrapper pins Gradle 8.8 plus its SHA-256; ForgeGradle is fixed to 6.0.42.
Resolved dependency versions and artifact verification hashes are retained.
The verification file records acquired artifacts, not a claim that every upstream
artifact has been independently audited. ForgeGradle still labels Mojang mappings
as changing and manages some downloads outside Gradle verification. The eight
game/mapping/MCP/Forge inputs in `java/build-inputs.json`, the wrapper JAR and
the Windows compiler binary are therefore checked separately before compilation.
This build currently qualifies only that Windows compiler profile; another
platform needs its own lock and verification.

From the repository root, inspect a stopped private spool:

```powershell
$env:PYTHONPATH = 'evaluator/src'
uv run python -m strata_evaluator.telemetry <absolute-private-boot.jsonl> `
  --campaign <campaign-id> --epoch 1 --e9e-furnace --output <private-report.json>
```

`--e9e-furnace` asserts the exact expert recipe and absence of the vanilla recipe.
It does not assert player crafting or quest state. The report remains private and
retains `gate_result=not_run`. Do not expose its recipes as a gameplay discovery
surface; a player-accessible recipe interface requires separate conformance.

Build provenance: the [official exact Forge MDK](https://maven.minecraftforge.net/net/minecraftforge/forge/1.19.2-43.4.23/forge-1.19.2-43.4.23-mdk.zip)
has SHA-256 `9e65749f4273cc1d7a5d6ed37715cc68a3b8fb848c63cb8cf66fce22701889d5`.
Its wrapper JAR has SHA-256 `ed2c26eba7cfb93cc2b7785d05e534f07b5b48b5e7fc941921cd098628abca58`.
Source/API evidence uses the exact Forge sources and the
[Forge 1.19.x setup documentation](https://docs.minecraftforge.net/en/1.19.x/gettingstarted/).
