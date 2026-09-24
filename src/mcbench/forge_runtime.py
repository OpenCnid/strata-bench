"""Prepare pinned E9E server libraries without running Forge or an installer.

Only software bytes with publisher metadata/archive joins are copied. Four
files are excluded from this subset. The SRG JAR is runtime-required and must
be supplied by the separate verified forge_derivation producer. This is an
input to role preparation, not complete provisioning or a licensing assertion.
"""

import hashlib
import re
import zipfile
from pathlib import Path

from .inference_transport import strict_json
from .inventory import file_hash, scan_tree
from .storage import Fault, reject_links, require, safe_relative
from .vanilla_artifacts import metadata
from .vanilla_runtime import _archive, _rows

POLICY = "e9e1270-forge43423-server-libraries/1"
INSTALLER_SHA256 = "5e801fb105951a4cea7d9b57edaea4a5d22b83107822f099167c95179a7e93a1"
INSTALLER_URL = ("https://maven.minecraftforge.net/net/minecraftforge/forge/"
                 "1.19.2-43.4.23/forge-1.19.2-43.4.23-installer.jar")
MC = "1.19.2-20220805.130853"
FORGE = "1.19.2-43.4.23"
MCP = f"de/oceanlabs/mcp/mcp_config/{MC}/mcp_config-{MC}"
SERVER = f"net/minecraft/server/{MC}/server-{MC}"
FORGE_DIR = f"net/minecraftforge/forge/{FORGE}"
EXCLUSIONS = {
    MCP + "-mappings-merged.txt": "installer_merged_mapping_intermediate",
    # Retain the original evidence label; it does not mean runtime-unnecessary.
    SERVER + "-srg.jar": "installer_renaming_intermediate",
    SERVER + "-slim.jar.cache": "installer_split_cache",
    SERVER + "-extra.jar.cache": "installer_split_cache",
}
MAX_BYTES = 512 * 1024**2


def read_input(path: Path, limit: int):
    reject_links(path.absolute())
    require(path.is_file() and path.stat().st_nlink == 1, "UNSAFE_PATH")
    require(path.stat().st_size <= limit, "ARTIFACT_QUOTA")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "ARTIFACT_QUOTA")
    return raw


def _coordinate(value):
    require(isinstance(value, str), "FORGE_METADATA_INVALID")
    parts = value.split("@")
    require(len(parts) <= 2, "FORGE_METADATA_INVALID")
    fields = parts[0].split(":")
    require(len(fields) in (3, 4) and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p)
            for p in fields + parts[1:]), "FORGE_METADATA_INVALID")
    group, artifact, version, *classifier = fields
    suffix = "-" + classifier[0] if classifier else ""
    extension = parts[1] if len(parts) == 2 else "jar"
    return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}{suffix}.{extension}"


