"""Compare installed npm bytes with lock-bound archives and reviewed generated shims.

Operator-only, offline and non-executing. Never run package lifecycle scripts or
trust a hidden lockfile as proof of file contents. This is provenance/integrity
evidence, not package safety, licensing, authenticated execution or isolation.
"""

import base64
import hashlib
import json
import os
import tarfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .inventory import file_hash
from .storage import digest, reject_links, require, safe_relative


def _file(path):
    reject_links(path.absolute())
    require(path.is_file() and path.stat().st_nlink == 1, "NPM_FILE_UNSAFE")
    return path


def binary_paths(packages):
    """Derive each declared Windows npm shim's target without searching PATH."""
    result = {}
    for location, metadata in packages.items():
        parts = PurePosixPath(location).parts
        require(parts[0] == "node_modules" and parts[-1] != "node_modules", "NPM_LOCK_UNSUPPORTED")
        safe_relative(location)
        index = max(i for i, part in enumerate(parts) if part == "node_modules")
        require(len(parts[index + 1:]) == (2 if parts[index + 1].startswith("@") else 1),
                "NPM_LOCK_UNSUPPORTED")
        binary = metadata.get("bin", {})
        if isinstance(binary, str):
            binary = {parts[-1]: binary}
        require(isinstance(binary, dict), "NPM_LOCK_UNSUPPORTED")
        for name, target in binary.items():
            require(len(safe_relative(name).parts) == 1 and isinstance(target, str), "NPM_LOCK_UNSUPPORTED")
            relative = PurePosixPath(*parts[:index + 1], ".bin", name).as_posix()
            require(relative not in result, "NPM_BIN_COLLISION")
            result[relative] = (PurePosixPath(location) / safe_relative(target)).as_posix()
    return result


