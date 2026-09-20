"""Private persisted Thermal furnace evidence, never a gameplay API or scorer.

Read immutable copies after an independently proven clean save/stop. This
projection follows the inspected 1.19.2 Thermal/CoFH encoding. It cannot bind a
save to installed artifacts, establish input provenance or infer causal credit.
Only untagged base-slot items are supported; augmented/extended cases reject.
"""

import argparse
from pathlib import Path

from mcbench.storage import require

from .cli import write_report
from .saved_blocks import NAME, NbtReader, _read_saved_points, block_states, field

POLICY = "saved-thermal1192-furnace-base-plain/1"
FURNACE = "thermal:machine_furnace"


def furnace_states(raw, chunk_x, chunk_z, points):
    # Validate the real persisted block as well as the independent entity ID;
    # a stale/orphaned entity cannot establish that a machine exists here.
    blocks = block_states(raw, chunk_x, chunk_z, points)
    require(all(block["block_id"] == FURNACE for block in blocks), "SAVED_MACHINE_BLOCK_MISMATCH")
    root = NbtReader(raw).root()
    subtype, entries = field(root, "block_entities", 9)
    require(subtype in (0, 10) and (subtype == 10 or not entries)
            and len(entries) <= 4096, "SAVED_MACHINE_ENTITIES_INVALID")
    wanted = set(points)
    selected = {}
    for entry in entries:
        entity = entry.value
        position = tuple(field(entity, axis, 3) for axis in ("x", "y", "z"))
        if position not in wanted:
            continue
        require(position not in selected, "SAVED_MACHINE_DUPLICATE")
        require(field(entity, "id", 8) == FURNACE, "SAVED_MACHINE_ENTITY_MISMATCH")
        require("keepPacked" not in entity or field(entity, "keepPacked", 1) == 0,
                "SAVED_MACHINE_NOT_LOADED")
        # Legacy augment lists can override ItemInv on load. Do not silently
        # ignore a second inventory source, fluid storage or extended resources.
        require("Augments" not in entity, "SAVED_MACHINE_UNSUPPORTED")
        # Forge writes an empty compound for this authentic unaugmented tile.
        # A nonempty capability can carry extra resources and remains unsupported.
        if "ForgeCaps" in entity:
            require(not field(entity, "ForgeCaps", 10), "SAVED_MACHINE_UNSUPPORTED")
        if "TankInv" in entity:
            tank_kind, tanks = field(entity, "TankInv", 9)
            require(tank_kind in (0, 10) and not tanks, "SAVED_MACHINE_UNSUPPORTED")
        energy = field(entity, "Energy", 3)
        require(0 <= energy <= 2**31 - 1, "SAVED_MACHINE_ENERGY_INVALID")
        process = {name: field(entity, name, 3) for name in ("Proc", "ProcMax", "ProcTick")}
        require(all(0 <= n <= 2**31 - 1 for n in process.values()), "SAVED_MACHINE_PROCESS_INVALID")
        active = field(entity, "Active", 1)
        require(active in (0, 1), "SAVED_MACHINE_ACTIVE_INVALID")
        slots = [None, None, None]
        if "ItemInv" in entity:
            item_kind, items = field(entity, "ItemInv", 9)
            require(item_kind in (0, 10) and (item_kind == 10 or not items)
                    and len(items) <= 3, "SAVED_MACHINE_INVENTORY_UNSUPPORTED")
            for item in items:
                value = item.value
                require(set(value) == {"Slot", "id", "Count"}, "SAVED_MACHINE_ITEM_UNSUPPORTED")
                slot = field(value, "Slot", 1)
                require(0 <= slot < 3 and slots[slot] is None, "SAVED_MACHINE_SLOT_INVALID")
                item_id, count = field(value, "id", 8), field(value, "Count", 1)
                require(0 < len(item_id) <= 256 and NAME.fullmatch(item_id)
                        and item_id != "minecraft:air" and 1 <= count <= 64, "SAVED_MACHINE_ITEM_INVALID")
                slots[slot] = {"item_id": item_id, "count": count}
        selected[position] = {
            "position": dict(zip(("x", "y", "z"), position, strict=True)),
            "block_entity_id": FURNACE, "energy_rf": energy, "active": bool(active),
            "persisted_process_fields": process, "slots": slots,
        }
    require(set(selected) == wanted, "SAVED_MACHINE_MISSING")
    return [{**block, **selected[point]} for block, point in zip(blocks, points, strict=True)]


def read_saved_furnaces(world: Path, dimension: str, points: list[tuple[int, int, int]], *, is_example: bool):
    result = _read_saved_points(world, dimension, points, is_example=is_example, decode=furnace_states)
    result["machines"] = result.pop("rows")
    return {"schema": "strata/SavedMachineReference/1", "policy": POLICY,
            "artifact_binding_proven": False, **result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--dimension", required=True)
    parser.add_argument("--point", action="append", nargs=3, type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--is-example", action="store_true")
    args = parser.parse_args(argv)
    report = read_saved_furnaces(args.world, args.dimension, [tuple(p) for p in args.point],
                                 is_example=args.is_example)
    write_report(args.output, report)


if __name__ == "__main__":
    main()
