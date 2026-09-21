"""Synthetic verifier negatives; actual native evidence is a separate explicit run."""

import copy
import importlib
import json
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_state_canaries")


def fixture(module):
    probe = module.StateCanaries()
    probe.cells = dict(zip(module.ACTORS, ("root-cell", "helper-cell")))
    probe.finished = set(module.ACTORS)
    for agent in module.ACTORS:
        peer = probe.other(agent)
        own = probe.markers[agent]
        phases = {
            "initialize": [
                      {"probe": "initial_state", "empty": True, "foreign": True},
                      {"probe": "own_initial", "value": own}],
            "store_read": [{"probe": "own_later", "value": own, "foreign": True}],
            "own_wait": [{"probe": "own_completion", "value": own},
                         {"probe": "cell_end", "at_ms": 2000}],
            "foreign_read": probe.cells[peer], "foreign_cancel": probe.cells[peer],
            "missing_read": module.MISSING_CELL}
        for phase, value in phases.items():
            key = agent + ":" + phase
            if phase in {"foreign_read", "foreign_cancel", "missing_read"}:
                value = "Script failed\nWall time 0.0 seconds\nOutput:\n\nScript error:\nexec cell " + value + " not found"
            if isinstance(value, list):
                value = "\n".join(json.dumps(v) for v in value)
                if phase == "own_wait":
                    value = "Script completed\n" + value
            probe.calls[key] = {"agent": agent, "phase": phase}
            probe.outputs[key] = {"agent": agent, "output": value}
            probe.observed_ms[key] = 1000
        probe.requests.append({"agent": agent, "body": {"output": own}})
    return probe


def test_positive_verifier_fixture(module):
    assert all(fixture(module).report()["checks"].values())


@pytest.mark.parametrize("case", ["missing_actor", "same_cell", "missing_output", "store_leak",
    "overwrite", "coerced_boolean", "missing_control", "unrelated_error", "foreign_completion",
    "foreign_cancel", "own_cancelled", "input_leak", "late_attempt", "missing_timestamp"])
def test_false_success_rejected(module, case):
    p = fixture(module)
    a, b = module.ACTORS
    key = a + ":"
    if case == "missing_actor":
        p.finished.remove(b)
    elif case == "same_cell":
        p.cells[b] = p.cells[a]
    elif case == "missing_output":
        del p.outputs[key + "store_read"]
    elif case in {"store_leak", "overwrite", "coerced_boolean"}:
        phase = "initialize" if case == "coerced_boolean" else "store_read"
        text = p.outputs[key + phase]["output"]
        text = text.replace('true', '1' if case == "coerced_boolean" else 'false')
        if case == "overwrite":
            text = text.replace(p.markers[a], p.markers[b])
        p.outputs[key + phase]["output"] = text
    elif case in {"missing_control", "unrelated_error", "foreign_completion", "foreign_cancel"}:
        phase = "missing_read" if case == "missing_control" else (
            "foreign_cancel" if case == "foreign_cancel" else "foreign_read")
        p.outputs[key + phase]["output"] = "Unknown unrelated error" if case == "unrelated_error" else ""
    elif case == "own_cancelled":
        p.outputs[key + "own_wait"]["output"] = "Script terminated"
    elif case == "input_leak":
        p.requests[0]["body"]["leak"] = p.markers[b]
    elif case == "late_attempt":
        p.observed_ms[key + "foreign_cancel"] = 2001
    elif case == "missing_timestamp":
        del p.observed_ms[key + "foreign_read"]
    assert not all(p.report()["checks"].values())


def test_observation_binds_real_actor_and_deduplicates(module):
    p = module.StateCanaries()
    agent = module.ACTORS[1]
    call = p.call(agent, "start", "operation", code=p.cell_code())
    body = {"input": [{"type": "custom_tool_call_output", "call_id": call["call_id"],
        "output": [{"type": "input_text", "text": "Script running with cell ID cell-1"}]}]}
    p.observe(agent, body)
    p.observe(agent, copy.deepcopy(body))
    assert p.cells == {agent: "cell-1"} and p.ready[agent].is_set()
    with pytest.raises(Fault, match="STATE_OUTPUT_WRONG_ACTOR"):
        p.observe(module.ACTORS[0], body)
    body["input"][0]["output"][0]["text"] += "changed"
    with pytest.raises(Fault, match="STATE_OUTPUT_CHANGED"):
        p.observe(agent, body)


def test_request_plan_uses_observed_handles_and_clean_helper(module):
    p = fixture(module)
    for actor in module.ACTORS:
        p.ready[actor].set()
    root, child = module.ACTORS
    spawn = p.next(root, 2, "spawn")[0]
    assert json.loads(spawn["arguments"])["fork_turns"] == "none"
    calls = p.next(root, 4, "root-cross")
    assert [json.loads(c["arguments"]).get("cell_id") for c in calls[:3]] == [
        p.cells[child], p.cells[child], module.MISSING_CELL]
    assert json.loads(calls[1]["arguments"])["terminate"] is True
    assert p.markers[child] not in calls[-1]["input"]
    with pytest.raises(Fault, match="STATE_UNEXPECTED_REQUEST"):
        p.next(root, 8, "excess")


def test_uncertain_fixture_closure_is_reported_without_retry(module):
    from native_mcp_identity_probe import close_fixture_budget
    class Runtime:
        calls = 0
        def close_dispatch_budget(self, job, seal):
            self.calls += 1
            raise Fault("METERING_UNKNOWN")
        def status(self, job):
            return {"state": "UNSETTLED"}
    class Plan:
        job_id = "root"
    runtime = Runtime()
    assert close_fixture_budget(runtime, Plan(), None, "sealed") == {
        "state": "UNSETTLED", "closure_error": "METERING_UNKNOWN"}
    assert runtime.calls == 1


@pytest.mark.parametrize("limit", [0, 13, True, 1.5, None, -1])
def test_helper_exposure_must_be_finite_and_inside_parent(module, tmp_path, limit):
    from native_dispatch_probe import LocalProvider
    with pytest.raises(Fault, match="HELPER_REQUEST_LIMIT"):
        LocalProvider(tmp_path / "unopened.sqlite", tmp_path / "objects", "identity",
                      max_requests=12, helper_requests=limit)
