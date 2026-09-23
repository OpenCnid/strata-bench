"""Retain actual native-model/game observations; no scientific score or G0 pass."""

import json
import math

from mcbench.broker import inspect_game_requests
from mcbench.contracts import ActionAck, Observation
from mcbench.native_piloting import MAX_REQUESTS
from mcbench.storage import Principal, canonical


def movement_checks(calls):
    """Ordered public observations and action receipts, not model self-reports."""
    observations, actions, receipts = [], [], {}
    for index, call in enumerate(calls):
        request, response = call["body"], call["result"]
        if request["method"] == "act":
            actions.append((index, request["action"]))
        value = response.get("result") if response and response.get("status") == "ok" else None
        if not isinstance(value, dict):
            continue
        if value.get("schema") == "mcbench/Observation/1":
            observations.append((index, Observation.model_validate(value)))
        elif value.get("schema") == "mcbench/ActionAck/1":
            ack = ActionAck.model_validate(value)
            receipts.setdefault(ack.request_id, []).append((index, ack))
    checks = {"all_game_calls_settled": bool(calls) and all(c["state"] == "SETTLED" for c in calls),
              "two_model_selected_actions": len(actions) == 2 and
              [a["action"]["kind"] for _, a in actions] == ["look_at", "move_to"],
              "bounded_actions_observed": False, "turn_observed": False, "walk_observed": False}
    changes = []
    if not checks["two_model_selected_actions"]:
        return checks, changes
    scope = None
    for index, batch in actions:
        before = [o for i, o in observations if i < index and o.observation_id == batch["observation_id"]]
        done = [(i, a) for i, a in receipts.get(batch["request_id"], []) if i >= index and
                a.status == "completed" and a.release_confirmed and not a.requires_resync and
                a.action_seq == batch["seq"] and
                (a.campaign_id, a.agent_id, a.epoch) == (batch["campaign_id"], batch["agent_id"], batch["epoch"])]
        after = [(i, o) for i, o in observations if done and i > done[0][0] and o.last_action_seq == batch["seq"]]
        if len(before) != 1 or not done or not after:
            return checks, changes
        b, a = before[0], after[0][1]
        current_scope = (b.campaign_id, b.agent_id, b.epoch)
        if scope is None:
            scope = current_scope
        if (scope != current_scope or scope != (a.campaign_id, a.agent_id, a.epoch) or
                scope != (batch["campaign_id"], batch["agent_id"], batch["epoch"]) or
                b.is_example or a.is_example or b.state is None or a.state is None or
                b.event_gap or a.event_gap or not b.state.connected or not a.state.connected or
                (b.last_action_seq or 0) + 1 != batch["seq"] or
                b.state_revision != batch["expected_state_revision"] or a.state_revision <= b.state_revision or
                b.capability_digest != batch["capability_digest"] or
                a.capability_digest != b.capability_digest or
                b.control_revision != batch["control_revision"] or
                not batch["release_at_end"] or batch["duration_ms"] > 2000 or a.held_keys):
            return checks, changes
        p, q = b.state.position, a.state.position
        distance = math.hypot(q.x-p.x, q.z-p.z)
        turn = abs(math.atan2(math.sin(a.state.yaw-b.state.yaw), math.cos(a.state.yaw-b.state.yaw)))
        target = batch["action"]["target"]
        residual = math.sqrt((q.x-target["x"])**2 + (q.y-target["y"])**2 + (q.z-target["z"])**2)
        changes.append({"request_id": batch["request_id"], "kind": batch["action"]["kind"],
            "before_observation": b.observation_id, "after_observation": a.observation_id,
            "before_position": p.model_dump(), "after_position": q.model_dump(),
            "horizontal_distance": distance, "yaw_change_radians": turn,
            "target_distance": residual, "health_before": b.state.health, "health_after": a.state.health})
        if batch["action"]["kind"] == "look_at":
            expected_yaw = math.atan2(p.x-target["x"], p.z-target["z"])
            yaw_error = abs(math.atan2(math.sin(a.state.yaw-expected_yaw), math.cos(a.state.yaw-expected_yaw)))
            changes[-1]["target_yaw_error_radians"] = yaw_error
            checks["turn_observed"] = turn >= 0.1 and yaw_error <= 0.1
        else:
            checks["walk_observed"] = (0.4 <= distance <= 4 and
                residual <= batch["action"]["tolerance"] + 0.1 and a.state.health >= b.state.health)
    checks["bounded_actions_observed"] = True
    return checks, changes


def record_outcome(gate, plan, seal_ref):
    db = gate.db.connection
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    calls = []
    if "broker_game_calls" in tables:
        bodies = inspect_game_requests(db, plan.job_id)
        for row in db.execute("SELECT * FROM broker_game_calls WHERE runtime=? ORDER BY rowid", (plan.job_id,)):
            calls.append({"thread": row["thread"], "state": row["state"],
                "body": bodies[(row["thread"], row["request"])],
                "result": json.loads(row["result"]) if row["result"] else None})
    checks, changes = movement_checks(calls)
    attempts = [dict(r) for r in db.execute("SELECT operation,state,reason,receipt_digest FROM inference_attempts "
        "WHERE json_extract(request,'$.runtime_job_id')=?", (plan.job_id,))]
    valuations = [json.loads(r[0]) for r in db.execute("SELECT v.body FROM inference_valuations v JOIN "
        "inference_attempts a ON a.operation=v.operation WHERE json_extract(a.request,'$.runtime_job_id')=?", (plan.job_id,))]
    stopped = db.execute("SELECT state FROM native_worker_bindings WHERE job=?", (plan.job_id,)).fetchone()
    native = db.execute("SELECT state,returncode,reason FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone()
    checks.update(authentic_model_receipts=not gate.simulation and 1 <= len(attempts) <= MAX_REQUESTS and
        len(valuations) == len(attempts) and all(a["state"] == "SETTLED" for a in attempts),
        one_executor=len({c["thread"] for c in calls}) == 1,
        native_completed=native is not None and tuple(native) == ("FINALIZED", 0, "native_exit"),
        worker_lane_stopped=stopped is not None and stopped[0] == "STOPPED")
    result = {"schema": "strata/NativePilotResult/1", "is_example": gate.simulation,
        "job_id": plan.job_id, "profile_digest": plan.profile_digest(), "scope_decision": "D14",
        "production_qualified": False, "isolation_qualified": False, "G0": "fail",
        "model_evidence": "synthetic_fixture" if gate.simulation else "actual_native_oauth",
        "receipt_result": "pass" if all(checks.values()) else "fail", "checks": checks,
        "changes": changes, "game_calls": calls, "attempts": attempts, "valuations": valuations,
        "seal_ref": seal_ref}
    ref = gate.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(result))
    return ref, result
