"""Synthetic completion brackets; no authentic producer or machine scoring claim."""

import copy

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, digest
from strata_evaluator.craft_witness import EMPTY_COMPONENTS
from strata_evaluator.machine_witness import POLICY, qualify_furnace_completion
from strata_evaluator.scorer import Scorer
from test_evaluator import predicate, register


def stack(item="minecraft:air", count=0):
    return {"item_id": item, "count": count, "components_sha256": EMPTY_COMPONENTS,
            "components_empty": True}


@pytest.fixture
def completion(example):
    recipe = {"policy": "thermal1192-furnace-plain-recipe/1", "recipe_id": "thermal:iron_ingot",
        "input": stack("emendatusenigmatica:iron_dust", 1), "output": stack("minecraft:iron_ingot", 1),
        "output_chance": 1, "recipe_energy_rf": 4000}
    state = {"slots": [stack("emendatusenigmatica:iron_dust", 3), stack("minecraft:iron_ingot", 2),
                       stack("minecraft:diamond", 1)],
             "augments": [stack(), stack()], "energy_rf": 8000, "process": 0,
             "process_max": 4000, "process_tick": 20, "active": True}
    body = {"policy": POLICY, "transaction_id": "completion1", "dimension": "minecraft:overworld",
        "position": [1, 70, -2], "block_id": "thermal:machine_furnace",
        "recipe_digest": digest(recipe), "state": state, "score_eligible": False}
    kinds = [("machine_resolve_begin", "strata/MachineResolveBegin/1"),
             ("machine_outputs_resolved", "strata/MachineOutputsResolved/1"),
             ("machine_inputs_resolved", "strata/MachineInputsResolved/1")]
    events = []
    for i, (kind, schema) in enumerate(kinds):
        payload = copy.deepcopy(body)
        if i >= 1:
            payload["state"]["slots"][1]["count"] = 3
        if i == 2:
            payload["state"]["slots"][0]["count"] = 2
        events.append(GameEvent.model_validate(example("GameEvent") | {
            "is_example": False, "kind": kind, "payload_schema": schema,
            "server_event_seq": 20+i, "server_tick": 500, "actor_ids": [], "payload": payload}))
    return events, recipe


def qualify(value):
    events, recipe = value
    return qualify_furnace_completion(*events, recipe)


def mutate(value, index, change):
    events, _ = value
    event = events[index].model_dump()
    change(event)
    events[index] = GameEvent.model_validate(event)


def test_complete_bracket_preserves_exact_deltas_and_no_score_authority(completion):
    events, recipe = completion
    result = qualify(completion)
    assert result["resource_witness"] == "pass"
    assert result["consumed"] == {"emendatusenigmatica:iron_dust": 1}
    assert result["produced"] == {"minecraft:iron_ingot": 1}
    assert result["recipe_digest"] == digest(recipe)
    assert result["source_event_digests"] == [digest(e.model_dump()) for e in events]
    assert all(result[k] is False for k in ("producer_authenticated", "setup_team_qualified",
        "sustained_operation_verified", "energy_consumption_verified", "fluid_consumption_verified",
        "scoring_eligible"))
    assert "energy_consumed" not in result


def test_consumed_last_input_and_previously_empty_output(completion):
    for index in range(3):
        def patch(event, i=index):
            event["payload"]["state"]["slots"][0] = (
                stack("emendatusenigmatica:iron_dust", 1) if i < 2 else stack())
            event["payload"]["state"]["slots"][1] = (
                stack() if i == 0 else stack("minecraft:iron_ingot", 1))
        mutate(completion, index, patch)
    assert qualify(completion)["resource_witness"] == "pass"


@pytest.mark.parametrize("field,value", [("campaign_id", "foreign"), ("epoch", 2),
    ("server_boot_id", "foreign"), ("server_tick", 501), ("server_event_seq", 23)])
def test_scope_or_sequence_change_rejects(completion, field, value):
    mutate(completion, 1, lambda e: e.update({field: value}))
    with pytest.raises(Fault, match="MACHINE_BOUNDARY_SCOPE"):
        qualify(completion)


@pytest.mark.parametrize("index", range(3))
def test_examples_or_guessed_actor_cannot_supply_machine_attribution(completion, index):
    mutate(completion, index, lambda e: e.update(actor_ids=["a1"]))
    with pytest.raises(Fault, match="MACHINE_ACTOR_UNPROVEN"):
        qualify(completion)
    mutate(completion, index, lambda e: e.update(actor_ids=[], is_example=True))
    with pytest.raises(Fault, match="MACHINE_PRIVATE_EVIDENCE_REQUIRED"):
        qualify(completion)


@pytest.mark.parametrize("field,value", [("transaction_id", "foreign"),
    ("dimension", "minecraft:the_nether"), ("position", [2, 70, -2]),
    ("recipe_digest", "f"*64)])
def test_machine_or_recipe_identity_change_rejects(completion, field, value):
    mutate(completion, 1, lambda e: e["payload"].update({field: value}))
    with pytest.raises(Fault, match="MACHINE_BOUNDARY_IDENTITY"):
        qualify(completion)


@pytest.mark.parametrize("field,value", [("energy_rf", 4000), ("process", -20),
    ("process_max", 5000), ("process_tick", 40), ("augments", [stack()])])
