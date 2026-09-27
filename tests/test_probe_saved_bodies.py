"""Synthetic player NBT and strict private declarations
no live-state proof."""

import copy
import gzip
import hashlib
import struct
import uuid

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.probe_saved_bodies import SavedProbeBody, saved_body, verify_saved_bodies
from test_saved_blocks import string

PLAYER = "00000000-0000-4000-8000-000000000001"


def payload(value):
    def encode(kind, value):
        if kind in (1, 3, 5, 6):
            return struct.pack({1: ">b", 3: ">i", 5: ">f", 6: ">d"}[kind], value)
        if kind == 8:
            return string(value)
        if kind == 9:
            subtype, entries = value
            return struct.pack(">Bi", subtype, len(entries)) + b"".join(encode(subtype, v) for v in entries)
        if kind == 10:
            return b"".join(bytes([k]) + string(n) + encode(k, v) for n, (k, v) in value.items()) + b"\0"
        if kind == 11:
            return struct.pack(">i", len(value) // 4) + value
        raise AssertionError(kind)
    return gzip.compress(b"\x0a\0\0" + encode(10, value), mtime=0)


def player():
    return {"DataVersion": (3, 3120), "UUID": (11, uuid.UUID(PLAYER).bytes),
        "Pos": (9, (6, [1.5, 64., -2.])), "Rotation": (9, (5, [90., 0.])),
        "Dimension": (8, "minecraft:overworld"), "Health": (5, 20.), "foodLevel": (3, 20),
        "SelectedItemSlot": (3, 0), "playerGameType": (3, 0),
        "Inventory": (9, (10, [{"Slot": (1, 0), "id": (8, "minecraft:stone"),
                              "Count": (1, 3), "tag": (10, {"custom": (8, "retained")})}])),
        "SpawnX": (3, 20), "AbilitiesExtension": (10, {"custom": (1, 1)})}


def registered(raw=None):
    raw = payload(player()) if raw is None else raw
    body = saved_body(raw)
    ref = body["player_file"]
    pair = {"common": {"n": 1, "members": {"a1": {"body_state": "body"}}},
            "world_files": {"world/playerdata/" + PLAYER + ".dat": ref}}
    return pair, {"body": body}, {ref: raw}


def verify(pair, declarations, blobs):
    def read(ref, limit):
        assert limit == 8 * 1024**2
        assert len(blobs[ref]) <= limit
        return blobs[ref]
    return verify_saved_bodies(pair, declarations.__getitem__, read)


def test_full_saved_body_and_complete_roster_are_bound():
    pair, bodies, blobs = registered()
    second = player()
    second["UUID"] = (11, uuid.UUID(int=2).bytes)
    raw = payload(second)
    body = saved_body(raw)
    pair["common"]["n"] = 2
    pair["common"]["members"]["a2"] = {"body_state": "second"}
    pair["world_files"]["world/playerdata/" + body["player_uuid"] + ".dat"] = body["player_file"]
    bodies["second"], blobs[body["player_file"]] = body, raw
    result = verify(pair, bodies, blobs)
    assert set(result["bodies"]) == {"a1", "a2"} and result["saved_state_verified"]
    assert SavedProbeBody.model_validate(result["bodies"]["a1"]["state"]).model_dump() == bodies["body"]
    assert not result["live_initial_state_verified"] and not result["account_assignment_verified"]


@pytest.mark.parametrize("key,value", [
    ("schema", "strata/PrivateVanillaProbeBody/2"),
    ("health", 19.), ("food", 19), ("position", [1.5, 65., -2.]),
    ("rotation", [90., 2.]), ("dimension", "minecraft:the_nether"),
    ("selected_slot", 1), ("game_mode", 1), ("nbt_sha256", "a" * 64),
    ("player_uuid", str(uuid.UUID(int=4))), ("player_file", "cas:sha256:" + "b" * 64),
    ("health", float("nan")), ("extra", True), ("food", True),
])
def test_wrong_body_never_verifies(key, value):
    pair, bodies, blobs = registered()
    bodies["body"][key] = value
    with pytest.raises((Fault, ValidationError)):
        verify(pair, bodies, blobs)


@pytest.mark.parametrize("change", ["missing", "duplicate", "world_alias", "declared_uuid", "raw_drift"])
def test_missing_aliased_or_drifted_body_refuses(change):
    pair, bodies, blobs = registered()
    if change == "missing":
        pair["common"]["n"] = 2
    elif change == "duplicate":
        pair["common"]["n"] = 2
        pair["common"]["members"]["a2"] = {"body_state": "body"}
    elif change == "world_alias":
        pair["world_files"] = {}
    elif change == "declared_uuid":
        body = bodies["body"]
        body["player_uuid"] = str(uuid.UUID(int=3))
        pair["world_files"] = {"world/playerdata/" + body["player_uuid"] + ".dat": body["player_file"]}
    else:
        v = player()
        v["SpawnX"] = (3, 21)
        blobs[bodies["body"]["player_file"]] = payload(v)
    with pytest.raises(Fault):
        verify(pair, bodies, blobs)


@pytest.mark.parametrize("change", ["version", "uuid", "nan", "duplicate_slot", "bad_slot", "zero_count"])
def test_invalid_player_structure_is_rejected(change):
    v = player()
    if change == "version":
        v["DataVersion"] = (3, 3121)
    elif change == "uuid":
        v["UUID"] = (11, b"1234")
    elif change == "nan":
        v["Pos"] = (9, (6, [float("inf"), 64., 2.]))
    else:
        item = v["Inventory"][1][1][0]
        if change == "duplicate_slot":
            v["Inventory"][1][1].append(copy.deepcopy(item))
        elif change == "bad_slot":
            item["Slot"] = (1, 36)
        else:
            item["Count"] = (1, 0)
    with pytest.raises(Fault):
        saved_body(payload(v))


def test_full_nbt_covers_unprojected_equipment_abilities_and_spawn():
    v = player()
    baseline = saved_body(payload(v))
    for change in ("inventory", "spawn", "abilities"):
        modified = copy.deepcopy(v)
        if change == "inventory":
            modified["Inventory"][1][1][0]["tag"][1]["custom"] = (8, "different")
        elif change == "spawn":
            modified["SpawnX"] = (3, 21)
        else:
            modified["AbilitiesExtension"] = (10, {"custom": (1, 0)})
        body = saved_body(payload(modified))
        assert body["nbt_sha256"] != baseline["nbt_sha256"]
        assert body["player_file"] != baseline["player_file"]
        assert body["position"] == baseline["position"]


def test_compressed_identity_and_gzip_trailing_bytes_are_not_ignored():
    raw = payload(player())
    assert saved_body(raw)["player_file"] == "cas:sha256:" + hashlib.sha256(raw).hexdigest()
    with pytest.raises(Fault):
        saved_body(raw + b"trailing")
