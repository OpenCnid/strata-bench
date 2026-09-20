"""Synthetic save-format cases; authentic machine operation is a separate gate."""

import copy
import json

import pytest

from mcbench.storage import Fault
from strata_evaluator.saved_machines import FURNACE, furnace_states, main, read_saved_furnaces
from test_saved_blocks import chunk, region_file, root_bytes, section


def entity(x=0):
    return {"x": (3, x), "y": (3, 0), "z": (3, 0), "id": (8, FURNACE),
            "Energy": (3, 20000), "Active": (1, 0), "Proc": (3, 0),
            "ProcMax": (3, 2000), "ProcTick": (3, 20),
            "Facing": (1, 2), "Sides": (7, bytes(6))}


def item(slot=0, item_id="minecraft:raw_iron", count=1):
    return {"Slot": (1, slot), "id": (8, item_id), "Count": (1, count)}


def machine_chunk(entities=None):
    value = chunk(sections=[section(palette=[{"Name": (8, FURNACE),
        "Properties": (10, {"facing": (8, "north"), "active": (8, "false")})}])])
    value["block_entities"] = (9, (10, entities if entities is not None else [entity()]))
    return value


def decode(value, points=None):
    return furnace_states(root_bytes(value), 0, 0, points or [(0, 0, 0)])


def test_empty_and_plain_slots_retain_energy_process_and_block():
    e = entity()
    e["ForgeCaps"] = (10, {})
    empty = decode(machine_chunk([e]))[0]
    assert empty["slots"] == [None] * 3 and empty["energy_rf"] == 20000
    e["ItemInv"] = (9, (10, [item(1, "minecraft:iron_ingot", 3), item()]))
    full = decode(machine_chunk([e]))[0]
    assert full["slots"] == [{"item_id": "minecraft:raw_iron", "count": 1},
                             {"item_id": "minecraft:iron_ingot", "count": 3}, None]
    assert full["block_id"] == full["block_entity_id"] == FURNACE
    assert full["persisted_process_fields"] == {"Proc": 0, "ProcMax": 2000, "ProcTick": 20}


@pytest.mark.parametrize("name,value,code", [
    ("id", (8, "minecraft:furnace"), "ENTITY_MISMATCH"),
    ("Energy", (3, -1), "ENERGY_INVALID"),
    ("Active", (1, 2), "ACTIVE_INVALID"),
    ("Proc", (3, -1), "PROCESS_INVALID"),
    ("keepPacked", (1, 1), "NOT_LOADED"),
    ("Augments", (9, (0, [])), "UNSUPPORTED"),
    ("ForgeCaps", (10, {"test:extra": (3, 1)}), "UNSUPPORTED"),
    ("TankInv", (9, (10, [{}])), "UNSUPPORTED"),
    ("Facing", (1, 0), "ORIENTATION_INVALID"),
    ("Facing", (1, 1), "ORIENTATION_INVALID"),
    ("Facing", (1, 3), "ORIENTATION_INVALID"),
    ("Facing", (1, -1), "ORIENTATION_INVALID"),
    ("Sides", (7, bytes(5)), "SIDES_INVALID"),
    ("Sides", (7, bytes(7)), "SIDES_INVALID"),
    ("Sides", (7, bytes([5, 0, 0, 0, 0, 0])), "SIDES_INVALID"),
    ("Sides", (7, bytes([255, 0, 0, 0, 0, 0])), "SIDES_INVALID"),
    ("ItemInv", (9, (8, ["bad"])), "INVENTORY_UNSUPPORTED"),
])
def test_wrong_partial_and_unsupported_persistence(name, value, code):
    e = entity()
    e[name] = value
    with pytest.raises(Fault, match="^SAVED_MACHINE_" + code + "$"):
        decode(machine_chunk([e]))


