"""Selected-profile state fixture with private notification controls.

Uses the existing state/cell ownership protocol. Adds notification publication
without sharing either private marker in helper instructions or final replies.
Native output routing must be independently reviewed before qualification.
"""

import json

from mcbench.storage import require
from native_state_canaries import ACTORS, StateCanaries, records


def inspect_state_records(probe):
    """Reject contradictory/duplicate positive markers within one native output."""
    checks = {}
    for actor in ACTORS:
        own = probe.markers[actor]
        expected = {
            "initialize": [{"probe": "initial_state", "empty": True, "foreign": True},
                           {"probe": "own_initial", "value": own}],
            "store_read": [{"probe": "own_later", "value": own, "foreign": True}],
            "own_wait": [{"probe": "own_completion", "value": own}],
        }
        valid = True
        for phase, values in expected.items():
            keys = [key for key, call in probe.calls.items() if call == {"agent": actor, "phase": phase}]
            observed = records(probe.outputs.get(keys[0], {}).get("output")) if len(keys) == 1 else []
            for value in values:
                matches = [v for v in observed if v.get("probe") == value["probe"]]
                # canonical JSON distinguishes booleans from integer values.
                valid &= len(matches) == 1 and json.dumps(matches[0], sort_keys=True) == json.dumps(value, sort_keys=True)
            if phase == "own_wait":
                ends = [v for v in observed if v.get("probe") == "cell_end"]
                valid &= len(ends) == 1 and set(ends[0]) == {"probe", "at_ms"} and type(
                    ends[0]["at_ms"]) is int and ends[0]["at_ms"] > 0
        checks[("root_" if actor == ACTORS[0] else "helper_") + "state_records_exact"] = bool(valid)
    return checks


class SelectedStateCanaries(StateCanaries):
    def __init__(self):
        super().__init__()
        self.notifications = {}
        self.notification_requests = []

    def start(self, agent, operation, code):
        code += '\nnotify(' + json.dumps({"probe": "state_notification", "value": self.markers[agent]}) + ');'
        code += '\ntext({probe:"state_notification_return",result:"returned"});'
        return super().start(agent, operation, code)

    def observe(self, agent, body):
        self.other(agent)
        filtered = []
        # notify() is an additional string output under the existing call ID.
        # Separate only its exact owned notification shape, retaining the strict
        # original output conflict check for every ordinary result.
        with self.lock:
            self.notification_requests.append({"agent": agent, "body": body})
            for item in body.get("input", []):
                output = item.get("output")
                try:
                    value = json.loads(output) if isinstance(output, str) else None
                except ValueError:
                    value = None
                if not isinstance(value, dict) or value.get("probe") != "state_notification":
                    filtered.append(item)
                    continue
                call = self.calls.get(item.get("call_id"))
                require(item.get("type") == "custom_tool_call_output" and call is not None
                        and call == {"agent": agent, "phase": "initialize"}
                        and value == {"probe": "state_notification", "value": self.markers[agent]},
                        "STATE_NOTIFICATION_INVALID")
                key = item["call_id"]
                require(key not in self.notifications or self.notifications[key] == item,
                        "STATE_NOTIFICATION_CHANGED")
                self.notifications[key] = item
        super().observe(agent, body | {"input": filtered})

    def report(self):
        result = super().report()
        result["checks"].update(inspect_state_records(self))
        result["checks"]["notification_output_independently_reviewed"] = False
        result["checks"]["notification_exact_owned_outputs"] = len(self.notifications) == 2 and {
            self.calls[key]["agent"] for key in self.notifications} == set(ACTORS)
        for agent in ACTORS:
            prefix = "root_" if agent == ACTORS[0] else "helper_"
            initial = [key for key, call in self.calls.items()
                       if call == {"agent": agent, "phase": "initialize"}]
            result["checks"][prefix + "notification_return"] = len(initial) == 1 and sum(
                value == {"probe": "state_notification_return", "result": "returned"}
                for value in records(self.outputs.get(initial[0], {}).get("output"))) == 1
            result["checks"][prefix + "notification_peer_absent"] = all(
                self.markers[self.other(agent)] not in json.dumps(row["body"])
                for row in self.notification_requests if row["agent"] == agent)
        result["notification"] = {"status": "not_run", "reason": "independent captured-output review required"}
        result["notification_outputs"] = self.notifications
        return result
