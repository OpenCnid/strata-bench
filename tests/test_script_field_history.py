"""Signed synthetic Rhino field writes and candidate rejection; exact live control remains separate."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.setup_history import POLICY_V4, POLICY_V5, POLICY_V6
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_team_map_history import team_history  # noqa: F401
from test_global_setup_history import globals_history  # noqa: F401
from test_telemetry_clocks import clocked  # noqa: F401
from test_setup_history import history  # noqa: F401
from test_setup_facts import native  # noqa: F401
from test_craft_reference import reference  # noqa: F401
from test_setup_control import source


@pytest.fixture(params=[4, 5, 6])
def fields_history(team_history, request):  # noqa: F811
    events = team_history[2]
    version = request.param
    policy = {4: POLICY_V4, 5: POLICY_V5, 6: POLICY_V6}[version]
    events[0]["payload_schema"] = f"strata/ServerStarted/{version + 8}"
    events[0]["payload"].update(module=f"strata-forge1192-telemetry/0.3.{version + 7}")
    events[0]["payload"]["setup_history_support"].update(policy=policy, script_field_hooks_verified=True)
    for event in events:
        if event["kind"] == "setup_history":
            event["payload_schema"] = f"strata/NativeSetupHistory/{version}"
            event["payload"]["policy"] = policy
            event["payload"]["attempts"].update(team_script_field_write=0, script_reflection_overflow=0)
            if version >= 6:
                event["payload"]["attempts"]["script_handle_unresolved"] = 0
    team_history[1]["required_history_policy"] = policy
    return team_history


@pytest.mark.parametrize("writes", [0, 8])
def test_reverted_script_fields_taint_otherwise_valid_private_craft(fields_history, tmp_path, writes):
    for event in fields_history[2]:
        if event["kind"] == "setup_history" and event["payload"]["phase"] != "startup":
            event["payload"]["attempts"]["team_script_field_write"] = writes
    folder, authority, path, boot = source(fields_history, tmp_path)
    assert startup_prefix(folder, authority, boot)["history"]["policy"] == fields_history[1]["required_history_policy"]
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert ("observed:team_script_field_write" in report["setup_history"]["reasons"]) == bool(writes)
    candidate = fields_history[0].inspect("i", path)
    assert candidate["required_history_policy"] == fields_history[1]["required_history_policy"]
    assert candidate["candidate_complete"] is (writes == 0)
    assert not candidate["scoring_eligible"] and not candidate["native_setup_continuity_qualified"]
    if writes:
        assert candidate["rejected_resource_witnesses"] == [
            {"transaction_id": "transaction", "reason": "CRAFT_NATIVE_HISTORY_TAINTED"}]


@pytest.mark.parametrize("fault", ["missing-route", "old-policy", "old-schema", "old-module", "rollback", "missing-hook"])
def test_script_field_history_requires_its_exact_module_routes_and_support(fields_history, tmp_path, fault):
    events = fields_history[2]
    histories = [e for e in events if e["kind"] == "setup_history"]
    if fault == "missing-route":
        del histories[-1]["payload"]["attempts"]["team_script_field_write"]
    elif fault == "old-policy":
        histories[-1]["payload"]["policy"] = "native-e9e-setup-mutation-watch/3"
    elif fault == "old-schema":
        histories[-1]["payload_schema"] = "strata/NativeSetupHistory/3"
    elif fault == "old-module":
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.10"
    elif fault == "rollback":
        histories[-2]["payload"]["attempts"]["team_script_field_write"] = 8
    else:
        del events[0]["payload"]["setup_history_support"]["script_field_hooks_verified"]
    _, authority, path, _ = source(fields_history, tmp_path)
    with pytest.raises((Fault, ValidationError)):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_unavailable_script_field_hook_cannot_admit_or_contribute_candidate(fields_history, tmp_path):
    fields_history[2][0]["payload"]["setup_history_support"]["script_field_hooks_verified"] = False
    folder, authority, path, boot = source(fields_history, tmp_path)
    with pytest.raises(Fault, match="SETUP_CONTROL_HOOKS_REQUIRED"):
        startup_prefix(folder, authority, boot)
    result = fields_history[0].inspect("i", path)
    assert "script_field_hook_unavailable" in result["native_mutation_history"]["reasons"]
    assert not result["candidate_complete"]


def test_fields_cannot_replace_a_sealed_map_only_requirement(fields_history, tmp_path):
    fields_history[1]["required_history_policy"] = "native-e9e-setup-mutation-watch/3"
    _, _, path, _ = source(fields_history, tmp_path)
    with pytest.raises(Fault, match="CRAFT_NATIVE_HISTORY_MISSING"):
        fields_history[0].inspect("i", path)


def test_tainted_script_field_startup_cannot_admit_participant(fields_history, tmp_path):
    for event in fields_history[2]:
        if event["kind"] == "setup_history":
            event["payload"]["attempts"]["team_script_field_write"] = 8
    folder, authority, _, boot = source(fields_history, tmp_path)
    with pytest.raises(Fault, match="SETUP_CONTROL_BASELINE_TAINTED"):
        startup_prefix(folder, authority, boot)


def test_unresolved_deep_reflection_taints_candidate(fields_history, tmp_path):
    for event in fields_history[2]:
        if event["kind"] == "setup_history" and event["payload"]["phase"] != "startup":
            event["payload"]["attempts"]["script_reflection_overflow"] = 1
    _, _, path, _ = source(fields_history, tmp_path)
    candidate = fields_history[0].inspect("i", path)
    assert "observed:script_reflection_overflow" in candidate["native_mutation_history"]["reasons"]
    assert not candidate["candidate_complete"]


def test_rank_owner_policy_cannot_be_relabelled_as_its_predecessor(fields_history, tmp_path):
    events = fields_history[2]
    events[0]["payload"]["setup_history_support"]["policy"] = (
        {POLICY_V4: "native-e9e-setup-mutation-watch/3", POLICY_V5: POLICY_V4, POLICY_V6: POLICY_V5}
        [fields_history[1]["required_history_policy"]])
    _, authority, path, _ = source(fields_history, tmp_path)
    with pytest.raises((Fault, ValidationError)):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_actual_java_signer_carries_versioned_rank_owner_contract(fields_history, tmp_path):
    from test_setup_facts import test_actual_java_signer_carries_native_point_contract_without_a_game
    test_actual_java_signer_carries_native_point_contract_without_a_game(fields_history, tmp_path)


def test_opaque_handles_taint_current_history_and_reject_legacy_routes(fields_history, tmp_path):
    for event in fields_history[2]:
        if event["kind"] == "setup_history" and event["payload"]["phase"] != "startup":
            event["payload"]["attempts"]["script_handle_unresolved"] = 4
    _, _, path, _ = source(fields_history, tmp_path)
    if fields_history[1]["required_history_policy"] != POLICY_V6:
        with pytest.raises((Fault, ValidationError)):
            fields_history[0].inspect("i", path)
    else:
        candidate = fields_history[0].inspect("i", path)
        assert "observed:script_handle_unresolved" in candidate["native_mutation_history"]["reasons"]
        assert not candidate["candidate_complete"] and not candidate["scoring_eligible"]
        assert candidate["rejected_resource_witnesses"] == [
            {"transaction_id": "transaction", "reason": "CRAFT_NATIVE_HISTORY_TAINTED"}]
