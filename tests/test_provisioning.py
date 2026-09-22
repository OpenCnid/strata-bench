"""Synthetic installation bytes exercise actual storage and provisioning, not T02."""

import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

import pytest
from typer.testing import CliRunner

from mcbench.cli import app
from mcbench.inventory import file_hash, inspect_archive, scan_tree, template_path
from mcbench.pack_policies import reviewed_vendor_paths
from mcbench.provisioning import (
    EXPERT_CHECKS, PROVISION_CHECKS, AcquisitionReceipt, LaunchProfile, PackProvider,
    ProvisioningEvidence, RoleInventoryInput, validate_launch_environment,
)
from mcbench.records import FileEntry, PackLock
from mcbench.storage import Fault, Principal, digest


@pytest.fixture
def prepared(database, cas, tmp_path):
    service = PackProvider(database, cas, simulation=True)
    service.resolve_candidate("pack1", "e9e")
    evidence = service._put("pack1", {"is_example": True, "source": "synthetic fixture"})
    manifest = {"manifestType": "minecraftModpack", "manifestVersion": 1, "version": "1.27.0",
                "minecraft": {"version": "1.19.2", "modLoaders": [
                    {"id": "forge-43.4.23", "primary": True}]},
                "files": [{"projectID": 1, "fileID": 2, "required": True}]}
    distributions = []
    for role, file_id in (("client", 8161120), ("server", 8161123)):
        path = tmp_path / (role + ".zip")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr("bootstrap.txt", "synthetic inspected bootstrap")
        distributions.append({"role": role, "file_id": file_id, "path": str(path),
            "sha256": file_hash(path), "license_ref": "synthetic license",
            "origin": f"https://www.curseforge.com/minecraft/modpacks/enigmatica9expert/files/{file_id}",
            "evidence_ref": evidence})
    executable = tmp_path / "java.fixture"
    executable.write_bytes(b"Not an executable; synthetic JVM fingerprint fixture")
    pin = {"version": "synthetic-17", "digest": file_hash(executable)}
    receipt = AcquisitionReceipt.model_validate({"schema": "strata/AcquisitionReceipt/1",
        "is_example": True, "request_id": "pack1", "provider": "curseforge", "target": "e9e",
        "distributions": distributions, "launcher": pin, "java": pin,
        "official_workflow_evidence": evidence})
    roles = []
    for role in ("client", "server"):
        root = tmp_path / role
        (root / "mods").mkdir(parents=True)
        (root / "mods" / "fixture.jar").write_bytes(b"synthetic mod fixture" * 100)
        (root / "config.txt").write_bytes(b"synthetic expert configuration")
        entries = [item | {"role": role, "origin": "synthetic origin", "project_id": 1,
                   "file_id": 2, "license_ref": "synthetic license", "layer": "resolved"}
                   for item in scan_tree(root)]
        roles.append(RoleInventoryInput.model_validate({"role": role, "root": str(root),
            "files": entries, "provenance_evidence": evidence, "exclusions_evidence": evidence}))
    command = {"executable": pin, "executable_path": str(executable), "arguments": ["@args.txt"],
               "working_directory": ".", "environment": {}, "reviewed_bootstrap": evidence}
    launch = LaunchProfile.model_validate({"schema": "strata/LaunchProfile/1", "is_example": True,
                                          "client": command, "server": command})
    return service, receipt, roles, launch, evidence


def seal(prepared):
    service, receipt, roles, launch, evidence = prepared
    imported = service.import_acquisition_receipt(receipt)
    inventory = service.verify_inventory("pack1", roles)
    identity = {"is_example": True, "request_id": "pack1", "inventory_digest": inventory[11:],
                "receipt_digest": imported[11:], "launch_profile_digest": digest(launch.model_dump())}
    checks = {key: service._put("pack1", {"schema": "strata/ProvisioningCheck/1", **identity,
              "check_id": key, "result": "pass", "evidence_refs": [evidence]})
              for key in PROVISION_CHECKS | EXPERT_CHECKS}
    proof = ProvisioningEvidence.model_validate({"schema": "strata/ProvisioningEvidence/1",
        "is_example": True, "request_id": "pack1", "inventory_digest": inventory[11:],
        "receipt_digest": imported[11:], "launch_profile_digest": digest(launch.model_dump()),
        "checks": checks})
    return service.seal_template("pack1", launch, proof), proof


