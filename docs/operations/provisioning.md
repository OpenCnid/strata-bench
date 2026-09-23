# Private pack provisioning

This operator-only workflow implements source import, inventory verification,
sealing and fresh materialization. It does not install Minecraft, accept terms,
start a game, or certify a release gate. Keep the store, installations, receipts,
launch profiles and evidence outside the source repository and gameplay runtimes.

The official [CurseForge profile guide](https://support.curseforge.com/support/solutions/articles/9000196904-creating-a-custom-profile)
describes vanilla profiles. Select Vanilla and Minecraft **1.19.2**, then verify
the actual installed workflow for T02. Exact E9E targets are the official
[client file 8161120](https://www.curseforge.com/minecraft/modpacks/enigmatica9expert/files/8161120)
and [server file 8161123](https://www.curseforge.com/minecraft/modpacks/enigmatica9expert/files/8161123),
release **1.27.0**, project **882461**. These pages were checked on 2026-09-18;
their existence is not an acquisition receipt or a measured distribution hash.

```powershell
mcbench pack resolve e9e --request e9e-1270 --store C:/StrataPrivate/store
mcbench pack acquire --request e9e-1270 --store C:/StrataPrivate/store
mcbench pack evidence --request e9e-1270 --file C:/StrataPrivate/workflow.json --store C:/StrataPrivate/store
mcbench pack import --receipt C:/StrataPrivate/receipt.json --store C:/StrataPrivate/store
mcbench pack verify --request e9e-1270 --inventory C:/StrataPrivate/roles.json --store C:/StrataPrivate/store
mcbench pack seal --request e9e-1270 --launch C:/StrataPrivate/launch.json --evidence C:/StrataPrivate/checks.json --store C:/StrataPrivate/store
mcbench pack materialize C:/StrataPrivate/instances/e9e-001 --request e9e-1270 --store C:/StrataPrivate/store
```

`acquire` persists `AWAITING_ARTIFACT` and returns the exact release and explicit
official app/site work. It does not fabricate an unattended download API. Pending
requests expire after seven days; acquisition attempts have a declared 30-minute
bound without automatic retry. `--simulation` permanently marks the provisioning
store and resulting locks as examples; a simulation store cannot be reopened live.

The strict models in [provisioning.py](../../src/mcbench/provisioning.py) define inputs:

For new vanilla distribution verification, use `AcquisitionReceipt/2` with
`vanilla_manifest` and `vanilla_version_metadata` CAS references. Preserve the
exact downloaded JSON bytes with `mcbench pack evidence --preserve-source-bytes`
when importing those two documents; normal evidence import still canonicalizes
JSON. Retain the official HTTPS acquisition observation separately. Version 2
joins the one 1.19.2 release entry to its metadata hash and each role's exact
URL, size, SHA-1 and receipt SHA-256. A self-consistent receipt for an altered
shared-cache JAR is rejected. Legacy version-1 receipts keep their original
meaning and do not receive this stronger verification credit.

The [vanilla intake checkpoint](../verification/2026-09-21-vanilla-acquisition.md)
records the authentic distribution import and retained shared-client mismatch.
`ACQUIRED` is not a sealed installation or T02 pass.

Prepare the acquired vanilla server's software bytes with:

```powershell
mcbench pack prepare-vanilla-server C:/StrataPrivate/installed-server C:/StrataPrivate/new-server-software --request vanilla-1192 --store C:/StrataPrivate/store
```

This operator command requires a durable version-2 vanilla acquisition and
rechecks its metadata/CAS joins. It verifies `server.jar`, the inner server
and every declared installed library, including exact directory membership,
before independently copying the acquired payloads to a **new** directory.
No installed source is changed or game launched. Known configuration files
are hash-recorded as pending; world/account state and logs have explicit
excluded dispositions. Unknown root files or runtime extras reject.
An error after output creation preserves diagnostic partial output, which
must not be reused. A successful auxiliary `VanillaServerSoftware/1` report
enters the request's private operator CAS; provisioning state is unchanged.

Embedded license/notices/POM metadata and opaque archive anomalies remain
bound to their original JAR hashes. This does not assign licenses, qualify
stopped-source custody or replace `RoleInventoryInput`/provisioning checks.
Complete licensing, configuration, Java/client roles, update policy and cold
restart evidence before the full PackLock. [Implementation and actual software
preparation](../verification/2026-09-22-vanilla-runtime.md).

Prepare the Windows client from the acquired pristine client and exact
metadata-selected cache inputs:

```powershell
mcbench pack prepare-vanilla-client C:/StrataPrivate/cache/assets C:/StrataPrivate/new-client-software --request vanilla-1192 --store C:/StrataPrivate/store --library-root C:/StrataPrivate/cache/libraries --library-root C:/StrataPrivate/verified-server-software/libraries
```

Library roots are explicit and ordered. Missing entries may come from a later
root only when their metadata hashes match; a corrupt earlier candidate rejects.
The command preserves the declared Windows classpath order and records other-OS
exclusions. It verifies the asset index, all unique asset objects, aliases and
logging configuration, then copies only the named inputs plus the acquired
client/version bytes. It never copies the shared launcher tree or substitutes
its altered client JAR. Complete-copy and unchanged-source checks precede
`VanillaClientSoftware/1` publication in private CAS; no provisioning state
promotion occurs. All licensing, runtime configuration, Java, cold restart
and complete-role checks still apply. [Actual client preparation and Java
source comparison](../verification/2026-09-22-vanilla-client.md).

- `AcquisitionReceipt`: exactly one client and one server distribution, actual
  SHA-256 hashes, exact official origin/file IDs, license references, JVM/launcher
  pins and private evidence refs. E9E's client archive must carry the selected
  Minecraft/release/Forge manifest. ZIP members are checked for traversal, links,
  collisions, encryption, private content and expansion limits, without execution.
- `RoleInventoryInput[]`: absolute clean stopped roots, **every** file's canonical
  `FileEntry` and explicit provenance/exclusion evidence. No blanket inferred
  license or silent exclusions. The importer copies every file into private CAS,
  then rescans the complete tree to catch source changes. Software templates reject
  saves, credentials, keys and links. This filename guard supplements actual
  operator review and isolation; it is not a general secret-content detector.
  An installed file may have the exact bytes of already retained JSON/text
  evidence. File import preserves that object's type and metadata while checking
  the source bytes again; it cannot change its visibility. `VERIFIED` is the
  installed-inventory stage, not a license certificate or sealed PackLock.
  Retain absent component declarations explicitly alongside actual source/terms
  references; separately qualify the required legal and runtime checks.
- `LaunchProfile`: reviewed argument arrays, exact executable hashes, working
  directories and allowlisted environment. No guessed universal Java command.
  This stores an inspected launch plan; the supervisor must enforce it at execution.
  The active vanilla client is Mineflayer; SPEC §7 does not require a renderer.
- `ProvisioningEvidence`: every required named check, bound to the imported
  receipt, inventory and launch-profile digests. Each `ProvisioningCheck` retains
  its private raw evidence. E9E also needs cold-start expert configuration, altered
  recipe, quest/team and independent player-reference checks. These are trusted
  operator attestations; arbitrary JSON is not automatic proof of authenticity.

Sealing freezes content and records `game_conformance_claim: null`. T02/T03 and
campaign admission still require their actual evidence. `materialize` verifies
blobs while copying into staging and renames a complete fresh instance containing
`client/`, `server/` and a private lock marker. It never overwrites an existing
directory and never hardlinks mutable instances to immutable blobs. Corruption
leaves no partially published instance. Windows is the initial deployment target;
other operating systems still require their own filesystem/isolation conformance.

Original account sign-in/EULA acceptance and vanilla acquisition have recorded
evidence (SPEC §15, D05). Remaining integration includes complete runtime and
transitive-provenance review, cold restart/expert evidence, authenticated launch
supervision and full exact-pack structured-control qualification. Do not repeat
settled account/terms steps or treat an import as those broader passes.

The bounded server runner also accepts private `strata/DevelopmentServer/3`
plans. Keep `target`, `max_wall_s` and external `evidence`; replace `launch` with
`pack`, containing `store`, `request_id`, the actual sealed `lock` CAS reference,
and `instance`. The store must already exist. The runner derives the reviewed
server command from its seal and rechecks both fresh role inventories. A separate
command override rejects. Evidence must be outside both instance and store.
The version-1 resolver is also callable for the client role. The version-2
vanilla worker launcher below adds bounded execution for that explicit profile.

This is first-launch preflight, not ongoing custody: arguments retain their
reviewed spelling, absolute executable pins remain host-specific, and runtime
dependency/isolation checks remain required. Once a game mutates the instance,
use a separately qualified recovery policy; do not strip state to force this
check to pass. The original real vanilla request remains VERIFIED and unsealed,
so this runner correctly refuses it. [Source/process checks and actual refusal](../verification/2026-09-22-pack-launch.md).

Inspect the existing Mineflayer npm installation without reinstalling it:

```powershell
mcbench pack inspect-npm-runtime C:/StrataSource/backends/mineflayer C:/StrataPrivate/archives-sha512 C:/StrataPrivate/reviewed-shims > C:/StrataPrivate/npm-runtime.json
```

The archive directory uses the SHA-512 layout `aa/bb/rest-of-hex`. The separate
reviewed shim directory mirrors every declared `node_modules/.bin` path,
including nested dependencies. Preserve generator source/license pins and its
procedure privately; the command does not authenticate arbitrary supplied shim
bytes. It verifies the entire installed tree and emits private
`NpmInstalledRuntime/1` with scope limits. Publish a reviewed report using the
existing `pack evidence` command when appropriate. [Actual verification and
retained failures](../verification/2026-09-22-mineflayer-runtime.md).

For the active vanilla Mineflayer client, `LaunchProfile/2` pins `worker_runtime`
(`path`, `sha256`), `worker_settings` (host, port, username, private auth-cache
reference, wall and primitive limits), and
`update_policy: sealed-local-bytes/no-installer/1`. Its client command is the
descriptor's exact Node executable and worker entrypoint followed by the literal
`{strata.worker_config}` slot. This is implemented substitution of one typed
configuration argument, not arbitrary shell interpolation. The server command
retains the existing reviewed argument/environment contract.

After actual sealing and fresh materialization, write an operator-only binding
with `store`, `request_id`, `lock` and `instance`. The separate invocation contains
exactly `campaign_id`, `agent_id`, `epoch`, `lease_id`, `state_directory` and
`configuration_path`. State must be an existing empty private directory; the
configuration must not exist and its parent must exist. Neither may overlap
the store, installation, runtime, credentials or checkout.

```powershell
mcbench pack launch-worker --binding C:/StrataPrivate/binding.json --invocation C:/StrataPrivate/invocation.json --evidence C:/StrataPrivate/import-check --import-only
```

The import-only invocation consumes its fresh configuration path; preserve it
and use new invocation paths for a later worker run. Omit `--import-only` to
start and own both the matching server and worker. Both roles are resolved before
the server creates world/log files. It performs the fixed import check first,
starts the server, waits for readiness, then launches the prepared worker with
the generated configuration. The worker grant remains in the private state directory for the
scoped CLI/broker. No inference is dispatched. The operator command retains
bounded logs, preparation/process elapsed times and owned-stop evidence, while
`HeldPackWorker` exposes the same lifecycle for a future joint native launcher.
The server has an 80-second readiness bound, the worker's pinned exposure and a
120-second normal-save window, with a separate lifetime watchdog. Failed readiness,
worker startup, logs, exits or shutdown retain failure and owned cleanup. These
development limits do not replace D13's emergency shutdown gate.

The original vanilla request is now SEALED with nine evidence-bound provisioning
checks. Its first actual materialization and held import-only invocation pass.
This does not qualify full joint gameplay: connect the existing native runner
and inventory-bound capture, then collect the changed-profile evidence. The
existing development execution/recovery remains narrower. [Actual seal/import,
source checks and retained failures](../verification/2026-09-22-vanilla-packlock.md).
