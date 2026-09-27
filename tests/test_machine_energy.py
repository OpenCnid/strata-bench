"""Synthetic native processTick captures; no authentic producer claim."""

import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.machine_energy import POLICY, KINDS, parse_tick, qualify_tick
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_registration import (  # noqa: F401 - pytest fixture dependency chain
    registered,
    capture,
    completion,
    fields_history,  # noqa: F401
    team_history,
    globals_history,
    clocked,
    history,
    native,
    reference,
    module16,
    append_capture,
)
from test_setup_control import source
from test_telemetry import write
from test_telemetry_pipe import sink  # noqa: F401


@pytest.fixture
def tick(registered):  # noqa: F811
    p = registered["payload"]
    before = copy.deepcopy(p["states"][0])
    before.update(
        energy_rf=4000,
        energy_capacity=50000,
        energy_creative=False,
        process=4000,
        process_tick=96,
        process_max=4000,
    )
    after = copy.deepcopy(before)
    after.update(energy_rf=3904, process=3904)
    p.update(policy=POLICY, states=[before, after], returned=96)
    registered.update(kind="machine_process_tick", payload_schema=KINDS["machine_process_tick"])
    return registered


def module17(events):
    module16(events)
    events[0]["payload_schema"] = "strata/ServerStarted/17"
    events[0]["payload"].update(
        module="strata-forge1192-telemetry/0.3.16", machine_process_tick_policy=POLICY
    )


@pytest.mark.parametrize(
    "remaining,energy", [(4000, 4000), (64, 4000), (64, 40), (64, 0), (0, 4000), (-32, 4000)]
)
@pytest.mark.parametrize("active", [False, True])
def test_actual_debit_is_distinct_from_progress_and_recipe_energy(tick, remaining, energy, active):
    p = tick["payload"]
    before, after = p["states"]
    step = 96 if remaining > 0 else 0
    before.update(process=remaining, energy_rf=energy, active=active)
    after.update(process=remaining - step, energy_rf=max(0, energy - step), active=active)
    p["returned"] = step
    event = GameEvent.model_validate(tick)
    result = qualify_tick(event, parse_tick(event, True))
    assert result["energy_debited_rf"] == min(energy, step)
    assert result["progress_decrement"] == step
    assert result["fully_funded"] == (energy >= step)
    assert not result["sustained_operation_verified"] and not result["scoring_eligible"]
    assert result["source_seq"] == event.seq and result["registration"] == p["registration"]


