"""Synthetic selected-config events; actual Forge evidence remains private."""

import copy

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_configs import ConfigQuery, ConfigSnapshot
from test_telemetry import records, write


def snapshot():
    return {"file_name": "fixture-common.toml", "status": "snapshot", "mod_id": "fixture",
            "config_type": "COMMON", "consistency": "matching_consecutive_reads",
            "values": [{"path": ["quoted.key", "items"], "declared": True,
                        "present": True, "value": [True, 1, 1.0, "text"]},
                       {"path": ["absent"], "declared": False, "present": False}]}


def config_records(example):
    values = records(example)
    values[0]["payload_schema"] = "strata/ServerStarted/2"
    values[0]["payload"]["module"] = "strata-forge1192-telemetry/0.2.0"
    values[0]["payload"]["config_queries"] = [{"file_name": "fixture-common.toml",
                                               "paths": [["quoted.key", "items"], ["absent"]]}]
    config = values[1] | {"kind": "config_snapshot", "payload_schema": "strata/ConfigSnapshot/1",
                          "payload": snapshot(), "server_tick": 1}
    values.insert(2, config)
    return resequence(values)


def resequence(values):
    for i, value in enumerate(values, 1):
        value["seq"] = value["server_event_seq"] = i
    return values


def test_selected_config_round_trip_retains_types_and_no_gate_claim(tmp_path, example):
    values = config_records(example)
    path = tmp_path / "spool.jsonl"
    write(path, values)
    report = inspect_spool(path, "synthetic", 1)
    assert report["config_snapshots"]["fixture-common.toml"] == snapshot()
    assert report["gate_result"] == "not_run" and not report["scoring_eligible"]
    assert report["config_queries"] == {"fixture-common.toml": [["quoted.key", "items"], ["absent"]]}
    for status in ("unregistered", "unloaded", "unsupported_spec", "unstable", "unsupported_value",
                   "read_failed", "quota_exceeded"):
        data = {"file_name": "fixture-common.toml", "status": status}
        if status != "unregistered":
            data |= {"mod_id": "fixture", "config_type": "COMMON"}
        values[2]["payload"] = data
        write(path, values)
        assert inspect_spool(path, "synthetic", 1)["config_snapshots"]["fixture-common.toml"] == data


def test_config_observation_cannot_earn_a_private_craft_score(example, database):
    from mcbench.records import GameEvent
    from strata_evaluator.scorer import Scorer
    from test_evaluator import predicate

    event = GameEvent.model_validate(config_records(example)[2])
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        Scorer(database).score("instance", predicate(), event)


@pytest.mark.parametrize("case", ["missing", "duplicate", "unrequested", "paths", "late", "order", "v1", "plan_duplicate"])
def test_missing_extra_reordered_and_unrequested_evidence_rejected(tmp_path, example, case):
    values = config_records(example)
    if case == "missing":
        values.pop(2)
    elif case == "duplicate":
        values.insert(3, copy.deepcopy(values[2]))
    elif case == "unrequested":
        values[2]["payload"]["file_name"] = "other.toml"
    elif case == "paths":
        values[2]["payload"]["values"].reverse()
    elif case == "late":
        values[2]["server_tick"] = 2
    elif case == "order":
        values[2], values[3] = values[3], values[2]
        values[3]["server_tick"] = 20
    elif case == "v1":
        values[0] = records(example)[0]
    else:
        plan = values[0]["payload"]["config_queries"]
        plan.append(copy.deepcopy(plan[0]))
    path = tmp_path / "spool.jsonl"
    write(path, resequence(values))
    with pytest.raises((Fault, ValidationError)):
        inspect_spool(path, "synthetic", 1)


@pytest.mark.parametrize("case", ["coerced", "present_missing", "absent_value", "unknown", "duplicate_path",
                                  "null_value", "object", "huge_int", "nan", "huge_string", "nodes", "depth", "bytes",
                                  "failed_values", "unregistered_metadata", "missing_metadata", "unknown_consistency"])
def test_payload_shape_types_and_quotas(case):
    data = snapshot()
    row = data["values"][0]
    if case == "coerced":
        row["declared"] = 1
    elif case == "present_missing":
        del row["value"]
    elif case == "absent_value":
        data["values"][1]["value"] = None
    elif case == "unknown":
        data["private_extra"] = True
    elif case == "duplicate_path":
        data["values"].append(copy.deepcopy(row))
    elif case in {"null_value", "object", "huge_int", "nan", "huge_string", "nodes", "depth", "bytes"}:
        nested = "x"
        for _ in range(9):
            nested = [nested]
        row["value"] = {"null_value": None, "object": {}, "huge_int": 9007199254740992,
                        "nan": float("nan"), "huge_string": "x" * 4097,
                        "nodes": [1] * 4096, "depth": nested, "bytes": ["x" * 4096] * 17}[case]
    elif case == "failed_values":
        data["status"] = "read_failed"
    elif case == "unregistered_metadata":
        data = {"file_name": "fixture.toml", "status": "unregistered", "mod_id": None}
    elif case == "missing_metadata":
        del data["mod_id"]
    else:
        data["consistency"] = "atomic"
    with pytest.raises((Fault, ValidationError)):
        ConfigSnapshot.model_validate(data)


@pytest.mark.parametrize("name,paths", [("../config.toml", [["x"]]), ("CONFIG.toml", [["x"]]),
    ("x.toml", []), ("x.toml", [[]]), ("x.toml", [["x"]] * 2), ("x.toml", [["x"] * 17]),
    ("x.toml", [["x" * 129]]), ("x.toml", [["\n"]]), ("x.toml", [["界"]])])
def test_query_selectors_are_bounded_exact_key_arrays(name, paths):
    with pytest.raises((Fault, ValidationError)):
        ConfigQuery(file_name=name, paths=paths)
