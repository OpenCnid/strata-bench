"""Operator-only E9E 1.27.0 setup and effective-file inspection.

These are file observations, not proof of loaded recipes, quests, gameplay or a
cold restart. No game command, script, world or configuration is executed/changed.
"""

import hashlib
import json
import stat
import tomllib
from pathlib import Path
from typing import Literal

from .inventory import scan_tree
from .storage import Fault, digest, reject_links, require, safe_relative

# Actual official distributions, including the resolved ConfigSwapper JAR.
# Full acquisition/provenance remains the PackProvider's separate responsibility.
E9E_MODE_FILES = {
    "mods/configswapper-3.2.jar":
        "e75051943a4264b94695f22a437ba51b54b74916f75299dfe4223eb0d8209d35",
    "config/configswapper.json":
        "05ef797a7721d835137a972191f6d8173ca51ba9d61b0d7ede282aaac477eec2",
    "kubejs/startup_scripts/packmode.js":
        "b16e6614e33f926b725a0b1860f2c96c13d1fafe3f1c47e729dcadd422ca5cdb",
    "kubejs/server_scripts/packmode.js":
        "5d572b01c281e6d02d048d26db210473421845d6b516f7ec0a159c8ccbb6083b",
    "kubejs/server_scripts/expert/recipes/minecraft/shaped.js":
        "c3632f129ffae78a9caa78ad85e95001b5ac8f1e7de6dde6835c843803cf0a7e",
    "config/ftbquests/quests/chapters/hidden_quests.snbt":
        "0d91ad4826e1142de8c6fc6f690277c065f944147b107d11fa927aa55af2b603",
}
E9E_OVERLAY_DIGEST = "aec96aed5745b8681f8e12d8e1e85ce60ddee39e417fbda5e95d30aa655b538b"
OVERLAY = "config/configswapper/expert"
MAX_FILE_BYTES = 8 * 1024**2


def _read(root: Path, relative: str) -> bytes:
    path = root.joinpath(*safe_relative(relative).parts)
    reject_links(path)
    require(path.is_file(), "AWAITING_ARTIFACT")
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "UNSAFE_PATH")
    require(before.st_size <= MAX_FILE_BYTES, "ARTIFACT_QUOTA")
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    require(len(data) <= MAX_FILE_BYTES, "ARTIFACT_QUOTA")
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), "SOURCE_CHANGED")
    return data


def _json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "MODE_CONFIG_INVALID")
            result[key] = value
        return result
    try:
        result = json.loads(data, object_pairs_hook=unique)
    except (ValueError, UnicodeError):
        raise Fault("MODE_CONFIG_INVALID") from None
    require(isinstance(result, dict), "MODE_CONFIG_INVALID")
    return result


def _differences(expected, actual, keys=()):
    """Compare overlay leaves only. Extra ordinary config keys are legitimate.

    Key paths are arrays, so a quoted TOML key containing '.' stays unambiguous.
    Type equality matters: Python otherwise considers True == 1 == 1.0.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [list(keys)]
        return [path for key, value in expected.items()
                for path in _differences(value, actual.get(key), (*keys, key))]
    if type(expected) is not type(actual):
        return [list(keys)]
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [list(keys)]
        return [path for i, (left, right) in enumerate(zip(expected, actual))
                for path in _differences(left, right, (*keys, str(i)))]
    return [] if expected == actual else [list(keys)]


def inspect_e9e_mode(root: Path, role: Literal["client", "server"], *,
                     effective=False, world: str | None = None):
    """Inspect an operator-owned stopped installation; never certify live state.

    Effective inspection requires the exact world directory selected by the
    operator. Missing target files remain unresolved (including client-only
    configs on a dedicated server); no guessed exclusions produce a pass.
    """
    require(root.is_absolute() and root.is_dir(), "UNSAFE_PATH")
    reject_links(root)
    require(role in {"client", "server"}, "CONFIG_INVALID")
    require(not effective or world is not None, "WORLD_PATH_REQUIRED")
    if world is not None:
        safe_relative(world)
        reject_links(root.joinpath(*safe_relative(world).parts))
    checks = []

    def check(name, operation):
        try:
            details = operation()
            checks.append({"check": name, "result": "pass", **details})
        except Fault as error:
            checks.append({"check": name, "result": "fail", "code": error.code})

    def pinned(path, sha):
        actual = hashlib.sha256(_read(root, path)).hexdigest()
        require(actual == sha, "RELEASE_MISMATCH")
        return {"path": path, "sha256": actual}

    for path, sha in E9E_MODE_FILES.items():
        check(path, lambda path=path, sha=sha: pinned(path, sha))

    entries = []

    def overlays():
        entries.extend(scan_tree(root / OVERLAY, max_files=1000, max_bytes=16 * 1024**2))
        actual = digest(entries)
        require(actual == E9E_OVERLAY_DIGEST, "RELEASE_MISMATCH")
        return {"files": len(entries), "digest": actual}

    check("expert_overlay_inventory", overlays)

    def selection():
        require(_json(_read(root, "config/configswapper.json")).get("defaultmode") == "expert",
                "MODE_MISMATCH")
        mode_path = root / "mode.json"
        reject_links(mode_path)
        if not mode_path.exists():
            require(not effective, "MODE_NOT_INITIALIZED")
            return {"mode": None, "default_mode": "expert", "initialized": False}
        require(_json(_read(root, "mode.json")).get("mode") == "expert", "MODE_MISMATCH")
        return {"mode": "expert", "default_mode": "expert", "initialized": True}

    check("mode_selection", selection)
    overlays_verified = all(item["result"] == "pass" for item in checks)
    if effective and overlays_verified:
        for entry in entries:
            relative = entry["path"]
            first = safe_relative(relative).parts[0]
            require(first in {"config", "serverconfig"}, "MODE_OVERLAY_UNSUPPORTED")
            target = f"{world}/{relative}" if first == "serverconfig" else relative

            def compare(entry=entry, target=target):
                source = _read(root, f"{OVERLAY}/{entry['path']}")
                require(hashlib.sha256(source).hexdigest() == entry["digest"], "SOURCE_CHANGED")
                actual = _read(root, target)
                if target.endswith(".toml"):
                    try:
                        wanted = tomllib.loads(source.decode("utf-8"))
                        observed = tomllib.loads(actual.decode("utf-8"))
                    except (ValueError, UnicodeError):
                        raise Fault("MODE_CONFIG_INVALID") from None
                    require(not _differences(wanted, observed), "MODE_OVERLAY_MISMATCH")
                else:
                    # ConfigSwapper 3.2 replaces non-TOML files byte-for-byte.
                    require(source == actual, "MODE_OVERLAY_MISMATCH")
                return {"path": target, "sha256": hashlib.sha256(actual).hexdigest()}

            check(f"effective:{relative}", compare)
    file_result = "pass" if all(item["result"] == "pass" for item in checks) else "fail"
    return {
        "schema": "strata/E9EModeInspection/1", "target": "e9e", "release": "1.27.0",
        "role": role, "scope": "effective_files" if effective else "setup_files",
        "root": str(root), "world": world, "file_result": file_result, "checks": checks,
        "loaded_runtime_verified": False, "gate_result": "not_run", "compatibility_claim": None,
        "required_runtime_checks": [
            "prebaseline_expert_initialization", "cold_restart", "loaded_expert_configuration",
            "expert_furnace_recipe", "expert_quest_and_team_state", "independent_player_reference",
        ],
    }
