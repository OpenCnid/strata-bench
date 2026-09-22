# Complete vanilla inventory and retained typed evidence

September 22, 2026. Operator-only. M0.3a.2 remains `in_progress`; M0 is
incomplete, G0 fails and G1–G5 are not run. F01/F05/F16, N01/N04/N08,
C03/C04/C24, partial T01/T02/T06/T13 and G0 item 2.

The original vanilla request now has a **VERIFIED installed-file inventory**:
all 4,097 prepared client/server files are registered in private operator CAS.
The PackLock remains unsealed. This durable state proves the provider's file
and reference checks; it is not legal, gameplay, isolation or recovery
qualification.

## Implemented fix and source checks

The real import exposed `REFERENCE_POLICY_CONFLICT`: the exact version JSON
was already retained as `application/json`, while
[CAS.put_file](../../src/mcbench/storage.py) demanded a new generic binary
type for identical bytes. The old import remains failed, with its partial
objects retained and no inventory publication.

File import now preserves an existing operator object's media type. It still
requires the same visibility, size and hash; it reads/hashes the supplied
source even when the destination already exists. Existing metadata is never
rewritten. Agent/evaluator visibility conflicts remain rejected, and ordinary
`put` still rejects an explicit media-type change. Namespace authorization,
quotas, corruption checks, staging and event semantics are unchanged.

Executed on Windows/Python 3.12.14:

```text
pytest -q tests/test_provisioning.py tests/test_vanilla_artifacts.py tests/test_storage_controller.py tests/test_checkpoints_artifacts.py
```

**90 pass**, 7.00 s; two existing Typer/Click deprecation warnings. New cases
cover metadata/event preservation, changed source bytes, forbidden visibility
changes and continued explicit-type refusal. The existing version-2 vanilla
test now carries the original raw version JSON through inventory, sealing and
fresh materialization. These are synthetic/source tests, not real sealing or
game acceptance. Full Ruff passes.

## Retained component metadata

The prior 41 missing file references now point to exact component records
bound to role, path, artifact digest and origin. Thirty raw source documents
are retained in the same operator namespace: published POMs, exact release
license texts, available publisher source archives and the
[Minecraft distribution terms](https://www.minecraft.net/en-us/eula).

The records distinguish observed component notices from the operator's
interpretation of distribution terms for the existing private installation.
They preserve absent POM declarations, infer no blanket standalone license or
SPDX expression, assert no redistribution authority and explicitly retain
`legal_prerequisites_qualified: false`. Source references therefore do not
silently convert missing declarations into a legal certificate. No new terms
acceptance, game installation or entitlement claim occurs.

Publisher source archives add concrete evidence: DataFixerUpper has license
headers in 145 of 162 Java source files; logging has one Apache notice among
nine files. Other retained Mojang source archives have no such headers. The
exact bytes and absence remain private. The source-fetch 404s are retained
and never serve as positive evidence.

The first metadata preparation failed on the previously uncollected,
client-only blocklist POM. Four auxiliary objects/events remain retained;
installed-file import had not started. The corrected preparation first checks
the full component metadata set. The later media-type failure left 3,671
objects/events relative to the original snapshot; the corrected importer
rechecks those exact bytes instead of deleting or relabeling them.

## Actual inventory publication and limits

The corrected real `pack verify` command exits zero and publishes:

`cas:sha256:7e40e6fa1097bec8b0d991c42aa81ba92f9edd0d4f25214a8b111201b315b0d0`

An independent read-only audit passes **25/25 checks**. All **4,097 source
files and imported file references** rehash correctly.
The total change is 3,677 new operator objects and 3,678 journal events,
including the inventory publication. All 88 original object records and the
142-event prefix remain unchanged. The original version JSON keeps its exact
bytes and `application/json` metadata. Only the vanilla provisioning row's
state/inventory fields change; E9E and all 31 unrelated tables remain intact.

Original accounting stays **$0.7554 held + $0.001458 settled = $0.756858**
under the original $10 allowance. D12 remains consumed; general model
admission stays blocked. No game/model process or shared-desktop input is
used, and no Java process remains.

Private evidence is in
`C:/Users/Darian/.strata/evidence/2026-09-22-vanilla-inventory-01`: **37 files /
6,712,370 bytes**, manifest SHA-256
`e41be7634070433c5405d1572170da5685e0d2b06781c210318b1d1214ab4fa0`.
The complete set and every file reverify. Its referenced prior role bundle
also verifies unchanged across all 4,917 files. An initial read-only seal-check
helper lacked an import; that diagnostic failure is retained before the corrected
complete check. No game rerun was involved.
Continue through the reviewed **Mineflayer worker/server** launch, runtime and
update policies, remaining legal/source review and bound provisioning checks
to the actual PackLock. SPEC §7 explicitly uses Mineflayer without a renderer
for vanilla; a graphical vanilla launch is not an added G0 prerequisite.
Preserve the prepared client distribution and its compatible role inventory.

Canonical custody/clocks/recovery, scorer/setup controls, native isolation,
Mineflayer/E9E incompatibility and the five effective-file failures remain
open. D13 and every legacy 500-ms failure retain their recorded outcomes.
No broader gate is promoted by this inventory result.
