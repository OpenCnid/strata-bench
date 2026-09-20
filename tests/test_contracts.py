"""Synthetic SPEC records and negative cases, not real-game acceptance."""

import copy
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.contracts import ActionAck, ActionBatch, Observation, RpcRequest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    data["schema"]: data
    for text in re.findall(
        r"```json\s*(.*?)```", (ROOT / "SPEC.md").read_text(encoding="utf-8"), re.S
    )
    if (data := json.loads(text))
}


@pytest.mark.parametrize("model", [Observation, ActionBatch, ActionAck])
def test_spec_examples_roundtrip(model):
    example = EXAMPLES[f"mcbench/{model.__name__}/1"]
    value = model.model_validate(example)
    assert value.model_dump() == example
    schema = json.loads((ROOT / "schemas/v1/public" / f"{model.__name__}.json").read_text())
    expected = model.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert schema == expected


@pytest.mark.parametrize(
    "patch",
    [
        {"seq": -1},
        {"seq": True},
        {"seq": "1"},
        {"seq": 2**53},
        {"schema": "mcbench/ActionBatch/2"},
        {"unknown": 1},
        {"campaign_id": "../private"},
        {"duration_ms": 30001},
        {"release_at_end": False},
        {"release_at_end": 1},
        {"deadline_at": "2026-02-31T12:00:00Z"},
        {"action": None},
        {"mode": "input"},
        {"action": {"kind": "eval", "text": "bot"}},
    ],
)
def test_invalid_envelope(patch):
    data = EXAMPLES["mcbench/ActionBatch/1"] | patch
    with pytest.raises((ValidationError, ValueError)):
        ActionBatch.model_validate(data)


def test_quest_open_is_explicit_source_bound_and_cannot_submit_or_select_hidden_quests():
    action = {"kind": "quest_ui", "operation": "open", "source": "ftb_quests",
              "source_generation": 1, "expected_catalog_revision": 1}
    batch = EXAMPLES["mcbench/ActionBatch/1"] | {"is_example": False, "duration_ms": 10000, "action": action}
    assert ActionBatch.model_validate(batch).action.model_dump() == action
    for patch in [{"operation": "claim"}, {"source": "server"}, {"source_generation": True},
                  {"source_generation": -1}, {"source_generation": 1.0}, {"expected_catalog_revision": "1"},
                  {"expected_catalog_revision": 2**53}, {"team_id": "private"}, {"quest_id": "hidden"}]:
        with pytest.raises(ValueError):
            ActionBatch.model_validate(batch | {"action": action | patch})
    for key in action:
        with pytest.raises(ValueError):
            ActionBatch.model_validate(batch | {"action": {k: v for k, v in action.items() if k != key}})
    with pytest.raises(ValueError):
        ActionBatch.model_validate(batch | {"duration_ms": 10001})


def test_close_window_is_explicit_revision_bound_and_rejects_extra_actions():
    original = EXAMPLES["mcbench/ActionBatch/1"] | {"is_example": False, "duration_ms": 10000,
        "action": {"kind": "close_window", "window_id": 1, "expected_window_revision": 4}}
    assert ActionBatch.model_validate(original).action.kind == "close_window"
    for patch in [{"window_id": -1}, {"window_id": True}, {"expected_window_revision": "4"},
                  {"drop": True}, {"kind": "close_all"}]:
        with pytest.raises(ValueError):
            ActionBatch.model_validate(original | {"action": original["action"] | patch})
    with pytest.raises(ValueError):
        ActionBatch.model_validate(original | {"duration_ms": 10001})


