"""Read-only development evidence join. Not transport authentication or score admission.

Stopped Forge scopes only. Hash-pinned raw files remain private; this report
does not infer missing model usage, avatar identity, active time or game success.
"""

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field

from mcbench.contracts import ActionAck, ActionBatch, Digest, Id, Strict, UInt
from mcbench.native_game import GameActionReceipt, GameAuthority, GameIdentity
from mcbench.storage import digest, reject_links, require

from .cli import write_report
from .telemetry import inspect_spool, unique_object


class InputFile(Strict):
    path: str
    sha256: Digest

    def checked(self):
        path = Path(self.path)
        require(path.is_absolute(), "COST_INPUT_PATH")
        reject_links(path)
        require(path.is_file() and path.stat().st_size <= 134217728, "COST_INPUT_SIZE")
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        require(actual == self.sha256, "COST_INPUT_CHANGED")
        return path


class CostJoin(Strict):
    wire_schema: Literal["strata/DevelopmentCostJoin/1"] = Field(alias="schema")
    evidence_kind: Literal["synthetic", "authentic_operator_reference"]
    campaign_id: Id
    agent_id: Id
    epoch: UInt
    native_journal: InputFile
    worker_database: InputFile
    server_spool: InputFile


class RestartCostJoin(Strict):
    wire_schema: Literal["strata/DevelopmentRestartCostJoin/1"] = Field(alias="schema")
    snapshots: list[CostJoin] = Field(min_length=2, max_length=32)


def decode(text):
    return json.loads(text, object_pairs_hook=unique_object)


def native_records(path):
    """Validate exact emitted framing; hash original payload bytes, not a reserialization."""
    previous = "0" * 64
    decoder = json.JSONDecoder(object_pairs_hook=unique_object)
    records = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        while line := stream.readline(1048577):
            require(len(line.encode("utf-8")) <= 1048576 and line.endswith("\n"), "COST_NATIVE_PARTIAL")
            frame = decode(line)
            require(set(frame) == {"schema", "seq", "previous", "payload", "sha256"}
                    and frame["schema"] == "strata/NativeGameJournalFrame/1"
                    and type(frame["seq"]) is int and frame["seq"] == len(records) + 1
                    and frame["previous"] == previous, "COST_NATIVE_FRAME")
            # The pinned Java writer emits this exact compact top-level prefix.
            prefix = '{"schema":"strata/NativeGameJournalFrame/1","seq":' + str(frame["seq"])
            prefix += ',"previous":"' + previous + '","payload":'
            require(line.startswith(prefix), "COST_NATIVE_FRAME")
            payload, end = decoder.raw_decode(line, len(prefix))
            require(isinstance(payload, dict), "COST_NATIVE_FRAME")
            raw = line[len(prefix):end]
            calculated = hashlib.sha256((previous + "\n" + raw).encode()).hexdigest()
            require(calculated == frame["sha256"], "COST_NATIVE_HASH")
            previous = calculated
            records.append(payload)
            require(len(records) <= 10000, "COST_NATIVE_QUOTA")
    require(bool(records), "COST_NATIVE_EMPTY")
    return records


def scope(batch, plan, epochs):
    require(not batch.is_example, "EXAMPLE_NOT_EXECUTABLE")
    require((batch.campaign_id, batch.agent_id) == (plan.campaign_id, plan.agent_id)
            and batch.epoch in epochs, "COST_SCOPE_MISMATCH")


def frozen_database(path):
    for suffix in ("-wal", "-journal"):
        sidecar = Path(str(path) + suffix)
        reject_links(sidecar)
        require(not sidecar.exists() or sidecar.stat().st_size == 0, "COST_DATABASE_NOT_FROZEN")


def inspect_costs(plan: CostJoin):
    return _inspect_costs(plan, [plan.epoch])[0]


