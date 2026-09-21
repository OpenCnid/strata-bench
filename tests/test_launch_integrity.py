"""Owned-file Windows integrity controls; no OAuth/game processes."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from mcbench.launch_integrity import FileLease, IntegrityError, encode, read_manifest, safe, snapshot

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows deny-write sharing contract")


def test_windows_lease_denies_write_delete_replace_and_parent_rename(tmp_path):
    tree = tmp_path / "sealed"
    tree.mkdir()
    source = tree / "source.py"
    source.write_bytes(b"original")
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"changed")
    with FileLease(snapshot([], [tree])) as lease:
        for mutation in (lambda: source.write_bytes(b"changed"), source.unlink,
                         lambda: replacement.replace(source), lambda: tree.rename(tmp_path / "moved")):
            with pytest.raises(OSError):
                mutation()
        lease.recheck()
        assert source.read_bytes() == b"original"
    source.write_bytes(b"after release")


def test_changed_bytes_and_partial_acquisition_release_prior_handles(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    inventory = snapshot([a, b], [])
    b.write_bytes(b"changed")
    with pytest.raises(IntegrityError, match="BOOTSTRAP_FILE_CHANGED"):
        FileLease(inventory)
    a.write_bytes(b"not left locked")


def test_native_lease_exceeds_crt_capacity_and_releases_after_late_hash_failure(tmp_path):
    """The authentic pack needs more than the CRT's 8,192 file descriptors."""
    tree = tmp_path / "large"
    tree.mkdir()
    entries = []
    for number in range(8300):
        path = tree / f"{number:05}.bin"
        raw = bytes(range(256)) * 517 if number == 8299 else str(number).encode()
        path.write_bytes(raw)
        entries.append({"path": str(path), "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()})
    inventory = {"schema": "strata/LaunchFileInventory/1", "files": entries, "trees": []}
    first, last = tree / "00000.bin", tree / "08299.bin"
    with FileLease(inventory) as lease:
        for path in (first, last):
            with pytest.raises(OSError):
                path.write_bytes(b"blocked")
            with pytest.raises(OSError):
                path.unlink()
        # Real stdio still works while all 8,300 native file handles are held.
        with (tmp_path / "stdio.txt").open("w") as stream:
            stream.write("available")
        lease.recheck()
    with pytest.raises(IntegrityError, match="BOOTSTRAP_LEASE_CLOSED"):
        lease.recheck()
    entries[-1]["sha256"] = "0" * 64
    with pytest.raises(IntegrityError, match="BOOTSTRAP_FILE_CHANGED"):
        FileLease(inventory)
    # Both earliest and failing handles must have been released.
    first.write_bytes(b"released")
    last.write_bytes(b"released")


def test_long_paths_are_inventoried_and_locked_without_missing_file_bypass(tmp_path):
    tree = safe(tmp_path / ("long" * 20) / ("nested" * 20))
    tree.mkdir(parents=True)
    path = tree / ("source" * 15 + ".py")
    path.write_bytes(b"long path")
    inventory = snapshot([], [safe(tmp_path)])
    assert any(entry["bytes"] == 9 and len(entry["path"]) > 260 for entry in inventory["files"])
    with FileLease(inventory):
        with pytest.raises(OSError):
            path.write_bytes(b"changed")


def test_added_file_is_detected_before_launch_and_during_lease(tmp_path):
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "one").write_bytes(b"one")
    inventory = snapshot([], [tree])
    with FileLease(inventory) as lease:
        (tree / "added.py").write_bytes(b"unlisted")
        with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
            lease.recheck()
    with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
        FileLease(inventory)


def test_manifest_is_content_bound_and_duplicate_paths_rejected(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_bytes(encode({"schema": "strata/NativeBootstrap/1"}))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert read_manifest(path, sha)["schema"] == "strata/NativeBootstrap/1"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(IntegrityError, match="BOOTSTRAP_DIGEST"):
        read_manifest(path, sha)
    inventory = snapshot([path], [])
    inventory["files"] *= 2
    with pytest.raises(IntegrityError, match="BOOTSTRAP_DUPLICATE"):
        FileLease(inventory)


def test_isolated_bootstrap_ignores_site_and_environment_and_blocks_unlisted_import(tmp_path):
    from mcbench import sealed_broker
    # Importing the bootstrap above installs only its sibling search root, no service.
    source = tmp_path / "source"
    package = source / "mcbench"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    result = tmp_path / "result.json"
    code = '''import sys,json
def run_config(path,**kwargs):
    from launch_integrity import IntegrityError
    result={"site_loaded":"site" in sys.modules,"isolated":sys.flags.isolated}
    try: import unsealed
    except IntegrityError as error: result["denied"]=str(error)
    path.write_text(json.dumps(result))
'''
    (package / "broker_stdio.py").write_text(code, encoding="utf-8")
    inventory = snapshot([], [source])
    import importlib.util
    import marshal
    import struct
    original = package / "broker_stdio.py"
    cached = Path(importlib.util.cache_from_source(str(original)))
    cached.parent.mkdir()
    cached.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack("<III", 0,
        int(original.stat().st_mtime), original.stat().st_size) + marshal.dumps(compile(
            "raise Exception('unsealed bytecode executed')", str(original), "exec")))
    (source / "unsealed.py").write_text("raise Exception('must not execute')", encoding="utf-8")
    # No tree inventory here: this separate test isolates origin checking itself.
    inventory["trees"] = []
    manifest = {"schema": "strata/NativeBootstrap/1", "python": str(Path(sys.executable).resolve()),
        "python_paths": [str(source)], "broker_config": str(result), "inventory": inventory}
    path = tmp_path / "manifest.json"
    path.write_bytes(encode(manifest))
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "sitecustomize.py").write_text("raise Exception('site executed')", encoding="utf-8")
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    env["PYTHONPATH"] = str(shadow)
    run = subprocess.run([sys.executable, "-I", "-S", "-B", sealed_broker.__file__, "--manifest",
        str(path), "--sha256", hashlib.sha256(path.read_bytes()).hexdigest()],
        env=env, cwd=shadow, capture_output=True, timeout=20)
    assert run.returncode == 0, run.stderr.decode()
    assert json.loads(result.read_bytes()) == {"site_loaded": False, "isolated": 1,
                                              "denied": "BOOTSTRAP_IMPORT_FORBIDDEN"}


