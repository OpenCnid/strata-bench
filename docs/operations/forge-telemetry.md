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

Telemetry 0.3.3 adds opt-in `strata/ForgeTelemetryConfig/3`: all version-2
fields plus `authentication`, containing exactly `challenge`, `key_file`,
`key_sha256` and `authority_digest`. Use the private issuer to create this
block; it binds a fresh per-boot key to the intended instance/campaign/epoch.
The key file must stay outside the game installation and agent access. Keep
configuration versions 1/2 labeled unauthenticated when replaying old evidence.

The private [craft reference seal](private-scoring.md#sealed-craft-reference-inputs)
issues authority schema 2, binding its preserved setup digest into the same
opaque authority fingerprint. That seal was introduced with module 0.3.3 and
configuration 3; module 0.3.4 retains configuration 3 and adds native launch identity.
Plain authority schema 1 remains valid for historical stream inspection but
cannot be attached retroactively to a sealed craft reference.

```powershell
python -m strata_evaluator.telemetry_auth issue `
  --directory <fresh-absolute-private-directory> --game-directory <absolute-game-root> `
  --instance <private-instance-id> --campaign <campaign-id> --epoch <epoch>
```

The command writes `authority.json`, a 32-byte `producer.key` and the
`producer-authentication.json` block. Insert that block in the version-3
configuration; no secret key bytes enter its JSON. Before its first event,
the producer exclusively creates/forces `producer.key.claimed`, binding the
grant to its boot. A consumed grant cannot start another boot. Retain failed
claims; do not delete them to retry. A new boot needs a fresh operator grant,
and a registered scorer restart still needs the existing increasing-epoch and
new-boot checks. Issuing a grant alone does not register or qualify a score.

Signed spools use `<boot>.authenticated.jsonl`. Each private wrapper authenticates
the exact original event bytes and its place in the per-boot chain. Encoded
bytes consume the configured quota, so reserve their actual storage overhead.
Inspect only against the separately issued authority:

```powershell
python -m strata_evaluator.telemetry_auth inspect `
  --spool <absolute-signed-spool> --authority <absolute-private-authority.json> `
  --output <absolute-private-report.json>
```

Successful stream authentication is distinct from authenticated process
identity, setup/team provenance and scorer eligibility. Existing raw readers
do not silently accept the signed format; use the explicit importer. Keep keys,
claims and spool/report files private through retention and recovery. The module
preserves explicit null payload fields as required by the importer.
[Implementation, Java/Python verification and limits](../verification/2026-09-20-authenticated-telemetry.md)
do not constitute authentic game or full T06/T10 qualification.

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

Telemetry 0.3.2 also supports an explicit private client configuration probe.
Pass `-Dstrata.clientConfigProbePlan=<absolute-external-plan.json>` only on a
separately pinned diagnostic client. Use `ForgeTelemetryConfig/2` with exactly
one event, `max_bytes` between 65536 and 1048576, empty `recipe_ids`, and 1–16
exact `config_queries`. The existing external `spool_directory` receives one
create-exclusive `client-config-<session-id>.json` after connection. No server
plan, game command or gameplay endpoint can activate the client probe.

Inspect that artifact privately:

```powershell
$env:PYTHONPATH='evaluator/src'
.\.venv\Scripts\python.exe -m strata_evaluator.client_configs `
  --plan <absolute-private-plan.json> --snapshot <absolute-private-snapshot.json> `
  --output <new-private-report.json>
```

Pin both input files, the loaded probe/client artifacts and the process identity
in the surrounding operator evidence. The importer verifies complete ordered
selectors and preserves absent/failed observations, but its result does not
authenticate same-user files, qualify a pack lock, prove cached consumer effects
or admit scores. Dedicated server 0.3.2 retains `ServerStarted/4`; the importer
continues accepting 0.3.1 with its original payload and witness requirements.

## Owned sealed reference launch

Telemetry 0.3.4 adds `ServerStarted/5` and native process/world/module identity.
Use a fresh private `PrivateCraftReferencePlan/1` seal and a
`PrivateReferenceLaunch/1` plan. The launcher performs preflight itself: do not
consume the one-use reservation in a separate preflight command first.

```powershell
$env:PYTHONPATH='src;evaluator/src'
.\.venv\Scripts\python.exe -m strata_evaluator.reference_launch `
  --database <absolute-private-database.sqlite> --plan <absolute-private-launch-plan.json>
```

The Windows production mode is `e9e-serverstarter`. It admits only the reviewed
bootstrap/configuration hashes in `reference_launch.py`, existing EULA acceptance,
loopback online-mode properties, pinned executable/module and complete immutable
JRE/mod/library/server-script/startup-script trees. Include the running Python
executable and `src/mcbench/process_bootstrap.py` in the pins. The evidence
directory must be fresh and outside game/authority roots. Private plans,
databases, archives, keys and spools must stay outside public source and gameplay
access. `synthetic-fixture` mode is restricted to a synthetic setup and is not
an alternate production launch command.

The bounded run binds the signed native identity to retained Job Object handles,
sends `stop` once, and retains complete logs and terminal/uncertain dispatch
state. Never retry a consumed or uncertain instance. Inspect a stopped run with
the existing craft-reference importer; tracked failed launches cannot bypass
their dispatch state. `launch_binding_verified` does not imply scoring,
mutable-world/config writer exclusion, full process isolation or recovery.
See [verification and limitations](../verification/2026-09-20-reference-launch.md).

For a bounded external operator client, use `PrivateReferenceLaunch/2`, omit
`ready_run_s` and provide `participant` with `participant_id`, `window_s` (1–420)
and an absolute fresh `report_path`. Its existing parent must be outside source,
game, authority and launcher evidence directories. The complete participant
window must fit within `max_wall_s` (still at most 600) after boot; otherwise the
one-use run fails without publishing readiness. Version 1 is unchanged.

Production E9E version-2/3 launches also require `--client-binding PRIVATE.json`.
Build a strict `PrivateReferenceClientBinding/1` from the sealed setup and
registered launch, not by copying a historical loose client manifest. Register
instance/campaign/epoch, agent/actor/native team, participant, numeric loopback
port, independent endpoint-plus-actor body digest, module/fixture pins, declared
supplied inputs, client/worker/terminal limits and primitive cap. Its endpoint
policy is `installed-cli-resolved-loopback/1`; other launch/address policies
need separate conformance. The driver must consume those values and still
compare actual native identity before actions. Preflight consistency is not
proof that a client ran or stopped correctly.

Run the read-only check before dispatch:

```powershell
python -m strata_evaluator.reference_client --binding PRIVATE.json --setup SETUP.json --launch LAUNCH.json --output NEW-CHECK.json
```

All paths are private and the output must be fresh. The launcher requires the
binding before consuming its one-use reservation, retains its digest/bytes and
rechecks declared hashes under held file leases. Synthetic v2 and headless v1
reject this argument. Preserve historical failures without updating their seals.
The [first actual client reference](../verification/2026-09-20-reference-client-binding.md)
failed before actions because of stale endpoint identity; its consumed grant
cannot be reused. A new reference must have fresh identity/lineage and a clean
registration, preserving current inventory and declared setup interventions.
The [corrected-body trial](../verification/2026-09-20-native-craft-reference.md)
also remains uncertain: startup left insufficient full worker exposure and an
outer abort interrupted cleanup reports. Do not use that unclean world as a
checkpoint or rerun its grant. Use the implemented typed abort component and durable outer pair monitor;
seal the changed driver/source profile before another game. Keep the hard server,
client and guardian limits and record missing reports as missing.

`PrivateReferenceLaunch/3` adds `outer_challenge` (a fresh 64-character hex
digest) and `abort_cleanup_ms` (500–15000), retaining all v2 registration and
exposure rules. `reference_abort.request_abort` publishes one private,
non-replacing scope-bound request after the outer failure has been durably
recorded. Pass the original exception so its typed fault code survives without
secret-bearing messages. Use `ParticipantAbortGuard.start` for the trusted
driver's owned client/worker objects, `check` before commands, and `close`
before its terminal report. The independent watcher also stops retained
children when the driver is blocked. A stalled close remains unconfirmed;
the outer hard watchdog is still required. No process is killed by PID lookup.

The server stops new readiness on abort, allows bounded participant cleanup,
and then uses ordinary server stop within existing deadlines. Invalid controls
also abort; failed/missing reports remain failures. Even successful cleanup or
a completed receipt cannot make an aborted run scoreable. This cleanup window
does not change the 500-ms guardian. Source/Windows/JVM component checks pass,
and the durable outer coordinator has actual CLI/owned-process fixture evidence.
The guarded private Forge-driver candidate and authentic pair remain unqualified. See [evidence](../verification/2026-09-20-reference-abort.md).

New E9E production pairs require `PrivateReferencePair/3` with a pinned `PrivateReferenceClientPreparation/1`. Complete cached-session preparation before calling the pair entrypoint; bind its nonsecret receipt, argument bytes, exact driver and client registration. Include `reference_preparation.py` in the source pins. The controller checks full remaining session exposure before starting the server and rechecks before the client. Missing/expired preparation must not trigger a server launch or automatic refresh. Keep argument files private and let the driver retire them after use. [Contract, source checks and retained scope05 failure](../verification/2026-09-21-client-preparation-admission.md).

For the implemented outer monitor, prepare a strict `PrivateReferencePair/1`
plan and run:

```powershell
python -m strata_evaluator.reference_pair --database PRIVATE.sqlite --plan PRIVATE-PAIR.json
```

Pin the launch JSON, production binding, private driver, current interpreter,
trusted bootstrap and all declared source/helper/configuration inputs. The
source root must match this checkout. Declare a separate fresh private pair
evidence directory. `client_window_ms` must equal production client wall plus
terminal reserve and fit completely at admission; `finalize_ms` is bounded
1000–15000 ms for outer terminal/log handling. These do not extend any inner
client, participant, server or guardian limit. The source checks scope and
challenge against the inner durable readiness record before dispatch.

The coordinator records one pair intent, owns both outer Jobs, captures bounded
logs and enforces independent deadlines. It preserves typed failures before
cooperative abort, exact terminal reports and uncertain/missing results.
Interrupted intents cannot be replayed by changing output paths. A terminal
inner server cannot bypass an incomplete outer pair during craft import.
See [source/owned-process evidence](../verification/2026-09-20-reference-pair.md).
The private driver candidate is prepared, not authentic qualification; reseal
all changed files and register sufficient complete exposure before dispatch.

Wait for the atomically published `participant-ready.json` in the private launch
evidence directory. Before dispatching the client, validate
`ReferenceParticipantReady/1` and compare instance, setup, complete launch-plan
digest and participant with the registered plan; reject an expired receipt or
terminal server. Independently own the client/worker, retain their bounded wall
watchdogs and existing guardian acceptance criteria, and keep shared input paused.
The launcher does not spawn or terminate the external participant.

After the client/worker have terminated, durably close the registered JSON report
(at most 8 MiB), then call `reference_participant.submit_completion(evidence,
ready, report_path, outcome)` exactly once. `outcome` is `completed` or `failed`;
do not relabel a failed client/guardian as completed. The helper publishes a
complete, non-replacing `participant-completion.json` with readiness digest and
report hash/length. The launcher verifies and preserves the report, holds its
bytes through server stop and journals the receipt before sending `stop`.
Missing/invalid/failed completion retains uncertainty; no automatic replay or
import bypass is allowed. Final server results are separate from the participant
report, so the driver must not wait for server termination before submitting its
own terminal report. A receipt is coordination evidence only, never authenticated
client execution, scoring or process isolation. See the
[focused evidence](../verification/2026-09-20-reference-participant.md).

Telemetry 0.3.5 uses `ServerStarted/6`, retaining configuration 3 and the launch
identity while declaring `native-e9e-setup-observation/1`. It emits private
`NativeSetupSnapshot/1` records at tick 1 and before each craft begin/end.
These observe server modes/admin exposure, command-attempt count, loaded KubeJS
mode/error state and an acting player's existing FTB team/rank/members. Missing
or changed dependency support is explicit; no JS or arbitrary method is exposed.
The operator importer checks exact record adjacency and scope. Version-2 sealed
reference plans register expected native teams separately. The Gradle resource
task now stamps `mods.toml` from the project version; keep historical artifacts
and their previous metadata mismatch unchanged. [Evidence and open qualification](../verification/2026-09-20-native-setup.md).

Telemetry 0.3.7 uses `ServerStarted/8` and retains the version-7 transport identity.
Its private `NativeSetupHistory/1` records precede every setup point and the final
stop event. Fixed native entry hooks retain mode/operator/team mutation attempts,
including reversals, without recording raw command arguments. A single exact
terminal native stop invocation is separately correlated. Hooks operate only
between this module's startup and stop handlers; no complete process-lifetime or
full mutation-route claim follows. Missing hooks, malformed history and observed
taint prevent candidate use. Existing 0.3.5/0.3.6 profiles keep their exact schema
and module requirements. [Implementation, verification and uncovered routes](../verification/2026-09-21-setup-history.md).
