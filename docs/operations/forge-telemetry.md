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

Telemetry 0.2.0 also accepts `strata/ForgeTelemetryConfig/2`, whose required
additional field is `config_queries`. Each query has `file_name` (a lowercase
TOML basename, at most 128 characters) and `paths` (1–32 unique arrays, each
1–16 printable ASCII keys of 1–128 characters). At most 16 distinct files are
allowed. These are exact public Forge registry selectors, not paths to open or
methods to invoke. Version 1 remains accepted with no config queries. Use keys
from the pinned release/config spec; retain erroneous probe plans separately.

`strata/ServerStarted/2` binds the query plan. On the first server tick END,
`strata/ConfigSnapshot/1` observes registration and selected raw loaded data.
It distinguishes unregistered, unloaded, unsupported spec/value, unstable,
read_failed and quota_exceeded outcomes. Successful rows distinguish declared
spec leaves from present raw keys; missing values have no value field. The reader
never invokes ConfigValue.get, correction, save, reload or setters. Two matching
copies plus unchanged object identities/loaded status establish only
`matching_consecutive_reads`, not atomicity against a file-watcher thread or
equivalence to a mod's cached consumer state. There is no automatic file exclusion
or whole-pack loaded-config pass.

Values are limited to booleans, integers within ±(2^53−1), finite doubles,
valid strings of at most 4096 UTF-8 bytes and lists. The complete copy permits
at most eight list levels, 4096 value nodes and 64 KiB; overflow discards the
whole selected snapshot. Unselected values and config comments are not copied.
The private importer rejects missing/duplicate/unrequested files, mismatched
path order, late snapshots, malformed/coerced values and incomplete streams.
The 0.1.0 historical module remains separately accepted with its original schema.

For the retained E9E findings, the exact source-backed selectors are BHMenu
`["pack_id"]`, No More World Settings `["buttondisabled"]`, Inventory Sorter
`["blacklists","containerBlacklist"]` / `["blacklists","slotBlacklist"]`,
legacy Sophisticated Core `["server","enabledItems"]`, and its current common
config `["common","enabledItems"]`. Create uses
`["logistics","defaultExtractionLimit"]` / `["logistics","defaultExtractionTimer"]`
and the four keys under `["schematics","schematicannon"]`:
`schematicannonGunpowderWorth`, `schematicannonFuelUsage`,
`schematicannonShotsPerGunpowder`, `schematicannonDelay`. Query both the legacy
and current paths; an absent or undeclared legacy key stays visible. Check the
actual startup plan against the privately hashed input config before relying on
an inspection. These selectors do not assert that a named file is registered.

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


Telemetry 0.3.0 records the ordinary server result-slot click before/after in
`CraftBegin/1` and `CraftEnd/1`, alongside its existing raw callback. Its required
server mixin targets the pinned 1.19.2 SRG `m_150399_` method at HEAD/RETURN;
startup failure or a missing/partial witness is not successful instrumentation.
`ServerStarted/3` identifies `server-result-pickup-bracket/1`; older schemas stay
readable. No action, output, component, recipe or inventory is altered.

The private importer checks exact output, ingredient consumption, unchanged full
component hashes for other inventory/armor/offhand slots, one matching callback,
actor/scope/tick continuity and the observed runtime recipe. Valid mirrored and
offset shaped recipes are allowed. Only a single untagged shaped recipe with no
remainders and one item per grid cell is currently supported. Metadata-bearing
ingredients, quick crafting, custom serializers, nested/partial calls and missing
or foreign callbacks do not qualify. Failed witnesses remain in the report;
duplicate transaction IDs and incomplete boundaries reject the spool.

`craft_witnesses[].resource_witness` describes resource evidence only. All records
and reports retain `score_eligible:false` / `scoring_eligible:false`. Deployment
isolation, authenticated provenance, fixture validity, team assignment, registered
private scoring controls and instrumentation parity are separate required gates.


Telemetry 0.3.1 uses `ServerStarted/4` and
`server-result-pickup-fastbench-bound/2`. Startup verifies that the required
click mixin's marker was actually applied. The only additional result-slot class
is exact FastWorkbench 7.1.4 CraftResultSlotExt, gated by its pinned loaded JAR
hash. Unknown subclasses or changed artifacts reject. Native callback diagnostics
record private class names and whether a bracket is pending. Every existing
resource and scope check remains; no automatic scorer admission is added.
