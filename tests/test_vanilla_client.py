"""Synthetic acquired client/cache joins; not a rendered-client acceptance run."""

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mcbench.cli import app
from mcbench.inventory import scan_tree
from mcbench.storage import Database, Fault
from mcbench.vanilla_client import prepare_client
from test_vanilla_artifacts import inputs as inputs, sources
from test_vanilla_runtime import jar


@pytest.fixture
def database(tmp_path):
    database = Database(tmp_path / "controller.sqlite")
    yield database
    database.close()


def pin(raw, url):
    sha = hashlib.sha1(raw).hexdigest()
    return {"sha1": sha, "size": len(raw), "url": url.format(sha=sha)}


def encode(value):
    return (json.dumps(value, indent=2) + "\n").encode()


@pytest.fixture
def client(tmp_path):
    assets, libraries, second = [tmp_path / name for name in ("assets", "libraries", "second-libraries")]
    for root in (assets, libraries, second):
        root.mkdir()
    entries = []
    for name, classifier, os_name in (("base", None, None), ("native", "natives-windows", "windows"),
                                       ("native", "natives-macos", "osx")):
        suffix = "-" + classifier if classifier else ""
        relative = f"example/{name}/1/{name}-1{suffix}.jar"
        raw = jar({"example.class": b"synthetic", "META-INF/LICENSE": b"synthetic license"})
        artifact = pin(raw, "https://libraries.minecraft.net/" + relative) | {"path": relative}
        item = {"name": f"example:{name}:1" + (":" + classifier if classifier else ""),
                "downloads": {"artifact": artifact}}
        if os_name:
            item["rules"] = [{"action": "allow", "os": {"name": os_name}}]
        if os_name != "osx":
            path = (second if name == "native" else libraries) / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        entries.append(item)
    object_raw = b"synthetic asset"
    sha = hashlib.sha1(object_raw).hexdigest()
    path = assets / "objects" / sha[:2] / sha
    path.parent.mkdir(parents=True)
    path.write_bytes(object_raw)
    asset_objects = {"minecraft/example.ogg": {"hash": sha, "size": len(object_raw)},
                     "minecraft/alias.ogg": {"hash": sha, "size": len(object_raw)}}
    index_raw = encode({"objects": asset_objects})
    (assets / "indexes").mkdir()
    (assets / "indexes/1.19.json").write_bytes(index_raw)
    logging_raw = b"<Configuration/>"
    (assets / "log_configs").mkdir()
    (assets / "log_configs/client-1.12.xml").write_bytes(logging_raw)
    client_raw = jar({"client.class": b"synthetic client"})
    version = {"id": "1.19.2", "type": "release", "mainClass": "net.minecraft.client.main.Main",
               "javaVersion": {"component": "java-runtime-gamma", "majorVersion": 17},
               "libraries": entries, "assets": "1.19", "assetIndex":
               pin(index_raw, "https://piston-meta.mojang.com/v1/packages/{sha}/1.19.json") |
               {"id": "1.19", "totalSize": 2 * len(object_raw)},
               "downloads": {"client": pin(client_raw, "https://piston-data.mojang.com/v1/objects/{sha}/client.jar")},
               "logging": {"client": {"type": "log4j2-xml", "argument": "-Dlog4j.configurationFile=${path}",
                   "file": pin(logging_raw, "https://piston-data.mojang.com/v1/objects/{sha}/client-1.12.xml") |
                   {"id": "client-1.12.xml"}}}}
    return client_raw, version, assets, [libraries, second], tmp_path / "software"


def prepare(values):
    raw, version, assets, libraries, destination = values
    return prepare_client(raw, encode(version), assets, libraries, destination)


def test_exact_selected_software_classpath_assets_and_exclusions(client):
    raw, _, assets, libraries, destination = client
    (assets / "unrelated-launcher-file.json").write_bytes(b"must not be copied")
    (libraries[0] / "unrelated-other-version.jar").write_bytes(b"must not be copied")
    value = prepare(client)
    assert len(scan_tree(destination)) == len(value["files"]) == 7
    assert value["classpath"] == ["libraries/example/base/1/base-1.jar",
        "libraries/example/native/1/native-1-natives-windows.jar", "versions/1.19.2/1.19.2.jar"]
    assert len(value["excluded_libraries"]) == 1 and value["asset_names"] == 2 and value["unique_asset_objects"] == 1
    assert value["independent_software_copy_verified"] and not value["complete_role_qualified"]
    assert not value["license_review_complete"] and not value["launch_configuration_qualified"]
    assert value["game_conformance_claim"] is None
    assert (destination / "versions/1.19.2/1.19.2.jar").read_bytes() == raw
    assert all(Path(f["source_path"]).stat().st_nlink == 1 for f in value["files"] if "source_path" in f)
    (destination / value["classpath"][0]).write_bytes(b"independent copy changed")
    assert (libraries[0] / "example/base/1/base-1.jar").read_bytes() != b"independent copy changed"


