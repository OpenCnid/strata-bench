# Forge client settings extension — development

`java/forge1192-client` is a separate, incomplete extension for the authentic
Minecraft 1.19.2 / Forge 43.4.23 client. This runbook describes its settings
development surface. D06 later added a separately identified structured-control
fallback, described in the [game API runbook](forge-game-api.md); it is not a
Mineflayer plugin or a qualified keybinding capability. Complete native CAS,
input/effect validation, restart and host integration remain required.

The optional private settings bridge and development settings writer do not
qualify a gameplay settings capability. The separate game-action API has its
own configuration and conformance requirements. With no configuration the
extension is inert. On a real client, the optional operator
variable `STRATA_SETTINGS_DISCOVERY_DIR` (or the per-launch JVM property
`strata.settingsDiscoveryDirectory`) selects an existing absolute private
directory outside the game installation. After mod loading, one client-thread
snapshot is written to a fresh `bindings-<random-id>.json` file and forced to disk.
The module is inactive on a dedicated server.

Discovery includes translation ID, localized label, current/default physical
representation, modifiers, context, registration occurrence and persisted value.
The options parser returns key fields only; unrelated options such as server
addresses are excluded. Duplicate persisted names are marked ambiguous. IDs keep
owner/translation/occurrence; unusually long/non-ASCII translation identifiers use
a stable hash while the original translation remains in its separate field.
On first launch, an absent options file is explicitly reported as absent, with
unknown persisted values; the diagnostic does not create or save game options.

Vanilla ownership is based on explicit mapped `Options` key references. It does
not reflect over arbitrary mod-injected fields or infer an owner from a translation
prefix. All mod ownership remains unknown until source/registration evidence is
bound. Custom conflict contexts are marked unknown. Every binding is protected
from mutation, the tested physical-key pool is empty, and `supported`, `atomic_cas`,
`restart_tested`, `layout_verified` and `consumer_tested` remain false. Parsing a
persisted F13 chord does not prove that the backend can emit it.

Build with the same pinned Java environment described in the
[telemetry runbook](forge-telemetry.md):

```powershell
cd java
$env:STRATA_FTB_LIBRARY_JAR = 'C:\path\to\official-E9E\mods\ftb-library-forge-1902.4.1-build.236.jar'
.\gradlew.bat :forge1192-client:build --no-daemon --console plain
```

Adding this JAR to a development client changes that client's instrumented identity
and must be recorded. An operator snapshot does not satisfy T05 or qualify a
gameplay tool. The current Python conflict planner treats universal/custom contexts,
unproved modifier exclusivity and unknown keysym/scancode aliases conservatively;
real consumer/effect, GUI, restart and isolation evidence still governs admission.

Audit a captured operator diagnostic with:

```powershell
uv run --frozen python -m mcbench.client_discovery <private-bindings.json> `
  --options <absolute-profile-options.txt> --output <new-private-audit.json>
