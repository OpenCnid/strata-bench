# Metadata-bound vanilla acquisition

September 21, 2026. Operator-only. M0.3a.1; F01/F05/F16, N01/N04/N08,
C03/C04/C24, partial T01/T02/T13 and G0 item 2. M0 remains incomplete,
G0 fails, and G1–G5 are not run.

The original durable vanilla request was still `RESOLVED`, despite existing
official workflow and game evidence. It is now **ACQUIRED** with a version-2
receipt and both exact distributions in private CAS. Inventory and sealed-lock
fields remain null. This closes distribution intake only.

## Implemented behavior and source verification

`vanilla_artifacts.py` joins retained official manifest/metadata bytes to the
exact 1.19.2 release, Java version, client/server URLs, sizes and published SHA-1
values. Each streamed artifact must also match its receipt SHA-256. Version-2
receipts require both metadata references in the same operator namespace;
source verification is recomputed before acquisition. The importer and later
template sealing accept the explicit new receipt type. Old receipt reports keep
their old meaning. The operator evidence command can retain source JSON bytes
exactly, within its quota, instead of canonicalizing a hashed source document.

Forty distinct focused tests pass: the original 39-test provisioning/metadata
selection plus the added version-2 seal/materialize path. The changed CLI path
was rechecked after its input-size bound was added. Tests cover changed artifact
bytes with a self-consistent receipt, wrong size/hash/release/Java/role/origin,
duplicate or missing release entries, changed raw metadata, duplicate JSON keys,
foreign namespace, missing proof and unsupported receipt target. All these use
synthetic metadata/artifacts; they do not prove official acquisition or gameplay.
Two existing Typer/Click deprecation warnings remain. Full Ruff and whitespace
checks pass.

## Authentic source and durable import

Fresh official HTTPS metadata was retained from Mojang's version manifest and
the selected [1.19.2 version metadata](https://piston-meta.mojang.com/v1/packages/ed548106acf3ac7e8205a6ee8fd2710facfa164f/1.19.2.json).
The web reader could not open the JSON endpoint; the private acquisition used
certificate-verified HTTPS with exact final URLs and bounded response sizes.
Response observations and raw bytes remain private. This is retained operator
source evidence, not a signed upstream attestation.

| Distribution | Bytes | SHA-256 |
|---|---:|---|
| Pristine vanilla client 1.19.2 | 21,644,740 | `e1ac65de9b471b6916cc457fdcff00c1bafac17027aa79100c4df893b3d956db` |
| Existing official vanilla server 1.19.2 | 45,609,512 | `b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96` |

The existing shared CurseForge client JAR is different: 20,022,012 bytes,
SHA-256 `14ac8adb372c63c6bba59394b89d02f675f3423e926c7906a2fc6abcb2c2f4fb`.
It lacks `META-INF/MANIFEST.MF`, `META-INF/MOJANGCS.RSA` and
`META-INF/MOJANGCS.SF`. All 18,355 shared archive entries have identical
uncompressed bytes; no other entry was added or changed. The cause and runtime
equivalence are not claimed. A private copy preserves this finding, and the
actual version-2 importer rejects it with `VANILLA_DISTRIBUTION_MISMATCH` while
leaving the request unresolved. The installed copy was not replaced.

The authentic receipt binds the existing CurseForge vanilla profile observation
and its earlier official-workflow evidence. The current signed CurseForge.exe
is separately pinned at observed ProductVersion 1.321.1.39714 and SHA-256
`6ce9052bcb76b5d50ca8137456255b32a09df58ff0c33147f33057005f132beb`; the
historical E9E receipt's launcher pin is retained unchanged. The existing Temurin
17 JRE pin is unchanged. No new launcher session, game, terms acceptance, model
request or shared-desktop input was needed.

The actual CLI imports the pristine pair as
`cas:sha256:573173402f63051cd14ecb860f57d6e8a78700a4e24487bfcee763952a38e09a`.
Identical re-import adds no event; both CAS distributions verify. Two operator
script errors are retained: invoking the module without its configured CLI entry
point produced no output or acquisition, and a post-import audit used the DB
column name `sealed` instead of the status API's `lock`. Durable state was read
before continuing; the successful acquisition was not replaced or rolled back.

Independent before/after checks preserve all 31 non-intake tables, all 73 existing
objects and the exact 126-event journal prefix. Only nine operator-visible
objects in the vanilla namespace and ten artifact/acquisition events were added.
Only the original vanilla row's state/receipt changed; E9E is unchanged. The
original $10 authority, $0.7554 unresolved hold, $0.001458 settled usage and
consumed D12 are unchanged. Profile and shared client bytes remain unchanged.

Raw evidence, database snapshots, metadata, artifacts and source copies are in
the private `2026-09-21-vanilla-acquisition-01` bundle. The 24-file / 42,832,056-byte seal was independently rechecked, with manifest
SHA-256 `a6eea060d89595133fc0db95baa4bbad7533b3ac0c0e3f7042df8a8ad3cb8103`.
Distribution CAS objects were separately rehashed; the existing server JAR remains
in private CAS/download storage.

## Remaining closure work

Complete compatible installed-role inventories and every transitive file's
provenance, exact launch/runtime configuration and update policy, cold restart,
and the real sealed PackLock. Resolve the shared client's packaging disposition
explicitly; do not relabel the downloaded pristine artifact as the currently
installed cache. E9E's five effective-file failures, Mineflayer incompatibility,
scorer/isolation, recovery, accounting hold and other G0 gaps remain open. This
work adds no game-conformance or release claim.
