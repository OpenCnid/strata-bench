"""Signed synthetic FTB map changes, admission and candidate refusal; no live pack claim."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.setup_history import POLICY_V3
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_global_setup_history import globals_history  # noqa: F401
from test_telemetry_clocks import clocked  # noqa: F401
from test_setup_history import history  # noqa: F401
from test_setup_facts import native  # noqa: F401
from test_craft_reference import reference  # noqa: F401
from test_setup_control import source


@pytest.fixture
def team_history(globals_history):  # noqa: F811
    events = globals_history[2]
    events[0]["payload_schema"] = "strata/ServerStarted/11"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.10")
    events[0]["payload"]["setup_history_support"].update(policy=POLICY_V3, team_map_hooks_verified=True)
    for event in events:
        if event["kind"] == "setup_history":
            event["payload_schema"] = "strata/NativeSetupHistory/3"
            event["payload"]["policy"] = POLICY_V3
            event["payload"]["attempts"]["team_map_write"] = 0
    globals_history[1]["required_history_policy"] = POLICY_V3
    return globals_history


@pytest.mark.parametrize("writes", [0, 8])
def test_reverted_team_maps_taint_otherwise_valid_private_craft(team_history, tmp_path, writes):
    for event in team_history[2]:
        if event["kind"] == "setup_history" and event["payload"]["phase"] != "startup":
            event["payload"]["attempts"]["team_map_write"] = writes
    folder, authority, path, boot = source(team_history, tmp_path)
    assert startup_prefix(folder, authority, boot)["history"]["policy"] == POLICY_V3
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert ("observed:team_map_write" in report["setup_history"]["reasons"]) == bool(writes)
    candidate = team_history[0].inspect("i", path)
    assert candidate["required_history_policy"] == POLICY_V3
    assert candidate["candidate_complete"] is (writes == 0)
    assert not candidate["scoring_eligible"] and not candidate["native_setup_continuity_qualified"]
    if writes:
        assert candidate["rejected_resource_witnesses"] == [
            {"transaction_id": "transaction", "reason": "CRAFT_NATIVE_HISTORY_TAINTED"}]


@pytest.mark.parametrize("fault", ["missing-route", "old-policy", "old-schema", "old-module", "rollback", "missing-hook"])
def test_team_map_history_requires_its_exact_module_routes_and_support(team_history, tmp_path, fault):
    events = team_history[2]
    histories = [e for e in events if e["kind"] == "setup_history"]
    if fault == "missing-route":
        del histories[-1]["payload"]["attempts"]["team_map_write"]
    elif fault == "old-policy":
        histories[-1]["payload"]["policy"] = "native-e9e-setup-mutation-watch/2"
    elif fault == "old-schema":
        histories[-1]["payload_schema"] = "strata/NativeSetupHistory/2"
    elif fault == "old-module":
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.9"
    elif fault == "rollback":
        histories[-2]["payload"]["attempts"]["team_map_write"] = 8
    else:
        del events[0]["payload"]["setup_history_support"]["team_map_hooks_verified"]
    _, authority, path, _ = source(team_history, tmp_path)
    with pytest.raises((Fault, ValidationError)):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_unavailable_team_map_hook_cannot_admit_or_contribute_candidate(team_history, tmp_path):
    team_history[2][0]["payload"]["setup_history_support"]["team_map_hooks_verified"] = False
    folder, authority, path, boot = source(team_history, tmp_path)
    with pytest.raises(Fault, match="SETUP_CONTROL_HOOKS_REQUIRED"):
        startup_prefix(folder, authority, boot)
    result = team_history[0].inspect("i", path)
    assert "team_map_hook_unavailable" in result["native_mutation_history"]["reasons"]
    assert not result["candidate_complete"]


def test_team_history_cannot_replace_a_sealed_global_only_requirement(team_history, tmp_path):
    team_history[1]["required_history_policy"] = "native-e9e-setup-mutation-watch/2"
    _, _, path, _ = source(team_history, tmp_path)
    with pytest.raises(Fault, match="CRAFT_NATIVE_HISTORY_MISSING"):
        team_history[0].inspect("i", path)


def test_tainted_team_startup_cannot_admit_participant(team_history, tmp_path):
    for event in team_history[2]:
        if event["kind"] == "setup_history":
            event["payload"]["attempts"]["team_map_write"] = 8
    folder, authority, _, boot = source(team_history, tmp_path)
    with pytest.raises(Fault, match="SETUP_CONTROL_BASELINE_TAINTED"):
        startup_prefix(folder, authority, boot)
