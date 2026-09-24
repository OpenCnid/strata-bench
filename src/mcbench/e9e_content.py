"""Exact E9E vendor content for role assembly, never a game installation runner.

Archive pins bind the official intake; mod pins bind the retained pre-game
operator captures. Those captures are not publisher signatures. Runtime state
and generated/effective settings are intentionally outside this component.
"""

import hashlib
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .forge_runtime import read_input
from .inference_transport import strict_json
from .inventory import file_hash, scan_tree, template_path
from .pack_policies import reviewed_vendor_paths
from .storage import Fault, reject_links, require, safe_relative
from .vanilla_runtime import _archive

POLICY = "e9e1270-vendor-content/1"
ARCHIVES = {
    "client": "04ece07ebd0ff973ea055195d7577194cc363feeb44cf973670218d89437922e",
    "server": "4667d8b9e430abb5306590350daab3d67c06ef0655a5a1feeb2f9eb19cecbeb7",
}
CAPTURES = {
    "client": "db2c998b0ef055bb44fabe45aa3be966a65b572fb12fc2941aa9c5de16eb74e5",
    "server": "6e218ce90a3cc32cda38924c828c5f256a34850ec83cc024fca3e95c54e9bf23",
}
SERVER_CONFIG = "8527a25c0875073173ea7c676d1625badb6c31cc289cc2d5329ed09f9008c514"
IGNORE_PROJECTS = {231275, 391382, 238372, 271740, 358191, 513857,
                   521714, 360673, 401648, 363363, 901997}
IGNORE_TREES = ("resources/", "packmenu/", "kubejs/assets/", "kubejs/client_scripts/",
                "building_gadgets_patterns/", "local/")
MAX_BYTES = 2 * 1024**3


def server_exclusion(path):
    # Exact reviewed ServerStarter Java glob semantics: '*' cannot cross '/'.
    # Paths.get removes a directory entry's trailing slash before matching.
    path = path.rstrip("/")
    for prefix in IGNORE_TREES:
        if path.startswith(prefix):
            return prefix + "**"
    if re.fullmatch(r"(?:config|defaultconfigs)/[^/]*-client\.toml", path):
        return path.split("/", 1)[0] + "/*-client.toml"
    return None


def _url(url, file_id):
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname == "edge.forgecdn.net" and
            parsed.port is None and parsed.username is None and parsed.password is None and
            not parsed.query and not parsed.fragment, "E9E_MOD_ORIGIN_INVALID")
    parts = parsed.path.split("/")
    require(len(parts) == 5 and parts[:2] == ["", "files"] and
            parts[2].isdigit() and parts[3].isdigit() and
            int(parts[2]) * 1000 + int(parts[3]) == file_id, "E9E_MOD_ORIGIN_INVALID")
    safe_relative(parts[4])
    require(len(safe_relative(unquote(parts[4])).parts) == 1 and parts[4].endswith(".jar"),
            "E9E_MOD_ORIGIN_INVALID")
    return parts[4]


def _manifest(raw):
    data = strict_json(raw)
    require(data["version"] == "1.27.0" and data["manifestType"] == "minecraftModpack"
            and data["manifestVersion"] == 1 and data["overrides"] == "overrides"
            and data["minecraft"] == {"version": "1.19.2", "modLoaders": [
                {"id": "forge-43.4.23", "primary": True}]}, "E9E_RELEASE_MISMATCH")
    require(isinstance(data["files"], list) and 0 < len(data["files"]) <= 512, "E9E_MANIFEST_INVALID")
    result = {}
    for row in data["files"]:
        project, file_id = row["projectID"], row["fileID"]
        require(type(project) is int and type(file_id) is int and project > 0 and file_id > 0
                and row["required"] is True and project not in result, "E9E_MANIFEST_INVALID")
        result[project] = row
    return result


