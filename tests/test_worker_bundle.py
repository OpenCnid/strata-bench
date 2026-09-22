"""Synthetic software exercises private packaging, source binding and failed-copy retention."""

import hashlib
import json

import pytest

from mcbench.storage import Fault, canonical, digest
from mcbench.worker_bundle import prepare_worker_bundle


@pytest.fixture
def inputs(tmp_path):
    repository, python, node_root = (tmp_path / name for name in ("repository", "python", "node"))
    backend = repository / "backends/mineflayer"

    def put(path, data=b"synthetic software"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    for relative in ("package.json", "package-lock.json", "tools/auth_cache_acl.py",
                     "dist/src/worker.js", "dist/src/auth_cache.js", "node_modules/fixture/index.js"):
        put(backend / relative)
    for name in ("ActionBatch", "ActionAck", "Observation", "RpcRequest"):
        put(repository / f"schemas/v1/public/{name}.json", b"{}")
    put(repository / "AGENTS.md", b"OPERATOR-ONLY-CANARY")
    put(repository / ".strata/auth.json", b"SYNTHETIC-SECRET-CANARY")
    for relative in ("python.exe", "python312.dll", "Lib/encodings/__init__.py", "DLLs/_ctypes.pyd",
                     "Lib/__pycache__/pathlib.cpython-312.pyc", "Lib/site-packages/unreviewed.pth"):
        put(python / relative)
    put(node_root / "node.exe")
    payload = backend / "node_modules/fixture/index.js"
    files = {"node_modules/fixture/index.js": {"bytes": payload.stat().st_size,
              "sha256": hashlib.sha256(payload.read_bytes()).hexdigest()}}
    report = {"schema": "strata/NpmInstalledRuntime/1", "files": files, "files_digest": digest(files),
              "manifest_sha256": hashlib.sha256((backend / "package.json").read_bytes()).hexdigest(),
              "lock_sha256": hashlib.sha256((backend / "package-lock.json").read_bytes()).hexdigest()}
    return repository, node_root / "node.exe", python, tmp_path / "bundle", report


def prepare(inputs, **updates):
    repository, node, python, destination, report = inputs
    return prepare_worker_bundle(repository, node, python, updates.get("destination", destination),
        updates.get("report", report), updates.get("ref", "cas:sha256:" + digest(report)))


def test_only_software_is_copied_and_every_output_is_pinned(inputs):
    result = prepare(inputs)
    raw = open(result["manifest"], "rb").read()
    manifest = json.loads(raw)
    for name in ("root", "node", "worker", "python", "acl_helper"):
        assert not manifest[name].startswith("\\\\?\\")
    assert manifest["root"] == str(inputs[3])
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["python_arguments"] == ["-I", "-S", "-B"]
    assert not manifest["runtime_qualified"] and not manifest["campaign_admission"]
    assert not manifest["auth_cache_copied"] and not manifest["game_state_copied"]
    output = inputs[3]
    assert not (output / "AGENTS.md").exists() and not (output / ".strata").exists()
    assert not (output / ".venv/Scripts/Lib/site-packages").exists()
    assert not (output / ".venv/Scripts/Lib/__pycache__").exists()
    assert len(manifest["excluded_python_files"]) == 2
    paths = {entry["path"] for entry in manifest["inventory"]["files"]}
    assert result["files"] == len(paths) == len([p for p in output.rglob("*") if p.is_file()])
    for entry in manifest["inventory"]["files"]:
        with open(entry["path"], "rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"]
    assert b"CANARY" not in canonical(manifest)
    # Independent copy: changing a source cannot change the prepared interpreter.
    (inputs[2] / "python.exe").write_bytes(b"changed")
    assert (output / ".venv/Scripts/python.exe").read_bytes() == b"synthetic software"


@pytest.mark.parametrize("change", ["reference", "report", "manifest", "lock", "dependency",
                                   "extra_dependency", "missing_python", "hardlink", "occupied", "overlap",
                                   "traversal"])
def test_invalid_source_never_publishes_a_manifest(inputs, change):
    repository, node, python, destination, report = inputs
    backend = repository / "backends/mineflayer"
    updates = {}
    if change == "reference":
        updates["ref"] = "cas:sha256:" + "a" * 64
    elif change == "report":
        updates["report"] = report | {"files_digest": "a" * 64}
        updates["ref"] = "cas:sha256:" + digest(updates["report"])
    elif change in {"manifest", "lock", "dependency", "extra_dependency"}:
        name = {"manifest": "package.json", "lock": "package-lock.json",
                "dependency": "node_modules/fixture/index.js", "extra_dependency": "node_modules/extra.js"}[change]
        (backend / name).write_bytes(b"changed")
    elif change == "missing_python":
        (python / "python.exe").unlink()
    elif change == "hardlink":
        (python / "alias").hardlink_to(node)
    elif change == "occupied":
        destination.mkdir()
    elif change == "traversal":
        updates["destination"] = repository.parent / "alias/../repository/bundle"
    else:
        updates["destination"] = repository / "bundle"
    with pytest.raises(Fault):
        prepare(inputs, **updates)
    assert not destination.with_suffix(".manifest.json").exists()
    assert not destination.exists() or change == "occupied"


def test_failed_copy_is_retained_but_cannot_be_reused_and_source_handles_close(inputs, monkeypatch):
    from mcbench import worker_bundle
    original = worker_bundle.shutil.copyfile
    calls = 0

    def fail(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic copy failure")
        return original(source, destination)

    monkeypatch.setattr(worker_bundle.shutil, "copyfile", fail)
    with pytest.raises(OSError, match="synthetic copy failure"):
        prepare(inputs)
    assert inputs[3].is_dir() and (inputs[3] / "node/node.exe").is_file()
    assert not inputs[3].with_suffix(".manifest.json").exists()
    with pytest.raises(Fault, match="BOOTSTRAP_TARGET_EXISTS"):
        prepare(inputs)
    inputs[1].write_bytes(b"handles released")
