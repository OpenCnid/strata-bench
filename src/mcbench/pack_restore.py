"""Restore a pinned stopped vanilla world into a new sealed installation.

Private operator implementation: never a gameplay tool or checkpoint admission.
The original template and snapshot stay untouched; partial failures are retained.
"""

from contextlib import ExitStack
import os
from pathlib import Path
import shutil

from .inventory import file_hash
from .launch_integrity import FileLease, safe, snapshot
from .pack_launch import PackLaunchBinding, RestoredPackLaunchBinding, VanillaWorldSource, _absolute, resolve_pack_launch
from .storage import canonical, digest, require
from .vanilla_persistence import disposition, layout, template_files, verify_snapshot, write_new

POLICY = "vanilla1192-sealed-stopped-world-restore/1"


def load_restoration(binding, inventory):
    source = _absolute(binding.restoration.snapshot)
    for path in (_absolute(binding.instance), _absolute(binding.store)):
        require(not source.is_relative_to(path) and not path.is_relative_to(source), "PACK_RESTORE_OVERLAP")
    world = verify_snapshot(source, binding.restoration.sha256)
    require(world["schema"] == "strata/StoppedVanillaSnapshot/2"
            and world["pack"] == {"lock": binding.lock, "request_id": binding.request_id,
                                  "inventory_digest": digest(inventory)}
            and world["installed_inventory"] == inventory, "PACK_RESTORE_SOURCE")
    return world


def restoration_marker(binding, world):
    return {"schema": "strata/Materialization/2", "is_example": False, "lock": binding.lock,
            "inventory_digest": world["pack"]["inventory_digest"], "policy": POLICY,
            "restoration": binding.restoration.model_dump(), "complete_checkpoint": False,
            "dispatch_authorized": False, "writer_custody_qualified": False}


def restored_layout(root, world):
    """Require exactly the saved state plus sealed software and a new empty lock."""
    template = template_files(world["installed_inventory"], world["pack"])
    inventory, entries, directories = layout(root, template=template)
    expected = {p: e for p, e in world["files"].items() if e["disposition"] in {"state", "immutable"}}
    expected["world/session.lock"] = {"bytes": 0, "sha256": digest_bytes(b""),
                                       "disposition": "transient_session_lock"}
    expected_dirs = {p.as_posix() for name in expected for p in Path(name).parents if str(p) != "."}
    expected_dirs.update(p for p in world["directories"] if p == "world" or p.startswith("world/"))
    require(entries == expected and set(directories) == expected_dirs, "PACK_RESTORE_CHANGED")
    return inventory, entries, directories


def digest_bytes(raw):
    from hashlib import sha256
    return sha256(raw).hexdigest()


def baseline_record(binding):
    return {"schema": "strata/StoppedWorldBaseline/1", "pack_lock": binding.lock,
            "snapshot_sha256": binding.restoration.sha256, "complete_checkpoint": False,
            "baseline_save_qualified": False}


def archive_restoration(binding, inventory, destination):
    """Retain the pinned source within a run for offline evidence reconstruction."""
    world = load_restoration(binding, inventory)
    source, target = _absolute(binding.restoration.snapshot), _absolute(destination)
    require(not target.exists() and not target.is_relative_to(source) and not source.is_relative_to(target),
            "PACK_RESTORE_TARGET")
    inputs = snapshot([], [source])
    with FileLease(inputs) as lease:
        require(load_restoration(binding, inventory) == world, "PACK_RESTORE_SOURCE")
        target.mkdir(parents=True)
        for directory in world["directories"]:
            if directory == "world" or directory.startswith("world/"):
                (target / "state" / directory).mkdir(parents=True, exist_ok=True)
        for entry in inputs["files"]:
            _copy(entry["path"], target / safe(entry["path"]).relative_to(safe(source)),
                  entry["bytes"], entry["sha256"])
        lease.recheck()
        require(verify_snapshot(target, binding.restoration.sha256) == world, "PACK_RESTORE_CHANGED")
    return world


