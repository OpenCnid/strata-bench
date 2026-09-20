"""Synthetic controls for the private native resource witness; no game claim."""

import copy

import pytest

from mcbench.records import GameEvent
from mcbench.storage import Fault
from pydantic import ValidationError
from strata_evaluator.craft_witness import EMPTY_COMPONENTS, qualify_click
from strata_evaluator.scorer import Scorer
from strata_evaluator.telemetry import inspect_spool
from test_evaluator import predicate
from test_telemetry import records, write


def stack(name="air", count=0):
    return {
        "item_id": f"minecraft:{name}",
        "count": count,
        "components_sha256": EMPTY_COMPONENTS,
        "components_empty": True,
    }


def plain(value):
    return {"item_id": value["item_id"], "count": value["count"], "has_nbt": False}


def sequence(example):
    values = records(example)
    values[0]["payload_schema"] = "strata/ServerStarted/3"
    values[0]["payload"].update(
        module="strata-forge1192-telemetry/0.3.0",
        config_queries=[],
        craft_capture_policy="server-result-pickup-bracket/1",
    )
    grid = [
        stack("andesite", 1)
        if i in (0, 1, 2, 3, 5)
        else stack("polished_andesite", 1)
        if i >= 6
        else stack()
        for i in range(9)
    ]
    output = stack("furnace", 1)
    recipe = {
        "recipe_id": "fixture:furnace",
        "present": True,
        "serializer": "minecraft:crafting_shaped",
        "output": plain(output),
        "ingredients": [[plain(s)] if s["count"] else [] for s in grid],
        "width": 3,
        "height": 3,
    }
    values[1]["payload"] = recipe
    before = {"slots": [output] + grid + [stack() for _ in range(36)], "cursor": stack()}
    # Nonempty unrelated metadata must stay exactly bound through the click.
    before["slots"][45] = stack("diamond", 1) | {
        "components_sha256": "a" * 64,
        "components_empty": False,
    }
    after = copy.deepcopy(before)
    after["slots"][:10] = [stack() for _ in range(10)]
    after["cursor"] = output
    base = values[2] | {"actor_ids": ["actor"], "server_tick": 20}
    shared = {
        "transaction_id": "transaction",
        "policy": "server-result-pickup-bracket/1",
        "container_id": 1,
        "score_eligible": False,
    }
    begin = base | {
        "kind": "craft_begin",
        "payload_schema": "strata/CraftBegin/1",
        "payload": shared
        | {
            "recipe_id": "fixture:furnace",
            "recipe_output": output,
            "grid_size": 9,
            "state": before,
        },
    }
    callback = base | {
        "kind": "craft_callback",
        "payload_schema": "strata/RawCraftCallback/1",
        "payload": {
            "score_eligible": False,
            "reason": "consumption_team_recipe_and_setup_provenance_unverified",
            "output_at_callback": plain(output),
            "matrix_at_callback": [plain(s) for s in grid],
        },
    }
    end = base | {
        "kind": "craft_end",
        "payload_schema": "strata/CraftEnd/1",
        "payload": shared
        | {
            "same_menu": True,
            "nested": False,
            "callback_count": 1,
            "callback": {"output": output, "grid": grid},
            "state": after,
        },
    }
    result = values[:2] + [begin, callback, end] + values[2:]
    for seq, event in enumerate(result, 1):
        event.update(seq=seq, server_event_seq=seq)
    return result


def qualify(values):
    return qualify_click(*(GameEvent.model_validate(v) for v in values[2:5]), values[1]["payload"])


def test_complete_native_resource_pair_is_private_not_a_score(example, tmp_path, database):
    values = sequence(example)
    result = qualify(values)
    assert result["consumed"] == {"minecraft:andesite": 5, "minecraft:polished_andesite": 3}
    assert result["resource_witness"] == "pass" and not result["score_eligible"]
    path = tmp_path / "spool.jsonl"
    write(path, values)
    report = inspect_spool(path, "synthetic", 1)
    assert report["craft_witnesses"] == [result] and not report["scoring_eligible"]
    for value in values[2:5]:
        with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
            Scorer(database).score("instance", predicate(), GameEvent.model_validate(value))


