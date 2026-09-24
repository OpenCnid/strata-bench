"""Synthetic role bytes/auth canaries; actual CAS seal/materialize/resolve flow."""

import hashlib
import json
from pathlib import Path
import shutil

import pytest
from pydantic import ValidationError

from mcbench import forge_client as client, pack_forge as forge
from mcbench.inventory import scan_layout
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.provisioning import E9ELaunchProfile, FrozenE9ELaunchProfile, parse_launch_profile
from mcbench.records import FileEntry, Pin
from mcbench.storage import CAS, Database, Fault, canonical
from test_forge_client import inputs  # noqa: F401 -- shared synthetic software fixture
from test_provisioning import prepare_fixture, seal
from test_pack_launch import rows

PROPERTIES = ("server-ip=127.0.0.1\nserver-port=25604\nonline-mode=true\n"
              "enable-rcon=false\nrcon.password=\nenable-command-block=false\n")
TOKEN = "SYNTHETIC-SESSION-SECRET-CANARY"


@pytest.fixture
def candidate(inputs, tmp_path, monkeypatch):  # noqa: F811 -- imported pytest fixture
    store = tmp_path / "store"
    db = Database(store / "controller.sqlite")
    prepared = prepare_fixture(db, CAS(db, store / "objects"), tmp_path)
    service, receipt, roles, original, evidence = prepared
    software = client.prepare_client(**inputs) | {"is_example": True}
    shutil.copytree(inputs["destination"], roles[0].root, dirs_exist_ok=True)
    (Path(roles[0].root) / "natives").mkdir()
    (Path(roles[0].root) / "mods/strata-forge1192-client-0.1.0.jar").write_bytes(b"synthetic module")
    server = Path(roles[1].root)
    (server / "java/bin").mkdir(parents=True)
    (server / forge.JAVA).write_bytes((Path(roles[0].root) / forge.JAVA).read_bytes())
    win = server / forge.WIN_ARGS
    win.parent.mkdir(parents=True)
    win.write_bytes(b"synthetic installed Forge arguments")
    monkeypatch.setattr(forge, "WIN_ARGS_SHA256", hashlib.sha256(win.read_bytes()).hexdigest())
    (server / "server.properties").write_text(PROPERTIES)
    for role in roles:
        layout = scan_layout(Path(role.root))
        role.files = [FileEntry.model_validate(r | {"role": role.role, "origin": "synthetic",
            "license_ref": "synthetic", "layer": "resolved", "project_id": None, "file_id": None})
            for r in layout["files"]]
        role.extra_directories = layout["directories"]
    command = original.client.model_dump() | {"executable_path": forge.JAVA,
        "executable": {"version": "synthetic-17", "digest": hashlib.sha256(
            (server / forge.JAVA).read_bytes()).hexdigest()}}
    receipt.java = Pin.model_validate(command["executable"])
    profile = E9ELaunchProfile.model_validate({"schema": "strata/LaunchProfile/3", "is_example": True,
        "client": command | {"arguments": forge.client_template(software, inputs["launcher_raw"],
            inputs["version_raw"], server_port=25604)},
        "server": command | {"arguments": forge.SERVER_ARGS}, "client_software": service._put("pack1", software),
        "backend": "forge_client", "host": "127.0.0.1", "port": 25604,
        "update_policy": "sealed-local-bytes/no-installer/1"})
    yield service, receipt, roles, profile, evidence
    db.close()


def invocation(profile, binding, tmp_path, suffix="one"):
    bridge = tmp_path / ("bridge-" + suffix)
    bridge.mkdir()
    args = forge.resolved_template(profile, Path(binding.instance) / "client", bridge)
    substitutions = {"${auth_player_name}": "TestPlayer", "${auth_uuid}": "1" * 32,
                     "${auth_access_token}": TOKEN}
    args = [substitutions.get(a, a) for a in args]
    path = tmp_path / ("session-" + suffix + ".txt")
    path.write_bytes(forge.encode_arguments(args))
    return {"arguments_path": str(path), "arguments_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bridge_directory": str(bridge), "player_name": "TestPlayer", "player_uuid": "1" * 32}


@pytest.fixture
def pack(candidate, tmp_path):
    service, _, _, profile, _ = candidate
    lock, _ = seal(candidate)
    instance = tmp_path / "instance-one"
    service.materialize("pack1", instance)
    binding = PackLaunchBinding(store=str(service.cas.root.parent), request_id="pack1", lock=lock,
                                instance=str(instance))
    return binding, invocation(profile, binding, tmp_path), profile, candidate


