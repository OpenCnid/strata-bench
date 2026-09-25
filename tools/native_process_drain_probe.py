"""Owned silent cells deliberately outlive helper completion; synthetic only."""

import json

from mcbench.storage import require
from native_state_canaries import ACTORS, StateCanaries

CHILD_DONE = "Synthetic process drain helper finished."
LATE_PATH = "results/after-process-stop.md"


class ProcessDrainCanaries(StateCanaries):
    def __init__(self):
        super().__init__()
        self.delivered = False
        self.waits = 0

    def observe(self, agent, body):
        super().observe(agent, body)
        if agent == ACTORS[0]:
            self.delivered |= any(item.get("type") == "agent_message"
                and item.get("author") == ACTORS[1] and item.get("recipient") == ACTORS[0]
                and any(part.get("type") == "input_text" and part.get("text", "").startswith(
                    "Message Type: FINAL_ANSWER\n") and part["text"].endswith("Payload:\n" + CHILD_DONE)
                    for part in item.get("content", [])) for item in body.get("input", []))

    def next(self, agent, step, operation):
        if step == 1:
            path = "notes/after-process-stop.md" if agent == ACTORS[0] else LATE_PATH
            code = ('await yield_control(); await new Promise(r=>setTimeout(r,90000)); '
                    'text(await tools.mcp__strata_broker__artifact_write(' + json.dumps({
                        "path": path, "text": "Owned late cell effect.", "expected_ref": None}) + '));')
            return [self.call(agent, "start", operation, code=code)]
        if agent == ACTORS[1]:
            require(step == 2 and self.ready[agent].is_set(), "PROCESS_DRAIN_HELPER_SEQUENCE")
            self.finished.add(agent)
            message = CHILD_DONE
        elif step == 2:
            return [self.call(agent, "spawn", operation, namespace="collaboration", name="spawn_agent",
                args={"task_name": "identity_child", "fork_turns": "none", "message":
                      "Use only the fixed synthetic broker and owned silent-cell fixture."})]
        elif not self.delivered:
            require(3 <= step <= 5, "PROCESS_DRAIN_HELPER_DELIVERY_BOUND")
            self.waits += 1
            return [self.call(agent, "join", operation, namespace="collaboration", name="wait_agent",
                              args={"timeout_ms": 10000})]
        else:
            require(3 <= step <= 6 and self.ready[agent].is_set(), "PROCESS_DRAIN_ROOT_SEQUENCE")
            self.finished.add(agent)
            message = "Synthetic whole-process drain fixture finished."
        return [{"id": "message-" + operation, "type": "message", "role": "assistant", "status": "completed",
                 "content": [{"type": "output_text", "text": message, "annotations": []}]}]

    def report(self):
        return {"schema": "strata/NativeProcessDrainCanaries/1", "is_example": True,
            "production_qualified": False, "cells": self.cells, "calls": self.calls,
            "outputs": self.outputs, "observed_ms": self.observed_ms, "checks": {
                "process_drain_both_silent_cells_observed": set(self.cells) == set(ACTORS),
                "process_drain_both_model_turns_finished": self.finished == set(ACTORS),
                "process_drain_helper_reply_delivered": self.delivered,
                "process_drain_bounded_joins": 1 <= self.waits <= 3,
            }}
