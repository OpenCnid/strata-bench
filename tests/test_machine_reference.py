"""Synthetic sealed-machine references; no protected scoring qualification."""

import copy

import pytest
from pydantic import ValidationError

from mcbench.storage import Database, Fault, digest
from strata_evaluator.craft_reference import CraftReferencePlanV4, CraftReferenceStore, parse_plan
from strata_evaluator.machine_reference import MachineReference
from strata_evaluator.protected_reference import ProtectedReferencePlan
from test_craft_reference import seal
from test_machine_registration import (registered, capture, completion, fields_history, team_history,  # noqa: F401
    globals_history, clocked, history, native, reference, module16, append_capture)
from test_machine_resource import expected
from test_protected_reference import plan  # noqa: F401
from test_setup_facts import TEAM


def machine_plan(record, start=0, end=1000):
    p = record["payload"]
    recipe = expected(record)
    return {"policy": "thermal1192-private-machine-reference/1", "start_server_tick": start,
        "cutoff_server_tick": end, "targets": {"furnace": {"dimension": p["dimension"],
        "position": list(p["position"]), "block_id": p["block_id"],
        "registration_origin": p["registration"]["origin"],
        "machine_recipe_ids": {recipe["recipe_id"]: p["registration"]["machine_recipe_id"]},
        "recipes": {recipe["recipe_id"]: recipe}, "minimum_output": 1}}}


def configure(fixture, record, *, emit=True):
    _, setup, events, _, _ = fixture
    setup["cutoff_server_tick"] = 30
    setup.update(schema="strata/PrivateCraftReferencePlan/4",
        machine_reference=machine_plan(record, setup["start_server_tick"], setup["cutoff_server_tick"]))
    module16(events)
    if emit:
        append_capture(events, record)
    return setup["machine_reference"]


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_sealed_machine_plan_authenticated_join_and_idempotent_reopen(fields_history, registered):  # noqa: F811
    store, setup, _, _, spool = fields_history
    configure(fields_history, registered)
    parsed = parse_plan(setup)
    assert isinstance(parsed, CraftReferencePlanV4)
    receipt, authority, _ = seal(fields_history)
    assert authority.setup_digest == receipt["setup_digest"] == digest(setup)
    result = store.inspect("i", spool)
    machine = result["machine_reference"]
    assert machine["plan_digest"] == digest(setup["machine_reference"])
    assert machine["targets"]["furnace"] == {"candidate_output": 1, "candidate_complete": True}
    assert len(machine["accepted_resource_witnesses"]) == 1
    assert not machine["rejected_resource_witnesses"] and not machine["scoring_eligible"]
    assert not result["scoring_authority_qualified"]
    cursor = store.database.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0]
    reopened = Database(store.database.path)
    try:
        assert CraftReferenceStore(reopened).inspect("i", spool) == result
        assert reopened.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0] == cursor
    finally:
        reopened.close()


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change,reason", [("position", "MACHINE_UNREGISTERED_LOCATION"),
    ("dimension", "MACHINE_UNREGISTERED_LOCATION"), ("window", "MACHINE_OUTSIDE_TICK_WINDOW"),
    ("recipe", "MACHINE_REGISTERED_RECIPE_MISMATCH"), ("source", "MACHINE_UNREGISTERED_RECIPE"),
    ("gift", "MACHINE_CONSUMPTION_UNPROVEN"), ("refusal", "MACHINE_NATIVE_REFUSED")])
def test_sealed_expectation_rejects_unmatched_completion(fields_history, registered, change, reason):  # noqa: F811
    store, setup, events, _, spool = fields_history
    ref = configure(fields_history, registered)
    target = ref["targets"]["furnace"]
    captured_event = next(e for e in events if e["kind"] == "machine_completion")
    if change == "position":
        target["position"][0] += 1
    elif change == "dimension":
        target["dimension"] = "minecraft:the_end"
    elif change == "window":
        setup["cutoff_server_tick"] = ref["cutoff_server_tick"] = 1
    elif change == "recipe":
        next(iter(target["recipes"].values()))["recipe_energy_rf"] += 1
    elif change == "source":
        lineage = captured_event["payload"]["registration"]
        lineage["source_recipe_id"] = lineage["machine_recipe_id"] = "thermal:another"
    elif change == "gift":
        states = captured_event["payload"]["states"]
        states[2]["slots"][0] = copy.deepcopy(states[0]["slots"][0])
    else:
        captured_event.update(kind="machine_capture_refused", payload_schema="strata/NativeFurnaceRefusal/2")
        for key in ("states", "resolved_recipe", "registration"):
            captured_event["payload"].pop(key)
        captured_event["payload"]["reason"] = "native_validation_failed"
    seal(fields_history)
    result = store.inspect("i", spool)["machine_reference"]
    assert result["targets"]["furnace"] == {"candidate_output": 0, "candidate_complete": False}
    assert [x["reason"] for x in result["rejected_resource_witnesses"]] == [reason]


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_connected_idle_stream_has_zero_machine_output(fields_history, registered):  # noqa: F811
    configure(fields_history, registered, emit=False)
    seal(fields_history)
    result = fields_history[0].inspect("i", fields_history[4])["machine_reference"]
    assert result["targets"]["furnace"] == {"candidate_output": 0, "candidate_complete": False}
    assert result["accepted_resource_witnesses"] == result["rejected_resource_witnesses"] == []


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["duplicate", "old_profile", "truncated", "tampered_plan"])
def test_invalid_import_has_no_durable_receipt(fields_history, registered, change):  # noqa: F811
    store, _, events, directory, spool = fields_history
    configure(fields_history, registered)
    if change == "duplicate":
        append_capture(events, registered)
    elif change == "old_profile":
        from test_machine_capture import module15
        module15(events)
        events[:] = [e for e in events if e["kind"] != "machine_completion"]
        from test_setup_facts import renumber
        renumber(events)
    seal(fields_history)
    if change == "truncated":
        spool.write_bytes(spool.read_bytes().rsplit(b'\n', 2)[0] + b'\n')
    elif change == "tampered_plan":
        # The sealed plan is durable; changes cannot be imported as the old seal.
        with store.database.transaction() as db:
            db.execute("UPDATE craft_reference_seals SET body='{}' WHERE instance='i'")
    with pytest.raises((Fault, ValidationError, KeyError)):
        store.inspect("i", spool)
    assert store.database.connection.execute("SELECT COUNT(*) FROM craft_reference_imports").fetchone()[0] == 0


