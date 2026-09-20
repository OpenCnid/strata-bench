"""Install the selected Dovetail commit with the actual pinned native CLI.

The upstream marketplace pins its own repository independently from plugin source
refs. A tiny local marketplace pins the plugin source URL too; plugin source and
attribution remain unchanged. No inference, credentials, or user-profile mutations.
"""

import hashlib
import json
import os
import subprocess
import tomllib
from pathlib import Path

from .inventory import file_hash
from .runtime import CODEX_VERSION, DOVETAIL_COMMIT
from .storage import canonical, digest, reject_links, require, safe_relative

CODEX_BINARY_SHA256 = "960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc"
MARKETPLACE = "strata-pinned"
PLUGIN_ID = "dovetail-codex@" + MARKETPLACE
CORE_SKILLS = tuple("skills/" + name + "/SKILL.md" for name in (
    "better-skill-creator", "hypershot-protocol", "judge-composition", "prompt-engineering",
    "self-play", "spark-steering", "subagent-composition", "upsum"))
EXPLICIT_SKILLS = ("skills/spark-steering/SKILL.md", "skills/upsum/SKILL.md")


def _extended_path(path: Path):
    """Use Windows long-path I/O without changing manifest or Git-relative names."""
    path = path.absolute()
    value = str(path)
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


def isolated_environment(profile: Path):
    temporary = profile / "temp"
    temporary.mkdir(exist_ok=True)
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH") if key in os.environ}
    env.update(CODEX_HOME=str(profile), HOME=str(profile), USERPROFILE=str(profile),
               APPDATA=str(profile / "appdata"), LOCALAPPDATA=str(profile / "localappdata"),
               TMP=str(temporary), TEMP=str(temporary), GIT_CONFIG_COUNT="1",
               GIT_CONFIG_KEY_0="core.longpaths", GIT_CONFIG_VALUE_0="true")
    return env


