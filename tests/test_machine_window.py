# ruff: noqa: F401, F811 -- shared synthetic fixture chain
"""Prior sealed window admission and unstable/idle/resource controls; no game run."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import GameEvent
from mcbench.storage import Database, Fault, digest
from strata_evaluator.craft_reference import CraftReferencePlanV5, CraftReferenceStore, parse_plan
from strata_evaluator.machine_capture import POLICY_V2, KINDS_V2, require_capture_scope
from strata_evaluator.machine_energy import parse_tick
from strata_evaluator.machine_interval import IntervalInspection, KINDS, parse_interval
from strata_evaluator.machine_reference import MachineReferenceInspection, MachineReferenceV2
from strata_evaluator.machine_transitions import parse_transition
from strata_evaluator.machine_window import inspect_operating_windows, qualify_operating_window
from strata_evaluator.protected_reference import ProtectedReferencePlan
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_craft_reference import seal
from test_machine_interval import (
    tick,
    interval,
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
    stage,
    ref,
    transition_child,
    module19,
    append_capture,
)
from test_machine_reference import machine_plan
from test_machine_witness import stack
from test_protected_reference import plan
from test_setup_facts import TEAM


@pytest.fixture
def episode(tick, interval):
    tick = copy.deepcopy(tick)
    tick["payload"]["resolved_recipe"]["recipe_energy_rf"] = 192
    initial = copy.deepcopy(tick["payload"]["states"][0])
    initial.update(energy_rf=1000, process=0, process_max=0, process_tick=0, active=False)
    initial["slots"][:2] = [stack("emendatusenigmatica:iron_dust", 1), stack()]
    started = initial | {"process": 192, "process_max": 192, "process_tick": 96}
    processed = started | {"process": 96, "energy_rf": 904}
    active = processed | {"active": True}
    first = copy.deepcopy(tick)
    first["payload"].update(transaction_id="process1", states=[started, processed])
    start = transition_child(tick, "start", initial, started, "start1")
    outer1 = copy.deepcopy(interval)
    outer1["payload"].update(
        transaction_id="outer1",
        states=[initial, active],
        child_ids=["start1", "process1"],
        steps=[
            ref(start),
            ref(first),
            stage("activate", processed, active),
            stage("charge", active),
        ],
    )
    depleted = active | {"process": 0, "energy_rf": 808}
    second = copy.deepcopy(tick)
    second["payload"].update(transaction_id="process2", states=[active, depleted])
    finished = copy.deepcopy(tick)
    p = finished["payload"]
    p.pop("returned")
    before = {k: v for k, v in depleted.items() if k not in {"energy_capacity", "energy_creative"}}
    middle = copy.deepcopy(before)
    middle["slots"][1] = stack("minecraft:iron_ingot", 1)
    after = copy.deepcopy(middle)
    after["slots"][0] = stack()
    p.update(policy=POLICY_V2, transaction_id="completion1", states=[before, middle, after])
    finished.update(kind="machine_completion", payload_schema=KINDS_V2["machine_completion"])
    completed = depleted | after
    refund = transition_child(tick, "refund", completed, copy.deepcopy(completed), "refund1")
    stopped = completed | {"active": False}
    outer2 = copy.deepcopy(outer1)
    outer2["payload"].update(
        transaction_id="outer2",
        ordinal=2,
        world_tick=101,
        states=[active, stopped],
        child_ids=["process2", "completion1", "refund1"],
        steps=[
            ref(second),
            ref(finished),
            stage("transfer_output", completed),
            stage("transfer_input", completed),
            ref(refund),
            stage("off", completed, stopped),
            stage("charge", stopped),
        ],
    )
    records = [start, first, outer1, second, finished, refund, outer2]
    for i, raw in enumerate(records, 1):
        raw.update(seq=i, server_event_seq=i, server_tick=18 if i <= 3 else 19)
    plan = machine_plan(finished, 0, 30)
    plan.update(
        policy="thermal1192-private-machine-reference/2",
        operating_windows={
            "furnace": {
                "selector": "first-start-through-first-refund/1",
                "minimum_ticks": 2,
                "minimum_net_energy_rf": 192,
            }
        },
    )
    return records, plan


def inspect_episode(episode):
    records, plan = episode
    intervals, machine = IntervalInspection(), MachineReferenceInspection(plan)
    for raw in records:
        event = GameEvent.model_validate(raw)
        if event.kind in KINDS:
            intervals.observe(event, parse_interval(event, True))
        else:
            captured = (
                parse_tick(event, True)
                if event.kind.startswith("machine_process_tick")
                else parse_transition(event, True)
                if event.kind.startswith("machine_process_transition")
                else require_capture_scope(event, True, POLICY_V2)
            )
            intervals.child(event, captured)
            machine.child(event, captured)
            if event.kind in KINDS_V2:
                machine.observe(event, captured)
    return machine, intervals.report()


@pytest.mark.parametrize(
    "selector", ["first-start-through-first-refund/1", "exact-inclusive-ticks/1"]
)
def test_complete_closed_episode_counts_only_joined_output_and_net_energy(episode, selector):
    window = episode[1]["operating_windows"]["furnace"]
    window["selector"] = selector
    if selector.startswith("exact"):
        window.update(start_server_tick=18, end_server_tick=19)
    machine, intervals = inspect_episode(episode)
    report = machine.report(intervals)
    assert report["targets"] == {"furnace": {"candidate_complete": True, "candidate_output": 1}}
    witness = report["operating_windows"]["targets"]["furnace"]["witness"]
    assert witness["net_energy_consumed_rf"] == witness["energy_debited_rf"] == 192
    assert witness["energy_refunded_rf"] == 0 and witness["completed_cycles"] == 1
    assert len(witness["child_event_digests"]) == 5
    assert witness["consumed"] == {"emendatusenigmatica:iron_dust": 1}
    assert witness["produced"] == {"minecraft:iron_ingot": 1}
    assert not witness["prior_registration_verified"] and not witness["scoring_eligible"]
    assert not report["sustained_operation_verified"] and not report["scoring_eligible"]


@pytest.mark.parametrize(
    "change,reason",
    [
        ("duration", "MACHINE_OPERATING_DURATION"),
        ("output", "MACHINE_OPERATING_OUTPUT"),
        ("energy", "MACHINE_OPERATING_NET_ENERGY"),
        ("wrong_recipe", "MACHINE_REGISTERED_RECIPE_MISMATCH"),
        ("wrong_origin", "MACHINE_REGISTRATION_MISMATCH"),
        ("no_start", "MACHINE_OPERATING_START_MISSING"),
        ("no_refund", "MACHINE_OPERATING_REFUND_MISSING"),
        ("missing_tick", "MACHINE_WINDOW_INCOMPLETE"),
        ("replacement", "MACHINE_WINDOW_INCOMPLETE"),
        ("retired", "MACHINE_WINDOW_RETIRED"),
        ("refused", "MACHINE_WINDOW_REJECTED_TICK"),
        ("external", "MACHINE_OPERATING_EXTERNAL_RESOURCE"),
        ("state_gap", "MACHINE_WINDOW_STATE_GAP"),
        ("partial", "MACHINE_OPERATING_PARTIAL_EPISODE"),
        ("unjoined", "MACHINE_OPERATING_CHILD_SCOPE"),
        ("gift", "MACHINE_OPERATING_RESOURCE_UNPROVEN"),
        ("forged_receipt", "MACHINE_OPERATING_RESOURCE_CHANGED"),
    ],
)
def test_window_rejects_incomplete_or_borrowed_evidence(episode, change, reason):
    machine, intervals = inspect_episode(episode)
    window = machine.plan.operating_windows["furnace"]
    target = machine.plan.targets["furnace"]
    if change == "duration":
        window.minimum_ticks = 3
    elif change == "output":
        target.minimum_output = 2
    elif change == "energy":
        window.minimum_net_energy_rf = 193
    elif change == "wrong_recipe":
        next(iter(target.recipes.values())).recipe_energy_rf += 1
    elif change == "wrong_origin":
        target.registration_origin = "converted_cooking"
    elif change == "no_start":
        machine.children.pop("start1")
    elif change == "no_refund":
        machine.children.pop("refund1")
    elif change == "missing_tick":
        intervals["accepted"].pop()
    elif change == "replacement":
        intervals["accepted"][1]["lifetime_id"] = "replacement"
    elif change == "retired":
        intervals["lifetime_ends"] = [{"lifetime_id": "lifetime", "server_tick": 18}]
    elif change == "refused":
        intervals["rejected"] = [{"lifetime_id": "lifetime", "server_tick": 19}]
    elif change == "external":
        intervals["accepted"][0]["external_resource_changes"] = True
    elif change == "state_gap":
        intervals["accepted"][1]["before"]["energy_rf"] += 1
    elif change == "partial":
        intervals["accepted"][0]["before"]["active"] = True
    elif change == "unjoined":
        machine.children.pop("process1")
    elif change == "gift":
        machine.accepted.clear()
    else:
        machine.accepted[0]["witness"]["source_event_digests"] = ["0" * 64]
    result = machine.report(intervals)
    assert result["targets"]["furnace"] == {"candidate_complete": False, "candidate_output": 0}
    assert result["operating_windows"]["targets"]["furnace"]["reason"] == reason


def test_first_episode_never_searches_for_a_later_success(episode):
    machine, intervals = inspect_episode(episode)
    event, capture = machine.children["start1"]
    earlier_event = event.model_copy(update={"server_tick": 17, "server_event_seq": 0})
    earlier = capture.model_copy(update={"transaction_id": "earlier-failed-start"})
    machine.children = {"earlier-failed-start": (earlier_event, earlier)} | machine.children
    result = machine.report(intervals)["operating_windows"]["targets"]["furnace"]
    assert (
        not result["candidate_complete"] and result["reason"] == "MACHINE_OPERATING_START_UNJOINED"
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing_target",
        "extra_target",
        "unknown_selector",
        "zero_ticks",
        "unbounded_ticks",
        "zero_energy",
        "boolean_energy",
        "reversed",
        "outside",
        "extra_field",
        "old_policy",
    ],
)
def test_prior_window_contract_refuses_invalid_scope_or_unsupported_fields(episode, change):
    p = copy.deepcopy(episode[1])
    w = p["operating_windows"]["furnace"]
    if change == "missing_target":
        p["operating_windows"].clear()
    elif change == "extra_target":
        p["operating_windows"]["other"] = copy.deepcopy(w)
    elif change == "unknown_selector":
        w["selector"] = "best-success-after-data"
    elif change == "zero_ticks":
        w["minimum_ticks"] = 0
    elif change == "unbounded_ticks":
        w["minimum_ticks"] = 16385
    elif change == "zero_energy":
        w["minimum_net_energy_rf"] = 0
    elif change == "boolean_energy":
        w["minimum_net_energy_rf"] = True
    elif change in {"reversed", "outside"}:
        w.update(
            selector="exact-inclusive-ticks/1",
            start_server_tick=20,
            end_server_tick=19 if change == "reversed" else 31,
        )
    elif change == "extra_field":
        w["forgive_replacement"] = True
    else:
        p["policy"] = "thermal1192-private-machine-reference/1"
    with pytest.raises((Fault, ValidationError)):
        MachineReferenceV2.model_validate(p)


def configure_window_fixture(fields_history, episode):
    store, setup, events, _, _ = fields_history
    records, plan = episode
    setup.update(
        schema="strata/PrivateCraftReferencePlan/5", cutoff_server_tick=30, machine_reference=plan
    )
    module19(events)
    for raw in records:
        inserted = append_capture(events, raw)
        inserted["server_tick"] = raw["server_tick"] + 3  # After the existing tick20 health sample.
    return store


@pytest.mark.parametrize("fields_history", [6], indirect=True)
def test_prior_seal_and_consumed_launch_bind_windows_and_reopen_idempotently(
    fields_history, episode
):
    store = configure_window_fixture(fields_history, episode)
    setup = fields_history[1]
    assert isinstance(parse_plan(setup), CraftReferencePlanV5)
    _, authority, _ = seal(fields_history)
    raw = inspect_authenticated_spool(
        fields_history[4],
        Path(authority.key_file).with_name("authority.json"),
        machine_reference=setup["machine_reference"],
    )
    assert not raw["machine_reference"]["operating_windows"]["prior_registration_verified"]
    result = store.inspect("i", fields_history[4])
    assert result["schema"] == "strata/PrivateCraftReferenceInspection/5"
    assert result["operating_window_registration"]["prior_registration_verified"]
    assert result["machine_reference"]["operating_windows"]["prior_registration_verified"]
    candidate = result["machine_reference"]["operating_windows"]["targets"]["furnace"]
    assert candidate["witness"]["sampled_window"]["prior_registration_verified"]
    assert result["machine_reference"]["targets"]["furnace"]["candidate_complete"]
    assert not result["scoring_eligible"] and not result["scoring_authority_qualified"]
    cursor = store.database.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0]
    reopened = Database(store.database.path)
    try:
        assert CraftReferenceStore(reopened).inspect("i", fields_history[4]) == result
        assert reopened.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0] == cursor
    finally:
        reopened.close()


@pytest.mark.parametrize("fields_history", [6], indirect=True)
@pytest.mark.parametrize("change", ["missing", "changed", "duplicate", "order"])
def test_missing_or_changed_prior_registration_never_publishes_receipt(
    fields_history, episode, change
):
    store = configure_window_fixture(fields_history, episode)
    seal(fields_history)
    with store.database.transaction() as db:
        row = db.execute(
            "SELECT cursor,body FROM outbox WHERE kind='private.craft_reference_sealed'"
        ).fetchone()
        if change == "missing":
            db.execute("DELETE FROM outbox WHERE cursor=?", (row["cursor"],))
        elif change == "order":
            db.execute("UPDATE outbox SET cursor=99 WHERE cursor=?", (row["cursor"],))
        elif change == "duplicate":
            store.database.event(db, "private.craft_reference_sealed", json.loads(row["body"]))
        else:
            body = json.loads(row["body"])
            body["setup_digest"] = "0" * 64
            db.execute("UPDATE outbox SET body=? WHERE cursor=?", (json.dumps(body), row["cursor"]))
    with pytest.raises(Fault, match="MACHINE_OPERATING_REGISTRATION"):
        store.inspect("i", fields_history[4])
    assert (
        store.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_imports"
        ).fetchone()[0]
        == 0
    )


def test_protected_launch_seals_the_new_window_plan(plan, episode):
    setup = plan["setup"]
    machine = copy.deepcopy(episode[1])
    machine.update(
        start_server_tick=setup["start_server_tick"], cutoff_server_tick=setup["cutoff_server_tick"]
    )
    setup.update(
        schema="strata/PrivateCraftReferencePlan/5",
        required_history_policy="native-e9e-setup-mutation-watch/6",
        native_team_ids=dict.fromkeys(setup["roster"], TEAM),
        machine_reference=machine,
    )
    plan["launch"]["setup_digest"] = digest(setup)
    assert isinstance(ProtectedReferencePlan.model_validate(plan).setup, CraftReferencePlanV5)
    machine["operating_windows"]["furnace"]["minimum_ticks"] += 1
    with pytest.raises((Fault, ValidationError), match="PROTECTED_REFERENCE_BINDING"):
        ProtectedReferencePlan.model_validate(plan)


@pytest.mark.parametrize(
    "change,reason",
    [
        ("underfunded", "MACHINE_OPERATING_UNFUNDED_TICK"),
        ("reload", "MACHINE_OPERATING_RECIPE_CONTINUITY"),
    ],
)
def test_valid_native_brackets_do_not_hide_underfunding_or_recipe_reload(episode, change, reason):
    records, _ = episode
    if change == "underfunded":
        seen = set()

        def drain(value):
            if isinstance(value, (dict, list)):
                if id(value) in seen:
                    return
                seen.add(id(value))
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "energy_rf":
                        value[key] = max(0, child - 900)
                    else:
                        drain(child)
            elif isinstance(value, list):
                for child in value:
                    drain(child)

        drain(records)
    else:
        for raw in records[3:]:
            if "registration" in raw["payload"]:
                raw["payload"]["registration"]["generation"] = 2
    machine, intervals = inspect_episode(episode)
    assert not intervals["rejected"]  # Native brackets themselves remain arithmetically valid.
    result = machine.report(intervals)["operating_windows"]["targets"]["furnace"]
    assert not result["candidate_complete"] and result["reason"] == reason


@pytest.mark.parametrize("converted", [False, True])
def test_registered_alternative_recipe_paths_remain_eligible(episode, converted):
    from test_machine_registration import registration

    records, plan = episode
    lineage = registration(converted)
    if not converted:
        lineage["source_recipe_id"] = lineage["machine_recipe_id"] = "thermal:valid_alternative"
    for raw in records:
        if "registration" in raw["payload"]:
            raw["payload"]["registration"] = copy.deepcopy(lineage)
    target = plan["targets"]["furnace"]
    recipe = next(iter(target["recipes"].values()))
    recipe["recipe_id"] = lineage["source_recipe_id"]
    target.update(
        registration_origin=lineage["origin"],
        recipes={recipe["recipe_id"]: recipe},
        machine_recipe_ids={recipe["recipe_id"]: lineage["machine_recipe_id"]},
    )
    machine, intervals = inspect_episode(episode)
    assert machine.report(intervals)["targets"]["furnace"]["candidate_complete"]


def test_complete_idle_trace_cannot_pad_a_registered_operating_window(episode):
    records, plan = episode
    idle = copy.deepcopy(records[2])
    initial = copy.deepcopy(idle["payload"]["states"][0])
    idle.update(server_tick=17)
    idle["payload"].update(
        transaction_id="idle",
        child_ids=[],
        states=[initial, initial],
        steps=[stage("charge", initial)],
    )
    for raw in records:
        if raw["kind"] == "machine_server_tick":
            raw["payload"]["ordinal"] += 1
            raw["payload"]["world_tick"] += 1
    records.insert(0, idle)
    for index, raw in enumerate(records, 1):
        raw.update(seq=index, server_event_seq=index)
    plan["operating_windows"]["furnace"].update(
        selector="exact-inclusive-ticks/1",
        start_server_tick=17,
        end_server_tick=19,
        minimum_ticks=3,
    )
    machine, intervals = inspect_episode(episode)
    assert len(intervals["accepted"]) == 3 and not intervals["rejected"]
    result = machine.report(intervals)["operating_windows"]["targets"]["furnace"]
    assert not result["candidate_complete"] and result["reason"] == "MACHINE_OPERATING_IDLE_TICK"


@pytest.mark.parametrize("reason", ["removed", "unloaded", "reactivated"])
def test_valid_replacement_trace_cannot_complete_the_retired_objects_window(episode, reason):
    from test_machine_interval import end

    records, _ = episode
    retired = end(records[2], reason)
    records[-1]["payload"].update(lifetime_id="replacement", ordinal=1)
    records.insert(3, retired)
    for index, raw in enumerate(records, 1):
        raw.update(seq=index, server_event_seq=index)
    machine, intervals = inspect_episode(episode)
    assert intervals["lifetimes"] == 2 and not intervals["rejected"]
    assert intervals["lifetime_ends"][0]["reason"] == reason
    result = machine.report(intervals)["operating_windows"]["targets"]["furnace"]
    assert not result["candidate_complete"] and result["reason"] == "MACHINE_WINDOW_RETIRED"
