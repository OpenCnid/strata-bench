"""Synthetic tampering tests; real stopped-run archives remain operator-private."""

import hashlib
import json
import sqlite3

import pytest

from mcbench.contracts import RpcRequest
from mcbench.storage import Fault, canonical, digest, extended_path
from strata_evaluator.evidence_bundle import EvidenceBundle
from strata_evaluator.native_game_evidence import NativeGameEvidencePlan, bootstrap_inventory, worker_evidence


def seal(root, entries=None):
    root = extended_path(root)
    if entries is None:
        entries = [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in root.rglob("*") if p.is_file() and p.name != "seal.json"]
    raw = canonical({"schema": "strata/PrivateEvidenceManifest/1", "files": entries,
                     "total_bytes": sum(e["bytes"] for e in entries)})
    (root / "seal.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def test_sealed_database_queries_cannot_write_or_create_sidecars(tmp_path):
    path = tmp_path / "record.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE records(value TEXT)")
        db.execute("INSERT INTO records VALUES('saved')")
    before = path.read_bytes()
    bundle = EvidenceBundle(tmp_path, seal(tmp_path))
    with bundle.database("record.sqlite") as db:
        assert db.execute("SELECT value FROM records").fetchone()[0] == "saved"
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db.execute("DELETE FROM records")
    bundle.verify()
    assert path.read_bytes() == before
    assert {p.name for p in tmp_path.iterdir()} == {"record.sqlite", "seal.json"}


@pytest.mark.parametrize("case,code", [("extra", "EVIDENCE_INVENTORY"),
    ("missing", "EVIDENCE_INVENTORY"), ("changed", "EVIDENCE_FILE_CHANGED"),
    ("seal", "EVIDENCE_SEAL_CHANGED"), ("traversal", "UNSAFE_PATH"),
    ("duplicate", "EVIDENCE_INVENTORY"), ("quota", "EVIDENCE_QUOTA")])
def test_manifest_faults_fail_closed(tmp_path, case, code):
    path = tmp_path / "record.txt"
    path.write_bytes(b"record")
    anchor = seal(tmp_path)
    if case == "extra":
        (tmp_path / "unlisted.txt").write_bytes(b"untrusted")
    elif case == "missing":
        path.unlink()
    elif case == "changed":
        path.write_bytes(b"forged")
    elif case == "seal":
        (tmp_path / "seal.json").write_bytes(b"{}")
    else:
        entries = json.loads((tmp_path / "seal.json").read_bytes())["files"]
        if case == "traversal":
            entries[0]["path"] = "../record.txt"
        elif case == "duplicate":
            entries.append(entries[0] | {"path": "RECORD.TXT"})
        else:
            entries[0]["bytes"] = 129 * 1024**2
        anchor = seal(tmp_path, entries)
    with pytest.raises(Fault, match=code):
        EvidenceBundle(tmp_path, anchor)


def test_sealed_wal_is_still_not_a_stopped_database(tmp_path):
    with sqlite3.connect(tmp_path / "record.sqlite") as db:
        db.execute("CREATE TABLE records(value TEXT)")
    (tmp_path / "record.sqlite-wal").write_bytes(b"pending committed pages")
    bundle = EvidenceBundle(tmp_path, seal(tmp_path))
    with pytest.raises(Fault, match="COST_DATABASE_NOT_FROZEN"):
        with bundle.database("record.sqlite"):
            pytest.fail("live WAL accepted")


