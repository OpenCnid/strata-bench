"""Operator-owned held-job drain evidence, never inferred from native prose.

This only supports stopped-job cell disposal/export. It grants no early helper
retirement, cost settlement, action success, checkpoint or runtime qualification.
"""

from typing import Literal

from pydantic import Field

from .contracts import Digest, Id, Positive, Strict, UInt
from .storage import Principal, canonical, require

POLICY = "held-windows-job-zero-active/1"
OPERATOR = Principal("operator", "operator")


class JobAccounting(Strict):
    total_processes: Positive
    active_processes: UInt = Field(le=0)
    terminated_processes: UInt


class HeldProcessDrain(Strict):
    schema_: Literal["strata/HeldProcessDrain/1"] = Field(alias="schema")
    policy: Literal["held-windows-job-zero-active/1"]
    root_returncode: int
    accounting: JobAccounting
    observed_unix_ms: Positive
    observation_elapsed_ns: UInt


class NativeProcessDrain(Strict):
    schema_: Literal["strata/NativeProcessDrain/1"] = Field(alias="schema")
    is_example: bool
    job_id: Id
    profile_digest: Digest
    plan_digest: Digest
    started_unix_ms: Positive
    observation: HeldProcessDrain


def record_process_drain(runtime, plan, observed):
    """Called only by the owning supervisor after stop/close has succeeded."""
    observation = HeldProcessDrain.model_validate(observed)
    require(observation.accounting.terminated_processes <= observation.accounting.total_processes,
            "NATIVE_PROCESS_DRAIN_ACCOUNTING")
    row = runtime._row(plan.job_id)
    require(row["state"] in {"RUNNING", "STOPPING"} and row["started"] is not None,
            "NATIVE_PROCESS_DRAIN_SCOPE")
    proof = NativeProcessDrain.model_validate({"schema": "strata/NativeProcessDrain/1",
        "is_example": runtime.simulation, "job_id": plan.job_id, "profile_digest": plan.profile_digest(),
        "plan_digest": row["plan_digest"], "started_unix_ms": int(row["started"] * 1000),
        "observation": observation.model_dump()})
    require(proof.started_unix_ms <= observation.observed_unix_ms, "NATIVE_PROCESS_DRAIN_CLOCK")
    ref = runtime.cas.put(OPERATOR, "operator", "operator", canonical(proof.model_dump()))
    with runtime.db.transaction() as db:
        require(db.execute("SELECT 1 FROM native_process_drains WHERE job=?", (plan.job_id,)).fetchone() is None,
                "NATIVE_PROCESS_DRAIN_DUPLICATE")
        event = runtime.db.event(db, "native.process_tree_drained", {
            "job_id": plan.job_id, "profile_digest": plan.profile_digest(), "proof_ref": ref})
        db.execute("INSERT INTO native_process_drains VALUES(?,?,?)", (plan.job_id, ref, event))
    return ref


def require_process_drain(db, cas, plan):
    """Read-only proof join for a finalized job; legacy absence is not a pass."""
    require(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='native_process_drains'").fetchone()
            is not None, "NATIVE_PROCESS_DRAIN_MISSING")
    row = db.execute("SELECT * FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone()
    require(row is not None and row["state"] == "FINALIZED" and row["started"] is not None
            and row["ended"] is not None and type(row["returncode"]) is int,
            "NATIVE_PROCESS_DRAIN_NOT_FINAL")
    link = db.execute("SELECT * FROM native_process_drains WHERE job=?", (plan.job_id,)).fetchone()
    require(link is not None, "NATIVE_PROCESS_DRAIN_MISSING")
    obj = db.execute("SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (link["proof_ref"],)).fetchone()
    require(obj is not None and obj["visibility"] == "operator", "NATIVE_PROCESS_DRAIN_PRIVATE")
    proof = NativeProcessDrain.model_validate_json(cas.read(OPERATOR, "operator", link["proof_ref"], max_bytes=16384))
    mode = db.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()
    require(proof.job_id == plan.job_id and proof.profile_digest == plan.profile_digest()
            and proof.plan_digest == row["plan_digest"]
            and type(plan).model_validate_json(row["plan"]).model_dump() == plan.model_dump()
            and mode is not None and proof.is_example is bool(mode[0]), "NATIVE_PROCESS_DRAIN_SCOPE")
    evidence = proof.observation
    require(proof.started_unix_ms == int(row["started"] * 1000)
            <= evidence.observed_unix_ms <= int(row["ended"] * 1000)
            and evidence.root_returncode == row["returncode"]
            and evidence.accounting.terminated_processes <= evidence.accounting.total_processes,
            "NATIVE_PROCESS_DRAIN_SCOPE")
    event = db.execute("SELECT kind,body FROM outbox WHERE cursor=?", (link["event"],)).fetchone()
    require(event is not None and event["kind"] == "native.process_tree_drained" and event["body"] == canonical({
        "job_id": plan.job_id, "profile_digest": plan.profile_digest(), "proof_ref": link["proof_ref"]}).decode(),
        "NATIVE_PROCESS_DRAIN_SOURCE")
    return {"policy": POLICY, "proof_ref": link["proof_ref"], "event": link["event"],
            "active_processes": 0, "total_processes": evidence.accounting.total_processes}