def _inspect_costs(plan: CostJoin, epochs):
    inputs = (plan.native_journal, plan.worker_database, plan.server_spool)
    native_path, database_path, spool_path = [item.checked() for item in inputs]
    require(len({native_path.resolve(), database_path.resolve(), spool_path.resolve()}) == 3,
            "COST_INPUT_ALIAS")
    # A stopped database must have been checkpointed or copied by SQLite backup.
    # Never silently ignore an extant WAL to obtain a convenient total.
    frozen_database(database_path)
    db = sqlite3.connect(database_path.as_uri() + "?mode=ro", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        require(db.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "COST_DATABASE_INVALID")
        require(db.execute("SELECT epoch FROM epochs ORDER BY epoch").fetchall()
                == [(epoch,) for epoch in epochs], "COST_SCOPE_MISMATCH")
        for table, limit in (("actions", 10000), ("events", 100000), ("counters", 1000)):
            require(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] <= limit, "COST_DATABASE_QUOTA")
        event_rows = db.execute("SELECT cursor,kind,body FROM events ORDER BY cursor").fetchall()
        require([r[0] for r in event_rows] == list(range(1, len(event_rows) + 1)), "COST_EVENT_GAP")
        bindings = [decode(row[2]) for row in event_rows if row[1] == 'native_binding']
        require([b["epoch"] for b in bindings] == epochs, "COST_BINDING_AMBIGUOUS")
        binding = bindings[0]
        authority = GameAuthority.model_validate(binding["authority"])
        identity = GameIdentity.model_validate(binding["identity"])
        require((authority.campaign_id, authority.agent_id) == (plan.campaign_id, plan.agent_id)
                and identity.body_fingerprint == authority.body_fingerprint, "COST_SCOPE_MISMATCH")
        fingerprint = binding["fingerprint"]
        require(isinstance(fingerprint, str) and len(fingerprint) == 64
                and all(c in "0123456789abcdef" for c in fingerprint), "COST_BINDING_INVALID")
        source = "native:" + fingerprint + ":" + digest(binding["authority"])
        for value in bindings:
            current_identity = GameIdentity.model_validate(value["identity"])
            require(value["authority"] == binding["authority"]
                    and value["fingerprint"] == fingerprint
                    and current_identity.body_fingerprint == identity.body_fingerprint,
                    "COST_RESTART_AUTHORITY_CHANGED")
        totals, high_water = 0, 0
        bound_epoch = None
        for _, kind, body in event_rows:
            if kind == 'native_binding':
                bound_epoch = decode(body)["epoch"]
            if kind != 'native_usage':
                continue
            value = decode(body)
            require(set(value) == {"epoch", "source", "attempted_primitive_events", "charged_delta"}
                    and value["epoch"] == bound_epoch and value["source"] == source,
                    "COST_USAGE_SCOPE")
            attempted, delta = value["attempted_primitive_events"], value["charged_delta"]
            require(type(attempted) is int and 0 <= attempted <= authority.primitive_limit
                    and type(delta) is int and delta == max(0, attempted - high_water), "COST_USAGE_DELTA")
            high_water = max(high_water, attempted)
            totals += delta
        counter_rows = db.execute("SELECT name,value FROM counters").fetchall()
        counters = dict(counter_rows)
        require(len(counters) == len(counter_rows)
                and all(type(v) is int and v >= 0 for v in counters.values()), "COST_COUNTER_MISMATCH")
        require(counters.get("primitive_events", 0) == counters.get(source, 0) == totals,
                "COST_COUNTER_MISMATCH")
        require(not any(k.startswith("native:") and k != source for k in counters), "COST_USAGE_SCOPE")
        actions = {}
        action_rows = db.execute(
            "SELECT request_id,epoch,seq,digest,request,ack FROM actions ORDER BY epoch,seq").fetchall()
        seen_sequences = set()
        for key, epoch, sequence, expected, request, ack in action_rows:
            raw = decode(request)
            batch = ActionBatch.model_validate(raw)
            scope(batch, plan, epochs)
            require((key, epoch, sequence) == (batch.request_id, batch.epoch, batch.seq)
                    and key not in actions and (epoch, sequence) not in seen_sequences
                    and batch.capability_digest == authority.capability_digest
                    and digest(raw) == expected, "COST_ACTION_BINDING")
            receipt = decode(ack)
            scope(ActionAck.model_validate(receipt), plan, epochs)
            require(receipt["request_id"] == key and receipt["epoch"] == epoch
                    and receipt["action_seq"] == sequence, "COST_ACTION_BINDING")
            actions[key] = (raw, receipt)
            seen_sequences.add((epoch, sequence))
    finally:
        db.close()
    records = native_records(native_path)
    java_authority = (f"Authority[campaign={authority.campaign_id}, agent={authority.agent_id}, "
                      f"capability={authority.capability_digest}, body={authority.body_fingerprint}, "
                      f"expires={authority.expires_unix_ms}, primitiveLimit={authority.primitive_limit}]")
    profile = hashlib.sha256((fingerprint + "\n" + java_authority).encode()).hexdigest()
    require(records[0] == {"kind": "profile", "identity": profile}, "COST_NATIVE_PROFILE")
    intents, receipts, attempted = {}, {}, Counter()
    safety, last_wall, lease, lease_epoch = 0, 0, None, None
    leased_epochs = []
    for record in records[1:]:
        wall = record.get("wall_ms")
        require(type(wall) is int and wall >= last_wall, "COST_WALL_ROLLBACK")
        last_wall = wall
        kind = record["kind"]
        if kind == "lease":
            index = len(leased_epochs)
            require(index < len(epochs) and record["epoch"] == epochs[index], "COST_SCOPE_MISMATCH")
            lease_epoch = record["epoch"]
            leased_epochs.append(lease_epoch)
            lease = record["lease_id"]
        elif kind == "renew":
            require(record["epoch"] == lease_epoch and record["lease_id"] == lease, "COST_SCOPE_MISMATCH")
        elif kind == "intent":
            raw = decode(record["batch_json"])
            batch = ActionBatch.model_validate(raw)
            scope(batch, plan, epochs)
            key = batch.request_id
            require(key not in intents and key in actions and raw == actions[key][0]
                    and batch.epoch == lease_epoch and batch.lease_id == lease, "COST_INTENT_BINDING")
            intents[key] = raw
        elif kind == "primitive":
            require(type(record["safety_release"]) is bool, "COST_PRIMITIVE_UNATTRIBUTED")
            key = record["request_id"]
            if key is None:
                require(record["safety_release"] is True, "COST_PRIMITIVE_UNATTRIBUTED")
                safety += 1
            else:
                require(key in intents and key not in receipts, "COST_PRIMITIVE_ORDER")
                attempted[key] += 1
        elif kind == "terminal":
            receipt = GameActionReceipt.model_validate(record["receipt"])
            key = receipt.request_id
            require(key in intents and key not in receipts and receipt.epoch == intents[key]["epoch"]
                    and receipt.action_seq == intents[key]["seq"]
                    and receipt.attempted_events == attempted[key]
                    and receipt.status == actions[key][1]["status"], "COST_RECEIPT_BINDING")
            receipts[key] = receipt
        else:
            require(kind == "delivery", "COST_NATIVE_KIND")
    require(set(intents) == set(actions) == set(receipts), "COST_ACTION_INCOMPLETE")
    require(leased_epochs == epochs, "COST_SCOPE_MISMATCH")
    require(sum(attempted.values()) + safety == totals, "COST_NATIVE_CHARGE_MISMATCH")
    telemetry = inspect_spool(spool_path, plan.campaign_id, plan.epoch)
    for item in inputs:
        item.checked()  # Detect changes during the read without modifying evidence.
    frozen_database(database_path)
    report = {"schema": "strata/DevelopmentCostReconciliation/1", "visibility": "evaluator",
            "evidence_kind": plan.evidence_kind,
            "reconciliation": "pass", "campaign_id": plan.campaign_id, "epoch": plan.epoch,
            "inputs": {name: getattr(plan, name).sha256 for name in
                       ("native_journal", "worker_database", "server_spool")},
            "primitive_events": totals, "unattributed_safety_releases": safety,
            "actions": [{"request_id": key, "status": receipt.status,
                         "attempted_events": attempted[key]} for key, receipt in receipts.items()],
            "unknown_requests": [key for key, r in receipts.items() if r.status == "unknown"],
            "server_boot_id": telemetry["server_boot_id"],
            "sampled_server_ticks": telemetry["sampled_server_ticks"],
            "sampled_server_wall_ns": telemetry["sampled_wall_ns"],
            "avatar_ticks_at_last_sample": telemetry["avatar_ticks_at_last_sample"],
            "last_server_tick": telemetry["last_server_tick"],
            "complete_project_accounting": False, "scoring_eligible": False, "gate_result": "not_run",
            "unresolved": ["authenticated_ingress_and_isolation", "qualified_profile_and_role_locks",
                           "avatar_identity_mapping", "startup_and_unsampled_clock_intervals",
                           "root_helper_retry_inference_join", "campaign_and_restart_aggregation"]}
    # Private comparison state is never serialized into the result.
    if "terminal_clock" in telemetry:
        report["terminal_clock"] = telemetry["terminal_clock"]
    native_bytes = native_path.read_bytes()
    require(hashlib.sha256(native_bytes).hexdigest() == plan.native_journal.sha256, "COST_INPUT_CHANGED")
    return report, {"actions": {r[0]: r for r in action_rows}, "events": event_rows,
                    "counters": counters, "native": native_bytes}


