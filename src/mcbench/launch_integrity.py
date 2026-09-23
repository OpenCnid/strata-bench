"""Standard-library-only launch inventory and Windows deny-write file leases.

This protects sealed files, not arbitrary same-user processes or credential
access. Native tool restrictions and protected ingress remain separate gates.
"""

import hashlib
import json
import os
from pathlib import Path
import stat


class IntegrityError(RuntimeError):
    pass


def check(value, code):
    if not value:
        raise IntegrityError(code)


def safe(path):
    path = Path(path)
    check(path.is_absolute(), "BOOTSTRAP_PATH")
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        value = str(path)
        path = Path("\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value)
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        # Inspect each component without first following it via exists(). This
        # also rejects dangling links and halves metadata queries on existing
        # paths. No component result is cached across checks or leases.
        check(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
              "BOOTSTRAP_LINK")
    return path


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def fingerprint(value):
    return hashlib.sha256(encode(value)).hexdigest()


def tree_files(root):
    root = safe(root)
    check(root.is_dir(), "BOOTSTRAP_TREE_MISSING")
    files = []
    def failed(error):
        raise error
    for directory, folders, names in os.walk(root, followlinks=False, onerror=failed):
        for name in folders + names:
            path = Path(directory) / name
            info = path.lstat()
            check(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                  "BOOTSTRAP_LINK")
            if name in names:
                check(stat.S_ISREG(info.st_mode), "BOOTSTRAP_FILE_TYPE")
                files.append(str(path))
                check(len(files) <= 12000, "BOOTSTRAP_QUOTA")
    return sorted(files)


def snapshot(files, trees):
    roots = [str(safe(p)) for p in trees]
    check(len(set(roots)) == len(roots) and len(roots) <= 16, "BOOTSTRAP_TREE")
    all_files = {str(safe(p)) for p in files}
    inventories = []
    for root in roots:
        paths = tree_files(root)
        inventories.append({"path": root, "files": paths})
        all_files.update(paths)
    check(0 < len(all_files) <= 12000, "BOOTSTRAP_QUOTA")
    entries, total = [], 0
    for name in sorted(all_files):
        path = safe(name)
        size = path.stat().st_size
        total += size
        check(size <= 512 * 1024**2 and total <= 1024**3, "BOOTSTRAP_QUOTA")
        with path.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        entries.append({"path": name, "bytes": size, "sha256": sha})
    return {"schema": "strata/LaunchFileInventory/1", "files": entries, "trees": inventories}


def read_manifest(path, expected):
    raw = safe(path).read_bytes()
    check(len(raw) <= 8 * 1024**2 and hashlib.sha256(raw).hexdigest() == expected, "BOOTSTRAP_DIGEST")
    value = json.loads(raw)
    check(value.get("schema") == "strata/NativeBootstrap/1", "BOOTSTRAP_SCHEMA")
    return value


class FileLease:
    """Open and hash the same held handles; Windows denies writes and replacement."""

    def __init__(self, inventory):
        self.inventory, self.handles, self.directories = inventory, [], []
        self.closed = False
        check(os.name == "nt", "BOOTSTRAP_PLATFORM_UNQUALIFIED")
        check(inventory.get("schema") == "strata/LaunchFileInventory/1" and
              0 < len(inventory.get("files", [])) <= 12000, "BOOTSTRAP_INVENTORY")
        self.paths = {entry["path"] for entry in inventory["files"]}
        check(len(self.paths) == len(inventory["files"]), "BOOTSTRAP_DUPLICATE")
        try:
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            create = kernel.CreateFileW
            create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                               wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
            create.restype = wintypes.HANDLE
            close = kernel.CloseHandle
            close.argtypes = [wintypes.HANDLE]
            close.restype = wintypes.BOOL
            self.close_handle = close
            size_of = kernel.GetFileSizeEx
            size_of.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong)]
            size_of.restype = wintypes.BOOL
            read = kernel.ReadFile
            read.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
            read.restype = wintypes.BOOL
            buffer = ctypes.create_string_buffer(65536)
            def native_path(path):
                text = str(path)
                return text if text.startswith("\\\\?\\") else "\\\\?\\" + text
            parents = {p for name in self.paths for p in safe(name).parents}
            check(len(parents) <= 12000, "BOOTSTRAP_QUOTA")
            for path in sorted(parents, key=str):
                handle = create(native_path(path), 0, 3, None, 3, 0x02000000, None)
                check(handle not in (None, ctypes.c_void_p(-1).value), "BOOTSTRAP_DIRECTORY_LOCK_FAILED")
                self.directories.append(handle)
            for entry in inventory["files"]:
                path = safe(entry["path"])
                handle = create(native_path(path), 0x80000000, 1, None, 3, 0x80, None)
                check(handle not in (None, ctypes.c_void_p(-1).value), "BOOTSTRAP_LOCK_FAILED")
                self.handles.append(handle)  # Retained before any hash/size failure.
                # Large authentic inventories exceed the CRT descriptor table.
                # Hash the retained native handle directly; never reopen by name
                # or exchange the deny-write/delete handle for a transient read.
                size = ctypes.c_longlong()
                check(size_of(handle, ctypes.byref(size)), "BOOTSTRAP_SIZE_UNAVAILABLE")
                check(size.value == entry["bytes"], "BOOTSTRAP_FILE_CHANGED")
                sha, count = hashlib.sha256(), 0
                while True:
                    received = wintypes.DWORD()
                    check(read(handle, buffer, len(buffer), ctypes.byref(received), None),
                          "BOOTSTRAP_READ_FAILED")
                    if received.value == 0:
                        break
                    count += received.value
                    check(count <= entry["bytes"], "BOOTSTRAP_FILE_CHANGED")
                    sha.update(buffer.raw[:received.value])
                check(count == entry["bytes"] and sha.hexdigest() == entry["sha256"],
                      "BOOTSTRAP_FILE_CHANGED")
            self.recheck()
        except BaseException:
            self.close()
            raise

    def recheck(self):
        check(not self.closed and len(self.handles) == len(self.inventory["files"]),
              "BOOTSTRAP_LEASE_CLOSED")
        for tree in self.inventory["trees"]:
            check(tree_files(tree["path"]) == tree["files"], "BOOTSTRAP_TREE_CHANGED")
        # Held file and ancestor-directory handles already deny replacement.
        # Only additions need re-enumeration; do not rescan every ancestor per file.

    def close(self):
        self.closed = True
        for handle in self.handles:
            self.close_handle(handle)
        self.handles.clear()
        for handle in self.directories:
            self.close_handle(handle)
        self.directories.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
