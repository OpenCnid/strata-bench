"""Owned code-mode state/cell probes in the pinned native loop, not qualification.

Only synthetic markers and already-yielded cell IDs cross the fixture provider.
Foreign waits deliberately bypass discovery; native caller metadata binds outputs.
"""

import json
import re
import threading
import time

from mcbench.storage import require

ACTORS = ("/root", "/root/identity_child")
KEY = "strata-state-collision"
MISSING_CELL = "strata-owned-absent-cell"


def output_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(v["text"] for v in value if isinstance(v, dict)
                         and v.get("type", "text") in {"text", "input_text"}
                         and isinstance(v.get("text"), str))
    return ""


def records(value):
    result = []
    for line in output_text(value).splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            result.append(item)
    return result


class StateCanaries:
    def __init__(self):
        self.markers = {a: "STRATA_OWN_STATE_" + ("ROOT" if a == ACTORS[0] else "HELPER")
                        for a in ACTORS}
        self.cells, self.calls, self.outputs, self.requests = {}, {}, {}, []
        self.observed_ms = {}
        self.ready = {a: threading.Event() for a in ACTORS}
        self.finished = set()
        self.lock = threading.Lock()

    @staticmethod
    def other(agent):
        require(agent in ACTORS, "STATE_ACTOR")
        return ACTORS[1] if agent == ACTORS[0] else ACTORS[0]

    def call(self, agent, phase, operation, *, code=None, name="wait", args=None,
             namespace="functions"):
        key = "state-" + phase + "-" + operation
        require(key not in self.calls, "STATE_CALL_DUPLICATE")
        self.calls[key] = {"agent": agent, "phase": phase}
        base = {"id": "tool-" + key, "call_id": key, "namespace": namespace, "name": name}
        if code is not None:
            return {**base, "type": "custom_tool_call", "name": "exec", "input": code}
        return {**base, "type": "function_call", "arguments": json.dumps(args)}

    def start(self, agent, operation, code):
        other = self.other(agent)
        code += '\ntext({probe:"initial_state",empty:load(' + json.dumps(KEY) + ')===undefined,'
        code += 'foreign:load(' + json.dumps(other) + ')===undefined});\n'
        code += 'store(' + json.dumps(KEY) + ',' + json.dumps(self.markers[agent]) + ');\n'
        code += 'store(' + json.dumps(agent) + ',' + json.dumps(self.markers[agent]) + ');\n'
        code += 'text({probe:"own_initial",value:load(' + json.dumps(KEY) + ')});\n'
        return self.call(agent, "initialize", operation, code=code)

    def reserve_root_handle(self, operation):
        # A completed no-op makes the later live handles distinguishable even
        # with participant-local counters. No foreign handle is guessed.
        return self.call(ACTORS[0], "reserve_handle", operation, code='text("Owned cell counter fixture.");')

    @staticmethod
    def cell_code():
        return ('await yield_control();\nawait new Promise(r=>setTimeout(r,25000));\n'
                'text({probe:"own_completion",value:load(' + json.dumps(KEY) + ')});\n'
                'text({probe:"cell_end",at_ms:Date.now()});')

    def observe(self, agent, body):
        self.other(agent)
        with self.lock:
            self.requests.append({"agent": agent, "body": body})
            for item in body.get("input", []):
                if item.get("type") not in {"custom_tool_call_output", "function_call_output"}:
                    continue
                key = item.get("call_id")
                if key not in self.calls:
                    continue
                require(self.calls[key]["agent"] == agent, "STATE_OUTPUT_WRONG_ACTOR")
                value = {"agent": agent, "output": item.get("output")}
                require(key not in self.outputs or self.outputs[key] == value, "STATE_OUTPUT_CHANGED")
                self.outputs[key] = value
                self.observed_ms.setdefault(key, time.time_ns() // 1000000)
                if self.calls[key]["phase"] == "start":
                    found = re.findall(r"Script running with cell ID ([A-Za-z0-9_-]+)",
                                       output_text(item.get("output")))
                    require(len(found) == 1, "STATE_CELL_NOT_YIELDED")
                    require(agent not in self.cells or self.cells[agent] == found[0], "STATE_CELL_CHANGED")
                    self.cells[agent] = found[0]
                    self.ready[agent].set()

    def next(self, agent, step, operation):
        other = self.other(agent)
        if step == 1:
            return [self.call(agent, "start", operation, code=self.cell_code())]
        if agent == ACTORS[0] and step == 2:
            return [self.call(agent, "spawn", operation, namespace="collaboration", name="spawn_agent",
                args={"task_name": "identity_child", "fork_turns": "none", "message":
                      "Exercise the fixed synthetic broker and code-mode state fixture only."})]
        if agent == ACTORS[0] and step == 3:
            return [self.call(agent, "synchronize", operation, namespace="collaboration",
                name="wait_agent", args={"timeout_ms": 10000})]
        offset = 3 if agent == ACTORS[0] else 1
        if step == 1 + offset:
            require(self.ready[other].is_set(), "STATE_PEER_CELL_NOT_READY")
            require(len(set(self.cells.values())) == 2, "STATE_CELL_IDS_COLLIDE")
            items = []
            for phase, cell, terminate in [("foreign_read", self.cells[other], False),
                    ("foreign_cancel", self.cells[other], True), ("missing_read", MISSING_CELL, False)]:
                items.append(self.call(agent, phase, operation, args={"cell_id": cell,
                    "yield_time_ms": 1, "max_tokens": 1000, "terminate": terminate}))
            code = 'text({probe:"own_later",value:load(' + json.dumps(KEY) + '),foreign:load('
            code += json.dumps(other) + ')===undefined});'
            items.append(self.call(agent, "store_read", operation, code=code))
            return items
        if step == 2 + offset:
            items = [self.call(agent, "own_wait", operation, args={"cell_id": self.cells[agent],
                "yield_time_ms": 30000, "max_tokens": 1000})]
            if agent == ACTORS[0]:
                items.append(self.call(agent, "join", operation, namespace="collaboration", name="wait_agent",
                    args={"timeout_ms": 30000}))
            return items
        require(step == 3 + offset, "STATE_UNEXPECTED_REQUEST")
        self.finished.add(agent)
        return [{"id": "message-" + operation, "type": "message", "role": "assistant",
            "status": "completed", "content": [{"type": "output_text",
            "text": "Synthetic state fixture finished.", "annotations": []}]}]

    def report(self):
        checks = {"state_distinct_native_cells": len(self.cells) == 2 and
            len(set(self.cells.values())) == 2, "state_both_finished": self.finished == set(ACTORS)}
        for agent in ACTORS:
            own, peer = self.markers[agent], self.markers[self.other(agent)]
            rows = {c["phase"]: self.outputs.get(key, {}) for key, c in self.calls.items()
                    if c["agent"] == agent}
            def get(phase):
                return rows.get(phase, {}).get("output")
            def has(phase, record):
                return any(json.dumps(record, sort_keys=True) == json.dumps(v, sort_keys=True)
                           for v in records(get(phase)))
            prefix = "root_" if agent == ACTORS[0] else "helper_"
            initial = "initialize"
            checks[prefix + "store_initially_empty"] = has(initial,
                {"probe": "initial_state", "empty": True, "foreign": True})
            checks[prefix + "store_own_roundtrip"] = has(initial,
                {"probe": "own_initial", "value": own}) and has("store_read",
                {"probe": "own_later", "value": own, "foreign": True})
            checks[prefix + "own_cell_survives_peer_cancel"] = has("own_wait",
                {"probe": "own_completion", "value": own}) and (
                    "Script completed" in output_text(get("own_wait")))
            # Unknown errors are not evidence of enforcement. Compare each native
            # foreign denial with the owned nonexistent-ID control, exact except ID.
            # The pinned host reports the same precise error for absent and
            # foreign handles. Ignore its measured wall-time display only.
            def denial(phase, cell):
                chunks = [line for line in output_text(get(phase)).splitlines() if line]
                return (chunks[:1] == ["Script failed"] and len(chunks) == 5 and
                        re.fullmatch(r"Wall time [0-9]+\.[0-9]+ seconds", chunks[1]) is not None and
                        chunks[2:] == ["Output:", "Script error:", "exec cell " + cell + " not found"])
            absent = denial("missing_read", MISSING_CELL)
            checks[prefix + "foreign_cell_read_denied"] = bool(absent) and (
                denial("foreign_read", self.cells.get(self.other(agent), "?")))
            checks[prefix + "foreign_cell_cancel_denied"] = bool(absent) and (
                denial("foreign_cancel", self.cells.get(self.other(agent), "?")))
            checks[prefix + "peer_marker_absent_from_inputs"] = all(peer not in json.dumps(r["body"])
                for r in self.requests if r["agent"] == agent)
            peer_ends = [v["at_ms"] for key, call in self.calls.items()
                if call["agent"] == self.other(agent) and call["phase"] == "own_wait"
                for v in records(self.outputs.get(key, {}).get("output"))
                if v.get("probe") == "cell_end" and type(v.get("at_ms")) is int]
            attempts = [self.observed_ms.get(key) for key, call in self.calls.items()
                if call["agent"] == agent and call["phase"] in {"foreign_read", "foreign_cancel"}]
            checks[prefix + "foreign_attempts_while_peer_pending"] = len(peer_ends) == 1 and (
                len(attempts) == 2 and all(type(t) is int and t < peer_ends[0] for t in attempts))
        return {"schema": "strata/NativeStateCanaries/1", "is_example": True,
            "production_qualified": False, "checks": checks, "cells": self.cells,
            "calls": self.calls, "outputs": self.outputs, "observed_ms": self.observed_ms}
