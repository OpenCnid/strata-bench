"""One-use handoff of an externally pinned, stopped worker journal.

The caller verifies its parent game/agent bundle. This restores no old grant,
does not admit a campaign and does not claim exclusion of external writers.
"""

from contextlib import closing
import os
from pathlib import Path
import sqlite3

from .contracts import ActionAck, ActionBatch, Digest, Id, Positive, Strict
from .inference_transport import strict_json
from .inventory import file_hash
from .launch_integrity import FileLease, safe, snapshot
from .pack_launch import _absolute
from .storage import digest, require


class WorkerJournalSource(Strict):
    path: str
    sha256: Digest
    campaign_id: Id
    agent_id: Id
    epoch: Positive


def frozen_sidecars(path):
    """Keep inert SQLite remnants in the source; never ignore pending writes."""
    result = {}
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = safe(Path(str(path) + suffix))
        if sidecar.exists():
            require(sidecar.is_file() and sidecar.stat().st_nlink == 1
                    and sidecar.stat().st_size in ({0, 32768} if suffix == "-shm" else {0}),
                    "WORKER_JOURNAL_NOT_STOPPED")
            result[suffix] = {"bytes": sidecar.stat().st_size, "sha256": file_hash(sidecar)}
    require(not safe(path.parent / "executor.lock").exists(), "WORKER_JOURNAL_NOT_STOPPED")
    return result


