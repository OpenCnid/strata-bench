"""Copied synthetic checkpoint fixture, separate from actual native execution."""

import hashlib
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_activation_probe import ActivationProbe
from mcbench.native import NativeExec
from mcbench.storage import CAS, Database, Fault, canonical
from test_native_skill_activation import activate, admitted as _admitted, stopped as _stopped

admitted = _admitted
stopped = _stopped


def test_probe_copies_verified_source_without_reauthorizing(stopped, tmp_path):
    service, checkpoint = activate(stopped)
    ref = service.create(checkpoint)
    origin = tmp_path / "sealed-source"
    origin.mkdir()
    with sqlite3.connect(origin / "synthetic.sqlite") as dest:
        service.db.connection.backup(dest)
    shutil.copytree(service.cas.root, origin / "objects")
    files = [{"path": p.relative_to(origin).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in origin.rglob("*") if p.is_file()]
    raw = canonical({"files": files})
    (origin / "seal.json").write_bytes(raw)
    source = {"directory": str(origin), "seal_sha256": hashlib.sha256(raw).hexdigest(), "skill_set_ref": ref}
    target = tmp_path / "new-native"
    target.mkdir()
    probe = ActivationProbe(source, target)
    db = Database(target / "synthetic.sqlite")
    try:
        runtime = NativeExec(db, CAS(db, target / "objects"), simulation=True)
        before = runtime.budgets.status("a1")
        plan = probe.prepare(runtime, stopped[1])
        assert runtime.budgets.status("a1") == before == service.runtime.budgets.status("a1")
        assert plan.epoch == 2 and plan.skill_activation_ref == plan.helper_skill_activation_ref == ref
        assert plan.purpose == "campaign"
        assert Path(plan.workspace, "active/revisions.json").is_file()
        assert not list(origin.glob("activated-workspace"))
    finally:
        db.close()
    damaged = next((origin / "objects").rglob("*.blob"), None)
    if damaged is None:
        damaged = next(p for p in (origin / "objects").rglob("*") if p.is_file())
    damaged.write_bytes(b"changed source")
    denied = tmp_path / "denied"
    denied.mkdir()
    with pytest.raises(Fault, match="ACTIVATION_SOURCE_CHANGED"):
        ActivationProbe(source, denied)
    assert not list(denied.iterdir())
