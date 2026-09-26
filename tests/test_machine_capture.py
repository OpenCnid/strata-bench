"""Synthetic native records and ingestion; live producer/parity remain unverified."""
import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.machine_capture import (KINDS, PINS, POLICY, FurnaceSupport,
    NativeFurnaceCompletion, require_capture_scope)
from strata_evaluator.scorer import Scorer
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.telemetry import inspect_spool, ServerStartedV14, ServerStartedV15
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_witness import completion  # noqa: F401
from test_craft_reference import reference  # noqa: F401
from test_setup_facts import native, renumber  # noqa: F401
from test_setup_history import history  # noqa: F401
from test_telemetry_clocks import clocked  # noqa: F401
from test_global_setup_history import globals_history  # noqa: F401
from test_team_map_history import team_history  # noqa: F401
from test_script_field_history import fields_history  # noqa: F401
from test_telemetry_pipe import sink  # noqa: F401
from test_setup_control import source
from test_evaluator import predicate, register
from test_telemetry import write


def support():
    return {"status": "supported", "artifacts": dict(PINS), "loaded_code_authenticated": False}


@pytest.fixture
def capture(completion):  # noqa: F811
    events, recipe = completion
    resolved = {k: v for k, v in recipe.items() if k not in {"policy", "recipe_id"}}
    resolved.update(runtime_class="cofh.thermal.lib.util.recipes.internal.SimpleMachineRecipe",
                    resolved_input_count=1)
    payload = {k: v for k, v in events[0].payload.items() if k not in {"recipe_digest", "state"}}
    payload.update(policy=POLICY, recipe_registration_bound=False, loaded_code_authenticated=False,
                   states=[e.payload["state"] for e in events], resolved_recipe=resolved)
    return events[0].model_dump() | {"kind": "machine_completion",
        "payload_schema": KINDS["machine_completion"], "payload": payload, "evidence_refs": []}


def module15(events):
    events[0]["payload_schema"] = "strata/ServerStarted/15"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.14",
        machine_capture_policy=POLICY, machine_capture_support=support())


def append_capture(events, capture):
    terminal = next(i for i, e in enumerate(events) if e["kind"] == "server_clock")
    event = copy.deepcopy(events[terminal]) | {k: capture[k] for k in ("kind", "payload_schema", "payload")}
    event["actor_ids"] = []
    events.insert(terminal, event)
    renumber(events)
    return event


def test_raw_capture_keeps_registration_and_score_unqualified(capture, database):
    parsed = NativeFurnaceCompletion.model_validate(capture["payload"])
    assert parsed.recipe_registration_bound is parsed.loaded_code_authenticated is parsed.score_eligible is False
    assert "recipe_id" not in parsed.resolved_recipe.model_dump()
    event = GameEvent.model_validate(capture)
    assert require_capture_scope(event, True) == parsed
    scorer = Scorer(database)
    p = predicate("machine")
    register(scorer, "instance", p, event)
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        scorer.score("instance", p, event)
    assert database.connection.execute("select count(*) from predicate_state").fetchone()[0] == 0


@pytest.mark.parametrize("change", ["score", "bound", "authenticated", "numeric_false", "missing_phase",
    "extra_phase", "recipe_id", "actor", "example", "legacy", "chance", "augmented", "processing",
    "metadata", "coordinate", "bool_count"])
def test_capture_rejects_promotions_or_out_of_profile_records(capture, change):
    p = capture["payload"]
    if change == "score":
        p["score_eligible"] = True
    elif change == "bound":
        p["recipe_registration_bound"] = True
    elif change == "authenticated":
        p["loaded_code_authenticated"] = True
    elif change == "numeric_false":
        p["score_eligible"] = 0
    elif change == "missing_phase":
        p["states"].pop()
    elif change == "extra_phase":
        p["states"].append(p["states"][0])
    elif change == "recipe_id":
        p["resolved_recipe"]["recipe_id"] = "thermal:guessed"
    elif change == "actor":
        capture["actor_ids"] = ["guessed"]
    elif change == "example":
        capture["is_example"] = True
    elif change == "chance":
        p["resolved_recipe"]["output_chance"] = 2
    elif change == "augmented":
        p["states"][0]["augments"][0]["count"] = 1
    elif change == "processing":
        p["states"][0]["process"] = 1
    elif change == "metadata":
        p["states"][0]["slots"][0]["components_empty"] = False
    elif change == "coordinate":
        p["position"][0] = 2**31
    elif change == "bool_count":
        p["resolved_recipe"]["resolved_input_count"] = True
    with pytest.raises((Fault, ValidationError)):
        require_capture_scope(GameEvent.model_validate(capture), change != "legacy")


