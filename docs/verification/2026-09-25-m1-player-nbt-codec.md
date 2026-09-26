# M1.6r.1 private player save-format codec

Status: **implemented_unverified** for live-player capture. M1.6r remains
in_progress; G1 remains not_run. This is a dependency of the private matched-body
witness, not a new gameplay affordance or a native admission path.

The retained native11 pair passed its owned worker/server lifecycle and ordinary
own-state projection. Read-only inspection now compares all 38 saved-player NBT
fields against the original sealed source. Both stopped exports differ from the
source in `XpSeed` and `warden_spawn_tracker`; the two arms also differ from each
other in those fields at stop. Stopped exports cannot establish
when those differences arose or prove equality at the beginning of play. No
unchanged native11 rerun was selected.

The first inspection script called nonexistent `EvidenceBundle.read_bytes` and
failed before inspecting bodies. Its script/output are retained. Replacing that
call with the existing hash-verifying `read` method passes the inspection.

[PlayerNbt](../../evaluator/java/livebody/PlayerNbt.java) binds the exact installed
official 1.19.2 `Entity.saveWithoutId`, UUID, owning-server, server-thread and
`NbtIo.write` descriptors. It accepts an exact ServerPlayer, verifies expected
UUID and the real server-thread predicate before and after serialization, and
checks the compound UUID. It retains every emitted field and returns only a
complete uncompressed compound of at most 16 MiB. It exposes no game tool,
network/file output or state restoration operation.

The installed implementation JAR SHA-256 is
`d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6`;
official mapping SHA-256 is
`e3e93dac4d886924ff3b81ce5d210925b9e4112776fdef4d0e6d5fefb062a879`.
The private archive contains inspected bytecode and individual class pins. Game
bytes and private body values are not published in this repository.

Five distinct focused tests pass using the pinned JDK17 and actual installed
server NBT classes. The first run retains three passes and one failure: an
assertion of negative-zero bit preservation failed. The real NBT reader caches
floating zero and changes `-0.0` to `+0.0`. A corrected ordinary-value round-trip
and a separate explicit normalization test then pass. The codec source did not
change between these runs. All twelve NBT types, nested/unknown fields, ordered
lists, modified UTF-8, signed numeric values, wrong receivers and bounded output
are exercised. These are synthetic data through actual installed codecs, not
live-player captures. Ruff and whitespace checks pass.

Executed commands (private output paths omitted):

```powershell
$env:PYTHONPATH='src;tools;evaluator/src'
$env:STRATA_VANILLA_SERVER_JAR='<pinned installed implementation JAR>'
python -m pytest tests/test_player_nbt.py -q
python -m pytest tests/test_player_nbt.py::test_all_tag_types_survive_actual_nbt_codec tests/test_player_nbt.py::test_actual_nbt_signed_zero_normalization_is_explicit -q
ruff check tests/test_player_nbt.py
git diff --check
```

The byte cap does not bound the game's temporary object graph or serialization
time. Save-format NBT omits transient state and the saved file's DataVersion
wrapper; numeric equality cannot prove bit preservation. Neither expected class
names nor reflection prove the loaded producer's authenticity. Exact loaded-byte
and owned-process binding, real callback/tick/sequence provenance, valid and
invalid live UUID/thread cases, overhead/side-effect checks, full state matching,
all-N readiness, tools, clocks and disposal remain required. Native probe
catalogs remain closed. No game or model was dispatched, no authority was
consumed, and no M1 spending allowance is inferred.

Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-live-body-witness-01`.

The final audit verifies 447 source pins, all 429 milestone IDs, append-only
history and 1,550 local documentation links. All 40 real authority tables remain
unchanged at $4.887796 exposure; no owned runtime remains. A documentation write
attempt returned `Invalid argument` without changing the file; the edits were
then applied successfully using the patch tool.

The private archive is sealed and independently verified: 48 files, 19,421,731
bytes, SHA-256
`9b23142694d2f3ebb08fedfa7b2ba480f57ceaf784eb54cd1612b5c2147a30b0`.
This seal pointer follows the archived documentation snapshot.