def test_completion_cannot_hide_other_processing_or_resource_changes(completion, field, value):
    mutate(completion, 2, lambda e: e["payload"]["state"].update({field: value}))
    with pytest.raises(Fault, match="MACHINE_OTHER_RESOURCES_CHANGED"):
        qualify(completion)


def test_incomplete_processing_cannot_supply_finished_witness(completion):
    for index in range(3):
        mutate(completion, index, lambda e: e["payload"]["state"].update(process=20))
    with pytest.raises(Fault, match="MACHINE_OTHER_RESOURCES_CHANGED"):
        qualify(completion)


def test_charge_slot_full_identity_change_rejects(completion):
    mutate(completion, 1, lambda e: e["payload"]["state"]["slots"][2].update(
        components_sha256="a"*64, components_empty=False))
    with pytest.raises(Fault, match="MACHINE_OTHER_RESOURCES_CHANGED"):
        qualify(completion)


@pytest.mark.parametrize("kind", ["gift", "underconsumed", "overconsumed", "no_output", "excess_output"])
def test_input_and_output_must_match_one_registered_operation(completion, kind):
    if kind in ("gift", "underconsumed", "overconsumed"):
        count = 3 if kind == "gift" else 2 if kind == "underconsumed" else 1
        if kind == "underconsumed":
            completion[1]["input"]["count"] = 2
            for index in range(3):
                mutate(completion, index, lambda e: e["payload"].update(recipe_digest=digest(completion[1])))
        mutate(completion, 2, lambda e: e["payload"]["state"]["slots"][0].update(count=count))
        code = "MACHINE_CONSUMPTION_UNPROVEN"
    else:
        count = 2 if kind == "no_output" else 4
        for index in (1, 2):
            mutate(completion, index, lambda e: e["payload"]["state"]["slots"][1].update(count=count))
        code = "MACHINE_OUTPUT_UNPROVEN"
    with pytest.raises(Fault, match=code):
        qualify(completion)


@pytest.mark.parametrize("slot", (0, 1))
def test_middle_boundary_prevents_net_delta_from_masking_reordered_effects(completion, slot):
    mutate(completion, 1, lambda e: e["payload"]["state"]["slots"][slot].update(count=1))
    with pytest.raises(Fault, match="MACHINE_RESOLUTION_ORDER"):
        qualify(completion)


@pytest.mark.parametrize("item", ("minecraft:gold_ingot", "minecraft:diamond"))
def test_wrong_item_cannot_match_equal_quantities(completion, item):
    for index in (1, 2):
        mutate(completion, index, lambda e: e["payload"]["state"]["slots"][1].update(item_id=item))
    with pytest.raises(Fault, match="MACHINE_RESOURCE_IDENTITY"):
        qualify(completion)


def test_active_augment_is_explicitly_unsupported(completion):
    for index in range(3):
        mutate(completion, index, lambda e: e["payload"]["state"].update(augments=[stack("minecraft:diamond", 1)]))
    with pytest.raises(Fault, match="MACHINE_AUGMENTS_UNSUPPORTED"):
        qualify(completion)


def test_partial_duplicate_or_foreign_boundary_cannot_pass(completion):
    events, recipe = completion
    for values in ((events[0], events[0], events[2]), (events[2], events[1], events[0])):
        with pytest.raises(Fault, match="MACHINE_BOUNDARY_SCHEMA"):
            qualify_furnace_completion(*values, recipe)


@pytest.mark.parametrize("patch", [{"output_chance": .5}, {"extra": True},
    {"input": stack()}, {"recipe_energy_rf": 0}, {"output_chance": True}])
def test_unsupported_or_incomplete_recipe_does_not_gain_witness(completion, patch):
    completion[1].update(patch)
    with pytest.raises((Fault, ValidationError)):
        qualify(completion)


def test_registered_recipe_bytes_must_match_all_boundaries(completion):
    completion[1]["recipe_energy_rf"] = 1000
    with pytest.raises(Fault, match="MACHINE_BOUNDARY_IDENTITY"):
        qualify(completion)


def test_private_boundaries_remain_unscorable(completion, database):
    events, _ = completion
    scorer, p = Scorer(database), predicate("machine")
    register(scorer, "private-fixture", p, events[0])
    for event in events:
        with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
            scorer.score("private-fixture", p, event)
    assert database.connection.execute("SELECT COUNT(*) FROM predicate_state").fetchone()[0] == 0


@pytest.mark.parametrize("field,value", [("slots", [stack()]*4),
    ("augments", [stack()]*17), ("energy_rf", -1), ("energy_rf", 2**31),
    ("process", -(2**31)-1), ("active", 1), ("active", False), ("fluid_tanks", [])])
def test_malformed_or_expanded_state_is_not_silently_projected(completion, field, value):
    mutate(completion, 1, lambda e: e["payload"]["state"].update({field: value}))
    with pytest.raises((Fault, ValidationError)):
        qualify(completion)


@pytest.mark.parametrize("position", [[0, 1], [0, 1, 2, 3], [0, 0, 2**31], [True, 0, 0]])
def test_malformed_position_refuses(completion, position):
    mutate(completion, 1, lambda e: e["payload"].update(position=position))
    with pytest.raises((Fault, ValidationError)):
        qualify(completion)


@pytest.mark.parametrize("flag", [0, True])
def test_raw_completion_cannot_claim_score_eligibility(completion, flag):
    mutate(completion, 1, lambda e: e["payload"].update(score_eligible=flag))
    with pytest.raises((Fault, ValidationError)):
        qualify(completion)
