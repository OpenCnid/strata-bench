"""Bounded, read-only access to an externally pinned private evidence bundle.

Archived absolute paths are data, never read authority. SQLite is opened only
after the stopped-file/WAL checks, without creating or updating shared memory.
"""

import hashlib
import os
import re
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Strict, UInt
from mcbench.inference_transport import strict_json
from mcbench.storage import CAS, extended_path, reject_links, require, safe_relative

from .run_costs import frozen_database


class EvidenceFile(Strict):
    path: str
    sha256: Digest
    bytes: UInt


class EvidenceManifest(Strict):
    schema_: Literal["strata/PrivateEvidenceManifest/1"] = Field(alias="schema")
    files: list[EvidenceFile] = Field(min_length=1, max_length=16384)
    total_bytes: UInt


class EvidenceBundle:
    def __init__(self, root, seal_sha256, *, inventory_extension=None):
        path = Path(root)
        require(path.is_absolute(), "EVIDENCE_PATH")
        self.root = extended_path(path)
        reject_links(self.root)
        require(self.root.is_dir(), "EVIDENCE_PATH")
        self.seal_sha256 = seal_sha256
        seal = self.root / "seal.json"
        reject_links(seal)
        require(seal.is_file() and seal.stat().st_size <= 8 * 1024**2, "EVIDENCE_SEAL_SIZE")
        raw = seal.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == seal_sha256, "EVIDENCE_SEAL_CHANGED")
        self.manifest = EvidenceManifest.model_validate(strict_json(raw))
        entries = self.manifest.files
        require(self.manifest.total_bytes == sum(e.bytes for e in entries)
                and self.manifest.total_bytes <= 512 * 1024**2
                and all(e.bytes <= 128 * 1024**2 for e in entries), "EVIDENCE_QUOTA")
        self.files = {e.path: e for e in entries}
        require(len({e.path.casefold() for e in entries}) == len(entries)
                and "seal.json" not in self.files, "EVIDENCE_INVENTORY")
        for entry in entries:
            safe_relative(entry.path)
        self.primary_files = dict(self.files)
        # A format-specific reader may discover additional hashes ONLY through
        # read(), which requires an already sealed input. Never accept an
        # unanchored inventory supplied alongside the archive.
        if inventory_extension is not None:
            additions = inventory_extension(self)
            require(len(additions) <= 16384, "EVIDENCE_QUOTA")
            for value in additions:
                entry = EvidenceFile.model_validate(value)
                safe_relative(entry.path)
                prior = self.files.get(entry.path)
                require(prior is None or prior == entry, "EVIDENCE_INVENTORY_CONFLICT")
                self.files[entry.path] = entry
            require(len(self.files) <= 16384
                    and len({n.casefold() for n in self.files}) == len(self.files)
                    and "seal.json" not in self.files
                    and sum(e.bytes for e in self.files.values()) <= 512 * 1024**2
                    and all(e.bytes <= 128 * 1024**2 for e in self.files.values()), "EVIDENCE_QUOTA")
        self.verify()

    def path(self, name):
        relative = safe_relative(name)
        require(name in self.files, "EVIDENCE_UNSEALED_INPUT")
        path = self.root.joinpath(*relative.parts)
        reject_links(path)
        require(path.is_file() and path.stat().st_size == self.files[name].bytes,
                "EVIDENCE_FILE_CHANGED")
        return path

    def read(self, name, maximum=8 * 1024**2):
        entry = self.files.get(name)
        require(entry is not None and entry.bytes <= maximum, "EVIDENCE_INPUT_SIZE")
        with self.path(name).open("rb") as stream:
            raw = stream.read(entry.bytes + 1)
        require(len(raw) == entry.bytes and hashlib.sha256(raw).hexdigest() == entry.sha256,
                "EVIDENCE_FILE_CHANGED")
        return raw

    def json(self, name):
        return strict_json(self.read(name))

    def verify(self):
        seen = set()
        count = 0

        def failed(error):
            raise error

        for directory, folders, names in os.walk(self.root, followlinks=False, onerror=failed):
            for name in folders + names:
                count += 1
                require(count <= 32768, "EVIDENCE_QUOTA")
                path = Path(directory) / name
                info = path.lstat()
                require(not stat.S_ISLNK(info.st_mode)
                        and not getattr(info, "st_file_attributes", 0) & 0x400, "UNSAFE_PATH")
                if name in names:
                    require(stat.S_ISREG(info.st_mode), "EVIDENCE_FILE_TYPE")
                    relative = path.relative_to(self.root).as_posix()
                    seen.add(relative)
                    require(len(seen) <= 16385, "EVIDENCE_QUOTA")
                    expected = self.seal_sha256 if relative == "seal.json" else (
                        self.files[relative].sha256 if relative in self.files else None)
                    require(expected is not None, "EVIDENCE_INVENTORY")
                    if relative != "seal.json":
                        require(info.st_size == self.files[relative].bytes, "EVIDENCE_FILE_CHANGED")
                    else:
                        require(info.st_size <= 8 * 1024**2, "EVIDENCE_SEAL_SIZE")
                    with path.open("rb") as stream:
                        require(hashlib.file_digest(stream, "sha256").hexdigest() == expected,
                                "EVIDENCE_FILE_CHANGED")
        require(seen == set(self.files) | {"seal.json"}, "EVIDENCE_INVENTORY")

    @contextmanager
    def database(self, name):
        path = self.path(name)
        frozen_database(path)
        # immutable=1 must never be used to ignore a live WAL. The external seal,
        # frozen-sidecar checks and final bundle recheck are required together.
        # SQLite URI parsing treats the Win32 extended-path prefix as a host.
        uri_path = Path(str(path).removeprefix("\\\\?\\")) if os.name == "nt" else path
        db = sqlite3.connect(uri_path.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            steps = 0

            def bounded_query():
                nonlocal steps
                steps += 1
                return int(steps > 100000)  # At most 100 million VM instructions.

            db.set_progress_handler(bounded_query, 1000)
            db.execute("BEGIN")
            require([tuple(r) for r in db.execute("PRAGMA integrity_check")] == [("ok",)],
                    "EVIDENCE_DATABASE_INVALID")
            tables = db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
            require(len(tables) <= 128, "EVIDENCE_DATABASE_QUOTA")
            for table in tables:
                require(re.fullmatch(r"[a-z_]+", table["name"])
                        and not table["sql"].upper().startswith("CREATE VIRTUAL"), "EVIDENCE_DATABASE_INVALID")
                require(db.execute('SELECT count(*) FROM "' + table["name"] + '"').fetchone()[0]
                        <= 100000, "EVIDENCE_DATABASE_QUOTA")
            yield db
        finally:
            db.close()
        frozen_database(path)


class EvidenceCAS(CAS):
    """Reuse CAS authorization/hash checks without invoking its creating constructor."""

    def __init__(self, db, bundle, prefix):
        self.database = SimpleNamespace(connection=db)
        self.bundle, self.prefix = bundle, prefix

    def _path(self, ref):
        require(isinstance(ref, str) and re.fullmatch(r"cas:sha256:[0-9a-f]{64}", ref),
                "INVALID_REFERENCE")
        return self.bundle.path(self.prefix + "/" + ref[11:])

    def put(self, *args, **kwargs):
        require(False, "EVIDENCE_READ_ONLY")

    put_file = put
    copy_to = put