@pytest.mark.parametrize("mutation", ["arguments", "environment", "native_executable", "omitted_file",
                                      "workspace_overlap", "job_scope", "catalog_unpinned",
                                      "catalog_pinned", "valid"])
def test_native_seal_binds_command_environment_and_all_bootstrap_files(tmp_path, mutation):
    from types import SimpleNamespace
    from mcbench.native_bootstrap import acquire_native_bootstrap
    from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings
    from mcbench.storage import Fault
    names = ("python", "broker_bootstrap", "process_bootstrap", "broker_config", "native_executable")
    files = {name: str(tmp_path / name) for name in names}
    for name, path in files.items():
        Path(path).write_text(name, encoding="utf-8")
    Path(files["broker_config"]).write_text(json.dumps({"schema": "strata/SealedBrokerConfig/1",
        "runtime_id": "job", "database": str(tmp_path / "operator.sqlite"),
        "objects": str(tmp_path / "objects"), "worker_grant": None}), encoding="utf-8")
    inventory = snapshot(map(Path, files.values()), [])
    if mutation == "omitted_file":
        inventory["files"] = [entry for entry in inventory["files"] if not entry["path"].endswith("broker_bootstrap")]
    manifest = {"schema": "strata/NativeBootstrap/1", "inventory": inventory,
                "python_paths": [str(tmp_path / "imports")], **files}
    path = tmp_path / "manifest.json"
    path.write_bytes(encode(manifest))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    server = {"command": files["python"], "args": ["-I", "-S", "-B", files["broker_bootstrap"],
        "--manifest", str(path), "--sha256", sha], "env": {}, "required": True,
        "enabled_tools": list(BROKER_TOOLS), "tools": {"artifact_write": {"approval_mode": "approve"},
                                                       "game": {"approval_mode": "approve"}}}
    plan = SimpleNamespace(bootstrap_manifest=str(path), bootstrap_digest=sha,
        executable=files["native_executable"], workspace=str(tmp_path / "gameplay"), job_id="job",
        config_overrides=restricted_settings() | {
            "mcp_servers.strata_broker": server})
    if mutation == "arguments":
        server["args"].remove("-S")
    elif mutation == "environment":
        server["env"]["PYTHONPATH"] = str(tmp_path)
    elif mutation == "native_executable":
        plan.executable += "-different"
    elif mutation == "workspace_overlap":
        plan.workspace = str(tmp_path)
    elif mutation == "job_scope":
        plan.job_id = "other"
    elif mutation in {"catalog_unpinned", "catalog_pinned"}:
        plan.config_overrides["model_catalog_json"] = files["python"] if mutation == "catalog_pinned" else str(tmp_path / "unlisted.json")
    if mutation in {"valid", "catalog_pinned"}:
        with acquire_native_bootstrap(plan):
            with pytest.raises(OSError):
                Path(files["broker_config"]).write_bytes(b"changed")
        return
    with pytest.raises(Fault, match="BOOTSTRAP_LAUNCH_MISMATCH|BOOTSTRAP_FILE_UNPINNED|"
                       "BOOTSTRAP_WORKSPACE_OVERLAP|BOOTSTRAP_BROKER_CONFIG|BOOTSTRAP_CATALOG_UNPINNED"):
        acquire_native_bootstrap(plan)
