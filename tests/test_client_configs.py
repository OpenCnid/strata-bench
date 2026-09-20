"""Synthetic private client observations. No authentic role or consumer claim."""

import hashlib
import json

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.client_configs import inspect_client_configs
from test_telemetry_configs import snapshot


def source(tmp_path):
    plan = {"schema": "strata/ForgeTelemetryConfig/2", "campaign_id": "synthetic", "epoch": 1,
            "spool_directory": str(tmp_path), "max_bytes": 65536, "max_events": 1, "recipe_ids": [],
            "config_queries": [{"file_name": "fixture-common.toml",
                                "paths": [["quoted.key", "items"], ["absent"]]},
                               {"file_name": "absent-client.toml", "paths": [["key"]]}]}
    raw = json.dumps(plan).encode()
    value = {"schema": "strata/ClientConfigSnapshot/1", "module": "strata-forge1192-telemetry/0.3.2",
             "campaign_id": "synthetic", "epoch": 1, "plan_sha256": hashlib.sha256(raw).hexdigest(),
             "client_session_id": "12345678-1234-1234-1234-123456789012", "process_id": 1,
             "captured_unix_ms": 1000, "java_runtime": "synthetic-runtime", "phase": "connected_client",
             "actor_uuid": "23456789-1234-1234-1234-123456789012", "dimension": "fixture:world",
             "operator_development_only": True, "scoring_eligible": False,
             "config_queries": plan["config_queries"],
             "config_snapshots": [snapshot(), {"file_name": "absent-client.toml", "status": "unregistered"}]}
    path = tmp_path / "plan.json"
    path.write_bytes(raw)
    return path, value


def test_exact_client_plan_keeps_unregistered_and_unqualified_states(tmp_path):
    plan, value = source(tmp_path)
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    result = inspect_client_configs(plan, path)
    assert result["inspection"] == "pass"
    assert result["observation"]["config_snapshots"] == value["config_snapshots"]
    assert not result["pack_lock_qualified"] and not result["scoring_eligible"]
    assert result["gate_result"] == "not_run"


@pytest.mark.parametrize("case", ["plan", "scope", "queries", "missing", "duplicate", "paths",
                                  "score", "unknown", "server_phase", "failed_values", "numeric_flag"])
def test_client_plan_evidence_cannot_change_scope_or_selectors(tmp_path, case):
    plan, value = source(tmp_path)
    if case == "plan":
        plan.write_bytes(plan.read_bytes() + b"\n")
    elif case == "scope":
        value["epoch"] = 2
    elif case == "queries":
        value["config_queries"].reverse()
    elif case == "missing":
        value["config_snapshots"].pop()
    elif case == "duplicate":
        value["config_snapshots"][1] = value["config_snapshots"][0]
    elif case == "paths":
        value["config_snapshots"][0]["values"].reverse()
    elif case == "score":
        value["scoring_eligible"] = True
    elif case == "unknown":
        value["commands"] = []
    elif case == "server_phase":
        value["phase"] = "dedicated_server"
    elif case == "numeric_flag":
        value["scoring_eligible"] = 0
    else:
        value["config_snapshots"][0]["status"] = "unstable"
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises((Fault, ValidationError)):
        inspect_client_configs(plan, path)
