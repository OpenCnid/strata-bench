"""Signed synthetic history joins; no authentic game or full-route qualification."""

import copy

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.craft_reference import CraftReferencePlanV3, parse_plan
from strata_evaluator.setup_history import POLICY, ROUTES
from test_craft_reference import reference, seal  # noqa: F401
from test_setup_facts import native, renumber  # noqa: F401


@pytest.fixture
def history(native):  # noqa: F811
    _, _, events, _, _ = native
    events[0]["payload_schema"] = "strata/ServerStarted/8"
    events[0]["payload"].update(
        module="strata-forge1192-telemetry/0.3.7", telemetry_transport="private-file/1",
        setup_history_support={"policy": POLICY, "vanilla_hooks_verified": True,
                               "team_hooks_verified": True, "all_mutation_routes_covered": False})
    values = []
    for event in events:
        if event["kind"] in {"setup_snapshot", "server_stopped"}:
            point = event["payload"]
            payload = {"policy": POLICY, "phase": point.get("phase", "stop"),
                       "transaction_id": point.get("transaction_id"),
                       "attempts": dict.fromkeys(sorted(ROUTES), 0),
                       "off_thread_attempts": 0, "overflowed": False}
            values.append(copy.deepcopy(event) | {"kind": "setup_history",
                          "payload_schema": "strata/NativeSetupHistory/1", "payload": payload})
        values.append(event)
    events[:] = values
    renumber(events)
    return native


def histories(events):
    return [event for event in events if event["kind"] == "setup_history"]


def require_history(plan):
    plan.update(schema="strata/PrivateCraftReferencePlan/3", required_history_policy=POLICY)
    return parse_plan(plan)


def test_required_history_cannot_import_a_valid_legacy_point_only_stream(native):  # noqa: F811
    store, plan, _, _, spool = native
    require_history(plan)
    seal(native)
    with pytest.raises(Fault, match="CRAFT_NATIVE_HISTORY_MISSING"):
        store.inspect("i", spool)
    assert store.database.connection.execute("SELECT COUNT(*) FROM craft_reference_imports").fetchone()[0] == 0


def test_required_history_is_sealed_and_imported_without_promoting_qualification(history):
    store, plan, _, _, spool = history
    parsed = require_history(plan)
    assert isinstance(parsed, CraftReferencePlanV3)
    seal(history)
    result = store.inspect("i", spool)
    assert result["schema"] == "strata/PrivateCraftReferenceInspection/3"
    assert result["required_history_policy"] == POLICY
    assert result["candidate_complete"] and result["native_mutation_history"]["observed_history_clear"]
    assert not result["scoring_eligible"] and not result["native_setup_continuity_qualified"]
    assert store.inspect("i", spool) == result


@pytest.mark.parametrize("change", ["missing", "unknown"])
def test_history_required_plan_cannot_drop_or_replace_its_policy(native, change):  # noqa: F811
    plan = native[1]
    require_history(plan)
    if change == "missing":
        del plan["required_history_policy"]
    else:
        plan["required_history_policy"] = "point-observations-only"
    with pytest.raises(ValidationError):
        parse_plan(plan)


def test_complete_clear_history_adds_no_score_and_retains_resource_witness(history):
    store, _, _, _, spool = history
    seal(history)
    result = store.inspect("i", spool)
    assert result["candidate_complete"] and result["candidate_output"] == 1
    observed = result["native_mutation_history"]
    assert observed["observed_history_clear"] and observed["reasons"] == []
    assert not observed["continuous_history_proven"] and not result["scoring_eligible"]
    assert not result["native_setup_continuity_qualified"]
    assert store.inspect("i", spool) == result


@pytest.mark.parametrize("route", sorted(ROUTES - {"native_stop_command"}))
def test_matching_native_points_cannot_erase_reverted_change(history, route):
    store, _, events, _, spool = history
    # Point facts remain unchanged; both forward and reverse entry attempts persist.
    for event in histories(events)[1:]:
        event["payload"]["attempts"][route] = 2
    seal(history)
    result = store.inspect("i", spool)
    assert result["native_point_checks"]["transaction"]["native_points_match"]
    assert result["candidate_output"] == 0 and not result["candidate_complete"]
    assert result["rejected_resource_witnesses"] == [{"transaction_id": "transaction",
                                                    "reason": "CRAFT_NATIVE_HISTORY_TAINTED"}]
    assert f"observed:{route}" in result["native_mutation_history"]["reasons"]