@pytest.mark.parametrize("tamper", [False, True])
def test_legacy_deep_files_need_an_unbroken_transitive_hash_chain(tmp_path, tamper):
    root = extended_path(tmp_path)
    deep = "run/native/" + "/".join(["deep-path" * 3] * 10) + "/file.txt"
    path = root.joinpath(*deep.split("/"))
    path.parent.mkdir(parents=True)
    path.write_bytes(b"pinned before launch")
    (root / "run/intent.json").write_bytes(canonical({"plan": {"output": "C:/original/run"}}))
    bootstrap = {"schema": "strata/NativeBootstrap/1", "inventory": {
        "schema": "strata/LaunchFileInventory/1", "files": [{"path": "C:/original/" + deep,
        "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}}
    (root / "run/native/broker-runtime.manifest.json").write_bytes(canonical(bootstrap))
    entries = [{"path": name, "bytes": (root / name).stat().st_size,
                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
               for name in ("run/intent.json", "run/native/broker-runtime.manifest.json")]
    anchor = seal(root, entries)
    with pytest.raises(Fault, match="EVIDENCE_INVENTORY"):
        EvidenceBundle(root, anchor)
    if tamper:
        path.write_bytes(b"changed after launch")
        with pytest.raises(Fault, match="EVIDENCE_FILE_CHANGED"):
            EvidenceBundle(root, anchor, inventory_extension=bootstrap_inventory)
    else:
        bundle = EvidenceBundle(root, anchor, inventory_extension=bootstrap_inventory)
        assert len(bundle.primary_files) == 2 and len(bundle.files) == 3
        assert bundle.read(deep) == b"pinned before launch"


def worker_fixture(example, *, traced=False, refused=False):
    """Small independently constructed worker/broker join, not copied run data."""
    scope = {"is_example": False, "campaign_id": "c1", "agent_id": "a1", "epoch": 1}
    cap = {"schema": "strata/Capabilities/1", "backend": "mineflayer",
           "profile": "vanilla-development/1", "keybindings": False}
    if traced:
        cap["primitive_accounting"] = {"policy": "durable-pre-dispatch-charge/1", "emission_confirmation": False}
    if refused:
        assert traced
        cap["action_admission"] = {"policy": "atomic-acceptance-sequence-refusal/1", "recorded_refusals": ["OUT_OF_ORDER"]}
    cap_digest = digest(cap)
    cap.update(digest=cap_digest, epoch=1, lease_id="lease1")
    before = example("Observation") | scope | {"capability_digest": cap_digest}
    after = before | {"seq": 2, "observation_id": "obs2", "last_action_seq": 1}
    batch = example("ActionBatch") | scope | {"capability_digest": cap_digest}
    ack = example("ActionAck") | scope | {"emitted_events": 1}
    accepted = ack | {"seq": 1, "status": "accepted", "emitted_events": 0,
                      "completed_mono_ms": None, "result_observation_id": None,
                      "release_confirmed": False}
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("CREATE TABLE epochs(epoch INTEGER); INSERT INTO epochs VALUES(1);"
        "CREATE TABLE actions(request_id TEXT,epoch INTEGER,seq INTEGER,digest TEXT,request TEXT,ack TEXT);"
        "CREATE TABLE events(cursor INTEGER PRIMARY KEY,kind TEXT,body TEXT);"
        "CREATE TABLE counters(name TEXT,value INTEGER);")
    db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?)", ("request1", 1, 1, digest(batch), canonical(batch), canonical(ack)))
    events = [("observation_delivery", before), ("ack", accepted),
              ("observation_delivery", after), ("ack", ack)]
    if traced:
        event_scope = {k: scope[k] for k in ("campaign_id", "agent_id", "epoch")}
        events.insert(2, ("primitive_charge", {"schema": "strata/MineflayerPrimitiveCharge/1",
            "policy": "durable-pre-dispatch-charge/1", **event_scope, "request_id": batch["request_id"],
            "action_seq": 1, "request_digest": digest(batch), "charge_seq": 1, "action_charge_seq": 1,
            "safety_release": False, "recorded_at": "2026-09-18T12:00:01Z", "mono_ms": 11000,
            "emission_confirmed": False}))
        events.insert(0, ("primitive_accounting", {"schema": "strata/MineflayerPrimitiveAccounting/1",
            "policy": "durable-pre-dispatch-charge/1", **event_scope, "opening_primitive_events": 0}))
    if refused:
        rejected = batch | {"seq": 3, "request_id": "bad-sequence"}
        events.insert(2, ("action_refusal", {"schema": "strata/ActionSequenceRefusal/1",
            "policy": "atomic-acceptance-sequence-refusal/1", **event_scope,
            "request_id": rejected["request_id"], "request_digest": digest(rejected), "action_seq": 3,
            "expected_action_seq": 1, "ack_counter": 0, "primitive_events": 0, "code": "OUT_OF_ORDER",
            "recorded_at": "2026-09-18T12:00:01Z", "mono_ms": 10001}))
    for kind, value in events:
        db.execute("INSERT INTO events(kind,body) VALUES(?,?)", (kind, canonical(value)))
    db.executemany("INSERT INTO counters VALUES(?,?)", [("primitive_events", 1),
                  ("1:action", 1), ("1:ack", 2), ("1:observation", 2)])
    source = {"participants": [{"participant": {"thread": "root", "depth": 0}}],
              "game_calls": [], "broker_calls": []}
    for i, value in enumerate([cap, before, accepted, ack, after]):
        response = {"schema": "strata/GameResponse/1", "status": "ok", "request_id": f"rpc-{i}", "result": value}
        source["game_calls"].append({"runtime": "job", "thread": "root", "request": f"rpc-{i}",
                                     "result": canonical(response)})
        if traced:
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1", "request_id": f"rpc-{i}",
                "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "deadline_at": "2026-09-18T12:00:03Z",
                "method": ["capabilities", "observe", "act", "action_status", "observe"][i],
                "action": batch if i == 2 else None, "target_request_id": "request1" if i == 3 else None,
                "after": None}).model_dump()
            source["game_calls"][-1].update(request_body=request, fingerprint=digest(request))
        source["broker_calls"].append({"state": "RETURNED", "result_digest": digest(response),
                                      "body": canonical({"tool": "game", "thread": "root"})})
    if refused:
        for index, (method, code) in enumerate((("act", "OUT_OF_ORDER"), ("action_status", "ACTION_UNKNOWN")), 2):
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1", "request_id": f"error-{index}",
                "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "deadline_at": "2026-09-18T12:00:03Z",
                "method": method, "action": rejected if method == "act" else None,
                "target_request_id": "wrong-outer-id" if method == "action_status" else None,
                "after": None}).model_dump()
            response = {"schema": "strata/GameResponse/1", "status": "error", "error": {
                "code": code, "message": code, "retryable": False, "retry_after_ms": None,
                "request_id": request["request_id"], "expected_epoch": 1, "details_ref": None}}
            source["game_calls"].insert(index, {"runtime": "job", "thread": "root", "request": request["request_id"],
                "result": canonical(response), "request_body": request, "fingerprint": digest(request)})
            source["broker_calls"].append({"state": "RETURNED", "result_digest": digest(response),
                                          "body": canonical({"tool": "game", "thread": "root"})})
    plan = NativeGameEvidencePlan.model_validate({"schema": "strata/NativeGameEvidencePlan/1",
        "bundle": "unused", "seal_sha256": "a" * 64, "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "job_id": "job"})
    return db, source, plan, {"lease_id": "lease1", "primitive_limit": 10}


def test_worker_join_counts_actions_not_polling_or_acknowledgments(example):
    db, source, plan, config = worker_fixture(example)
    try:
        result, _, _ = worker_evidence(db, source, plan, config)
        assert result["primitive_events"] == 1 and len(result["actions"]) == 1
        assert result["game_calls"] == 5 and result["observations"] == 2
        assert result["primitive_trace_verified"] is False and result["request_preimages_complete"] is False
    finally:
        db.close()


def test_new_worker_trace_joins_exact_broker_requests_and_charges_without_claiming_emission(example):
    db, source, plan, config = worker_fixture(example, traced=True)
    try:
        result, _, _ = worker_evidence(db, source, plan, config)
        assert result["request_preimages_verified"] == 5 and result["request_preimages_complete"]
        assert result["primitive_trace_verified"] and not result["primitive_charges_confirm_emission"]
    finally:
        db.close()


def test_refused_attempt_and_unknown_status_read_do_not_hide_one_completed_action(example):
    db, source, plan, config = worker_fixture(example, traced=True, refused=True)
    try:
        report, _, _ = worker_evidence(db, source, plan, config, allow_recorded_refusals=True)
        assert report["known_attempts_reconciled"] and not report["gameplay_success_qualified"]
        assert len(report["actions"]) == 1 and report["primitive_events"] == 1 and report["game_calls"] == 7
        assert len(report["recorded_refusals"]) == len(report["read_errors"]) == 1
        assert report["recorded_refusals"][0]["accepted"] is False
        assert report["recorded_refusals"][0]["primitive_events"] == 0
        with pytest.raises(Fault, match="NATIVE_GAME_REFUSAL_PROFILE"):
            worker_evidence(db, source, plan, config)
    finally:
        db.close()


@pytest.mark.parametrize("case", ["missing", "orphan", "digest", "sequence", "ack_count", "primitives",
                                  "observation_time", "foreign", "unknown_code", "error_identity", "status_target"])
def test_refusal_join_rejects_missing_proof_and_uncertain_or_inconsistent_outcomes(example, case):
    db, source, plan, config = worker_fixture(example, traced=True, refused=True)
    try:
        if case == "missing":
            db.execute("UPDATE events SET kind='public_signal' WHERE kind='action_refusal'")
        elif case == "orphan":
            source["game_calls"].pop(2)
        elif case in {"unknown_code", "error_identity"}:
            call = source["game_calls"][2]
            response = json.loads(call["result"])
            if case == "unknown_code":
                response["error"].update(code="INTERNAL_ERROR", message="INTERNAL_ERROR")
            else:
                response["error"]["request_id"] = "foreign-call"
            old = digest(json.loads(call["result"]))
            call["result"] = canonical(response)
            next(c for c in source["broker_calls"] if c["result_digest"] == old)["result_digest"] = digest(response)
        elif case == "status_target":
            call = source["game_calls"][3]
            call["request_body"]["target_request_id"] = "request1"
            call["fingerprint"] = digest(call["request_body"])
        else:
            value = json.loads(db.execute("SELECT body FROM events WHERE kind='action_refusal'").fetchone()[0])
            value.update({"digest": {"request_digest": "f" * 64}, "sequence": {"expected_action_seq": 3},
                "ack_count": {"ack_counter": 1}, "primitives": {"primitive_events": 1},
                "observation_time": {"mono_ms": 0}, "foreign": {"agent_id": "foreign"}}[case])
            db.execute("UPDATE events SET body=? WHERE kind='action_refusal'", (canonical(value),))
        with pytest.raises(Fault):
            worker_evidence(db, source, plan, config, allow_recorded_refusals=True)
    finally:
        db.close()


def test_missing_admission_policy_is_not_inferred_from_absence_of_refusals(example):
    db, source, plan, config = worker_fixture(example, traced=True)
    try:
        with pytest.raises(Fault, match="NATIVE_GAME_REFUSAL_PROFILE"):
            worker_evidence(db, source, plan, config, allow_recorded_refusals=True)
    finally:
        db.close()


@pytest.mark.parametrize("case,code", [("missing", "NATIVE_GAME_PRIMITIVE_INCOMPLETE"),
    ("foreign_action", "NATIVE_GAME_PRIMITIVE_BINDING"), ("sequence", "NATIVE_GAME_PRIMITIVE_BINDING"),
    ("clock", "NATIVE_GAME_PRIMITIVE_BINDING"), ("opening", "NATIVE_GAME_PRIMITIVE_POLICY"),
    ("rpc_receipt", "NATIVE_GAME_REQUEST_MISMATCH")])
def test_new_trace_rejects_gaps_foreign_actions_and_request_receipt_conflicts(example, case, code):
    db, source, plan, config = worker_fixture(example, traced=True)
    try:
        if case == "missing":
            db.execute("UPDATE events SET kind='public_signal' WHERE kind='primitive_charge'")
        elif case == "rpc_receipt":
            body = source["game_calls"][3]["request_body"]
            body["target_request_id"] = "other-action"
            source["game_calls"][3]["fingerprint"] = digest(body)
        else:
            kind = "primitive_accounting" if case == "opening" else "primitive_charge"
            value = json.loads(db.execute("SELECT body FROM events WHERE kind=?", (kind,)).fetchone()[0])
            value.update({"foreign_action": {"request_id": "other-action"}, "sequence": {"charge_seq": 2},
                          "clock": {"mono_ms": 13000}, "opening": {"opening_primitive_events": 9}}[case])
            db.execute("UPDATE events SET body=? WHERE kind=?", (canonical(value), kind))
        with pytest.raises(Fault, match=code):
            worker_evidence(db, source, plan, config)
    finally:
        db.close()


@pytest.mark.parametrize("case,code", [
    ("epoch", "NATIVE_GAME_EVIDENCE_SCOPE"), ("missing", "NATIVE_GAME_ACK_INCOMPLETE"),
    ("duplicate", "NATIVE_GAME_ACK_INCOMPLETE"), ("foreign", "NATIVE_GAME_EVIDENCE_SCOPE"),
    ("counter", "NATIVE_GAME_COUNTER_MISMATCH"), ("request", "NATIVE_GAME_ACTION_BINDING"),
    ("broker", "NATIVE_GAME_RECEIPT_MISSING"), ("helper", "NATIVE_GAME_BROKER_SCOPE"),
    ("receipt", "NATIVE_GAME_RECEIPT_MISMATCH"), ("unknown", "NATIVE_GAME_ACTION_UNCERTAIN")])
def test_worker_receipt_and_scope_corruption_is_not_reconciled(example, case, code):
    db, source, plan, config = worker_fixture(example)
    try:
        if case == "epoch":
            db.execute("INSERT INTO epochs VALUES(2)")
        elif case == "missing":
            db.execute("DELETE FROM events WHERE cursor=4")
        elif case == "duplicate":
            ack = json.loads(db.execute("SELECT body FROM events WHERE cursor=4").fetchone()[0])
            db.execute("INSERT INTO events VALUES(5,'ack',?)", (canonical(ack | {"seq": 3}),))
        elif case == "foreign":
            value = json.loads(db.execute("SELECT body FROM events WHERE cursor=1").fetchone()[0])
            db.execute("UPDATE events SET body=? WHERE cursor=1", (canonical(value | {"agent_id": "sibling"}),))
        elif case == "counter":
            db.execute("UPDATE counters SET value=2 WHERE name='primitive_events'")
        elif case == "request":
            db.execute("UPDATE actions SET digest=?", ("b" * 64,))
        elif case == "broker":
            source["game_calls"].pop(3)
        elif case == "helper":
            source["game_calls"][0]["thread"] = "child"
        elif case == "receipt":
            response = json.loads(source["game_calls"][3]["result"])
            response["result"]["emitted_events"] += 1
            source["game_calls"][3]["result"] = canonical(response)
            source["broker_calls"][3]["result_digest"] = digest(response)
        else:
            ack = json.loads(db.execute("SELECT ack FROM actions").fetchone()[0])
            ack.update(status="unknown", requires_resync=True, release_confirmed=False)
            db.execute("UPDATE actions SET ack=?", (canonical(ack),))
            db.execute("UPDATE events SET body=? WHERE cursor=4", (canonical(ack),))
        with pytest.raises(Fault, match=code):
            worker_evidence(db, source, plan, config)
    finally:
        db.close()
