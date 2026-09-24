"""Synthetic archives test preparation failures; no installer or game executes."""

import hashlib
import io
import json
import os
import zipfile

import pytest
from typer.testing import CliRunner

from mcbench import forge_runtime as forge
from mcbench.cli import app
from mcbench.storage import Fault


def jar(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, raw in entries.items():
            archive.writestr(name, raw)
    return output.getvalue()


def sha(raw, algorithm="sha256"):
    return hashlib.new(algorithm, raw).hexdigest()


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    mcp = jar({"config.json": json.dumps({"data": {"mappings": "config/joined.tsrg"}}),
               "config/joined.tsrg": b"mapping"})
    library = b"synthetic library"
    libpath = "example/runtime/1/runtime-1.jar"
    payload = b"synthetic server"
    bundle = jar({
        "META-INF/libraries.list": f"{sha(library)}\texample:runtime:1\t{libpath}\n",
        "META-INF/libraries/" + libpath: library,
        "META-INF/versions.list": f"{sha(payload)}\t1.19.2\t1.19.2/server-1.19.2.jar\n",
        "META-INF/versions/1.19.2/server-1.19.2.jar": payload,
    })
    mapping = b"mojang mapping"
    version = json.dumps({"id": "1.19.2", "type": "release", "javaVersion": {"majorVersion": 17},
                         "downloads": {key: {"sha1": sha(raw, "sha1"), "size": len(raw),
                             "url": f"https://piston-data.mojang.com/v1/objects/{sha(raw, 'sha1')}/{name}"}
                         for key, raw, name in (("client", b"client", "client.jar"),
                                                ("server", bundle, "server.jar"),
                                                ("server_mappings", mapping, "server.txt"))}}).encode()
    manifest = json.dumps({"versions": [{"id": "1.19.2", "type": "release", "sha1": sha(version, "sha1"),
                            "url": f"https://piston-meta.mojang.com/v1/packages/{sha(version, 'sha1')}/1.19.2.json"}]}).encode()
    entries = []
    for coordinate, path, raw in ((f"de.oceanlabs.mcp:mcp_config:{forge.MC}@zip", forge.MCP + ".zip", mcp),
                                  ("example:runtime:1", libpath, library)):
        entries.append({"name": coordinate, "downloads": {"artifact": {
            "path": path, "url": "https://example.invalid/" + path,
            "sha1": sha(raw, "sha1"), "size": len(raw)}}})
    data = {}
    installed = {forge.MCP + ".zip": mcp, forge.MCP + "-mappings.txt": b"mapping",
                 libpath: library, forge.SERVER + "-mappings.txt": mapping,
                 forge.SERVER + "-unpacked.jar": payload,
                 "net/minecraft/server/1.19.2/server-1.19.2.jar": bundle}
    for variable, coordinate in (("MC_SLIM", f"net.minecraft:server:{forge.MC}:slim"),
                                 ("MC_EXTRA", f"net.minecraft:server:{forge.MC}:extra"),
                                 ("PATCHED", f"net.minecraftforge:forge:{forge.FORGE}:server")):
        raw = variable.encode()
        data[variable] = {"server": f"[{coordinate}]"}
        data[variable + "_SHA"] = {"server": f"'{sha(raw, 'sha1')}'"}
        installed[forge._coordinate(coordinate)] = raw
    profile = {"spec": 1, "minecraft": "1.19.2", "version": "1.19.2-forge-43.4.23",
               "libraries": entries, "data": data}
    forge_version = {"id": profile["version"], "inheritsFrom": "1.19.2", "libraries": entries[:1]}
    installer_entries = {"install_profile.json": json.dumps(profile), "version.json": json.dumps(forge_version)}
    for name in ("win_args.txt", "unix_args.txt"):
        installer_entries["data/" + name] = b"synthetic launch arguments"
        installed[f"{forge.FORGE_DIR}/{name}"] = installer_entries["data/" + name]
    installer = jar(installer_entries)
    monkeypatch.setattr(forge, "INSTALLER_SHA256", sha(installer))
    installed.update({path: b"unqualified intermediate" for path in forge.EXCLUSIONS})
    root = tmp_path / "source"
    for path, raw in installed.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return {"installer": installer, "bundle": bundle, "manifest_raw": manifest, "version_raw": version,
            "root": root, "destination": tmp_path / "output"}


def test_prepares_exact_bytes_retains_all_origins_and_exclusions(prepared):
    result = forge.prepare_server_libraries(**prepared)
    assert len(result["files"]) == 11 and len(result["source_dispositions"]) == 4
    assert not result["installer_executed"] and not result["complete_role_qualified"]
    assert not result["license_review_complete"] and result["game_conformance_claim"] is None
    for row in result["files"]:
        assert (prepared["destination"] / row["path"]).read_bytes() == (prepared["root"] / row["path"]).read_bytes()
        assert row["license_review"] == "pending"
    for row in result["source_dispositions"]:
        assert row["provenance_qualified"] is False and row["copied"] is False
        assert not (prepared["destination"] / row["path"]).exists()
    lib = next(x for x in result["files"] if x["path"].startswith("example/"))
    assert {x["kind"] for x in lib["origins"]} == {"publisher_library", "archive_member"}
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        forge.prepare_server_libraries(**prepared)


@pytest.mark.parametrize("field", ["installer", "bundle", "version_raw"])
def test_rejects_changed_publisher_inputs(prepared, field):
    prepared[field] += b" "
    with pytest.raises(Fault):
        forge.prepare_server_libraries(**prepared)
    assert not prepared["destination"].exists()


@pytest.mark.parametrize("path", [forge.MCP + ".zip", forge.MCP + "-mappings.txt",
    forge.SERVER + "-mappings.txt", forge.SERVER + "-extra.jar", forge.SERVER + "-unpacked.jar",
    f"{forge.FORGE_DIR}/forge-{forge.FORGE}-server.jar", f"{forge.FORGE_DIR}/win_args.txt"])
def test_rejects_changed_installed_bytes_before_copy(prepared, path):
    (prepared["root"] / path).write_bytes(b"modified")
    with pytest.raises(Fault, match="FORGE_FILE_MISMATCH"):
        forge.prepare_server_libraries(**prepared)
    assert not prepared["destination"].exists()


@pytest.mark.parametrize("mutation", ["extra", "missing", "hardlink", "private"])
def test_rejects_incomplete_unsafe_source_trees(prepared, mutation):
    root = prepared["root"]
    if mutation == "missing":
        (root / (forge.SERVER + "-srg.jar")).unlink()
    elif mutation == "hardlink":
        os.link(root / (forge.SERVER + "-srg.jar"), root / "linked")
    else:
        (root / ("auth.json" if mutation == "private" else "surprise.jar")).write_bytes(b"unexpected")
    with pytest.raises(Fault):
        forge.prepare_server_libraries(**prepared)
    assert not prepared["destination"].exists()


def test_rejects_destination_inside_source(prepared):
    prepared["destination"] = prepared["root"] / "child"
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        forge.prepare_server_libraries(**prepared)


def test_changed_source_during_copy_retains_failed_destination(prepared, monkeypatch):
    original = forge.read_input
    def changed(path, limit):
        raw = original(path, limit)
        return raw + b"changed" if prepared["destination"].exists() else raw
    monkeypatch.setattr(forge, "read_input", changed)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        forge.prepare_server_libraries(**prepared)
    assert prepared["destination"].exists()
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        forge.prepare_server_libraries(**prepared)


def test_cli_connects_preparation_without_database_or_game(prepared, tmp_path):
    paths = []
    for name in ("installer", "bundle", "manifest_raw", "version_raw"):
        path = tmp_path / name
        path.write_bytes(prepared[name])
        paths.append(str(path))
    result = CliRunner().invoke(app, ["pack", "prepare-forge-server-libraries", *paths,
                                    str(prepared["root"]), str(prepared["destination"])])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["schema"] == "strata/ForgeServerLibraries/1"
    blocked = CliRunner().invoke(app, ["pack", "prepare-forge-server-libraries", *paths,
                                     str(prepared["root"]), str(prepared["destination"])])
    assert blocked.exit_code == 2 and json.loads(blocked.output)["code"] == "DESTINATION_EXISTS"
