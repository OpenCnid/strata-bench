"""Synthetic journal restoration; no Minecraft, provider or desktop input."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess

from pydantic import ValidationError
import pytest

from mcbench.inventory import file_hash
from mcbench.pack_worker import HeldPackWorker
from mcbench.storage import Fault, canonical
from mcbench.worker_journal_restore import HeldRestoredJournal, WorkerJournalSource, inspect_journal
from test_native_game_evidence import worker_fixture
import test_pack_worker as worker_tests

inputs = worker_tests.inputs
candidate = worker_tests.candidate
pack = worker_tests.pack


@pytest.fixture
def journal(example, tmp_path):
    """Actual worker schema, populated by independent synthetic receipt fixtures."""
    directory = tmp_path / "source"
    directory.mkdir()
    path = directory / "actions.sqlite"
    fixture, *_ = worker_fixture(example, traced=True)
    with closing(fixture), closing(sqlite3.connect(path)) as db:
        db.executescript("CREATE TABLE epochs(epoch INTEGER PRIMARY KEY);"
            "CREATE TABLE actions(request_id TEXT PRIMARY KEY, epoch INTEGER NOT NULL,"
            "seq INTEGER NOT NULL, digest TEXT NOT NULL, request TEXT NOT NULL, ack TEXT NOT NULL, UNIQUE(epoch,seq));"
            "CREATE TABLE events(cursor INTEGER PRIMARY KEY,kind TEXT NOT NULL,body TEXT NOT NULL);"
            "CREATE TABLE counters(name TEXT PRIMARY KEY,value INTEGER NOT NULL);")
        for table in ("epochs", "actions", "events", "counters"):
            # Node stores JSON as SQLite TEXT, not Python's bytes/BLOB binding.
            rows = [tuple(v.decode() if isinstance(v, bytes) else v for v in r)
                    for r in fixture.execute(f"SELECT * FROM {table}")]
            db.executemany(f"INSERT INTO {table} VALUES({','.join('?' for _ in rows[0])})", rows)
        db.commit()
    (directory / "grant-1.json").write_bytes(b"synthetic obsolete grant; must not copy")
    target = tmp_path / "target"
    target.mkdir()
    reference = {"path": str(path), "sha256": file_hash(path), "campaign_id": "c1", "agent_id": "a1", "epoch": 1}
    config = {"state_directory": str(target), "campaign_id": "c1", "agent_id": "a1", "epoch": 2, "primitive_limit": 10}
    return reference, config


def test_restore_keeps_exact_bytes_and_holds_them_until_one_use_handoff(journal):
    reference, config = journal
    original = Path(reference["path"]).read_bytes()
    held = HeldRestoredJournal(reference, config)
    try:
        assert held.target.read_bytes() == original
        assert {p.name for p in held.target.parent.iterdir()} == {"actions.sqlite"}
        with pytest.raises(PermissionError):
            held.target.open("r+b")
        with pytest.raises(Fault, match="WORKER_JOURNAL_NOT_DISPATCHED"):
            held.receipt()
        held.handoff()
        receipt = held.receipt()
        assert receipt["retained"] == {"epochs": [1], "action_rows": 1, "event_rows": 6, "primitive_events": 1}
        assert receipt["held_until_launch_handoff"] and not receipt["old_grant_restored"]
        assert not receipt["writer_custody_qualified"]
        with held.target.open("r+b"):
            pass
        with pytest.raises(Fault, match="WORKER_JOURNAL_ALREADY_DISPATCHED"):
            held.handoff()
    finally:
        held.close()
    assert Path(reference["path"]).read_bytes() == original


def test_windows_extended_archive_path_can_be_read_without_becoming_a_uri_host(journal):
    reference, config = journal
    reference["path"] = "\\\\?\\" + reference["path"]
    held = HeldRestoredJournal(reference, config)
    try:
        held.handoff()
        assert held.receipt()["retained"]["primitive_events"] == 1
    finally:
        held.close()


@pytest.mark.parametrize("change", ["campaign", "agent", "same-epoch", "skip-epoch", "exhausted", "over-limit", "occupied"])
def test_scope_or_budget_failure_cannot_copy_state(journal, change):
    reference, config = journal
    if change in {"campaign", "agent"}:
        config[change + "_id"] = "unrelated"
    elif change in {"same-epoch", "skip-epoch"}:
        config["epoch"] = 1 if change == "same-epoch" else 3
    elif change in {"exhausted", "over-limit"}:
        config["primitive_limit"] = 1 if change == "exhausted" else 0
    else:
        (Path(config["state_directory"]) / "preserve.txt").write_bytes(b"old state")
    before = Path(reference["path"]).read_bytes()
    with pytest.raises(Fault):
        HeldRestoredJournal(reference, config)
    assert not (Path(config["state_directory"]) / "actions.sqlite").exists()
    assert Path(reference["path"]).read_bytes() == before


@pytest.mark.parametrize("sidecar", ["actions.sqlite-wal", "actions.sqlite-shm", "actions.sqlite-journal", "executor.lock"])
def test_live_or_uncertain_source_is_never_restored(journal, sidecar):
    reference, config = journal
    (Path(reference["path"]).parent / sidecar).write_bytes(b"retained uncertainty")
    with pytest.raises(Fault, match="WORKER_JOURNAL_NOT_STOPPED"):
        HeldRestoredJournal(reference, config)
    assert not any(Path(config["state_directory"]).iterdir())


def test_frozen_source_sidecars_are_held_recorded_and_left_in_the_source(journal):
    reference, config = journal
    source = Path(reference["path"])
    originals = {"-wal": b"", "-shm": b"\0" * 32768, "-journal": b""}
    for suffix, content in originals.items():
        Path(str(source) + suffix).write_bytes(content)
    held = HeldRestoredJournal(reference, config)
    try:
        held.handoff()
        receipt = held.receipt()
        assert set(receipt["source_sidecars"]) == set(originals) and not receipt["sidecars_copied"]
        assert {p.name for p in held.target.parent.iterdir()} == {"actions.sqlite"}
        assert held.target.read_bytes() == source.read_bytes()
    finally:
        held.close()
    for suffix, content in originals.items():
        assert Path(str(source) + suffix).read_bytes() == content


@pytest.mark.parametrize("change", ["hash", "table", "trigger", "future-epoch", "no-actions", "digest", "scope",
    "uncertain", "resync", "unreleased", "example", "negative", "refund", "charge-gap", "charge-bool", "event-gap",
    "unknown-event", "event-scope", "event-bool", "event-body", "action-blob", "event-blob"])
def test_pinned_but_invalid_journals_fail_closed(journal, change):
    reference, config = journal
    with closing(sqlite3.connect(reference["path"])) as db:
        if change == "table":
            db.execute("CREATE TABLE unreviewed(value TEXT)")
        elif change == "trigger":
            db.execute("CREATE TRIGGER hidden AFTER INSERT ON epochs BEGIN DELETE FROM actions; END")
        elif change == "future-epoch":
            db.execute("INSERT INTO epochs VALUES(2)")
        elif change == "no-actions":
            db.execute("DELETE FROM actions")
        elif change == "digest":
            db.execute("UPDATE actions SET digest=?", ("a"*64,))
        elif change == "action-blob":
            db.execute("UPDATE actions SET request=CAST(request AS BLOB)")
        elif change == "event-blob":
            db.execute("UPDATE events SET body=CAST(body AS BLOB)")
        elif change in {"scope", "uncertain", "resync", "unreleased", "example"}:
            ack = json.loads(db.execute("SELECT ack FROM actions").fetchone()[0])
            ack.update({"scope": {"campaign_id": "sibling"}, "uncertain": {"status": "unknown"},
                "resync": {"requires_resync": True}, "unreleased": {"release_confirmed": False},
                "example": {"is_example": True}}[change])
            db.execute("UPDATE actions SET ack=?", (canonical(ack).decode(),))
        elif change in {"negative", "refund"}:
            db.execute("UPDATE counters SET value=? WHERE name='primitive_events'", (-1 if change == "negative" else 0,))
        elif change in {"charge-gap", "charge-bool", "event-scope", "event-bool", "event-body"}:
            body = json.loads(db.execute("SELECT body FROM events WHERE kind='primitive_charge'").fetchone()[0])
            body.update({"charge-gap": {"charge_seq": 2}, "charge-bool": {"charge_seq": True},
                "event-scope": {"campaign_id": "sibling"}, "event-bool": {"epoch": True}, "event-body": {}}[change])
            db.execute("UPDATE events SET body=? WHERE kind='primitive_charge'", (canonical([] if change == "event-body" else body).decode(),))
        elif change == "event-gap":
            db.execute("DELETE FROM events WHERE cursor=2")
        elif change == "unknown-event":
            db.execute("UPDATE events SET kind='unreviewed' WHERE cursor=2")
        db.commit()
    reference["sha256"] = "f"*64 if change == "hash" else file_hash(Path(reference["path"]))
    with pytest.raises((Fault, ValidationError)):
        HeldRestoredJournal(reference, config)
    assert not any(Path(config["state_directory"]).iterdir())


@pytest.mark.parametrize("change", ["extra-file", "closed-handle"])
def test_target_change_or_abandoned_handoff_cannot_launch(journal, change):
    reference, config = journal
    held = HeldRestoredJournal(reference, config)
    try:
        if change == "extra-file":
            (held.target.parent / "grant-1.json").write_bytes(b"obsolete")
        else:
            held.close()
        with pytest.raises(Fault):
            held.handoff()
        assert not held.dispatched
    finally:
        held.close()
    assert held.target.read_bytes() == Path(reference["path"]).read_bytes()


def test_actual_node_journal_opens_next_epoch_without_replaying_or_refunding(journal):
    reference, config = journal
    root = Path(__file__).resolve().parents[1]
    node = Path("C:/Program Files/nodejs/node.exe")
    module = root / "backends/mineflayer/dist/src/journal.js"
    assert node.is_file() and module.is_file(), "This Windows/Node interoperability check requires the pinned local build"
    old = Path(reference["path"]).read_bytes()
    held = HeldRestoredJournal(reference, config)
    try:
        held.handoff()
        script = ("import {Journal} from " + json.dumps(module.as_uri()) + ";"
            "const j=new Journal(process.argv[1],2);"
            "try {j.beginPrimitiveAccounting({campaign_id:'c1',agent_id:'a1',epoch:2});"
            "process.stdout.write(JSON.stringify({old:j.status('request1'),cost:j.counter('primitive_events'),"
            "newActions:j.counter('2:action')}));} finally {j.close();}")
        completed = subprocess.run([str(node), "--input-type=module", "-e", script, config["state_directory"]],
            capture_output=True, timeout=20, check=True)
        result = json.loads(completed.stdout)
        assert result["old"]["epoch"] == 1 and result["old"]["status"] == "completed"
        assert result["cost"] == 1 and result["newActions"] == 0
        with closing(sqlite3.connect(held.target)) as db:
            assert list(db.execute("SELECT epoch FROM epochs ORDER BY epoch")) == [(1,), (2,)]
            body = json.loads(db.execute("SELECT body FROM events ORDER BY cursor DESC LIMIT 1").fetchone()[0])
            assert body["epoch"] == 2 and body["opening_primitive_events"] == 1
            assert db.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 1
    finally:
        held.close()
    assert Path(reference["path"]).read_bytes() == old
    assert {p.name for p in held.target.parent.iterdir()} == {"actions.sqlite"}


@pytest.mark.parametrize("failure", [None, "construction"])
def test_pack_launch_consumes_restoration_once_and_requires_a_real_worker_receipt(pack, journal, monkeypatch, failure):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    reference, _ = journal
    invocation |= {"campaign_id": "c1", "agent_id": "a1", "epoch": 2}
    calls = []
    factory = worker_tests.fake_process_factory(calls)
    def create(*args, **kwargs):
        if failure and calls:
            raise OSError("synthetic worker construction failure")
        return factory(*args, **kwargs)
    monkeypatch.setattr(module, "ManagedProcess", create)
    with HeldPackWorker(binding, invocation) as worker:
        with pytest.raises(Fault, match="WORKER_JOURNAL_ORDER"):
            worker.restore_journal(reference)
        worker.start(preflight=True)
        worker.restore_journal(reference)
        with pytest.raises(Fault, match="WORKER_JOURNAL_ORDER"):
            worker.restore_journal(reference)
        with pytest.raises(Fault, match="WORKER_LAUNCH_STOP_UNPROVEN"):
            worker.receipt()
        if failure:
            with pytest.raises(OSError, match="synthetic worker construction failure"):
                worker.start()
            with pytest.raises(Fault, match="WORKER_JOURNAL_ALREADY_DISPATCHED"):
                worker.start()
            with pytest.raises(Fault, match="WORKER_LAUNCH_STOP_UNPROVEN"):
                worker.receipt()
        else:
            worker.start()
            receipt = worker.receipt()
            assert receipt["schema"] == "strata/HeldPackWorker/2"
            assert receipt["journal_restoration"]["source"] == reference
            inspect_journal(Path(invocation["state_directory"]) / "actions.sqlite", WorkerJournalSource.model_validate(reference))
    assert all(call[0].closed for call in calls)


@pytest.mark.parametrize("failure", ["active", "forced", "nonzero"])
def test_preflight_must_have_a_proven_normal_stop_before_restoring(pack, journal, monkeypatch, failure):
    import mcbench.pack_worker as module
    binding, invocation, _ = pack
    reference, _ = journal
    invocation |= {"campaign_id": "c1", "agent_id": "a1", "epoch": 2}
    monkeypatch.setattr(module, "ManagedProcess", worker_tests.fake_process_factory([]))
    with HeldPackWorker(binding, invocation) as worker:
        process = worker.start(preflight=True)
        process.code = 1 if failure == "nonzero" else 0
        process.job.accounting = lambda: {"active_processes": int(failure == "active"),
            "terminated_processes": int(failure == "forced"), "total_processes": 1}
        with pytest.raises(Fault, match="WORKER_JOURNAL_ORDER"):
            worker.restore_journal(reference)
        assert not any(Path(invocation["state_directory"]).iterdir())
