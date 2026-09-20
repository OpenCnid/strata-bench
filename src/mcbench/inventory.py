"""Operator-only installation inventory. No archive execution or guessed bootstrap."""

import hashlib
import os
import stat
import zipfile
from pathlib import Path

from .storage import require, reject_links, safe_relative

# Templates contain software/configuration only. Runtime credentials and game
# state belong to separately protected stores/checkpoints, never pack exports.
FORBIDDEN_PARTS = {
    ".git", ".codex", ".ssh", ".aws", "auth", "auth-cache", "auth_cache", "accounts",
    "saves", "world", "playerdata", "level.dat", "level.dat_old", "session.lock", "launcher_accounts.json",
    "launcher_msa_credentials.bin", "authentication.json", "auth.json", "credentials.json",
    ".env", "usercache.json", "ops.json", "whitelist.json", "banned-players.json",
}


def template_path(value: str, *, reviewed_world_paths=()):
    path = safe_relative(value)
    forbidden = FORBIDDEN_PARTS - ({"world"} if value in reviewed_world_paths else set())
    require(not forbidden.intersection(p.casefold() for p in path.parts),
            "PRIVATE_INSTALLATION_CONTENT")
    require(not any(p.casefold().endswith((".key", ".pem", ".pfx")) for p in path.parts),
            "PRIVATE_INSTALLATION_CONTENT")
    return path


def file_hash(path: Path) -> str:
    reject_links(path.absolute())
    require(path.is_file(), "AWAITING_ARTIFACT")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scan_tree(root: Path, *, max_files=200000, max_bytes=64 * 1024**3,
              reviewed_world_paths=None) -> list[dict]:
    """Inventory ALL files of an already prepared dedicated, stopped installation.

    Nothing is silently excluded. Clean source trees must be prepared separately;
    executable startup configuration and transitive downloads remain hash-bound.
    Path names are portable and case collisions are rejected even on Linux.
    """
    root = root.absolute()
    reject_links(root)
    require(root.is_dir(), "AWAITING_ARTIFACT")
    reviewed_world_paths = reviewed_world_paths or {}
    entries, seen, total = [], set(), 0
    for current, directories, files in os.walk(root, followlinks=False):
        for name in sorted(directories + files):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            template_path(relative, reviewed_world_paths=reviewed_world_paths)
            require(relative.casefold() not in seen, "PATH_COLLISION")
            seen.add(relative.casefold())
            reject_links(path)
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), "UNSAFE_PATH")
            if relative in reviewed_world_paths:
                require(stat.S_ISDIR(info.st_mode) == (reviewed_world_paths[relative] is None),
                        "VENDOR_CONTENT_MISMATCH")
            if stat.S_ISREG(info.st_mode):
                # Shared writable hardlinks defeat both snapshot independence and
                # safe source auditing. Copies are inexpensive compared with that risk.
                require(info.st_nlink == 1, "UNSAFE_PATH")
                total += info.st_size
                require(len(entries) < max_files and total <= max_bytes, "ARTIFACT_QUOTA")
                sha = file_hash(path)
                if relative in reviewed_world_paths:
                    require(sha == reviewed_world_paths[relative], "VENDOR_CONTENT_MISMATCH")
                entries.append({"path": relative, "digest": sha,
                                "bytes": info.st_size})
    require(bool(entries), "EMPTY_INVENTORY")
    return sorted(entries, key=lambda e: e["path"])


def inspect_archive(path: Path, *, max_members=200000, max_expanded_bytes=64 * 1024**3,
                    reviewed_world_paths=None):
    """Inspect ZIP structure before any official bootstrap; never extract or run it.

    No heuristic compression-ratio rejection: real resource archives compress
    well. Hard caps and portable paths defend the actual expansion footprint.
    """
    reviewed_world_paths = reviewed_world_paths or {}
    reject_links(path.absolute())
    require(zipfile.is_zipfile(path), "ARCHIVE_UNSUPPORTED")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        require(len(infos) <= max_members, "ARTIFACT_QUOTA")
        total, names, kinds = 0, set(), {}
        for info in infos:
            name = info.filename.rstrip("/")
            template_path(name, reviewed_world_paths=reviewed_world_paths)
            folded = name.casefold()
            require(folded not in names, "PATH_COLLISION")
            names.add(folded)
            mode = info.external_attr >> 16
            require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR), "UNSAFE_PATH")
            require(not info.flag_bits & 1, "ARCHIVE_UNSUPPORTED")
            kinds[folded] = info.is_dir()
            total += info.file_size
            require(total <= max_expanded_bytes, "ARTIFACT_QUOTA")
            if name in reviewed_world_paths:
                expected = reviewed_world_paths[name]
                require(info.is_dir() == (expected is None), "VENDOR_CONTENT_MISMATCH")
                if expected is not None:
                    with archive.open(info) as stream:
                        require(hashlib.file_digest(stream, "sha256").hexdigest() == expected,
                                "VENDOR_CONTENT_MISMATCH")
        for name in names:
            for parent in safe_relative(name).parents:
                if str(parent) != ".":
                    require(kinds.get(str(parent), True), "PATH_COLLISION")
        return {"members": len(infos), "expanded_bytes": total,
                "paths": sorted(names)}
