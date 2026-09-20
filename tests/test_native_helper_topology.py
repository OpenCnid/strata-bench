"""Negative verdict checks for synthetic native overlap and nested capability probes."""

import importlib
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def topology(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_helper_topology")


def overlap(topology, mode):
    probe = topology.Topology(mode)
    root, first, second = topology.ROOT, topology.FIRST, topology.SECOND
    children = [first, second] if mode == "concurrency_pair" else [first]
    def agents(complete):
        return {"agents": [{"agent_name": root, "agent_status": "running"}] + [
            {"agent_name": name, "agent_status": {"completed": topology.RESULT} if complete else "running"}
            for name in children]}
    probe.calls = {first: 1, second: int(len(children) == 2)}
    probe.finished, probe.root_step = True, 6
    probe.tool_outputs = [{"tool": "spawn_agent", "output": {"task_name": first}},
        {"tool": "spawn_agent", "output": {"task_name": second} if len(children) == 2 else topology.DENIAL},
        {"tool": "list_agents", "output": agents(False)},
        {"tool": "wait_agent", "output": {"message": "Wait completed.", "timed_out": False}},
        {"tool": "list_agents", "output": agents(True)}]
    lineage = [{"agent_name": name, "thread_id": "thread-" + name, "root_turn_id": "root-turn",
                "turn_id": "root-turn" if name == root else "turn-" + name}
               for name in [root] * 6 + children]
    result = {"lineage": lineage, "requests": [{} for _ in lineage],
              "attempts": [{"state": "SETTLED"} for _ in lineage], "upstream_request_count": len(lineage)}
    return probe, result


@pytest.mark.parametrize("mode", ["concurrency_limit", "concurrency_pair"])
def test_observed_overlap_and_exact_native_denial(topology, mode):
    probe, result = overlap(topology, mode)
    probe.validate(result)
    probe.tool_outputs[2]["output"]["agents"].reverse()
    probe.validate(result)


@pytest.mark.parametrize("case", ["denial", "extra_request", "no_overlap", "duplicate_agent", "wrong_result",
                                  "timeout", "coerced_timeout", "unknown_usage", "missing_upstream", "lineage"])
def test_overlap_false_success_rejected(topology, case):
    probe, result = overlap(topology, "concurrency_limit")
    if case == "denial":
        probe.tool_outputs[1]["output"] = "another error"
    elif case == "extra_request":
        probe.calls[topology.SECOND] = 1
    elif case in {"no_overlap", "wrong_result"}:
        index = 2 if case == "no_overlap" else 4
        probe.tool_outputs[index]["output"]["agents"][1]["agent_status"] = "interrupted"
    elif case == "duplicate_agent":
        probe.tool_outputs[2]["output"]["agents"][1] = probe.tool_outputs[2]["output"]["agents"][0]
    elif case in {"timeout", "coerced_timeout"}:
        probe.tool_outputs[3]["output"]["timed_out"] = True if case == "timeout" else 0
    elif case == "unknown_usage":
        result["attempts"][0]["state"] = "UNSETTLED"
    elif case == "missing_upstream":
        result["upstream_request_count"] -= 1
    else:
        result["lineage"][-1]["root_turn_id"] = "other-root"
    with pytest.raises(Fault):
        probe.validate(result)


def test_error_text_is_preserved_without_inventing_a_json_ack(topology):
    assert topology.decode_output(topology.DENIAL) == topology.DENIAL
    assert topology.decode_output("") is None
    assert topology.decode_output('{"task_name":"/root/child"}') == {"task_name": "/root/child"}


def test_nested_missing_native_tools_never_emits_unavailable_call(topology):
    probe = topology.NestedTopology()
    body = {"input": [{"type": "additional_tools", "tools": [{"name": "functions", "tools": []}]},
                      {"type": "message", "content": [{"text": topology.CHILD_CONTEXT}]}]}
    text, call = probe.choose(body, topology.FIRST, {}, "parent-secret")
    assert text == topology.RESULT and call is None
    assert probe.missing_tools == ["spawn_agent", "wait_agent"]
    with pytest.raises(Fault, match="NATIVE_NESTED_TOOLS_MISSING"):
        probe.validate({})


@pytest.mark.parametrize("agent,canary", [("child", "parent"), ("grandchild", "parent"), ("grandchild", "child")])
def test_nested_ancestor_context_rejected(topology, agent, canary):
    probe = topology.NestedTopology()
    body = {"input": [{"type": "message", "content": [{"text":
        topology.CHILD_CONTEXT if canary == "child" else "parent-secret"}]}]}
    with pytest.raises(Fault, match="CONTEXT_LEAK"):
        probe.choose(body, topology.FIRST if agent == "child" else topology.GRANDCHILD, {}, "parent-secret")