def test_full_seal_materialize_resolve_relocates_every_path_without_credentials(pack, tmp_path):
    binding, call, profile, candidate = pack
    service = candidate[0]
    before = rows(service)
    result = resolve_pack_launch(binding, "client", simulation=True, forge_invocation=call)
    server = resolve_pack_launch(binding, "server", simulation=True)
    assert server["launch"]["arguments"] == forge.SERVER_ARGS
    assert result["launch"]["arguments"] == ["@" + call["arguments_path"]]
    assert result["launch"]["executable_path"] == str(Path(binding.instance) / "client" / forge.JAVA)
    assert server["launch"]["executable_path"] == str(Path(binding.instance) / "server" / forge.JAVA)
    assert result["backend"] == "forge_client" and result["schema"] == "strata/ResolvedPackLaunch/3"
    assert not result["session_authentication_qualified"] and not result["campaign_admission"]
    assert not result["writer_custody_qualified"]
    assert TOKEN not in json.dumps(result) and TOKEN not in json.dumps(profile.model_dump())
    assert isinstance(parse_launch_profile(profile.model_dump()), E9ELaunchProfile)
    assert rows(service) == before
    other = tmp_path / "instance-two"
    service.materialize("pack1", other)
    second = binding.model_copy(update={"instance": str(other)})
    with pytest.raises(Fault, match="FORGE_SESSION_ARGUMENTS"):
        resolve_pack_launch(second, "client", simulation=True, forge_invocation=call)
    next_call = invocation(profile, second, tmp_path, "two")
    next_result = resolve_pack_launch(second, "client", simulation=True, forge_invocation=next_call)
    assert next_result["lock"] == result["lock"]
    assert next_result["session_arguments_sha256"] != result["session_arguments_sha256"]


@pytest.mark.parametrize("change", ["extra_arg", "old_java", "java_pin", "cwd", "classpath", "server_args",
                                   "port", "software", "environment", "win_args", "settings", "bridge_module",
                                   "java_version"])
def test_profile_drift_refuses_seal(candidate, change):
    service, _, roles, profile, _ = candidate
    if change == "extra_arg":
        profile.client.arguments.append("--unreviewed")
    elif change == "old_java":
        profile.client.executable_path = str(Path(roles[0].root) / forge.JAVA)
    elif change == "java_pin":
        profile.server.executable.digest = "a" * 64
    elif change == "java_version":
        profile.client.executable.version = "incorrect version for matching bytes"
    elif change == "cwd":
        profile.client.working_directory = "versions"
    elif change == "classpath":
        profile.client.arguments[profile.client.arguments.index("-cp") + 1] += ";old/source.jar"
    elif change == "server_args":
        profile.server.arguments = ["-jar", "ServerStarter.jar"]
    elif change == "port":
        profile.port += 1
    elif change == "software":
        software = service._json("pack1", profile.client_software)
        software["files"][0]["digest"] = "a" * 64
        profile.client_software = service._put("pack1", software)
    elif change == "environment":
        profile.client.environment = {"PATH": "old-launcher"}
    elif change == "bridge_module":
        path = "mods/strata-forge1192-client-0.1.0.jar"
        (Path(roles[0].root) / path).unlink()
        roles[0].files = [r for r in roles[0].files if r.path != path]
    else:
        name = forge.WIN_ARGS if change == "win_args" else "server.properties"
        path = Path(roles[1].root) / name
        path.write_bytes(b"unreviewed bytes")
        row = next(r for r in roles[1].files if r.path == name)
        row.digest, row.bytes = hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size
    with pytest.raises(Fault):
        seal(candidate)
    assert service.status("pack1")["state"] == "VERIFIED"


def test_new_profile_does_not_bypass_thirteen_evidence_bound_checks(candidate):
    service = candidate[0]
    _, proof = seal(candidate)
    # Retain the valid identity but remove exactly one required expert outcome.
    del proof.checks["expert_recipe"]
    with pytest.raises(Fault, match="PROVISIONING_UNVERIFIED"):
        service.seal_template("pack1", candidate[3], proof)