def inspect_restart_costs(plan: RestartCostJoin):
    """Join complete cumulative snapshots; never add their inherited totals twice."""
    first = plan.snapshots[0]
    epochs = [p.epoch for p in plan.snapshots]
    require(epochs == sorted(set(epochs)), "COST_RESTART_ORDER")
    require(all((p.campaign_id, p.agent_id, p.evidence_kind)
                == (first.campaign_id, first.agent_id, first.evidence_kind) for p in plan.snapshots),
            "COST_SCOPE_MISMATCH")
    previous, totals, boots, reports = None, 0, set(), []
    for index, snapshot in enumerate(plan.snapshots):
        report, state = _inspect_costs(snapshot, epochs[:index + 1])
        require(report["server_boot_id"] not in boots, "COST_RESTART_BOOT_REUSED")
        boots.add(report["server_boot_id"])
        if previous is not None:
            require(state["native"].startswith(previous["native"]), "COST_RESTART_NATIVE_PREFIX")
            require(state["events"][:len(previous["events"])] == previous["events"],
                    "COST_RESTART_EVENT_PREFIX")
            require(all(state["actions"].get(k) == v for k, v in previous["actions"].items()),
                    "COST_RESTART_RECEIPT_CHANGED")
            require(all(state["counters"].get(k, -1) >= v for k, v in previous["counters"].items()),
                    "COST_RESTART_COUNTER_ROLLBACK")
        report["new_primitive_events"] = report["primitive_events"] - totals
        require(report["new_primitive_events"] >= 0, "COST_RESTART_COUNTER_ROLLBACK")
        totals = report["primitive_events"]
        reports.append(report)
        previous = state
    for snapshot in plan.snapshots:
        for item in (snapshot.native_journal, snapshot.worker_database, snapshot.server_spool):
            item.checked()
        frozen_database(Path(snapshot.worker_database.path))
    return {"schema": "strata/DevelopmentRestartCostReconciliation/1", "visibility": "evaluator",
            "evidence_kind": first.evidence_kind, "campaign_id": first.campaign_id,
            "agent_id": first.agent_id, "epochs": epochs, "reconciliation": "pass",
            "primitive_events": totals, "unknown_requests": reports[-1]["unknown_requests"],
            "sampled_server_ticks": sum(r["sampled_server_ticks"] for r in reports),
            "sampled_server_wall_ns": sum(r["sampled_server_wall_ns"] for r in reports),
            "snapshots": reports, "scoring_eligible": False, "complete_project_accounting": False,
            "gate_result": "not_run", "unresolved": ["authenticated_ingress_and_isolation",
                "qualified_profile_and_role_locks", "avatar_identity_mapping",
                "startup_and_unsampled_clock_intervals", "root_helper_retry_inference_join",
                "complete_game_and_agent_checkpoint_state", "cross_authority_campaign_aggregation"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    require(not args.output.exists(), "COST_REPORT_EXISTS")
    value = decode(args.plan.read_text(encoding="utf-8"))
    report = (inspect_restart_costs(RestartCostJoin.model_validate(value))
              if value.get("schema") == "strata/DevelopmentRestartCostJoin/1"
              else inspect_costs(CostJoin.model_validate(value)))
    print(json.dumps({"status": "reconciled", "visibility": "evaluator", **write_report(args.output, report)}))


if __name__ == "__main__":
    main()
