"""Stopped synthetic activation custody; no native or game launch."""

import hashlib
import importlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

from mcbench.storage import Fault, canonical


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    module = importlib.import_module("native_activation_source")
    origin, output = tmp_path / "source", tmp_path / "output"
    origin.mkdir()
    output.mkdir()
    db = sqlite3.connect(origin / "synthetic.sqlite")
    db.execute("CREATE TABLE native_profile (simulation INTEGER)")
    db.execute("INSERT INTO native_profile VALUES(1)")
    db.execute("CREATE TABLE native_jobs (state TEXT)")
    db.execute("INSERT INTO native_jobs VALUES('FINALIZED')")
    db.commit()
    db.close()
    (origin / "objects").mkdir()
    raw = b"public fixture artifact"
    blob = origin / "objects" / hashlib.sha256(raw).hexdigest()
    blob.write_bytes(raw)

    def seal(*, mutate=None):
        files = [
            {
                "path": p.relative_to(origin).as_posix(),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(origin.rglob("*"))
            if p.is_file() and p.name != "seal.json"
        ]
        if mutate:
            mutate(files)
        raw = canonical({"files": files})
        (origin / "seal.json").write_bytes(raw)
        return {
            "directory": str(origin),
            "seal_sha256": hashlib.sha256(raw).hexdigest(),
            "skill_set_ref": "cas:sha256:" + "a" * 64,
        }

    return module, origin, output, blob, seal


def test_copy_is_exact_preserves_source_and_does_not_create_source_sidecars(fixture):
    module, origin, output, blob, seal = fixture
    source = seal()
    before = {
        p.relative_to(origin).as_posix(): p.read_bytes() for p in origin.rglob("*") if p.is_file()
    }
    report = module.copy_activation_source(source, output)
    assert report["files"] == 2 and not report["dispatch_authorized"]
    assert (output / "objects" / blob.name).read_bytes() == blob.read_bytes()
    assert (output / "synthetic.sqlite").read_bytes() == (origin / "synthetic.sqlite").read_bytes()
    assert before == {
        p.relative_to(origin).as_posix(): p.read_bytes() for p in origin.rglob("*") if p.is_file()
    }
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        module.copy_activation_source(source, output)


@pytest.mark.parametrize(
    "case",
    [
        "unlisted",
        "missing",
        "traversal",
        "duplicate",
        "case_collision",
        "bad_hash",
        "wrong_bytes",
        "bool_bytes",
        "wal",
        "journal",
        "live",
        "production",
        "hardlink",
        "changed_seal",
    ],
)
def test_bad_source_rejects_before_destination_copy(fixture, case):
    module, origin, output, blob, seal = fixture
    if case in {"live", "production"}:
        db = sqlite3.connect(origin / "synthetic.sqlite")
        db.execute(
            "UPDATE native_jobs SET state='RUNNING'"
            if case == "live"
            else "UPDATE native_profile SET simulation=0"
        )
        db.commit()
        db.close()

    def mutate(files):
        if case == "traversal":
            files[0]["path"] = "objects/../../private"
        elif case == "duplicate":
            files.append(dict(files[0]))
        elif case == "case_collision":
            files.append(files[0] | {"path": files[0]["path"].upper()})
        elif case == "bad_hash":
            files[0]["sha256"] = "not-a-hash"
        elif case == "wrong_bytes":
            files[0]["bytes"] = 1
        elif case == "bool_bytes":
            files[0]["bytes"] = True

    source = seal(mutate=mutate)
    if case == "unlisted":
        (origin / "objects" / ("b" * 64)).write_bytes(b"unsealed")
    elif case == "missing":
        blob.unlink()
    elif case in {"wal", "journal"}:
        (origin / ("synthetic.sqlite-" + case)).write_bytes(b"uncheckpointed")
    elif case == "hardlink":
        os.link(blob, origin.parent / "linked-blob")
    elif case == "changed_seal":
        (origin / "seal.json").write_bytes(b"{}")
    with pytest.raises(Fault):
        module.copy_activation_source(source, output)
    assert not list(output.iterdir())


@pytest.mark.parametrize("change", ["blob", "seal", "wal", "destination"])
def test_copy_time_change_retains_partial_output_and_refuses_success(fixture, monkeypatch, change):
    module, origin, output, blob, seal = fixture
    source = seal()
    original = module.shutil.copyfile
    changed = False

    def copy(a, b):
        nonlocal changed
        result = original(a, b)
        if not changed:
            changed = True
            if change == "blob":
                blob.write_bytes(b"changed source")
            elif change == "seal":
                (origin / "seal.json").write_bytes(b"{}")
            elif change == "wal":
                (origin / "synthetic.sqlite-wal").write_bytes(b"new WAL")
            else:
                Path(b).write_bytes(b"changed destination")
        return result

    monkeypatch.setattr(module.shutil, "copyfile", copy)
    with pytest.raises(Fault):
        module.copy_activation_source(source, output)
    assert list(output.iterdir())  # Preserve interrupted output; no implicit rearm.


def test_actual_uncheckpointed_sqlite_wal_is_never_ignored(fixture):
    module, origin, output, _, seal = fixture
    db = sqlite3.connect(origin / "synthetic.sqlite")
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA wal_autocheckpoint=0")
        db.execute("UPDATE native_jobs SET state='RUNNING'")
        db.commit()
        source = seal()
        assert (origin / "synthetic.sqlite-wal").stat().st_size > 0
        with pytest.raises(Fault, match="ACTIVATION_SOURCE_NOT_FROZEN"):
            module.copy_activation_source(source, output)
        assert not list(output.iterdir())
    finally:
        db.close()


def test_parent_source_and_destination_cannot_overlap(fixture):
    module, origin, _, _, seal = fixture
    target = origin / "nested"
    target.mkdir()
    with pytest.raises(Fault, match="ACTIVATION_SOURCE_OVERLAP"):
        module.copy_activation_source(seal(), target)


def test_nonselected_metadata_is_not_copied(fixture):
    module, origin, output, _, seal = fixture
    (origin / "operator-private.json").write_text(json.dumps({"private": "source provenance"}))
    module.copy_activation_source(seal(), output)
    assert not (output / "operator-private.json").exists()