@pytest.mark.parametrize(
    "case",
    [
        "gift",
        "no_consumption",
        "other_loss",
        "other_metadata",
        "cursor_old",
        "output_wrong",
        "callback_wrong",
        "callback_repeated",
        "callback_absent",
        "callback_actor",
        "nested",
        "changed_menu",
        "actor",
        "tick",
        "epoch",
        "transaction",
        "recipe",
        "recipe_ingredient",
        "recipe_output",
    ],
)
def test_causal_negative_controls_retained_as_failed_witness(example, tmp_path, case):
    values = sequence(example)
    begin, callback, end = values[2:5]
    a, b = begin["payload"], end["payload"]
    if case == "gift":
        a["state"]["slots"][1:10] = [stack() for _ in range(9)]
    elif case == "no_consumption":
        b["state"]["slots"][1] = stack("andesite", 1)
    elif case == "other_loss":
        b["state"]["slots"][45] = stack()
    elif case == "other_metadata":
        b["state"]["slots"][45]["components_sha256"] = "b" * 64
    elif case == "cursor_old":
        a["state"]["cursor"] = stack("furnace", 1)
    elif case == "output_wrong":
        b["state"]["cursor"] = stack("diamond", 1)
    elif case == "callback_wrong":
        callback["payload"]["output_at_callback"] = plain(stack("diamond", 1))
    elif case == "callback_repeated":
        b["callback_count"] = 2
    elif case == "callback_absent":
        b["callback"] = None
    elif case == "callback_actor":
        callback["actor_ids"] = ["other"]
    elif case == "nested":
        b["nested"] = True
    elif case == "changed_menu":
        b["same_menu"] = False
    elif case == "actor":
        end["actor_ids"] = ["other"]
    elif case == "tick":
        end["server_tick"] = 21
        values[5]["server_tick"] = 21
        values[5]["payload"]["interval_server_ticks"] = 21
    elif case == "epoch":
        end["epoch"] = 2
    elif case == "transaction":
        b["transaction_id"] = "other"
    elif case == "recipe":
        a["recipe_id"] = "fixture:other"
    elif case == "recipe_ingredient":
        values[1]["payload"]["ingredients"][0] = [plain(stack("diamond", 1))]
    elif case == "recipe_output":
        values[1]["payload"]["output"] = plain(stack("diamond", 1))
    with pytest.raises(Fault):
        qualify(values)
    path = tmp_path / "spool.jsonl"
    write(path, values)
    if case in ("epoch", "transaction"):
        with pytest.raises(Fault):
            inspect_spool(path, "synthetic", 1)
    else:
        report = inspect_spool(path, "synthetic", 1)
        assert report["craft_witnesses"][0]["resource_witness"] == "fail"
        assert not report["scoring_eligible"]


def test_incomplete_native_click_is_not_erased_by_clean_stop(example, tmp_path):
    values = sequence(example)
    values.pop(4)
    for seq, event in enumerate(values, 1):
        event.update(seq=seq, server_event_seq=seq)
    path = tmp_path / "spool.jsonl"
    write(path, values)
    with pytest.raises(Fault, match="TELEMETRY_CRAFT_INCOMPLETE"):
        inspect_spool(path, "synthetic", 1)


def test_shaped_recipe_offset_and_mirror_are_valid_alternatives(example):
    values = sequence(example)
    a, b = values[2]["payload"], values[4]["payload"]
    grid = [stack() for _ in range(9)]
    grid[7], grid[8] = stack("andesite", 1), stack("polished_andesite", 1)
    a["state"]["slots"][1:10] = grid
    b["callback"]["grid"] = grid
    values[3]["payload"]["matrix_at_callback"] = [plain(s) for s in grid]
    values[1]["payload"].update(width=2, height=1, ingredients=[[plain(grid[8])], [plain(grid[7])]])
    assert qualify(values)["resource_witness"] == "pass"


@pytest.mark.parametrize("case", ["duplicate", "older_module"])
def test_witness_requires_unique_transaction_and_qualified_producer_schema(example, tmp_path, case):
    values = sequence(example)
    if case == "duplicate":
        values[5:5] = copy.deepcopy(values[2:5])
    else:
        values[0]["payload_schema"] = "strata/ServerStarted/2"
        values[0]["payload"]["module"] = "strata-forge1192-telemetry/0.2.0"
        values[0]["payload"].pop("craft_capture_policy")
    for seq, event in enumerate(values, 1):
        event.update(seq=seq, server_event_seq=seq)
    path = tmp_path / "spool.jsonl"
    write(path, values)
    code = "TELEMETRY_CRAFT_DUPLICATE" if case == "duplicate" else "TELEMETRY_MODULE_MISMATCH"
    with pytest.raises(Fault, match=code):
        inspect_spool(path, "synthetic", 1)


@pytest.mark.parametrize(
    "case", ["pinned", "vanilla", "wrong_artifact", "missing_hook", "mixed_policy"]
)
@pytest.mark.parametrize("version", ["0.3.1", "0.3.2"])
def test_fastbench_source_and_applied_hook_are_bound_before_witnesses(example, tmp_path, case, version):
    values = sequence(example)
    policy = "server-result-pickup-fastbench-bound/2"
    values[0]["payload_schema"] = "strata/ServerStarted/4"
    values[0]["payload"].update(
        module=f"strata-forge1192-telemetry/{version}",
        craft_capture_policy=policy,
        craft_capture_support={
            "hook_verified": True,
            "fastbench_sha256": "a2ac76078734a2506dec112cf9b6ba214528ce91e99ae5553070a88690f61c12",
        },
    )
    for index in (2, 4):
        values[index]["payload"]["policy"] = policy
    support = values[0]["payload"]["craft_capture_support"]
    if case == "vanilla":
        support["fastbench_sha256"] = None
    elif case == "wrong_artifact":
        support["fastbench_sha256"] = "0" * 64
    elif case == "missing_hook":
        support["hook_verified"] = False
    elif case == "mixed_policy":
        values[2]["payload"]["policy"] = "server-result-pickup-bracket/1"
    path = tmp_path / "spool.jsonl"
    write(path, values)
    if case in ("pinned", "vanilla"):
        report = inspect_spool(path, "synthetic", 1)
        assert report["craft_witnesses"][0]["resource_witness"] == "pass"
        assert not report["scoring_eligible"]
    else:
        with pytest.raises((Fault, ValidationError)):
            inspect_spool(path, "synthetic", 1)
