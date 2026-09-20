"""Synthetic complete snapshots: retained unknowns, restart charges and tamper cases."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from mcbench.storage import Fault, digest
from strata_evaluator.run_costs import RestartCostJoin, inspect_restart_costs, main, native_records
from test_run_costs import build, compact
from test_telemetry import records, write


def pin(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def framed(path, values):
    previous, lines = "0" * 64, []
    for seq, value in enumerate(values, 1):
        checksum = hashlib.sha256((previous + "\n" + compact(value)).encode()).hexdigest()
        lines.append(compact({"schema": "strata/NativeGameJournalFrame/1", "seq": seq,
                              "previous": previous, "payload": value, "sha256": checksum}) + "\n")
        previous = checksum
    path.write_text("".join(lines), encoding="utf-8")


def pair(tmp_path, example, fault=None):
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir()
    two.mkdir()
    first = build(one, example).model_dump(mode="json", by_alias=True)
    database = Path(first["worker_database"]["path"])
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO events(kind,body) VALUES('operator_note',?)", (compact({"value": 1}),))
        db.execute("INSERT INTO counters VALUES('1:observe',7)")
        with sqlite3.connect(two / "worker.sqlite") as target:
            db.commit()
            db.backup(target)
    first["worker_database"] = pin(database)
    values = native_records(Path(first["native_journal"]["path"]))
    with sqlite3.connect(two / "worker.sqlite") as db:
        db.execute("INSERT INTO epochs VALUES(3)")  # Epochs increase; they need not be contiguous.
        binding = json.loads(db.execute("SELECT body FROM events WHERE kind='native_binding'").fetchone()[0])
        binding["epoch"] = 3
        binding["identity"]["connection_generation"] = 2
        if fault == "authority":
            binding["authority"]["expires_unix_ms"] += 1
        db.execute("INSERT INTO events(kind,body) VALUES('native_binding',?)", (compact(binding),))
        source = db.execute("SELECT name FROM counters WHERE name LIKE 'native:%'").fetchone()[0]
        for attempted, delta in [(3, 0), (4, 1), (5, 1), (5, 0), (4, 0)]:
            if fault == "double_charge" and attempted == 3:
                delta = 3
            usage = {"epoch": 3, "source": source,
                     "attempted_primitive_events": attempted, "charged_delta": delta}
            db.execute("INSERT INTO events(kind,body) VALUES('native_usage',?)", (compact(usage),))
        db.execute("UPDATE counters SET value=5 WHERE name IN (?, 'primitive_events')", (source,))
        batch, ack = [json.loads(v) for v in db.execute("SELECT request,ack FROM actions").fetchone()]
        batch.update(request_id="second-request", epoch=3, lease_id="second-lease")
        ack.update(request_id=batch["request_id"], epoch=3, status="emitted",
                   error_code=None, emitted_events=1, release_confirmed=True)
        db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?)", (batch["request_id"], 3, 1,
                                                               digest(batch), compact(batch), compact(ack)))
        if fault == "event_prefix":
            db.execute("UPDATE events SET body=? WHERE kind='operator_note'", (compact({"value": 2}),))
        if fault == "event_gap":
            db.execute("UPDATE events SET cursor=cursor+1000")
        if fault == "receipt":
            raw = json.loads(db.execute("SELECT ack FROM actions WHERE epoch=1").fetchone()[0])
            raw["seq"] += 1
            db.execute("UPDATE actions SET ack=? WHERE epoch=1", (compact(raw),))
        if fault == "counter":
            db.execute("UPDATE counters SET value=6 WHERE name='1:observe'")
        if fault == "missing_epoch":
            db.execute("DELETE FROM epochs WHERE epoch=1")
        if fault == "missing_action":
            db.execute("DELETE FROM actions WHERE epoch=1")
    receipt = {"schema": "strata/NativeGameActionReceipt/1", "request_id": batch["request_id"],
               "epoch": 3, "action_seq": 1, "status": "emitted", "attempted_events": 1,
               "emitted_events": 1, "release_confirmed": True, "error_code": None, "requires_resync": True}
    values += [{"kind": "lease", "wall_ms": 10, "epoch": 3, "lease_id": batch["lease_id"]},
               {"kind": "primitive", "wall_ms": 11, "request_id": None, "safety_release": True},
               {"kind": "intent", "wall_ms": 12, "batch_json": compact(batch)},
               {"kind": "primitive", "wall_ms": 13, "request_id": batch["request_id"], "safety_release": False},
               {"kind": "terminal", "wall_ms": 14, "receipt": receipt}]
    if fault == "native_prefix":
        values[1]["wall_ms"] = 0  # Internally valid history rewritten in the second snapshot.
    if fault == "replay":
        values.append(values[3] | {"wall_ms": 15})
    framed(two / "native.jsonl", values)
    telemetry = [v | {"epoch": 3, "server_boot_id": "boot" if fault == "boot" else "boot-two"}
                 for v in records(example)]
    write(two / "server.jsonl", telemetry)
    second = first | {"epoch": 3, "native_journal": pin(two / "native.jsonl"),
                      "worker_database": pin(two / "worker.sqlite"),
                      "server_spool": pin(two / "server.jsonl")}
    if fault == "mixed_kind":
        second["evidence_kind"] = "authentic_operator_reference"
    snapshots = [second, first] if fault == "order" else [first, second]
    return RestartCostJoin.model_validate({"schema": "strata/DevelopmentRestartCostJoin/1",
                                          "snapshots": snapshots})


def test_restart_keeps_unknown_and_charges_only_new_attempts(tmp_path, example):
    plan = pair(tmp_path, example)
    pins = [[v.checked().read_bytes() for v in (p.native_journal, p.worker_database, p.server_spool)]
            for p in plan.snapshots]
    report = inspect_restart_costs(plan)
    assert report["reconciliation"] == "pass" and report["epochs"] == [1, 3]
    assert report["primitive_events"] == 5  # Never 3 + cumulative 5.
    assert [r["new_primitive_events"] for r in report["snapshots"]] == [3, 2]
    assert report["unknown_requests"] == report["snapshots"][0]["unknown_requests"]
    assert len(report["unknown_requests"]) == 1
    assert report["sampled_server_ticks"] == 40 and report["sampled_server_wall_ns"] == 2000000000
    assert not report["scoring_eligible"] and not report["complete_project_accounting"]
    assert report["gate_result"] == "not_run"
    assert pins == [[v.checked().read_bytes() for v in (p.native_journal, p.worker_database, p.server_spool)]
                    for p in plan.snapshots]


@pytest.mark.parametrize("fault,code", [
    ("authority", "COST_RESTART_AUTHORITY_CHANGED"), ("double_charge", "COST_USAGE_DELTA"),
    ("event_prefix", "COST_RESTART_EVENT_PREFIX"), ("event_gap", "COST_EVENT_GAP"),
    ("receipt", "COST_RESTART_RECEIPT_CHANGED"), ("counter", "COST_RESTART_COUNTER_ROLLBACK"),
    ("missing_epoch", "COST_SCOPE_MISMATCH"), ("missing_action", "COST_INTENT_BINDING"),
    ("native_prefix", "COST_RESTART_NATIVE_PREFIX"), ("replay", "COST_INTENT_BINDING"),
    ("boot", "COST_RESTART_BOOT_REUSED"), ("mixed_kind", "COST_SCOPE_MISMATCH"),
    ("order", "COST_RESTART_ORDER"),
])
def test_restart_rejects_rewritten_or_refunded_history(tmp_path, example, fault, code):
    with pytest.raises(Fault, match=code):
        inspect_restart_costs(pair(tmp_path, example, fault))


def test_cli_dispatch_preserves_existing_output(tmp_path, example):
    plan = pair(tmp_path, example)
    source, output = tmp_path / "plan.json", tmp_path / "report.json"
    source.write_text(plan.model_dump_json(by_alias=True), encoding="utf-8")
    main(["--plan", str(source), "--output", str(output)])
    original = output.read_bytes()
    envelope = json.loads(original)
    assert envelope["report"]["primitive_events"] == 5
    assert envelope["content_digest"] == digest(envelope["report"])
    with pytest.raises(Fault, match="COST_REPORT_EXISTS"):
        main(["--plan", str(source), "--output", str(output)])
    assert output.read_bytes() == original


def test_prior_snapshot_wal_appearing_during_later_read_rejects(tmp_path, example, monkeypatch):
    from strata_evaluator import run_costs
    plan = pair(tmp_path, example)
    inspect = run_costs._inspect_costs

    def concurrent_write(snapshot, epochs):
        result = inspect(snapshot, epochs)
        if snapshot.epoch == 3:
            Path(plan.snapshots[0].worker_database.path + "-wal").write_bytes(b"pending")
        return result

    monkeypatch.setattr(run_costs, "_inspect_costs", concurrent_write)
    with pytest.raises(Fault, match="COST_DATABASE_NOT_FROZEN"):
        inspect_restart_costs(plan)