@pytest.mark.parametrize("missing", ["license", "origin", "file"])
def test_invalid_second_role_is_rejected_before_any_installed_file_import(prepared, missing):
    service, receipt, roles, _, _ = prepared
    service.import_acquisition_receipt(receipt)
    role = next(role for role in roles if role.role == "server")
    if missing == "license":
        role.files[-1].license_ref = None
    elif missing == "origin":
        role.files[-1].origin = ""
    else:
        (Path(role.root) / role.files[-1].path).unlink()
    before_objects = list(service.db.connection.execute("SELECT * FROM objects ORDER BY namespace,ref"))
    before_events = list(service.db.connection.execute("SELECT * FROM outbox ORDER BY cursor"))
    with pytest.raises(Fault):
        service.verify_inventory("pack1", roles)
    assert list(service.db.connection.execute("SELECT * FROM objects ORDER BY namespace,ref")) == before_objects
    assert list(service.db.connection.execute("SELECT * FROM outbox ORDER BY cursor")) == before_events
    assert service.status("pack1")["state"] == "ACQUIRED"
    assert service.status("pack1")["inventory"] is None


def test_full_import_seal_materialization_independent_bytes(prepared, tmp_path):
    service, receipt, roles, launch, _ = prepared
    result = service.request_acquisition("pack1")
    assert result["state"] == "AWAITING_ARTIFACT"
    assert not result["download_started"] and not result["terms_accepted"]
    lock_ref, proof = seal(prepared)
    assert service.seal_template("pack1", launch, proof) == lock_ref
    lock = PackLock.model_validate(service._json("pack1", lock_ref))
    assert lock.status == "sealed" and lock.is_example
    assert service.import_acquisition_receipt(receipt) == service.status("pack1")["receipt"]
    for name in ("one", "two"):
        marker = service.materialize("pack1", tmp_path / name)
        assert marker["lock"] == lock_ref
        assert scan_tree(tmp_path / name / "server") == scan_tree(tmp_path / roles[1].root)
    (tmp_path / "one/server/mods/fixture.jar").write_bytes(b"changed in writable instance")
    assert (tmp_path / "two/server/mods/fixture.jar").read_bytes() == b"synthetic mod fixture" * 100
    with pytest.raises(Fault, match="DESTINATION_EXISTS"):
        service.materialize("pack1", tmp_path / "two")
    assert service.status("pack1")["game_conformance_claim"] is None


def test_sealed_explicit_platform_environment_preserves_only_declared_values(prepared, tmp_path, monkeypatch):
    service, _, _, launch, _ = prepared
    scratch = tmp_path / "private-temp"
    scratch.mkdir()
    settings = {"SystemRoot": str(tmp_path), "WINDIR": str(tmp_path),
                "TEMP": str(scratch), "TMP": str(scratch)}
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-inherited-canary")
    launch.server.environment = settings
    lock_ref, _ = seal(prepared)
    lock = service._json("pack1", lock_ref)
    profile = service._json("pack1", lock["launch_profile"])
    assert profile["server"]["environment"] == settings
    assert profile["client"]["environment"] == {}


