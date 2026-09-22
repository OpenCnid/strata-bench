"""Join retained Mojang metadata to exact vanilla distributions, without launch.

The official HTTPS capture remains operator evidence, not a signed Mojang
attestation. Matching distributions do not qualify installed role inventories.
"""

import hashlib
from pathlib import Path
import re

from .inference_transport import strict_json
from .storage import Fault, reject_links, require

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
POLICY = "mojang-vanilla1192-distributions/1"


def metadata(manifest_raw, version_raw):
    require(len(manifest_raw) <= 4 * 1024**2 and len(version_raw) <= 2 * 1024**2, "ARTIFACT_QUOTA")
    try:
        manifest, version = strict_json(manifest_raw), strict_json(version_raw)
        require(isinstance(manifest, dict) and isinstance(version, dict), "VANILLA_METADATA_INVALID")
        versions = manifest.get("versions")
        require(isinstance(versions, list) and len(versions) <= 10000
                and all(isinstance(item, dict) for item in versions), "VANILLA_METADATA_INVALID")
        selected = [item for item in versions if item.get("id") == "1.19.2"]
        require(len(selected) == 1, "VANILLA_RELEASE_MISMATCH")
        entry = selected[0]
        sha = entry.get("sha1")
        require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha)
                and entry.get("type") == "release"
                and entry.get("url") == f"https://piston-meta.mojang.com/v1/packages/{sha}/1.19.2.json",
                "VANILLA_RELEASE_MISMATCH")
        require(hashlib.sha1(version_raw).hexdigest() == sha, "VANILLA_METADATA_HASH_MISMATCH")
        require(version.get("id") == "1.19.2" and version.get("type") == "release"
                and version.get("javaVersion", {}).get("majorVersion") == 17, "VANILLA_RELEASE_MISMATCH")
        downloads = version.get("downloads")
        require(isinstance(downloads, dict), "VANILLA_METADATA_INVALID")
        selected_downloads = {}
        for role in ("client", "server"):
            item = downloads.get(role)
            require(isinstance(item, dict), "VANILLA_METADATA_INVALID")
            sha, size = item.get("sha1"), item.get("size")
            require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha)
                    and type(size) is int and 0 < size <= 512 * 1024**2
                    and item.get("url") == f"https://piston-data.mojang.com/v1/objects/{sha}/{role}.jar",
                    "VANILLA_DISTRIBUTION_SOURCE")
            selected_downloads[role] = {"sha1": sha, "bytes": size, "url": item["url"]}
        return {"policy": POLICY, "manifest_url": MANIFEST_URL, "version_url": entry["url"],
                "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
                "version_sha256": hashlib.sha256(version_raw).hexdigest(), "downloads": selected_downloads}
    except (TypeError, ValueError, AttributeError) as error:
        if isinstance(error, Fault):
            raise
        raise Fault("VANILLA_METADATA_INVALID") from None


def distribution(item, source):
    require(item.origin == source["url"] and item.file_id is None, "VANILLA_DISTRIBUTION_SOURCE")
    path = Path(item.path)
    require(path.is_absolute(), "UNSAFE_PATH")
    reject_links(path)
    require(path.is_file(), "AWAITING_ARTIFACT")
    require(path.stat().st_size == source["bytes"], "VANILLA_DISTRIBUTION_MISMATCH")
    sha1, sha256, total = hashlib.sha1(), hashlib.sha256(), 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024**2):
            total += len(chunk)
            require(total <= source["bytes"], "VANILLA_DISTRIBUTION_MISMATCH")
            sha1.update(chunk)
            sha256.update(chunk)
    require(total == source["bytes"] and sha1.hexdigest() == source["sha1"]
            and sha256.hexdigest() == item.sha256, "VANILLA_DISTRIBUTION_MISMATCH")
    return {"role": item.role, "bytes": total, "sha1": sha1.hexdigest(), "sha256": sha256.hexdigest(),
            "source_url": source["url"]}
