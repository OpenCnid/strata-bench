# ruff: noqa: F401, F811
"""Synthetic interval framing/continuity; authentic capture remains a separate gate."""

import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.machine_energy import parse_tick
from strata_evaluator.machine_interval import (
    POLICY,
    KINDS,
    IntervalInspection,
    parse_interval,
    qualify_window,
)
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_machine_transitions import (  # noqa: F401 - fixture dependency chain
    tick,
    registered,
    capture,
    completion,
    fields_history,
    team_history,
    globals_history,
    clocked,
    history,
    native,
    reference,
    sink,
    module18,
    append_capture,
)
from test_setup_control import source
from test_telemetry import write


def stage(name, before, after=None):
    return {
        "kind": "stage",
        "stage": name,
        "states": [copy.deepcopy(before), copy.deepcopy(before if after is None else after)],
    }


def transition_child(tick, operation, before, after, transaction):
    from strata_evaluator.machine_transitions import (
        POLICY as TRANSITION_POLICY,
        KINDS as TRANSITION_KINDS,
    )

    raw = copy.deepcopy(tick)
    p = raw["payload"]
    p.pop("returned")
    p.update(
        policy=TRANSITION_POLICY,
        operation=operation,
        states=[before, after],
        transaction_id=transaction,
    )
    if operation == "start":
        p["base_process_tick"] = 96
    else:
        p.pop("registration")
        p.pop("resolved_recipe")
    raw.update(
        kind="machine_process_transition",
        payload_schema=TRANSITION_KINDS["machine_process_transition"],
    )
    return raw


def whole_trace(interval, children, before, after, steps):
    from strata_evaluator.machine_capture import require_capture_scope, POLICY_V2
    from strata_evaluator.machine_transitions import parse_transition

    inspector = IntervalInspection()
    for index, raw in enumerate(children, 1):
        raw.update(seq=index, server_event_seq=index)
        e = GameEvent.model_validate(raw)
        parsed = (
            parse_tick(e, True)
            if e.kind == "machine_process_tick"
            else parse_transition(e, True)
            if e.kind == "machine_process_transition"
            else require_capture_scope(e, True, POLICY_V2)
        )
        inspector.child(e, parsed)
    interval.update(seq=len(children) + 1, server_event_seq=len(children) + 1)
    interval["payload"].update(
        states=[before, after],
        steps=steps,
        child_ids=[c["payload"]["transaction_id"] for c in children],
    )
    observe(inspector, interval)
    report = inspector.report()
    assert not report["rejected"] and len(report["accepted"]) == 1
    return report


def ref(raw):
    return {"kind": "child", "transaction_id": raw["payload"]["transaction_id"]}


def test_complete_inactive_start_processing_and_activation_path(tick, interval):  # noqa: F811
    for state in tick["payload"]["states"]:
        state["active"] = False
    before = copy.deepcopy(tick["payload"]["states"][0])
    before.update(process=0, process_max=0, process_tick=0)
    start = transition_child(
        tick, "start", before, copy.deepcopy(tick["payload"]["states"][0]), "start"
    )
    processed = copy.deepcopy(tick["payload"]["states"][1])
    after = processed | {"active": True}
    whole_trace(
        interval,
        [start, tick],
        before,
        after,
        [ref(start), ref(tick), stage("activate", processed, after), stage("charge", after)],
    )


@pytest.mark.parametrize("following", ["start", "refund"])
def test_complete_active_completion_restart_or_refund_path(tick, interval, following):  # noqa: F811
    from strata_evaluator.machine_capture import POLICY_V2, KINDS_V2

    a, b = tick["payload"]["states"]
    a.update(process=64, energy_rf=1000)
    b.update(process=-32, energy_rf=904)
    completion = copy.deepcopy(tick)
    p = completion["payload"]
    p.pop("returned")
    initial = {k: v for k, v in b.items() if k not in {"energy_capacity", "energy_creative"}}
    middle = copy.deepcopy(initial)
    middle["slots"][1]["count"] += 1
    final = copy.deepcopy(middle)
    final["slots"][0]["count"] -= 1
    p.update(policy=POLICY_V2, transaction_id="completion", states=[initial, middle, final])
    completion.update(kind="machine_completion", payload_schema=KINDS_V2["machine_completion"])
    completed = b | final
    after = completed | (
        {"process": 3968, "process_max": 3968} if following == "start" else {"energy_rf": 936}
    )
    transition = transition_child(
        tick, following, copy.deepcopy(completed), copy.deepcopy(after), following
    )
    steps = [
        ref(tick),
        ref(completion),
        stage("transfer_output", completed),
        stage("transfer_input", completed),
        ref(transition),
    ]
    if following == "refund":
        stopped = after | {"process": 0, "active": False}
        steps.append(stage("off", after, stopped))
        after = stopped
    steps.append(stage("charge", after))
    whole_trace(interval, [tick, completion, transition], a, after, steps)


