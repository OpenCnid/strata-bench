"""Copy only hash-pinned, stopped synthetic activation inputs, never live WALs."""

import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path

from mcbench.storage import extended_path, reject_links, require, safe_relative

MAX_BYTES = 512 * 1024**2


def copy_activation_source(source, output):
    require(isinstance(source, dict) and set(source) == {"directory", "seal_sha256", "skill_set_ref"},
            "ACTIVATION_FIXTURE_SOURCE")
    origin, output = Path(source["directory"]), Path(output)
    require(origin.is_absolute() and output.is_absolute(), "ACTIVATION_FIXTURE_SOURCE")
    origin, output = extended_path(origin), extended_path(output)
    reject_links(origin)
    reject_links(output)
    require(origin.is_dir() and output.is_dir() and not output.is_relative_to(origin)
            and not origin.is_relative_to(output), "ACTIVATION_SOURCE_OVERLAP")
    seal = origin / "seal.json"
    reject_links(seal)
    require(seal.is_file() and seal.stat().st_size <= 8 * 1024**2, "ACTIVATION_SOURCE_SIZE")
    raw = seal.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source["seal_sha256"], "ACTIVATION_SOURCE_CHANGED")
    manifest = json.loads(raw)
    require(isinstance(manifest, dict) and isinstance(manifest.get("files"), list)
            and 0 < len(manifest["files"]) <= 16384, "ACTIVATION_SOURCE_MANIFEST")
    selected, names = {}, set()
    total = 0
    for entry in manifest["files"]:
        require(isinstance(entry, dict) and isinstance(entry.get("path"), str)
                and isinstance(entry.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]), "ACTIVATION_SOURCE_MANIFEST")
        name = entry["path"]
        safe_relative(name)
        require(name.casefold() not in names, "ACTIVATION_SOURCE_MANIFEST")
        names.add(name.casefold())
        if name != "synthetic.sqlite" and not name.startswith("objects/"):
            continue
        require(name == "synthetic.sqlite" or re.fullmatch(r"objects/[0-9a-f]{64}", name),
                "ACTIVATION_SOURCE_MANIFEST")
        path = origin / name
        reject_links(path)
        require(path.is_file() and path.stat().st_nlink == 1, "ACTIVATION_SOURCE_CHANGED")
        size = path.stat().st_size
        require(size <= 128 * 1024**2 and ("bytes" not in entry or
                type(entry["bytes"]) is int and entry["bytes"] == size), "ACTIVATION_SOURCE_SIZE")
        total += size
        require(total <= MAX_BYTES, "ACTIVATION_SOURCE_SIZE")
        selected[name] = entry["sha256"]
    require("synthetic.sqlite" in selected and len(selected) > 1, "ACTIVATION_FIXTURE_SOURCE")

    def frozen():
        for suffix in ("-wal", "-journal"):
            path = origin / ("synthetic.sqlite" + suffix)
            reject_links(path)
            require(not path.exists() or path.is_file() and path.stat().st_size == 0,
                    "ACTIVATION_SOURCE_NOT_FROZEN")

    def verify(root):
        actual = set()
        reject_links(root / "objects")
        for path in (root / "objects").rglob("*"):
            reject_links(path)
            require(path.is_file() and path.stat().st_nlink == 1, "ACTIVATION_SOURCE_CHANGED")
            actual.add(path.relative_to(root).as_posix())
        require(actual == set(selected) - {"synthetic.sqlite"}, "ACTIVATION_SOURCE_INVENTORY")
        for name, pin in selected.items():
            path = root / name
            reject_links(path)
            with path.open("rb") as stream:
                require(hashlib.file_digest(stream, "sha256").hexdigest() == pin,
                        "ACTIVATION_SOURCE_CHANGED")

    frozen()
    verify(origin)
    dbpath = Path(str(origin / "synthetic.sqlite").removeprefix("\\\\?\\"))
    db = sqlite3.connect(dbpath.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        require(db.execute("SELECT simulation FROM native_profile").fetchall() == [(1,)], "SIMULATION_STORE")
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='native_jobs'").fetchone():
            require(not db.execute("SELECT 1 FROM native_jobs WHERE state IN "
                "('PREPARED','STARTING','RUNNING','STOPPING')").fetchone(), "ACTIVATION_SOURCE_NOT_STOPPED")
    finally:
        db.close()
    require(not (output / "synthetic.sqlite").exists() and not (output / "objects").exists(), "TARGET_EXISTS")
    (output / "objects").mkdir()
    for name in selected:
        shutil.copyfile(origin / name, output / name)
    verify(output)
    frozen()
    verify(origin)
    require(seal.read_bytes() == raw, "ACTIVATION_SOURCE_CHANGED")
    # On any failure retain the occupied partial output; never implicitly retry.
    return {"files": len(selected), "bytes": total, "seal_sha256": source["seal_sha256"],
            "policy": "stopped-sealed-activation-copy/1", "dispatch_authorized": False}
