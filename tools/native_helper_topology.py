"""Bounded synthetic native helper overlap; no production admission authority."""

import json
import threading

from mcbench.storage import canonical, require

MODES = {"concurrency_limit", "concurrency_pair", "grandchild"}
ROOT = "/root"
FIRST = ROOT + "/synthetic_child"
SECOND = ROOT + "/synthetic_second"
RESULT = "STRATA_TOPOLOGY_RESULT_61a87d90"
GRANDCHILD = FIRST + "/synthetic_grandchild"
CHILD_CONTEXT = "STRATA_CHILD_CONTEXT_c0e62899"
DENIAL = "collab spawn failed: agent thread limit reached"


def decode_output(output):
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        # Native tool errors may be text. Preserve the exact observed value.
        return output


class Topology:
    def __init__(self, mode):
        require(mode in MODES, "TOPOLOGY_MODE")
        self.mode, self.root_step = mode, 0
        self.started = {name: threading.Event() for name in (FIRST, SECOND)}
        self.release = threading.Event()
        self.calls = {name: 0 for name in (FIRST, SECOND)}
        self.tool_outputs = []
        self.seen_outputs = set()
        self.finished = False

    def before_request(self, agent):
        # Never hold the provider lock while waiting for another HTTP handler.
        if agent == ROOT and self.root_step == 1:
            require(self.started[FIRST].wait(5), "FIRST_CHILD_STREAM_NOT_STARTED")
        if agent == ROOT and self.root_step == 2 and self.mode == "concurrency_pair":
            require(self.started[SECOND].wait(5), "SECOND_CHILD_STREAM_NOT_STARTED")

    def choose(self, body, agent, native_tool_calls, parent_canary):
        require(agent in {ROOT, FIRST, SECOND}, "UNEXPECTED_NATIVE_AGENT")
        if agent != ROOT:
            self.calls[agent] += 1
            require(self.calls[agent] == 1 and parent_canary not in json.dumps(body),
                    "UNEXPECTED_CHILD_CONTEXT_OR_RETRY")
            return RESULT, None
        for item in body.get("input", []):
            call_id = item.get("call_id")
            if (item.get("type") == "function_call_output" and call_id in native_tool_calls
                    and call_id not in self.seen_outputs):
                self.seen_outputs.add(call_id)
                self.tool_outputs.append({"tool": native_tool_calls[call_id],
                                          "output": decode_output(item["output"])})
        step = self.root_step
        self.root_step += 1
        require(step < 10, "NATIVE_TOPOLOGY_STEP_LIMIT")
        if step in {0, 1}:
            name = "synthetic_child" if step == 0 else "synthetic_second"
            return "", ("spawn_agent", {"task_name": name, "fork_turns": "none",
                "message": "Return the fixed synthetic result. Do not call tools or access files."})
        if step == 2:
            return "", ("list_agents", {})
        if step == 3:
            # The prior list result records native states while streams are held.
            # Always release even if native admission violated the requested cap.
            self.release.set()
            return "", ("wait_agent", {"timeout_ms": 10000})
        if step % 2 == 0:
            return "", ("list_agents", {})
        listing = self.tool_outputs[-1]
        require(listing["tool"] == "list_agents" and isinstance(listing["output"], dict),
                "NATIVE_AGENT_LIST_MISSING")
        children = [v for v in listing["output"]["agents"] if v["agent_name"] != ROOT]
        if children and all(v["agent_status"] == {"completed": RESULT} for v in children):
            self.finished = True
            return "Synthetic helper overlap complete.", None
        return "", ("wait_agent", {"timeout_ms": 10000})

    def hold_stream(self, agent):
        self.started[agent].set()
        require(self.release.wait(12), "TOPOLOGY_STREAM_RELEASE_TIMEOUT")

    def validate(self, result):
        outputs = self.tool_outputs
        require(self.finished and len(outputs) >= 5 and
                [v["tool"] for v in outputs[:3]] == ["spawn_agent", "spawn_agent", "list_agents"] and
                outputs[0]["output"] == {"task_name": FIRST}, "NATIVE_TOPOLOGY_FLOW")
        expected_children = [FIRST, SECOND] if self.mode == "concurrency_pair" else [FIRST]
        require(self.calls == {FIRST: 1, SECOND: int(self.mode == "concurrency_pair")},
                "NATIVE_HELPER_LIMIT_NOT_ENFORCED")
        if self.mode == "concurrency_pair":
            require(outputs[1]["output"] == {"task_name": SECOND}, "NATIVE_SECOND_HELPER_NOT_ADMITTED")
        else:
            require(outputs[1]["output"] == DENIAL, "NATIVE_HELPER_DENIAL_MISMATCH")
        for output, complete in ((outputs[2]["output"], False), (outputs[-1]["output"], True)):
            expected = [{"agent_name": ROOT, "agent_status": "running"}] + [
                {"agent_name": name, "agent_status": {"completed": RESULT} if complete else "running"}
                for name in expected_children]
            require(isinstance(output, dict) and set(output) == {"agents"} and
                    sorted(map(canonical, output["agents"])) == sorted(map(canonical, expected)),
                    "NATIVE_OVERLAP_STATE_MISMATCH")
        for index, output in enumerate(outputs[3:], 3):
            require(output["tool"] == ("wait_agent" if index % 2 else "list_agents"),
                    "NATIVE_TOPOLOGY_FLOW")
            if index % 2:
                require(canonical(output["output"]) == canonical({"message": "Wait completed.",
                                                                 "timed_out": False}),
                        "NATIVE_TOPOLOGY_WAIT_FAILED")
        lineage = result["lineage"]
        roots = [v for v in lineage if v["agent_name"] == ROOT]
        require(len(roots) == self.root_step and
                {v["root_turn_id"] for v in lineage} == {roots[0]["turn_id"]} and
                len({v["thread_id"] for v in lineage}) == 1 + len(expected_children),
                "NATIVE_TOPOLOGY_LINEAGE_MISMATCH")
        require(len(result["requests"]) == len(lineage) == self.root_step + len(expected_children) and
                all(a["state"] == "SETTLED" for a in result["attempts"]) and
                len(result["attempts"]) == len(lineage) == result["upstream_request_count"],
                "NATIVE_TOPOLOGY_ACCOUNTING_MISMATCH")