def module19(events):
    module18(events)
    events[0]["payload_schema"] = "strata/ServerStarted/19"
    events[0]["payload"].update(
        module="strata-forge1192-telemetry/0.3.18", machine_interval_policy=POLICY
    )


@pytest.fixture
def interval(tick):  # noqa: F811
    raw = copy.deepcopy(tick)
    p = raw["payload"]
    for key in ("registration", "resolved_recipe", "returned"):
        p.pop(key)
    p.update(
        policy=POLICY,
        transaction_id="outer",
        lifetime_id="lifetime",
        ordinal=1,
        world_tick=100,
        child_ids=[tick["payload"]["transaction_id"]],
        steps=[
            {"kind": "child", "transaction_id": tick["payload"]["transaction_id"]},
            {"kind": "stage", "stage": "charge", "states": [copy.deepcopy(p["states"][1])] * 2},
        ],
    )
    raw.update(
        kind="machine_server_tick",
        payload_schema=KINDS["machine_server_tick"],
        seq=tick["seq"] + 1,
        server_event_seq=tick["seq"] + 1,
    )
    return raw


def idle(raw, ordinal=1, server_tick=None):
    raw = copy.deepcopy(raw)
    p = raw["payload"]
    state = copy.deepcopy(p["states"][0])
    state.update(active=False, process=0, process_max=0, process_tick=0)
    p.update(
        states=[state, copy.deepcopy(state)],
        child_ids=[],
        ordinal=ordinal,
        world_tick=99 + ordinal,
        transaction_id="tick-" + str(ordinal),
        steps=[{"kind": "stage", "stage": "charge", "states": [state, copy.deepcopy(state)]}],
    )
    raw.update(
        seq=ordinal + 1,
        server_event_seq=ordinal + 1,
        server_tick=ordinal if server_tick is None else server_tick,
    )
    return raw


def observe(inspector, raw):
    event = GameEvent.model_validate(raw)
    inspector.observe(event, parse_interval(event, True))


def end(raw, reason="removed"):
    raw = copy.deepcopy(raw)
    p = raw["payload"]
    for key in ("states", "steps", "child_ids"):
        p.pop(key)
    p.update(transaction_id="end-" + reason, reason=reason)
    raw.update(
        kind="machine_lifetime_end",
        payload_schema=KINDS["machine_lifetime_end"],
        seq=raw["seq"] + 1,
        server_event_seq=raw["server_event_seq"] + 1,
    )
    return raw


def test_child_math_and_entire_tick_trace_are_joined(tick, interval):  # noqa: F811
    inspector = IntervalInspection()
    e = GameEvent.model_validate(tick)
    inspector.child(e, parse_tick(e, True))
    observe(inspector, interval)
    report = inspector.report()
    assert len(report["accepted"]) == 1 and not report["rejected"]
    result = qualify_window(report, "lifetime", e.server_tick, e.server_tick)
    assert result["sampled_lifetime_continuity_verified"] and not result["scoring_eligible"]
    assert not result["prior_registration_verified"] and result["observed_ticks"] == 1


def test_requested_contiguous_window_does_not_expand_or_trim_bounds(interval):
    inspector = IntervalInspection()
    for ordinal in range(1, 4):
        observe(inspector, idle(interval, ordinal))
    result = qualify_window(inspector.report(), "lifetime", 1, 3)
    assert result["observed_ticks"] == 3 and len(result["source_event_digests"]) == 3
    assert not result["external_resource_changes"] and not result["scoring_eligible"]
    for first, last in [(0, 3), (1, 4), (2, 1), (True, 3), (1, 16385)]:
        with pytest.raises(Fault):
            qualify_window(inspector.report(), "lifetime", first, last)


def test_native_refusal_is_retained_and_cannot_qualify_a_window(interval):
    inspector = IntervalInspection()
    raw = idle(interval)
    raw.update(
        kind="machine_server_tick_refused", payload_schema=KINDS["machine_server_tick_refused"]
    )
    raw["payload"].pop("states")
    raw["payload"].pop("steps")
    raw["payload"]["reason"] = "native_profile_unsupported"
    observe(inspector, raw)
    report = inspector.report()
    assert (
        not report["accepted"]
        and report["rejected"][0]["reason"] == "MACHINE_INTERVAL_NATIVE_REFUSED"
    )
    with pytest.raises(Fault, match="MACHINE_WINDOW_REJECTED_TICK"):
        qualify_window(report, "lifetime", 1, 1)


