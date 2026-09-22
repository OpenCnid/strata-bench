"""Prepare exact Windows vanilla client software from retained official metadata.

Read only explicitly selected cache objects; do not copy a launcher directory,
credentials or game state. No downloads, authentication, extraction or launch.
"""

import hashlib
from pathlib import Path
import re
import zipfile

from .inference_transport import strict_json
from .inventory import file_hash, scan_tree
from .storage import Fault, reject_links, require, safe_relative
from .vanilla_runtime import _license_metadata

POLICY = "mojang-vanilla1192-windows-client-software/1"
MAX_TOTAL = 2 * 1024**3


def _pin(item, url):
    require(isinstance(item, dict) and isinstance(item.get("sha1"), str)
            and re.fullmatch(r"[0-9a-f]{40}", item["sha1"])
            and type(item.get("size")) is int and 0 < item["size"] <= 512 * 1024**2
            and item.get("url") == url, "VANILLA_CLIENT_METADATA_INVALID")
    return {"sha1": item["sha1"], "bytes": item["size"], "origin": url}


def _path(root):
    require(isinstance(root, Path) and root.is_absolute(), "UNSAFE_PATH")
    reject_links(root)
    require(root == root.resolve(), "UNSAFE_PATH")
    return root


def _hash(path, item):
    reject_links(path)
    require(path.is_file(), "AWAITING_ARTIFACT")
    info = path.stat()
    require(info.st_nlink == 1, "UNSAFE_PATH")
    require(info.st_size == item["bytes"], "VANILLA_CLIENT_ARTIFACT_MISMATCH")
    sha1, sha256, total = hashlib.sha1(), hashlib.sha256(), 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024**2):
            total += len(chunk)
            require(total <= item["bytes"], "VANILLA_CLIENT_ARTIFACT_MISMATCH")
            sha1.update(chunk)
            sha256.update(chunk)
    require(total == item["bytes"] and sha1.hexdigest() == item["sha1"], "VANILLA_CLIENT_ARTIFACT_MISMATCH")
    return sha256.hexdigest()


def _libraries(version):
    libraries = version.get("libraries")
    require(isinstance(libraries, list) and 0 < len(libraries) <= 512, "VANILLA_CLIENT_METADATA_INVALID")
    selected, excluded, seen = [], [], set()
    for item in libraries:
        require(isinstance(item, dict) and set(item) <= {"name", "downloads", "rules"},
                "VANILLA_CLIENT_METADATA_INVALID")
        coordinate = item.get("name")
        require(isinstance(coordinate, str), "VANILLA_CLIENT_METADATA_INVALID")
        parts = coordinate.split(":")
        require(len(parts) in (3, 4) and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts),
                "VANILLA_CLIENT_METADATA_INVALID")
        group, artifact, version_id, *classifier = parts
        suffix = "-" + classifier[0] if classifier else ""
        relative = f"{group.replace('.', '/')}/{artifact}/{version_id}/{artifact}-{version_id}{suffix}.jar"
        safe_relative(relative)
        require(relative.casefold() not in seen, "PATH_COLLISION")
        seen.add(relative.casefold())
        downloads = item.get("downloads")
        require(isinstance(downloads, dict) and set(downloads) == {"artifact"}, "VANILLA_CLIENT_METADATA_INVALID")
        artifact = downloads["artifact"]
        pin = _pin(artifact, "https://libraries.minecraft.net/" + relative)
        require(artifact.get("path") == relative, "VANILLA_CLIENT_METADATA_INVALID")
        rules = item.get("rules")
        if "rules" in item:
            require(rules in [[{"action": "allow", "os": {"name": name}}]
                              for name in ("windows", "linux", "osx")], "VANILLA_CLIENT_RULE_UNSUPPORTED")
        if rules is None or rules == [{"action": "allow", "os": {"name": "windows"}}]:
            selected.append({"path": "libraries/" + relative, "coordinate": coordinate, **pin})
        else:
            excluded.append({"coordinate": coordinate, "rules": rules, "disposition": "other_operating_system"})
    require(bool(selected), "VANILLA_CLIENT_METADATA_INVALID")
    return selected, excluded