def test_attempt_after_craft_conservatively_taints_whole_reference(history):
    store, _, events, _, spool = history
    histories(events)[-1]["payload"]["attempts"]["operator_add"] = 1
    seal(history)
    assert store.inspect("i", spool)["candidate_output"] == 0


@pytest.mark.parametrize("commands,stops,clear", [(1, 1, True), (2, 1, False), (1, 0, False), (0, 1, False), (2, 2, False)])
def test_terminal_native_stop_does_not_hide_additional_commands(history, commands, stops, clear):
    store, _, events, _, spool = history
    terminal = histories(events)[-1]["payload"]["attempts"]
    terminal.update(command_attempt=commands, native_stop_command=stops)
    seal(history)
    result = store.inspect("i", spool)
    assert result["native_mutation_history"]["observed_history_clear"] is clear
    assert result["candidate_complete"] is clear


def test_native_stop_before_later_setup_cannot_be_treated_as_normal_terminal_management(history):
    store, _, events, _, spool = history
    for event in histories(events)[1:]:
        event["payload"]["attempts"].update(command_attempt=1, native_stop_command=1)
    seal(history)
    with pytest.raises(Fault, match="SETUP_HISTORY_EARLY_STOP"):
        store.inspect("i", spool)


@pytest.mark.parametrize("change", ["off_thread", "overflow", "vanilla_hooks", "team_hooks"])
def test_uncertain_or_missing_hook_coverage_rejects_candidate(history, change):
    store, _, events, _, spool = history
    terminal = histories(events)[-1]["payload"]
    if change == "off_thread":
        terminal["attempts"]["world_mode"] = terminal["off_thread_attempts"] = 1
    elif change == "overflow":
        terminal["overflowed"] = True
    else:
        events[0]["payload"]["setup_history_support"][change + "_verified"] = False
    seal(history)
    assert store.inspect("i", spool)["candidate_output"] == 0


@pytest.mark.parametrize("change", ["missing_start", "missing_before", "missing_end", "missing_stop",
    "duplicate", "foreign_transaction", "foreign_actor", "wrong_tick", "rollback", "off_thread_rollback",
    "overflow_rollback", "unknown_route", "missing_route", "legacy_module", "full_coverage_assertion",
    "nonadjacent", "early_stop"])
def test_history_cannot_be_omitted_reordered_or_relabelled(history, change):
    store, _, events, _, spool = history
    points = histories(events)
    if change.startswith("missing_") and change != "missing_route":
        events.remove(points[{"missing_start": 0, "missing_before": 1, "missing_end": 2, "missing_stop": 3}[change]])
    elif change == "duplicate":
        events.insert(events.index(points[1]), copy.deepcopy(points[1]))
    elif change == "foreign_transaction":
        points[1]["payload"]["transaction_id"] = "other"
    elif change == "foreign_actor":
        points[1]["actor_ids"] = ["other"]
    elif change == "wrong_tick":
        points[1]["server_tick"] -= 1
    elif change in {"rollback", "off_thread_rollback", "overflow_rollback"}:
        points[1]["payload"]["attempts"]["team_create"] = 1
        if change == "off_thread_rollback":
            points[1]["payload"]["off_thread_attempts"] = 1
            for point in points[2:]:
                point["payload"]["attempts"]["team_create"] = 1
        elif change == "overflow_rollback":
            points[1]["payload"]["overflowed"] = True
            for point in points[2:]:
                point["payload"]["attempts"]["team_create"] = 1
    elif change == "unknown_route":
        points[1]["payload"]["attempts"]["invented"] = 0
    elif change == "missing_route":
        del points[1]["payload"]["attempts"]["team_create"]
    elif change == "legacy_module":
        events[0]["payload_schema"] = "strata/ServerStarted/7"
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.6"
        del events[0]["payload"]["setup_history_support"]
    elif change == "full_coverage_assertion":
        events[0]["payload"]["setup_history_support"]["all_mutation_routes_covered"] = True
    elif change == "nonadjacent":
        events.insert(events.index(points[1]) + 1, copy.deepcopy(events[1]) | {"server_tick": 20})
    elif change == "early_stop":
        points[2]["payload"].update(phase="stop", transaction_id=None)
        points[2]["actor_ids"] = []
    renumber(events)
    seal(history)
    with pytest.raises((Fault, ValidationError)):
        store.inspect("i", spool)


def test_actual_java_signer_carries_history_contract(history, tmp_path):
    from test_setup_facts import test_actual_java_signer_carries_native_point_contract_without_a_game
    test_actual_java_signer_carries_native_point_contract_without_a_game(history, tmp_path)
