"""Read-only PackLock binding for the first launch of a fresh materialization.

This is preflight integrity, not ongoing writer exclusion or checkpoint admission.
Runtime-mutated instances need a separate recovery policy and cannot pass here.
"""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

from .contracts import Digest, Id, Ref, Strict
from .inventory import file_hash, scan_tree, template_path
from .pack_policies import reviewed_vendor_paths
from .provisioning import TARGETS, VanillaLaunchProfile, parse_launch_profile, validate_launch_environment
from .records import FileEntry, PackLock
from .storage import CAS, Principal, canonical, digest, reject_links, require


class PackLaunchBinding(Strict):
    store: str
    request_id: Id
    lock: Ref
    instance: str


class VanillaWorldSource(Strict):
    snapshot: str
    sha256: Digest


class RestoredPackLaunchBinding(PackLaunchBinding):
    restoration: VanillaWorldSource


def parse_pack_binding(value):
    model = RestoredPackLaunchBinding if isinstance(value, dict) and "restoration" in value else PackLaunchBinding
    return model.model_validate(value)


def _absolute(value):
    path = Path(value)
    require(path.is_absolute() and path == Path(os.path.abspath(path)), "UNSAFE_PATH")
    reject_links(path)
    return path


def resolve_pack_launch(binding: PackLaunchBinding, role: str, *, simulation=False, worker_invocation=None):
    """Resolve an exact sealed command without creating/migrating a store.

The caller must keep the binding private and enforce its own process, input,
credential, runtime dependency and mutable-world boundaries.
"""
    require(role in {"client", "server"}, "ROLE_MISMATCH")
    store = _absolute(binding.store)
    database = store / "controller.sqlite"
    objects = store / "objects"
    reject_links(database)
    reject_links(objects)
    require(database.is_file() and objects.is_dir(), "AWAITING_ARTIFACT")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")  # One durable snapshot; no schema initialization.
        profile = connection.execute("SELECT simulation FROM provisioning_profile").fetchall()
        require(len(profile) == 1 and profile[0][0] == int(simulation), "SIMULATION_STORE")
        row = connection.execute("SELECT * FROM provisioning WHERE id=?",
                                 (binding.request_id,)).fetchone()
        require(row is not None, "REQUEST_MISSING")
        require(row["state"] == "SEALED" and row["sealed"], "UNSEALED_PACK")
        require(row["sealed"] == binding.lock, "PACK_BINDING_MISMATCH")
        cas = CAS(SimpleNamespace(connection=connection), objects)
        principal, namespace = Principal("pack-launch", "operator"), "pack:" + binding.request_id

        def read(ref):
            metadata = connection.execute("SELECT visibility FROM objects WHERE namespace=? AND ref=?",
                                          (namespace, ref)).fetchone()
            require(metadata is not None and metadata[0] == "operator", "FORBIDDEN")
            return json.loads(cas.read(principal, namespace, ref, max_bytes=64 * 1024**2))

        lock = PackLock.model_validate(read(binding.lock))
        require(lock.status == "sealed" and lock.lock_id == binding.request_id
                and lock.is_example == simulation, "PACK_BINDING_MISMATCH")
        require(row["target"] in TARGETS and all(getattr(lock, key) == value
                for key, value in TARGETS[row["target"]].items() if key != "loader")
                and lock.loader.model_dump() == TARGETS[row["target"]]["loader"], "RELEASE_MISMATCH")
        require(lock.resolved_inventory == row["inventory"], "PACK_BINDING_MISMATCH")
        inventory = read(lock.resolved_inventory)
        require(inventory.get("schema") == "strata/InstalledInventory/1"
                and inventory.get("is_example") is simulation
                and digest(inventory) == lock.installed_root_digest, "CORRUPT_EVIDENCE")
        report = read(lock.acquisition_report)
        require(report.get("schema") == "strata/AcquisitionReport/1"
                and report.get("is_example") is simulation and report.get("receipt") == row["receipt"]
                and report.get("inventory") == row["inventory"], "PACK_BINDING_MISMATCH")
        launch = parse_launch_profile(read(lock.launch_profile))
        require(launch.is_example == simulation, "EXAMPLE_NOT_EXECUTABLE")
        require(worker_invocation is None or role == "client" and isinstance(launch, VanillaLaunchProfile),
                "WORKER_INVOCATION_UNSUPPORTED")
        if isinstance(launch, VanillaLaunchProfile):
            require(row["target"] == "vanilla", "RELEASE_MISMATCH")
        command = getattr(launch, role).model_copy(deep=True)
        read(command.reviewed_bootstrap)
        target = row["target"]

    instance = _absolute(binding.instance)
    restored = isinstance(binding, RestoredPackLaunchBinding)
    if restored:
        require(target == "vanilla" and isinstance(launch, VanillaLaunchProfile) and not simulation,
                "PACK_RESTORE_UNSUPPORTED")
    require(instance.is_dir() and not instance.is_relative_to(store)
            and not store.is_relative_to(instance), "UNSAFE_PATH")
    require({p.name for p in instance.iterdir()} == {"client", "server", ".strata-instance.json"},
            "MATERIALIZATION_CHANGED")
    marker = instance / ".strata-instance.json"
    reject_links(marker)
    expected_marker = {"schema": "strata/Materialization/1", "is_example": simulation,
                       "lock": binding.lock, "inventory_digest": lock.installed_root_digest}
    if restored:
        from .pack_restore import load_restoration, restoration_marker, restored_layout
        world = load_restoration(binding, inventory)
        expected_marker = restoration_marker(binding, world)
    require(marker.is_file() and marker.stat().st_nlink == 1 and marker.stat().st_size < 4096
            and marker.read_bytes() == canonical(expected_marker), "PACK_BINDING_MISMATCH")
    reviewed = reviewed_vendor_paths(target)
    entries = [FileEntry.model_validate(entry) for entry in inventory["files"]]
    require({entry.role for entry in entries} == {"client", "server"}, "ROLE_MISMATCH")
    for selected in ("client", "server"):
        root = instance / selected
        if restored and selected == "server":
            restored_layout(root, world)
            continue
        declared = sorted(({"path": entry.path, "digest": entry.digest, "bytes": entry.bytes}
                           for entry in entries if entry.role == selected), key=lambda e: e["path"])
        require(scan_tree(root, reviewed_world_paths=reviewed) == declared, "MATERIALIZATION_CHANGED")
        # Empty added directories also change the installation; scan_tree hashes files.
        expected_dirs = {p.as_posix() for entry in declared for p in Path(entry["path"]).parents
                         if str(p) != "."}
        actual_dirs = {str((Path(current) / name).relative_to(root).as_posix())
                       for current, dirs, _ in os.walk(root) for name in dirs}
        require(actual_dirs == expected_dirs, "MATERIALIZATION_CHANGED")
    relative = (Path(".") if command.working_directory == "."
                else template_path(command.working_directory))
    working_directory = instance / role / relative
    require(working_directory.is_dir(), "AWAITING_ARTIFACT")
    executable = _absolute(command.executable_path)
    require(executable.stat().st_nlink == 1 and file_hash(executable) == command.executable.digest,
            "HASH_MISMATCH")
    require(all("\x00" not in arg for arg in command.arguments), "INVALID_ARGUMENT")
    validate_launch_environment(command.environment)
    command.working_directory = str(working_directory)
    result = {"schema": "strata/ResolvedPackLaunch/1", "is_example": simulation,
            "request_id": binding.request_id, "lock": binding.lock, "target": target,
            "inventory_digest": lock.installed_root_digest, "launch_profile": lock.launch_profile,
            "role": role, "instance": str(instance), "launch": command.model_dump(),
            "scope": "fresh_materialization_preflight", "writer_custody_qualified": False,
            "campaign_admission": False}
    if restored:
        result.update(scope="restored_materialization_preflight", restoration=binding.restoration.model_dump())
    if isinstance(launch, VanillaLaunchProfile) and role == "client":
        from .pack_worker import resolve_worker_invocation
        result.update(resolve_worker_invocation(launch, worker_invocation, binding))
    return result
