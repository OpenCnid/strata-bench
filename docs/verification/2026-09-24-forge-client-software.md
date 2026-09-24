# Exact E9E client software preparation

M0.3a.4d is **verified** for preparing the selected client software. The actual
result contains 3,786 files / 832,122,144 bytes. Its 93 classpath entries and
eight module paths match the retained authentic Forge launch in exact order;
all eight additional loader-selected files are present. Corrected audit passes
14/14, and 72 distinct focused source tests pass. E9E remains ACQUIRED;
complete role assembly, launch qualification and sealing remain open.

Coverage: M0.3a.4/.4d; F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T13, G0 item 2. M0 stays in_progress and G0 fail. D14's
isolation deferral and M1–M7 remain unchanged.

The [client producer](../../src/mcbench/forge_client.py) and original
[provisioning consumer](../../src/mcbench/provisioning.py) bind the exact
official Forge installer, the original sealed vanilla inventory/PackLock and
the acquired reproduced SRG artifact. They copy only named software into a
fresh independent directory, without launcher account state, downloads or
execution. Complete pre/post source scans, bounded copies and output hashes
reject missing, changed, extra, linked or mismatched content. Failed partial
outputs cannot be reused. Original license references retain their source
namespace; new library license metadata is collected without claiming that
the complete license review is finished.

The selection preserves the sealed vanilla Java runtime and assets, both
original vanilla version files, 60 vanilla libraries, 32 Forge classpath
libraries, five FML/universal runtime files, extra/SRG/patched JARs, and the
reviewed Forge version alias/metadata. Four older vanilla libraries are
explicitly superseded: JNA/JNA-platform 5.10.0 by 5.12.1 and Log4j API/core
2.17.0 by 2.19.0. The artifact/classifier identity determines replacement.
Unselected cache files never enter the prepared tree.

The retained CurseForge version JSON is hash-pinned and compared with the
official installer version JSON after only the reviewed transformations:
version alias, equivalent UTC timestamps, removal of comment/empty logging,
assets/minimum-launcher fields, the version alias in the ignore list and
Forge CDN library URLs. Arbitrary JVM or library changes reject. Original
publisher hashes still verify the library bytes. The successful launch's
credential-bearing game arguments are not copied into this evidence projection;
only its classpath/module paths and template hash are retained.

One actual preparation succeeded. The first independent audit reported 13/14
because it compared the raw SQLite state tuple against a JSON-loaded list.
All dependency, file and accounting checks already passed. An offline
correction normalizes serialization, rechecks the unchanged authority and
passes 14/14; both audit versions remain retained. No preparation, game,
installer, mapping processor or model request was replayed.

| Evidence | SHA-256 / CAS digest |
|---|---|
| Original acquired software report | `e139d2465bb84f23b5eae2199f9fc446d944b88db7e290f9f355fffcc962e6c4` |
| Initial audit: 13/14 | `bda30cfacb7a235a29373d9ef0df618fce5eb7197225aaf6306eb4b74a850add` |
| Corrected audit: 14/14 | `58e5c9f9a05dd8662addf0a214bad0e9595bdd0303410965de71f5a0d4154b57` |
| Launch dependency projection | `d639bc74381a5d8f189695715fc537b2defb35550038f9f8adf80f0f80c0168e` |
| Control seal: 25 files / 26,154,050 bytes | `fba30b0421587b91cb1d1c0d488e053eb565ba67e58ade10e344f7b87857e91c` |
| Software archive 01 seal | `c89c9e653a33f2991990cb1c5ccd04bfe512ed3167109ae841cfeaa1e2e525b1` |
| Software archive 02 seal | `bfb800bf1325b7dcc350fc3c67ecdebfba068b0132c355c79489bebf3720a5ea` |
| Software archive 03 seal | `532f6c32b32468d3b4d650a074fc909dc3a4c36fb08ee9dba9cab8ffbdecace5` |

Private `2026-09-24-forge-client-software-01` retains raw preparation. Its
separate `-control` and three `-archiveNN` bundles preserve every prepared file
through bounded ordered PAX archive parts, with full member/hash readback
without extraction. Existing 128-MiB object / 512-MiB bundle limits remain.
The control manifest binds all archive seals and the prepared directories.

Executed `python -X utf8 -m pytest tests/test_forge_client.py tests/test_forge_derivation.py tests/test_provisioning.py -q`:
65 passed in 15.75 seconds with two existing Typer/Click deprecations. Seven
additional acquisition/cohort consumer cases extend the final client selection
to 19 passed in 6.31 seconds, for **72 distinct passing tests** overall. Cases
cover independent copying, explicit replacements, unrelated cache omission,
corruption, missing/extra files, wrong SRG role, arbitrary launcher changes,
mid-copy changes/partial retention, and wrong acquisition/sealed base bindings.
Ruff passes after three style-only findings were corrected.

All 37 non-artifact authority tables and every old artifact/event row remain
unchanged; only the client preparation object and its event append. Original
committed/reserved exposure stays **$2.831942/$10**, with every unresolved hold
retained. No game, model, desktop input, installer or processor executes.

Next combine this software with the prepared vendor content, server libraries
plus reproduced SRG and sealed Java, harness/effective settings, explicit role
exclusions and license dispositions. Then use existing inventory/seal admission
and verify the resulting launch configuration. This preparation alone does not
qualify cold startup, expert settings, private scoring or the complete E9E role.
The previously verified GPT-6 Luna/Mineflayer pilot remains unchanged.