def _catalog(installer, bundle, manifest_raw, version_raw):
    """Derive file expectations from retained, exact publisher sources."""
    require(len(installer) <= 16 * 1024**2 and
            hashlib.sha256(installer).hexdigest() == INSTALLER_SHA256, "FORGE_INSTALLER_MISMATCH")
    source = metadata(manifest_raw, version_raw)
    server = source["downloads"]["server"]
    require(len(bundle) == server["bytes"] and
            hashlib.sha1(bundle).hexdigest() == server["sha1"], "VANILLA_DISTRIBUTION_MISMATCH")
    expected = {}

    def add(path, algorithm, sha, size, origin):
        safe_relative(path)
        require(algorithm in {"sha1", "sha256"} and isinstance(sha, str) and
                re.fullmatch(r"[0-9a-f]{" + str(40 if algorithm == "sha1" else 64) + "}", sha)
                and (size is None or type(size) is int and 0 < size <= MAX_BYTES),
                "FORGE_METADATA_INVALID")
        item = {"algorithm": algorithm, "expected_hash": sha, "expected_bytes": size,
                "origins": [origin]}
        if path in expected:
            previous = expected[path]
            require(all(previous[k] == item[k] for k in ("algorithm", "expected_hash", "expected_bytes")),
                    "FORGE_SOURCE_CONFLICT")
            previous["origins"].append(origin)
        else:
            require(path.casefold() not in {p.casefold() for p in expected}, "PATH_COLLISION")
            expected[path] = item

    def embedded(path, raw, archive_sha, member):
        add(path, "sha256", hashlib.sha256(raw).hexdigest(), len(raw),
            {"kind": "archive_member", "archive_sha256": archive_sha, "member": member})

    with _archive(installer, max_members=10000) as archive:
        profile = strict_json(archive.read("install_profile.json"))
        version = strict_json(archive.read("version.json"))
        require(profile["spec"] == 1 and profile["minecraft"] == "1.19.2" and
                profile["version"] == version["id"] == "1.19.2-forge-43.4.23" and
                version["inheritsFrom"] == "1.19.2", "FORGE_RELEASE_MISMATCH")
        for member, document in (("install_profile.json", profile), ("version.json", version)):
            require(isinstance(document["libraries"], list) and len(document["libraries"]) <= 128,
                    "FORGE_METADATA_INVALID")
            for entry in document["libraries"]:
                artifact = entry["downloads"]["artifact"]
                require(artifact["path"] == _coordinate(entry["name"]) and
                        artifact["url"].startswith("https://"), "FORGE_METADATA_INVALID")
                add(artifact["path"], "sha1", artifact["sha1"], artifact["size"],
                    {"kind": "publisher_library", "installer_sha256": INSTALLER_SHA256,
                     "metadata_member": member, "coordinate": entry["name"], "url": artifact["url"]})
        # The pinned installer declares hashes for these generated outputs.
        # Do not replace those expected hashes with observed installation bytes.
        for variable in ("MC_SLIM", "MC_EXTRA", "PATCHED"):
            coordinate = profile["data"][variable]["server"]
            quoted_sha = profile["data"][variable + "_SHA"]["server"]
            require(coordinate.startswith("[") and coordinate.endswith("]") and
                    re.fullmatch(r"'[0-9a-f]{40}'", quoted_sha), "FORGE_METADATA_INVALID")
            add(_coordinate(coordinate[1:-1]), "sha1", quoted_sha[1:-1], None,
                {"kind": "publisher_processor_output", "installer_sha256": INSTALLER_SHA256,
                 "metadata_member": "install_profile.json", "variable": variable})
        for name in ("win_args.txt", "unix_args.txt"):
            embedded(f"{FORGE_DIR}/{name}", archive.read("data/" + name), INSTALLER_SHA256, "data/" + name)
    bundle_sha = hashlib.sha256(bundle).hexdigest()
    add("net/minecraft/server/1.19.2/server-1.19.2.jar", "sha1", server["sha1"], server["bytes"],
        {"kind": "mojang_distribution", "url": server["url"], "version_sha256": source["version_sha256"]})
    with _archive(bundle, max_members=1024) as archive:
        for item in _rows(archive, "META-INF/libraries.list", "libraries"):
            # Some libraries occur in both sources with different hash algorithms.
            path = item["path"].removeprefix("libraries/")
            raw = archive.read(item["bundle_member"])
            if path in expected:
                prior = expected[path]
                require(hashlib.new(prior["algorithm"], raw).hexdigest() == prior["expected_hash"]
                        and len(raw) == prior["expected_bytes"], "FORGE_SOURCE_CONFLICT")
                prior["origins"].append({"kind": "archive_member", "archive_sha256": bundle_sha,
                                         "member": item["bundle_member"]})
            else:
                embedded(path, raw, bundle_sha, item["bundle_member"])
        unpacked = _rows(archive, "META-INF/versions.list", "versions")
        require(len(unpacked) == 1, "VANILLA_BUNDLE_INVALID")
        member = unpacked[0]["bundle_member"]
        embedded(SERVER + "-unpacked.jar", archive.read(member), bundle_sha, member)
    mapping = strict_json(version_raw)["downloads"]["server_mappings"]
    require(mapping["url"] == f"https://piston-data.mojang.com/v1/objects/{mapping['sha1']}/server.txt",
            "FORGE_METADATA_INVALID")
    add(SERVER + "-mappings.txt", "sha1", mapping["sha1"], mapping["size"],
        {"kind": "mojang_mappings", "url": mapping["url"], "version_sha256": source["version_sha256"]})
    return expected, source


