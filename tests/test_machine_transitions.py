"""Synthetic transition witnesses, including signed-stream and live-pipe guards."""

import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.machine_transitions import POLICY, KINDS, parse_transition, qualify_transition
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_energy import (  # noqa: F401 - pytest fixture dependency chain
    tick, registered, capture, completion, fields_history, team_history, globals_history,
    clocked, history, native, reference, sink, module17, append_capture,
)
from test_setup_control import source
from test_telemetry import write


def module18(events):
    module17(events)
    events[0]["payload_schema"] = "strata/ServerStarted/18"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.17",
                                machine_transition_policy=POLICY)


@pytest.fixture
def transition(tick):  # noqa: F811
    p = tick["payload"]
    p.pop("returned")
    p.update(policy=POLICY, operation="start", base_process_tick=96)
    before, after = p["states"]
    before.update(process=0, process_max=0, process_tick=0, active=False)
    after.update(energy_rf=before["energy_rf"], active=False,
                 process=p["resolved_recipe"]["recipe_energy_rf"],
                 process_max=p["resolved_recipe"]["recipe_energy_rf"])
    tick.update(kind="machine_process_transition", payload_schema=KINDS["machine_process_transition"])
    return tick


def refund(transition, progress=-32, energy=4000, capacity=50000):
    p = transition["payload"]
    p.update(operation="refund")
    for key in ("registration", "resolved_recipe", "base_process_tick"):
        p.pop(key)
    before = p["states"][0]
    before.update(process=progress, energy_rf=energy, energy_capacity=capacity,
                  process_max=4000, process_tick=96, active=True)
    after = copy.deepcopy(before)
    after["energy_rf"] = min(capacity, energy - progress)
    p["states"][1] = after
    return transition


def witness(raw):
    event = GameEvent.model_validate(raw)
    return qualify_transition(event, parse_transition(event, True))


@pytest.mark.parametrize("carry", [0, -32, -64])
@pytest.mark.parametrize("active", [False, True])
def test_start_carries_progress_without_debit_or_invented_completion(transition, carry, active):
    p = transition["payload"]
    amount = p["resolved_recipe"]["recipe_energy_rf"] + carry
    p["states"][0].update(process=carry, active=active)
    p["states"][1].update(process=amount, process_max=amount, active=active)
    result = witness(transition)
    assert result["progress_carried"] == carry and result["progress_started"] == amount
    assert result["registration"] == p["registration"]
    assert not any(result[k] for k in ("producer_authenticated", "sustained_operation_verified",
                                      "setup_team_qualified", "scoring_eligible"))


@pytest.mark.parametrize("progress,energy,capacity", [(0, 4000, 50000), (-32, 4000, 50000),
                                                    (-64, 49980, 50000), (-32, 50000, 50000)])
def test_refund_preserves_requested_and_actual_clamped_amount(transition, progress, energy, capacity):
    result = witness(refund(transition, progress, energy, capacity))
    assert result["requested_refund_rf"] == -progress
    assert result["energy_refunded_rf"] == min(-progress, capacity - energy)
    assert "registration" not in result and not result["scoring_eligible"]


@pytest.mark.parametrize("operation", ["start", "refund"])
@pytest.mark.parametrize("change", ["energy", "process", "max", "step", "active", "slot", "capacity",
                                    "creative", "numeric_bool", "actor", "example", "policy", "schema",
                                    "extra_state", "foreign_fields"])
def test_changes_and_profile_substitution_fail(transition, operation, change):
    if operation == "refund":
        refund(transition)
    p = transition["payload"]
    after = p["states"][1]
    if change in {"energy", "process", "max", "step", "capacity"}:
        key = {"energy": "energy_rf", "process": "process", "max": "process_max",
               "step": "process_tick", "capacity": "energy_capacity"}[change]
        after[key] += 1
    elif change == "active":
        after["active"] = not after["active"]
    elif change == "slot":
        after["slots"][0]["count"] += 1
    elif change in {"creative", "numeric_bool"}:
        after["energy_creative"] = True if change == "creative" else 0
    elif change == "actor":
        transition["actor_ids"] = ["guessed"]
    elif change == "example":
        transition["is_example"] = True
    elif change == "policy":
        p["policy"] = "thermal1192-native-furnace-process-tick/1"
    elif change == "schema":
        transition["payload_schema"] = "strata/NativeFurnaceProcessTick/1"
    elif change == "extra_state":
        p["states"].append(copy.deepcopy(after))
    else:
        p["returned"] = 96
    with pytest.raises((Fault, ValidationError)):
        witness(transition)


