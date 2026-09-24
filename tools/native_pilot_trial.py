"""M0 live-piloting adapter, with explicit one-run operator decision input."""

import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from mcbench.authorization import ExecutionAuthorization, parse_authorization
from mcbench.budgets import Budgets
from mcbench.native_piloting import MAX_SPEND
from mcbench.storage import digest, reject_links, require

ROOT = Path(__file__).resolve().parents[1]


def check_inputs(inputs):
    require(isinstance(inputs, dict) and set(inputs) - {"budget_decision"} == {
        "database", "objects", "credentials", "preflight", "authorization", "job_id"}, "PILOT_INPUTS")
    for key in ("database", "objects", "credentials", "preflight"):
        path = Path(inputs[key])
        reject_links(path)
        require(path.is_absolute() and path.exists() and not path.resolve().is_relative_to(ROOT), "PILOT_PRIVATE_INPUT")
    require(inputs["authorization"] == "validation-2026-09-18", "PILOT_INPUTS")
    # WAL-aware read-only access, before Java, worker, credentials or model startup.
    db = sqlite3.connect(Path(inputs["database"]).as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        row = db.execute("SELECT * FROM execution_authorizations WHERE id=?", (inputs["authorization"],)).fetchone()
        require(row is not None, "ORIGINAL_ACCOUNTING_REQUIRED")
        policy = parse_authorization(row["body"])
        require(isinstance(policy, ExecutionAuthorization) and digest(policy.model_dump()) == row["digest"] and policy.first_trial_max_microusd >= MAX_SPEND,
                "ORIGINAL_ACCOUNTING_REQUIRED")
        require(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (inputs["job_id"],)).fetchone() is None,
                "PILOT_ALREADY_ATTEMPTED")
        totals, unknown = Budgets.totals(db, row["account"])
        decision = None
        if "budget_decision" in inputs:
            path = Path(inputs["budget_decision"])
            reject_links(path)
            require(path.is_absolute() and path.is_file() and not path.resolve().is_relative_to(ROOT),
                    "PILOT_PRIVATE_INPUT")
            from mcbench.pilot_budget import check_decision
            decision = json.loads(path.read_bytes())
            check_decision(db, decision)
            require(decision["job_id"] == inputs["job_id"], "PILOT_INPUTS")
        require(not unknown or decision is not None, "PILOT_ACCOUNTING_BLOCKED")
        from mcbench.pilot_budget import DECISIONS
        require(decision is not None or inputs["job_id"] in {job for job, _ in DECISIONS.values()},
                "PILOT_INPUTS")
        require(totals["spend_microusd"] + MAX_SPEND <= policy.total_spend_microusd, "ALLOWANCE_UNAVAILABLE")
        require(len(policy.models) == 1 and policy.models[0] == policy.accounting_basis.model,
                "PILOT_MODEL_AUTHORITY")
        return {"authorization_digest": row["digest"], "model": policy.models[0], "committed_and_reserved": totals,
                "additional_maximum_microusd": MAX_SPEND, "isolation_qualified": False,
                "budget_decision": decision}
    finally:
        db.close()


def run_trial(plan, output, descriptor, lease_id):
    from native_oauth_conformance import run_native_trial
    inputs = plan["pilot"]
    admission = check_inputs(inputs)
    args = SimpleNamespace(**{key: Path(inputs[key]) for key in (
        "database", "objects", "credentials", "preflight")}, authorization=inputs["authorization"],
        codex=Path(plan["codex"]), output=output, catalog=Path(plan["model_catalog"]),
        tool_projections=Path(plan["tool_projections"]), metering_trial=None)
    run_native_trial(args, pilot={"job_id": inputs["job_id"], "descriptor": descriptor, "lease_id": lease_id,
                                 "budget_decision": admission["budget_decision"]})
    return json.loads((output / "result.json").read_bytes())