def test_craft_source_selection_is_explicit_strict_and_preserves_book_default():
    action = {"kind": "craft", "recipe_id": "test:recipe", "count": 1, "window_id": 0, "expected_window_revision": 1}
    batch = EXAMPLES["mcbench/ActionBatch/1"] | {"is_example": False, "duration_ms": 10000, "action": action}
    assert ActionBatch.model_validate(batch).action.recipe_selection is None
    selection = {"source_generation": 1, "revision": 2,
                 "query": {"source": "jei", "category": "minecraft:crafting", "item_id": "test:output", "role": "output", "after": 0}}
    accepted = ActionBatch.model_validate(batch | {"action": action | {"recipe_selection": selection}})
    assert accepted.action.recipe_selection.model_dump() == selection
    for patch in [{"source_generation": -1}, {"source_generation": True}, {"revision": "2"},
                  {"private_solver": True}, {"query": selection["query"] | {"include_hidden": True}},
                  {"query": selection["query"] | {"category": "all"}}]:
        with pytest.raises(ValueError):
            ActionBatch.model_validate(batch | {"action": action | {"recipe_selection": selection | patch}})


@pytest.mark.parametrize(
    "action,duration",
    [
        ({"kind": "look_at", "target": {"x": float("nan"), "y": 64, "z": 0}}, 1000),
        ({"kind": "look_at", "target": {"x": 0, "y": 64, "z": 0}}, 10001),
        (
            {
                "kind": "place",
                "support": {"x": 0, "y": 64, "z": 0},
                "face": {"x": 1, "y": 1, "z": 0},
                "expected_item_id": "minecraft:stone",
            },
            1000,
        ),
        ({"kind": "use_item", "hand": "main", "hold_ms": 2001}, 3000),
        ({"kind": "use_item", "hand": "main", "hold_ms": 1000}, 500),
        ({"kind": "chat", "text": "\U0001f600" * 257}, 1000),
    ],
)
def test_action_bounds(action, duration):
    with pytest.raises(ValidationError):
        ActionBatch.model_validate(
            EXAMPLES["mcbench/ActionBatch/1"] | {"action": action, "duration_ms": duration}
        )


def test_private_item_metadata_and_oversized_state_rejected():
    o = copy.deepcopy(EXAMPLES["mcbench/Observation/1"])
    o["state"]["inventory"] = [
        {
            "slot": 0,
            "item_id": "minecraft:stone",
            "count": 1,
            "component_summary": {"hidden_canary": "private"},
        }
    ]
    with pytest.raises(ValidationError):
        Observation.model_validate(o)
    o["state"]["inventory"] = []
    o["age_at_send_ms"] = 0
    with pytest.raises(ValidationError):
        Observation.model_validate(o)


def test_unknown_effects_and_incomplete_receipts_are_not_success():
    a = EXAMPLES["mcbench/ActionAck/1"]
    for patch in (
        {"status": "unknown", "requires_resync": False},
        {"result_observation_id": None},
        {"completed_mono_ms": None},
    ):
        with pytest.raises(ValidationError):
            ActionAck.model_validate(a | patch)


def test_spatial_cursor_is_additive_and_bound_to_its_method():
    old_request = dict(schema="strata/GameRequest/1", request_id="r", campaign_id="c",
                       agent_id="a", epoch=1, deadline_at="2026-09-18T00:00:00Z",
                       method="observe", action=None, target_request_id=None, after=None)
    assert RpcRequest.model_validate(old_request).cursor is None
    assert RpcRequest.model_validate(old_request | {"method": "observe.page", "cursor": "opaque"})
    for patch in ({"method": "observe.page"}, {"cursor": "opaque"}, {"cursor": "../private"},
                  {"method": "observe.page", "cursor": "opaque", "after": 0}):
        with pytest.raises(ValidationError):
            RpcRequest.model_validate(old_request | patch)


def test_carried_item_projection_is_bounded_and_does_not_expose_nbt():
    example = copy.deepcopy(EXAMPLES["mcbench/Observation/1"])
    example["state"]["window"] = dict(id=0, revision=1, type="minecraft:inventory", slots=[],
                                    cursor_item=dict(item_id="minecraft:stone", count=3,
                                                     component_summary={}))
    assert Observation.model_validate(example).state.window.cursor_item.count == 3
    example["state"]["window"]["cursor_item"]["component_summary"] = {"nbt": "private"}
    with pytest.raises(ValidationError):
        Observation.model_validate(example)
    example["state"]["window"]["cursor_item"] = None
    assert Observation.model_validate(example).state.window.cursor_item is None
