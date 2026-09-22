"""Prepare a private vanilla worker plus its stdlib-only Windows ACL helper.

No accounts, credentials, game state, instructions or evaluator material are
copied. Preparation does not authenticate, start an avatar or admit a campaign.
"""

import hashlib
import os
from pathlib import Path
import shutil

from .launch_integrity import FileLease, encode, safe, snapshot, tree_files
from .storage import digest, require, safe_relative


def launch_path(path: Path) -> str:
    """Node's entrypoint resolver needs DOS/UNC paths, not extended Win32 paths.

    Keep extended paths in the file inventory for safe long-path reads/leases.
    This only converts the spelling of an already validated absolute path.
    """
    value = str(safe(path))
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    return value[4:] if value.startswith("\\\\?\\") else value


def prepare_worker_bundle(repository: Path, node: Path, python_root: Path, destination: Path,
                          dependency_report: dict, dependency_ref: str):
    require(all(".." not in Path(p).parts for p in (repository, node, python_root, destination)),
            "WORKER_BUNDLE_PATH")
    repository, node, python_root, destination = map(safe, (repository, node, python_root, destination))
    require(os.name == "nt", "WORKER_BUNDLE_PLATFORM_UNQUALIFIED")
    require(not destination.exists() and not destination.with_suffix(".manifest.json").exists(),
            "BOOTSTRAP_TARGET_EXISTS")
    require(all(not destination.is_relative_to(p) and not p.is_relative_to(destination)
                for p in (repository, python_root, node.parent)), "WORKER_BUNDLE_OVERLAP")
    require(dependency_report.get("schema") == "strata/NpmInstalledRuntime/1"
            and dependency_ref == "cas:sha256:" + digest(dependency_report)
            and digest(dependency_report.get("files")) == dependency_report.get("files_digest"),
            "WORKER_DEPENDENCIES_UNVERIFIED")
    backend = repository / "backends/mineflayer"
    assignments = {}

    def add(source, relative):
        source = safe(source)
        require(source.is_file() and source.stat().st_nlink == 1, "WORKER_BUNDLE_FILE_UNSAFE")
        relative = safe_relative(relative).as_posix()
        require(relative not in assignments, "WORKER_BUNDLE_COLLISION")
        assignments[relative] = source

    add(node, "node/node.exe")
    for name in ("package.json", "package-lock.json", "tools/auth_cache_acl.py"):
        add(backend / name, "backends/mineflayer/" + name)
    require(hashlib.sha256((backend / "package.json").read_bytes()).hexdigest()
            == dependency_report["manifest_sha256"]
            and hashlib.sha256((backend / "package-lock.json").read_bytes()).hexdigest()
            == dependency_report["lock_sha256"], "WORKER_DEPENDENCIES_CHANGED")
    for relative, entry in dependency_report["files"].items():
        path = safe_relative(relative)
        require(path.parts[0] == "node_modules", "WORKER_DEPENDENCIES_UNVERIFIED")
        add(backend / path, "backends/mineflayer/" + relative)
    actual_dependencies = {Path(p).relative_to(backend).as_posix() for p in tree_files(backend / "node_modules")}
    require(actual_dependencies == set(dependency_report["files"]), "WORKER_DEPENDENCIES_CHANGED")
    for value in tree_files(backend / "dist/src"):
        path = Path(value)
        add(path, path.relative_to(repository).as_posix())
    for name in ("ActionBatch", "ActionAck", "Observation", "RpcRequest"):
        relative = f"schemas/v1/public/{name}.json"
        add(repository / relative, relative)
    exclusions = []
    for value in tree_files(python_root):
        path = Path(value)
        relative = path.relative_to(python_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc" or relative.is_relative_to("Lib/site-packages"):
            exclusions.append(relative.as_posix())
            continue
        # Preserve the existing worker's root-relative helper lookup. This is
        # a copied base interpreter layout, not a virtualenv or host redirector.
        add(path, ".venv/Scripts/" + relative.as_posix())
    require(all(name in assignments for name in (".venv/Scripts/python.exe",
            ".venv/Scripts/Lib/encodings/__init__.py", ".venv/Scripts/DLLs/_ctypes.pyd",
            "backends/mineflayer/dist/src/worker.js", "backends/mineflayer/dist/src/auth_cache.js")),
            "WORKER_BUNDLE_INCOMPLETE")
    source = snapshot(list(assignments.values()), [backend / "node_modules", backend / "dist/src"])
    pins = {entry["path"]: entry for entry in source["files"]}
    for name, entry in dependency_report["files"].items():
        pin = pins[str(safe(backend / name))]
        require(pin["bytes"] == entry["bytes"] and pin["sha256"] == entry["sha256"],
                "WORKER_DEPENDENCIES_CHANGED")
    # Validate before creating an output. If later copying fails, retain the
    # partial private directory for diagnosis; it cannot be reused or launched.
    with FileLease(source) as lease:
        destination.mkdir(parents=True)
        for relative, path in assignments.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        lease.recheck()
        inventory = snapshot([], [destination])
        copied = {Path(entry["path"]).relative_to(destination).as_posix(): entry for entry in inventory["files"]}
        require(set(copied) == set(assignments) and all(
            copied[name]["sha256"] == pins[str(path)]["sha256"]
            and copied[name]["bytes"] == pins[str(path)]["bytes"] for name, path in assignments.items()),
            "WORKER_BUNDLE_COPY_CHANGED")
    manifest = {"schema": "strata/WorkerRuntimeBundle/1", "profile": "vanilla1192-private-worker/1",
        "root": launch_path(destination), "node": launch_path(destination / "node/node.exe"),
        "worker": launch_path(destination / "backends/mineflayer/dist/src/worker.js"),
        "python": launch_path(destination / ".venv/Scripts/python.exe"),
        "acl_helper": launch_path(destination / "backends/mineflayer/tools/auth_cache_acl.py"),
        "python_arguments": ["-I", "-S", "-B"], "dependency_evidence": dependency_ref,
        "source_inventory": source, "inventory": inventory,
        "excluded_python_files": exclusions, "exclusion_policy": "no-bytecode-or-site-packages/1",
        "auth_cache_copied": False, "game_state_copied": False, "campaign_admission": False,
        "runtime_qualified": False, "isolation_qualified": False}
    manifest_path = destination.with_suffix(".manifest.json")
    raw = encode(manifest)
    with manifest_path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {"manifest": launch_path(manifest_path), "sha256": hashlib.sha256(raw).hexdigest(),
            "files": len(inventory["files"]), "bytes": sum(e["bytes"] for e in inventory["files"]),
            "campaign_admission": False, "runtime_qualified": False}
