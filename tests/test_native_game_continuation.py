"""Synthetic two-epoch controls, including tampering with retained history."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from pydantic import ValidationError
import pytest

from mcbench.storage import Fault, canonical, digest
from mcbench.budgets import Budgets, DIMENSIONS
from strata_evaluator.native_game_continuation import cumulative_usage, native_history, source_record
from strata_evaluator.native_game_evidence import NativeGameRecoveryEvidencePlan, private_report_output, worker_evidence
from test_native_game_evidence import worker_fixture


def clone(db):
    db.commit()
    result = sqlite3.connect(":memory:")
    result.row_factory = sqlite3.Row
    db.backup(result)
    return result


def rewritten(value):
    if isinstance(value, list):
        return [rewritten(v) for v in value]
    if isinstance(value, dict):
        return {k: 2 if k == "epoch" else rewritten(v) for k, v in value.items()}
    return {"request1": "request2", "lease1": "lease2", "job": "job-2"}.get(value, value) if isinstance(value, str) else value


@pytest.fixture
def continued(example):
    old, source, plan, config = worker_fixture(example, traced=True)
    db = clone(old)
    db.execute("INSERT INTO epochs VALUES(2)")
    row = old.execute("SELECT * FROM actions").fetchone()
    batch, ack = rewritten(json.loads(row["request"])), rewritten(json.loads(row["ack"]))
    db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?)", ("request2", 2, 1, digest(batch), canonical(batch), canonical(ack)))
    for row in old.execute("SELECT * FROM events ORDER BY cursor"):
        body = rewritten(json.loads(row["body"]))
        if row["kind"] == "primitive_accounting":
            body["opening_primitive_events"] = 1
        elif row["kind"] == "primitive_charge":
            body |= {"charge_seq": 2, "request_digest": digest(batch)}
        db.execute("INSERT INTO events(kind,body) VALUES(?,?)", (row["kind"], canonical(body)))
    db.execute("UPDATE counters SET value=2 WHERE name='primitive_events'")
    db.executemany("INSERT INTO counters VALUES(?,?)", [("2:action", 1), ("2:ack", 2), ("2:observation", 2)])
    for call, broker in zip(source["game_calls"], source["broker_calls"]):
        call["runtime"] = "job-2"
        response = rewritten(json.loads(call["result"]))
        call["result"] = canonical(response)
        call["request_body"] = rewritten(call["request_body"])
        call["fingerprint"] = digest(call["request_body"])
        broker["result_digest"] = digest(response)
    plan = NativeGameRecoveryEvidencePlan.model_validate(plan.model_dump() | {
        "schema": "strata/NativeGameEvidencePlan/2", "epoch": 2, "job_id": "job-2", "previous": plan.model_dump()})
    yield db, old, source, plan, config | {"lease_id": "lease2"}
    db.close()
    old.close()


def test_new_epoch_is_reconciled_only_after_exact_history_preservation(continued):
    db, old, source, plan, config = continued
    result, _, observations = worker_evidence(db, source, plan, config, previous=old)
    assert result["opening_primitive_events"] == result["primitive_events"] == 1
    assert result["cumulative_primitive_events"] == 2 and result["primitive_trace_verified"]
    assert result["retained_history"] == {"opening_primitive_events": 1, "worker_events": 6, "worker_actions": 1}
    assert result["actions"][0]["request_id"] == "request2" and len(observations) == 2
    assert db.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 2
    assert old.execute("SELECT value FROM counters WHERE name='primitive_events'").fetchone()[0] == 1


@pytest.mark.parametrize("change", ["old-action", "delete-action", "old-event", "delete-event", "old-counter",
    "refund", "opening", "charge-seq", "extra-epoch", "unregistered-epoch", "extra-counter", "duplicate-counter",
    "new-schema", "fake-signal", "old-scope", "budget", "missing-parent"])
def test_corrupt_or_refunded_history_cannot_be_hidden_by_the_new_epoch(continued, change):
    db, old, source, plan, config = continued
    if change == "old-action":
        db.execute("UPDATE actions SET digest=? WHERE epoch=1", ("f"*64,))
    elif change == "delete-action":
        db.execute("DELETE FROM actions WHERE epoch=1")
    elif change == "old-event":
        db.execute("UPDATE events SET body='{}' WHERE cursor=1")
    elif change == "delete-event":
        db.execute("DELETE FROM events WHERE cursor=1")
    elif change in {"old-counter", "refund"}:
        db.execute("UPDATE counters SET value=0 WHERE name=?", ("1:action" if change == "old-counter" else "primitive_events",))
    elif change in {"opening", "charge-seq", "old-scope"}:
        cursor, key, value = {"opening": (7, "opening_primitive_events", 0),
            "charge-seq": (10, "charge_seq", 1), "old-scope": (8, "epoch", 1)}[change]
        body = json.loads(db.execute("SELECT body FROM events WHERE cursor=?", (cursor,)).fetchone()[0])
        body[key] = value
        db.execute("UPDATE events SET body=? WHERE cursor=?", (canonical(body), cursor))
    elif change == "extra-epoch":
        db.execute("INSERT INTO epochs VALUES(3)")
    elif change == "unregistered-epoch":
        db.execute("UPDATE actions SET epoch=3 WHERE epoch=2")
    elif change == "extra-counter":
        db.execute("INSERT INTO counters VALUES('hidden:counter',1)")
    elif change == "duplicate-counter":
        db.execute("INSERT INTO counters VALUES('primitive_events',2)")
    elif change == "new-schema":
        db.execute("CREATE TABLE discarded_history(value TEXT)")
    elif change == "fake-signal":
        db.execute("INSERT INTO events(kind,body) VALUES('public_signal',?)", (canonical({"cursor": 2}),))
    elif change == "budget":
        config["primitive_limit"] = 1
    with pytest.raises(Fault):
        worker_evidence(db, source, plan, config, previous=None if change == "missing-parent" else old)


@pytest.fixture
def native_pair():
    old = sqlite3.connect(":memory:")
    old.row_factory = sqlite3.Row
    for table in ("accounts", "campaigns", "native_retention_policies", "execution_authorizations", "native_jobs", "operations"):
        old.execute(f"CREATE TABLE {table}(id TEXT PRIMARY KEY,value TEXT)")
        old.execute(f"INSERT INTO {table} VALUES('old','immutable retained state')")
    old.execute("CREATE TABLE ledger(body TEXT)")
    old.execute("INSERT INTO ledger VALUES('old charge')")
    old.execute("CREATE TABLE private_history(value TEXT)")
    old.execute("INSERT INTO private_history VALUES('old private evidence')")
    db = clone(old)
    db.execute("INSERT INTO native_jobs VALUES('new','new run')")
    db.execute("INSERT INTO operations VALUES('new','new operation')")
    db.execute("INSERT INTO ledger VALUES('new charge')")
    db.execute("CREATE TABLE native_recovery_projections (runtime TEXT, thread TEXT, component TEXT, PRIMARY KEY(runtime,thread))")
    source = {"operations": [{"id": "new"}], "ledger": [{"cursor": 2}]}
    yield old, db, SimpleNamespace(job_id="new"), source
    old.close()
    db.close()


def test_every_old_native_row_and_ledger_position_survives(native_pair):
    old, db, native, source = native_pair
    assert native_history(db, old, native, source) == {"native_tables": 8, "native_rows": 8, "ledger_rows": 1}


@pytest.mark.parametrize("change", ["old-row", "delete-row", "account-increase", "new-account", "policy", "schema",
    "trigger", "third-job", "unattributed-operation", "unattributed-ledger", "ledger-position"])
def test_retained_native_or_accounting_corruption_blocks_reconciliation(native_pair, change):
    old, db, native, source = native_pair
    if change == "old-row":
        db.execute("UPDATE private_history SET value='altered'")
    elif change == "delete-row":
        db.execute("DELETE FROM private_history")
    elif change == "account-increase":
        db.execute("UPDATE accounts SET value='larger allowance'")
    elif change == "new-account":
        db.execute("INSERT INTO accounts VALUES('new','fresh allowance')")
    elif change == "policy":
        db.execute("INSERT INTO native_retention_policies VALUES('new','replacement baseline')")
    elif change == "schema":
        db.execute("CREATE TABLE extra(value TEXT)")
    elif change == "trigger":
        db.execute("CREATE TRIGGER hidden AFTER INSERT ON ledger BEGIN DELETE FROM private_history; END")
    elif change == "third-job":
        db.execute("INSERT INTO native_jobs VALUES('sibling','unaccounted')")
    elif change == "unattributed-operation":
        db.execute("INSERT INTO operations VALUES('sibling','unaccounted')")
    elif change == "unattributed-ledger":
        db.execute("INSERT INTO ledger VALUES('unaccounted')")
    else:
        db.execute("UPDATE ledger SET rowid=3 WHERE rowid=1")
    with pytest.raises(Fault):
        native_history(db, old, native, source)


def test_recovery_input_requires_explicit_nonrecursive_parent(continued):
    _, _, _, plan, _ = continued
    raw = plan.model_dump()
    raw["previous"]["previous"] = dict(raw["previous"])
    with pytest.raises(ValidationError):
        NativeGameRecoveryEvidencePlan.model_validate(raw)


@pytest.mark.parametrize("target", ["current", "previous", "repository", "existing", "allowed"])
def test_report_output_normalizes_traversal_before_protecting_both_archives(continued, tmp_path, target):
    *_, plan, _ = continued
    plan.bundle = str(tmp_path / "current")
    plan.previous.bundle = str(tmp_path / "previous")
    Path(plan.bundle).mkdir()
    Path(plan.previous.bundle).mkdir()
    via = tmp_path / "via"
    via.mkdir()
    if target == "repository":
        output = Path(__file__).resolve().parents[1] / "unmade-subdir/../never-write-report.json"
    elif target == "existing":
        output = tmp_path / "existing.json"
        output.write_bytes(b"preserve")
    else:
        output = via / ".." / target / "report.json"
    if target == "allowed":
        assert private_report_output(output, plan) == tmp_path / "allowed/report.json"
    else:
        with pytest.raises(Fault, match="EVIDENCE_OUTPUT_PRIVATE"):
            private_report_output(output, plan)


def test_journal_verification_does_not_write_a_live_copy(continued, tmp_path):
    db, old, source, plan, config = continued
    before = [tuple(r) for r in db.execute("SELECT * FROM events")]
    with closing(clone(db)) as snapshot:
        worker_evidence(snapshot, source, plan, config, previous=old)
        assert [tuple(r) for r in snapshot.execute("SELECT * FROM events")] == before
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("change", [None, "refund", "old-uncertainty", "new-uncertainty", "unreported-cost", "opening-report", "units"])
def test_cumulative_costs_use_actual_budget_operations(database, change):
    budgets = Budgets(database)
    budgets.create_account("account", {k: 1000 for k in DIMENSIONS}, "c1", "a1")
    old = database.connection
    amount = dict.fromkeys(DIMENSIONS, 0) | {"input_tokens": 10, "output_tokens": 4, "model_calls": 1, "spend_microusd": 14}
    old.execute("INSERT INTO operations VALUES('old','account',NULL,'model',?,?,0)",
                (canonical(amount).decode(), canonical(amount).decode()))
    with closing(clone(old)) as db:
        db.execute("INSERT INTO operations VALUES('new','account',NULL,'model',?,?,0)",
                    (canonical(amount).decode(), canonical(amount).decode()))
        prior = {"unit": "synthetic_fixture_units", "totals": {"input_tokens": 10, "output_tokens": 4,
                 "model_calls": 1, "amount": 14, "cached_input_tokens": 2, "request_wall_ms": 5}}
        current = {"unit": prior["unit"], "totals": dict(prior["totals"])}
        if change == "refund":
            db.execute("DELETE FROM operations WHERE id='old'")
        elif change == "old-uncertainty":
            old.execute("UPDATE operations SET uncertain=1 WHERE id='old'")
        elif change == "new-uncertainty":
            db.execute("UPDATE operations SET uncertain=1 WHERE id='new'")
        elif change == "unreported-cost":
            db.execute("UPDATE operations SET actual=? WHERE id='new'", (canonical(amount | {"primitive_events": 1}).decode(),))
        elif change == "opening-report":
            prior["totals"]["amount"] = 0
        elif change == "units":
            current["unit"] = "actual_dollars"
        if change:
            with pytest.raises(Fault):
                cumulative_usage(db, old, SimpleNamespace(account="account"), current, prior)
        else:
            assert cumulative_usage(db, old, SimpleNamespace(account="account"), current, prior) == {
                k: 2*v for k, v in prior["totals"].items()}


@pytest.mark.parametrize("change", [None, "component", "journal-hash", "copied-grant", "sidecar", "refund", "source-path"])
def test_sealed_handoff_joins_the_original_component_journal_and_inert_sidecars(continued, change):
    _, old, _, plan, _ = continued
    journal = "run/worker/actions.sqlite"
    reference = {"bundle": "C:/original/bundle", "seal_sha256": plan.previous.seal_sha256}
    prior_retention = {"component_ref": "cas:sha256:" + "a"*64, "snapshot_sha256": "b"*64}
    entry = SimpleNamespace(sha256="c"*64, bytes=100)
    sidecar = SimpleNamespace(sha256=digest({}), bytes=0)
    previous = SimpleNamespace(files={journal: entry, journal + "-wal": sidecar}, json=lambda _: {"status": "pass"})
    recorded = {"source": reference, "component": prior_retention["component_ref"], "original_outer_result": "pass",
        "world_snapshot": prior_retention["snapshot_sha256"], "epoch": 2, "worker_rows_preserved": 1,
        "full_checkpoint": False, "G0": "fail"}
    restoration = {"schema": "strata/WorkerJournalRestoration/1", "source": {"path": "C:/original/bundle/" + journal,
        "sha256": entry.sha256, "campaign_id": "c1", "agent_id": "a1", "epoch": 1},
        "retained": {"epochs": [1], "action_rows": 1, "event_rows": 6, "primitive_events": 1},
        "old_grant_restored": False, "source_sidecars": {"-wal": {"sha256": sidecar.sha256, "bytes": 0}},
        "sidecars_copied": False, "held_until_launch_handoff": True, "writer_custody_qualified": False}
    bodies = {"run/intent.json": {"plan": {"schema": "strata/M0NativeGameRecovery/3", "recovery_source": reference}},
        "run/recovery-source.json": recorded, "run/result.json": {"sealed_worker_receipt": {"journal_restoration": restoration}}}
    files = {"run/worker/grant-2.json"}
    if change == "component":
        recorded["component"] = "cas:sha256:" + "f"*64
    elif change == "journal-hash":
        restoration["source"]["sha256"] = "f"*64
    elif change == "copied-grant":
        files.add("run/worker/grant-1.json")
    elif change == "sidecar":
        restoration["source_sidecars"] = {}
    elif change == "refund":
        restoration["retained"]["primitive_events"] = 0
    elif change == "source-path":
        restoration["source"]["path"] = "C:/sibling/actions.sqlite"
    bundle = SimpleNamespace(json=lambda name: bodies[name], files=files)
    if change:
        with pytest.raises(Fault):
            source_record(bundle, previous, plan, old, prior_retention)
    else:
        source_record(bundle, previous, plan, old, prior_retention)