@pytest.mark.parametrize("change", ["overlap", "alias", "recipe_id", "window", "position", "mixed_output"])
def test_invalid_plan_rejects_before_sealing(registered, change):  # noqa: F811
    value = machine_plan(registered)
    target = value["targets"]["furnace"]
    key = next(iter(target["recipes"]))
    if change == "overlap":
        value["targets"]["second"] = copy.deepcopy(target)
    elif change == "alias":
        target["machine_recipe_ids"][key] = "thermal:wrong"
    elif change == "recipe_id":
        target["recipes"][key]["recipe_id"] = "thermal:wrong"
    elif change == "window":
        value["cutoff_server_tick"] = value["start_server_tick"]
    elif change == "position":
        target["position"][0] = 2**31
    else:
        other = copy.deepcopy(target["recipes"][key])
        other.update(recipe_id="thermal:other")
        other["output"]["item_id"] = "minecraft:gold_ingot"
        target["recipes"]["thermal:other"] = other
        target["machine_recipe_ids"]["thermal:other"] = "thermal:other"
    with pytest.raises((Fault, ValidationError)):
        MachineReference.model_validate(value)


def test_protected_launch_digest_includes_machine_plan(plan, registered):  # noqa: F811
    setup = plan["setup"]
    setup.update(schema="strata/PrivateCraftReferencePlan/4", required_history_policy="native-e9e-setup-mutation-watch/6",
        native_team_ids=dict.fromkeys(setup["roster"], TEAM),
        machine_reference=machine_plan(registered, setup["start_server_tick"], setup["cutoff_server_tick"]))
    plan["launch"]["setup_digest"] = digest(setup)
    parsed = ProtectedReferencePlan.model_validate(plan)
    assert isinstance(parsed.setup, CraftReferencePlanV4)
    setup["machine_reference"]["targets"]["furnace"]["minimum_output"] += 1
    with pytest.raises((Fault, ValidationError)):
        ProtectedReferencePlan.model_validate(plan)


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("converted", [False, True])
def test_registered_alternate_and_converted_strategy_remain_distinct(fields_history, registered, converted):  # noqa: F811
    from test_machine_registration import registration
    registered["payload"]["registration"] = registration(converted)
    ref = configure(fields_history, registered, emit=False)
    target = ref["targets"]["furnace"]
    alternative = copy.deepcopy(registered)
    lineage = alternative["payload"]["registration"]
    source_id = "minecraft:alternative" if converted else "thermal:alternative"
    lineage["source_recipe_id"] = source_id
    lineage["machine_recipe_id"] = "thermal:second_conversion" if converted else source_id
    target["recipes"][source_id] = expected(alternative)
    target["machine_recipe_ids"][source_id] = lineage["machine_recipe_id"]
    append_capture(fields_history[2], alternative)
    seal(fields_history)
    result = fields_history[0].inspect("i", fields_history[4])["machine_reference"]
    witness = result["accepted_resource_witnesses"][0]["witness"]
    assert witness["recipe_id"] == source_id
    assert witness["registration"] == lineage
    assert result["targets"]["furnace"]["candidate_output"] == 1


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_separate_machine_targets_cannot_borrow_each_others_output(fields_history, registered):  # noqa: F811
    ref = configure(fields_history, registered)
    other = copy.deepcopy(ref["targets"]["furnace"])
    other["position"][0] += 1
    ref["targets"]["second"] = other
    ref["targets"]["furnace"]["minimum_output"] = 2
    seal(fields_history)
    result = fields_history[0].inspect("i", fields_history[4])["machine_reference"]
    assert result["targets"] == {"furnace": {"candidate_output": 1, "candidate_complete": False},
        "second": {"candidate_output": 0, "candidate_complete": False}}