@pytest.mark.parametrize("case", ["secret", "java_injection", "nul", "relative", "missing", "file", "mismatch"])
def test_launch_environment_rejects_unsafe_or_ambiguous_settings(tmp_path, case):
    file = tmp_path / "file"
    file.write_text("fixture")
    values = {
        "secret": {"OPENAI_API_KEY": "synthetic-secret"},
        "java_injection": {"JAVA_TOOL_OPTIONS": "-Dfixture=true"},
        "nul": {"LANG": "en\x00US"},
        "relative": {"TEMP": "relative"},
        "missing": {"TEMP": str(tmp_path / "missing")},
        "file": {"TMP": str(file)},
        "mismatch": {"TEMP": str(tmp_path), "TMP": str(tmp_path.parent)},
    }
    with pytest.raises(Fault, match="ENVIRONMENT_NOT_ALLOWED|INVALID_ENVIRONMENT"):
        validate_launch_environment(values[case])


def test_expired_request_and_stable_candidate(database, cas):
    service = PackProvider(database, cas)
    service.resolve_candidate("v", "vanilla", now=10)
    service.resolve_candidate("v", "vanilla", now=20)
    assert service.request_acquisition("v", now=30)["expires_unix"] == 10 + 7 * 86400
    with pytest.raises(Fault, match="REQUEST_EXPIRED"):
        service.request_acquisition("v", now=10 + 7 * 86400)
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        service.resolve_candidate("v", "e9e")
    with pytest.raises(Fault, match="SIMULATION_STORE"):
        PackProvider(database, cas, simulation=True)


@pytest.mark.parametrize("change,code", [
    ({"file_id": 99}, "UNAPPROVED_ORIGIN|RELEASE_MISMATCH"),
    ({"origin": "https://www.curseforge.com.evil.test/minecraft/x"}, "UNAPPROVED_ORIGIN"),
    ({"origin": "https://user:secret@www.curseforge.com/"}, "UNAPPROVED_ORIGIN"),
    ({"sha256": "0" * 64}, "HASH_MISMATCH"),
    ({"path": "relative.zip"}, "UNSAFE_PATH"),
])
def test_receipt_identity_and_hash_rejections(prepared, change, code):
    service, receipt, *_ = prepared
    modified = receipt.model_dump()
    modified["distributions"][0].update(change)
    with pytest.raises(Fault, match=code):
        service.import_acquisition_receipt(AcquisitionReceipt.model_validate(modified))
    assert service.status("pack1")["state"] == "RESOLVED"


def test_wrong_manifest_loader_and_example_profile(prepared, tmp_path):
    service, receipt, *_ = prepared
    path = tmp_path / "client.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"manifestType": "minecraftModpack",
            "manifestVersion": 1, "version": "1.26.0", "minecraft": {"version": "1.19.2"}}))
    changed = receipt.model_dump()
    changed["distributions"][0]["sha256"] = file_hash(path)
    with pytest.raises(Fault, match="RELEASE_MISMATCH"):
        service.import_acquisition_receipt(AcquisitionReceipt.model_validate(changed))
    changed["is_example"] = False
    with pytest.raises(Fault, match="EXAMPLE_NOT_EXECUTABLE"):
        service.import_acquisition_receipt(AcquisitionReceipt.model_validate(changed))


@pytest.mark.parametrize("name,code", [
    ("../escape", "UNSAFE_PATH"), ("C:/escape", "UNSAFE_PATH"),
    ("mods/auth.json", "PRIVATE_INSTALLATION_CONTENT"), ("world/level.dat", "PRIVATE_INSTALLATION_CONTENT"),
])
def test_archive_rejects_unsafe_and_private_members(tmp_path, name, code):
    path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, "private canary")
    with pytest.raises(Fault, match=code):
        inspect_archive(path)


def test_archive_symlink_collision_and_size(tmp_path):
    path = tmp_path / "unsafe.zip"
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(link, "outside")
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        inspect_archive(path)
    for names in (("File", "file"), ("mods", "mods/file")):
        with zipfile.ZipFile(path, "w") as archive:
            for name in names:
                archive.writestr(name, "bytes")
        with pytest.raises(Fault, match="PATH_COLLISION"):
            inspect_archive(path)
    with pytest.raises(Fault, match="ARTIFACT_QUOTA"):
        inspect_archive(path, max_expanded_bytes=1)


