"""Private installed E9E launch preflight; never a gameplay policy.

The sealed profile contains no session credentials or source installation paths.
This resolver checks bytes without launching, leasing files, authenticating an
account, or qualifying custody/isolation. Execution still needs those consumers.
"""

import hashlib
import json
import os
from pathlib import Path
import re

from pydantic import Field

from .contracts import Digest, Strict
from .forge_client import ROLE_ROOT, VERSION, argument_template
from .inference_transport import strict_json
from .inventory import inventory_directories
from .pack_policies import reviewed_vendor_paths
from .pack_worker import validate_server_settings
from .provisioning import E9ELaunchProfile, FrozenE9ELaunchProfile, validate_launch_environment
from .runtime_data import AGENT_PATH, REMOTE_MODS, validate_snapshot
from .storage import reject_links, require, safe_relative

JAVA = "java/bin/java.exe"
WIN_ARGS = "libraries/net/minecraftforge/forge/1.19.2-43.4.23/win_args.txt"
WIN_ARGS_SHA256 = "083c60331e7cdd9c76f73a3131f86e1f8b5454fa1a531f59e2d9748c27923c30"
BRIDGE = "{strata.game_bridge}"
SERVER_ARGS = ["-XX:ActiveProcessorCount=4", "-Xms2G", "-Xmx5G", "@" + WIN_ARGS, "nogui"]
ROOT = Path(__file__).resolve().parents[2]


class ForgeClientInvocation(Strict):
    arguments_path: str
    arguments_sha256: Digest
    bridge_directory: str
    # Binds the expected authenticated body; these are private operator inputs.
    player_name: str = Field(pattern=r"^[A-Za-z0-9_]{1,16}$")
    player_uuid: str = Field(pattern=r"^[0-9a-f]{32}$")


def client_template(software, launcher_raw, vanilla_raw, *, server_port, frozen=False):
    return [*agent_arguments(frozen), "-Dstrata.gameBridgeDirectory=" + BRIDGE, "-Dstrata.awaitGameAuthority=true",
            *argument_template(software, launcher_raw, vanilla_raw, server_port=server_port)]


def agent_arguments(frozen):
    return ["-javaagent:" + str(Path(ROLE_ROOT) / AGENT_PATH)] if frozen else []


def validate_forge_profile(profile, inventory, read, *, java):
    """Bind both commands and the complete prepared client software to CAS bytes."""
    frozen = isinstance(profile, FrozenE9ELaunchProfile)
    profile = (FrozenE9ELaunchProfile if frozen else E9ELaunchProfile).model_validate(profile.model_dump())
    require(profile.client.executable == profile.server.executable == java, "FORGE_JAVA_PIN_MISMATCH")
    require(inventory.get("schema") in {"strata/InstalledInventory/1", "strata/InstalledInventory/2"}
            and inventory.get("is_example") is profile.is_example, "FORGE_PROFILE_MISMATCH")
    rows = inventory["files"]
    files = {(r["role"], r["path"]): r for r in rows}
    require(len(files) == len(rows), "FORGE_PROFILE_MISMATCH")
    require(("client", "mods/strata-forge1192-client-0.1.0.jar") in files, "FORGE_BRIDGE_MODULE_MISSING")

    def blob(ref):
        raw = read(ref)
        require("cas:sha256:" + hashlib.sha256(raw).hexdigest() == ref, "HASH_MISMATCH")
        return raw

    def installed(role, path):
        require((role, path) in files, "FORGE_PROFILE_MISMATCH")
        row = files[role, path]
        raw = blob("cas:sha256:" + row["digest"])
        require(len(raw) == row["bytes"], "HASH_MISMATCH")
        return raw

    if frozen:
        report_raw = blob(profile.runtime_data)
        for role in ("client", "server"):
            validate_snapshot(report_raw, installed(role, AGENT_PATH))
    else:
        require(not any(path in REMOTE_MODS for _, path in files), "FORGE_RUNTIME_DATA_UNPINNED")

    software = strict_json(blob(profile.client_software))
    require(software.get("is_example") is profile.is_example
            and isinstance(software.get("files"), list) and 0 < len(software["files"]) <= 21000,
            "FORGE_CLIENT_SOFTWARE_MISMATCH")
    seen = set()
    for row in software["files"]:
        path = safe_relative(row["path"])
        require(path.parts[0] in {"assets", "java", "libraries", "versions"}
                and row["path"].casefold() not in seen, "FORGE_CLIENT_SOFTWARE_MISMATCH")
        seen.add(row["path"].casefold())
        entry = files.get(("client", row["path"]))
        require(entry is not None and all(entry[k] == row[k] for k in ("digest", "bytes")),
                "FORGE_RUNTIME_INVENTORY_MISMATCH")
    directories = inventory_directories(inventory, reviewed_world_paths=reviewed_vendor_paths("e9e"))
    require("natives" in directories["client"], "FORGE_CLIENT_NATIVES")
    expected = client_template(software, installed("client", f"versions/{VERSION}/{VERSION}.json"),
        installed("client", "versions/1.19.2/1.19.2.json"), server_port=profile.port, frozen=frozen)
    require(profile.client.arguments == expected and profile.server.arguments == [*agent_arguments(frozen), *SERVER_ARGS],
            "FORGE_LAUNCH_COMMAND_MISMATCH")
    for role in ("client", "server"):
        command = getattr(profile, role)
        require(command.executable_path == JAVA and command.working_directory == "."
                and (role, JAVA) in files and files[role, JAVA]["digest"] == command.executable.digest,
                "FORGE_LAUNCH_COMMAND_MISMATCH")
        # No inherited launcher Java/PATH and no permanent per-run temp paths.
        require(set(command.environment) <= {"SystemRoot", "WINDIR", "LANG", "TZ"},
                "ENVIRONMENT_NOT_ALLOWED")
        validate_launch_environment(command.environment)
    require(hashlib.sha256(installed("server", WIN_ARGS)).hexdigest() == WIN_ARGS_SHA256,
            "FORGE_SERVER_ARGUMENTS_MISMATCH")
    validate_server_settings(installed("server", "server.properties"), profile)
    return expected


