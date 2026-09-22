"""Operator-only derivation of vanilla server software from the acquired bundle.

This prepares independent software bytes, not a complete role or a PackLock.
Configuration, runtime state, licensing review and launch qualification remain
explicit. No Java/bootstrap is executed and no installed file is replaced.
"""

import hashlib
import io
import os
from pathlib import Path
import re
import stat
import zipfile

from .inventory import file_hash, scan_tree
from .storage import Fault, reject_links, require, safe_relative

POLICY = "mojang-vanilla1192-server-bundle/1"
MAX_EXPANDED = 256 * 1024**2
CONFIG = {"server.properties", "eula.txt"}
STATE = {"banned-ips.json", "banned-players.json", "ops.json", "usercache.json", "whitelist.json"}


def _archive(raw, *, max_members, opaque_metadata=False):
    archive = zipfile.ZipFile(io.BytesIO(raw))
    try:
        infos = archive.infolist()
        require(len(infos) <= max_members, "ARTIFACT_QUOTA")
        seen, total = {}, 0
        for item in infos:
            name = item.filename.rstrip("/")
            safe_relative(name)
            require(name.casefold() not in seen, "PATH_COLLISION")
            seen[name.casefold()] = item.is_dir()
            # Some published SLF4J JARs use a 0xffff mode sentinel on empty
            # directory records. They remain opaque JAR metadata, never paths
            # to extract or permissions to apply. Keep their exact attributes.
            empty_sentinel = (opaque_metadata and item.is_dir() and item.external_attr == 0xffff0010
                              and item.file_size == item.compress_size == item.CRC == 0)
            require(stat.S_IFMT(item.external_attr >> 16) in (0, stat.S_IFREG, stat.S_IFDIR) or empty_sentinel,
                    "UNSAFE_PATH")
            require(not item.flag_bits & 1, "ARCHIVE_UNSUPPORTED")
            total += item.file_size
            require(total <= MAX_EXPANDED, "ARTIFACT_QUOTA")
        for name in seen:
            for parent in safe_relative(name).parents:
                if str(parent) != ".":
                    require(seen.get(str(parent), True), "PATH_COLLISION")
        return archive
    except BaseException:
        archive.close()
        raise


def _text(archive, name):
    require(archive.getinfo(name).file_size <= 65536, "ARTIFACT_QUOTA")
    return archive.read(name).decode("utf-8")


def _rows(archive, name, kind):
    rows, coordinates, paths = [], set(), set()
    for line in _text(archive, name).splitlines():
        fields = line.split("\t")
        require(len(fields) == 3, "VANILLA_BUNDLE_INVALID")
        sha, coordinate, relative = fields
        safe_relative(relative)
        require(re.fullmatch(r"[0-9a-f]{64}", sha), "VANILLA_BUNDLE_INVALID")
        if kind == "libraries":
            parts = coordinate.split(":")
            require(len(parts) in (3, 4) and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts),
                    "VANILLA_BUNDLE_INVALID")
            group, artifact, version, *classifier = parts
            suffix = "-" + classifier[0] if classifier else ""
            require(relative == f"{group.replace('.', '/')}/{artifact}/{version}/"
                    f"{artifact}-{version}{suffix}.jar", "VANILLA_BUNDLE_INVALID")
        else:
            require(coordinate == "1.19.2" and relative == "1.19.2/server-1.19.2.jar",
                    "VANILLA_BUNDLE_INVALID")
        require(coordinate not in coordinates and relative.casefold() not in paths, "PATH_COLLISION")
        coordinates.add(coordinate)
        paths.add(relative.casefold())
        member = f"META-INF/{kind}/{relative}"
        info = archive.getinfo(member)
        require(not info.is_dir(), "VANILLA_BUNDLE_INVALID")
        with archive.open(info) as stream:
            require(hashlib.file_digest(stream, "sha256").hexdigest() == sha, "VANILLA_PAYLOAD_MISMATCH")
        rows.append({"path": f"{kind}/{relative}", "digest": sha, "bytes": info.file_size,
                     "coordinate": coordinate, "bundle_member": member})
    require(0 < len(rows) <= (128 if kind == "libraries" else 1), "VANILLA_BUNDLE_INVALID")
    return rows


def _license_metadata(raw):
    """Retain exact embedded notices/POMs without inferring a component's license."""
    entries, notes = [], []
    with _archive(raw, max_members=50000, opaque_metadata=True) as archive:
        for item in archive.infolist():
            if item.is_dir() and item.external_attr == 0xffff0010:
                notes.append({"member": item.filename, "external_attributes": item.external_attr,
                              "disposition": "opaque_empty_directory_not_extracted"})
            leaf = item.filename.rsplit("/", 1)[-1].casefold()
            if (not item.is_dir() and (leaf == "pom.xml" or
                    re.fullmatch(r"(?:license|notice|copying)(?:\.[a-z0-9]+)?", leaf))):
                require(item.file_size <= 4 * 1024**2 and len(entries) < 128, "ARTIFACT_QUOTA")
                data = archive.read(item)
                entries.append({"member": item.filename, "bytes": len(data),
                                "sha256": hashlib.sha256(data).hexdigest()})
    return sorted(entries, key=lambda item: item["member"]), sorted(notes, key=lambda item: item["member"])


