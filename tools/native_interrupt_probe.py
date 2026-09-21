"""Owned native pending-cell interruption and explicit owner cleanup fixture."""

import json
import re
import time

from mcbench.native_admission import NativeAdmission
from mcbench.native_retirement import POLICY
from mcbench.storage import CAS, Database, Principal, canonical, require
from native_retirement_probe import wait_for_issuance
from native_state_canaries import output_text, records

ROOT, CHILD = "/root", "/root/identity_child"
LATE_PATH = "results/late-cell.md"


def cell_state(value, cell):
    lines = [line for line in output_text(value).splitlines() if line]
    if len(lines) < 3 or not re.fullmatch(r"Wall time [0-9]+\.[0-9]+ seconds", lines[1]):
        return None
    if lines[2] != "Output:":
        return None
    if lines[0] == "Script running with cell ID " + str(cell):
        return "pending"
    if lines == ["Script failed", lines[1], "Output:", "Script error:", "exec cell " + str(cell) + " not found"]:
        return "absent"
    if lines == ["Script terminated", lines[1], "Output:"]:
        return "terminated"
    return None


def allowed_listing(result):
    if not isinstance(result, dict) or result.get("isError"):
        return False
    content = result.get("content")
    if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict):
        return False
    try:
        body = json.loads(content[0].get("text", ""))
    except (ValueError, TypeError):
        return False
    if not isinstance(body, dict) or set(body) != {"files"} or not isinstance(body["files"], list):
        return False
    rows = body["files"]
    return len(rows) == 2 and all(isinstance(r, dict) and set(r) == {"path", "ref", "immutable"}
        and isinstance(r["ref"], str) and re.fullmatch(r"cas:sha256:[0-9a-f]{64}", r["ref"])
        and type(r["immutable"]) is int and r["immutable"] == int(r["path"] == "supplied/plan.md") for r in rows
        ) and {r["path"] for r in rows} == {"supplied/plan.md", "results/advice.md"}