@pytest.mark.parametrize("change", ["missing_library", "wrong_library", "bad_preferred_copy", "wrong_asset",
    "hardlinked_asset", "wrong_logging", "other_library_origin", "coordinate_mismatch", "duplicate_library",
    "unsupported_rule", "explicit_null_rule", "wrong_java", "wrong_main", "index_hash", "index_total",
    "existing_destination", "destination_inside_assets"])
def test_invalid_or_incomplete_inputs_reject_without_prepared_output(client, change):
    _, version, assets, libraries, destination = client
    first = libraries[0] / "example/base/1/base-1.jar"
    asset = next((assets / "objects").rglob("?" * 40))
    if change == "missing_library":
        first.unlink()
    elif change in {"wrong_library", "bad_preferred_copy"}:
        if change == "bad_preferred_copy":
            other = libraries[1] / "example/base/1/base-1.jar"
            other.parent.mkdir(parents=True)
            other.write_bytes(first.read_bytes())
        first.write_bytes(b"wrong")
    elif change == "wrong_asset":
        asset.write_bytes(b"wrong asset")
    elif change == "hardlinked_asset":
        os.link(asset, assets / "hardlink")
    elif change == "wrong_logging":
        (assets / "log_configs/client-1.12.xml").write_bytes(b"wrong")
    elif change == "other_library_origin":
        version["libraries"][0]["downloads"]["artifact"]["url"] = "https://example.invalid/library.jar"
    elif change == "coordinate_mismatch":
        version["libraries"][0]["name"] = "different:base:1"
    elif change == "duplicate_library":
        version["libraries"].append(copy.deepcopy(version["libraries"][0]))
    elif change == "unsupported_rule":
        version["libraries"][0]["rules"] = [{"action": "allow", "features": {"unknown_feature": True}}]
    elif change == "explicit_null_rule":
        version["libraries"][0]["rules"] = None
    elif change == "wrong_java":
        version["javaVersion"]["majorVersion"] = 21
    elif change == "wrong_main":
        version["mainClass"] = "example.Main"
    elif change == "index_hash":
        (assets / "indexes/1.19.json").write_bytes(b"{}")
    elif change == "index_total":
        version["assetIndex"]["totalSize"] += 1
    elif change == "existing_destination":
        destination.mkdir()
    elif change == "destination_inside_assets":
        client = (*client[:-1], assets / "output")
    with pytest.raises(Fault):
        prepare(client)
    assert not destination.exists() or change == "existing_destination"


@pytest.mark.parametrize("change", ["traversal_name", "conflicting_alias", "virtual_layout", "unsafe_hash"])
def test_asset_index_layout_and_aliases_are_exact(client, change):
    _, version, assets, _, destination = client
    path = assets / "indexes/1.19.json"
    index = json.loads(path.read_bytes())
    if change == "traversal_name":
        index["objects"]["../private"] = index["objects"].pop("minecraft/alias.ogg")
    elif change == "conflicting_alias":
        index["objects"]["minecraft/alias.ogg"]["size"] += 1
    elif change == "virtual_layout":
        index["virtual"] = True
    else:
        index["objects"]["minecraft/alias.ogg"]["hash"] = "../escape"
    raw = encode(index)
    path.write_bytes(raw)
    version["assetIndex"].update(pin(raw, "https://piston-meta.mojang.com/v1/packages/{sha}/1.19.json"))
    with pytest.raises(Fault):
        prepare(client)
    assert not destination.exists()


def test_late_source_change_retains_partial_copy_and_refuses_replay(client, monkeypatch):
    import mcbench.vanilla_client as module
    original = module._license_metadata
    first = client[3][0] / "example/base/1/base-1.jar"

    def change(raw):
        first.write_bytes(b"changed after copy")
        return original(raw)

    monkeypatch.setattr(module, "_license_metadata", change)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        prepare(client)
    assert client[-1].is_dir()
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        prepare(client)


def test_cli_uses_durable_acquisition_and_preserves_request_state(request, client):
    provider, receipt, source_version = request.getfixturevalue("inputs")
    raw, version, assets, libraries, destination = client
    version["downloads"]["server"] = source_version["downloads"]["server"]
    item = next(item for item in receipt["distributions"] if item["role"] == "client")
    Path(item["path"]).write_bytes(raw)
    item.update(sha256=hashlib.sha256(raw).hexdigest(), origin=version["downloads"]["client"]["url"])
    ref = provider.import_acquisition_receipt(sources(provider, receipt, version))
    Path(item["path"]).unlink()
    args = ["pack", "prepare-vanilla-client", str(assets), str(destination), "--request", "vanilla",
            "--store", str(provider.db.path.parent), "--simulation"]
    for root in libraries:
        args.extend(["--library-root", str(root)])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    value = json.loads(result.output)
    assert value["schema"] == "strata/VanillaClientSoftware/1" and value["acquisition_receipt"] == ref
    assert provider._json("vanilla", value["evidence"])["classpath"] == value["classpath"]
    status = provider.status("vanilla")
    assert status["state"] == "ACQUIRED" and status["inventory"] is None and status["lock"] is None
