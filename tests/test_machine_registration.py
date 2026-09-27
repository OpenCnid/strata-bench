"""Synthetic registered-source payloads; actual transformed Forge remains required."""
import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.machine_capture import (POLICY_V2, KINDS_V2, FurnaceRegistration,
    NativeFurnaceCompletionV2, require_capture_scope)
from strata_evaluator.scorer import Scorer
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_capture import (capture, completion, reference, native, history, clocked,  # noqa: F401
    globals_history, team_history, fields_history, sink, module15, append_capture)
from test_setup_control import source
from test_evaluator import predicate, register
from test_telemetry import write


def registration(converted=False):
    return {"policy": "thermal1192-native-recipe-registration/1", "generation": 1,
        "origin": "converted_cooking" if converted else "direct",
        "source_recipe_id": "minecraft:iron_ingot_from_smelting_iron_ore" if converted else "thermal:smelting_iron",
        "source_recipe_type": "minecraft:smelting" if converted else "thermal:furnace",
        "source_serializer_id": "minecraft:smelting" if converted else "thermal:furnace",
        "machine_recipe_id": "thermal:observed_converted_id" if converted else "thermal:smelting_iron"}


@pytest.fixture
def registered(capture):  # noqa: F811
    capture["payload_schema"] = KINDS_V2["machine_completion"]
    capture["payload"].update(policy=POLICY_V2, registration=registration())
    return capture


def module16(events):
    module15(events)
    events[0]["payload_schema"] = "strata/ServerStarted/16"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.15", machine_capture_policy=POLICY_V2)
    events[0]["payload"]["machine_capture_support"]["registration_hooks_verified"] = True


@pytest.mark.parametrize("converted", [False, True])
def test_observed_lineage_retains_both_source_ids_without_scoring(registered, database, converted):
    registered["payload"]["registration"] = registration(converted)
    event = GameEvent.model_validate(registered)
    parsed = require_capture_scope(event, True, POLICY_V2)
    assert parsed.registration.source_recipe_id == registration(converted)["source_recipe_id"]
    assert not parsed.recipe_registration_bound and not parsed.loaded_code_authenticated and not parsed.score_eligible
    scorer, p = Scorer(database), predicate("machine")
    register(scorer, "instance", p, event)
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        scorer.score("instance", p, event)
    assert database.connection.execute("select count(*) from predicate_state").fetchone()[0] == 0


@pytest.mark.parametrize("field,value", [("generation", 0), ("generation", 9007199254740992),
    ("generation", True), ("source_recipe_id", "thermal:other"), ("source_recipe_type", "minecraft:smelting"),
    ("source_serializer_id", "minecraft:smelting"), ("origin", "guessed"), ("policy", "unknown")])
def test_direct_binding_cannot_accept_invalid_or_converted_identity(field, value):
    body = registration()
    body[field] = value
    with pytest.raises((Fault, ValidationError)):
        FurnaceRegistration.model_validate(body)


@pytest.mark.parametrize("field,value", [("source_recipe_type", "thermal:furnace"),
    ("source_serializer_id", "thermal:furnace"), ("machine_recipe_id", "minecraft:guessed")])
def test_conversion_keeps_its_actual_recipe_domain(field, value):
    body = registration(True)
    body[field] = value
    with pytest.raises((Fault, ValidationError)):
        FurnaceRegistration.model_validate(body)


@pytest.mark.parametrize("change", ["missing", "old_policy", "bound", "authenticated", "extra"])
def test_registration_is_required_but_does_not_grant_authority(registered, change):
    body = registered["payload"]
    if change == "missing":
        del body["registration"]
    elif change == "old_policy":
        body["policy"] = "thermal1192-native-furnace-phases/1"
    elif change == "bound":
        body["recipe_registration_bound"] = True
    elif change == "authenticated":
        body["loaded_code_authenticated"] = True
    else:
        body["registration"]["source_object_address"] = "invented"
    with pytest.raises((Fault, ValidationError)):
        NativeFurnaceCompletionV2.model_validate(body)


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("converted", [False, True])
def test_signed_source_lineage_and_prefix_inspection(fields_history, registered, tmp_path, converted):  # noqa: F811
    events = fields_history[2]
    module16(events)
    registered["payload"]["registration"] = registration(converted)
    append_capture(events, registered)
    folder, authority, path, boot = source(fields_history, tmp_path)
    assert startup_prefix(folder, authority, boot)["history"]["phase"] == "startup"
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert result["machine_capture"]["transactions"] == 1
    assert not result["machine_capture"]["recipe_registration_bound"] and not result["scoring_eligible"]


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["old_module", "old_event", "rollback", "missing_hook", "numeric_hook", "wrong_module"])
def test_exact_reader_profile_and_monotonic_generation(fields_history, registered, tmp_path, change):  # noqa: F811
    events = fields_history[2]
    module16(events)
    first = append_capture(events, registered)
    if change == "old_module":
        module15(events)
    elif change == "old_event":
        first["payload_schema"] = "strata/NativeFurnaceCompletion/1"
    elif change == "rollback":
        second = copy.deepcopy(registered)
        first["payload"]["registration"]["generation"] = 2
        second["payload"]["transaction_id"] = "second"
        append_capture(events, second)
    elif change == "missing_hook":
        del events[0]["payload"]["machine_capture_support"]["registration_hooks_verified"]
    elif change == "numeric_hook":
        events[0]["payload"]["machine_capture_support"]["registration_hooks_verified"] = 1
    else:
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.14"
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_online_generation_rollback_has_no_durable_receipt(sink, fields_history, registered):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    launch = first["payload"]["launch_identity"]
    module16(fields_history[2])
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload_schema"] = "strata/ServerStarted/16"
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    broker._event(canonical(first) + b"\n", identity, key)
    event = first | {k: registered[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=[])
    event["payload"]["registration"]["generation"] = 2
    broker._event(canonical(event) + b"\n", identity, key)
    event = copy.deepcopy(event)
    event.update(seq=3, server_event_seq=3)
    event["payload"].update(transaction_id="second")
    event["payload"]["registration"]["generation"] = 1
    with pytest.raises(Fault, match="MACHINE_REGISTRATION_ROLLBACK"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("reason", ["native_registration_unobserved", "native_registration_changed"])
def test_signed_registration_refusals_remain_explicit(fields_history, registered, tmp_path, reason):  # noqa: F811
    module16(fields_history[2])
    registered.update(kind="machine_capture_refused", payload_schema=KINDS_V2["machine_capture_refused"])
    registered["payload"] = {k: v for k, v in registered["payload"].items()
                             if k not in {"states", "resolved_recipe", "registration"}}
    registered["payload"]["reason"] = reason
    append_capture(fields_history[2], registered)
    _, authority, path, _ = source(fields_history, tmp_path)
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert result["kind_counts"]["machine_capture_refused"] == 1
    assert not result["scoring_eligible"]
