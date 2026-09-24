"""Synthetic source/acquisition and paired role preparation; no game evidence."""

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import pytest

from mcbench import e9e_content as content
from mcbench.storage import Fault
from test_provisioning import prepare_fixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def provisioning_fixture(database, cas, tmp_path):
    return prepare_fixture(database, cas, tmp_path)


def archive(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        for name, raw in entries.items():
            z.writestr(name, raw)
    return output.getvalue()


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    manifest = {"version": "1.27.0", "manifestType": "minecraftModpack", "manifestVersion": 1,
        "overrides": "overrides", "minecraft": {"version": "1.19.2", "modLoaders": [
            {"id": "forge-43.4.23", "primary": True}]}, "files": [
            {"projectID": p, "fileID": f, "required": True,
             "downloadUrl": f"https://edge.forgecdn.net/files/{f // 1000}/{f % 1000}/{name}"}
            for p, f, name in ((1, 1001, "shared%2bmod.jar"), (231275, 1002, "client-only.jar"))]}
    vendor = {"overrides/config/initial.toml": b"vendor configuration", "overrides/local/a.txt": b"local",
              "overrides/config/example-client.toml": b"client only",
              "overrides/config/sub/example-client.toml": b"nested not matched by star",
              "overrides/config/empty/": b""}
    config = b"synthetic reviewed server policy"
    archives = {role: archive({**vendor, "manifest.json": json.dumps(manifest),
                **({"server-setup-config.yaml": config, "start-server.bat": b"not executed"}
                   if role == "server" else {})}) for role in ("client", "server")}
    captures, roots, exclusions = {}, {}, {}
    for role in ("client", "server"):
        roots[role] = tmp_path / (role + "-mods")
        roots[role].mkdir()
        rows = []
        for entry in manifest["files"]:
            if role == "server" and entry["projectID"] == 231275:
                continue
            name = entry["downloadUrl"].rsplit("/", 1)[-1]
            if role == "client":
                name = name.replace("%2b", "+")
            raw = str(entry["projectID"]).encode()
            (roots[role] / name).write_bytes(raw)
            rows.append({"path": "mods/" + name, "bytes": len(raw), "sha256": sha(raw), "manifest": entry})
        captures[role] = json.dumps({"missing": [], "extra": [], "files": rows}).encode()
        name = "strata-forge1192-telemetry-0.3.4.jar"
        (roots[role] / name).write_bytes(b"operator instrumentation")
        exclusions[role] = [{"path": name, "digest": sha(b"operator instrumentation"), "bytes": 24}]
    monkeypatch.setattr(content, "ARCHIVES", {role: sha(raw) for role, raw in archives.items()})
    monkeypatch.setattr(content, "CAPTURES", {role: sha(raw) for role, raw in captures.items()})
    monkeypatch.setattr(content, "SERVER_CONFIG", sha(config))
    return {"archives": archives, "captures": captures, "mod_roots": roots,
            "excluded_harness": exclusions, "destination": tmp_path / "vendor"}


def test_paired_content_exact_names_filters_and_pending_authority(inputs):
    result = content.prepare_content(**inputs)
    client, server = result["roles"]
    assert len(client["files"]) == 6 and len(server["files"]) == 3
    assert (Path(client["root"]) / "mods/shared+mod.jar").read_bytes() == b"1"
    assert (Path(server["root"]) / "mods/shared%2bmod.jar").read_bytes() == b"1"
    assert not (Path(server["root"]) / "config/example-client.toml").exists()
    assert (Path(server["root"]) / "config/sub/example-client.toml").exists()
    assert (Path(client["root"]) / "config/empty").is_dir()
    assert server["excluded_projects"] == [231275]
    assert all(not r["effective_expert_settings_qualified"] for r in result["roles"])
    assert not result["complete_roles_qualified"] and not result["license_review_complete"]
    assert not result["bootstrap_executed"] and result["game_conformance_claim"] is None
    assert all(not list(Path(r["root"]).glob("mods/strata*")) for r in result["roles"])
    assert len(server["archive_exclusions"]) == 5
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        content.prepare_content(**inputs)


@pytest.mark.parametrize("target", ["archives", "captures"])
@pytest.mark.parametrize("role", ["client", "server"])
def test_changed_pinned_sources_reject_before_output(inputs, target, role):
    inputs[target][role] += b" "
    with pytest.raises(Fault):
        content.prepare_content(**inputs)
    assert not inputs["destination"].exists()


@pytest.mark.parametrize("mutation", ["changed", "missing", "extra", "hardlink", "wrong_exclusion"])
def test_both_roles_validate_before_any_copy(inputs, mutation):
    root = inputs["mod_roots"]["server"]
    mod = root / "shared%2bmod.jar"
    if mutation == "changed":
        mod.write_bytes(b"changed")
    elif mutation == "missing":
        mod.unlink()
    elif mutation == "extra":
        (root / "unreviewed.jar").write_bytes(b"extra")
    elif mutation == "hardlink":
        os.link(mod, root / "linked.jar")
    else:
        inputs["excluded_harness"]["server"][0]["digest"] = "0" * 64
    with pytest.raises(Fault):
        content.prepare_content(**inputs)
    assert not inputs["destination"].exists()


@pytest.mark.parametrize("mutation", ["missing_project", "wrong_manifest", "wrong_filename", "role_hash"])
def test_capture_semantics_are_not_only_a_hash_check(inputs, monkeypatch, mutation):
    document = json.loads(inputs["captures"]["server"])
    if mutation == "missing_project":
        document["files"] = []
    elif mutation == "wrong_manifest":
        document["files"][0]["manifest"]["fileID"] += 1
    elif mutation == "wrong_filename":
        document["files"][0]["path"] = "mods/unknown.jar"
    else:
        document["files"][0]["sha256"] = "0" * 64
    raw = json.dumps(document).encode()
    inputs["captures"]["server"] = raw
    monkeypatch.setitem(content.CAPTURES, "server", sha(raw))
    with pytest.raises(Fault):
        content.prepare_content(**inputs)
    assert not inputs["destination"].exists()


def test_copy_change_leaves_partial_output_and_no_receipt(inputs, monkeypatch):
    original = content.read_input
    monkeypatch.setattr(content, "read_input", lambda path, limit: original(path, limit) + b"changed")
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        content.prepare_content(**inputs)
    assert inputs["destination"].exists()
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        content.prepare_content(**inputs)


def test_durable_acquisition_consumer_binds_capture_refs_without_promoting_state(inputs, provisioning_fixture):
    service, receipt, *_ = provisioning_fixture
    for item in receipt.distributions:
        raw = inputs["archives"][item.role]
        Path(item.path).write_bytes(raw)
        item.sha256 = sha(raw)
    acquisition = service.import_acquisition_receipt(receipt)
    paths = {}
    for role, raw in inputs["captures"].items():
        paths[role] = inputs["destination"].parent / (role + "-capture.json")
        paths[role].write_bytes(raw)
    result = service.prepare_e9e_content("pack1", paths, inputs["mod_roots"],
                                         inputs["excluded_harness"], inputs["destination"])
    assert result["acquisition_receipt"] == acquisition and result["is_example"]
    assert service.status("pack1")["state"] == "ACQUIRED"
    assert service._json("pack1", result["evidence"])["roles"] == result["roles"]
    for role, ref in result["capture_refs"].items():
        assert ref == "cas:sha256:" + sha(inputs["captures"][role])


def test_vendor_mod_cannot_be_reclassified_as_harness(inputs):
    inputs["excluded_harness"]["server"].append({"path": "shared%2bmod.jar", "digest": sha(b"1"), "bytes": 1})
    with pytest.raises(Fault, match="E9E_HARNESS_EXCLUSION_INVALID"):
        content.prepare_content(**inputs)


@pytest.mark.parametrize("directory", ["kubejs/assets/", "kubejs/client_scripts/", "local/", "packmenu/"])
def test_java_paths_normalization_keeps_ignored_tree_parent_directory(directory):
    assert content.server_exclusion(directory) is None
    assert content.server_exclusion(directory + "child") == directory + "**"
