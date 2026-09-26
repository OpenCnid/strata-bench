"""Synthetic resource admission controls; authentic replay is retained privately."""

import copy

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, digest
from strata_evaluator.machine_resource import qualify_native_furnace_completion
from strata_evaluator.scorer import Scorer
from test_evaluator import predicate, register
from test_machine_registration import registered, capture, completion, registration  # noqa: F401


def expected(record):
    p = record["payload"]
    return {"policy": "thermal1192-furnace-plain-recipe/1",
        "recipe_id": p["registration"]["source_recipe_id"],
        **{k: copy.deepcopy(p["resolved_recipe"][k]) for k in
           ("input", "output", "output_chance", "recipe_energy_rf")}}


@pytest.mark.parametrize("converted", [False, True])
def test_one_actual_event_and_complete_registration_are_preserved(registered, converted):  # noqa: F811 - imported pytest fixture
    registered["payload"]["registration"] = registration(converted)
    event = GameEvent.model_validate(registered)
    original = event.model_dump()
    witness = qualify_native_furnace_completion(event, expected(registered))
    assert event.model_dump() == original
    assert witness["source_event_digests"] == [digest(original)]
    assert witness["server_event_seq"] == event.server_event_seq
    assert witness["registration"] == registered["payload"]["registration"]
    assert witness["consumed"] == {"emendatusenigmatica:iron_dust": 1}
    assert witness["produced"] == {"minecraft:iron_ingot": 1}
    assert all(witness[k] is False for k in ("producer_authenticated", "recipe_registration_bound",
        "setup_team_qualified", "sustained_operation_verified", "energy_consumption_verified",
        "fluid_consumption_verified", "scoring_eligible"))


@pytest.mark.parametrize("field", ["recipe_id", "input", "output", "recipe_energy_rf"])
def test_independent_expectation_must_match_exactly(registered, field):  # noqa: F811 - imported pytest fixture
    recipe = expected(registered)
    if field == "recipe_id":
        recipe[field] = "thermal:another_recipe"
    elif field == "recipe_energy_rf":
        recipe[field] += 1
    else:
        recipe[field]["count"] += 1
    with pytest.raises(Fault, match="MACHINE_REGISTERED_RECIPE_MISMATCH"):
        qualify_native_furnace_completion(GameEvent.model_validate(registered), recipe)


def test_converted_machine_id_cannot_replace_source_id(registered):  # noqa: F811 - imported pytest fixture
    registered["payload"]["registration"] = registration(True)
    recipe = expected(registered)
    recipe["recipe_id"] = registered["payload"]["registration"]["machine_recipe_id"]
    with pytest.raises(Fault, match="MACHINE_REGISTERED_RECIPE_MISMATCH"):
        qualify_native_furnace_completion(GameEvent.model_validate(registered), recipe)


@pytest.mark.parametrize("mutation", ["gift", "no_output", "reordered_input", "reordered_output",
    "energy", "charge", "process", "resolved_count", "wrong_output", "missing_phase", "actor",
    "example", "old_schema", "score_claim", "refusal"])
def test_invalid_native_completion_cannot_gain_resource_witness(registered, mutation):  # noqa: F811 - imported pytest fixture
    recipe = expected(registered)
    p = registered["payload"]
    a, b, c = p["states"]
    if mutation == "gift":
        c["slots"][0] = copy.deepcopy(a["slots"][0])
    elif mutation == "no_output":
        b["slots"][1] = c["slots"][1] = copy.deepcopy(a["slots"][1])
    elif mutation == "reordered_input":
        b["slots"][0] = copy.deepcopy(c["slots"][0])
    elif mutation == "reordered_output":
        b["slots"][1] = copy.deepcopy(a["slots"][1])
    elif mutation == "energy":
        c["energy_rf"] -= 1
    elif mutation == "charge":
        c["slots"][2] = copy.deepcopy(recipe["input"])
    elif mutation == "process":
        c["process"] -= 1
    elif mutation == "resolved_count":
        p["resolved_recipe"]["resolved_input_count"] += 1
    elif mutation == "wrong_output":
        for state in (b, c):
            state["slots"][1]["item_id"] = "minecraft:gold_ingot"
    elif mutation == "missing_phase":
        p["states"].pop()
    elif mutation == "actor":
        registered["actor_ids"] = ["guessed-player"]
    elif mutation == "example":
        registered["is_example"] = True
    elif mutation == "old_schema":
        registered["payload_schema"] = "strata/NativeFurnaceCompletion/1"
    elif mutation == "score_claim":
        p["score_eligible"] = True
    else:
        registered.update(kind="machine_capture_refused", payload_schema="strata/NativeFurnaceRefusal/2")
        for key in ("states", "resolved_recipe", "registration"):
            p.pop(key)
        p["reason"] = "native_validation_failed"
    with pytest.raises((Fault, ValidationError)):
        qualify_native_furnace_completion(GameEvent.model_validate(registered), recipe)


def test_successful_resource_verification_does_not_open_scorer(registered, database):  # noqa: F811 - imported pytest fixture
    event = GameEvent.model_validate(registered)
    assert qualify_native_furnace_completion(event, expected(registered))["resource_witness"] == "pass"
    scorer, p = Scorer(database), predicate("machine")
    register(scorer, "private-fixture", p, event)
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        scorer.score("private-fixture", p, event)
    assert database.connection.execute("SELECT COUNT(*) FROM predicate_state").fetchone()[0] == 0
