"""Root-only native control fixture; scripted provider, no ablation claim."""

import json
import re

from mcbench.storage import canonical, require
from mcbench.native_cell_lifecycle import _status

ROOT_CODE = '''text({initial_private_state:load("no-helper-private")??null});
store("no-helper-private","permitted root state");
text({retained_private_state:load("no-helper-private")});
text({helper_tools:ALL_TOOLS.filter(t=>/spawn_agent|followup_task|interrupt_agent|send_message|wait_agent|list_agents/.test(t.name)).map(t=>t.name)});
'''


class NoSelfPlayProbe:
    def __init__(self):
        self.calls, self.returns, self.seen = {}, {}, {}

    def observe(self, actor, body):
        require(actor == "/root" and isinstance(body.get("input"), list), "NO_SELF_PLAY_ACTOR")
        for item in body["input"]:
            if item.get("type") not in {"function_call_output", "custom_tool_call_output"}:
                continue
            key = item.get("call_id")
            if key not in self.calls:
                continue
            value = item.get("output")
            require(key not in self.seen or canonical(self.seen[key]) == canonical(value),
                    "NO_SELF_PLAY_RETURN_CHANGED")
            expected = self.calls[key]
            require(item["type"] == expected["type"] + "_output", "NO_SELF_PLAY_RETURN_SCOPE")
            echoed = [i for i in body["input"] if i.get("call_id") == key and i.get("type") == expected["type"]]
            require(len(echoed) == 1 and all(echoed[0].get(k) == v for k, v in expected.items()
                    if k != "id"), "NO_SELF_PLAY_CALL_CHANGED")
            self.seen[key] = value
            self.returns[key] = value

    def next(self, step, operation):
        require(step in {1, 2, 3}, "NO_SELF_PLAY_STEP")
        key = "no-helper-" + operation
        require(key not in self.calls, "NO_SELF_PLAY_REPLAY")
        item = {"id": "tool-" + key, "call_id": key}
        if step in {1, 2}:
            item |= {"namespace": "collaboration", "name": "spawn_agent"}
            args = json.dumps({"task_name": "forbidden_child", "fork_turns": "none",
                               "message": "This control disables helpers; do not execute."})
            item |= ({"type": "function_call", "arguments": args} if step == 1 else
                     {"type": "custom_tool_call", "input": args})
        else:
            item |= {"type": "custom_tool_call", "namespace": "functions", "name": "exec", "input": ROOT_CODE}
        self.calls[key] = item
        return item

    def report(self, db, plan, provider):
        refused = [key for key, call in self.calls.items() if call["namespace"] == "collaboration"]
        # Native unknown-tool refusals, not arbitrary text containing "error".
        def missing(key):
            value = self.returns.get(key)
            label = "unsupported call: " if self.calls[key]["type"] == "function_call" else "unsupported custom tool call: "
            return value == label + "collaborationspawn_agent" or isinstance(value, str) and "spawn_agent" in value and bool(re.fullmatch(
                r"(?:Error: )?(?:Unknown tool[^\n]*|Unrecognized function name[^\n]*|Tool [^\n]* not found[^\n]*)", value))
        root = [self.returns.get(key) for key, call in self.calls.items() if call["namespace"] == "functions"]
        def values(value):
            if isinstance(value, list):
                for item in value:
                    yield from values(item)
            elif isinstance(value, dict):
                yield value
                for item in value.values():
                    yield from values(item)
            elif isinstance(value, str):
                for line in value.splitlines():
                    try:
                        yield json.loads(line)
                    except ValueError:
                        pass
        output = list(values(root))
        participants = db.connection.execute("SELECT depth FROM native_participants WHERE job=?", (plan.job_id,)).fetchall()
        return {"policy": "native-no-self-play-control/1", "production_qualified": False,
                "calls": self.calls, "returns": self.returns, "checks": {
            "both_spawn_wire_types_refused": len(refused) == 2 and all(missing(key) for key in refused),
            "root_native_exec_completed": len(root) == 1 and isinstance(root[0], list) and _status(root[0])[0] == "completed",
            "root_private_state_fresh_and_permitted": {"initial_private_state": None} in output and
                {"retained_private_state": "permitted root state"} in output,
            "no_deferred_helper_tools": {"helper_tools": []} in output,
            "zero_native_helper_participants": len(participants) == 1 and participants[0][0] == 0,
            "zero_helper_reservations": db.connection.execute("SELECT count(*) FROM operations WHERE kind='helper'").fetchone()[0] == 0,
            "only_root_provider_requests": len(provider.requests) == 5 and not provider.errors and
                all(i["agent"] == "/root" for i in provider.identities),
            "zero_helper_capability": plan.helper_limit == 0 and plan.helper_skill_activation_ref is None and
                plan.config_overrides["features.multi_agent_v2"] is False and plan.config_overrides.get("agents.enabled") is False,
        }}