@pytest.mark.parametrize("entries,code", [
    ([item(3)], "SLOT_INVALID"), ([item(), item()], "SLOT_INVALID"),
    ([item(count=0)], "ITEM_INVALID"), ([item(count=65)], "ITEM_INVALID"),
    ([item(item_id="minecraft:air")], "ITEM_INVALID"),
    ([item(item_id="bad:id with spaces")], "ITEM_INVALID"),
    ([item() | {"tag": (10, {})}], "ITEM_UNSUPPORTED"),
    ([item() | {"IntCount": (3, 500)}], "ITEM_UNSUPPORTED"),
    ([item() | {"ForgeCaps": (10, {})}], "ITEM_UNSUPPORTED"),
])
def test_no_silent_slot_component_or_quantity_loss(entries, code):
    e = entity()
    e["ItemInv"] = (9, (10, entries))
    with pytest.raises(Fault, match="^SAVED_MACHINE_" + code + "$"):
        decode(machine_chunk([e]))


def test_missing_duplicate_or_orphaned_entity_never_becomes_empty_machine():
    with pytest.raises(Fault, match="SAVED_MACHINE_MISSING"):
        decode(machine_chunk([]))
    with pytest.raises(Fault, match="SAVED_MACHINE_DUPLICATE"):
        decode(machine_chunk([entity(), entity()]))
    value = machine_chunk()
    value["sections"] = (9, (10, [section()]))
    with pytest.raises(Fault, match="SAVED_MACHINE_BLOCK_MISMATCH"):
        decode(value)


def test_missing_fields_and_wrong_numeric_types_reject():
    for key in ("Energy", "Proc", "Active", "id", "Facing", "Sides"):
        e = entity()
        del e[key]
        with pytest.raises(Fault, match="SAVED_CHUNK_FIELD_INVALID"):
            decode(machine_chunk([e]))
    e = entity()
    e["Energy"] = (1, 20)
    with pytest.raises(Fault, match="SAVED_CHUNK_FIELD_INVALID"):
        decode(machine_chunk([e]))


@pytest.mark.parametrize(("code", "name"), [(2, "north"), (3, "south"), (4, "west"), (5, "east")])
def test_each_horizontal_orientation_and_known_side_modes(code, name):
    e = entity()
    e["Facing"] = (1, code)
    e["Sides"] = (7, bytes([0, 1, 2, 3, 4, 0]))
    value = machine_chunk([e])
    value["sections"] = (9, (10, [section(palette=[{"Name": (8, FURNACE),
        "Properties": (10, {"facing": (8, name), "active": (8, "false")})}])]))
    assert decode(value)[0]["properties"]["facing"] == name


def test_projection_selection_order_source_hashes_and_no_eligibility(tmp_path):
    e = entity(1)
    e["Energy"] = (3, 0)
    value = machine_chunk([entity(), e, entity(2)])
    before = copy.deepcopy(value)
    region_file(tmp_path / "region", value)
    result = read_saved_furnaces(tmp_path, "minecraft:overworld", [(1, 0, 0), (0, 0, 0)], is_example=True)
    assert [m["energy_rf"] for m in result["machines"]] == [0, 20000]
    assert len(result["sources"]) == 1 and len(result["sources"][0]["nbt_sha256"]) == 64
    assert result["is_example"] and value == before
    for key in ("artifact_binding_proven", "snapshot_consistency_proven", "action_causality_proven",
                "registry_membership_verified", "scoring_provenance_supported"):
        assert result[key] is False


def test_cli_writes_private_digest_envelope(tmp_path):
    world = tmp_path / "world"
    region_file(world / "region", machine_chunk())
    out = tmp_path / "report.json"
    main(["--world", str(world), "--dimension", "minecraft:overworld", "--point", "0", "0", "0",
          "--output", str(out), "--is-example"])
    result = json.loads(out.read_bytes())
    assert result["schema"] == "strata/ReportArtifact/1"
    assert result["report"]["schema"] == "strata/SavedMachineReference/1"
