"""Bounded private stopped-instance capture for the inspected vanilla 1.19.2 layout.

This records process termination and leased file bytes, not a complete campaign
checkpoint or proof of all game save semantics/other writers. No gameplay API.
"""

import hashlib
import os
import re
import shutil
from pathlib import Path

from .launch_integrity import FileLease, safe, snapshot
from .inference_transport import strict_json
from .storage import canonical, digest, reject_links, require, safe_relative

POLICY = "vanilla1192-stopped-instance/1"
PINNED_JARS = {
    "server.jar": "b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96",
    "versions/1.19.2/server-1.19.2.jar": "d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6",
}
MUTABLE = {"server.properties", "ops.json", "whitelist.json", "banned-ips.json",
           "banned-players.json", "usercache.json"}
WORLD_ROOTS = {"advancements", "data", "datapacks", "DIM-1", "DIM1", "entities",
               "playerdata", "poi", "region", "stats"}
SECRET_NAMES = {".git", ".codex", ".ssh", ".aws", "auth.json", "credentials.json", "keys.json",
                "launcher_accounts.json", "launcher_msa_credentials.bin", "auth-cache", "auth_cache"}


def disposition(path):
    parts = safe_relative(path).parts
    require(not {p.casefold() for p in parts} & SECRET_NAMES, "SECRET_IN_SNAPSHOT")
    if path in MUTABLE:
        return "state"
    if path in {"server.jar", "eula.txt"} or len(parts) > 1 and parts[0] in {"libraries", "versions"}:
        return "immutable"
    if path == "world/session.lock":
        return "transient_session_lock"
    if parts[0] == "world" and (len(parts) == 2 and parts[1] in {"level.dat", "level.dat_old"}
                              or len(parts) > 2 and parts[1] in WORLD_ROOTS):
        return "state"
    if parts[0] == "logs" and len(parts) == 2 and parts[1].endswith((".log", ".log.gz")):
        return "diagnostic_log"
    require(False, "VANILLA_PERSISTENCE_LAYOUT_UNSUPPORTED")


def layout(root):
    root = safe(root)
    inventory = snapshot([], [root])
    entries = {}
    for entry in inventory["files"]:
        path = safe(entry["path"])
        require(path.stat().st_nlink == 1, "UNSAFE_PATH")
        relative = path.relative_to(root).as_posix()
        entries[relative] = {"bytes": entry["bytes"], "sha256": entry["sha256"],
                             "disposition": disposition(relative)}
    require(MUTABLE | {"world/level.dat", "world/session.lock", *PINNED_JARS} <= entries.keys(),
            "VANILLA_PERSISTENCE_INCOMPLETE")
    require(all(entries[path]["sha256"] == pin for path, pin in PINNED_JARS.items()), "VANILLA_PIN_MISMATCH")
    # Empty directories matter too: a new mod/external-state root is not silently
    # omitted just because its first file has not yet been written.
    directories = []
    for path in root.rglob("*"):
        safe(path)
        if path.is_dir():
            relative = path.relative_to(root).as_posix()
            parts = safe_relative(relative).parts
            require(parts[0] in {"libraries", "versions", "logs", "world"}
                    and (parts[0] != "world" or len(parts) == 1 or parts[1] in WORLD_ROOTS),
                    "VANILLA_PERSISTENCE_LAYOUT_UNSUPPORTED")
            require(not {p.casefold() for p in parts} & SECRET_NAMES, "SECRET_IN_SNAPSHOT")
            directories.append(relative)
            require(len(directories) <= 12000, "VANILLA_PERSISTENCE_QUOTA")
    return inventory, entries, sorted(directories)