def _archives(raws):
    require(set(raws) == {"client", "server"}, "ROLE_MISMATCH")
    contents, manifests, dispositions = {}, {}, {}
    for role, raw in raws.items():
        require(len(raw) <= 64 * 1024**2 and hashlib.sha256(raw).hexdigest() == ARCHIVES[role],
                "E9E_ARCHIVE_MISMATCH")
        contents[role], dispositions[role] = {}, []
        with _archive(raw, max_members=20000) as archive:
            manifests[role] = _manifest(archive.read("manifest.json"))
            if role == "server":
                require(hashlib.sha256(archive.read("server-setup-config.yaml")).hexdigest() == SERVER_CONFIG,
                        "E9E_SERVER_POLICY_MISMATCH")
            for info in archive.infolist():
                if not info.filename.startswith("overrides/") or info.filename == "overrides/":
                    if not info.is_dir():
                        metadata_raw = archive.read(info)
                        dispositions[role].append({"path": info.filename, "member": info.filename,
                            "directory": False, "digest": hashlib.sha256(metadata_raw).hexdigest(),
                            "bytes": len(metadata_raw), "disposition": "vendor_metadata_or_bootstrap_not_executed"})
                    continue
                path = info.filename.removeprefix("overrides/").rstrip("/")
                template_path(path, reviewed_world_paths=reviewed_vendor_paths("e9e"))
                require(not path.startswith("mods/") and path != "mods", "E9E_OVERRIDE_MOD_UNSUPPORTED")
                raw = b"" if info.is_dir() else archive.read(info)
                sha = None if info.is_dir() else hashlib.sha256(raw).hexdigest()
                reviewed = reviewed_vendor_paths("e9e")
                if path in reviewed:
                    require(sha == reviewed[path] and info.is_dir() == (reviewed[path] is None),
                            "VENDOR_CONTENT_MISMATCH")
                contents[role][path] = {"member": info.filename, "directory": info.is_dir(),
                                         "digest": sha, "bytes": len(raw)}
    require(contents["client"] == contents["server"], "E9E_OVERRIDE_ROLE_MISMATCH")
    require({p: (r["fileID"], r["required"]) for p, r in manifests["client"].items()} ==
            {p: (r["fileID"], r["required"]) for p, r in manifests["server"].items()},
            "E9E_MANIFEST_ROLE_MISMATCH")
    for row in manifests["client"].values():
        _url(row["downloadUrl"], row["fileID"])
    for role in contents:
        selected = {}
        for path, row in contents[role].items():
            pattern = server_exclusion(path + "/" if row["directory"] else path) if role == "server" else None
            if pattern:
                dispositions[role].append({"path": path, **row, "disposition": "vendor_server_ignore",
                                           "pattern": pattern})
            else:
                selected[path] = row
        contents[role] = selected
    return contents, manifests["client"], dispositions