def _path(value):
    path = Path(value)
    require(path.is_absolute() and path == Path(os.path.abspath(path))
            and not any(c in value for c in '\r\n\x00;${}')
            and all(":" not in p and not p.endswith((" ", ".")) for p in path.parts[1:]),
            "FORGE_LAUNCH_PATH")
    reject_links(path)
    return path  # Keep normal Windows paths, never extended paths in JVM properties.


def _apart(first, second):
    require(not first.is_relative_to(second) and not second.is_relative_to(first), "FORGE_LAUNCH_OVERLAP")


def resolved_template(profile, root, bridge):
    root, bridge = _path(str(root)), _path(str(bridge))
    return [arg.replace(ROLE_ROOT, str(root)).replace(BRIDGE, str(bridge)) for arg in profile.client.arguments]


def encode_arguments(arguments):
    """Exact Java argfile quoting used by the protected session preparer."""
    require(all(not any(c in arg for c in '\r\n\x00') for arg in arguments), "FORGE_SESSION_ARGUMENTS")
    return ("\n".join('"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"' for a in arguments) + "\n").encode("utf-8")


def resolve_forge_invocation(profile, value, binding, command):
    require(value is not None, "FORGE_INVOCATION_REQUIRED")
    invocation = ForgeClientInvocation.model_validate(value)
    arguments, bridge = _path(invocation.arguments_path), _path(invocation.bridge_directory)
    instance = _path(binding.instance)
    require(arguments.is_file() and arguments.stat().st_nlink == 1
            and arguments.stat().st_size <= 65536 and bridge.is_dir() and not any(bridge.iterdir()),
            "FORGE_INVOCATION_NOT_FRESH")
    for first in (arguments, bridge):
        for second in (_path(binding.store), instance, _path(str(ROOT))):
            _apart(first, second)
    _apart(arguments, bridge)
    raw = arguments.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == invocation.arguments_sha256, "HASH_MISMATCH")
    # Accept only the canonical quoted format, then compare every non-auth byte.
    # Errors never contain actual argument values (especially the access token).
    try:
        actual = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    except (UnicodeError, ValueError):
        actual = []
    require(actual and all(isinstance(a, str) for a in actual), "FORGE_SESSION_ARGUMENTS")
    require(encode_arguments(actual) == raw, "FORGE_SESSION_ARGUMENTS")
    expected = resolved_template(profile, instance / "client", bridge)
    require(len(expected) == len(actual), "FORGE_SESSION_ARGUMENTS")
    substitutions = {"${auth_player_name}": invocation.player_name, "${auth_uuid}": invocation.player_uuid}
    for want, got in zip(expected, actual, strict=True):
        if want == "${auth_access_token}":
            require(re.fullmatch(r"[A-Za-z0-9_.=-]{16,16384}", got) is not None, "FORGE_SESSION_ARGUMENTS")
        else:
            require(got == substitutions.get(want, want), "FORGE_SESSION_ARGUMENTS")
    return {"schema": "strata/ResolvedPackLaunch/3",
            "launch": command.model_dump() | {"arguments": ["@" + str(arguments)]},
            "session_arguments_sha256": invocation.arguments_sha256,
            "bridge_directory": str(bridge), "backend": profile.backend,
            "update_policy": profile.update_policy, "session_authentication_qualified": False}