def _installed(root, files):
    require(root.is_absolute(), "UNSAFE_PATH")
    reject_links(root)
    require(root.is_dir(), "AWAITING_ARTIFACT")
    reject_links(root / "server.jar")
    require((root / "server.jar").is_file(), "AWAITING_ARTIFACT")
    require((root / "server.jar").stat().st_nlink == 1, "UNSAFE_PATH")
    actual = [{"path": "server.jar", "digest": file_hash(root / "server.jar"),
               "bytes": (root / "server.jar").stat().st_size}]
    for kind in ("libraries", "versions"):
        actual.extend(item | {"path": f"{kind}/{item['path']}"} for item in scan_tree(
            root / kind, max_files=129, max_bytes=MAX_EXPANDED))
        expected_dirs = {str(parent) for item in files if item["path"].startswith(kind + "/")
                         for parent in safe_relative(item["path"]).parents if str(parent) != "."}
        actual_dirs = {kind}
        for current, directories, _ in os.walk(root / kind, followlinks=False):
            actual_dirs.update((Path(current) / name).relative_to(root).as_posix() for name in directories)
        require(actual_dirs == expected_dirs, "VANILLA_RUNTIME_INVENTORY_MISMATCH")
    expected = [{key: item[key] for key in ("path", "digest", "bytes")} for item in files]
    require(sorted(actual, key=lambda item: item["path"]) == sorted(expected, key=lambda item: item["path"]),
            "VANILLA_RUNTIME_INVENTORY_MISMATCH")
    dispositions = []
    for path in sorted(root.iterdir()):
        reject_links(path)
        name = path.name
        if name in {"server.jar", "libraries", "versions"}:
            continue
        if name in CONFIG | STATE:
            require(path.is_file() and path.stat().st_nlink == 1, "UNSAFE_PATH")
            require(path.stat().st_size <= 4 * 1024**2, "ARTIFACT_QUOTA")
            dispositions.append({"path": name, "kind": "file", "digest": file_hash(path),
                                 "bytes": path.stat().st_size,
                                 "disposition": "configuration_pending" if name in CONFIG else "private_state_excluded"})
        elif name in {"world", "logs"}:
            require(path.is_dir(), "UNSAFE_PATH")
            dispositions.append({"path": name, "kind": "directory", "recursive_inventory": False,
                                 "disposition": "private_state_excluded" if name == "world" else "diagnostic_excluded"})
        else:
            raise Fault("VANILLA_RUNTIME_UNREVIEWED_CONTENT")
    return dispositions


def prepare_server(raw, root: Path, destination: Path):
    """Verify installed payloads against the acquired bundle, then copy fresh bytes.

    Call only with CAS-authorized bytes verified against release metadata. Any
    failure after destination creation preserves partial output for diagnosis;
    it never returns a successful receipt or overwrites/replays that directory.
    """
    require(root.is_absolute() and destination.is_absolute(), "UNSAFE_PATH")
    reject_links(root)
    reject_links(destination)
    require(root == root.resolve() and destination == destination.resolve()
            and not destination.is_relative_to(root) and not root.is_relative_to(destination), "UNSAFE_PATH")
    require(not destination.exists(), "DESTINATION_EXISTS")
    try:
        with _archive(raw, max_members=1024) as archive:
            manifest = _text(archive, "META-INF/MANIFEST.MF").replace("\r\n", "\n")
            require(manifest == "Manifest-Version: 1.0\nMain-Class: net.minecraft.bundler.Main\n"
                    "Bundler-Format: 1.0\n\n" and
                    _text(archive, "META-INF/main-class").strip() == "net.minecraft.server.Main",
                    "VANILLA_BUNDLE_INVALID")
            files = _rows(archive, "META-INF/versions.list", "versions")
            files += _rows(archive, "META-INF/libraries.list", "libraries")
            members = {item["bundle_member"] for item in files}
            require({item.filename for item in archive.infolist() if not item.is_dir() and
                     item.filename.startswith(("META-INF/libraries/", "META-INF/versions/"))} == members,
                    "VANILLA_BUNDLE_UNDECLARED_PAYLOAD")
            for item in files:
                item["license_metadata"], item["archive_notes"] = _license_metadata(archive.read(item["bundle_member"]))
                item["license_review"] = "pending"
            license_metadata, archive_notes = _license_metadata(raw)
            files.append({"path": "server.jar", "digest": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                          "coordinate": "net.minecraft:server-bundler:1.19.2", "bundle_member": None,
                          "license_metadata": license_metadata, "archive_notes": archive_notes,
                          "license_review": "pending"})
            files.sort(key=lambda item: item["path"])
            dispositions = _installed(root, files)
            destination.mkdir(parents=True, exist_ok=False)
            for item in files:
                target = destination / item["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                data = raw if item["bundle_member"] is None else archive.read(item["bundle_member"])
                with target.open("xb") as stream:
                    stream.write(data)
                require(file_hash(target) == item["digest"], "HASH_MISMATCH")
            require(_installed(root, files) == dispositions, "SOURCE_CHANGED")
            require(_installed(destination, files) == [], "VANILLA_RUNTIME_INVENTORY_MISMATCH")
        return {"policy": POLICY, "source_root": str(root), "software_root": str(destination),
                "files": files, "source_dispositions": dispositions,
                "installed_payloads_verified": True, "independent_software_copy_verified": True,
                "complete_role_qualified": False, "license_review_complete": False,
                "game_conformance_claim": None}
    except (KeyError, UnicodeError, zipfile.BadZipFile, NotImplementedError) as error:
        raise Fault("VANILLA_BUNDLE_INVALID") from error
