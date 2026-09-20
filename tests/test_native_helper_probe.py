"""Synthetic negatives for the explicit operator-only native fixture's verdicts."""

import importlib
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def probe(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_helper_probe")


def lifecycle(probe):
    def agents(result):
        return {"agents": [{"agent_name": "/root", "agent_status": "running"},
            {"agent_name": "/root/synthetic_child", "agent_status": {"completed": result}}]}
    values = [("spawn_agent", {"task_name": "/root/synthetic_child"}),
              ("wait_agent", {"message": "Wait completed.", "timed_out": False}),
              ("send_message", None), ("list_agents", agents(probe.CHILD_RESULT)),
              ("followup_task", None),
              ("wait_agent", {"message": "Wait completed.", "timed_out": False}),
              ("list_agents", agents(probe.FOLLOWUP_RESULT)),
              ("interrupt_agent", {"previous_status": {"completed": probe.FOLLOWUP_RESULT}}),
              ("list_agents", agents(probe.FOLLOWUP_RESULT))]
    return [{"tool": name, "output": output} for name, output in values]


def test_exact_native_result_shapes_allow_agent_listing_order_only(probe):
    values = lifecycle(probe)
    probe.validate_lifecycle_outputs(values)
    for i in (3, 6, 8):
        values[i]["output"]["agents"].reverse()
    probe.validate_lifecycle_outputs(values)


@pytest.mark.parametrize("case", ["wrong_child", "timeout", "coerced_timeout", "message_ack", "followup_ack",
                                 "wrong_result", "duplicate_agent", "extra_agent", "wrong_previous", "order"])
def test_idle_lifecycle_false_successes_rejected(probe, case):
    values = lifecycle(probe)
    if case == "wrong_child":
        values[0]["output"]["task_name"] = "/root/other"
    elif case in {"timeout", "coerced_timeout"}:
        values[1]["output"]["timed_out"] = True if case == "timeout" else 0
    elif case == "message_ack":
        values[2]["output"] = {}
    elif case == "followup_ack":
        values[4]["output"] = {"error": "missing child"}
    elif case == "wrong_result":
        values[6]["output"]["agents"][1]["agent_status"] = {"completed": "wrong"}
    elif case == "duplicate_agent":
        values[3]["output"]["agents"][1] = values[3]["output"]["agents"][0]
    elif case == "extra_agent":
        values[3]["output"]["agents"].append({"agent_name": "/root/other", "agent_status": "running"})
    elif case == "wrong_previous":
        values[7]["output"]["previous_status"] = "running"
    else:
        values[1], values[2] = values[2], values[1]
    with pytest.raises(Fault):
        probe.validate_lifecycle_outputs(values)


def active():
    return [{"tool": "spawn_agent", "output": {"task_name": "/root/synthetic_child"}},
            {"tool": "interrupt_agent", "output": {"previous_status": "running"}},
            {"tool": "list_agents", "output": {"agents": [
                {"agent_name": "/root", "agent_status": "running"},
                {"agent_name": "/root/synthetic_child", "agent_status": "interrupted"}]}}]


def test_active_interruption_requires_running_then_interrupted(probe):
    probe.validate_interruption_outputs(active())
    for previous, current in [("completed", "interrupted"), ("running", "completed"), ("running", "running")]:
        values = active()
        values[1]["output"]["previous_status"] = previous
        values[2]["output"]["agents"][1]["agent_status"] = current
        with pytest.raises(Fault):
            probe.validate_interruption_outputs(values)


@pytest.mark.parametrize("limit", [0, 33, True, 1.0, None])
def test_fixture_request_limits_reject_unbounded_or_coerced_input(probe, tmp_path, limit):
    with pytest.raises(Fault, match="REQUEST_LIMIT"):
        probe.LocalProvider(tmp_path / "never-opened.sqlite", tmp_path / "objects", "success", max_requests=limit)