def test_reviewed_vendor_world_paths_require_exact_content_and_kind(tmp_path):
    import hashlib
    relative = "config/jei/world/local/fixture/bookmarks.ini"
    data = b"synthetic vendor bookmark"
    reviewed = {relative: hashlib.sha256(data).hexdigest()}
    reviewed.update({str(p): None for p in PurePosixPath(relative).parents
                     if str(p) != "."})
    root = tmp_path / "installed"
    file = root / relative
    file.parent.mkdir(parents=True)
    file.write_bytes(data)
    assert scan_tree(root, reviewed_world_paths=reviewed)[0]["digest"] == reviewed[relative]
    with pytest.raises(Fault, match="PRIVATE_INSTALLATION_CONTENT"):
        scan_tree(root)
    file.write_bytes(b"learned player bookmark")
    with pytest.raises(Fault, match="VENDOR_CONTENT_MISMATCH"):
        scan_tree(root, reviewed_world_paths=reviewed)
    file.write_bytes(data)
    sibling = file.parent / "player-cache.ini"
    sibling.write_bytes(b"private canary")
    with pytest.raises(Fault, match="PRIVATE_INSTALLATION_CONTENT"):
        scan_tree(root, reviewed_world_paths=reviewed)
    # A review cannot authorize credentials, even at the exact listed path.
    with pytest.raises(Fault, match="PRIVATE_INSTALLATION_CONTENT"):
        template_path("config/jei/world/auth.json", reviewed_world_paths={
            "config/jei/world/auth.json": "0" * 64})
    path = tmp_path / "vendor.zip"
    for contents, valid in ((data, True), (b"modified", False)):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(relative, contents)
        if valid:
            assert inspect_archive(path, reviewed_world_paths=reviewed)["members"] == 1
        else:
            with pytest.raises(Fault, match="VENDOR_CONTENT_MISMATCH"):
                inspect_archive(path, reviewed_world_paths=reviewed)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("config/jei/world", b"file masquerading as reviewed directory")
    with pytest.raises(Fault, match="VENDOR_CONTENT_MISMATCH"):
        inspect_archive(path, reviewed_world_paths=reviewed)
    assert reviewed_vendor_paths("vanilla") == {}
    assert all(p.startswith("overrides/") for p in reviewed_vendor_paths("e9e", archive=True))


def test_reviewed_initial_file_survives_seal_and_fresh_materialization(prepared, tmp_path, monkeypatch):
    import hashlib
    _, _, roles, _, _ = prepared
    relative = "config/jei/world/local/fixture/bookmarks.ini"
    data = b"synthetic immutable vendor knowledge"
    review = {relative: hashlib.sha256(data).hexdigest()}
    review.update({str(p): None for p in PurePosixPath(relative).parents if str(p) != "."})
    monkeypatch.setattr("mcbench.provisioning.reviewed_vendor_paths",
                        lambda target, archive=False: {} if archive else review)
    for role in roles:
        root = Path(role.root)
        file = root / relative
        file.parent.mkdir(parents=True)
        file.write_bytes(data)
        entry = {"path": relative, "digest": review[relative], "bytes": len(data), "role": role.role,
                 "origin": "synthetic vendor", "project_id": None, "file_id": None,
                 "license_ref": "synthetic", "layer": "resolved"}
        role.files.append(FileEntry.model_validate(entry))
    seal(prepared)
    prepared[0].materialize("pack1", tmp_path / "initial-copy")
    assert (tmp_path / "initial-copy/client" / relative).read_bytes() == data
    assert (tmp_path / "initial-copy/server" / relative).read_bytes() == data