def verify_installed_packages(root: Path, cache: Path, generated_shims: Path):
    """`generated_shims` is a private, separately reviewed npm cmd-shim output.

    Its generation tool/source pins and procedure must accompany this report.
    Matching it does not independently authenticate that operator input.
    """
    root, cache, generated_shims = (p.absolute() for p in (root, cache, generated_shims))
    for path in (root, cache, generated_shims):
        reject_links(path)
    require(not generated_shims.is_relative_to(root) and not root.is_relative_to(generated_shims),
            "NPM_GENERATOR_OVERLAP")
    lock_raw = _file(root / "package-lock.json").read_bytes()
    lock = json.loads(lock_raw)
    manifest_raw = _file(root / "package.json").read_bytes()
    manifest = json.loads(manifest_raw)
    require(lock.get("lockfileVersion") == 3 and isinstance(lock.get("packages"), dict), "NPM_LOCK_UNSUPPORTED")
    packages = {k: v for k, v in lock["packages"].items() if k}
    require(0 < len(packages) <= 512 and "" in lock["packages"], "NPM_LOCK_UNSUPPORTED")
    declared = lock["packages"][""]
    require(all(manifest.get(k) == v for k, v in declared.items()), "NPM_ROOT_MISMATCH")
    hidden_path = _file(root / "node_modules/.package-lock.json")
    hidden_raw = hidden_path.read_bytes()
    hidden = json.loads(hidden_raw)
    require(hidden.get("lockfileVersion") == 3 and hidden.get("packages") == packages
            and hidden.get("name") == lock.get("name") and hidden.get("version") == lock.get("version"),
            "NPM_HIDDEN_LOCK_MISMATCH")
    binaries = binary_paths(packages)
    expected, receipts, total, count = {}, [], 0, 0
    for location, metadata in sorted(packages.items()):
        require(isinstance(metadata.get("version"), str) and not metadata.get("link"), "NPM_LOCK_UNSUPPORTED")
        url = urlsplit(metadata.get("resolved", ""))
        require(url.scheme == "https" and url.hostname == "registry.npmjs.org"
                and url.port in (None, 443) and url.username is None and url.password is None
                and not url.query and not url.fragment and url.path.endswith(".tgz"), "NPM_ORIGIN_UNSUPPORTED")
        integrity = metadata.get("integrity", "")
        require(isinstance(integrity, str) and integrity.startswith("sha512-"), "NPM_INTEGRITY_UNSUPPORTED")
        try:
            sha = base64.b64decode(integrity[7:], validate=True)
        except ValueError:
            require(False, "NPM_INTEGRITY_UNSUPPORTED")
        require(len(sha) == 64 and base64.b64encode(sha).decode() == integrity[7:], "NPM_INTEGRITY_UNSUPPORTED")
        address = sha.hex()
        archive_path = _file(cache / address[:2] / address[2:4] / address[4:])
        require(archive_path.stat().st_size <= 128 * 1024**2, "NPM_ARCHIVE_QUOTA")
        with archive_path.open("rb") as stream:
            require(hashlib.file_digest(stream, "sha512").digest() == sha, "NPM_ARCHIVE_CHANGED")
        package, members, prefix = {}, set(), None
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive:
                parts = safe_relative(member.name.rstrip("/")).parts
                require(member.isfile() or member.isdir(), "NPM_ARCHIVE_UNSAFE")
                prefix = prefix or parts[0]
                require(parts[0] == prefix, "NPM_ARCHIVE_UNSAFE")
                if member.isdir():
                    continue
                require(len(parts) > 1, "NPM_ARCHIVE_UNSAFE")
                relative = PurePosixPath(*parts[1:]).as_posix()  # npm/pacote strip: 1.
                require(relative.casefold() not in members, "NPM_ARCHIVE_COLLISION")
                members.add(relative.casefold())
                # npm/pacote's ignore-file normalization; ambiguous pairs reject.
                target = relative[:-10] + ".npmignore" if relative.endswith(".gitignore") else relative
                require(target.casefold() not in {p.casefold() for p in package}, "NPM_ARCHIVE_COLLISION")
                count += 1
                total += member.size
                require(count <= 12000 and member.size <= 512 * 1024**2 and total <= 1024**3,
                        "NPM_ARCHIVE_QUOTA")
                with archive.extractfile(member) as stream:
                    actual_sha = hashlib.file_digest(stream, "sha256").hexdigest()
                path = f"{location}/{target}"
                installed = _file(root / path)
                require(installed.stat().st_size == member.size and file_hash(installed) == actual_sha,
                        "NPM_INSTALLED_CHANGED")
                require(path not in expected, "NPM_ARCHIVE_COLLISION")
                expected[path] = {"bytes": member.size, "sha256": actual_sha}
                package[target] = {"archive_path": member.name, **expected[path]}
        require("package.json" in package, "NPM_PACKAGE_MISSING")
        package_json = json.loads((root / location / "package.json").read_bytes())
        require(package_json.get("version") == metadata["version"], "NPM_PACKAGE_MISMATCH")
        receipts.append({"location": location, "version": metadata["version"], "resolved": metadata["resolved"],
                         "integrity": integrity, "archive_bytes": archive_path.stat().st_size,
                         "license_declaration": package_json.get("license"), "files": package})
    for binary in binaries:
        for suffix in ("", ".cmd", ".ps1"):
            name = binary + suffix
            reviewed = _file(generated_shims / name)
            installed = _file(root / name)
            require(installed.stat().st_size == reviewed.stat().st_size
                    and file_hash(installed) == file_hash(reviewed), "NPM_SHIM_CHANGED")
            expected[name] = {"bytes": reviewed.stat().st_size, "sha256": file_hash(reviewed)}
    expected["node_modules/.package-lock.json"] = {"bytes": len(hidden_raw),
                                                 "sha256": hashlib.sha256(hidden_raw).hexdigest()}
    actual = set()
    directories = set()
    for current, dirs, names in os.walk(root / "node_modules", followlinks=False):
        for name in dirs:
            path = Path(current) / name
            reject_links(path)
            directories.add(path.relative_to(root).as_posix())
        for name in names:
            path = _file(Path(current) / name)
            relative = path.relative_to(root).as_posix()
            require(relative in expected, "NPM_EXTRA_FILE")
            require(path.stat().st_size == expected[relative]["bytes"]
                    and file_hash(path) == expected[relative]["sha256"], "NPM_INSTALLED_CHANGED")
            actual.add(relative)
    require(actual == set(expected), "NPM_MISSING_FILE")
    expected_dirs = {p.as_posix() for name in expected for p in PurePosixPath(name).parents
                     if p.as_posix() not in {".", "node_modules"}}
    require(directories == expected_dirs, "NPM_EXTRA_DIRECTORY")
    require((root / "package-lock.json").read_bytes() == lock_raw
            and (root / "package.json").read_bytes() == manifest_raw, "NPM_SOURCE_CHANGED")
    return {"schema": "strata/NpmInstalledRuntime/1", "lock_sha256": hashlib.sha256(lock_raw).hexdigest(),
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(), "packages": receipts,
            "generated_shims": binaries, "files": expected, "files_digest": digest(expected),
            "scope": "installed_bytes_and_retained_provenance", "campaign_admission": False,
            "license_qualification": False, "writer_custody_qualified": False}