def write_new(path, data):
    reject_links(path)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def verify_snapshot(destination, expected_manifest_sha256):
    """Verify an externally pinned receipt and every archived byte; no self-sealing."""
    destination = safe(destination)
    path = destination / "manifest.json"
    safe(path)
    require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size <= 8 * 1024**2,
            "VANILLA_CAPTURE_MANIFEST")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_manifest_sha256, "VANILLA_CAPTURE_CHANGED")
    body = strict_json(raw)
    require(set(body) == {"schema", "policy", "minecraft", "server_plan_digest", "source_root", "files",
                         "directories", "state_bytes", "owned_processes", "clean_save_proven", "complete_checkpoint",
                         "dispatch_authorized", "writer_custody_qualified", "G0"}
            and body["schema"] == "strata/StoppedVanillaSnapshot/1" and body["policy"] == POLICY
            and body["minecraft"] == "1.19.2" and body["G0"] == "fail"
            and all(body[k] is False for k in ("clean_save_proven", "complete_checkpoint", "dispatch_authorized",
                                             "writer_custody_qualified")), "VANILLA_CAPTURE_MANIFEST")
    require(isinstance(body["files"], dict) and 0 < len(body["files"]) <= 12000, "VANILLA_CAPTURE_MANIFEST")
    require(MUTABLE | {"world/level.dat", "world/session.lock", *PINNED_JARS} <= body["files"].keys()
            and isinstance(body["server_plan_digest"], str)
            and re.fullmatch("[0-9a-f]{64}", body["server_plan_digest"])
            and isinstance(body["directories"], list) and len(body["directories"]) <= 12000
            and body["directories"] == sorted(set(body["directories"])), "VANILLA_CAPTURE_MANIFEST")
    states = {}
    for relative, entry in body["files"].items():
        require(set(entry) == {"bytes", "sha256", "disposition"}
                and entry["disposition"] == disposition(relative) and type(entry["bytes"]) is int
                and 0 <= entry["bytes"] <= 512 * 1024**2
                and re.fullmatch("[0-9a-f]{64}", entry["sha256"]), "VANILLA_CAPTURE_MANIFEST")
        if entry["disposition"] == "state":
            states[relative] = entry
    require(sum(e["bytes"] for e in states.values()) == body["state_bytes"] <= 1024**3,
            "VANILLA_CAPTURE_MANIFEST")
    require(all(body["files"][p]["sha256"] == pin for p, pin in PINNED_JARS.items()), "VANILLA_PIN_MISMATCH")
    owned = body["owned_processes"]
    require(set(owned) == {"job", "held", "complete_owned_process_history", "all_external_writers_excluded"}
            and owned["complete_owned_process_history"] is True and owned["all_external_writers_excluded"] is False
            and set(owned["job"]) == {"total_processes", "active_processes", "terminated_processes"}
            and set(owned["held"]) == {"held_processes", "signaled_processes"}
            and all(type(v) is int for v in [*owned["job"].values(), *owned["held"].values()])
            and owned["job"]["active_processes"] == owned["job"]["terminated_processes"] == 0
            and 0 < owned["job"]["total_processes"] == owned["held"]["held_processes"]
            == owned["held"]["signaled_processes"] <= 256, "VANILLA_STOP_UNPROVEN")
    for relative in body["directories"]:
        parts = safe_relative(relative).parts
        require(parts[0] in {"libraries", "versions", "logs", "world"}
                and (parts[0] != "world" or len(parts) == 1 or parts[1] in WORLD_ROOTS),
                "VANILLA_PERSISTENCE_LAYOUT_UNSUPPORTED")
    expected_dirs = {"state"} | {"state/" + p for p in body["directories"] if p == "world" or p.startswith("world/")}
    for relative in states:
        expected_dirs.update("state/" + str(p) for p in safe_relative(relative).parents if str(p) != ".")
    found, directories = set(), set()
    for path in destination.rglob("*"):
        safe(path)
        relative = path.relative_to(destination).as_posix()
        if path.is_dir():
            require(relative in expected_dirs, "VANILLA_CAPTURE_CHANGED")
            directories.add(relative)
        elif relative != "manifest.json":
            require(relative.startswith("state/") and relative[6:] in states, "VANILLA_CAPTURE_CHANGED")
            entry = states[relative[6:]]
            require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size == entry["bytes"],
                    "VANILLA_CAPTURE_CHANGED")
            with path.open("rb") as stream:
                require(hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"], "VANILLA_CAPTURE_CHANGED")
            found.add(relative[6:])
    require(found == set(states) and directories == expected_dirs, "VANILLA_CAPTURE_CHANGED")
    return body


class VanillaPersistence:
    def __init__(self, root):
        self.root, self.lease = safe(root), None
        inventory, entries, _ = layout(self.root)
        self.immutable = {p: e for p, e in entries.items() if e["disposition"] == "immutable"}
        selected = [e for e in inventory["files"] if Path(e["path"]).relative_to(self.root).as_posix() in self.immutable]
        trees = snapshot([], [self.root / "libraries", self.root / "versions"])["trees"]
        self.lease = FileLease({"schema": "strata/LaunchFileInventory/1", "files": selected, "trees": trees})

    @staticmethod
    def terminal_processes(process):
        require(process.poll() == 0 and process.job is not None, "VANILLA_STOP_UNPROVEN")
        accounting, held = process.job.accounting(), process.job.member_status()
        require(accounting["active_processes"] == accounting["terminated_processes"] == 0
                and 0 < accounting["total_processes"] == held["held_processes"] == held["signaled_processes"],
                "VANILLA_STOP_UNPROVEN")
        return {"job": accounting, "held": held, "complete_owned_process_history": True,
                "all_external_writers_excluded": False}

    def capture(self, destination, process, *, plan_digest):
        destination = safe(destination)
        require(not destination.is_relative_to(self.root) and not destination.exists(), "VANILLA_CAPTURE_TARGET")
        require(isinstance(plan_digest, str) and re.fullmatch("[0-9a-f]{64}", plan_digest), "VANILLA_CAPTURE_SCOPE")
        stopped = self.terminal_processes(process)
        self.lease.recheck()
        inventory, entries, directories = layout(self.root)
        require({p: e for p, e in entries.items() if e["disposition"] == "immutable"} == self.immutable,
                "VANILLA_PIN_MISMATCH")
        states = {p: e for p, e in entries.items() if e["disposition"] == "state"}
        state_bytes = sum(e["bytes"] for e in states.values())
        require(shutil.disk_usage(destination.parent).free >= state_bytes + 5 * 1024**3, "DISK_RESERVE_LOW")
        # Hold all actual post-stop input bytes while copying. This is never a
        # live-save copy; the retained job must already prove every member exited.
        with FileLease(inventory) as lease:
            destination.mkdir()
            for relative in directories:
                if relative == "world" or relative.startswith("world/"):
                    (destination / "state" / relative).mkdir(parents=True, exist_ok=True)
            for relative, entry in states.items():
                target = destination / "state" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with (self.root / relative).open("rb") as source, target.open("xb") as output:
                    sha, size = hashlib.sha256(), 0
                    while block := source.read(65536):
                        size += len(block)
                        require(size <= entry["bytes"], "VANILLA_CAPTURE_CHANGED")
                        sha.update(block)
                        output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
                require(size == entry["bytes"] and sha.hexdigest() == entry["sha256"], "VANILLA_CAPTURE_CHANGED")
            lease.recheck()
            require(layout(self.root)[1:] == (entries, directories), "VANILLA_CAPTURE_CHANGED")
            require(self.terminal_processes(process) == stopped, "VANILLA_STOP_UNPROVEN")
            manifest = {"schema": "strata/StoppedVanillaSnapshot/1", "policy": POLICY,
                "minecraft": "1.19.2", "server_plan_digest": plan_digest,
                "source_root": str(self.root), "files": entries, "directories": directories,
                "state_bytes": state_bytes, "owned_processes": stopped,
                "clean_save_proven": False, "complete_checkpoint": False, "dispatch_authorized": False,
                "writer_custody_qualified": False, "G0": "fail"}
            raw = canonical(manifest)
            write_new(destination / "manifest.json", raw)
            verify_snapshot(destination, hashlib.sha256(raw).hexdigest())
        return {"path": str(destination), "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                "inventory_digest": digest(entries), "state_files": len(states), "state_bytes": state_bytes,
                "complete_owned_process_history": True, "complete_checkpoint": False, "clean_save_proven": False}

    def close(self):
        if self.lease is not None:
            self.lease.close()