def _mods(role, raw, manifest):
    require(len(raw) <= 2 * 1024**2 and hashlib.sha256(raw).hexdigest() == CAPTURES[role],
            "E9E_MOD_CAPTURE_MISMATCH")
    capture = strict_json(raw)
    require(capture["missing"] == [] and capture["extra"] == [] and
            isinstance(capture["files"], list) and len(capture["files"]) <= 512, "E9E_MOD_CAPTURE_INVALID")
    selected = {p: row for p, row in manifest.items() if role == "client" or p not in IGNORE_PROJECTS}
    result, seen = {}, set()
    for item in capture["files"]:
        entry = item["manifest"]
        project = entry["projectID"]
        require(project in selected and project not in seen, "E9E_MOD_CAPTURE_INVALID")
        seen.add(project)
        require(entry == selected[project], "E9E_MOD_CAPTURE_MANIFEST_MISMATCH")
        relative = safe_relative(item["path"])
        filename = _url(entry["downloadUrl"], entry["fileID"])
        require(len(relative.parts) == 2 and relative.parts[0] == "mods" and
                relative.name in {filename, unquote(filename)} and
                str(relative).casefold() not in {p.casefold() for p in result}, "E9E_MOD_PATH_MISMATCH")
        require(type(item["bytes"]) is int and 0 < item["bytes"] <= 256 * 1024**2 and
                isinstance(item["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]),
                "E9E_MOD_CAPTURE_INVALID")
        result[str(relative)] = {"path": str(relative), "digest": item["sha256"], "bytes": item["bytes"],
            "project_id": project, "file_id": entry["fileID"], "origin": entry["downloadUrl"],
            "source_capture_sha256": CAPTURES[role], "authority": "retained_operator_intake",
            "license_review": "pending"}
    require(seen == set(selected), "E9E_MOD_CAPTURE_INCOMPLETE")
    return result


def prepare_content(archives, captures, mod_roots, excluded_harness, destination: Path):
    """Prepare both roles' initial vendor content, not generated/effective state.

    `mod_roots` names only existing mods directories. `excluded_harness` lists
    exact source additions to retain in the audit, never vendor omissions.
    Everything is validated for both roles before creating the destination.
    """
    require(set(captures) == set(mod_roots) == set(excluded_harness) == {"client", "server"}, "ROLE_MISMATCH")
    require(destination.is_absolute(), "UNSAFE_PATH")
    reject_links(destination)
    require(destination == destination.resolve() and not destination.exists(), "DESTINATION_EXISTS")
    for root in mod_roots.values():
        require(root.is_absolute() and root == root.resolve(), "UNSAFE_PATH")
        reject_links(root)
        require(not root.is_relative_to(destination) and not destination.is_relative_to(root), "UNSAFE_PATH")
    try:
        overrides, manifest, dispositions = _archives(archives)
        mods = {role: _mods(role, captures[role], manifest) for role in ("client", "server")}
        client_by_id = {r["project_id"]: r for r in mods["client"].values()}
        require(all((r["digest"], r["bytes"]) == (client_by_id[r["project_id"]]["digest"],
                    client_by_id[r["project_id"]]["bytes"]) for r in mods["server"].values()),
                "E9E_MOD_ROLE_MISMATCH")
        before = {}
        for role, root in mod_roots.items():
            before[role] = scan_tree(root, max_files=520, max_bytes=MAX_BYTES)
            expected = [{"path": p.removeprefix("mods/"), "digest": row["digest"], "bytes": row["bytes"]}
                        for p, row in mods[role].items()]
            extras = excluded_harness[role]
            require(isinstance(extras, list) and len(extras) <= 8, "E9E_HARNESS_EXCLUSION_INVALID")
            for row in extras:
                require(set(row) == {"path", "digest", "bytes"} and
                        re.fullmatch(r"strata-forge1192-(?:client|telemetry)-[0-9.]+\.jar", row["path"])
                        and len(safe_relative(row["path"]).parts) == 1 and
                        type(row["bytes"]) is int and row["bytes"] > 0 and
                        re.fullmatch(r"[0-9a-f]{64}", row["digest"]), "E9E_HARNESS_EXCLUSION_INVALID")
            expected += extras
            require(len({r["path"].casefold() for r in expected}) == len(expected) and
                    before[role] == sorted(expected, key=lambda r: r["path"]), "E9E_INSTALLED_MOD_MISMATCH")
        destination.mkdir(parents=True, exist_ok=False)
        roles = []
        for role in ("client", "server"):
            output, files, directories = destination / role, [], []
            output.mkdir()
            with _archive(archives[role], max_members=20000) as archive:
                for path, row in sorted(overrides[role].items()):
                    target = output / path
                    if row["directory"]:
                        target.mkdir(parents=True, exist_ok=True)
                        directories.append(path)
                        continue
                    raw = archive.read(row["member"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(raw)
                    files.append({"path": path, "digest": row["digest"], "bytes": row["bytes"],
                        "archive_sha256": ARCHIVES[role], "archive_member": row["member"],
                        "origin": f"archive:sha256:{ARCHIVES[role]}!/{row['member']}", "license_review": "pending"})
            for path, row in sorted(mods[role].items()):
                raw = read_input(mod_roots[role] / path.removeprefix("mods/"), 256 * 1024**2)
                require(hashlib.sha256(raw).hexdigest() == row["digest"] and len(raw) == row["bytes"], "SOURCE_CHANGED")
                target = output / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(raw)
                require(file_hash(target) == row["digest"], "HASH_MISMATCH")
                files.append(row)
            files.sort(key=lambda r: r["path"])
            require(scan_tree(output, max_files=20000, max_bytes=MAX_BYTES,
                              reviewed_world_paths=reviewed_vendor_paths("e9e")) ==
                    [{k: row[k] for k in ("path", "digest", "bytes")} for row in files], "E9E_CONTENT_COPY_MISMATCH")
            roles.append({"role": role, "root": str(output), "files": files, "vendor_directories": directories,
                "archive_exclusions": dispositions[role], "excluded_source_harness": excluded_harness[role],
                "excluded_projects": sorted(set(manifest) & IGNORE_PROJECTS) if role == "server" else [],
                "initial_vendor_content": True, "effective_expert_settings_qualified": False})
        require(all(scan_tree(root, max_files=520, max_bytes=MAX_BYTES) == before[role]
                    for role, root in mod_roots.items()), "SOURCE_CHANGED")
        return {"schema": "strata/E9EVendorContent/1", "policy": POLICY, "roles": roles,
                "archives": ARCHIVES, "mod_captures": CAPTURES, "server_policy_sha256": SERVER_CONFIG,
                "mod_sources": {role: str(root) for role, root in mod_roots.items()},
                "complete_roles_qualified": False, "license_review_complete": False,
                "bootstrap_executed": False, "game_conformance_claim": None}
    except (KeyError, TypeError, UnicodeError, zipfile.BadZipFile, NotImplementedError) as error:
        raise Fault("E9E_CONTENT_INVALID") from error