class NestedTopology(Topology):
    """One root, child and grandchild; observed metadata is not trusted lineage."""

    def __init__(self):
        super().__init__("grandchild")
        self.calls = {name: 0 for name in (ROOT, FIRST, GRANDCHILD)}
        self.deliveries = set()
        self.missing_tools = []

    def before_request(self, agent):
        pass

    def hold_stream(self, agent):
        pass

    def choose(self, body, agent, native_tool_calls, parent_canary):
        require(agent in self.calls, "UNEXPECTED_NATIVE_AGENT")
        step = self.calls[agent]
        self.calls[agent] += 1
        require(step < (1 if agent == GRANDCHILD else 3), "UNEXPECTED_NESTED_RETRY")
        serialized = json.dumps(body)
        if agent != ROOT:
            require(parent_canary not in serialized, "NESTED_PARENT_CONTEXT_LEAK")
        if agent == GRANDCHILD:
            require(CHILD_CONTEXT not in serialized, "NESTED_CHILD_CONTEXT_LEAK")
            return RESULT, None
        if agent == FIRST:
            require(CHILD_CONTEXT in serialized, "CHILD_CONTEXT_MISSING")
            if step == 0:
                catalogs = [n for item in body.get("input", []) if item.get("type") == "additional_tools"
                            for n in item["tools"] if n.get("name") == "collaboration"]
                names = {t.get("name") for n in catalogs for t in n.get("tools", [])}
                self.missing_tools = sorted({"spawn_agent", "wait_agent"} - names)
                if self.missing_tools:
                    # Complete authoritative usage for this capability failure.
                    # The validation stays failed; do not emit unavailable calls.
                    return RESULT, None
        for item in body.get("input", []):
            call_id = item.get("call_id")
            if (item.get("type") == "function_call_output" and call_id in native_tool_calls and
                    call_id not in self.seen_outputs):
                self.seen_outputs.add(call_id)
                self.tool_outputs.append({"agent": agent, "tool": native_tool_calls[call_id],
                                          "output": decode_output(item["output"])})
        if step == 0:
            return "", ("spawn_agent", {"task_name": "synthetic_child" if agent == ROOT else "synthetic_grandchild",
                "fork_turns": "none", "message": "Perform the fixed synthetic nested task. " +
                    (CHILD_CONTEXT if agent == ROOT else "Return the fixed result.") +
                    " Do not execute commands or access files."})
        if step == 1:
            return "", ("wait_agent", {"timeout_ms": 10000})
        source = FIRST if agent == ROOT else GRANDCHILD
        delivered = any(item.get("type") == "agent_message" and item.get("author") == source and
            item.get("recipient") == agent and any(part.get("text", "").endswith("Payload:\n" + RESULT) and
                part["text"].startswith("Message Type: FINAL_ANSWER\n") for part in item.get("content", []))
            for item in body.get("input", []))
        require(delivered, "NESTED_RESULT_NOT_DELIVERED")
        self.deliveries.add((source, agent))
        self.finished = agent == ROOT
        return RESULT, None

    def validate(self, result):
        require(not self.missing_tools, "NATIVE_NESTED_TOOLS_MISSING")
        require(self.finished and self.calls == {ROOT: 3, FIRST: 3, GRANDCHILD: 1} and
                self.deliveries == {(FIRST, ROOT), (GRANDCHILD, FIRST)}, "NATIVE_NESTED_FLOW")
        for agent, child in ((ROOT, FIRST), (FIRST, GRANDCHILD)):
            outputs = [v for v in self.tool_outputs if v["agent"] == agent]
            expected = [{"agent": agent, "tool": "spawn_agent", "output": {"task_name": child}},
                        {"agent": agent, "tool": "wait_agent",
                         "output": {"message": "Wait completed.", "timed_out": False}}]
            require(canonical(outputs) == canonical(expected), "NATIVE_NESTED_TOOL_RESULT")
        lineage = result["lineage"]
        require(len(lineage) == 7 and {v["agent_name"] for v in lineage} == set(self.calls) and
                len({v["root_turn_id"] for v in lineage}) == 1 and
                len({v["thread_id"] for v in lineage}) == 3 and
                len(result["requests"]) == len(result["attempts"]) == result["upstream_request_count"] == 7 and
                all(a["state"] == "SETTLED" for a in result["attempts"]), "NATIVE_NESTED_ACCOUNTING")
