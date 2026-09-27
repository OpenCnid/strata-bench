"""Exact activated JavaScript through native exec; no host eval or new tool.

Fixed-provider conformance only. A script must first arrive through an actual
artifact-read return. Copy its exact bytes into the existing restricted native
exec call; do not evaluate source in the operator process. Native completion,
broker effects and whole-runtime qualification remain separate evidence.
"""

import hashlib
import json
import re

from mcbench.native_cell_lifecycle import _status
from mcbench.storage import canonical, require, safe_relative

ACTORS = ("/root", "/root/identity_child")
POLICY = "native-active-javascript-exec/1"


def artifact_returns(value, depth=0):
    """Decode returned native content only; never provider call arguments."""
    require(depth <= 12, "SCRIPT_RETURN_DEPTH")
    if isinstance(value, dict):
        if set(value) == {"path", "ref", "text"}:
            yield value
        else:
            for child in value.values():
                yield from artifact_returns(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_returns(child, depth + 1)
    elif isinstance(value, str):
        for line in [value, *value.splitlines()]:
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if parsed != value:
                yield from artifact_returns(parsed, depth + 1)


class ActiveScriptProbe:
    def __init__(self, skill_set, path, source):
        relative = safe_relative(path)
        require(path.isascii() and len(path) <= 256 and len(relative.parts) >= 4
                and relative.parts[0] == "active" and relative.parts[2] == "scripts"
                and relative.suffix == ".js", "SCRIPT_PATH")
        name = relative.parts[1]
        require(name in skill_set["skills"], "SCRIPT_NOT_ACTIVE")
        active = skill_set["skills"][name]
        require(active["revision"]["status"] == "active" and active["revision"]["activated_at"],
                "SCRIPT_NOT_ACTIVE")
        file = "/".join(relative.parts[2:])
        require(file in active["files"] and isinstance(source, str)
                and 0 < len(source.encode("utf-8")) <= 256 * 1024, "SCRIPT_SOURCE")
        self.ref = "cas:sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
        require(self.ref == active["files"][file], "SCRIPT_SOURCE_CHANGED")
        self.path, self.source = path, source
        self.revision = active["revision"]["revision_id"]
        self.calls, self.reads, self.outputs = {}, {}, {}
        self.read_calls = {}
        self.seen = {}

    def read_call(self):
        return "artifact_read", {"path": self.path}

    def expect_read(self, actor, call_id):
        require(actor in ACTORS and actor not in self.read_calls and isinstance(call_id, str)
                and 0 < len(call_id) <= 256, "SCRIPT_READ_SCOPE")
        self.read_calls[actor] = call_id

    def observe(self, actor, body):
        require(actor in ACTORS and isinstance(body.get("input"), list)
                and all(isinstance(i, dict) for i in body["input"]), "SCRIPT_CALLER")
        require(len(canonical(body)) <= 1024 * 1024, "SCRIPT_CAPTURE_SIZE")
        for item in body["input"]:
            if item.get("type") not in {"custom_tool_call_output", "function_call_output"}:
                continue
            key = item.get("call_id")
            require(isinstance(key, str) and 0 < len(key) <= 256, "SCRIPT_RETURN_SCOPE")
            identity = (actor, key)
            value = item.get("output")
            require(identity not in self.seen or canonical(self.seen[identity]) == canonical(value),
                    "SCRIPT_RETURN_CHANGED")
            self.seen[identity] = value
            if key in self.calls:
                require(self.calls[key]["actor"] == actor and item["type"] == "custom_tool_call_output",
                        "SCRIPT_RETURN_SCOPE")
                echoed = [i for i in body["input"] if i.get("type") == "custom_tool_call"
                          and i.get("call_id") == key]
                require(len(echoed) == 1 and echoed[0].get("namespace") == "functions"
                        and echoed[0].get("name") == "exec" and echoed[0].get("input") == self.source,
                        "SCRIPT_EXECUTION_CHANGED")
                # Scalar notify() text cannot establish native completion.
                require(isinstance(value, list), "SCRIPT_COMPLETION_FRAME")
                self.outputs[key] = value
            if key != self.read_calls.get(actor):
                continue
            require(item["type"] == "custom_tool_call_output", "SCRIPT_READ_SCOPE")
            for returned in artifact_returns(value):
                if returned.get("path") == self.path:
                    require(returned == {"path": self.path, "ref": self.ref, "text": self.source},
                            "SCRIPT_SOURCE_CHANGED")
                    self.reads.setdefault(actor, key)

    def issue(self, actor, operation):
        require(actor in ACTORS and actor in self.reads, "SCRIPT_READ_REQUIRED")
        require(isinstance(operation, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", operation),
                "SCRIPT_OPERATION")
        require(not any(call["actor"] == actor for call in self.calls.values()), "SCRIPT_REPLAY")
        key = "active-script-" + operation
        require(key not in self.calls, "SCRIPT_REPLAY")
        self.calls[key] = {"actor": actor, "operation": operation, "read_call_id": self.reads[actor]}
        return {"id": "tool-" + key, "call_id": key, "namespace": "functions", "name": "exec",
                "type": "custom_tool_call", "input": self.source}

    def report(self):
        completed = {}
        for key, call in self.calls.items():
            value = self.outputs.get(key)
            completed[call["actor"]] = value is not None and _status(value)[0] == "completed"
        return {"policy": POLICY, "path": self.path, "source_ref": self.ref, "revision_id": self.revision,
                "calls": self.calls, "outputs": self.outputs,
                "checks": {"both_actors_read_exact_active_script": set(self.reads) == set(ACTORS),
                           "both_actors_issued_exact_source": len(self.calls) == 2,
                           "both_native_calls_completed": completed == dict.fromkeys(ACTORS, True)},
                "operator_evaluated_script": False, "broker_effects_qualified": False,
                "runtime_qualified": False}
