"""M0 live-piloting adapter. Never supplies an accounting exception or a fixture."""

import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from mcbench.authorization import ExecutionAuthorization
from mcbench.budgets import Budgets
from mcbench.native_piloting import MAX_SPEND
from mcbench.storage import digest, reject_links, require

ROOT = Path(__file__).resolve().parents[1]


def check_inputs(inputs):
    require(isinstance(inputs, dict) and set(inputs) == {
        "database", "objects", "credentials", "preflight", "authorization", "job_id"}, "PILOT_INPUTS")
    for key in ("database", "objects", "credentials", "preflight"):
        path = Path(inputs[key])
        reject_links(path)
        require(path.is_absolute() and path.exists() and not path.resolve().is_relative_to(ROOT), "PILOT_PRIVATE_INPUT")
    require(inputs["authorization"] == "validation-2026-09-18" and
            inputs["job_id"] == inputs["authorization"] + ":m0-pilot-01", "PILOT_INPUTS")
    # WAL-aware read-only access, before Java, worker, credentials or model startup.
    db = sqlite3.connect(Path(inputs["database"]).as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        row = db.execute("SELECT * FROM execution_authorizations WHERE id=?", (inputs["authorization"],)).fetchone()
        require(row is not None, "ORIGINAL_ACCOUNTING_REQUIRED")
        policy = ExecutionAuthorization.model_validate_json(row["body"])
        require(digest(policy.model_dump()) == row["digest"] and policy.first_trial_max_microusd >= MAX_SPEND,
                "ORIGINAL_ACCOUNTING_REQUIRED")
        require(db.execute("SELECT 1 FROM native_jobs WHERE id=?", (inputs["job_id"],)).fetchone() is None,
                "PILOT_ALREADY_ATTEMPTED")
        totals, unknown = Budgets.totals(db, row["account"])
        require(not unknown, "PILOT_ACCOUNTING_BLOCKED")
        require(totals["spend_microusd"] + MAX_SPEND <= policy.total_spend_microusd, "ALLOWANCE_UNAVAILABLE")
        return {"authorization_digest": row["digest"], "committed_and_reserved": totals,
                "additional_maximum_microusd": MAX_SPEND, "isolation_qualified": False}
    finally:
        db.close()


def run_trial(plan, output, descriptor, lease_id):
    from native_oauth_conformance import run_native_trial
    inputs = plan["pilot"]
    check_inputs(inputs)
    args = SimpleNamespace(**{key: Path(inputs[key]) for key in (
        "database", "objects", "credentials", "preflight")}, authorization=inputs["authorization"],
        codex=Path(plan["codex"]), output=output, catalog=Path(plan["model_catalog"]),
        tool_projections=Path(plan["tool_projections"]), metering_trial=None)
    run_native_trial(args, pilot={"job_id": inputs["job_id"], "descriptor": descriptor, "lease_id": lease_id})
    return json.loads((output / "result.json").read_bytes())