def inspect_journal(path, source):
    path = _absolute(path)
    require(path.name == "actions.sqlite" and path.is_file() and path.stat().st_nlink == 1
            and path.stat().st_size <= 64 * 1024**2 and file_hash(path) == source.sha256,
            "WORKER_JOURNAL_CHANGED")
    frozen_sidecars(path)
    uri_path = Path(str(path).removeprefix("\\\\?\\")) if os.name == "nt" else path
    with closing(sqlite3.connect(uri_path.as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
        db.row_factory = sqlite3.Row
        require(db.execute("PRAGMA quick_check").fetchall()[0][0] == "ok", "WORKER_JOURNAL_CHANGED")
        objects = list(db.execute("SELECT type,name FROM sqlite_master"))
        require({r[1] for r in objects if r[0] == "table"} == {"epochs", "actions", "events", "counters"}
                and all(r[0] == "table" or r[0] == "index" and r[1].startswith("sqlite_autoindex_") for r in objects),
                "WORKER_JOURNAL_SCHEMA")
        epochs = [r[0] for r in db.execute("SELECT epoch FROM epochs ORDER BY epoch")]
        require(epochs and epochs == sorted(set(epochs))
                and all(type(e) is int and 0 < e <= source.epoch for e in epochs)
                and epochs[-1] == source.epoch, "WORKER_JOURNAL_SCOPE")
        actions = list(db.execute("SELECT * FROM actions ORDER BY epoch,seq"))
        require(0 < len(actions) <= 10000, "WORKER_JOURNAL_ACTIONS")
        for row in actions:
            require(isinstance(row["request"], str) and isinstance(row["ack"], str), "WORKER_JOURNAL_SCHEMA")
            request, ack = ActionBatch.model_validate(strict_json(row["request"])), ActionAck.model_validate(strict_json(row["ack"]))
            require(all(getattr(value, k) == getattr(source, k) for value in (request, ack)
                        for k in ("campaign_id", "agent_id")) and request.epoch == ack.epoch == row["epoch"]
                    and request.epoch in epochs and request.request_id == ack.request_id == row["request_id"]
                    and request.seq == ack.action_seq == row["seq"] and digest(request.model_dump()) == row["digest"]
                    and not request.is_example and not ack.is_example
                    and ack.status in {"completed", "emitted", "cancelled", "rejected"}
                    and (ack.status == "rejected" or ack.release_confirmed)
                    and not ack.requires_resync, "WORKER_JOURNAL_ACTIONS")
        counter_rows = list(db.execute("SELECT name,value FROM counters"))
        counters = dict(counter_rows)
        require(len(counters) == len(counter_rows)
                and all(type(v) is int and v >= 0 for v in counters.values()) and "primitive_events" in counters,
                "WORKER_JOURNAL_COUNTERS")
        events = list(db.execute("SELECT cursor,kind,body FROM events ORDER BY cursor"))
        require(len(events) <= 100000 and [e[0] for e in events] == list(range(1, len(events) + 1)),
                "WORKER_JOURNAL_EVENTS")
        charges = []
        for _, kind, raw in events:
            require(isinstance(raw, str), "WORKER_JOURNAL_SCHEMA")
            body = strict_json(raw)
            require(isinstance(body, dict)
                    and kind in {"public_signal", "observation_delivery", "ack", "primitive_accounting", "primitive_charge"},
                    "WORKER_JOURNAL_EVENTS")
            if kind != "public_signal":
                require(body["campaign_id"] == source.campaign_id and body["agent_id"] == source.agent_id
                        and type(body["epoch"]) is int and body["epoch"] in epochs, "WORKER_JOURNAL_SCOPE")
            if kind == "primitive_charge":
                require(type(body["charge_seq"]) is int, "WORKER_JOURNAL_COUNTERS")
                charges.append(body["charge_seq"])
        require(counters["primitive_events"] <= len(events)
                and charges == list(range(1, counters["primitive_events"] + 1)), "WORKER_JOURNAL_COUNTERS")
    return {"epochs": epochs, "action_rows": len(actions), "event_rows": len(events),
            "primitive_events": counters["primitive_events"]}


class HeldRestoredJournal:
    def __init__(self, reference, configuration):
        self.source = WorkerJournalSource.model_validate(reference)
        self.target = _absolute(configuration["state_directory"]) / "actions.sqlite"
        self.lease = None
        self.dispatched = False
        require(configuration["campaign_id"] == self.source.campaign_id
                and configuration["agent_id"] == self.source.agent_id
                and configuration["epoch"] == self.source.epoch + 1, "WORKER_JOURNAL_SCOPE")
        source = _absolute(self.source.path)
        require(not source.is_relative_to(self.target.parent) and not self.target.parent.is_relative_to(source.parent)
                and self.target.parent.is_dir() and not any(self.target.parent.iterdir()), "WORKER_JOURNAL_TARGET")
        self.sidecars = frozen_sidecars(source)
        with FileLease(snapshot([source, *(Path(str(source) + suffix) for suffix in self.sidecars)], [])) as original:
            self.summary = inspect_journal(source, self.source)
            require(type(configuration["primitive_limit"]) is int
                    and self.summary["primitive_events"] < configuration["primitive_limit"],
                    "WORKER_JOURNAL_BUDGET_EXHAUSTED")
            with source.open("rb") as incoming, self.target.open("xb") as outgoing:
                import shutil
                shutil.copyfileobj(incoming, outgoing, 1024**2)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            original.recheck()
            require(frozen_sidecars(source) == self.sidecars, "WORKER_JOURNAL_CHANGED")
            require(inspect_journal(self.target, self.source) == self.summary, "WORKER_JOURNAL_CHANGED")
        self.lease = FileLease(snapshot([self.target], []))

    def handoff(self):
        require(not self.dispatched and self.lease is not None, "WORKER_JOURNAL_ALREADY_DISPATCHED")
        require({safe(p) for p in self.target.parent.iterdir()} == {safe(self.target)}, "WORKER_JOURNAL_CHANGED")
        self.lease.recheck()
        require(file_hash(self.target) == self.source.sha256, "WORKER_JOURNAL_CHANGED")
        # SQLite must regain write access. This narrow handoff does not certify
        # other-writer exclusion; a failed construction consumes this attempt.
        self.dispatched = True
        self.close()

    def receipt(self):
        require(self.dispatched, "WORKER_JOURNAL_NOT_DISPATCHED")
        return {"schema": "strata/WorkerJournalRestoration/1", "source": self.source.model_dump(),
                "retained": self.summary, "old_grant_restored": False,
                "source_sidecars": self.sidecars, "sidecars_copied": False,
                "held_until_launch_handoff": True, "writer_custody_qualified": False}

    def close(self):
        if self.lease is not None:
            self.lease.close()
            self.lease = None
