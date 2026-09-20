"""Synthetic producer records; live evidence is stored outside the repository."""

import json

import pytest

from mcbench.storage import Fault
from strata_evaluator.scorer import Scorer
from strata_evaluator.telemetry import KINDS, assert_e9e_furnace, inspect_spool
from test_evaluator import predicate


def records(example):
    base = example("GameEvent") | {
        "is_example": False,
        "campaign_id": "synthetic",
        "epoch": 1,
        "server_boot_id": "boot",
        "actor_ids": [],
    }
    payloads = [
        (
            "server_started",
            0,
            {
                "module": "strata-forge1192-telemetry/0.1.0",
                "minecraft": "1.19.2",
                "forge": "43.4.23",
                "scoring_provenance_supported": False,
                "recipe_count": 10,
            },
        ),
        ("recipe_snapshot", 0, {"recipe_id": "minecraft:furnace", "present": False}),
        (
            "server_health",
            20,
            {
                "interval_server_ticks": 20,
                "interval_wall_ns": 1000000000,
                "durable_event_seq_before_sample": 2,
                "avatar_ticks_since_boot": {"actor": 10},
                "observed_tick_work_ns": 3000000,
                "server_average_mspt": 1.0,
                "heap_used_bytes": 1024,
                "gc_count": 1,
                "gc_time_ms": 1,
            },
        ),
        ("server_stopped", 30, {}),
    ]
    return [
        base
        | {
            "seq": i,
            "server_event_seq": i,
            "server_tick": tick,
            "kind": kind,
            "payload_schema": KINDS[kind],
            "payload": payload,
        }
        for i, (kind, tick, payload) in enumerate(payloads, 1)
    ]


def write(path, values):
    path.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")


def test_clean_spool_sequence_clocks_and_no_scoring_claim(tmp_path, example, database):
    path = tmp_path / "boot.jsonl"
    values = records(example)
    write(path, values)
    report = inspect_spool(path, "synthetic", 1)
    assert report["records"] == 4 and report["last_server_tick"] == 30
    assert report["sampled_server_ticks"] == 20 and report["avatar_ticks_at_last_sample"] == {
        "actor": 10
    }
    assert not report["scoring_eligible"] and not report["transport_identity_verified"]
    assert report["gate_result"] == "not_run"
    from mcbench.records import GameEvent

    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        Scorer(database).score("instance", predicate(), GameEvent.model_validate(values[1]))


@pytest.mark.parametrize(
    "case,code",
    [
        ("gap", "TELEMETRY_SEQUENCE_GAP"),
        ("scope", "TELEMETRY_SCOPE_MISMATCH"),
        ("boot", "TELEMETRY_BOOT_MISMATCH"),
        ("tick", "TELEMETRY_TICK_ROLLBACK"),
        ("clock", "TELEMETRY_CLOCK_MISMATCH"),
        ("avatar", "TELEMETRY_AVATAR_TICKS_INVALID"),
        ("durable", "TELEMETRY_CURSOR_INVALID"),
        ("tail", "TELEMETRY_CLEAN_STOP_MISSING"),
        ("after", "TELEMETRY_AFTER_STOP"),
        ("partial", "TELEMETRY_PARTIAL_RECORD"),
        ("duplicate", "TELEMETRY_DUPLICATE_FIELD"),
        ("spoof", "TELEMETRY_MODULE_MISMATCH"),
    ],
)
def test_corrupt_mixed_or_incomplete_stream_rejected(tmp_path, example, case, code):
    path = tmp_path / "boot.jsonl"
    values = records(example)
    if case == "gap":
        values[2]["server_event_seq"] = 4
    if case == "scope":
        values[2]["campaign_id"] = "other"
    if case == "boot":
        values[2]["server_boot_id"] = "other"
    if case == "tick":
        values[3]["server_tick"] = 19
    if case == "clock":
        values[2]["payload"]["interval_server_ticks"] = 21
    if case == "avatar":
        values[2]["payload"]["avatar_ticks_since_boot"]["actor"] = 21
    if case == "durable":
        values[2]["payload"]["durable_event_seq_before_sample"] = 3
    if case == "tail":
        values.pop()
    if case == "after":
        values.append(values[-1])
    if case == "spoof":
        values[0]["payload"]["scoring_provenance_supported"] = True
    write(path, values)
    if case == "partial":
        path.write_bytes(path.read_bytes()[:-1])
    if case == "duplicate":
        path.write_bytes(path.read_bytes().replace(b'"seq": 1', b'"seq": 1,"seq": 1'))
    with pytest.raises(Fault, match=code):
        inspect_spool(path, "synthetic", 1)


def test_exact_expert_recipe_assertions_and_negative_normal_mode():
    def stack(name):
        return {"item_id": "minecraft:" + name, "count": 1, "has_nbt": False}
    expert = {"present": True, "width": 3, "height": 3,
              "serializer": "minecraft:crafting_shaped", "output": stack("furnace"),
              "ingredients": [[stack("andesite")] for _ in range(4)] + [[], [stack("andesite")]]
              + [[stack("polished_andesite")] for _ in range(3)]}
    report = {"file_sha256": "0" * 64, "recipe_snapshots": {
        "enigmatica:expert/minecraft/shaped/furnace": expert,
        "minecraft:furnace": {"present": False}}}
    result = assert_e9e_furnace(report)
    assert result["result"] == "pass" and not result["player_crafting_verified"]
    report["recipe_snapshots"]["minecraft:furnace"]["present"] = True
    assert assert_e9e_furnace(report)["result"] == "fail"
    report["recipe_snapshots"]["minecraft:furnace"]["present"] = False
    expert["ingredients"][0] = [stack("cobblestone")]
    assert assert_e9e_furnace(report)["result"] == "fail"
    expert["ingredients"][0] = [stack("andesite")]
    expert["output"]["count"] = 2
    assert assert_e9e_furnace(report)["result"] == "fail"
