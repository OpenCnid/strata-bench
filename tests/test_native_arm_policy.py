"""Preregistered no-self-play authority; synthetic providers, never qualification."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_arm_policy import require_arm_policy
from mcbench.native_broker_policy import (POLICY, NO_HELPER_POLICY, NO_HELPER_TEAM_POLICY,
    restricted_settings, validate_broker_settings, settings_policy, broker_tools, broker_approvals)
from mcbench.native_checkpoint import NativeCheckpointStates
from mcbench.native_tool_projection import pin_tool_projection, read_tool_projection, request_projection, require_tool_projection
from mcbench.storage import Fault, Principal
from test_native_admission import begin, broker_meta
from test_native_checkpoint import admitted as checkpoint_admitted
from test_native_export import stopped
from test_native_tool_projection import wire_tools


@pytest.fixture
def controlled(database, cas, tmp_path, example, configs):
    request = SimpleNamespace(param="no-self-play")
    return checkpoint_admitted.__wrapped__(database, cas, tmp_path, example, configs, request, model="gpt-6-luna")


def test_root_permitted_child_refused_before_envelope_or_admission(controlled):
    _, gate, broker, plan, request, prepare, _ = controlled
    assert require_arm_policy(gate.db.connection, gate.cas, plan) == "no-self-play"
    begin(controlled, request("root-call"))
    assert broker.call("artifact_list", {}, broker_meta(model=plan.model)) == {"files": []}
    before = gate.budgets.status("a1")
    operations = list(gate.db.connection.execute("SELECT id FROM operations"))
    with pytest.raises(Fault, match="HELPER_CAPACITY"):
        prepare(request("child-call", "child", "/root/child", "root", child=True))
    assert gate.budgets.status("a1") == before
    assert list(gate.db.connection.execute("SELECT id FROM operations")) == operations
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1


@pytest.mark.parametrize("value", [True, 0, None])
def test_native_agents_switch_must_explicitly_disable_helpers(controlled, value):
    _, gate, _, plan, _, _, _ = controlled
    plan.config_overrides["agents.enabled"] = value
    with pytest.raises(Fault, match="NATIVE_HELPER_TOOLS_ENABLED"):
        require_arm_policy(gate.db.connection, gate.cas, plan)


def test_legacy_contradictory_job_is_fenced_at_dispatch_and_broker(controlled):
    _, gate, broker, plan, request, prepare, _ = controlled
    begin(controlled, request("first"))
    before = gate.budgets.status("a1")
    plan.broker_policy, plan.helper_limit = POLICY, 2
    plan.config_overrides["features.multi_agent_v2"] = True
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    with pytest.raises(Fault, match="NATIVE_NO_SELF_PLAY"):
        prepare(request("second"))
    with pytest.raises(Fault, match="NATIVE_NO_SELF_PLAY"):
        broker.call("artifact_list", {}, broker_meta(model=plan.model))
    assert gate.budgets.status("a1") == before
    assert gate.db.connection.execute("SELECT count(*) FROM native_request_admissions").fetchone()[0] == 1


@pytest.mark.parametrize("broker_policy", [POLICY, None])
def test_start_rejects_no_self_play_violation_before_native_intent(controlled, broker_policy):
    _, gate, _, original, _, _, _ = controlled
    from mcbench.inventory import file_hash
    from mcbench.records import BudgetLedger
    plan = original.model_copy(deep=True, update={"job_id": "forbidden", "broker_policy": broker_policy, "helper_limit": 2})
    plan.config_overrides["features.multi_agent_v2"] = True
    plan.binary_digest = file_hash(Path(plan.executable))
    Path(plan.workspace).mkdir()
    Path(plan.profile_directory).mkdir()
    reserve = BudgetLedger.model_validate_json(gate.db.connection.execute("SELECT body FROM ledger LIMIT 1").fetchone()[0])
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="NATIVE_NO_SELF_PLAY"):
        runtime.start(plan, reserve, fixture_argv=[plan.executable, "-c", "raise SystemExit(99)"])
    assert not runtime.live and gate.budgets.status("a1") == before
    assert gate.db.connection.execute("SELECT 1 FROM native_jobs WHERE id='forbidden'").fetchone() is None


def test_registration_requires_zero_helpers_and_historical_root_export_is_valid(controlled):
    _, gate, _, plan, _, _, _ = controlled
    runtime, _, _ = stopped.__wrapped__(controlled)
    fixture = gate.db.checkpoint_fixture
    with pytest.raises(Fault, match="NATIVE_RETENTION_SCOPE"):
        NativeCheckpointStates(runtime).register(fixture["config"], fixture["agent"].model_copy(update={"helper_limit": 1}))
    export = runtime.export_broker_state(plan.job_id)
    assert export.startswith("cas:sha256:")
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1
    assert runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 14


@pytest.mark.parametrize("missing", ["row", "table"])
def test_missing_registration_cannot_reenable_declared_no_self_play(controlled, missing):
    _, gate, _, plan, request, prepare, _ = controlled
    gate.db.connection.execute("DROP TABLE native_retention_policies" if missing == "table"
                               else "DELETE FROM native_retention_policies")
    with pytest.raises(Fault, match="NATIVE_RETENTION_NOT_REGISTERED"):
        require_arm_policy(gate.db.connection, gate.cas, plan)
    with pytest.raises(Fault, match="NATIVE_RETENTION_NOT_REGISTERED"):
        prepare(request("refused"))


@pytest.mark.parametrize("policy", [NO_HELPER_POLICY, NO_HELPER_TEAM_POLICY])
def test_explicit_helper_free_settings_and_catalog_are_separate(controlled, policy):
    _, gate, _, original, _, _, put = controlled
    config = restricted_settings(policy=policy) | {"mcp_servers.strata_broker": {
        "required": True, "enabled_tools": list(broker_tools(policy)), "tools": broker_approvals(policy)}}
    plan = NativeLaunch.model_validate(original.model_dump() | {"broker_policy": policy,
        "config_overrides": config, "team_policy_ref": put({"is_example": True}) if policy == NO_HELPER_TEAM_POLICY else None})
    body = {"input": [wire_tools("helper")]}
    projection = request_projection(body, "executor", helper_free=True)
    plan.tool_projection_ref = pin_tool_projection(gate.cas, plan, {"executor": projection}, helper_free=True)
    assert set(read_tool_projection(gate.cas, plan)) == {"executor"}
    pin = gate.cas.json(Principal("operator", "operator"), "operator", plan.tool_projection_ref)
    assert pin["schema"] == "strata/NativeToolProjection/6" and "helper_ref" not in pin
    assert settings_policy(policy) == "native-broker-closed-features-stdio/4"
    require_tool_projection(gate.cas, plan, body, "executor")
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        require_tool_projection(gate.cas, plan, body, "helper")
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SHAPE"):
        require_tool_projection(gate.cas, plan, {"input": [wire_tools("executor")]}, "executor")
    for change in (True, 0, None):
        changed = copy.deepcopy(config)
        changed["features.multi_agent_v2"] = change
        with pytest.raises(Fault, match="BROKER_TOOL_POLICY"):
            validate_broker_settings(changed, policy=policy)
    with pytest.raises(Fault, match="BROKER_TOOL_POLICY"):
        validate_broker_settings(config)


@pytest.mark.parametrize("update", [{"helper_limit": 1}, {"role": "helper"}, {"depth": 1},
    {"parent_job_id": "parent"}, {"helper_skill_activation_ref": "cas:sha256:" + "a" * 64}])
def test_helper_free_launch_has_no_hidden_helper_capability(controlled, update):
    plan = controlled[3]
    with pytest.raises(ValidationError):
        NativeLaunch.model_validate(plan.model_dump() | update)


@pytest.mark.parametrize("update", [{"helper_limit": 1}, {"helper_limit": False},
    {"purpose": "conformance"}, {"purpose": "development_piloting"}, {"model": "gpt-5.6-luna"}])
def test_helper_free_projection_cannot_change_selected_scope(controlled, update):
    _, gate, _, plan, _, _, _ = controlled
    projection = request_projection({"input": [wire_tools("helper")]}, "executor", helper_free=True)
    plan.tool_projection_ref = pin_tool_projection(gate.cas, plan, {"executor": projection}, helper_free=True)
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        read_tool_projection(gate.cas, plan.model_copy(update=update))


@pytest.mark.parametrize("value", [0, None, True])
def test_live_agent_boolean_must_match_registered_bytes(controlled, value):
    _, gate, _, plan, _, _, _ = controlled
    agents = json.loads(gate.db.connection.execute("SELECT agents FROM campaigns").fetchone()[0])
    agents[0]["self_play"] = value
    gate.db.connection.execute("UPDATE campaigns SET agents=?", (json.dumps(agents),))
    with pytest.raises(Fault, match="NATIVE_ARM_SCOPE"):
        require_arm_policy(gate.db.connection, gate.cas, plan)


@pytest.mark.parametrize("mutation", ["self_play", "agent_limit", "scope", "unknown_arm"])
def test_private_registration_cannot_silently_relabel_control(controlled, mutation):
    _, gate, _, plan, _, _, _ = controlled
    row = gate.db.connection.execute("SELECT * FROM native_retention_policies").fetchone()
    if mutation == "unknown_arm":
        policy = gate.cas.json(Principal("operator", "operator"), "operator", row["ref"])
        policy["arm"] = "unregistered"
        from mcbench.storage import canonical
        ref = gate.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(policy))
        gate.db.connection.execute("UPDATE native_retention_policies SET ref=?", (ref,))
    else:
        agent = json.loads(row["agent_config"])
        agent[{"self_play": "self_play", "agent_limit": "helper_limit", "scope": "agent_id"}[mutation]] = {
            "self_play": True, "agent_limit": 1, "scope": "foreign"}[mutation]
        gate.db.connection.execute("UPDATE native_retention_policies SET agent_config=?", (json.dumps(agent),))
    with pytest.raises((Fault, ValidationError)):
        require_arm_policy(gate.db.connection, gate.cas, plan)
