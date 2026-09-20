"""Stage stopped development journals without replay, renewal or game launch.

The source stop evidence is an operator attestation, not process authentication.
This deliberately does not replace a complete game/agent checkpoint or admit a
campaign. Launch still requires fresh process, body, epoch and observation checks.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator

from mcbench.contracts import Digest, Id, Strict
from mcbench.native_game import GameAuthority
from mcbench.storage import canonical, digest, reject_links, require

from .run_costs import (
    CostJoin, InputFile, RestartCostJoin, decode, frozen_database, inspect_costs,
    inspect_restart_costs,
)


class StoppedSource(Strict):
    wire_schema: Literal["strata/StoppedNativeSource/1"] = Field(alias="schema")
    evidence_kind: Literal["synthetic", "authentic_operator_reference"]
    campaign_id: Id
    agent_id: Id
    epoch: int = Field(ge=1, le=9007199254740991)
    native_journal_sha256: Digest
    worker_database_sha256: Digest
    server_spool_sha256: Digest
    authority_sha256: Digest
    processes_terminal: Literal[True]
    controls_released: Literal[True]
    saved_state_consistent: Literal[True]
    guardian_result: Literal["pass", "fail"]
    evidence_sha256: list[Digest] = Field(min_length=1, max_length=32)

    @field_validator("processes_terminal", "controls_released", "saved_state_consistent", mode="before")
    @classmethod
    def strict_flags(cls, value):
        require(type(value) is bool, "RESTART_STOP_FLAG_TYPE")
        return value


class JournalRestart(Strict):
    wire_schema: Literal["strata/DevelopmentJournalRestart/1"] = Field(alias="schema")
    source: CostJoin | RestartCostJoin
    stopped_source: InputFile
    authority: InputFile
    next_epoch: int = Field(ge=1, le=9007199254740991)
    minimum_remaining_ms: int = Field(ge=1, le=1200000)


def _small(item):
    path = item.checked()
    require(path.stat().st_size <= 65536, "RESTART_METADATA_QUOTA")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == item.sha256, "COST_INPUT_CHANGED")
    return raw


def _now_ms():
    return time.time_ns() // 1000000


def _copy(item, target):
    source = item.checked()
    require(source.stat().st_nlink == 1, "RESTART_LINKED_INPUT")
    checksum = hashlib.sha256()
    total = 0
    with source.open("rb") as reader, target.open("xb") as writer:
        while chunk := reader.read(1048576):
            total += len(chunk)
            require(total <= 134217728, "COST_INPUT_SIZE")
            checksum.update(chunk)
            writer.write(chunk)
        writer.flush()
        os.fsync(writer.fileno())
    require(checksum.hexdigest() == item.sha256, "COST_INPUT_CHANGED")


def stage_journals(plan: JournalRestart, destination: Path):
    """Reserve a new directory and commit its manifest last; never launch it."""
    require(destination.is_absolute(), "RESTART_DESTINATION_PATH")
    reject_links(destination)
    require(destination.parent.is_dir() and not destination.exists(), "RESTART_DESTINATION_EXISTS")
    snapshots = plan.source.snapshots if isinstance(plan.source, RestartCostJoin) else [plan.source]
    latest = snapshots[-1]
    require(plan.next_epoch > latest.epoch, "STALE_EPOCH")
    source_items = [item for snapshot in snapshots for item in
                    (snapshot.native_journal, snapshot.worker_database, snapshot.server_spool)]
    source_items += [plan.authority, plan.stopped_source]
    for item in source_items:
        source = item.checked()
        require(source.stat().st_nlink == 1, "RESTART_LINKED_INPUT")
        require(not source.is_relative_to(destination.resolve()), "RESTART_INPUT_ALIAS")
    stop = StoppedSource.model_validate(decode(_small(plan.stopped_source)))
    require((stop.campaign_id, stop.agent_id, stop.epoch, stop.evidence_kind) ==
            (latest.campaign_id, latest.agent_id, latest.epoch, latest.evidence_kind), "RESTART_STOP_SCOPE")
    require(all(getattr(stop, name + "_sha256") == getattr(latest, name).sha256 for name in
                ("native_journal", "worker_database", "server_spool"))
            and stop.authority_sha256 == plan.authority.sha256, "RESTART_STOP_INPUTS")
    authority = GameAuthority.model_validate(decode(_small(plan.authority)))
    frozen_database(Path(latest.worker_database.path))
    db = sqlite3.connect(Path(latest.worker_database.path).as_uri() + "?mode=ro", uri=True)
    try:
        rows = db.execute("SELECT body FROM events WHERE kind='native_binding' ORDER BY cursor").fetchall()
        require(rows and all(decode(row[0])["authority"] == authority.model_dump(by_alias=True)
                             for row in rows), "RESTART_AUTHORITY_CHANGED")
    finally:
        db.close()
    # Validate the entire lineage before copying, including historical unknowns.
    costs = inspect_restart_costs(plan.source) if isinstance(plan.source, RestartCostJoin) else inspect_costs(plan.source)
    require(authority.expires_unix_ms - _now_ms() > plan.minimum_remaining_ms, "RESTART_AUTHORITY_EXPIRED")
    require(costs["primitive_events"] < authority.primitive_limit, "RESTART_INPUT_BUDGET_EXHAUSTED")
    copied = {"native.jsonl": latest.native_journal, "worker.sqlite": latest.worker_database,
              "authority.json": plan.authority}
    receipt = {
        "schema": "strata/StagedNativeJournals/1", "visibility": "evaluator",
        "evidence_kind": latest.evidence_kind, "campaign_id": latest.campaign_id,
        "agent_id": latest.agent_id, "source_epoch": latest.epoch, "next_epoch": plan.next_epoch,
        "plan_digest": digest(plan.model_dump(mode="json", by_alias=True)),
        "stop_evidence_sha256": plan.stopped_source.sha256,
        "guardian_result": stop.guardian_result, "stop_authority": "operator_attestation",
        "files": {name: item.sha256 for name, item in copied.items()},
        "inherited_primitive_events": costs["primitive_events"],
        "retained_unknown_requests": costs["unknown_requests"], "replay_requests": [],
        "authority_renewed": False, "cost_refunded": False, "launched": False,
        "requires_fresh_body_epoch_observation": True,
        "complete_checkpoint": False, "campaign_admission": False, "gate_result": "not_run",
    }
    # Sources are already verified frozen exports. Byte copying the SQLite file
    # preserves its exact identity, all tables and unknown receipts; no table
    # selection, ALTER, epoch insertion or WAL omission can lose old state.
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".journal-stage-") as temporary:
        temporary_path = Path(temporary).resolve()
        require(temporary_path.parent == destination.parent.resolve(), "RESTART_STAGING_PATH")
        staging = temporary_path / "journals"
        staging.mkdir()
        for name, item in copied.items():
            _copy(item, staging / name)
        with (staging / "manifest.json").open("xb") as stream:
            stream.write(canonical(receipt) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        for item in source_items:
            item.checked()
        for snapshot in snapshots:
            frozen_database(Path(snapshot.worker_database.path))
        require(authority.expires_unix_ms - _now_ms() > plan.minimum_remaining_ms,
                "RESTART_AUTHORITY_EXPIRED")
        reject_links(destination)
        require(not destination.exists(), "RESTART_DESTINATION_EXISTS")
        # mkdir is exclusive on both Windows and POSIX. Unlike directory rename,
        # it cannot replace an empty destination created by a concurrent caller.
        # A crash here leaves an incomplete destination WITHOUT a committed
        # manifest. Preserve that directory for inspection; retries must refuse it.
        destination.mkdir()
        for name in copied:
            os.rename(staging / name, destination / name)
        os.rename(staging / "manifest.json", destination / "manifest.json")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    reject_links(args.plan.absolute())
    require(args.plan.stat().st_size <= 1048576, "RESTART_PLAN_QUOTA")
    plan = JournalRestart.model_validate(decode(args.plan.read_bytes()))
    result = stage_journals(plan, args.destination)
    print(json.dumps({"status": "staged", "manifest_digest": digest(result), "launched": False}))


if __name__ == "__main__":
    main()