@pytest.mark.parametrize(
    "change",
    [
        "rf",
        "progress",
        "returned",
        "capacity",
        "active",
        "step",
        "max",
        "slot",
        "augment",
        "creative",
        "numeric_creative",
        "metadata",
        "negative_rf",
        "over_capacity",
        "actor",
        "example",
        "reference",
        "wrong_schema",
        "old_policy",
        "extra_state",
    ],
)
def test_tick_rejects_unproven_or_changed_state(tick, change):
    p = tick["payload"]
    after = p["states"][1]
    if change in {"rf", "progress", "step", "max", "capacity"}:
        key = {
            "rf": "energy_rf",
            "progress": "process",
            "step": "process_tick",
            "max": "process_max",
            "capacity": "energy_capacity",
        }[change]
        after[key] += 1
    elif change == "returned":
        p["returned"] += 1
    elif change == "active":
        after["active"] = False
    elif change == "slot":
        after["slots"][0]["count"] += 1
    elif change == "augment":
        after["augments"] = [copy.deepcopy(after["slots"][0])]
    elif change == "creative":
        after["energy_creative"] = True
    elif change == "numeric_creative":
        after["energy_creative"] = 0
    elif change == "metadata":
        after["slots"][0]["components_empty"] = False
    elif change == "negative_rf":
        after["energy_rf"] = -1
    elif change == "over_capacity":
        after["energy_rf"] = after["energy_capacity"] + 1
    elif change == "actor":
        tick["actor_ids"] = ["guessed"]
    elif change == "example":
        tick["is_example"] = True
    elif change == "reference":
        tick["evidence_refs"] = ["0" * 64]
    elif change == "wrong_schema":
        tick["payload_schema"] = "strata/NativeFurnaceCompletion/2"
    elif change == "old_policy":
        p["policy"] = "thermal1192-native-furnace-phases/2"
    else:
        p["states"].append(copy.deepcopy(after))
    with pytest.raises((Fault, ValidationError)):
        event = GameEvent.model_validate(tick)
        qualify_tick(event, parse_tick(event, True))


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_signed_tick_stream_authenticates_before_returning_private_debits(
    fields_history, tick, tmp_path  # noqa: F811
):  # noqa: F811
    events = fields_history[2]
    module17(events)
    append_capture(events, tick)
    _, authority, path, _ = source(fields_history, tmp_path)
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert result["authentication"]["stream_authentication_verified"]
    energy = result["machine_process_ticks"]
    assert energy["energy_debited_rf"] == 96 and len(energy["accepted"]) == 1
    assert not energy["rejected"] and not energy["scoring_eligible"]


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize(
    "change",
    ["old_profile", "unsupported", "duplicate", "generation_rollback", "missing_policy", "partial"],
)
def test_stream_rejects_mixed_missing_duplicate_or_partial_evidence(
    fields_history, tick, tmp_path, change  # noqa: F811
):  # noqa: F811
    events = fields_history[2]
    module17(events)
    first = append_capture(events, tick)
    if change == "old_profile":
        module16(events)
        events[0]["payload"].pop("machine_process_tick_policy")
    elif change == "unsupported":
        support = events[0]["payload"]["machine_capture_support"]
        support.update(status="unsupported", registration_hooks_verified=False)
        support["artifacts"]["thermal"] = None
    elif change in {"duplicate", "generation_rollback"}:
        second = append_capture(events, copy.deepcopy(tick))
        if change == "generation_rollback":
            first["payload"]["registration"]["generation"] = 2
            second["payload"]["transaction_id"] = "second"
    elif change == "missing_policy":
        events[0]["payload"].pop("machine_process_tick_policy")
    else:
        events.pop()
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("native_refusal", [False, True])
def test_refused_or_invalid_tick_cannot_earn_energy(fields_history, tick, tmp_path, native_refusal):  # noqa: F811
    events = fields_history[2]
    module17(events)
    if native_refusal:
        tick.update(
            kind="machine_process_tick_refused",
            payload_schema=KINDS["machine_process_tick_refused"],
        )
        for key in ("states", "registration", "resolved_recipe", "returned"):
            tick["payload"].pop(key)
        tick["payload"]["reason"] = "native_profile_unsupported"
    else:
        tick["payload"]["states"][1]["energy_rf"] += 1
    append_capture(events, tick)
    path = tmp_path / "stream.jsonl"
    write(path, events)
    result = inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])[
        "machine_process_ticks"
    ]
    assert (
        not result["accepted"] and result["energy_debited_rf"] == 0 and len(result["rejected"]) == 1
    )


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_online_tick_profile_and_duplicate_rejection(sink, fields_history, tick):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    launch = first["payload"]["launch_identity"]
    module17(fields_history[2])
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload_schema"] = "strata/ServerStarted/17"
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    broker._event(canonical(first) + b"\n", identity, key)
    event = first | {k: tick[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=[])
    broker._event(canonical(event) + b"\n", identity, key)
    event.update(seq=3, server_event_seq=3)
    with pytest.raises(Fault, match="MACHINE_CAPTURE_DUPLICATE"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_tick_quota_is_fail_closed_without_partial_report(fields_history, tick, tmp_path, monkeypatch):  # noqa: F811
    from strata_evaluator import telemetry
    monkeypatch.setattr(telemetry, "MAX_PROCESS_TICKS", 1)
    events = fields_history[2]
    module17(events)
    append_capture(events, tick)
    second = copy.deepcopy(tick)
    second["payload"]["transaction_id"] = "second"
    append_capture(events, second)
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises(Fault, match="MACHINE_TICK_QUOTA"):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_debit_does_not_invent_a_completion(fields_history, tick, tmp_path):  # noqa: F811
    events = fields_history[2]
    module17(events)
    append_capture(events, tick)
    path = tmp_path / "stream.jsonl"
    write(path, events)
    result = inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])
    assert result["machine_capture"]["transactions"] == 0
    assert len(result["machine_process_ticks"]["accepted"]) == 1
    assert not result["machine_process_ticks"]["sustained_operation_verified"]