def prepare_client(client_raw, version_raw, assets: Path, library_roots: list[Path], destination: Path):
    """Caller must first bind client/version bytes to the durable acquisition."""
    _path(assets)
    _path(destination)
    require(1 <= len(library_roots) <= 4 and len(set(library_roots)) == len(library_roots), "UNSAFE_PATH")
    for root in [assets, *library_roots]:
        _path(root)
        require(root.is_dir() and not destination.is_relative_to(root) and not root.is_relative_to(destination),
                "UNSAFE_PATH")
    require(not destination.exists(), "DESTINATION_EXISTS")
    version = strict_json(version_raw)
    require(isinstance(version, dict) and version.get("id") == "1.19.2"
            and version.get("mainClass") == "net.minecraft.client.main.Main"
            and version.get("javaVersion") == {"component": "java-runtime-gamma", "majorVersion": 17},
            "VANILLA_CLIENT_METADATA_INVALID")
    files, excluded = _libraries(version)
    for item in files:
        relative = item["path"][len("libraries/"):]
        # Never hide a corrupted earlier candidate by falling back to another.
        candidates = [root / relative for root in library_roots]
        for candidate in candidates:
            reject_links(candidate)
        source = next((path for path in candidates if path.exists()), None)
        require(source is not None, "AWAITING_ARTIFACT")
        item.update(source_path=str(source), digest=_hash(source, item))
    index = version.get("assetIndex")
    require(isinstance(index, dict) and index.get("id") == version.get("assets") == "1.19"
            and type(index.get("totalSize")) is int and 0 < index["totalSize"] <= MAX_TOTAL,
            "VANILLA_CLIENT_METADATA_INVALID")
    pin = _pin(index, f"https://piston-meta.mojang.com/v1/packages/{index.get('sha1')}/1.19.json")
    require(pin["bytes"] <= 4 * 1024**2, "ARTIFACT_QUOTA")
    index_path = assets / "indexes/1.19.json"
    index_digest = _hash(index_path, pin)
    index_raw = index_path.read_bytes()
    require(hashlib.sha256(index_raw).hexdigest() == index_digest, "SOURCE_CHANGED")
    parsed = strict_json(index_raw)
    require(isinstance(parsed, dict) and set(parsed) == {"objects"} and isinstance(parsed["objects"], dict)
            and 0 < len(parsed["objects"]) <= 20000, "VANILLA_ASSET_INDEX_INVALID")
    objects, logical_total = {}, 0
    for name, value in parsed["objects"].items():
        safe_relative(name)
        require(isinstance(value, dict) and set(value) == {"hash", "size"}
                and isinstance(value["hash"], str) and re.fullmatch(r"[0-9a-f]{40}", value["hash"])
                and type(value["size"]) is int and 0 <= value["size"] <= 128 * 1024**2,
                "VANILLA_ASSET_INDEX_INVALID")
        sha, size = value["hash"], value["size"]
        require(sha not in objects or objects[sha] == size, "VANILLA_ASSET_INDEX_INVALID")
        objects[sha] = size
        logical_total += size
        require(logical_total <= MAX_TOTAL, "ARTIFACT_QUOTA")
    require(logical_total == index["totalSize"], "VANILLA_ASSET_INDEX_INVALID")
    for sha, size in sorted(objects.items()):
        relative = f"objects/{sha[:2]}/{sha}"
        source = assets / relative
        item = {"path": "assets/" + relative, "sha1": sha, "bytes": size,
                "origin": "https://resources.download.minecraft.net/" + sha[:2] + "/" + sha}
        item.update(source_path=str(source), digest=_hash(source, item))
        files.append(item)
    files.append({"path": "assets/indexes/1.19.json", "source_path": str(index_path), "digest": index_digest, **pin})
    logging = version.get("logging")
    require(isinstance(logging, dict) and set(logging) == {"client"}, "VANILLA_CLIENT_METADATA_INVALID")
    logging = logging["client"]
    require(isinstance(logging, dict) and logging.get("type") == "log4j2-xml"
            and logging.get("argument") == "-Dlog4j.configurationFile=${path}"
            and isinstance(logging.get("file"), dict) and logging["file"].get("id") == "client-1.12.xml",
            "VANILLA_CLIENT_METADATA_INVALID")
    item = logging["file"]
    pin = _pin(item, f"https://piston-data.mojang.com/v1/objects/{item.get('sha1')}/client-1.12.xml")
    source = assets / "log_configs/client-1.12.xml"
    files.append({"path": "assets/log_configs/client-1.12.xml", "source_path": str(source),
                  "digest": _hash(source, pin), **pin})
    client_pin = _pin(version["downloads"]["client"],
                      f"https://piston-data.mojang.com/v1/objects/{hashlib.sha1(client_raw).hexdigest()}/client.jar")
    require(len(client_raw) == client_pin["bytes"] and hashlib.sha1(client_raw).hexdigest() == client_pin["sha1"],
            "VANILLA_CLIENT_ARTIFACT_MISMATCH")
    files.append({"path": "versions/1.19.2/1.19.2.jar", "digest": hashlib.sha256(client_raw).hexdigest(), **client_pin})
    files.append({"path": "versions/1.19.2/1.19.2.json", "digest": hashlib.sha256(version_raw).hexdigest(),
                  "sha1": hashlib.sha1(version_raw).hexdigest(), "bytes": len(version_raw),
                  "origin": f"https://piston-meta.mojang.com/v1/packages/{hashlib.sha1(version_raw).hexdigest()}/1.19.2.json"})
    require(sum(item["bytes"] for item in files) <= MAX_TOTAL, "ARTIFACT_QUOTA")
    classpath = [item["path"] for item in files if item["path"].endswith(".jar")]
    # All validation above precedes output creation. Unexpected copy failures
    # retain partial bytes and never publish successful evidence or reuse them.
    destination.mkdir(parents=True, exist_ok=False)
    for item in files:
        target = destination / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if "source_path" in item:
            source = Path(item["source_path"])
            reject_links(source)
            total, sha = 0, hashlib.sha256()
            with source.open("rb") as input_stream, target.open("xb") as output_stream:
                while chunk := input_stream.read(1024**2):
                    total += len(chunk)
                    require(total <= item["bytes"], "SOURCE_CHANGED")
                    output_stream.write(chunk)
                    sha.update(chunk)
            require(total == item["bytes"] and sha.hexdigest() == item["digest"], "SOURCE_CHANGED")
        else:
            with target.open("xb") as stream:
                stream.write(client_raw if item["path"].endswith(".jar") else version_raw)
        if item["path"].endswith(".jar"):
            try:
                item["license_metadata"], item["archive_notes"] = _license_metadata(target.read_bytes())
            except (KeyError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
                raise Fault("VANILLA_CLIENT_ARCHIVE_INVALID") from error
            item["license_review"] = "pending"
    expected = sorted(({k: item[k] for k in ("path", "digest", "bytes")} for item in files), key=lambda item: item["path"])
    require(scan_tree(destination, max_files=21000, max_bytes=MAX_TOTAL) == expected, "VANILLA_CLIENT_INVENTORY_MISMATCH")
    for item in files:
        if "source_path" in item:
            require(file_hash(Path(item["source_path"])) == item["digest"], "SOURCE_CHANGED")
    return {"policy": POLICY, "platform": "windows", "software_root": str(destination),
            "library_roots": [str(path) for path in library_roots], "assets_root": str(assets),
            "files": sorted(files, key=lambda item: item["path"]), "classpath": classpath,
            "excluded_libraries": excluded, "asset_names": len(parsed["objects"]),
            "unique_asset_objects": len(objects), "source_selection": "only_metadata_named_objects",
            "independent_software_copy_verified": True, "complete_role_qualified": False,
            "license_review_complete": False, "launch_configuration_qualified": False,
            "game_conformance_claim": None}
