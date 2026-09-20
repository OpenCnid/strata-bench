"""Inspect a private connected-client config export. No scoring or lock authority."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from mcbench.contracts import Digest, Id, Name, Strict, UInt
from mcbench.storage import reject_links, require

from .cli import write_report
from .run_costs import decode
from .telemetry_configs import ConfigQuery, ConfigSnapshot

Uuid = Annotated[str, Field(pattern=r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$")]


class ClientPlan(Strict):
    wire_schema: Literal["strata/ForgeTelemetryConfig/2"] = Field(alias="schema")
    campaign_id: Id
    epoch: int = Field(ge=1, le=9007199254740991)
    spool_directory: str
    max_bytes: int = Field(ge=65536, le=1048576)
    max_events: int = Field(ge=1, le=1)
    recipe_ids: list[Name] = Field(max_length=0)
    config_queries: list[ConfigQuery] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def unique(self):
        require(len({q.file_name for q in self.config_queries}) == len(self.config_queries),
                "CLIENT_CONFIG_QUERY_DUPLICATE")
        require(Path(self.spool_directory).is_absolute(), "CLIENT_CONFIG_PRIVATE_PATH")
        return self


class ClientSnapshot(Strict):
    wire_schema: Literal["strata/ClientConfigSnapshot/1"] = Field(alias="schema")
    module: Literal["strata-forge1192-telemetry/0.3.2"]
    campaign_id: Id
    epoch: UInt
    plan_sha256: Digest
    client_session_id: Uuid
    process_id: int = Field(ge=1, le=9007199254740991)
    captured_unix_ms: UInt
    java_runtime: str = Field(min_length=1, max_length=128)
    phase: Literal["connected_client"]
    actor_uuid: Uuid
    dimension: Name
    operator_development_only: Literal[True]
    scoring_eligible: Literal[False]
    config_queries: list[ConfigQuery] = Field(min_length=1, max_length=16)
    config_snapshots: list[ConfigSnapshot] = Field(min_length=1, max_length=16)

    @field_validator("operator_development_only", "scoring_eligible", mode="before")
    @classmethod
    def strict_flags(cls, value):
        require(type(value) is bool, "CLIENT_CONFIG_FLAG_TYPE")
        return value


def read_private(path, limit):
    require(path.is_absolute(), "CLIENT_CONFIG_PRIVATE_PATH")
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= limit, "CLIENT_CONFIG_INPUT_QUOTA")
    value = path.read_bytes()
    require(len(value) <= limit, "CLIENT_CONFIG_INPUT_QUOTA")
    return value


def inspect_client_configs(plan_path, snapshot_path):
    source = read_private(plan_path, 65536)
    plan = ClientPlan.model_validate(decode(source))
    raw = read_private(snapshot_path, plan.max_bytes)
    snapshot = ClientSnapshot.model_validate(decode(raw))
    require(snapshot.plan_sha256 == hashlib.sha256(source).hexdigest(), "CLIENT_CONFIG_PLAN_CHANGED")
    require((snapshot.campaign_id, snapshot.epoch) == (plan.campaign_id, plan.epoch), "CLIENT_CONFIG_SCOPE")
    require(snapshot.config_queries == plan.config_queries, "CLIENT_CONFIG_QUERY_MISMATCH")
    require([s.file_name for s in snapshot.config_snapshots] == [q.file_name for q in plan.config_queries],
            "CLIENT_CONFIG_SNAPSHOT_MISMATCH")
    for query, value in zip(plan.config_queries, snapshot.config_snapshots, strict=True):
        if value.status == "snapshot":
            require([row.path for row in value.values] == query.paths, "CLIENT_CONFIG_PATH_MISMATCH")
    require(source == read_private(plan_path, 65536) and raw == read_private(snapshot_path, plan.max_bytes),
            "CLIENT_CONFIG_SOURCE_CHANGED")
    return {"schema": "strata/ClientConfigInspection/1", "visibility": "evaluator",
            "inspection": "pass", "campaign_id": plan.campaign_id, "epoch": plan.epoch,
            "inputs": {"plan_sha256": snapshot.plan_sha256,
                       "snapshot_sha256": hashlib.sha256(raw).hexdigest()},
            "observation": snapshot.model_dump(mode="json", by_alias=True, exclude_unset=True),
            "scoring_eligible": False, "pack_lock_qualified": False, "gate_result": "not_run",
            "unresolved": ["authenticated_process_and_artifact_binding", "client_server_role_comparison",
                           "consumer_cache_and_mechanics_equivalence", "cold_restart_equivalence",
                           "instrumentation_parity", "enforced_gameplay_isolation"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    require(not args.output.exists(), "CLIENT_CONFIG_REPORT_EXISTS")
    report = inspect_client_configs(args.plan, args.snapshot)
    print(json.dumps(write_report(args.output, report)))


if __name__ == "__main__":
    main()
