"""Versioned private signed global-map history; synthetic contents, no real pack run."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.setup_control import startup_prefix
from strata_evaluator.setup_history import POLICY_V2
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_telemetry_clocks import clocked  # noqa: F401
from test_setup_history import history  # noqa: F401
from test_setup_facts import native  # noqa: F401
from test_craft_reference import reference  # noqa: F401
from test_setup_control import source


@pytest.fixture
def globals_history(clocked):  # noqa: F811
    events = clocked[2]
    events[0]["payload_schema"] = "strata/ServerStarted/10"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.9")
    events[0]["payload"]["setup_history_support"].update(policy=POLICY_V2, global_map_hooks_verified=True)
    for e in events:
        if e["kind"] == "setup_history":
            e["payload_schema"] = "strata/NativeSetupHistory/2"
            e["payload"]["policy"] = POLICY_V2
            e["payload"]["attempts"]["global_mode_write"] = 0
    clocked[1].update(schema="strata/PrivateCraftReferencePlan/3", required_history_policy=POLICY_V2)
    return clocked


@pytest.mark.parametrize("writes", [0, 2])
def test_signed_global_history_joins_native_points_and_retains_reverted_writes(globals_history, tmp_path, writes):
    events = globals_history[2]
    for e in events:
        if e["kind"] == "setup_history" and e["payload"]["phase"] != "startup":
            e["payload"]["attempts"]["global_mode_write"] = writes
    folder, authority, path, boot = source(globals_history, tmp_path)
    assert startup_prefix(folder, authority, boot)["history"]["policy"] == POLICY_V2
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    h = report["setup_history"]
    assert h["policy"] == POLICY_V2
    assert ("observed:global_mode_write" in h["reasons"]) == bool(writes)
    assert not h["continuous_history_proven"] and not report["scoring_eligible"]
    candidate = globals_history[0].inspect("i", path)
    assert candidate["required_history_policy"] == POLICY_V2
    assert candidate["candidate_complete"] is (writes == 0)
    assert not candidate["scoring_eligible"]
    if writes:
        assert candidate["rejected_resource_witnesses"] == [
            {"transaction_id": "transaction", "reason": "CRAFT_NATIVE_HISTORY_TAINTED"}]


@pytest.mark.parametrize("fault", ["missing-route", "old-policy", "old-schema", "old-module", "rollback", "hook-missing"])
def test_new_global_history_cannot_be_omitted_downgraded_or_erased(globals_history, tmp_path, fault):
    events = globals_history[2]
    histories = [e for e in events if e["kind"] == "setup_history"]
    if fault == "missing-route":
        del histories[-1]["payload"]["attempts"]["global_mode_write"]
    elif fault == "old-policy":
        histories[-1]["payload"]["policy"] = "native-e9e-setup-mutation-watch/1"
    elif fault == "old-schema":
        histories[-1]["payload_schema"] = "strata/NativeSetupHistory/1"
    elif fault == "old-module":
        events[0]["payload"]["module"] = "strata-forge1192-telemetry/0.3.8"
    elif fault == "rollback":
        histories[-2]["payload"]["attempts"]["global_mode_write"] = 2
    else:
        del events[0]["payload"]["setup_history_support"]["global_map_hooks_verified"]
    _, authority, path, _ = source(globals_history, tmp_path)
    with pytest.raises((Fault, ValidationError)):
        inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_unavailable_hook_is_explicit_and_never_qualified(globals_history, tmp_path):
    globals_history[2][0]["payload"]["setup_history_support"]["global_map_hooks_verified"] = False
    _, authority, path, _ = source(globals_history, tmp_path)
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    assert "global_map_hook_unavailable" in report["setup_history"]["reasons"]
    assert not report["scoring_eligible"]


def test_new_history_cannot_silently_replace_a_legacy_plan_requirement(globals_history, tmp_path):
    globals_history[1]["required_history_policy"] = "native-e9e-setup-mutation-watch/1"
    _, _, path, _ = source(globals_history, tmp_path)
    with pytest.raises(Fault, match="CRAFT_NATIVE_HISTORY_MISSING"):
        globals_history[0].inspect("i", path)


@pytest.mark.parametrize("fault", ["hook", "tainted"])
def test_new_history_cannot_admit_participant_with_unavailable_or_tainted_global_map(globals_history, tmp_path, fault):
    if fault == "hook":
        globals_history[2][0]["payload"]["setup_history_support"]["global_map_hooks_verified"] = False
    else:
        for event in globals_history[2]:
            if event["kind"] == "setup_history":
                event["payload"]["attempts"]["global_mode_write"] = 6
    folder, authority, _, boot = source(globals_history, tmp_path)
    with pytest.raises(Fault, match="SETUP_CONTROL_(HOOKS_REQUIRED|BASELINE_TAINTED)"):
        startup_prefix(folder, authority, boot)
