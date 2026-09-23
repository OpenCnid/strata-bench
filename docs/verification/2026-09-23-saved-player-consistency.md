# Stopped player and snapshot consistency

M0.1d.8d; parent F01/F03/F04/F05/F09/F11/F16,
N01/N02/N04/N06/N08, C03/C04/C06/C12/C16/C17/C20/C24,
partial T01/T02/T03/T04/T06/T07/T12/T13 and G0 items 4/6.
M0 remains in_progress and G0 remains fail.

The previous recovery matcher accepted two malformed inputs: saved NBT slot36
could alias protocol hotbar slot36, and duplicate observed slots collapsed into
one dictionary entry. A private reproduction executes the previous function
against both inputs: each returns true. The corrected shared recovery/inspection
function rejects both with GAME_RECOVERY_PLAYER.

Only actual player-NBT slot ranges are accepted: 0–35,100–103 and signed-byte
−106. Hotbar, storage, armor and offhand mappings remain distinct. Duplicate
saved or observed slots, invalid occupied stack IDs/counts and occupied
nonpersisted crafting slots reject. Valid empty protocol slots and vanilla End
or Compound empty Inventory lists remain supported.

Normal-completion reconstruction previously checked only pose. It now also
compares saved dimension, health, food and occupied inventory slot/item/count
against the latest delivered observation. The live recovery admission uses the
same matcher. Independently, the stopped-component join requires player-after.dat
to match the exact hash and size of the sole playerdata .dat file in the verified
stopped-world inventory. A separately sealed unrelated copy cannot substitute.

New single-epoch NativeGameEvidenceReport/3 and recovery report/4 use their
respective evidence-join policy2. Input plans and old sealed reports remain
unchanged. The new reports explicitly say item metadata is not compared and
retain false clean-save, writer-custody and complete-checkpoint flags. This is
recorded-state consistency, not proof of every hidden player field, external
writer exclusion or atomic game/agent recovery.

## Executed verification

On Windows / Python3.12.14, the focused selection passes 196 cases:

```text
pytest tests/test_native_game_recovery.py tests/test_sealed_native_game.py tests/test_native_game_retention.py tests/test_native_game_continuation.py tests/test_native_game_evidence.py -q
```

Two subsequently added cases pass separately: valid mapping boundaries across
hotbar/storage/armor/offhand and a changed player copy with identical byte length.
Total: **198 distinct passing cases**. Tests use synthetic tags/observations and
real local capture/seal machinery. Repository-wide Ruff passes.

Read-only reconstruction then passes against these retained authentic game
archives, without rerunning Minecraft or changing any old evidence:

| Recorded execution | Original seal | New report digest |
|---|---|---|
| September22 normal-stop case04 | 2461c79170101d40665ce2f591a29b606f7ced6b1b5062192f3bd5590edb7783 | 0f35dd04c08cb30e2f7999b21424e5ece2ac0f59fcad86a5ff448774f5ab26f8 |
| September22 sealed recovery case02, including its parent | 2be1d6eecc05d8c6eccc03a7c951f5fbf803385e1fa05b7304155972c67400e0 | ed9be1ffa1b2e800642ea01b3cffedfb7aef6874bd1cf243c1aa114a7a82dd21 |

Both reports pass the additional observation/save fields and exact
player-copy/snapshot join. Their original scripted inference, cost, action,
process and failure qualifications remain unchanged. All 39 original accounting
tables compare identically before and after; exposure remains $1.795559. No
model request, game launch, replay, refund or new execution approval occurred.

Private supplemental bundle `2026-09-23-saved-player-join-01` contains the old
function reproduction, executed audit, new reports, source snapshots, accounting
comparisons and the separate FTB bytecode investigation:

- Seal: `6314c6e956b45bf1430dd95d2e1ffb042544e6b1e7a31360765193aa21f54334`
- 19 files / 281,341 bytes; complete inventory rehashed
- Result digest: `1fd4e64304e0d43ce7de65b40d56573c523e7f31481d50eeceab4eb96f748793`

The first sealing command omitted PYTHONPATH and failed before writing files;
the corrected command created and verified the seal. No game was retried.

## Remaining work

A separate read-only ASM audit inspected 57,296 classes in 263 installed/nested
JARs and found150 writes targeting the FTB data package. It confirms that the
reviewed ordinary party changes use existing hooked methods, but identifies
the manager's lifecycle singleton writes for follow-up. Raw original bytecode
alone does not prove transformed runtime coverage, dynamic invocation coverage,
history before activation or full scorer authority. No new FTB hook or coverage
qualification is claimed here.

Continue the connected private scorer/setup and authoritative save/custody,
clock and profile work. Preserve the unresolved model usage and D18 continuing
authorization; paid admission remains blocked by uncertainty. Full isolation
qualification remains deferred under D14, and M1–M7 are unchanged.