@pytest.mark.parametrize("change", ["missing", "changed", "extra", "promoted", "numeric_false"])
def test_support_requires_complete_exact_artifact_binding(change):
    value = support()
    if change == "missing":
        del value["artifacts"]["thermal"]
    elif change == "changed":
        value["artifacts"]["thermal"] = "0" * 64
    elif change == "extra":
        value["artifacts"]["other"] = "0" * 64
    elif change == "promoted":
        value["loaded_code_authenticated"] = True
    else:
        value["loaded_code_authenticated"] = 0
    with pytest.raises((Fault, ValidationError)):
        FurnaceSupport.model_validate(value)


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_signed_complete_stream_and_startup_prefix_preserve_raw_scope(fields_history, capture, tmp_path):  # noqa: F811
    events = fields_history[2]
    module15(events)
    append_capture(events, capture)
    folder, authority, path, boot = source(fields_history, tmp_path)
    assert startup_prefix(folder, authority, boot)["history"]["phase"] == "startup"
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert report["machine_capture"] == {"supported": True, "transactions": 1,
        "recipe_registration_bound": False, "loaded_code_authenticated": False, "scoring_eligible": False}
    assert report["kind_counts"]["machine_completion"] == 1
    assert report["scoring_eligible"] is False


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["legacy", "unsupported", "duplicate", "actor", "wrong_schema"])
def test_offline_reader_rejects_unbound_or_duplicate_capture(fields_history, capture, tmp_path, change):  # noqa: F811
    events = fields_history[2]
    if change != "legacy":
        module15(events)
    record = append_capture(events, capture)
    if change == "unsupported":
        events[0]["payload"]["machine_capture_support"].update(status="unsupported", artifacts=dict.fromkeys(PINS))
    elif change == "duplicate":
        append_capture(events, capture)
    elif change == "actor":
        record["actor_ids"] = ["guessed"]
    elif change == "wrong_schema":
        record["payload_schema"] = "strata/MachineInputsResolved/1"
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_new_startup_fields_cannot_relabel_old_module(fields_history):  # noqa: F811
    payload = fields_history[2][0]["payload"]
    assert ServerStartedV14.model_validate(payload)
    module15(fields_history[2])
    assert ServerStartedV15.model_validate(payload)
    with pytest.raises(ValidationError):
        ServerStartedV14.model_validate(payload)


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("refused", [False, True])
def test_online_pipe_validates_scope_and_duplicate_before_receipt(sink, fields_history, capture, refused):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    module15(fields_history[2])
    launch = first["payload"]["launch_identity"]
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    first["payload_schema"] = "strata/ServerStarted/15"
    broker._event(canonical(first) + b"\n", identity, key)
    event = first | {k: capture[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=[])
    if refused:
        event["kind"] = "machine_capture_refused"
        event["payload_schema"] = KINDS[event["kind"]]
        event["payload"] = {k: v for k, v in event["payload"].items() if k not in {"states", "resolved_recipe"}}
        event["payload"]["reason"] = "native_profile_unsupported"
    broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2
    event.update(seq=3, server_event_seq=3)
    with pytest.raises(Fault, match="MACHINE_CAPTURE_DUPLICATE"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2
    broker.output.close()


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["legacy", "unsupported", "actor", "transport"])
def test_online_refuses_unqualified_scope_without_machine_receipt(sink, fields_history, capture, change):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    launch = first["payload"]["launch_identity"]
    if change != "legacy":
        module15(fields_history[2])
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload_schema"] = fields_history[2][0]["payload_schema"]
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    if change == "unsupported":
        first["payload"]["machine_capture_support"].update(status="unsupported", artifacts=dict.fromkeys(PINS))
    if change == "transport":
        first["payload"]["telemetry_transport"] = "private-file/1"
        with pytest.raises(Fault, match="TELEMETRY_PIPE_TRANSPORT"):
            broker._event(canonical(first) + b"\n", identity, key)
        assert not receipts
        return
    broker._event(canonical(first) + b"\n", identity, key)
    event = first | {k: capture[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=["guessed"] if change == "actor" else [])
    with pytest.raises(Fault, match="MACHINE_CAPTURE_SCOPE"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 1


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_refusal_retained_in_signed_stream_with_no_machine_score(fields_history, capture, tmp_path):  # noqa: F811
    events = fields_history[2]
    module15(events)
    capture["kind"] = "machine_capture_refused"
    capture["payload_schema"] = KINDS[capture["kind"]]
    capture["payload"] = {k: v for k, v in capture["payload"].items() if k not in {"states", "resolved_recipe"}}
    capture["payload"]["reason"] = "native_validation_failed"
    append_capture(events, capture)
    _, authority, path, _ = source(fields_history, tmp_path)
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert report["kind_counts"]["machine_capture_refused"] == 1
    assert report["machine_capture"]["transactions"] == 1
    assert report["scoring_eligible"] is False
