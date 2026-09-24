"""Synthetic callback clocks with actual signing/owned-JVM integration when selected."""

import copy
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from strata_evaluator.telemetry_clocks import POLICY
from test_craft_reference import ACTOR, reference  # noqa: F401
from test_reference_launch import launch  # noqa: F401
from test_setup_facts import native, renumber  # noqa: F401
from test_setup_history import history  # noqa: F401
from test_setup_control import source
from test_telemetry import write


@pytest.fixture
def clocked(history):  # noqa: F811
    events = history[2]
    events[0]["payload_schema"] = "strata/ServerStarted/9"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.8", clock_policy=POLICY)
    health = [e["payload"] for e in events if e["kind"] == "server_health"]
    value = {"policy": POLICY, "origin": "server_started_callback", "boundary": "server_stopped_callback",
             "elapsed_wall_ns": sum(h["interval_wall_ns"] for h in health) + 500_000,
             "completed_server_ticks": events[-1]["server_tick"],
             "observed_tick_work_ns": sum(h["observed_tick_work_ns"] for h in health) + 2000,
             "avatar_tick_events": {ACTOR: 2}}
    events.insert(-2, copy.deepcopy(events[-1]) | {"kind": "server_clock",
                  "payload_schema": "strata/ServerClock/1", "payload": value})
    renumber(events)
    return history


def test_signed_terminal_reconciles_tail_without_promoting_active_time_or_scoring(clocked, tmp_path):
    folder, authority, path, boot = source(clocked, tmp_path)
    before = path.read_bytes()
    assert startup_prefix(folder, authority, boot)["history"]["phase"] == "startup"
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    clock = result["terminal_clock"]
    assert clock["completed_server_ticks"] == result["last_server_tick"]
    assert clock["wall_outside_health_samples_ns"] == 500_000
    assert clock["avatar_tick_events"] == {ACTOR: 2}
    assert not clock["active_time_qualified"] and not clock["avatar_roster_mapping_qualified"]
    assert not clock["pre_startup_time_included"] and not result["scoring_eligible"]
    assert path.read_bytes() == before


@pytest.mark.parametrize("change", ["missing", "duplicate", "legacy", "after_history", "before_health",
    "foreign_actor", "tick_mismatch", "wall_underflow", "work_underflow", "work_overflow", "uuid",
    "avatar_overflow", "avatar_zero", "avatar_limit", "float", "bool", "unknown_policy", "wrong_origin",
    "stop_tick", "health_after", "extra"])
def test_missing_relabelled_or_contradictory_terminal_clocks_cannot_pass(clocked, tmp_path, change):
    events = clocked[2]
    terminal = next(e for e in events if e["kind"] == "server_clock")
    value = terminal["payload"]
    if change == "missing":
        events.remove(terminal)
    elif change == "duplicate":
        events.insert(-2, copy.deepcopy(terminal))
    elif change == "legacy":
        events[0]["payload_schema"] = "strata/ServerStarted/8"
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.7"
        del events[0]["payload"]["clock_policy"]
    elif change == "after_history":
        events.remove(terminal)
        events.insert(-1, terminal)
    elif change == "before_health":
        events.remove(terminal)
        events.insert(4, terminal)
    elif change == "foreign_actor":
        terminal["actor_ids"] = [ACTOR]
    elif change == "tick_mismatch":
        value["completed_server_ticks"] += 1
    elif change == "wall_underflow":
        value["elapsed_wall_ns"] = 0
        value["observed_tick_work_ns"] = 0
    elif change == "work_underflow":
        value["observed_tick_work_ns"] = 0
    elif change == "work_overflow":
        value["observed_tick_work_ns"] = value["elapsed_wall_ns"] + 1
    elif change == "uuid":
        value["avatar_tick_events"] = {"foreign": 1}
    elif change == "avatar_overflow":
        value["avatar_tick_events"][ACTOR] = value["completed_server_ticks"] + 1
    elif change == "avatar_zero":
        value["avatar_tick_events"][ACTOR] = 0
    elif change == "avatar_limit":
        value["avatar_tick_events"] = {f"00000000-0000-0000-0000-{i:012x}": 1 for i in range(65)}
    elif change == "float":
        value["completed_server_ticks"] += 0.5
    elif change == "bool":
        value["elapsed_wall_ns"] = True
    elif change == "unknown_policy":
        events[0]["payload"]["clock_policy"] = "inferred20hz"
    elif change == "wrong_origin":
        value["origin"] = "process_started"
    elif change == "stop_tick":
        events[-2]["server_tick"] += 1
        events[-1]["server_tick"] += 1
    elif change == "health_after":
        health = copy.deepcopy(next(e for e in events if e["kind"] == "server_health"))
        health["server_tick"] = terminal["server_tick"]
        events.insert(-2, health)
    else:
        value["active_time_qualified"] = True
    renumber(events)
    _, authority, path, _ = source(clocked, tmp_path)
    with pytest.raises((Fault, ValidationError)):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_legacy_stream_does_not_invent_terminal_exposure(history, tmp_path):  # noqa: F811
    _, authority, path, _ = source(history, tmp_path)
    result = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert "terminal_clock" not in result


def test_integral_float_in_raw_wire_is_rejected_before_any_number_canonicalization(clocked, tmp_path):
    events = clocked[2]
    terminal = next(e for e in events if e["kind"] == "server_clock")["payload"]
    terminal["completed_server_ticks"] = float(terminal["completed_server_ticks"])
    path = tmp_path / "raw.jsonl"
    write(path, events)
    with pytest.raises(ValidationError):
        inspect_spool(path, "synthetic", 1)


def test_existing_cost_join_carries_terminal_record_without_refunding_or_inferring_active_time(clocked, tmp_path, example):
    from test_run_costs import build
    from strata_evaluator.run_costs import InputFile, inspect_costs
    plan = build(tmp_path, example)
    path = Path(plan.server_spool.path)
    write(path, clocked[2])
    plan.server_spool = InputFile(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    result = inspect_costs(plan)
    expected = inspect_spool(path, plan.campaign_id, plan.epoch)["terminal_clock"]
    assert result["terminal_clock"] == expected and result["primitive_events"] == 3
    assert result["unknown_requests"] and not result["complete_project_accounting"]


def test_actual_owned_jvm_signs_production_clock_and_launcher_retains_terminal_evidence(launch):  # noqa: F811
    launcher, plan, _ = launch
    plan["fixture_arguments"][2] = "io.github.opencnid.strata.telemetry.SetupControlFixture"
    plan["fixture_arguments"][-1] = "clock"
    result = launcher.run(plan)
    assert result["status"] == "stopped_reference", result
    clock = result["terminal_clock"]
    assert clock["completed_server_ticks"] == 22 and clock["ticks_after_last_health_sample"] == 2
    assert clock["elapsed_wall_ns"] == 1_200_000_000 and clock["wall_outside_health_samples_ns"] == 200_000_000
    assert clock["avatar_tick_events"] == {ACTOR: 2} and not clock["active_time_qualified"]
    assert result["held_members"]["signaled_processes"] == result["job_accounting"]["total_processes"]
    assert result["job_accounting"]["active_processes"] == 0 and not result["forced_stop"]
    with pytest.raises(Fault):
        launcher.run(plan)
