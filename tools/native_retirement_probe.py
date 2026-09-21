"""Fixed native helper retirement/replacement fixture; synthetic provider only."""

import json
import time

from mcbench.native_admission import NativeAdmission
from mcbench.native_retirement import POLICY
from mcbench.storage import CAS, Database, Principal, canonical, require

ACTORS = {"/root", "/root/identity_child", "/root/replacement"}


def wait_for_issuance(db, operation, *, timeout_s=0.5):
    """Drain a known local receipt race, not a provider retry or unknown settlement."""
    require(0 < timeout_s <= 0.5, "RETIREMENT_FIXTURE_WAIT_BOUND")
    deadline = time.monotonic() + timeout_s
    while True:
        row = db.connection.execute("SELECT state FROM inference_attempts WHERE operation=?",
                                    (operation,)).fetchone()
        require(row is not None and row[0] in {"DISPATCHING", "SETTLED"}, "RETIREMENT_FIXTURE_ISSUANCE_FAILED")
        if row[0] == "SETTLED":
            return
        require(time.monotonic() < deadline, "RETIREMENT_FIXTURE_ISSUANCE_TIMEOUT")
        time.sleep(0.005)


class RetirementProbe:
    def __init__(self):
        self.issuance = None
        self.status_call = None
        self.proof_ref = None
        self.retired = None
        self.finished = set()
        self.fence_counts = None
        self.calls = {}

    def call(self, operation, name, args):
        call_id = "retirement-" + operation
        self.calls[call_id] = {"name": name, "args": args}
        return {"id": "tool-" + operation, "type": "function_call", "call_id": call_id,
                "namespace": "collaboration", "name": name, "arguments": json.dumps(args)}

    @staticmethod
    def child(db):
        row = db.connection.execute("SELECT thread FROM native_participants WHERE job='root' "
                                    "AND name='/root/identity_child'").fetchone()
        require(row is not None, "RETIREMENT_FIXTURE_CHILD_MISSING")
        return row[0]

    def next(self, provider, agent, step, operation):
        require(agent in ACTORS, "RETIREMENT_FIXTURE_ACTOR")
        if agent != "/root":
            require(step == 1, "RETIRED_HELPER_WAS_FORWARDED")
            self.finished.add(agent)
            message = "Synthetic original helper completed." if agent.endswith("identity_child") else (
                "Synthetic replacement helper completed.")
        elif step == 1:
            return self.call(operation, "spawn_agent", {"task_name": "identity_child", "fork_turns": "none",
                "message": "Use only the fixed synthetic broker; then return the fixture result."})
        elif step in {2, 6, 8}:
            return self.call(operation, "wait_agent", {"timeout_ms": 30000})
        elif step == 3:
            require("/root/identity_child" in self.finished, "RETIREMENT_FIXTURE_CHILD_NOT_FINISHED")
            db = Database(provider.database_path)
            try:
                admission = NativeAdmission(db, CAS(db, provider.objects))
                thread = self.child(db)
                admission.revoke("root", thread)
                self.fence_counts = {"held_helpers": db.connection.execute(
                    "SELECT count(*) FROM native_participants WHERE job='root' AND depth>0 "
                    "AND state!='CLOSED'").fetchone()[0], "state": db.connection.execute(
                    "SELECT state FROM native_participants WHERE job='root' AND thread=?", (thread,)).fetchone()[0]}
            finally:
                db.close()
            return self.call(operation, "interrupt_agent", {"target": "identity_child"})
        elif step == 4:
            self.issuance = operation
            result = self.call(operation, "list_agents", {})
            self.status_call = result["call_id"]
            return result
        elif step == 5:
            db = Database(provider.database_path)
            try:
                wait_for_issuance(db, self.issuance)
                cas = CAS(db, provider.objects)
                proof = {"schema": "strata/NativeParticipantRetirement/1", "policy": POLICY,
                    "is_example": True, "job_id": "root", "profile_digest": provider.plan.profile_digest(),
                    "thread_id": self.child(db), "issuance_operation": self.issuance,
                    "observation_operation": operation, "call_id": self.status_call}
                self.proof_ref = cas.put(Principal("operator", "operator"), "operator", "operator", canonical(proof))
                self.retired = NativeAdmission(db, cas).retire("root", proof["thread_id"], self.proof_ref)
            finally:
                db.close()
            return self.call(operation, "followup_task", {"target": "identity_child",
                "message": "Owned negative fixture: request another response after permanent retirement."})
        elif step == 7:
            return self.call(operation, "spawn_agent", {"task_name": "replacement", "fork_turns": "none",
                "message": "Use only the fixed synthetic broker; then return the fixture result."})
        elif step == 9:
            require("/root/replacement" in self.finished, "RETIREMENT_FIXTURE_REPLACEMENT_NOT_FINISHED")
            return self.call(operation, "list_agents", {})
        else:
            require(step == 10, "RETIREMENT_FIXTURE_REQUEST_BOUND")
            self.finished.add(agent)
            message = "Synthetic native retirement fixture finished."
        return {"id": "message-" + operation, "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": message, "annotations": []}]}

    def report(self, provider, db):
        participants = [dict(r) for r in db.connection.execute(
            "SELECT * FROM native_participants ORDER BY name")]
        retires = [dict(r) for r in db.connection.execute("SELECT * FROM native_participant_retirements")]
        forwarded = [r for r in provider.requests if r.get("forwarded")]
        rejected = [r for r in provider.requests if not r.get("forwarded")]
        attempts = [dict(r) for r in db.connection.execute("SELECT operation,state FROM inference_attempts")]
        namespaces = [dict(r) for r in db.connection.execute("SELECT thread,namespace FROM broker_grants")]
        role_counts = {a: sum(i["agent"] == a for i in provider.identities) for a in ACTORS}
        checks = {
            "retirement_one_slot_profile": provider.plan.helper_limit == 1,
            "revocation_kept_slot_until_proved": self.fence_counts == {"held_helpers": 1, "state": "REVOKED"},
            "retirement_closed_original_helper": self.retired is not None and self.retired["state"] == "CLOSED",
            "native_original_resume_not_forwarded": len(rejected) == 1 and
                provider.errors == ["NATIVE_ADMISSION_SCOPE"],
            "retirement_exact_request_inventory": len(provider.requests) == 16 and len(forwarded) == 15 and
                len(attempts) == 15 and all(r["state"] == "SETTLED" for r in attempts),
            "retirement_distinct_namespaces": len(namespaces) == 3 and len({r["namespace"] for r in namespaces}) == 3,
            "retirement_distinct_thread_identities": len(participants) == 3 and
                {p["name"] for p in participants} == ACTORS and len({p["thread"] for p in participants}) == 3,
            "retirement_exact_role_counts": role_counts == {"/root": 11, "/root/identity_child": 2,
                                                             "/root/replacement": 2},
            "retirement_durable_proof": len(retires) == 1 and retires[0]["proof_ref"] == self.proof_ref,
            "retirement_every_actor_finished": self.finished == ACTORS,
        }
        return {"schema": "strata/NativeRetirementProbe/1", "is_example": True,
            "production_qualified": False, "checks": checks, "proof_ref": self.proof_ref,
            "fence_counts": self.fence_counts, "role_counts": role_counts,
            "requests": provider.requests, "retirements": retires, "namespaces": namespaces}