def pinned_marketplace():
    return {"name": MARKETPLACE, "interface": {"displayName": "Strata pinned native dependencies"},
            "plugins": [{"name": "dovetail-codex", "source": {"source": "url",
                "url": "https://github.com/OpenCnid/dovetail-codex.git", "ref": DOVETAIL_COMMIT},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity"}]}


def discovery_policy(root: Path, inventory):
    """Pin discovery without modifying the selected upstream plugin source.

    Nested public test fixtures are not gameplay skills. This is catalog policy,
    not filesystem isolation: inaccessible fixture/source directories still need
    the separate OS boundary before gameplay admission.
    """
    require(inventory["source_commit"] == DOVETAIL_COMMIT and
            sorted(inventory["skills"]) == sorted(CORE_SKILLS), "PLUGIN_SKILL_INVENTORY_MISMATCH")
    excluded = sorted(e["path"] for e in inventory["files"] if e["path"].startswith("skills/")
                      and e["path"].endswith("/SKILL.md") and e["path"] not in CORE_SKILLS)
    return {"schema": "strata/NativeSkillDiscovery/1", "policy": "dovetail-top-level-eight/1",
            "core": list(CORE_SKILLS), "explicit_only": list(EXPLICIT_SKILLS),
            "excluded_nested": excluded, "config_overrides": {"skills.config": [
                {"path": str(root.joinpath(*safe_relative(p).parts)), "enabled": False}
                for p in excluded]}}


def inspect_plugin_tree(root: Path, *, git="git", expected_commit=DOVETAIL_COMMIT):
    root = root.absolute()
    reject_links(root)
    def run(*args, input_data=None):
        result = subprocess.run([git, "-c", "core.longpaths=true", "-C", str(root), *args],
                                input=input_data, capture_output=True, timeout=30, check=False)
        require(result.returncode == 0, "PLUGIN_GIT_INSPECTION_FAILED")
        return result.stdout
    commit = run("rev-parse", "HEAD").decode().strip()
    require(commit == expected_commit, "PLUGIN_REVISION_MISMATCH")
    require(not run("status", "--porcelain", "--untracked-files=all").strip(), "PLUGIN_TREE_MODIFIED")
    manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    require(manifest.get("name") == "dovetail-codex" and manifest.get("version") == "0.4.1"
            and manifest.get("skills") == "./skills/", "PLUGIN_MANIFEST_MISMATCH")
    records = [r for r in run("ls-tree", "-rz", "--full-tree", "HEAD").split(b"\x00") if r]
    require(len(records) <= 10000, "PLUGIN_INVENTORY_QUOTA")
    object_ids = sorted({r.split(b"\t", 1)[0].split()[2] for r in records})
    packed = run("cat-file", "--batch", input_data=b"\n".join(object_ids) + b"\n")
    require(len(packed) <= 256 * 1024**2, "PLUGIN_INVENTORY_QUOTA")
    blobs, cursor = {}, 0
    for expected in object_ids:
        end = packed.index(b"\n", cursor)
        oid, kind, size = packed[cursor:end].split()
        require(oid == expected and kind == b"blob", "PLUGIN_PATH_UNSUPPORTED")
        cursor = end + 1
        length = int(size)
        blobs[oid.decode()] = hashlib.sha256(packed[cursor:cursor + length]).hexdigest()
        cursor += length
        require(packed[cursor:cursor + 1] == b"\n", "PLUGIN_GIT_INSPECTION_FAILED")
        cursor += 1
    require(cursor == len(packed), "PLUGIN_GIT_INSPECTION_FAILED")
    entries = []
    for record in records:
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        require(kind == "blob" and mode in {"100644", "100755"}, "PLUGIN_PATH_UNSUPPORTED")
        relative = name.decode("utf-8")
        path = _extended_path(root.joinpath(*safe_relative(relative).parts))
        reject_links(path)
        data = path.read_bytes()
        # git status checks normalized content; hash both the installed bytes and
        # canonical git blob. Actual CRLF checkout bytes are a distinct runtime pin.
        entries.append({"path": relative, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "git_blob_sha256": blobs[oid], "mode": mode})
    require(bool(entries), "EMPTY_PLUGIN")
    skills = sorted(e["path"] for e in entries if e["path"].startswith("skills/") and
                    e["path"].count("/") == 2 and e["path"].endswith("/SKILL.md"))
    require(len(skills) == 8, "PLUGIN_SKILL_INVENTORY_MISMATCH")
    return {"schema": "strata/NativePluginInventory/1", "source_commit": commit,
            "manifest_digest": digest(manifest), "installed_tree_digest": digest(entries),
            "files": entries, "skills": skills, "native_invocation_verified": False}


def install_dovetail(binary: Path, profile: Path):
    binary, profile = binary.absolute(), profile.absolute()
    reject_links(binary)
    reject_links(profile)
    require(file_hash(binary) == CODEX_BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    require(not profile.exists() or not any(profile.iterdir()), "PROFILE_NOT_EMPTY")
    profile.mkdir(parents=True, exist_ok=True)
    env = isolated_environment(profile)
    version = subprocess.run([str(binary), "--version"], capture_output=True,
                             env=env, timeout=10, check=True).stdout.decode().strip()
    require(version == CODEX_VERSION, "RUNTIME_PIN_MISMATCH")
    source = profile / "pinned-marketplace"
    metadata = source / ".agents/plugins"
    metadata.mkdir(parents=True)
    (metadata / "marketplace.json").write_bytes(canonical(pinned_marketplace()))
    outputs = []
    for arguments in (["plugin", "marketplace", "add", str(source), "--json"],
                       ["plugin", "add", PLUGIN_ID, "--json"]):
        result = subprocess.run([str(binary), *arguments], cwd=profile, env=env,
                                capture_output=True, timeout=60)
        # Log these non-inference operations privately, including real failure.
        outputs.append({"operation": arguments[:3], "returncode": result.returncode,
                        "stdout": result.stdout.decode("utf-8", errors="replace"),
                        "stderr": result.stderr.decode("utf-8", errors="replace")})
        (profile / "installation-commands.json").write_bytes(canonical(outputs))
        require(result.returncode == 0, "PLUGIN_INSTALL_FAILED")
    installed = json.loads(outputs[-1]["stdout"])
    require(installed.get("pluginId") == PLUGIN_ID and installed.get("version") == "0.4.1",
            "PLUGIN_MANIFEST_MISMATCH")
    root = Path(installed["installedPath"])
    require(root.absolute().is_relative_to(profile), "PLUGIN_OUTSIDE_PROFILE")
    inventory = inspect_plugin_tree(root)
    discovery = discovery_policy(root, inventory)
    # The CLI records a canonical Windows extended path as marketplace identity.
    # Preserve that identity when --ignore-user-config requires explicit overrides.
    settings = tomllib.loads((profile / "config.toml").read_text(encoding="utf-8"))
    registered = settings.get("marketplaces", {}).get(MARKETPLACE, {})
    require(registered.get("source_type") == "local" and
            isinstance(registered.get("source"), str) and
            Path(registered["source"]).samefile(source), "PLUGIN_MARKETPLACE_MISMATCH")
    report = {"schema": "strata/NativePluginInstallation/1", "binary_digest": CODEX_BINARY_SHA256,
              "binary_version": version, "plugin_id": PLUGIN_ID,
              "marketplace_digest": digest(pinned_marketplace()), "inventory": inventory,
              "discovery_policy": discovery,
              "inference_started": False, "credential_imported": False,
              "required_config_overrides": {
                  "features.plugins": True,
                  f"plugins.{PLUGIN_ID}.enabled": True,
                  f"marketplaces.{MARKETPLACE}.source_type": "local",
                  f"marketplaces.{MARKETPLACE}.source": registered["source"],
                  **discovery["config_overrides"]}}
    (profile / "installation-report.json").write_bytes(canonical(report))
    return report
