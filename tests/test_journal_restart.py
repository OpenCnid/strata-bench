"""Synthetic staging boundaries; no game launch, security or campaign qualification."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator import journal_restart as restart
from test_restart_costs import pair, pin
from test_run_costs import build


def prepared(tmp_path, example, monkeypatch, multiple=False):
    source = tmp_path / "source"
    source.mkdir()
    costs = pair(source, example) if multiple else build(source, example)
    latest = costs.snapshots[-1] if multiple else costs
    with sqlite3.connect(latest.worker_database.path) as db:
        authority = json.loads(db.execute("SELECT body FROM events WHERE kind='native_binding'").fetchone()[0])["authority"]
    auth = source / "authority.json"
    auth.write_text(json.dumps(authority), encoding="utf-8")
    stop = source / "stopped.json"
    stop.write_text(json.dumps({
        "schema": "strata/StoppedNativeSource/1", "evidence_kind": "synthetic",
        "campaign_id": latest.campaign_id, "agent_id": latest.agent_id, "epoch": latest.epoch,
        **{name + "_sha256": getattr(latest, name).sha256 for name in
           ("native_journal", "worker_database", "server_spool")},
        "authority_sha256": pin(auth)["sha256"], "processes_terminal": True,
        "controls_released": True, "saved_state_consistent": True,
        "guardian_result": "fail", "evidence_sha256": ["a" * 64],
    }), encoding="utf-8")
    # The historical fixture clock is injected in tests only; the CLI has no override.
    monkeypatch.setattr(restart, "_now_ms", lambda: authority["expires_unix_ms"] - 2000)
    plan = restart.JournalRestart.model_validate({
        "schema": "strata/DevelopmentJournalRestart/1", "source": costs.model_dump(by_alias=True),
        "stopped_source": pin(stop), "authority": pin(auth),
        "next_epoch": latest.epoch + 1, "minimum_remaining_ms": 1000,
    })
    return plan, latest, tmp_path / "destination"


@pytest.mark.parametrize("multiple", [False, True])
def test_stage_exact_history_and_unknowns_without_replay(tmp_path, example, monkeypatch, multiple):
    plan, latest, target = prepared(tmp_path, example, monkeypatch, multiple)
    (Path(plan.authority.path).parent / "auth.json").write_text("synthetic-secret-canary")
    originals = {"native.jsonl": Path(latest.native_journal.path).read_bytes(),
                 "worker.sqlite": Path(latest.worker_database.path).read_bytes(),
                 "authority.json": Path(plan.authority.path).read_bytes()}
    result = restart.stage_journals(plan, target)
    assert set(p.name for p in target.iterdir()) == {*originals, "manifest.json"}
    for name, raw in originals.items():
        assert (target / name).read_bytes() == raw
        assert result["files"][name] == hashlib.sha256(raw).hexdigest()
    assert json.loads((target / "manifest.json").read_bytes()) == result
    assert result["inherited_primitive_events"] == (5 if multiple else 3)
    assert len(result["retained_unknown_requests"]) == 1 and result["replay_requests"] == []
    assert result["guardian_result"] == "fail" and result["stop_authority"] == "operator_attestation"
    assert not any(result[key] for key in ("launched", "authority_renewed", "cost_refunded",
                                           "complete_checkpoint", "campaign_admission"))
    assert not list(tmp_path.glob(".journal-stage-*"))


@pytest.mark.parametrize("change,code", [
    ("epoch", "STALE_EPOCH"), ("stop_scope", "RESTART_STOP_SCOPE"),
    ("stop_pin", "RESTART_STOP_INPUTS"), ("renew_authority", "RESTART_AUTHORITY_CHANGED"),
    ("expired", "RESTART_AUTHORITY_EXPIRED"), ("active_wal", "COST_DATABASE_NOT_FROZEN"),
])
def test_reject_invalid_continuation(tmp_path, example, monkeypatch, change, code):
    plan, latest, target = prepared(tmp_path, example, monkeypatch)
    stop = Path(plan.stopped_source.path)
    data = json.loads(stop.read_bytes())
    if change == "epoch":
        plan.next_epoch = latest.epoch
    elif change == "stop_scope":
        data["campaign_id"] = "foreign"
    elif change == "stop_pin":
        data["native_journal_sha256"] = "f" * 64
    elif change == "renew_authority":
        auth = Path(plan.authority.path)
        value = json.loads(auth.read_bytes())
        value["expires_unix_ms"] += 1
        auth.write_text(json.dumps(value))
        plan.authority = restart.InputFile.model_validate(pin(auth))
        data["authority_sha256"] = plan.authority.sha256
    elif change == "expired":
        monkeypatch.setattr(restart, "_now_ms", lambda: 123456789)
    elif change == "active_wal":
        Path(latest.worker_database.path + "-wal").write_bytes(b"pending")
    stop.write_text(json.dumps(data))
    plan.stopped_source = restart.InputFile.model_validate(pin(stop))
    with pytest.raises(Fault, match=code):
        restart.stage_journals(plan, target)
    assert not target.exists()


@pytest.mark.parametrize("flag", [False, 1])
def test_unconfirmed_or_nonboolean_stop_rejected(tmp_path, example, monkeypatch, flag):
    plan, _, target = prepared(tmp_path, example, monkeypatch)
    stop = Path(plan.stopped_source.path)
    data = json.loads(stop.read_bytes()) | {"processes_terminal": flag}
    stop.write_text(json.dumps(data))
    plan.stopped_source = restart.InputFile.model_validate(pin(stop))
    with pytest.raises(ValidationError):
        restart.stage_journals(plan, target)
    assert not target.exists()


@pytest.mark.parametrize("change,code", [
    ("expiry", "RESTART_AUTHORITY_EXPIRED"), ("source", "COST_INPUT_CHANGED"),
    ("wal", "COST_DATABASE_NOT_FROZEN"),
])
def test_recheck_before_atomic_publication(tmp_path, example, monkeypatch, change, code):
    plan, latest, target = prepared(tmp_path, example, monkeypatch)
    original = restart._copy

    def changing_copy(item, output):
        original(item, output)
        if output.name == "authority.json":
            if change == "expiry":
                monkeypatch.setattr(restart, "_now_ms", lambda: 123456789)
            elif change == "source":
                with Path(latest.native_journal.path).open("ab") as stream:
                    stream.write(b"changed")
            else:
                Path(latest.worker_database.path + "-wal").write_bytes(b"pending")

    monkeypatch.setattr(restart, "_copy", changing_copy)
    with pytest.raises(Fault, match=code):
        restart.stage_journals(plan, target)
    assert not target.exists() and not list(tmp_path.glob(".journal-stage-*"))


def test_existing_destination_never_overwritten(tmp_path, example, monkeypatch):
    plan, _, target = prepared(tmp_path, example, monkeypatch)
    target.mkdir()
    keep = target / "retained.txt"
    keep.write_bytes(b"original")
    with pytest.raises(Fault, match="RESTART_DESTINATION_EXISTS"):
        restart.stage_journals(plan, target)
    assert keep.read_bytes() == b"original"


def test_cli_stages_without_exposing_private_manifest(tmp_path, example, monkeypatch, capsys):
    plan, _, target = prepared(tmp_path, example, monkeypatch)
    source = tmp_path / "plan.json"
    source.write_text(plan.model_dump_json(by_alias=True))
    restart.main(["--plan", str(source), "--destination", str(target)])
    result = json.loads(capsys.readouterr().out)
    assert set(result) == {"status", "manifest_digest", "launched"}
    assert result["status"] == "staged" and result["launched"] is False


def test_interrupted_publication_retains_partial_without_commit(tmp_path, example, monkeypatch):
    plan, latest, target = prepared(tmp_path, example, monkeypatch)
    raw = Path(latest.native_journal.path).read_bytes()
    original = restart.os.rename

    def interrupted(source, destination):
        if source.name == "worker.sqlite":
            raise OSError("synthetic publication interruption")
        return original(source, destination)

    monkeypatch.setattr(restart.os, "rename", interrupted)
    with pytest.raises(OSError, match="synthetic publication interruption"):
        restart.stage_journals(plan, target)
    assert (target / "native.jsonl").read_bytes() == raw
    assert not (target / "manifest.json").exists()
    assert Path(latest.native_journal.path).read_bytes() == raw
    with pytest.raises(Fault, match="RESTART_DESTINATION_EXISTS"):
        restart.stage_journals(plan, target)
