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
- `LaunchProfile`: reviewed argument arrays, exact executable hashes, working
  directories and allowlisted environment. No guessed universal Java command.
  This stores an inspected launch plan; the supervisor must enforce it at execution.
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

Remaining integration: actual official acquisition/account/terms, reviewed
bootstrap and download inventory, cold restart/expert evidence, authenticated
launch supervisor and health/stop, full transitive provenance validation, and
real vanilla followed immediately by exact-pack structured-control tests.