```

The bounded reader rejects duplicate JSON fields, unknown fields, incorrect stable
IDs/occurrence flags, mixed backends and attempts by this unqualified module to
advertise settings mutation or tested input. It reports unknown persistence,
runtime/persisted differences and whether the options file still has the snapshot's
hash. A changed file is reported, never silently treated as matching. Unrelated
options values are not copied into the report. `format_result=pass` establishes
only diagnostic format consistency: producer authentication, effects, restart and
T05/G1 remain unverified. Reports are created exclusively and cannot overwrite
earlier evidence. The command belongs to operator tooling, outside gameplay packages.

During the 2026-09-18 development checks, CurseForge regenerated its managed
Launcher's Java path and arguments on each profile Play. Reapply and verify the
pinned runtime and diagnostic property before collecting a comparison run. Opening
`minecraft.exe` directly without the managed working directory used a different
launcher profile/authentication context; use the CurseForge-managed route. Do not
copy authentication caches between those directories.

Two actual client boots produced 253 bindings with stable identifiers and runtime
values. The first export found an options file containing no persisted key fields;
ordinary game settings save followed by cold restart produced 253 matching
persisted values. This is read-only discovery/persistence evidence, not native
transaction or input-effect conformance. The Controls screen also logged an
invalid-scancode GL error, retained for diagnosis. Full details and unresolved
cases are in the [verification record](../verification/2026-09-18-long-horizon.md).

## Development native transaction probe

`SettingsStore` holds a per-profile file lock and writes a bounded, forced,
hash-chained private journal. A transaction validates the expected runtime/options
revision, saves owned values and all-key digests before mutation, updates native
key mappings on the client thread, and atomically replaces only selected key
fields in `options.txt`. Unrelated bytes are preserved. Applied transactions stay
`applied_pending_verification`; this module has no commit operation. Duplicate
request IDs return existing status without repeating a forward write. Recovery
restores transaction-owned values only. Foreign runtime/options changes leave a
`rollback_conflict` and block further mutation.

The lock excludes cooperating Strata writers. Actual process/filesystem isolation
must exclude other writers to make the read/replace sequence a qualified CAS.
Forced file writes and atomic replacement have unit evidence; power-loss and
directory metadata durability are not qualified. The journal hash chain detects
damage, not a malicious actor with write access to the private directory.

`NativeSettingsRuntime` binds its one development mutation authority to exact
Curios JAR SHA-256
`1f7742d6c4f6b6cd8d106e54181255c2d264194ba232d42901ef90da6b91e635`
and object identity of its public `KeyRegistry.openCurios` registration. It hashes
loaded mod artifacts into a runtime fingerprint. It does not infer ownership
from labels or claim the general discovery payload now has resolved mod owners.
All other mappings remain protected. Native setters rebuild the key lookup, and
release clears native down states and pending click queues; physical OS release,
polling, context and effect parity remain unverified.

For a separately authorized desktop development run, the per-launch JVM property
`-Dstrata.settingsTransactionDirectory=<absolute-existing-private-directory>`
enables one title-screen round trip. The directory must be outside the game
profile and have no existing transaction journal. Curios must initially be
unbound. The probe changes that configuration to F13, reads runtime and persisted
state, and always attempts rollback in the same client tick. It records private
before/applied/restored state and the transaction journal. It never joins a world,
presses F13, invokes Curios, or commits a patch. F13 here is an encoding probe,
**not a tested physical key**. A completed report must have equal before/restored
states; exceptions fail the probe and any retained pending journal needs operator
recovery. Do not reuse a journal directory to retry a forward transaction.

The current extension is installed in the dedicated development profile.
[September 20 authentic evidence](../verification/2026-09-20-native-settings.md)
passes its first title-screen round trip and an independent discovery-only cold
restart: all 253 runtime mappings and persisted values match the restored map,
with unrelated options bytes preserved. Physical F13, conflict/effect repair,
interrupted recovery and complete T05 remain unqualified. Existing desktop
authorization covers this separate-desktop/API route; shared input remains
paused. No scored run may enable these diagnostics.

## Private native bridge (not qualified for gameplay)

The alternative JVM property
`-Dstrata.settingsBridgeDirectory=<absolute-existing-private-broker-directory>`
starts a private bridge after reaching the title screen. Do not set it together
with `strata.settingsTransactionDirectory`; both paths reject that combination
before their mutation. The broker directory must be outside the game profile,
outside gameplay workspaces and outside evidence exports. Its generated
`connection-<uuid>.json` contains a **bearer credential**, loopback port, fresh
session ID and runtime fingerprint. Never publish or commit connection files.
Each boot creates a new session; retained files cannot authenticate to a new one.

Only `127.0.0.1` is bound. Authentication, exact host, browser-Origin rejection,
strict JSON/schema, current session, deadlines and body limits precede queueing.
The request body is limited to 32 KiB; response to 512 KiB; pending queue to eight;
result cache to 64. HTTP workers only queue/read responses. The client thread
executes at most one queued operation each tick, checking its monotonic deadline
again before dispatch. The title-screen restriction is checked at dispatch;
`stop_all` only releases native key states and does not claim physical OS release.
No game object, file path, packet, evaluator or arbitrary command is callable.

The bridge offers private `snapshot`, `apply`, `status`, `rollback` and `stop_all`.
It has no commit operation. Applied changes remain pending verification until
explicit rollback. Inspecting a pending transaction does not consume journal
recovery space. A client crash preserves prepared/applied state; reopen the same
journal with the same exact runtime fingerprint and query its transaction ID
before rolling it back. A changed runtime fingerprint is fenced, not silently
used for recovery. A timed-out request is uncertain: query status, never repeat a
forward write with a new transaction ID. The Java store deduplicates identical
transaction content even across process restarts.

Operator commands (connection path is private; no secret token in arguments):

```text
python -m mcbench.native_settings --connection <private-connection.json> snapshot
python -m mcbench.native_settings --connection <private-connection.json> apply --patch <private-patch.json>
python -m mcbench.native_settings --connection <private-connection.json> status --transaction-id <id>
python -m mcbench.native_settings --connection <private-connection.json> rollback --transaction-id <id>
```

Patch shape: `transaction_id`, `expected_revision`, `expected_digest` from the
native snapshot, plus `changes` keyed by stable native binding ID, each containing
`before` and `after` persisted strings. This development adapter permits only its
source-bound Curios target and unbound/F13 encodings. This is a private transport
record, not a completed public `KeybindingPatch` or a tested physical-key pool.
Python sends one POST, then polls only that request's status. Lost/malformed or
mismatched acknowledgments return `SETTINGS_OUTCOME_UNKNOWN`; the client does
not retry a mutation. Diagnostics do not print raw validation inputs or secrets.

`Controls.plan` rejects this native snapshot with `CAPABILITY_MISSING` because
`supported` remains false. Full qualified discovery projection, controller
reconfiguration/lease/accounting, effect and restart services, verified commit,
and the scoped gameplay CLI remain required. Bearer checks do not prove same-user
filesystem/process isolation. The authenticated bridge's OS boundary and timing
must still pass T05/T06/T07 on the authentic client.

Explicit non-game cross-language checks:

```powershell
cd java
$env:STRATA_FTB_LIBRARY_JAR = 'C:\path\to\official-E9E\mods\ftb-library-forge-1902.4.1-build.236.jar'
.\gradlew.bat :forge1192-client:test :forge1192-client:writeTestClasspath --no-daemon --console plain
cd ..
$env:STRATA_SETTINGS_TEST_JAVA='<pinned-JDK>\bin\java.exe'
$env:STRATA_SETTINGS_TEST_CLASSPATH='<checkout>\java\forge1192-client\build\test-classpath.txt'
uv run --frozen pytest tests/test_native_settings.py tests/test_native_settings_jvm.py -q
```

The fixture is compiled from test sources and excluded from the client JAR. It
uses the production store/HTTP bridge with a synthetic key runtime. Its process
restart and lost-ack results cannot replace Minecraft integration or effects.
