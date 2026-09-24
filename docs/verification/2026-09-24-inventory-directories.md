# Directory-preserving installed inventories

M0.3a.4f is **verified** for the source contract and synthetic inventory → seal →
materialization → launch/capture/restore round trip. **230 distinct focused tests**
pass. A read-only audit of the actual prepared E9E roles passes **10/10**, and the
original sealed vanilla inventory passes **3/3** compatibility checks. This fixes
a concrete dependency of G0 item 2; it does not qualify E9E startup or seal it.

The old inventory recorded files only. Materialization recreated their parent
directories, losing 13 client and 14 server directories from the prepared E9E
roles. Launch preflight also rejected those directories if copied independently.
The lost paths include client `natives` and server `kubejs/assets`,
`kubejs/client_scripts`, `local` and `packmenu`, along with empty vendor config
paths. This is a reproducible layout defect, not evidence of a failed game launch.

| Actual initial role | Files rehashed | Bytes | Complete directories | Lost by file-only layout |
|---|---:|---:|---:|---:|
| Client | 13,628 | 1,208,220,163 | 1,489 | 13 |
| Server | 8,819 | 650,842,622 | 1,108 | 14 |

Coverage: M0.3a.4/.4f; F01/F05/F09/F16, N01/N04/N06/N08,
C03/C04/C16/C19; partial T01/T02/T07/T13, G0 item 2 and existing vanilla
restoration regression. No unrelated M1–M7 work or new canonical record type.

## Implemented behavior

[RoleInventoryInput](../../src/mcbench/provisioning.py) accepts explicit
`extra_directories`. File-parent closure plus these paths must exactly match both
stopped source trees before any file import. Existing path, link, private-content
and reviewed vendor exceptions remain enforced. Case collisions, duplicates,
file/directory conflicts, missing/unlisted directories and mid-copy changes fail.

[InstalledInventory/2](../../src/mcbench/inventory.py) binds complete sorted
`directories.client` and `directories.server` lists, including every parent.
It is emitted only when directories extend the file-parent layout. File-only
inventories retain /1 bytes and idempotent identity. The /1 reader rejects a
silently added directory field; /2 rejects incomplete, unordered, foreign-role or
unsafe lists. No existing PackLock is rewritten.

[Materialization](../../src/mcbench/provisioning.py) creates the bound directories
in fresh staging. [Launch preflight](../../src/mcbench/pack_launch.py) compares
both complete file and directory sets. [Vanilla capture](../../src/mcbench/vanilla_persistence.py)
and [restore](../../src/mcbench/pack_restore.py) preserve sealed software
directories, including empty Java/library paths, in addition to saved world
directories. They reject removal at capture, snapshot verification and restored
launch. This retains the existing narrow vanilla software/state policy; arbitrary
new runtime roots, E9E recovery and clean-save authority are not qualified.

## Verification

Windows, Python 3.12; repository source on PYTHONPATH. No model or Minecraft
execution. Synthetic attestation fixtures remain explicitly synthetic.

```text
python -X utf8 -m pytest tests/test_inventory_directories.py tests/test_provisioning.py tests/test_pack_launch.py tests/test_pack_restore.py tests/test_vanilla_persistence.py -q --disable-warnings --maxfail=3
# 136 passed, 2 warnings, 47.55 seconds
python -X utf8 -m pytest tests/test_inventory_directories.py tests/test_pack_restore.py::test_directory_bound_template_capture_restore_and_recapture tests/test_pack_worker.py tests/test_pack_baseline.py tests/test_role_composition.py tests/test_e9e_content.py -q --disable-warnings --maxfail=3
# 115 passed, 2 warnings, 62.83 seconds; 21 repeated cases, 230 distinct total
```

The second selection also verifies two added assertions: missing pinned empty
directory refuses capture before output and cannot be omitted from an archived
snapshot. Changed Python files pass Ruff. Initial local checks caught a removed
`os` import (three failures), then an unregistered test fixture (four passes/three
setup errors); a fixture-import shadowing lint issue was also corrected. These
local development failures and final results are retained in `verification.json`.

The actual role audit rehashes every file, checks the original composition-plan
binding, reproduces the legacy directory loss, and compares the new directory
closure. It does not submit the prospective inventory to authority. A separate
read-only check confirms the original vanilla inventory
`7e40e6fa1097bec8b0d991c42aa81ba92f9edd0d4f25214a8b111201b315b0d0`
still contains 4,097 files and derives the same 445 client/149 server directories.

Private evidence bundle `2026-09-24-inventory-directories-01` retains audit,
source, verification and before/after authority hashes: 15 files / 129,504 bytes.
Full bundle readback passes. Pins:

- Seal: `5e81b810912bff26766042f9b4ef652fb10cf29c45aa685aec2f5ac6034cffc6`.
- Role audit: `77511ecd82e6f662ff57168c07b1c8d397cd7b2dd13386654633eacd8b4cd55b`.
- Original composition plan: `b3c3a50472ed88ea47f12520b333498ae17d431af88f7abde59c25143fc413f4`.

All **39 authority tables** are unchanged; no CAS/event rows append. E9E stays
ACQUIRED and the original vanilla lock stays SEALED. Exposure remains
**$2.831942/$10**, with all unresolved/full envelopes retained.

Next create a fresh controlled working instance from the retained initial roles
and qualify expert initialization/cold restart and generated effective settings.
Only then submit the final inventory/profile through existing admission. Preserve
all original preparation evidence and the successful D19.5 LLM/Mineflayer pilot;
do not replay unchanged game tests. M0 stays in_progress, G0 fail, and D14
isolation deferral and every later milestone remain unchanged.