def restore_pack_instance(fresh, source, destination):
    """Copy verified template/state under file leases, then atomically publish.

    No process is launched, source is never modified, and durable accounting is
    only read. A failed staging directory is retained and cannot be reused.
    """
    require(type(fresh) is PackLaunchBinding, "PACK_RESTORE_TEMPLATE")
    source = VanillaWorldSource.model_validate(source)
    template_root, target = _absolute(fresh.instance), _absolute(destination)
    require(not target.exists() and target.parent.is_dir(), "PACK_RESTORE_TARGET")
    binding = RestoredPackLaunchBinding(**(fresh.model_dump() | {"instance": str(target)}), restoration=source)
    for path in (template_root, _absolute(fresh.store), _absolute(source.snapshot)):
        require(not target.is_relative_to(path) and not path.is_relative_to(target), "PACK_RESTORE_OVERLAP")
    require(not template_root.is_relative_to(_absolute(source.snapshot))
            and not _absolute(source.snapshot).is_relative_to(template_root), "PACK_RESTORE_OVERLAP")
    resolved = resolve_pack_launch(fresh, "server")
    require(resolved["target"] == "vanilla", "PACK_RESTORE_UNSUPPORTED")
    raw = safe(Path(fresh.store) / "objects" / resolved["inventory_digest"]).read_bytes()
    from .inference_transport import strict_json
    inventory = strict_json(raw)
    require(digest_bytes(raw) == resolved["inventory_digest"], "PACK_RESTORE_SOURCE")
    world = load_restoration(binding, inventory)
    template = template_files(inventory, world["pack"])
    layout(template_root / "server", template=template, initial=True)
    staging = target.with_name(target.name + ".preparing")
    require(not staging.exists(), "PACK_RESTORE_TARGET")
    require(shutil.disk_usage(target.parent).free >= 5 * 1024**3 + world["state_bytes"]
            + sum(e["bytes"] for e in inventory["files"]), "DISK_RESERVE_LOW")
    with ExitStack() as resources:
        template_lease = resources.enter_context(FileLease(snapshot([], [template_root])))
        source_lease = resources.enter_context(FileLease(snapshot([], [_absolute(source.snapshot)])))
        # Revalidate after opening the held file handles, before creating output.
        resolve_pack_launch(fresh, "server")
        require(load_restoration(binding, inventory) == world, "PACK_RESTORE_SOURCE")
        staging.mkdir()
        for entry in inventory["files"]:
            name, role = entry["path"], entry["role"]
            require(role in {"client", "server"}, "PACK_RESTORE_TEMPLATE")
            if role == "server" and disposition(name, template) == "state":
                continue
            _copy(template_root / role / name, staging / role / name, entry["bytes"], entry["digest"])
        for directory in world["directories"]:
            if directory == "world" or directory.startswith("world/"):
                (staging / "server" / directory).mkdir(parents=True, exist_ok=True)
        for name, entry in world["files"].items():
            if entry["disposition"] == "state":
                _copy(Path(source.snapshot) / "state" / name, staging / "server" / name,
                      entry["bytes"], entry["sha256"])
        write_new(staging / "server/world/session.lock", b"")
        write_new(staging / ".strata-instance.json", canonical(restoration_marker(binding, world)))
        restored_layout(staging / "server", world)
        staged_binding = binding.model_copy(update={"instance": str(staging)})
        resolve_pack_launch(staged_binding, "server")
        template_lease.recheck()
        source_lease.recheck()
        require(not target.exists(), "PACK_RESTORE_TARGET")
        os.rename(staging, target)
    return binding


def _copy(source, target, size, sha):
    source, target = safe(source), safe(target)
    require(source.is_file() and source.stat().st_nlink == 1, "PACK_RESTORE_SOURCE")
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as incoming, target.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing, 1024**2)
        outgoing.flush()
        os.fsync(outgoing.fileno())
    require(target.stat().st_size == size and file_hash(target) == sha, "PACK_RESTORE_CHANGED")
