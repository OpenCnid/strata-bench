"""Synthetic journal/database/clock joins. Authentic evidence stays external."""

import hashlib
import json
import sqlite3

import pytest

from mcbench.storage import Fault, digest
from strata_evaluator.run_costs import CostJoin, inspect_costs
from test_telemetry import records, write


def compact(value):
    return json.dumps(value, separators=(",", ":"))


def build(tmp_path, example, fault=None):
    batch = example("ActionBatch") | {"campaign_id": "synthetic", "agent_id": "a1",
                                     "epoch": 1, "seq": 1, "is_example": False}
    authority = {"schema": "strata/NativeGameAuthority/1", "campaign_id": "synthetic", "agent_id": "a1",
                 "capability_digest": batch["capability_digest"], "body_fingerprint": "b" * 64,
                 "expires_unix_ms": 123456789, "primitive_limit": 100}
    binding = {"fingerprint": "a" * 64, "epoch": 1, "authority": authority,
               "identity": {"schema": "strata/NativeGameIdentity/1", "body_fingerprint": "b" * 64,
                            "connection_generation": 1}}
    source = "native:" + "a" * 64 + ":" + digest(authority)
    public = example("ActionAck") | {"campaign_id": "synthetic", "agent_id": "a1", "epoch": 1,
                                    "is_example": False, "action_seq": 1, "request_id": batch["request_id"],
                                    "status": "unknown", "requires_resync": True}
    receipt = {"schema": "strata/NativeGameActionReceipt/1", "request_id": batch["request_id"],
               "epoch": 1, "action_seq": 1, "status": "unknown", "attempted_events": 2,
               "emitted_events": None, "release_confirmed": False,
               "error_code": "PROCESS_INTERRUPTED", "requires_resync": True}
    # Independent spelling of the pinned Java record toString identity.
    identity = "Authority[campaign=synthetic, agent=a1, capability=" + batch["capability_digest"]
    identity += ", body=" + "b" * 64 + ", expires=123456789, primitiveLimit=100]"
    profile = hashlib.sha256(("a" * 64 + "\n" + identity).encode()).hexdigest()
    events = [{"kind": "profile", "identity": profile},
              {"kind": "lease", "wall_ms": 1, "epoch": 1, "lease_id": batch["lease_id"]},
              {"kind": "primitive", "wall_ms": 2, "request_id": None, "safety_release": True},
              {"kind": "intent", "wall_ms": 3, "batch_json": compact(batch)},
              {"kind": "primitive", "wall_ms": 4, "request_id": batch["request_id"], "safety_release": False},
              {"kind": "primitive", "wall_ms": 5, "request_id": batch["request_id"], "safety_release": True},
              {"kind": "terminal", "wall_ms": 6, "receipt": receipt}]
    if fault == "unattributed":
        events[2]["safety_release"] = False
    if fault == "replay":
        events.insert(5, events[3] | {"wall_ms": 4})
    if fault == "receipt":
        receipt["attempted_events"] = 1
    if fault == "profile":
        events[0]["identity"] = "c" * 64
    if fault == "incomplete":
        events.pop()
    native = tmp_path / "native.jsonl"
    previous = "0" * 64
    lines = []
    for sequence, payload in enumerate(events, 1):
        checksum = hashlib.sha256((previous + "\n" + compact(payload)).encode()).hexdigest()
        lines.append(compact({"schema": "strata/NativeGameJournalFrame/1", "seq": sequence,
                              "previous": previous, "payload": payload, "sha256": checksum}) + "\n")
        previous = checksum
    native.write_text("".join(lines), encoding="utf-8")
    if fault == "partial":
        native.write_bytes(native.read_bytes()[:-1])
    if fault == "hash":
        native.write_bytes(native.read_bytes().replace(b'"wall_ms":4', b'"wall_ms":7'))
    database = tmp_path / "worker.sqlite"
    db = sqlite3.connect(database)
    db.executescript("CREATE TABLE epochs(epoch INTEGER); INSERT INTO epochs VALUES(1);"
                     "CREATE TABLE actions(request_id TEXT,epoch INTEGER,seq INTEGER,digest TEXT,request TEXT,ack TEXT);"
                     "CREATE TABLE events(cursor INTEGER PRIMARY KEY,kind TEXT,body TEXT);"
                     "CREATE TABLE counters(name TEXT,value INTEGER);")
    db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?)", (batch["request_id"], 1, 1, digest(batch),
                                                          compact(batch), compact(public)))
    db.execute("INSERT INTO events(kind,body) VALUES('native_binding',?)", (compact(binding),))
    # Repeated and out-of-order observations do not charge the high-water mark twice.
    for attempted, delta in [(0, 0), (2, 2), (1, 0), (3, 1), (3, 0)]:
        if fault == "delta" and attempted == 1:
            delta = 1
        value = {"epoch": 1, "source": source, "attempted_primitive_events": attempted, "charged_delta": delta}
        db.execute("INSERT INTO events(kind,body) VALUES('native_usage',?)", (compact(value),))
    db.executemany("INSERT INTO counters VALUES(?,?)", [(source, 3), ("primitive_events", 2 if fault == "counter" else 3)])
    if fault == "epoch":
        db.execute("INSERT INTO epochs VALUES(2)")
    db.commit()
    db.close()
    if fault == "wal":
        (tmp_path / "worker.sqlite-wal").write_bytes(b"pending")
    spool = tmp_path / "server.jsonl"
    values = records(example)
    if fault == "server_scope":
        for value in values:
            value["campaign_id"] = "other"
    write(spool, values)
    files = {key: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for key, path in [("native_journal", native), ("worker_database", database), ("server_spool", spool)]}
    plan = CostJoin.model_validate({"schema": "strata/DevelopmentCostJoin/1", "evidence_kind": "synthetic",
                                   "campaign_id": "synthetic", "agent_id": "a1", "epoch": 1, **files})
    if fault == "pin":
        native.write_bytes(native.read_bytes() + b" ")
    return plan


