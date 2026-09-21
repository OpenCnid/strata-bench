"""Synthetic native point/roster controls; never a continuous setup proof."""

import copy
import json
import os
from pathlib import Path
import subprocess

import pytest
from pydantic import ValidationError
from mcbench.storage import Fault, canonical
from strata_evaluator.craft_reference import parse_plan
from strata_evaluator.setup_facts import PINS, POLICY
from strata_evaluator.telemetry_auth import parse_authority
from test_craft_reference import ACTOR, reference, seal  # noqa: F401

TEAM = "33333333-3333-3333-3333-333333333333"


def point(phase):
    return {
        "policy": POLICY,
        "phase": phase,
        "transaction_id": None if phase == "startup" else "transaction",
        "server": {
            "default_game_mode": "survival",
            "world_game_mode": "survival",
            "difficulty": "normal",
            "hardcore": False,
            "world_allows_commands": False,
            "command_blocks_enabled": False,
            "rcon_enabled": False,
            "operator_levels": [],
            "command_events_seen": 0,
        },
        "pack": {
            "status": "observed",
            "mode": "expert",
            "is_expert": True,
            "is_normal": False,
            "startup_errors": 0,
            "server_errors": 0,
        },
        "team": {"status": "manager_ready"}
        if phase == "startup"
        else {
            "status": "observed",
            "team_id": TEAM,
            "team_type": "PARTY",
            "actor_rank": "MEMBER",
            "member_ids": [ACTOR],
        },
        "actor": None
        if phase == "startup"
        else {"uuid": ACTOR, "game_mode": "survival", "is_operator": False},
    }


@pytest.fixture
def native(reference):  # noqa: F811 - imported shared pytest fixture
    store, plan, events, directory, spool = reference
    plan.update(schema="strata/PrivateCraftReferencePlan/2", native_team_ids={"agent": TEAM})
    events[0]["payload_schema"] = "strata/ServerStarted/6"
    events[0]["payload"].update(
        module="strata-forge1192-telemetry/0.3.5",
        launch_identity={
            "policy": "native-server-launch-observation/1",
            "pid": 1,
            "process_started_unix_ms": 1,
            "executable": "synthetic",
            "game_directory": "synthetic",
            "world_directory": "synthetic",
            "module_file": "synthetic",
            "module_sha256": "a" * 64,
            "online_mode": True,
            "server_port": 25569,
        },
        setup_capture_policy=POLICY,
        setup_capture_support={"status": "supported", "artifacts": PINS},
    )

    def record(phase):
        return events[2] | {
            "kind": "setup_snapshot",
            "payload_schema": "strata/NativeSetupSnapshot/1",
            "server_tick": 1 if phase == "startup" else 20,
            "actor_ids": [] if phase == "startup" else [ACTOR],
            "payload": point(phase),
        }

    values = [
        *events[:2],
        record("startup"),
        record("craft_begin"),
        *events[2:4],
        record("craft_end"),
        *events[4:],
    ]
    events[:] = values
    renumber(events)
    return reference


def renumber(events):
    for index, event in enumerate(events, 1):
        event.update(seq=index, server_event_seq=index)


def test_native_mode_admin_and_registered_pack_team_points_join_but_never_score(native):
    store, _, _, _, spool = native
    seal(native)
    result = store.inspect("i", spool)
    assert result["schema"] == "strata/PrivateCraftReferenceInspection/2"
    assert result["candidate_complete"] and result["candidate_output"] == 1
    check = result["native_point_checks"]["transaction"]
    assert check["native_points_match"] and not check["continuous_history_proven"]
    assert not result["native_setup_continuity_qualified"] and not result["scoring_eligible"]
    assert store.inspect("i", spool) == result


@pytest.mark.parametrize(
    "change",
    [
        "normal",
        "inconsistent",
        "script_error",
        "operator",
        "commands",
        "creative",
        "rcon",
        "command_blocks",
        "world_cheats",
        "wrong_team",
        "invited",
        "missing_member",
        "missing_team",
        "unavailable_mode",
        "state_changed",
    ],
)
def test_native_observed_bad_or_missing_facts_do_not_admit_resource_candidate(native, change):
    store, _, events, _, spool = native
    before, after = events[3]["payload"], events[6]["payload"]
    for value in (before, after):
        if change == "normal":
            value["pack"].update(mode="normal", is_expert=False, is_normal=True)
        elif change == "inconsistent":
            value["pack"]["is_expert"] = False
        elif change == "script_error":
            value["pack"]["server_errors"] = 1
        elif change == "operator":
            value["actor"]["is_operator"] = True
        elif change == "commands":
            value["server"]["command_events_seen"] = 1
        elif change == "creative":
            value["actor"]["game_mode"] = "creative"
        elif change == "rcon":
            value["server"]["rcon_enabled"] = True
        elif change == "command_blocks":
            value["server"]["command_blocks_enabled"] = True
        elif change == "world_cheats":
            value["server"]["world_allows_commands"] = True
        elif change == "wrong_team":
            value["team"]["team_id"] = ACTOR
        elif change == "invited":
            value["team"]["actor_rank"] = "INVITED"
        elif change == "missing_member":
            value["team"]["member_ids"] = []
        elif change == "missing_team":
            value["team"] = {"status": "unavailable", "error_code": "SETUP_TEAM_MISSING"}
        elif change == "unavailable_mode":
            value["pack"] = {"status": "unavailable", "error_code": "SETUP_MODE_UNAVAILABLE"}
    if change == "state_changed":
        after["server"]["difficulty"] = "hard"
    seal(native)
    result = store.inspect("i", spool)
    assert result["candidate_output"] == 0 and not result["candidate_complete"]
    assert result["rejected_resource_witnesses"][0]["reason"] == "CRAFT_NATIVE_POINTS_UNPROVEN"
    assert result["native_point_checks"]["transaction"]["reasons"]


