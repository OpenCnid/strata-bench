"""Synthetic bundles exercise exact acquired/installed/staged joins; no game runs."""

import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import pytest
from typer.testing import CliRunner

from mcbench.cli import app
from mcbench.inventory import file_hash, scan_tree
from mcbench.provisioning import parse_acquisition
from mcbench.storage import Database, Fault
from mcbench.vanilla_runtime import _archive, _license_metadata, prepare_server
from test_vanilla_artifacts import inputs as inputs, sources


@pytest.fixture
def database(tmp_path):
    database = Database(tmp_path / "controller.sqlite")
    yield database
    database.close()


def jar(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, raw in entries.items():
            archive.writestr(name, raw)
    return stream.getvalue()


def bundle(change=None):
    library = jar({"example.class": b"synthetic", "META-INF/LICENSE.txt": b"synthetic license evidence"})
    server = jar({"server.class": b"synthetic server"})
    member = "example/runtime/1/runtime-1.jar"
    sha = hashlib.sha256(library).hexdigest()
    versions = hashlib.sha256(server).hexdigest() + "\t1.19.2\t1.19.2/server-1.19.2.jar\n"
    libraries = f"{sha}\texample:runtime:1\t{member}\n"
    entries = {"META-INF/MANIFEST.MF": "Manifest-Version: 1.0\r\nMain-Class: net.minecraft.bundler.Main\r\n"
               "Bundler-Format: 1.0\r\n\r\n", "META-INF/main-class": "net.minecraft.server.Main",
               "META-INF/versions.list": versions, "META-INF/libraries.list": libraries,
               "META-INF/versions/1.19.2/server-1.19.2.jar": server,
               "META-INF/libraries/" + member: library}
    if change == "unlisted_payload":
        entries["META-INF/libraries/extra.jar"] = library
    elif change == "false_payload_hash":
        entries["META-INF/libraries.list"] = libraries.replace(sha, "0" * 64)
    elif change == "duplicate_payload":
        entries["META-INF/libraries.list"] = libraries * 2
    elif change == "wrong_coordinate":
        entries["META-INF/libraries.list"] = libraries.replace("example:runtime:1", "other:runtime:1")
    elif change == "traversal":
        entries["../escape.jar"] = library
    elif change == "wrong_main":
        entries["META-INF/main-class"] = "example.Main"
    elif change == "missing_payload":
        del entries["META-INF/libraries/" + member]
    elif change == "case_collision":
        entries["meta-inf/LIBRARIES/" + member] = library
    elif change == "non_zip_payload":
        entries["META-INF/libraries/" + member] = b"unreadable payload"
    elif change == "wrong_version":
        entries["META-INF/versions.list"] = versions.replace("\t1.19.2\t", "\t1.19.3\t")
    return jar(entries), {"libraries/" + member: library, "versions/1.19.2/server-1.19.2.jar": server}


def installed(tmp_path, change=None):
    raw, files = bundle(change)
    root = tmp_path / "installed"
    for name, data in {"server.jar": raw, **files}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (root / "world").mkdir()
    (root / "world/level.dat").write_bytes(b"private saved world")
    (root / "logs").mkdir()
    (root / "server.properties").write_text("synthetic configuration")
    (root / "usercache.json").write_text("[]")
    return raw, root


def test_derives_every_payload_preserves_state_and_retains_license_evidence(tmp_path):
    raw, root = installed(tmp_path)
    destination = tmp_path / "software"
    result = prepare_server(raw, root, destination)
    assert result["installed_payloads_verified"] and result["independent_software_copy_verified"]
    assert not result["complete_role_qualified"] and not result["license_review_complete"]
    assert result["game_conformance_claim"] is None
    assert len(result["files"]) == 3
    assert len(scan_tree(destination)) == 3
    assert (root / "world/level.dat").read_bytes() == b"private saved world"
    assert not (destination / "world").exists() and not (destination / "server.properties").exists()
    assert {d["path"]: d["disposition"] for d in result["source_dispositions"]} == {
        "world": "private_state_excluded", "logs": "diagnostic_excluded",
        "usercache.json": "private_state_excluded", "server.properties": "configuration_pending"}
    library = next(f for f in result["files"] if f["path"].startswith("libraries/"))
    assert library["license_metadata"][0]["sha256"] == hashlib.sha256(b"synthetic license evidence").hexdigest()
    assert all(f["license_review"] == "pending" for f in result["files"])
    (destination / "server.jar").write_bytes(b"changed independent copy")
    assert file_hash(root / "server.jar") == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("change", ["unlisted_payload", "false_payload_hash", "duplicate_payload",
    "wrong_coordinate", "traversal", "wrong_main", "missing_payload", "case_collision",
    "non_zip_payload", "wrong_version"])
def test_bad_bundles_reject_before_destination_creation(tmp_path, change):
    raw, root = installed(tmp_path, change)
    with pytest.raises(Fault):
        prepare_server(raw, root, tmp_path / "software")
    assert not (tmp_path / "software").exists()


@pytest.mark.parametrize("change", ["modified", "missing", "extra_library", "extra_empty_directory",
    "unknown_root", "hardlink", "existing_destination", "destination_inside_source", "parent_escape"])
def test_runtime_mismatch_or_unsafe_copy_preserves_source(tmp_path, change):
    raw, root = installed(tmp_path)
    library = next((root / "libraries").rglob("*.jar"))
    destination = tmp_path / "software"
    if change == "modified":
        library.write_bytes(b"modified installed library")
    elif change == "missing":
        library.unlink()
    elif change == "extra_library":
        (root / "libraries/extra.jar").write_bytes(b"extra")
    elif change == "extra_empty_directory":
        (root / "libraries/empty").mkdir()
    elif change == "unknown_root":
        (root / "new-configuration.json").write_text("{}")
    elif change == "hardlink":
        os.link(library, tmp_path / "shared.jar")
    elif change == "existing_destination":
        destination.mkdir()
    elif change == "destination_inside_source":
        destination = root / "copy"
    elif change == "parent_escape":
        destination = tmp_path / "nonexistent/../software"
    with pytest.raises(Fault):
        prepare_server(raw, root, destination)
    assert (root / "server.jar").read_bytes() == raw
    assert (root / "world/level.dat").read_bytes() == b"private saved world"


def test_change_during_copy_retains_partial_output_without_success(tmp_path, monkeypatch):
    import mcbench.vanilla_runtime as runtime
    raw, root = installed(tmp_path)
    original = runtime.file_hash
    destination = tmp_path / "software"

    def changed(path):
        if path == destination / "server.jar":
            (root / "server.properties").write_text("changed during preparation")
        return original(path)

    monkeypatch.setattr(runtime, "file_hash", changed)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        prepare_server(raw, root, destination)
    assert destination.is_dir()  # Diagnostic evidence, never silently deleted or replayed.
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        prepare_server(raw, root, destination)


def acquired(values, tmp_path):
    provider, receipt, version = values
    raw, root = installed(tmp_path)
    item = next(item for item in receipt["distributions"] if item["role"] == "server")
    Path(item["path"]).write_bytes(raw)
    sha1 = hashlib.sha1(raw).hexdigest()
    url = f"https://piston-data.mojang.com/v1/objects/{sha1}/server.jar"
    item.update(sha256=hashlib.sha256(raw).hexdigest(), origin=url)
    version["downloads"]["server"] = {"sha1": sha1, "url": url, "size": len(raw)}
    provider.import_acquisition_receipt(sources(provider, receipt, version))
    return provider, receipt, root


def test_operator_command_joins_cas_source_without_reopening_old_acquisition_paths(request, tmp_path):
    provider, receipt, root = acquired(request.getfixturevalue("inputs"), tmp_path)
    for item in receipt["distributions"]:
        Path(item["path"]).unlink()
    result = CliRunner().invoke(app, ["pack", "prepare-vanilla-server", str(root), str(tmp_path / "software"),
        "--request", "vanilla", "--store", str(provider.db.path.parent), "--simulation"])
    assert result.exit_code == 0, result.output
    value = json.loads(result.output)
    assert value["acquisition_receipt"] == provider.status("vanilla")["receipt"]
    assert value["is_example"] and len(value["files"]) == 3
    assert provider._json("vanilla", value["evidence"])["software_root"] == str(tmp_path / "software")
    assert provider.status("vanilla")["state"] == "ACQUIRED"
    assert provider.status("vanilla")["inventory"] is None


def test_corrupt_retained_source_cannot_prepare(request, tmp_path):
    provider, receipt, root = acquired(request.getfixturevalue("inputs"), tmp_path)
    sha = next(item["sha256"] for item in receipt["distributions"] if item["role"] == "server")
    (provider.cas.root / sha).write_bytes(b"corrupt source")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        provider.prepare_vanilla_server("vanilla", root, tmp_path / "software")
    assert not (tmp_path / "software").exists()


def test_legacy_receipt_cannot_receive_new_verification_credit(request, tmp_path):
    provider, receipt, _ = request.getfixturevalue("inputs")
    receipt["schema"] = "strata/AcquisitionReceipt/1"
    provider.import_acquisition_receipt(parse_acquisition(receipt))
    with pytest.raises(Fault, match="VANILLA_SOURCE_VERIFICATION_REQUIRED"):
        provider.prepare_vanilla_server("vanilla", tmp_path / "source", tmp_path / "software")


def test_opaque_empty_directory_sentinel_is_retained_without_extraction():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        info = zipfile.ZipInfo("META-INF/maven/")
        info.external_attr = 0xffff0010
        archive.writestr(info, b"")
    raw = stream.getvalue()
    entries, notes = _license_metadata(raw)
    assert entries == [] and notes == [{"member": "META-INF/maven/", "external_attributes": 0xffff0010,
                                       "disposition": "opaque_empty_directory_not_extracted"}]
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        _archive(raw, max_members=10)  # Outer extraction policy remains strict.


@pytest.mark.parametrize("kind", ["symlink", "nonempty_sentinel"])
def test_opaque_metadata_does_not_accept_links_or_nonempty_sentinel(kind):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        info = zipfile.ZipInfo("META-INF/maven/" if kind == "nonempty_sentinel" else "META-INF/LICENSE")
        info.external_attr = 0xffff0010 if kind == "nonempty_sentinel" else 0o120777 << 16
        archive.writestr(info, b"target")
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        _license_metadata(stream.getvalue())