@pytest.mark.parametrize("case", ["positive_carry", "excess_carry", "negation_overflow", "sum_overflow"])
def test_invalid_progress_and_overflow_cannot_earn_work(transition, case):
    if case in {"positive_carry", "excess_carry"}:
        p = transition["payload"]
        p["states"][0]["process"] = 1 if case == "positive_carry" else -p["resolved_recipe"]["recipe_energy_rf"]
        amount = p["resolved_recipe"]["recipe_energy_rf"] + p["states"][0]["process"]
        p["states"][1].update(process=amount, process_max=amount)
    else:
        refund(transition, -2**31 if case == "negation_overflow" else -32,
               2**31-2, 2**31-1)
    with pytest.raises(Fault):
        witness(transition)


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_complete_authenticated_stream_keeps_start_refund_and_debit_distinct(fields_history, transition, tmp_path):  # noqa: F811
    events = fields_history[2]
    module18(events)
    append_capture(events, transition)
    returned = refund(copy.deepcopy(transition))
    returned["payload"]["transaction_id"] = "refund"
    append_capture(events, returned)
    _, authority, path, _ = source(fields_history, tmp_path)
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    report = result["machine_process_transitions"]
    assert result["authentication"]["stream_authentication_verified"]
    assert len(report["accepted"]) == 2 and not report["rejected"]
    assert report["energy_refunded_rf"] == 32 and not report["scoring_eligible"]
    assert result["machine_capture"]["transactions"] == 0
    assert result["machine_process_ticks"]["energy_debited_rf"] == 0


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["old_profile", "unsupported", "duplicate", "generation_rollback",
                                    "missing_policy", "partial", "quota"])
def test_incomplete_or_wrong_stream_fails(fields_history, transition, tmp_path, monkeypatch, change):  # noqa: F811
    events = fields_history[2]
    module18(events)
    first = append_capture(events, transition)
    if change == "old_profile":
        module17(events)
        events[0]["payload"].pop("machine_transition_policy")
    elif change == "unsupported":
        support = events[0]["payload"]["machine_capture_support"]
        support.update(status="unsupported", registration_hooks_verified=False)
        support["artifacts"]["thermal"] = None
    elif change in {"duplicate", "generation_rollback", "quota"}:
        second = append_capture(events, copy.deepcopy(transition))
        if change != "duplicate":
            second["payload"]["transaction_id"] = "second"
        if change == "generation_rollback":
            first["payload"]["registration"]["generation"] = 2
        if change == "quota":
            from strata_evaluator import telemetry
            monkeypatch.setattr(telemetry, "MAX_PROCESS_TRANSITIONS", 1)
    elif change == "missing_policy":
        events[0]["payload"].pop("machine_transition_policy")
    else:
        events.pop()
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("native_refusal", [False, True])
def test_refused_and_invalid_transition_retains_reason_without_refund(fields_history, transition, tmp_path, native_refusal):  # noqa: F811
    events = fields_history[2]
    module18(events)
    refund(transition)
    if native_refusal:
        transition.update(kind="machine_process_transition_refused",
                          payload_schema=KINDS["machine_process_transition_refused"])
        transition["payload"].pop("states")
        transition["payload"]["reason"] = "native_profile_unsupported"
    else:
        transition["payload"]["states"][1]["energy_rf"] += 1
    append_capture(events, transition)
    path = tmp_path / "stream.jsonl"
    write(path, events)
    report = inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])["machine_process_transitions"]
    assert not report["accepted"] and report["energy_refunded_rf"] == 0
    assert len(report["rejected"]) == 1 and report["rejected"][0]["source_seq"] > 1


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("operation", ["start", "refund"])
def test_online_transition_is_bound_and_duplicate_fails(sink, fields_history, transition, operation):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    launch = first["payload"]["launch_identity"]
    module18(fields_history[2])
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload_schema"] = "strata/ServerStarted/18"
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    broker._event(canonical(first) + b"\n", identity, key)
    if operation == "refund":
        refund(transition)
    event = first | {k: transition[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=[])
    broker._event(canonical(event) + b"\n", identity, key)
    event.update(seq=3, server_event_seq=3)
    with pytest.raises(Fault, match="MACHINE_CAPTURE_DUPLICATE"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2