def test_incomplete_changed_or_secret_installed_inventory(prepared, tmp_path):
    service, receipt, roles, *_ = prepared
    service.import_acquisition_receipt(receipt)
    missing = roles[0].model_copy(update={"files": roles[0].files[:-1]})
    with pytest.raises(Fault, match="INCOMPLETE_INVENTORY"):
        service.verify_inventory("pack1", [missing, roles[1]])
    config = tmp_path / "client/config.txt"
    before = config.read_bytes()
    config.write_bytes(b"different")
    with pytest.raises(Fault, match="HASH_MISMATCH"):
        service.verify_inventory("pack1", roles)
    config.write_bytes(before)
    (tmp_path / "client/auth.json").write_text("secret canary")
    with pytest.raises(Fault, match="PRIVATE_INSTALLATION_CONTENT"):
        service.verify_inventory("pack1", roles)
    assert service.status("pack1")["state"] == "ACQUIRED"


def test_seal_requires_all_bound_evidence_and_immutable_inputs(prepared):
    service, _, _, launch, _ = prepared
    _, proof = seal(prepared)
    for update, code in [({"inventory_digest": "0" * 64}, "HASH_MISMATCH"),
                         ({"checks": {}}, "PROVISIONING_UNVERIFIED")]:
        with pytest.raises(Fault, match=code):
            service.seal_template("pack1", launch, proof.model_copy(update=update))
    with pytest.raises(Fault, match="HASH_MISMATCH"):
        service.seal_template("pack1", launch.model_copy(update={"server": launch.server.model_copy(
            update={"arguments": ["different"]})}), proof)


def test_tampered_cas_leaves_no_partial_materialization(prepared, tmp_path):
    service, *_ = prepared
    lock_ref, _ = seal(prepared)
    lock = service._json("pack1", lock_ref)
    inventory = service._json("pack1", lock["resolved_inventory"])
    service.cas._path("cas:sha256:" + inventory["files"][0]["digest"]).write_bytes(b"tampered")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        service.materialize("pack1", tmp_path / "new")
    assert not (tmp_path / "new").exists()
    assert not list(tmp_path.glob(".strata-instance-*"))


def test_streaming_quota_no_orphans_and_no_agent_access(cas, operator, tmp_path):
    source = tmp_path / "blob"
    source.write_bytes(b"x" * 1_100_000)
    sha = file_hash(source)
    with pytest.raises(Fault, match="ARTIFACT_QUOTA"):
        cas.put_file(operator, "large", "operator", source, sha, quota_bytes=1, max_object_bytes=2**22)
    assert not cas._path("cas:sha256:" + sha).exists()
    with pytest.raises(Fault, match="HASH_MISMATCH"):
        cas.put_file(operator, "large", "operator", source, "0" * 64,
                     quota_bytes=2**22, max_object_bytes=2**22)
    assert not list(cas.root.glob(".asset-*"))
    ref = cas.put_file(operator, "large", "operator", source, sha,
                       quota_bytes=2**22, max_object_bytes=2**22)
    with pytest.raises(Fault, match="FORBIDDEN"):
        cas.copy_to(Principal("large", "executor"), "large", ref, tmp_path / "stolen")
    assert not (tmp_path / "stolen").exists()
    cas.copy_to(operator, "large", ref, tmp_path / "copied")
    assert file_hash(tmp_path / "copied") == sha


def test_pack_cli_requests_do_not_install_or_accept_terms(tmp_path):
    runner = CliRunner()
    args = ["--request", "vanilla1", "--store", str(tmp_path / "private")]
    result = runner.invoke(app, ["pack", "resolve", "vanilla", *args])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "candidate"
    result = runner.invoke(app, ["pack", "acquire", *args])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["state"] == "AWAITING_ARTIFACT"
    assert not json.loads(result.output)["terms_accepted"]
    result = runner.invoke(app, ["pack", "materialize", str(tmp_path / "instance"), *args])
    assert result.exit_code == 2, result.output
    assert json.loads(result.output)["code"] == "UNSEALED_PACK"
