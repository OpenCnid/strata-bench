"""Synthetic metadata/artifacts exercise real intake, not official acquisition."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from mcbench.cli import app
from mcbench.provisioning import PackProvider, parse_acquisition
from mcbench.storage import Fault


def encoded(value):
    return (json.dumps(value, indent=2) + "\n").encode()


@pytest.fixture
def inputs(database, cas, tmp_path):
    provider = PackProvider(database, cas, simulation=True)
    provider.resolve_candidate("vanilla", "vanilla")
    evidence = provider._put("vanilla", {"is_example": True, "authority": "synthetic"})
    downloads, distributions = {}, []
    for role in ("client", "server"):
        raw = (role + " synthetic distribution").encode()
        path = tmp_path / (role + ".jar")
        path.write_bytes(raw)
        sha = hashlib.sha1(raw).hexdigest()
        url = f"https://piston-data.mojang.com/v1/objects/{sha}/{role}.jar"
        downloads[role] = {"sha1": sha, "size": len(raw), "url": url}
        distributions.append({"role": role, "path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                              "origin": url, "file_id": None, "license_ref": "synthetic", "evidence_ref": evidence})
    version = {"id": "1.19.2", "type": "release", "javaVersion": {"majorVersion": 17}, "downloads": downloads}
    receipt = {"schema": "strata/AcquisitionReceipt/2", "is_example": True, "request_id": "vanilla",
               "provider": "curseforge", "target": "vanilla", "distributions": distributions,
               "launcher": {"version": "synthetic", "digest": "a" * 64},
               "java": {"version": "synthetic", "digest": "b" * 64}, "official_workflow_evidence": evidence}
    return provider, receipt, version


def sources(provider, receipt, version, *, change=None):
    raw = encoded(version)
    sha = hashlib.sha1(raw).hexdigest()
    entry = {"id": "1.19.2", "type": "release", "sha1": sha,
             "url": f"https://piston-meta.mojang.com/v1/packages/{sha}/1.19.2.json"}
    manifest = {"versions": [entry]}
    if change == "duplicate_release":
        manifest["versions"].append(copy.deepcopy(entry))
    elif change == "missing_release":
        manifest["versions"] = []
    elif change == "wrong_metadata_origin":
        entry["url"] = "https://example.invalid/1.19.2.json"
    elif change == "changed_raw_metadata":
        raw = json.dumps(version).encode()
    elif change == "duplicate_json_key":
        raw = raw.replace(b'"id": "1.19.2",', b'"id": "1.19.2", "id": "1.19.2",')
    namespace = provider.namespace("foreign" if change == "foreign_namespace" else "vanilla")
    for field, data in (("vanilla_manifest", encoded(manifest)), ("vanilla_version_metadata", raw)):
        receipt[field] = provider.cas.put(provider.principal, namespace, "operator", data)
    return parse_acquisition(receipt)


def test_vanilla_intake_joins_exact_metadata_and_artifacts_idempotently(inputs):
    provider, receipt, version = inputs
    parsed = sources(provider, receipt, version)
    ref = provider.import_acquisition_receipt(parsed)
    imported = provider._json("vanilla", ref)
    proof = imported["source_verification"]
    assert proof["policy"] == "mojang-vanilla1192-distributions/1"
    assert {p["role"] for p in proof["distributions"]} == {"client", "server"}
    assert not proof["installed_roles_qualified"] and proof["game_conformance_claim"] is None
    count = provider.db.connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
    assert provider.import_acquisition_receipt(parsed) == ref
    assert provider.db.connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == count
    assert provider.status("vanilla")["state"] == "ACQUIRED"
    assert parse_acquisition(imported["receipt"]) == parsed


@pytest.mark.parametrize("change", ["duplicate_release", "missing_release", "wrong_metadata_origin",
    "changed_raw_metadata", "duplicate_json_key", "foreign_namespace", "wrong_release", "wrong_java",
    "snapshot", "wrong_download_origin", "wrong_role_url", "wrong_size", "missing_role",
    "different_installed_bytes", "wrong_receipt_origin", "wrong_receipt_hash"])
def test_mismatched_or_unbound_sources_never_acquire(inputs, change):
    provider, receipt, version = inputs
    if change == "wrong_release":
        version["id"] = "1.19.3"
    elif change == "wrong_java":
        version["javaVersion"]["majorVersion"] = 8
    elif change == "snapshot":
        version["type"] = "snapshot"
    elif change == "wrong_download_origin":
        version["downloads"]["client"]["url"] = "https://example.invalid/client.jar"
    elif change == "wrong_role_url":
        version["downloads"]["client"]["url"] = version["downloads"]["server"]["url"]
    elif change == "wrong_size":
        version["downloads"]["client"]["size"] += 1
    elif change == "missing_role":
        del version["downloads"]["server"]
    elif change == "different_installed_bytes":
        item = receipt["distributions"][0]
        path = Path(item["path"])
        raw = b"x" * path.stat().st_size
        path.write_bytes(raw)
        item["sha256"] = hashlib.sha256(raw).hexdigest()  # Self-consistent receipt is insufficient.
    elif change == "wrong_receipt_origin":
        receipt["distributions"][0]["origin"] = receipt["distributions"][1]["origin"]
    elif change == "wrong_receipt_hash":
        receipt["distributions"][0]["sha256"] = "c" * 64
    parsed = sources(provider, receipt, version, change=change)
    with pytest.raises(Fault):
        provider.import_acquisition_receipt(parsed)
    status = provider.status("vanilla")
    assert status["state"] == "RESOLVED" and status["receipt"] is None


def test_new_receipt_cannot_relabel_forge_or_omit_the_manifest(inputs):
    provider, receipt, version = inputs
    sources(provider, receipt, version)
    receipt["target"] = "e9e"
    with pytest.raises(ValidationError):
        parse_acquisition(receipt)
    receipt["target"] = "vanilla"
    del receipt["vanilla_manifest"]
    with pytest.raises(ValidationError):
        parse_acquisition(receipt)


def test_cli_preserves_source_bytes_only_when_requested(tmp_path):
    runner = CliRunner()
    args = ["--request", "vanilla", "--store", str(tmp_path / "store"), "--simulation"]
    assert runner.invoke(app, ["pack", "resolve", "vanilla", *args]).exit_code == 0
    path = tmp_path / "metadata.json"
    raw = b'{\n  "is_example": true, "retained": "exact bytes"\n}\n'
    path.write_bytes(raw)
    result = runner.invoke(app, ["pack", "evidence", *args, "--file", str(path), "--preserve-source-bytes"])
    assert result.exit_code == 0, result.output
    ref = json.loads(result.output)["ref"]
    assert ref == "cas:sha256:" + hashlib.sha256(raw).hexdigest()
    assert (tmp_path / "store/objects" / ref[11:]).read_bytes() == raw
    canonical = runner.invoke(app, ["pack", "evidence", *args, "--file", str(path)])
    assert canonical.exit_code == 0 and json.loads(canonical.output)["ref"] != ref


def test_v2_receipt_survives_template_sealing_and_materialization(inputs, tmp_path):
    from mcbench.inventory import file_hash, scan_tree
    from mcbench.provisioning import PROVISION_CHECKS, LaunchProfile, ProvisioningEvidence, RoleInventoryInput
    from mcbench.storage import digest
    provider, receipt, version = inputs
    imported = provider.import_acquisition_receipt(sources(provider, receipt, version))
    evidence = receipt["official_workflow_evidence"]
    roles = []
    for role in ("client", "server"):
        root = tmp_path / (role + "-role")
        root.mkdir()
        (root / "fixture.txt").write_text("synthetic installed role")
        files = [item | {"role": role, "origin": "synthetic", "project_id": None, "file_id": None,
                         "license_ref": "synthetic", "layer": "resolved"} for item in scan_tree(root)]
        roles.append(RoleInventoryInput.model_validate({"role": role, "root": str(root), "files": files,
                     "provenance_evidence": evidence, "exclusions_evidence": evidence}))
    inventory = provider.verify_inventory("vanilla", roles)
    executable = tmp_path / "java.fixture"
    executable.write_bytes(b"synthetic nonexecutable")
    command = {"executable": {"version": "synthetic", "digest": file_hash(executable)},
               "executable_path": str(executable), "arguments": [], "working_directory": ".",
               "environment": {}, "reviewed_bootstrap": evidence}
    launch = LaunchProfile.model_validate({"schema": "strata/LaunchProfile/1", "is_example": True,
                                          "client": command, "server": command})
    identity = {"is_example": True, "request_id": "vanilla", "inventory_digest": inventory[11:],
                "receipt_digest": imported[11:], "launch_profile_digest": digest(launch.model_dump())}
    checks = {key: provider._put("vanilla", {"schema": "strata/ProvisioningCheck/1", **identity,
              "check_id": key, "result": "pass", "evidence_refs": [evidence]}) for key in PROVISION_CHECKS}
    proof = ProvisioningEvidence.model_validate({"schema": "strata/ProvisioningEvidence/1", **identity, "checks": checks})
    lock = provider.seal_template("vanilla", launch, proof)
    result = provider.materialize("vanilla", tmp_path / "instance")
    assert result["lock"] == lock and result["is_example"]
    assert (tmp_path / "instance/server/fixture.txt").read_text() == "synthetic installed role"
    assert provider.status("vanilla")["game_conformance_claim"] is None