@pytest.mark.parametrize("reason", ["removed", "unloaded", "reactivated"])
def test_retirement_prevents_revival_and_splicing_objects(interval, reason):
    inspector = IntervalInspection()
    raw = idle(interval)
    observe(inspector, raw)
    observe(inspector, end(raw, reason))
    with pytest.raises(Fault, match="MACHINE_WINDOW_RETIRED"):
        qualify_window(inspector.report(), "lifetime", 1, 1)
    with pytest.raises(Fault, match="MACHINE_LIFETIME_SEQUENCE"):
        observe(inspector, idle(interval, 2))
    fresh = idle(interval, 1, 2)
    fresh["payload"]["lifetime_id"] = "replacement"
    observe(inspector, fresh)
    with pytest.raises(Fault, match="MACHINE_WINDOW_INCOMPLETE"):
        qualify_window(inspector.report(), "replacement", 1, 2)


@pytest.mark.parametrize(
    "change", ["ordinal", "world", "server", "location", "replacement", "foreign_boot"]
)
def test_lifetime_sequence_identity_and_replacement_guards(interval, change):
    inspector = IntervalInspection()
    observe(inspector, idle(interval))
    raw = idle(interval, 2)
    if change == "ordinal":
        raw["payload"]["ordinal"] = 3
    elif change == "world":
        raw["payload"]["world_tick"] = 100
    elif change == "server":
        raw["server_tick"] = 1
    elif change == "location":
        raw["payload"]["position"][0] += 1
    elif change == "replacement":
        raw["payload"].update(lifetime_id="replacement", ordinal=1)
    else:
        raw["server_boot_id"] = "foreign"
    with pytest.raises(Fault):
        observe(inspector, raw)


@pytest.mark.parametrize(
    "change", ["before", "after", "stage", "order", "missing_process", "child_math"]
)
def test_unobserved_changes_missing_steps_and_bad_child_math_reject_tick(tick, interval, change):  # noqa: F811
    inspector = IntervalInspection()
    if change == "before":
        interval["payload"]["states"][0]["energy_rf"] += 1
    elif change == "after":
        interval["payload"]["states"][1]["process"] += 1
    elif change == "stage":
        interval["payload"]["steps"][1]["states"][0]["energy_rf"] += 1
    elif change == "order":
        interval["payload"]["steps"].insert(
            1,
            {
                "kind": "stage",
                "stage": "activate",
                "states": copy.deepcopy(interval["payload"]["states"]),
            },
        )
    elif change == "missing_process":
        interval["payload"]["child_ids"] = []
        interval["payload"]["steps"].pop(0)
    else:
        tick["payload"]["returned"] += 1
    if change != "missing_process":
        e = GameEvent.model_validate(tick)
        inspector.child(e, parse_tick(e, True))
    observe(inspector, interval)
    report = inspector.report()
    assert not report["accepted"] and len(report["rejected"]) == 1


@pytest.mark.parametrize("change", ["missing_child", "foreign_child", "wrong_tick", "late_child"])
def test_child_scope_and_missing_native_outer_are_structural_failures(tick, interval, change):  # noqa: F811
    inspector = IntervalInspection()
    if change != "missing_child":
        if change == "foreign_child":
            tick["payload"]["position"][0] += 1
        if change == "wrong_tick":
            tick["server_tick"] += 1
        if change == "late_child":
            tick.update(seq=interval["seq"] + 1, server_event_seq=interval["seq"] + 1)
        e = GameEvent.model_validate(tick)
        inspector.child(e, parse_tick(e, True))
    with pytest.raises(Fault):
        observe(inspector, interval)


def test_exact_requested_window_never_fills_gaps_or_intertick_changes(interval):
    inspector = IntervalInspection()
    observe(inspector, idle(interval))
    raw = idle(interval, 2, 3)
    raw["payload"]["world_tick"] = 102
    observe(inspector, raw)
    assert inspector.report()["rejected"][0]["reason"] == "MACHINE_INTERVAL_TICK_GAP"
    with pytest.raises(Fault):
        qualify_window(inspector.report(), "lifetime", 1, 3)
    inspector = IntervalInspection()
    observe(inspector, idle(interval))
    raw = idle(interval, 2)
    for state in raw["payload"]["states"] + raw["payload"]["steps"][0]["states"]:
        state["energy_rf"] = 2000
    observe(inspector, raw)
    assert len(inspector.report()["accepted"]) == 2
    with pytest.raises(Fault, match="MACHINE_WINDOW_STATE_GAP"):
        qualify_window(inspector.report(), "lifetime", 1, 2)