@pytest.mark.parametrize("change", [None, "missing_agent", "changed_snapshot", "legacy"])
def test_frozen_data_profile_joins_both_installed_roles_before_seal_and_resolve(candidate, tmp_path, change):
    from mcbench.runtime_data import AGENT_PATH, REMOTE_MODS, SOURCES, prepare_runtime_data
    from test_runtime_data import jdk
    service, receipt, roles, original, evidence = candidate
    snapshots = []
    for name, (repo, relative) in SOURCES.items():
        path = tmp_path / name
        path.write_bytes(b"synthetic snapshot\n")
        snapshots.append({"name": name, "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "commit": "a" * 40, "url": f"https://raw.githubusercontent.com/{repo}/{'a' * 40}/{relative}"})
    report = prepare_runtime_data(snapshots, jdk(), tmp_path / "agent-build")
    if change == "changed_snapshot":
        report["inputs"][0]["sha256"] = "b" * 64
    profile = FrozenE9ELaunchProfile.model_validate(original.model_dump() | {
        "schema": "strata/LaunchProfile/4", "runtime_data": service._put("pack1", report)})
    for role in roles:
        root = Path(role.root)
        (root / "harness").mkdir()
        if change != "missing_agent" or role.role != "client":
            shutil.copyfile(tmp_path / "agent-build/strata-runtime-data-0.1.0.jar", root / AGENT_PATH)
        for name in REMOTE_MODS:
            (root / name).write_bytes(b"synthetic mod with runtime inputs")
        layout = scan_layout(root)
        role.files = [FileEntry.model_validate(r | {"role": role.role, "origin": "synthetic",
            "license_ref": "synthetic", "layer": "resolved", "project_id": None, "file_id": None})
            for r in layout["files"]]
        role.extra_directories = layout["directories"]
        command = getattr(profile, role.role)
        command.arguments = [*forge.agent_arguments(True), *command.arguments]
    if change == "legacy":
        profile = original
    fixture = service, receipt, roles, profile, evidence
    if change:
        with pytest.raises(Fault):
            seal(fixture)
        assert service.status("pack1")["state"] == "VERIFIED"
        return
    lock, _ = seal(fixture)
    instance = tmp_path / "frozen-instance"
    service.materialize("pack1", instance)
    binding = PackLaunchBinding(store=str(service.cas.root.parent), request_id="pack1", lock=lock, instance=str(instance))
    call = invocation(profile, binding, tmp_path, "frozen")
    resolved = resolve_pack_launch(binding, "client", simulation=True, forge_invocation=call)
    server = resolve_pack_launch(binding, "server", simulation=True)
    assert server["launch"]["arguments"][0] == "-javaagent:" + str(instance / "server" / AGENT_PATH)
    assert str(instance / "client" / AGENT_PATH).replace("\\", "\\\\").encode() in Path(call["arguments_path"]).read_bytes()
    assert resolved["lock"] == lock and isinstance(parse_launch_profile(profile.model_dump()), FrozenE9ELaunchProfile)
    assert TOKEN.encode() not in canonical(resolved)


@pytest.mark.parametrize("change", ["missing", "server_role", "worker", "bridge_occupied", "bridge_inside",
    "arguments_inside", "hash", "extra_arg", "body", "bad_token", "control", "unquoted", "hardlink", "drift"])
def test_invocation_errors_do_not_start_or_write_and_never_disclose_token(pack, change, tmp_path):
    binding, call, _, candidate = pack
    role = "client"
    kwargs = {}
    if change == "missing":
        call = None
    elif change == "server_role":
        role = "server"
    elif change == "worker":
        kwargs["worker_invocation"] = {}
    elif change == "bridge_occupied":
        (Path(call["bridge_directory"]) / "old-connection").write_text("prior session")
    elif change == "bridge_inside":
        call["bridge_directory"] = str(Path(binding.instance) / "client/natives")
    elif change == "arguments_inside":
        call["arguments_path"] = str(Path(binding.instance) / "client/versions/1.19.2/1.19.2.json")
    elif change == "hash":
        call["arguments_sha256"] = "a" * 64
    elif change == "hardlink":
        (tmp_path / "shared-session").hardlink_to(call["arguments_path"])
    elif change == "drift":
        (Path(binding.instance) / "server" / forge.JAVA).write_bytes(b"changed")
    else:
        path = Path(call["arguments_path"])
        args = [json.loads(line) for line in path.read_text().splitlines()]
        if change == "extra_arg":
            args.append("--unreviewed")
        elif change == "body":
            args[args.index("--uuid") + 1] = "2" * 32
        elif change == "bad_token":
            args[args.index("--accessToken") + 1] = "-javaagent:evil.jar"
        if change == "control":
            raw = path.read_bytes().replace(TOKEN.encode(), b"bad\\nvalue")
        elif change == "unquoted":
            raw = path.read_bytes() + b"extra\n"
        else:
            raw = forge.encode_arguments(args)
        path.write_bytes(raw)
        call["arguments_sha256"] = hashlib.sha256(raw).hexdigest()
    before = rows(candidate[0])
    with pytest.raises((Fault, ValidationError)) as exc:
        resolve_pack_launch(binding, role, simulation=True, forge_invocation=call, **kwargs)
    assert TOKEN not in str(exc.value)
    assert rows(candidate[0]) == before
