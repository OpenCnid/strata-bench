"""Synthetic native reply and public contract cases; no actual JEI conformance claim."""

import copy
import json

import pytest

from mcbench.contracts import RecipeSelection
from mcbench.native_game import NativeGameClient, RECIPE_QUERY_POLICY
from mcbench.storage import Fault
from test_native_game import connection, response


@pytest.mark.parametrize("case", ["pass", "furnace", "category", "authority", "energy", "bool_energy", "large_energy",
    "boolean", "hidden", "tooltip", "reversed", "amount", "tagged", "duplicate", "custom", "zero_count", "float_count"])
def test_machine_query_boundaries_and_no_retry(monkeypatch, case):
    category = "thermal:furnace" if case == "furnace" else "thermal:crucible"
    query = {"source": "jei", "category": category, "fluid_id": "fixture:fluid", "role": "output", "after": 0}
    row = {"recipe_id": "fixture:machine", "supported": True, "category": category, "energy_rf": 4000,
           "craft_authority": "discovery_only", "output_tooltip": None,
           "slots": [{"role": "input", "ingredients": [{"kind": "item", "item_id": "fixture:input", "count": 1}]},
                     {"role": "output", "ingredients": [{"kind": "fluid", "fluid_id": "fixture:fluid", "amount_mb": 250}]}]}
    if case == "furnace":
        query.pop("fluid_id")
        query["item_id"] = "fixture:output"
        row["slots"][1]["ingredients"] = [{"kind": "item", "item_id": "fixture:output", "count": 2}]
        row["output_tooltip"] = {"kind": "additional_chance", "percent": 50}
    elif case == "category":
        row["category"] = "thermal:furnace"
    elif case == "authority":
        row["craft_authority"] = "recipe_book"
    elif case in {"energy", "bool_energy", "large_energy"}:
        row["energy_rf"] = {"energy": 0, "bool_energy": True, "large_energy": 2147483648}[case]
    elif case == "boolean":
        row["supported"] = 1
    elif case == "hidden":
        row["hidden_solution"] = "private canary"
    elif case == "tooltip":
        row["output_tooltip"] = {"kind": "chance", "percent": 50}
    elif case == "reversed":
        row["slots"].reverse()
    elif case == "amount":
        row["slots"][1]["ingredients"][0]["amount_mb"] = 0
    elif case == "tagged":
        row["slots"][1]["ingredients"][0]["nbt"] = "private canary"
    elif case == "duplicate":
        row["slots"][0]["ingredients"] *= 2
    elif case == "custom":
        row["slots"][0]["ingredients"][0]["kind"] = "custom"
    elif case in {"zero_count", "float_count"}:
        row["slots"][0]["ingredients"][0]["count"] = 0 if case == "zero_count" else 1.5
    page = {"schema": "strata/NativeRecipeQuery/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
            "revision": 1, "query": copy.deepcopy(query), "source_generation": 1, "policy": RECIPE_QUERY_POLICY,
            "recipes": [row], "next_cursor": None}
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "recipe_query" and request["args"] == query
        calls.append(method)
        return response(request, result=page)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if case in {"pass", "furnace"}:
        assert client.call("recipe_query", query) == page
    else:
        with pytest.raises(Fault):
            client.call("recipe_query", query)
    assert calls == ["POST"]
    for patch in [{"category": "minecraft:crafting", "fluid_id": "fixture:fluid"}, {"include_hidden": True},
                  {"category": "thermal:unknown"}, {"after": True}, {"after": 513},
                  {"item_id": "fixture:output", "fluid_id": "fixture:fluid"}]:
        with pytest.raises(ValueError):
            client.call("recipe_query", query | patch)
    assert calls == ["POST"]
    with pytest.raises(ValueError):
        RecipeSelection.model_validate({"query": query, "source_generation": 1, "revision": 1})