class InterruptProbe:
    def __init__(self):
        self.calls, self.outputs, self.observed_ms = {}, {}, {}
        self.cell = self.cell_started_ms = None
        self.root_phase = "spawn"
        self.polls = 0
        self.joins = 0
        self.finished = False
        self.post_interrupt = None
        self.issuance = self.status_call = self.proof_ref = self.retired = None
        self.wait_operation = None

    def call(self, actor, phase, operation, *, name="exec", namespace="functions", args=None, code=None):
        key = "interrupt-" + phase + "-" + operation
        require(key not in self.calls, "INTERRUPT_DUPLICATE_CALL")
        self.calls[key] = {"actor": actor, "phase": phase, "issued_ms": time.time_ns() // 1000000}
        base = {"id": "tool-" + key, "call_id": key, "namespace": namespace, "name": name}
        return {**base, "type": "custom_tool_call", "input": code} if code is not None else {
            **base, "type": "function_call", "arguments": json.dumps(args)}

    def observe(self, actor, body):
        require(actor in {ROOT, CHILD}, "INTERRUPT_ACTOR")
        for item in body.get("input", []):
            if item.get("type") not in {"function_call_output", "custom_tool_call_output"}:
                continue
            key = item.get("call_id")
            if key not in self.calls:
                continue
            require(self.calls[key]["actor"] == actor, "INTERRUPT_WRONG_ACTOR")
            value = item.get("output")
            require(key not in self.outputs or self.outputs[key] == value, "INTERRUPT_RESULT_CHANGED")
            self.outputs[key] = value
            self.observed_ms.setdefault(key, time.time_ns() // 1000000)
            if self.calls[key]["phase"] == "pending":
                found = re.findall(r"Script running with cell ID ([A-Za-z0-9_-]+)", output_text(value))
                require(len(found) == 1 and (self.cell is None or self.cell == found[0]), "INTERRUPT_CELL_REQUIRED")
                self.cell = found[0]
                starts = [r["at_ms"] for r in records(value) if r.get("probe") == "cell_start" and
                          type(r.get("at_ms")) is int]
                require(len(starts) == 1 and (self.cell_started_ms is None or self.cell_started_ms == starts[0]),
                        "INTERRUPT_CELL_START_REQUIRED")
                self.cell_started_ms = starts[0]

    def output(self, phase):
        values = [self.outputs[k] for k, c in self.calls.items() if c["phase"] == phase and k in self.outputs]
        require(len(values) == 1, "INTERRUPT_RESULT_MISSING")
        return values[0]

    @staticmethod
    def child_thread(db):
        row = db.connection.execute("SELECT thread FROM native_participants WHERE job='root' AND name=?",
                                    (CHILD,)).fetchone()
        require(row is not None, "INTERRUPT_CHILD_MISSING")
        return row[0]

    def next(self, provider, actor, step, operation):
        if actor == CHILD:
            if step == 1:
                code = ('text({probe:"cell_start",at_ms:Date.now()}); await yield_control(); '
                    'await new Promise(r=>setTimeout(r,60000)); '
                    'const t=ALL_TOOLS.find(t=>t.name.endsWith("__artifact_write")); '
                    'text(await tools[t.name](' + json.dumps({"path": LATE_PATH,
                    "text": "Owned late cell canary.", "expected_ref": None}) + ')); '
                    'text({probe:"late_effect",at_ms:Date.now()});')
                return self.call(actor, "pending", operation, code=code)
            if step == 2:
                require(self.cell is not None, "INTERRUPT_CELL_REQUIRED")
                self.wait_operation = operation
                return self.call(actor, "original_wait", operation, name="wait",
                                 args={"cell_id": self.cell, "yield_time_ms": 30000, "max_tokens": 1000})
            if step == 3:
                require(self.root_phase in {"join", "status"}, "INTERRUPT_UNEXPECTED_RESUME")
                return self.call(actor, "after_interrupt", operation, name="wait",
                                 args={"cell_id": self.cell, "yield_time_ms": 1, "max_tokens": 1000})
            if step == 4:
                value = cell_state(self.output("after_interrupt"), self.cell)
                if value == "pending":
                    self.post_interrupt = "surviving_pending_cell"
                elif value == "absent":
                    self.post_interrupt = "cell_absent_after_interrupt"
                else:
                    require(False, "INTERRUPT_CELL_OUTCOME_UNEXPECTED")
                # Explicit owner cancellation, even when interruption already
                # removed the cell. Never use a foreign participant's handle.
                return self.call(actor, "owner_cancel", operation, name="wait", args={
                    "cell_id": self.cell, "yield_time_ms": 1, "max_tokens": 1000, "terminate": True})
            if step == 5:
                code = ('const t=ALL_TOOLS.find(t=>t.name.endsWith("__artifact_list")); '
                    'text({probe:"after_cleanup",result:await tools[t.name]({})});')
                return self.call(actor, "after_cleanup", operation, code=code)
            if step == 6:
                deadline = self.cell_started_ms + 60500
                code = ('// @exec: {"yield_time_ms": 60000}\n'
                    'const remaining=' + str(deadline) + '-Date.now(); '
                    'if(remaining<0 || remaining>60500) throw new Error("OBSERVATION_WINDOW"); '
                    'await new Promise(r=>setTimeout(r,remaining)); '
                    'const t=ALL_TOOLS.find(t=>t.name.endsWith("__artifact_list")); '
                    'text({probe:"after_deadline",at_ms:Date.now(),result:await tools[t.name]({})});')
                return self.call(actor, "after_deadline", operation, code=code)
            require(step == 7, "INTERRUPT_HELPER_BOUND")
            db = Database(provider.database_path)
            try:
                NativeAdmission(db, CAS(db, provider.objects)).revoke("root", self.child_thread(db))
            finally:
                db.close()
            self.finished = True
        else:
            require(actor == ROOT, "INTERRUPT_ACTOR")
            phase = self.root_phase
            if phase == "spawn":
                self.root_phase = "poll"
                return self.call(actor, phase, operation, namespace="collaboration", name="spawn_agent", args={
                    "task_name": "identity_child", "fork_turns": "none",
                    "message": "Exercise only the owned pending-cell and cleanup fixture."})
            if phase == "poll":
                if self.cell is None:
                    self.polls += 1
                    require(self.polls <= 3, "INTERRUPT_STARTUP_BOUND")
                    return self.call(actor, "startup_" + str(self.polls), operation, namespace="collaboration",
                        name="wait_agent", args={"timeout_ms": 10000})
                self.root_phase = "followup"
                db = Database(provider.database_path)
                try:
                    require(self.wait_operation is not None, "INTERRUPT_WAIT_NOT_ISSUED")
                    wait_for_issuance(db, self.wait_operation)
                finally:
                    db.close()
                return self.call(actor, "interrupt", operation, namespace="collaboration", name="interrupt_agent",
                                 args={"target": "identity_child"})
            if phase == "followup":
                self.root_phase = "join"
                return self.call(actor, phase, operation, namespace="collaboration", name="followup_task", args={
                    "target": "identity_child", "message": "Owned diagnostic: inspect and clean up the prior cell."})
            if phase == "join":
                if not self.finished:
                    self.joins += 1
                    require(self.joins <= 3, "INTERRUPT_DRAIN_BOUND")
                    return self.call(actor, "join_" + str(self.joins), operation, namespace="collaboration",
                                     name="wait_agent", args={"timeout_ms": 30000})
                self.root_phase = phase = "status"
            if phase == "status":
                require(self.finished, "INTERRUPT_CLEANUP_INCOMPLETE")
                self.root_phase = "retire"
                self.issuance = operation
                call = self.call(actor, phase, operation, namespace="collaboration", name="list_agents", args={})
                self.status_call = call["call_id"]
                return call
            require(phase == "retire", "INTERRUPT_ROOT_BOUND")
            db = Database(provider.database_path)
            try:
                wait_for_issuance(db, self.issuance)
                cas = CAS(db, provider.objects)
                proof = {"schema": "strata/NativeParticipantRetirement/1", "policy": POLICY,
                    "is_example": True, "job_id": "root", "profile_digest": provider.plan.profile_digest(),
                    "thread_id": self.child_thread(db), "issuance_operation": self.issuance,
                    "observation_operation": operation, "call_id": self.status_call}
                self.proof_ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(proof))
                self.retired = NativeAdmission(db, cas).retire("root", proof["thread_id"], self.proof_ref)
            finally:
                db.close()
            self.root_phase = "done"
        return {"id": "message-" + operation, "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": "Synthetic interruption fixture finished.", "annotations": []}]}

    def report(self, provider, db):
        phases = {c["phase"]: key for key, c in self.calls.items()}
        cancel = cell_state(self.outputs.get(phases.get("owner_cancel")), self.cell)
        cleanup = records(self.outputs.get(phases.get("after_cleanup")))
        late = records(self.outputs.get(phases.get("after_deadline")))
        interrupted = records(self.outputs.get(phases.get("interrupt")))
        rows = [dict(r) for r in db.connection.execute("SELECT l.* FROM broker_call_lifecycle l ORDER BY event")]
        checks = {
            "interrupt_pending_cell_observed": self.cell is not None,
            "interrupt_post_status_observed": self.post_interrupt in {
                "surviving_pending_cell", "cell_absent_after_interrupt"},
            "interrupt_target_was_running": interrupted == [{"previous_status": "running"}],
            "interrupt_explicit_owner_cleanup": (self.post_interrupt == "surviving_pending_cell" and
                cancel == "terminated") or (self.post_interrupt == "cell_absent_after_interrupt" and cancel == "absent"),
            "interrupt_cleanup_before_late_deadline": "pending" in phases and "after_cleanup" in phases and
                self.observed_ms.get(phases["after_cleanup"], 2**63) - self.calls[phases["pending"]]["issued_ms"] < 60000,
            "interrupt_no_late_artifact": not any(r[0] == LATE_PATH for r in db.connection.execute(
                "SELECT path FROM broker_files")),
            "interrupt_allowed_listing_after_cleanup": any(r.get("probe") == "after_cleanup" and
                allowed_listing(r.get("result")) for r in cleanup),
            "interrupt_no_effect_after_deadline_with_active_grant": any(r.get("probe") == "after_deadline" and
                type(r.get("at_ms")) is int and type(self.cell_started_ms) is int and
                r["at_ms"] >= self.cell_started_ms + 60000 and
                allowed_listing(r.get("result")) for r in late),
            "interrupt_helper_retired_after_cleanup": self.retired is not None and self.retired["state"] == "CLOSED",
            "interrupt_every_broker_call_terminal": bool(rows) and all(r["state"] in {"RETURNED", "REJECTED"}
                and r["elapsed_ns"] is not None for r in rows),
            "interrupt_every_actor_finished": self.finished and self.root_phase == "done",
            "interrupt_fixture_bounded": len(provider.requests) <= 20 and self.polls <= 3 and self.joins <= 3,
        }
        return {"schema": "strata/NativeInterruptProbe/1", "is_example": True, "production_qualified": False,
            "checks": checks, "post_interrupt": self.post_interrupt, "cell": self.cell,
            "cell_started_ms": self.cell_started_ms,
            "calls": self.calls, "outputs": self.outputs, "observed_ms": self.observed_ms,
            "broker_lifecycle": rows, "proof_ref": self.proof_ref}