def test_exact_cross_journal_charges_keep_unknowns_and_unqualified_clock_gaps(tmp_path, example):
    plan = build(tmp_path, example)
    before = [item.checked().read_bytes() for item in (plan.native_journal, plan.worker_database, plan.server_spool)]
    result = inspect_costs(plan)
    assert result["reconciliation"] == "pass" and result["evidence_kind"] == "synthetic"
    assert result["primitive_events"] == 3 and result["unattributed_safety_releases"] == 1
    assert len(result["unknown_requests"]) == 1
    assert result["sampled_server_ticks"] == 20 and result["last_server_tick"] == 30
    assert result["sampled_server_wall_ns"] == 1000000000
    assert not result["complete_project_accounting"] and not result["scoring_eligible"]
    assert result["gate_result"] == "not_run" and "root_helper_retry_inference_join" in result["unresolved"]
    assert before == [item.checked().read_bytes() for item in (plan.native_journal, plan.worker_database, plan.server_spool)]


@pytest.mark.parametrize("fault,code", [
    ("unattributed", "COST_PRIMITIVE_UNATTRIBUTED"), ("replay", "COST_INTENT_BINDING"),
    ("receipt", "COST_RECEIPT_BINDING"), ("profile", "COST_NATIVE_PROFILE"),
    ("incomplete", "COST_ACTION_INCOMPLETE"), ("partial", "COST_NATIVE_PARTIAL"),
    ("hash", "COST_NATIVE_HASH"), ("delta", "COST_USAGE_DELTA"),
    ("counter", "COST_COUNTER_MISMATCH"), ("epoch", "COST_SCOPE_MISMATCH"),
    ("wal", "COST_DATABASE_NOT_FROZEN"), ("server_scope", "TELEMETRY_SCOPE_MISMATCH"),
    ("pin", "COST_INPUT_CHANGED"),
])
def test_missing_corrupt_mixed_and_double_counted_evidence_rejects(tmp_path, example, fault, code):
    with pytest.raises(Fault, match=code):
        inspect_costs(build(tmp_path, example, fault))