@pytest.mark.parametrize(
    "change",
    ["policy", "schema", "actor", "example", "duplicate_child", "no_charge", "too_many_states"],
)
def test_strict_interval_profile(interval, change):
    p = interval["payload"]
    if change == "policy":
        p["policy"] = "old"
    elif change == "schema":
        interval["payload_schema"] = "strata/NativeFurnaceProcessTick/1"
    elif change == "actor":
        interval["actor_ids"] = ["guessed"]
    elif change == "example":
        interval["is_example"] = True
    elif change == "duplicate_child":
        p["child_ids"] *= 2
    elif change == "no_charge":
        p["steps"].pop()
    else:
        p["states"].append(copy.deepcopy(p["states"][0]))
    with pytest.raises((Fault, ValidationError)):
        parse_interval(GameEvent.model_validate(interval), True)


def test_quotas_and_orphan_child_are_not_partial_success(interval, tick, monkeypatch):  # noqa: F811
    from strata_evaluator import machine_interval

    inspector = IntervalInspection()
    e = GameEvent.model_validate(tick)
    inspector.child(e, parse_tick(e, True))
    with pytest.raises(Fault, match="MACHINE_INTERVAL_ORPHAN_CHILD"):
        inspector.report()
    inspector = IntervalInspection()
    monkeypatch.setattr(machine_interval, "MAX_TICKS", 1)
    observe(inspector, idle(interval))
    with pytest.raises(Fault, match="MACHINE_INTERVAL_QUOTA"):
        observe(inspector, idle(interval, 2))


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_authenticated_stream_joins_children_before_returning_interval_report(
    fields_history, tick, interval, tmp_path
):  # noqa: F811
    events = fields_history[2]
    module19(events)
    append_capture(events, tick)
    append_capture(events, interval)
    _, authority, path, _ = source(fields_history, tmp_path)
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert result["authentication"]["stream_authentication_verified"]
    assert (
        len(result["machine_intervals"]["accepted"]) == 1
        and not result["machine_intervals"]["rejected"]
    )
    assert not result["machine_intervals"]["scoring_eligible"]


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize(
    "change", ["old_profile", "missing_policy", "orphan", "partial", "unsupported"]
)
def test_stream_profile_and_completeness_fail_closed(
    fields_history, tick, interval, tmp_path, change
):  # noqa: F811
    events = fields_history[2]
    module19(events)
    append_capture(events, tick)
    if change != "orphan":
        append_capture(events, interval)
    if change == "old_profile":
        module18(events)
        events[0]["payload"].pop("machine_interval_policy")
    elif change == "missing_policy":
        events[0]["payload"].pop("machine_interval_policy")
    elif change == "partial":
        events.pop()
    elif change == "unsupported":
        support = events[0]["payload"]["machine_capture_support"]
        support.update(status="unsupported", registration_hooks_verified=False)
        support["artifacts"]["thermal"] = None
    path = tmp_path / "stream.jsonl"
    write(path, events)
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, events[0]["campaign_id"], events[0]["epoch"])


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_online_interval_scope_and_duplicate_fence(sink, fields_history, interval):  # noqa: F811
    broker, first, identity, key, receipts, _ = sink
    launch = first["payload"]["launch_identity"]
    module19(fields_history[2])
    first["payload"] = copy.deepcopy(fields_history[2][0]["payload"])
    first["payload_schema"] = "strata/ServerStarted/19"
    first["payload"].update(launch_identity=launch, telemetry_transport="windows-owned-pipe/1")
    broker._event(canonical(first) + b"\n", identity, key)
    raw = idle(interval)
    event = first | {k: raw[k] for k in ("kind", "payload_schema", "payload")}
    event.update(seq=2, server_event_seq=2, server_tick=2, actor_ids=[])
    broker._event(canonical(event) + b"\n", identity, key)
    event.update(seq=3, server_event_seq=3)
    with pytest.raises(Fault, match="MACHINE_CAPTURE_DUPLICATE"):
        broker._event(canonical(event) + b"\n", identity, key)
    assert len(receipts) == 2
