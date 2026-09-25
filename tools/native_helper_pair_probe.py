"""Two admitted native helpers with routed public messages; scripted, never N bodies."""

import json

from mcbench.storage import require
from native_state_canaries import output_text, records

ROOT = "/root"
HELPERS = (ROOT + "/identity_child", ROOT + "/identity_second")
ACTORS = (ROOT, *HELPERS)
OVERFLOW = ROOT + "/overflow"
PRIVATE = {actor: "STRATA_PAIR_PRIVATE_" + actor.rsplit("/", 1)[-1] for actor in ACTORS}
READY = {actor: "STRATA_PAIR_READY_" + actor.rsplit("/", 1)[-1] for actor in HELPERS}
RELEASE = {actor: "STRATA_PAIR_RELEASE_" + actor.rsplit("/", 1)[-1] for actor in HELPERS}
ADVICE = {actor: "STRATA_PAIR_ADVICE_" + actor.rsplit("/", 1)[-1] for actor in HELPERS}
DONE = {actor: "STRATA_PAIR_DONE_" + actor.rsplit("/", 1)[-1] for actor in HELPERS}


def private_path(actor):
    return ("notes/" if actor == ROOT else "results/") + actor.rsplit("/", 1)[-1] + "-private.md"


class HelperPairProbe:
    def __init__(self):
        self.calls, self.outputs, self.requests = {}, {}, []
        self.messages = set()
        self.finished = set()
        self.phases = dict.fromkeys(ACTORS, 0)
        self.waits = dict.fromkeys(ACTORS, 0)
        self.wait_phases = {}

    def call(self, actor, phase, operation, *, name=None, args=None, code=None):
        require(actor in ACTORS, "PAIR_ACTOR")
        key = "pair-" + phase + "-" + operation
        require(key not in self.calls, "PAIR_DUPLICATE_CALL")
        self.calls[key] = {"actor": actor, "phase": phase}
        base = {"id": "tool-" + key, "call_id": key}
        if code is not None:
            return {**base, "type": "custom_tool_call", "namespace": "functions", "name": "exec", "input": code}
        return {**base, "type": "function_call", "namespace": "collaboration", "name": name,
                "arguments": json.dumps(args)}

    def start(self, actor, operation, code):
        code += '\ntext({probe:"pair_private_write",result:await tools.mcp__strata_broker__artifact_write('
        code += json.dumps({"path": private_path(actor), "text": PRIVATE[actor], "expected_ref": None}) + ')});'
        return self.call(actor, "initialize", operation, code=code)

    def observe(self, actor, body):
        require(actor in ACTORS, "PAIR_ACTOR")
        self.requests.append({"actor": actor, "body": body})
        for item in body.get("input", []):
            key = item.get("call_id")
            if item.get("type") in {"function_call_output", "custom_tool_call_output"} and key in self.calls:
                require(self.calls[key]["actor"] == actor, "PAIR_WRONG_CALLER")
                value = item.get("output")
                require(key not in self.outputs or self.outputs[key] == value, "PAIR_CHANGED_OUTPUT")
                self.outputs[key] = value
            if item.get("type") == "agent_message" and item.get("recipient") == actor:
                author = item.get("author")
                if author not in ACTORS:
                    continue
                parts = item.get("content", [])
                for kind in ("MESSAGE", "FINAL_ANSWER"):
                    header = "Message Type: " + kind + "\nTask name: " + actor + "\nSender: " + author + "\nPayload:\n"
                    if len(parts) == 1 and parts[0].get("type") == "input_text" and isinstance(
                            parts[0].get("text"), str) and parts[0]["text"].startswith(header):
                        self.messages.add((author, actor, kind, parts[0]["text"][len(header):]))
                    elif len(parts) == 2 and parts[0] == {"type": "input_text", "text": header}:
                        # Native routes a provider message in a separate payload
                        # part. In this local scripted fixture its bytes are known;
                        # this is not a general ciphertext decoding capability.
                        field = "encrypted_content" if parts[1].get("type") == "encrypted_content" else "text"
                        if parts[1].get("type") in {"input_text", "encrypted_content"} and set(parts[1]) == {
                                "type", field} and isinstance(parts[1][field], str):
                            self.messages.add((author, actor, kind, parts[1][field]))

    def received(self, sender, recipient, marker, kind="MESSAGE"):
        return (sender, recipient, kind, marker) in self.messages

    def wait(self, actor, operation):
        require(actor in ACTORS, "PAIR_ACTOR")
        self.waits[actor] += 1
        key = actor + ":" + str(self.phases[actor])
        self.wait_phases[key] = self.wait_phases.get(key, 0) + 1
        # Root has two separate rendezvous: two ready messages, then two
        # final replies plus the refused overflow's notification. A global
        # four-wait cap incorrectly conflated those independent event sets.
        require(self.wait_phases[key] <= 3 and self.waits[actor] <= (6 if actor == ROOT else 3),
                "PAIR_DELIVERY_BOUND")
        return self.call(actor, "wait", operation, name="wait_agent", args={"timeout_ms": 10000})

    def read_code(self, actor):
        calls = [{"probe": "own", "path": private_path(actor)}] + [
            {"probe": "foreign", "path": private_path(peer)} for peer in ACTORS if peer != actor]
        return ('for(const c of ' + json.dumps(calls) + ') text({probe:c.probe,path:c.path,'
                'result:await tools.mcp__strata_broker__artifact_read({path:c.path})});')

    def next(self, actor, step, operation):
        require(actor in ACTORS and type(step) is int and 1 <= step <= 18, "PAIR_SEQUENCE")
        phase = self.phases[actor]
        if actor == ROOT:
            if phase < 2:
                self.phases[actor] += 1
                return [self.call(actor, "spawn", operation, name="spawn_agent", args={
                    "task_name": HELPERS[phase].rsplit("/", 1)[-1], "fork_turns": "none",
                    "message": "Exercise only the fixed two-helper broker and public-message fixture."})]
            if phase == 2:
                if not all(self.received(helper, ROOT, READY[helper]) for helper in HELPERS):
                    return [self.wait(actor, operation)]
                self.phases[actor] += 1
                return [self.call(actor, "overlap", operation, name="list_agents", args={})]
            if phase == 3:
                self.phases[actor] += 1
                return [self.call(actor, "overflow", operation, name="spawn_agent", args={
                    "task_name": "overflow", "fork_turns": "none", "message": "Fixed capacity refusal control."})]
            if phase in (4, 5):
                helper = HELPERS[phase - 4]
                self.phases[actor] += 1
                return [self.call(actor, "release", operation, name="send_message", args={
                    "target": helper, "message": RELEASE[helper]})]
            if phase == 6:
                if not all(self.received(helper, ROOT, DONE[helper], "FINAL_ANSWER") for helper in HELPERS):
                    return [self.wait(actor, operation)]
                self.phases[actor] += 1
                return [self.call(actor, "artifact_scope", operation, code=self.read_code(actor))]
            require(phase == 7, "PAIR_SEQUENCE")
            message = "Synthetic two-helper communication fixture complete."
        else:
            peer = next(helper for helper in HELPERS if helper != actor)
            if phase == 0:
                self.phases[actor] += 1
                return [self.call(actor, "ready", operation, name="send_message", args={
                    "target": ROOT, "message": READY[actor]})]
            if phase == 1:
                if not self.received(ROOT, actor, RELEASE[actor]):
                    return [self.wait(actor, operation)]
                self.phases[actor] += 1
                return [self.call(actor, "advice", operation, name="send_message", args={
                    "target": peer, "message": ADVICE[actor]})]
            if phase == 2:
                if not self.received(peer, actor, ADVICE[peer]):
                    return [self.wait(actor, operation)]
                self.phases[actor] += 1
                return [self.call(actor, "artifact_scope", operation, code=self.read_code(actor))]
            require(phase == 3, "PAIR_SEQUENCE")
            message = DONE[actor]
        self.finished.add(actor)
        self.phases[actor] += 1
        return [{"id": "message-" + operation, "type": "message", "role": "assistant", "status": "completed",
                 "content": [{"type": "output_text", "text": message, "annotations": []}]}]

    def report(self):
        overlap = [self.outputs.get(key) for key, call in self.calls.items() if call["phase"] == "overlap"]
        expected = {"agents": [{"agent_name": actor, "agent_status": "running"} for actor in ACTORS]}
        try:
            actual = json.loads(overlap[0]) if len(overlap) == 1 else None
            actual["agents"].sort(key=lambda row: row["agent_name"])
        except (ValueError, TypeError, KeyError):
            actual = None
        checks = {"pair_native_simultaneous_running": actual == expected,
                  "pair_three_finished": self.finished == set(ACTORS),
                  "pair_all_routed_messages_delivered": all(
                      self.received(h, ROOT, READY[h]) and self.received(ROOT, h, RELEASE[h]) and
                      self.received(h, ROOT, DONE[h], "FINAL_ANSWER") and
                      self.received(h, next(p for p in HELPERS if p != h), ADVICE[h]) for h in HELPERS)}
        for actor in ACTORS:
            prefix = actor.rsplit("/", 1)[-1]
            checks[prefix + "_private_marker_not_in_other_inputs"] = all(PRIVATE[actor] not in json.dumps(r["body"])
                for r in self.requests if r["actor"] != actor)
            results = [v for key, call in self.calls.items() if call == {"actor": actor, "phase": "artifact_scope"}
                       for v in records(self.outputs.get(key))]
            own = [v for v in results if v.get("probe") == "own"]
            foreign = [v for v in results if v.get("probe") == "foreign"]
            checks[prefix + "_own_artifact_read"] = len(own) == 1 and PRIVATE[actor] in json.dumps(own)
            checks[prefix + "_foreign_artifact_read_denied"] = len(foreign) == 2 and all(
                '"isError": true' in json.dumps(v) and "BROKER_FORBIDDEN" in json.dumps(v) for v in foreign)
        return {"schema": "strata/NativeHelperPairProbe/1", "is_example": True, "production_qualified": False,
                "checks": checks, "calls": self.calls, "outputs": self.outputs,
                "messages": sorted(self.messages), "waits": self.waits,
                "wait_phases": self.wait_phases,
                "overlap_native_text": [output_text(v) for v in overlap]}
