"""Synthetic checks for the explicitly root-only actual-runtime fixture."""

import copy
import json
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault
from test_native_selected_activation import selected_seed
from native_activation_probe import ActivationProbe
from native_mcp_identity_probe import run
from native_no_self_play_probe import NoSelfPlayProbe, ROOT_CODE


def test_no_self_play_seed_is_registered_before_source_calls(database, cas, tmp_path, example, configs):
    source, service, ref = selected_seed(database, cas, tmp_path, example, configs, arm="no-self-play")
    runtime, plan, _ = source
    agent = json.loads(database.connection.execute("SELECT agents FROM campaigns").fetchone()[0])[0]
    assert agent["self_play"] is False and agent["helper_limit"] == plan.helper_limit == 0
    assert database.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1
    assert runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 14
    probe = object.__new__(ActivationProbe)
    probe.ref, probe.output = ref, tmp_path
    prepared = probe.prepare(runtime, plan, helper_free=True)
    assert prepared.helper_skill_activation_ref is None and prepared.skill_activation_ref == ref
    assert service.load(ref)["skills"]["learned-crafting"]["revision"]["kind"] == "executable"
    assert probe.calls("/root").count(("artifact_read", {"path": "active/learned-crafting/scripts/check.js"})) == 1


def test_full_seed_cannot_be_relabelled_helper_free(database, cas, tmp_path, example, configs):
    source, _, ref = selected_seed(database, cas, tmp_path, example, configs)
    probe = object.__new__(ActivationProbe)
    probe.ref, probe.output = ref, tmp_path
    with pytest.raises(Fault, match="ACTIVATION_FIXTURE_ARM"):
        probe.prepare(source[0], source[1], helper_free=True)


@pytest.mark.parametrize("value", [True, 1, None, "true"])
def test_root_only_run_requires_explicit_selected_profile(tmp_path, value):
    with pytest.raises(Fault, match="NO_SELF_PLAY_PROFILE_REQUIRED"):
        run(tmp_path / "missing.exe", tmp_path, no_self_play=value)
    assert not list(tmp_path.iterdir())


def transcript(probe, step, value):
    call = probe.next(step, "case-" + str(step))
    return {"input": [call, {"type": call["type"] + "_output", "call_id": call["call_id"], "output": value}]}


def test_refusal_requires_exact_call_identity_and_stable_return():
    probe = NoSelfPlayProbe()
    body = transcript(probe, 1, "Unknown tool: collaboration.spawn_agent")
    probe.observe("/root", body)
    probe.observe("/root", body)
    with pytest.raises(Fault, match="NO_SELF_PLAY_ACTOR"):
        probe.observe("/root/forbidden_child", body)
    altered = copy.deepcopy(body)
    altered["input"][1]["output"] = "success"
    with pytest.raises(Fault, match="NO_SELF_PLAY_RETURN_CHANGED"):
        probe.observe("/root", altered)
    altered = copy.deepcopy(body)
    altered["input"][0]["namespace"] = "functions"
    with pytest.raises(Fault, match="NO_SELF_PLAY_CALL_CHANGED"):
        probe.observe("/root", altered)
    with pytest.raises(Fault, match="NO_SELF_PLAY_REPLAY"):
        probe.next(1, "case-1")


def test_pinned_native_unsupported_wire_shapes_are_exact(database):
    database.connection.execute("CREATE TABLE native_participants(job TEXT,depth INTEGER)")
    database.connection.execute("CREATE TABLE operations(kind TEXT)")
    probe = NoSelfPlayProbe()
    for step, message in ((1, "unsupported call: collaborationspawn_agent"),
                          (2, "unsupported custom tool call: collaborationspawn_agent")):
        probe.observe("/root", transcript(probe, step, message))
    plan = SimpleNamespace(job_id="job", helper_limit=0, helper_skill_activation_ref=None,
                           config_overrides={"features.multi_agent_v2": False, "agents.enabled": False})
    provider = SimpleNamespace(requests=[], errors=[], identities=[])
    assert probe.report(database, plan, provider)["checks"]["both_spawn_wire_types_refused"]
    probe.returns[next(iter(probe.calls))] = "unsupported custom tool call: collaborationspawn_agent"
    assert not probe.report(database, plan, provider)["checks"]["both_spawn_wire_types_refused"]


@pytest.mark.parametrize("denial,passes", [
    ("Unknown tool: collaboration.spawn_agent", True),
    ("Unrecognized function name 'collaboration.spawn_agent'", True),
    ("Error: random failure", False), (None, False), ({"error": "Unknown tool"}, False),
])
def test_report_does_not_infer_refusal_from_unrelated_error(database, denial, passes):
    database.connection.execute("CREATE TABLE native_participants(job TEXT,depth INTEGER)")
    database.connection.execute("INSERT INTO native_participants VALUES('job',0)")
    database.connection.execute("CREATE TABLE operations(kind TEXT)")
    probe = NoSelfPlayProbe()
    for step in (1, 2):
        probe.observe("/root", transcript(probe, step, denial))
    value = [{"type": "input_text", "text": "Script completed\nWall time 0.1 seconds\nOutput:\n"},
        {"type": "input_text", "text": '\n'.join(json.dumps(v) for v in (
        {"initial_private_state": None}, {"retained_private_state": "permitted root state"}, {"helper_tools": []}))}]
    body = transcript(probe, 3, value)
    assert body["input"][0]["input"] == ROOT_CODE
    probe.observe("/root", body)
    plan = SimpleNamespace(job_id="job", helper_limit=0, helper_skill_activation_ref=None,
                           config_overrides={"features.multi_agent_v2": False, "agents.enabled": False})
    provider = SimpleNamespace(requests=[None]*5, errors=[], identities=[{"agent": "/root"}]*5)
    checks = probe.report(database, plan, provider)["checks"]
    assert checks.pop("both_spawn_wire_types_refused") is passes
    assert all(checks.values())