def prepare_server_libraries(installer: bytes, bundle: bytes, manifest_raw: bytes,
                             version_raw: bytes, root: Path, destination: Path):
    """Produce a fresh libraries tree and provenance for subsequent role assembly.

    `root` names only the stopped installation's libraries directory. No shared
    launcher/account folders, world, mod configuration or bootstrap is consumed.
    Partial destinations survive failure and cannot be reused.
    """
    require(root.is_absolute() and destination.is_absolute(), "UNSAFE_PATH")
    for path in (root, destination):
        reject_links(path)
        require(path == path.resolve(), "UNSAFE_PATH")
    require(not root.is_relative_to(destination) and not destination.is_relative_to(root), "UNSAFE_PATH")
    require(not destination.exists(), "DESTINATION_EXISTS")
    try:
        expected, source = _catalog(installer, bundle, manifest_raw, version_raw)
        before = scan_tree(root, max_files=256, max_bytes=MAX_BYTES)
        actual = {row["path"]: row for row in before}
        mcp_zip = MCP + ".zip"
        mcp_raw = read_input(root / mcp_zip, 32 * 1024**2)
        pin = expected[mcp_zip]
        require(len(mcp_raw) == pin["expected_bytes"] and
                hashlib.new(pin["algorithm"], mcp_raw).hexdigest() == pin["expected_hash"], "FORGE_FILE_MISMATCH")
        with _archive(mcp_raw, max_members=50000) as archive:
            member = strict_json(archive.read("config.json"))["data"]["mappings"]
            safe_relative(member)
            raw = archive.read(member)
            expected[MCP + "-mappings.txt"] = {
                "algorithm": "sha256", "expected_hash": hashlib.sha256(raw).hexdigest(),
                "expected_bytes": len(raw), "origins": [{"kind": "archive_member",
                    "archive_sha256": hashlib.sha256(mcp_raw).hexdigest(), "member": member}]}
        require(set(actual) == set(expected) | set(EXCLUSIONS), "FORGE_RUNTIME_INVENTORY_MISMATCH")
        files = []
        # Validate all selected bytes before creating a partial destination.
        for path, pin in sorted(expected.items()):
            raw = read_input(root / path, MAX_BYTES)
            require(hashlib.sha256(raw).hexdigest() == actual[path]["digest"] and
                    hashlib.new(pin["algorithm"], raw).hexdigest() == pin["expected_hash"] and
                    (pin["expected_bytes"] is None or len(raw) == pin["expected_bytes"]), "FORGE_FILE_MISMATCH")
            files.append(actual[path] | {"origins": pin["origins"], "license_review": "pending"})
        exclusions = [actual[path] | {"disposition": reason, "copied": False,
                       "provenance_qualified": False} for path, reason in sorted(EXCLUSIONS.items())]
        destination.mkdir(parents=True, exist_ok=False)
        for item in files:
            path = item["path"]
            raw = read_input(root / path, MAX_BYTES)
            require(hashlib.sha256(raw).hexdigest() == item["digest"], "SOURCE_CHANGED")
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
            require(file_hash(target) == item["digest"], "HASH_MISMATCH")
        require(scan_tree(root, max_files=256, max_bytes=MAX_BYTES) == before, "SOURCE_CHANGED")
        require(scan_tree(destination, max_files=256, max_bytes=MAX_BYTES) ==
                [{key: row[key] for key in ("path", "digest", "bytes")} for row in files],
                "FORGE_RUNTIME_INVENTORY_MISMATCH")
        return {"schema": "strata/ForgeServerLibraries/1", "policy": POLICY,
                "source_root": str(root), "software_root": str(destination), "files": files,
                "source_dispositions": exclusions, "source_verification": source,
                "installer_sha256": INSTALLER_SHA256, "installer_url": INSTALLER_URL,
                "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
                "installed_payloads_verified": True, "independent_software_copy_verified": True,
                "installer_executed": False, "complete_role_qualified": False,
                "license_review_complete": False, "game_conformance_claim": None}
    except (KeyError, TypeError, UnicodeError, zipfile.BadZipFile, NotImplementedError) as error:
        raise Fault("FORGE_METADATA_INVALID") from error