@pytest.mark.parametrize(
    "change,code",
    [
        ("missing_start", "SETUP_ACTOR_MISMATCH"),
        ("missing_point", "SETUP_POINT_MISSING"),
        ("wrong_actor", "SETUP_ACTOR_MISMATCH"),
        ("wrong_transaction", "SETUP_POINT_NOT_ADJACENT"),
        ("non_adjacent", "SETUP_POINT_NOT_ADJACENT"),
        ("late_point", "SETUP_POINT_NOT_ADJACENT"),
        ("counter_rollback", "SETUP_COMMAND_COUNTER_ROLLBACK"),
        ("duplicate_start", "SETUP_START_INVALID"),
        ("unsupported", "CRAFT_NATIVE_SETUP_MISSING"),
    ],
)
def test_missing_foreign_reordered_and_unsupported_native_observations_fail_closed(
    native, change, code
):
    store, _, events, _, spool = native
    if change == "missing_start":
        events.pop(2)
    elif change == "missing_point":
        events.pop(3)
    elif change == "wrong_actor":
        events[3]["actor_ids"] = [TEAM]
    elif change == "wrong_transaction":
        events[3]["payload"]["transaction_id"] = "foreign"
    elif change == "non_adjacent":
        events.insert(4, copy.deepcopy(events[2]) | {"server_tick": 20})
    elif change == "late_point":
        events[3]["server_tick"] = 19
    elif change == "counter_rollback":
        events[3]["payload"]["server"]["command_events_seen"] = 1
    elif change == "duplicate_start":
        events.insert(3, copy.deepcopy(events[2]))
    elif change == "unsupported":
        events[0]["payload"]["setup_capture_support"] = {
            "status": "unsupported",
            "artifacts": {key: None for key in PINS},
        }
    renumber(events)
    seal(native)
    with pytest.raises(Fault, match=code):
        store.inspect("i", spool)


def test_version2_requires_exact_registered_native_team_mapping(native):
    _, plan, _, _, _ = native
    plan["native_team_ids"] = {"other": TEAM}
    with pytest.raises(ValidationError, match="CRAFT_NATIVE_ROSTER_SCOPE"):
        parse_plan(plan)


def test_two_native_crafts_remain_distinct(native):
    store, plan, events, _, spool = native
    plan["predicate"]["minimum_output"] = 2
    second = copy.deepcopy(events[3:8])
    for event in second:
        if "transaction_id" in event["payload"]:
            event["payload"]["transaction_id"] = "second"
    events[8:8] = second
    renumber(events)
    seal(native)
    result = store.inspect("i", spool)
    assert result["candidate_complete"] and result["candidate_output"] == 2
    assert set(result["native_point_checks"]) == {"transaction", "second"}


def test_unavailable_startup_team_manager_cannot_be_inferred_from_later_points(native):
    store, _, events, _, spool = native
    events[2]["payload"]["team"] = {"status": "unavailable", "error_code": "SETUP_TEAM_MANAGER"}
    seal(native)
    result = store.inspect("i", spool)
    assert result["candidate_output"] == 0
    assert "startup:team_manager_unavailable" in result["native_point_checks"]["transaction"]["reasons"]


def test_actual_java_signer_carries_native_point_contract_without_a_game(native, tmp_path):
    java, classpath = (
        os.environ.get("STRATA_TELEMETRY_TEST_JAVA"),
        os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH"),
    )
    if not java or not classpath:
        pytest.skip("Pinned JVM opt-in required; fabricated point data")
    store, plan, events, directory, _ = native
    store.seal(plan, directory)
    store.preflight("i")
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    spool = tmp_path / "jvm"
    spool.mkdir()
    config = {
        "schema": "strata/ForgeTelemetryConfig/3",
        "campaign_id": plan["campaign_id"],
        "epoch": 1,
        "spool_directory": str(spool),
        "max_bytes": 1048576,
        "max_events": 64,
        "recipe_ids": [],
        "config_queries": [],
        "authentication": authority.producer_config(),
    }
    (directory / "config.json").write_bytes(canonical(config))
    (directory / "events.json").write_bytes(canonical(events))
    completed = subprocess.run(
        [
            java,
            "-cp",
            Path(classpath).read_text(),
            "io.github.opencnid.strata.telemetry.AuthenticatedSpoolFixture",
            str(directory / "config.json"),
            plan["game_directory"],
            str(directory / "events.json"),
        ],
        capture_output=True,
        timeout=20,
        **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
    )
    assert completed.returncode == 0, completed.stderr.decode()
    report = store.inspect("i", next(spool.glob("*.authenticated.jsonl")))
    assert (
        report["candidate_output"] == 1
        and report["native_point_checks"]["transaction"]["native_points_match"]
    )
    assert not report["scoring_eligible"]
