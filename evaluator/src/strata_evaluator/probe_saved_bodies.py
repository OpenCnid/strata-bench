"""Private 1.19.2 saved-player binding. No live-state or account authority.

The full decompressed NBT digest includes state not projected below (effects,
attributes, respawn, recipes, ender inventory and custom tags). Never expose
these records or raw saved data through gameplay observations.
"""

import hashlib
import math
import uuid
from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Name, Ref, Strict
from mcbench.storage import require

from .saved_blocks import DATA_VERSION, MAX_COMPRESSED, NbtReader, field, unpack_chunk
from .setup_facts import UUID

POLICY = "registered-vanilla1192-saved-bodies/1"


class SavedProbeBody(Strict):
    schema_: Literal["strata/PrivateVanillaProbeBody/1"] = Field(alias="schema")
    player_uuid: UUID
    player_file: Ref
    nbt_sha256: Digest
    dimension: Name
    position: list[float] = Field(min_length=3, max_length=3)
    rotation: list[float] = Field(min_length=2, max_length=2)
    health: float = Field(ge=0)
    food: int = Field(ge=0, le=20)
    selected_slot: int = Field(ge=0, le=8)
    game_mode: int = Field(ge=0, le=3)


def saved_body(payload):
    """Derive a declaration from exact bounded gzip player data, before sealing."""
    raw = unpack_chunk(payload, 1)
    root = NbtReader(raw).root()
    require(field(root, "DataVersion", 3) == DATA_VERSION, "PROBE_BODY_VERSION")
    identity = field(root, "UUID", 11)
    require(len(identity) == 16, "PROBE_BODY_UUID")

    def coordinates(name, kind, length):
        subtype, entries = field(root, name, 9)
        require(subtype == kind and len(entries) == length, "PROBE_BODY_COORDINATES")
        result = [v.value for v in entries]
        require(all(math.isfinite(v) for v in result), "PROBE_BODY_COORDINATES")
        return result

    subtype, inventory = field(root, "Inventory", 9)
    require(subtype == 10 or subtype == 0 and not inventory, "PROBE_BODY_INVENTORY")
    seen = set()
    for item in inventory:
        slot = field(item.value, "Slot", 1)
        require((0 <= slot <= 35 or 100 <= slot <= 103 or slot == -106)
                and slot not in seen, "PROBE_BODY_INVENTORY")
        seen.add(slot)
        name, count = field(item.value, "id", 8), field(item.value, "Count", 1)
        from .saved_blocks import NAME
        require(NAME.fullmatch(name) and name != "minecraft:air" and 1 <= count <= 127,
                "PROBE_BODY_INVENTORY")
    return SavedProbeBody.model_validate({
        "schema": "strata/PrivateVanillaProbeBody/1",
        "player_uuid": str(uuid.UUID(bytes=bytes(identity))),
        "player_file": "cas:sha256:" + hashlib.sha256(payload).hexdigest(),
        "nbt_sha256": hashlib.sha256(raw).hexdigest(),
        "dimension": field(root, "Dimension", 8),
        "position": coordinates("Pos", 6, 3),
        "rotation": coordinates("Rotation", 5, 2),
        "health": field(root, "Health", 5), "food": field(root, "foodLevel", 3),
        "selected_slot": field(root, "SelectedItemSlot", 3),
        "game_mode": field(root, "playerGameType", 3),
    }).model_dump(by_alias=True)


def verify_saved_bodies(pair, private, read_world):
    """Require all declared bodies to match distinct registered saved players.

    read_world accepts only registered CAS refs and a compressed-byte limit;
    private reads only evaluator records. Neither callback is agent supplied.
    Additional historical player saves may remain in the world; this does not
    assign them an executor or certify a complete live online roster.
    """
    members = pair["common"]["members"]
    require(len(members) == pair["common"]["n"], "PROBE_COMPLETE_ROSTER")
    bodies, seen = {}, set()
    for agent, member in members.items():
        body = SavedProbeBody.model_validate(private(member["body_state"]))
        require(body.player_uuid not in seen, "PROBE_BODY_IDENTITY_REUSED")
        seen.add(body.player_uuid)
        name = "world/playerdata/" + body.player_uuid + ".dat"
        require(pair["world_files"].get(name) == body.player_file, "PROBE_BODY_WORLD_MISMATCH")
        actual = saved_body(read_world(body.player_file, MAX_COMPRESSED))
        require(actual == body.model_dump(by_alias=True), "PROBE_BODY_STATE_MISMATCH")
        bodies[agent] = {"body_ref": member["body_state"], "player_path": name, "state": actual}
    return {"policy": POLICY, "bodies": bodies, "saved_state_verified": True,
            "live_initial_state_verified": False, "account_assignment_verified": False}
