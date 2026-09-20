"""Private operator persistence. Service authorization complements OS isolation.

Never mount this database or CAS inside an agent runtime. Principal instances
are constructed by the trusted transport after authenticating a protected grant.
"""

import hashlib
import json
import os
import re
import sqlite3
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import rfc8785


class Fault(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise Fault(code)


def canonical(value) -> bytes:
    return rfc8785.dumps(value)


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def safe_relative(path: str) -> PurePosixPath:
    require(isinstance(path, str) and bool(path), "UNSAFE_PATH")
    require(not any(c in path for c in ("\\", ":", "\x00")), "UNSAFE_PATH")
    parts = path.split("/")
    require(all(p not in {"", ".", ".."} and not p.endswith((" ", ".")) for p in parts),
            "UNSAFE_PATH")
    for part in parts:
        require(not re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", part, re.I),
                "UNSAFE_PATH")
        require(not any(ord(c) < 32 or c in '<>"|?*' for c in part), "UNSAFE_PATH")
    return PurePosixPath(path)


def reject_links(path: Path):
    """Includes Windows junctions/reparse points, not just Python symlinks."""
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and
                    not getattr(info, "st_file_attributes", 0) & 0x400, "UNSAFE_PATH")


class Database:
    def __init__(self, path: Path):
        path = path.absolute()
        reject_links(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path.resolve()
        self.connection = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.connection.close()
            raise Fault("SCHEMA_UNSUPPORTED")
        with self.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS outbox (cursor INTEGER PRIMARY KEY, "
                       "kind TEXT NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS objects (namespace TEXT, ref TEXT, "
                       "visibility TEXT NOT NULL, media_type TEXT NOT NULL, bytes INTEGER NOT NULL, "
                       "PRIMARY KEY(namespace,ref))")
            db.execute("PRAGMA user_version=1")

    @contextmanager
    def transaction(self):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield self.connection
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    @staticmethod
    def event(db, kind, body):
        return db.execute("INSERT INTO outbox(kind,body) VALUES (?,?)",
                          (kind, canonical(body).decode())).lastrowid

    def export_journal(self, target: Path):
        """Atomically rebuild JSONL from committed outbox; ignores a corrupt old tail."""
        reject_links(target.absolute())
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".journal-")
        try:
            with os.fdopen(fd, "wb") as stream:
                for row in self.connection.execute("SELECT * FROM outbox ORDER BY cursor"):
                    stream.write(canonical({"cursor": row["cursor"], "kind": row["kind"],
                                            "body": json.loads(row["body"])}) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def close(self):
        self.connection.close()


@dataclass(frozen=True)
class Principal:
    namespace: str
    role: str  # operator, evaluator, executor, helper; supplied by trusted authentication


class CAS:
    def __init__(self, database: Database, root: Path):
        self.database = database
        self.root = root.absolute()
        reject_links(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref):
        require(bool(re.fullmatch(r"cas:sha256:[0-9a-f]{64}", ref)), "INVALID_REFERENCE")
        path = self.root / ref[11:]
        reject_links(path)
        return path

    @staticmethod
    def authorize(principal, namespace, visibility, write=False):
        require(principal.role in {"operator", "evaluator", "executor", "helper"}, "FORBIDDEN")
        if principal.role == "operator":
            return
        require(principal.namespace == namespace, "FORBIDDEN")
        require((principal.role == "evaluator" and visibility == "evaluator") or
                (principal.role in {"executor", "helper"} and visibility == "agent"), "FORBIDDEN")
        require(not write or principal.role != "helper", "FORBIDDEN")

    def put(self, principal, namespace, visibility, data: bytes, media_type="application/json",
            quota_bytes=20 * 1024 * 1024, max_object_bytes=256 * 1024):
        require(visibility in {"agent", "operator", "evaluator"}, "FORBIDDEN")
        self.authorize(principal, namespace, visibility, write=True)
        require(len(data) <= max_object_bytes, "ARTIFACT_QUOTA")
        ref = "cas:sha256:" + hashlib.sha256(data).hexdigest()
        path = self._path(ref)
        with self.database.transaction() as db:
            old = db.execute("SELECT * FROM objects WHERE namespace=? AND ref=?",
                             (namespace, ref)).fetchone()
            if old:
                require(old["visibility"] == visibility and old["media_type"] == media_type,
                        "REFERENCE_POLICY_CONFLICT")
            else:
                size = db.execute("SELECT COALESCE(SUM(bytes),0) FROM objects WHERE namespace=?",
                                  (namespace,)).fetchone()[0]
                require(size + len(data) <= quota_bytes, "ARTIFACT_QUOTA")
            # Reserve under the DB writer lock BEFORE writing bytes. Rejected quota
            # requests must not accumulate unreferenced blobs and exhaust the disk.
            # Flush before inserting the reference. Crash orphans remain operator-only.
            if not path.exists():
                fd, temporary = tempfile.mkstemp(dir=self.root, prefix=".staging-")
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, path)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            require(hashlib.sha256(path.read_bytes()).hexdigest() == ref[11:], "CORRUPT_EVIDENCE")
            if not old:
                db.execute("INSERT INTO objects VALUES (?,?,?,?,?)",
                           (namespace, ref, visibility, media_type, len(data)))
                self.database.event(db, "artifact.created", {"namespace": namespace, "ref": ref,
                                                             "visibility": visibility})
        return ref

    def read(self, principal, namespace, ref, *, max_bytes=None):
        row = self.database.connection.execute(
            "SELECT * FROM objects WHERE namespace=? AND ref=?", (namespace, ref)).fetchone()
        require(row is not None, "FORBIDDEN")  # no existence oracle for guessed hashes
        self.authorize(principal, namespace, row["visibility"])
        if max_bytes is not None:
            require(type(max_bytes) is int and max_bytes >= 0, "INVALID_QUOTA")
            require(row["bytes"] <= max_bytes, "ARTIFACT_QUOTA")
        path = self._path(ref)
        require(path.is_file(), "MISSING_EVIDENCE")
        with path.open("rb") as stream:
            data = stream.read(row["bytes"] + 1)
        require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == ref[11:],
                "CORRUPT_EVIDENCE")
        return data

    def verify(self, principal, namespace, ref):
        """Authorize and hash a blob with bounded memory, including large saves."""
        row = self.database.connection.execute(
            "SELECT * FROM objects WHERE namespace=? AND ref=?", (namespace, ref)).fetchone()
        require(row is not None, "FORBIDDEN")
        self.authorize(principal, namespace, row["visibility"])
        path = self._path(ref)
        require(path.is_file(), "MISSING_EVIDENCE")
        require(path.stat().st_size == row["bytes"], "CORRUPT_EVIDENCE")
        with path.open("rb") as stream:
            require(hashlib.file_digest(stream, "sha256").hexdigest() == ref[11:], "CORRUPT_EVIDENCE")
        return row["bytes"]

    def json(self, principal, namespace, ref):
        row = self.database.connection.execute(
            "SELECT * FROM objects WHERE namespace=? AND ref=?", (namespace, ref)).fetchone()
        require(row is not None, "FORBIDDEN")
        self.authorize(principal, namespace, row["visibility"])
        require(row["bytes"] <= 64 * 1024**2, "ARTIFACT_QUOTA")
        return json.loads(self.read(principal, namespace, ref))

    def put_file(self, principal, namespace, visibility, source: Path, expected_digest: str,
                 *, quota_bytes: int, max_object_bytes: int):
        """Stream a private installation asset without loading a jar/archive into memory.

        Quota and reference publication share the writer transaction. The expected
        digest binds the import to the operator's inspected inventory, including a
        source changed between inventory and copying. Game assets never use agent CAS.
        """
        require(principal.role == "operator" and visibility == "operator", "FORBIDDEN")
        source = source.absolute()
        reject_links(source)
        require(source.is_file(), "AWAITING_ARTIFACT")
        ref = "cas:sha256:" + expected_digest
        destination = self._path(ref)
        size = source.stat().st_size
        require(0 <= size <= max_object_bytes, "ARTIFACT_QUOTA")
        with self.database.transaction() as db:
            old = db.execute("SELECT * FROM objects WHERE namespace=? AND ref=?",
                             (namespace, ref)).fetchone()
            if old:
                require(old["visibility"] == visibility and
                        old["media_type"] == "application/octet-stream", "REFERENCE_POLICY_CONFLICT")
                require(old["bytes"] == size, "HASH_MISMATCH")
            else:
                used = db.execute("SELECT COALESCE(SUM(bytes),0) FROM objects WHERE namespace=?",
                                  (namespace,)).fetchone()[0]
                require(used + size <= quota_bytes, "ARTIFACT_QUOTA")
            fd, temporary = tempfile.mkstemp(dir=self.root, prefix=".asset-")
            try:
                hasher, copied = hashlib.sha256(), 0
                with os.fdopen(fd, "wb") as output, source.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        copied += len(chunk)
                        require(copied <= size, "HASH_MISMATCH")
                        hasher.update(chunk)
                        output.write(chunk)
                    require(copied == size and hasher.hexdigest() == expected_digest,
                            "HASH_MISMATCH")
                    output.flush()
                    os.fsync(output.fileno())
                if destination.exists():
                    with destination.open("rb") as stream:
                        require(hashlib.file_digest(stream, "sha256").hexdigest() == expected_digest,
                                "CORRUPT_EVIDENCE")
                else:
                    os.replace(temporary, destination)
                if not old:
                    db.execute("INSERT INTO objects VALUES (?,?,?,?,?)",
                               (namespace, ref, visibility, "application/octet-stream", size))
                    self.database.event(db, "artifact.created", {
                        "namespace": namespace, "ref": ref, "visibility": visibility})
            finally:
                Path(temporary).unlink(missing_ok=True)
        return ref

    def copy_to(self, principal, namespace, ref, target: Path):
        """Copy a verified blob into a new private staging file; never a hardlink."""
        row = self.database.connection.execute(
            "SELECT * FROM objects WHERE namespace=? AND ref=?", (namespace, ref)).fetchone()
        require(row is not None, "FORBIDDEN")
        self.authorize(principal, namespace, row["visibility"])
        source = self._path(ref)
        require(source.is_file(), "MISSING_EVIDENCE")
        reject_links(target.absolute())
        require(not target.exists(), "DESTINATION_EXISTS")
        created = False
        try:
            with target.open("xb") as output, source.open("rb") as stream:
                created = True
                hasher, size = hashlib.sha256(), 0
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    require(size <= row["bytes"], "CORRUPT_EVIDENCE")
                    hasher.update(chunk)
                    output.write(chunk)
                require(size == row["bytes"] and hasher.hexdigest() == ref[11:], "CORRUPT_EVIDENCE")
                output.flush()
                os.fsync(output.fileno())
        except BaseException:
            if created:
                target.unlink(missing_ok=True)
            raise
