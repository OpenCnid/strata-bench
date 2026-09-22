"""Complete-set disk/publication faults on synthetic worlds and native receipts."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mcbench.checkpoints import Checkpoints
from mcbench.storage import CAS, Database, Fault, canonical
from test_native_checkpoint import admitted as _admitted, stage, stopped as _stopped

admitted, stopped = _admitted, _stopped


def process_environment():
    root = Path(__file__).resolve().parents[1]
    return dict(os.environ) | {"PYTHONPATH": os.pathsep.join(str(root / p) for p in ("src", "evaluator/src", "tools"))}


def prepared(stopped, tmp_path):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped, boundary="recovery")
    config = runtime.db.checkpoint_fixture["config"]
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(config, manifest, "operator")
    target = tmp_path / "staged"
    receipt = checkpoints.materialize_set("cp1", config, 2, target)
    return runtime, checkpoints, config, target, receipt


@pytest.mark.parametrize("admitted", ["full", "frozen-persistence", "frozen-skills", "no-self-play"], indirect=True)
def test_verified_staged_set_survives_controller_restart_without_new_charges(stopped, tmp_path):
    runtime, service, config, target, receipt = prepared(stopped, tmp_path)
    assert receipt["schema"] == "strata/RestoredCheckpoint/2"
    before = runtime.db.connection.total_changes
    budget = runtime.budgets.status("a1")
    result = service.verify_set("cp1", config, 2, target)
    assert result == receipt | {"verified_staging_only": True}
    assert not result["dispatch_authorized"] and result["requires_restore_assertions"]
    assert runtime.db.connection.total_changes == before
    assert runtime.budgets.status("a1") == budget
    db = Database(runtime.db.path)
    try:
        fresh = Checkpoints(db, CAS(db, runtime.cas.root))
        assert fresh.verify_set("cp1", config, 2, target) == result
        assert db.connection.execute("SELECT COUNT(*) FROM checkpoint_restorations").fetchone()[0] == 1
    finally:
        db.close()


@pytest.mark.parametrize("part", ["server/world/level.dat", "server/external/teams.dat",
    "workspace/notes/root.md", "private/backend_state.json", "private/runtime_state.json", "restore.json"])
def test_each_changed_world_agent_or_receipt_component_rejects(stopped, tmp_path, part):
    runtime, service, config, target, receipt = prepared(stopped, tmp_path)
    prefix = target if part.startswith("server/") or part == "restore.json" else \
        target / receipt["members"]["a1"]["directory"]
    changed = prefix / part
    data = changed.read_bytes()
    changed.write_bytes(bytes([data[0] ^ 1]) + data[1:])
    before = runtime.budgets.status("a1")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        service.verify_set("cp1", config, 2, target)
    assert runtime.budgets.status("a1") == before
    assert changed.read_bytes() != data  # The verifier must not repair the evidence.


@pytest.mark.parametrize("kind", ["extra_file", "empty_directory", "missing_file", "hardlink", "receipt_missing"])
def test_extra_missing_or_aliased_artifacts_reject(stopped, tmp_path, kind):
    _, service, config, target, _ = prepared(stopped, tmp_path)
    path = target / "server/world/level.dat"
    error = "MIXED_SNAPSHOT"
    if kind == "extra_file":
        (target / "future-notes.txt").write_text("later knowledge")
    elif kind == "empty_directory":
        (target / "unregistered-cache").mkdir()
    elif kind == "missing_file":
        path.unlink()
    elif kind == "hardlink":
        os.link(path, tmp_path / "external-write-route")
        error = "UNSAFE_PATH"
    else:
        (target / "restore.json").unlink()
    with pytest.raises(Fault, match=error):
        service.verify_set("cp1", config, 2, target)


def test_copied_receipt_and_legacy_output_do_not_register_a_restore(stopped, tmp_path):
    runtime, service, config, target, receipt = prepared(stopped, tmp_path)
    copy = tmp_path / "copied"
    shutil.copytree(target, copy)
    for legacy in (False, True):
        if legacy:
            (copy / "restore.json").write_bytes(canonical(receipt | {"schema": "strata/RestoredCheckpoint/1"}))
        with pytest.raises(Fault, match="RESTORE_SET_UNCOMMITTED"):
            service.verify_set("cp1", config, 2, copy)
    assert runtime.db.connection.execute("SELECT COUNT(*) FROM checkpoint_restorations").fetchone()[0] == 1
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        service.materialize_set("cp1", config, 2, copy)


def test_changed_durable_scope_or_receipt_cannot_bless_altered_set(stopped, tmp_path):
    runtime, service, config, target, receipt = prepared(stopped, tmp_path)
    with pytest.raises(Fault, match="RESTORE_SET_SCOPE"):
        service.verify_set("cp1", config, 3, target)
    modified = receipt | {"dispatch_authorized": True}
    runtime.db.connection.execute("UPDATE checkpoint_restorations SET receipt=?", (canonical(modified).decode(),))
    (target / "restore.json").write_bytes(canonical(modified))
    with pytest.raises(Fault, match="RESTORE_SET_SOURCE_CHANGED"):
        service.verify_set("cp1", config, 2, target)
    runtime.db.connection.execute("UPDATE checkpoint_restorations SET receipt=?", (canonical(receipt).decode(),))
    (target / "restore.json").write_bytes(canonical(receipt))
    runtime.db.connection.execute("UPDATE campaigns SET epoch=3")
    with pytest.raises(Fault, match="STALE_EPOCH"):
        service.verify_set("cp1", config, 2, target)
    for invalid in (True, 2.5, "3", 2**63):
        with pytest.raises(Fault, match="STALE_EPOCH"):
            service.materialize_set("cp1", config, invalid, tmp_path / "invalid-epoch")
    assert not (tmp_path / "invalid-epoch").exists()


def test_later_unknown_charge_is_retained_during_verification(stopped, tmp_path):
    runtime, service, config, target, _ = prepared(stopped, tmp_path)
    from mcbench.records import BudgetLedger
    reserve = BudgetLedger.model_validate_json(runtime.db.connection.execute("SELECT body FROM ledger WHERE "
        "json_extract(body,'$.operation_id')='child-call' AND json_extract(body,'$.posting')='reserve'").fetchone()[0])
    reserve.operation_id = reserve.ledger_id = reserve.source_event_id = "later-unknown"
    reserve.parent_operation_id = None
    runtime.budgets.post("a1", reserve)
    runtime.db.connection.execute("UPDATE operations SET uncertain=1 WHERE id='later-unknown'")
    before = runtime.budgets.status("a1")
    assert before["uncertain"] and not before["dispatch_allowed"]
    service.verify_set("cp1", config, 2, target)
    assert runtime.budgets.status("a1") == before


def test_failure_after_rename_retains_occupied_output_without_publication(stopped, tmp_path, monkeypatch):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped, boundary="recovery")
    config = runtime.db.checkpoint_fixture["config"]
    service = Checkpoints(runtime.db, runtime.cas)
    service.commit(config, manifest, "operator")
    original = runtime.db.event
    def fail(db, kind, body):
        if kind == "checkpoint.restored_set":
            raise OSError("injected journal failure after directory publication")
        return original(db, kind, body)
    monkeypatch.setattr(runtime.db, "event", fail)
    target = tmp_path / "occupied"
    before = runtime.budgets.status("a1")
    with pytest.raises(OSError, match="injected journal failure"):
        service.materialize_set("cp1", config, 2, target)
    assert json.loads((target / "restore.json").read_bytes())["dispatch_authorized"] is False
    assert not list(tmp_path.glob(".restore-set-*"))
    assert runtime.db.connection.execute("SELECT COUNT(*) FROM checkpoint_restorations").fetchone()[0] == 0
    with pytest.raises(Fault, match="RESTORE_SET_UNCOMMITTED"):
        service.verify_set("cp1", config, 2, target)
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        service.materialize_set("cp1", config, 2, target)
    assert runtime.budgets.status("a1") == before


def test_later_epoch_during_verification_cannot_return_success(stopped, tmp_path, monkeypatch):
    runtime, service, config, target, _ = prepared(stopped, tmp_path)
    verify = service._verify_staged_tree
    def changed(*args, **kwargs):
        verify(*args, **kwargs)
        runtime.db.connection.execute("UPDATE campaigns SET epoch=9")
    monkeypatch.setattr(service, "_verify_staged_tree", changed)
    with pytest.raises(Fault, match="STALE_EPOCH"):
        service.verify_set("cp1", config, 2, target)


def test_fresh_operator_process_verifies_then_rejects_changed_world(stopped, tmp_path):
    runtime, _, _, target, _ = prepared(stopped, tmp_path)
    command = [sys.executable, "tools/checkpoint_set.py", "--verify", "--database", str(runtime.db.path),
        "--objects", str(runtime.cas.root), "--checkpoint", "cp1", "--epoch", "2", "--directory", str(target)]
    before = runtime.budgets.status("a1")
    result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                            cwd=Path(__file__).resolve().parents[1], env=process_environment())
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["verified_staging_only"] and not report["dispatch_authorized"]
    (target / "server/world/level.dat").write_bytes(b"changed save")
    result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                            cwd=Path(__file__).resolve().parents[1], env=process_environment())
    assert result.returncode == 1 and json.loads(result.stdout)["code"] == "CORRUPT_EVIDENCE"
    assert runtime.budgets.status("a1") == before


@pytest.mark.parametrize("point", ["before_rename", "after_rename"])
def test_actual_process_loss_does_not_register_or_replay_partial_restore(stopped, tmp_path, point):
    runtime, service, config, _, _ = prepared(stopped, tmp_path)
    target = tmp_path / "interrupted"
    script = r'''
import json, os, sys
from pathlib import Path
import mcbench.checkpoints as module
from checkpoint_set import run
rename = module.os.rename
def interrupt(source, target):
    if sys.argv[4] == "after_rename":
        rename(source, target)
    os._exit(75)
module.os.rename = interrupt
run(Path(sys.argv[1]), Path(sys.argv[2]), "cp1", 2, Path(sys.argv[3]), verify=False)
'''
    before = runtime.budgets.status("a1")
    result = subprocess.run([sys.executable, "-c", script, str(runtime.db.path), str(runtime.cas.root),
        str(target), point], capture_output=True, text=True, timeout=30, env=process_environment())
    assert result.returncode == 75, result.stderr
    assert target.exists() is (point == "after_rename")
    assert runtime.db.connection.execute("SELECT COUNT(*) FROM checkpoint_restorations").fetchone()[0] == 1
    with pytest.raises(Fault, match="RESTORE_SET_UNCOMMITTED"):
        service.verify_set("cp1", config, 2, target)
    if target.exists():
        with pytest.raises(Fault, match="TARGET_EXISTS"):
            service.materialize_set("cp1", config, 2, target)
    assert runtime.budgets.status("a1") == before
