"""Build a private sealed broker runtime from inspected installed dependencies.

This copies software only. Credentials and mutable controller/game stores stay
outside the bundle. A manifest is launch integrity evidence, not qualification.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from .launch_integrity import FileLease, encode, read_manifest, safe, snapshot, tree_files
from .native_broker_policy import BROKER_TOOLS, validate_broker_settings
from .storage import require

DEPENDENCIES = ("pydantic", "pydantic_core", "annotated_types", "typing_extensions",
                "typing_inspection", "rfc8785")


def copy_software(source, target):
    source, target = safe(source), safe(target)
    require(not target.exists(), "BOOTSTRAP_TARGET_EXISTS")
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return
    for value in tree_files(source):
        path = Path(value)
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)


def prepare_bundle(root, *, native_executable, plugin_root, broker_config, static_files=(), static_trees=()):
    root = safe(root)
    require(not root.exists(), "BOOTSTRAP_TARGET_EXISTS")
    root.mkdir(parents=True)
    # A dedicated interpreter tree avoids locking the user's shared Python install.
    copy_software(Path(sys.base_prefix), root / "python")
    source = root / "source"
    copy_software(Path(__file__).resolve().parent, source / "mcbench")
    dependencies = root / "dependencies"
    dependencies.mkdir()
    for name in DEPENDENCIES:
        spec = importlib.util.find_spec(name)
        require(spec is not None and spec.origin is not None, "BOOTSTRAP_DEPENDENCY_MISSING")
        origin = Path(spec.origin).resolve()
        location = origin.parent if origin.name == "__init__.py" else origin
        copy_software(location, dependencies / (name if location.is_dir() else origin.name))
    python = root / "python/python.exe"
    require(python.is_file(), "BOOTSTRAP_PLATFORM_UNQUALIFIED")
    config = json.loads(safe(broker_config).read_bytes())
    require(config.get("schema") == "strata/SealedBrokerConfig/1", "BOOTSTRAP_BROKER_CONFIG")
    files = [Path(native_executable), Path(broker_config), *map(Path, static_files)]
    if config["worker_grant"] is not None:
        files.append(Path(config["worker_grant"]))
    # Mutable DB/CAS, native session state and credentials are never inventoried/copied.
    inventory = snapshot(files, [root, Path(plugin_root), *map(Path, static_trees)])
    manifest = {"schema": "strata/NativeBootstrap/1", "policy": "windows-held-files-isolated-imports/1",
        "python": str(python), "python_paths": [str(source), str(dependencies),
            str(root / "python/Lib"), str(root / "python/DLLs"), str(root / "python")],
        "broker_config": str(Path(broker_config)), "native_executable": str(Path(native_executable)),
        "broker_bootstrap": str(source / "mcbench/sealed_broker.py"),
        "process_bootstrap": str(source / "mcbench/process_bootstrap.py"), "inventory": inventory}
    # Keep the manifest outside the inventoried root to avoid self-reference.
    path = root.with_suffix(".manifest.json")
    require(not path.exists(), "BOOTSTRAP_TARGET_EXISTS")
    raw = encode(manifest)
    path.write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    server = {"command": str(python), "args": ["-I", "-S", "-B", manifest["broker_bootstrap"],
        "--manifest", str(path), "--sha256", sha], "env": {}, "required": True,
        "enabled_tools": list(BROKER_TOOLS), "tools": {"artifact_write": {"approval_mode": "approve"},
            "game": {"approval_mode": "approve"}}, "startup_timeout_sec": 30, "tool_timeout_sec": 10}
    return {"path": str(path), "sha256": sha, "server": server}


def acquire_native_bootstrap(plan):
    require(plan.bootstrap_manifest is not None and plan.bootstrap_digest is not None,
            "BOOTSTRAP_REQUIRED")
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    required = ("python", "broker_bootstrap", "process_bootstrap", "broker_config", "native_executable")
    pinned = {str(safe(entry["path"])).casefold() for entry in manifest["inventory"]["files"]}
    require(all(str(safe(manifest[key])).casefold() in pinned for key in required),
            "BOOTSTRAP_FILE_UNPINNED")
    validate_broker_settings(plan.config_overrides)
    server = plan.config_overrides["mcp_servers.strata_broker"]
    require(server.get("command") == manifest["python"] and server.get("args") == [
        "-I", "-S", "-B", manifest["broker_bootstrap"], "--manifest", plan.bootstrap_manifest,
        "--sha256", plan.bootstrap_digest] and server.get("env") == {} and
        manifest["native_executable"] == plan.executable, "BOOTSTRAP_LAUNCH_MISMATCH")
    workspace = safe(plan.workspace)
    private = [safe(manifest[key]) for key in required] + [safe(plan.bootstrap_manifest)]
    catalog = plan.config_overrides.get("model_catalog_json")
    if catalog is not None:
        require(str(safe(catalog)).casefold() in pinned, "BOOTSTRAP_CATALOG_UNPINNED")
        private.append(safe(catalog))
    private.extend(safe(path) for path in manifest["python_paths"])
    require(all(not path.is_relative_to(workspace) for path in private), "BOOTSTRAP_WORKSPACE_OVERLAP")
    config = json.loads(safe(manifest["broker_config"]).read_bytes())
    require(config.get("schema") == "strata/SealedBrokerConfig/1" and
            config.get("runtime_id") == plan.job_id, "BOOTSTRAP_BROKER_CONFIG")
    private.extend(safe(config[key]) for key in ("database", "objects"))
    if config["worker_grant"] is not None:
        private.append(safe(config["worker_grant"]))
    require(all(not path.is_relative_to(workspace) for path in private), "BOOTSTRAP_WORKSPACE_OVERLAP")
    # The manifest itself is locked alongside the content it names.
    inventory = manifest["inventory"]
    manifest_file = snapshot([Path(plan.bootstrap_manifest)], [])
    lease = FileLease(inventory | {"files": inventory["files"] + manifest_file["files"]})
    lease.managed_bootstrap = {"bootstrap_python": manifest["python"],
                               "bootstrap_script": manifest["process_bootstrap"]}
    return lease


def verify_native_inventory(plan):
    manifest = read_manifest(plan.bootstrap_manifest, plan.bootstrap_digest)
    for tree in manifest["inventory"]["trees"]:
        require(tree_files(tree["path"]) == tree["files"], "BOOTSTRAP_TREE_CHANGED")
