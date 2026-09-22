"""Durable official-acquisition workflow and immutable pack templates.

Receipts are operator attestations with retained evidence, not authentication of
arbitrary web content. This service does not accept EULAs, acquire accounts, run
uninspected startup scripts, or equate imported bytes with game conformance.
"""

import json
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import Field, TypeAdapter

from .contracts import Digest, Id, Ref, Strict, UInt
from .inventory import file_hash, inspect_archive, scan_tree, template_path
from .pack_policies import reviewed_vendor_paths
from .records import FileEntry, PackLock, Pin
from .storage import Principal, canonical, digest, reject_links, require

TARGETS = {
    "vanilla": {"pack_slug": "vanilla", "release": "1.19.2", "minecraft": "1.19.2",
                "loader": {"name": "none", "version": None}, "project_id": None,
                "client_file_id": None, "server_file_id": None, "source_revision": None},
    "e9e": {"pack_slug": "enigmatica9expert", "release": "1.27.0", "minecraft": "1.19.2",
            "loader": {"name": "forge", "version": "43.4.23"}, "project_id": 882461,
            "client_file_id": 8161120, "server_file_id": 8161123,
            "source_revision": "d6bed3a552de25b3bc211856fcd276fbb35d1c43"},
}
Role = Literal["client", "server"]
PROVISION_CHECKS = {
    "official_workflow", "dedicated_stopped_installation", "bootstrap_and_downloads_reviewed",
    "transitive_provenance_complete", "compatible_role_inventories", "automatic_updates_disabled",
    "legal_prerequisites_completed", "cold_restart", "runtime_configuration_pinned",
}
EXPERT_CHECKS = {"expert_config", "expert_recipe", "quest_team", "independent_player_reference"}


class DistributionInput(Strict):
    role: Role
    path: str
    sha256: Digest
    origin: str
    file_id: UInt | None
    license_ref: Annotated[str, Field(min_length=1)]
    evidence_ref: Ref


class AcquisitionReceipt(Strict):
    schema_: Literal["strata/AcquisitionReceipt/1"] = Field(alias="schema")
    is_example: bool
    request_id: Id
    provider: Literal["curseforge"]
    target: Literal["vanilla", "e9e"]
    distributions: Annotated[list[DistributionInput], Field(min_length=2, max_length=2)]
    launcher: Pin
    java: Pin
    official_workflow_evidence: Ref


class VanillaAcquisitionReceipt(AcquisitionReceipt):
    schema_: Literal["strata/AcquisitionReceipt/2"] = Field(alias="schema")
    target: Literal["vanilla"]
    vanilla_manifest: Ref
    vanilla_version_metadata: Ref


def parse_acquisition(value):
    return TypeAdapter(AcquisitionReceipt | VanillaAcquisitionReceipt).validate_python(value)


class RoleInventoryInput(Strict):
    role: Role
    root: str
    # Exact per-file provenance. No blanket inferred origin or silent exclusions.
    files: Annotated[list[FileEntry], Field(min_length=1, max_length=200000)]
    provenance_evidence: Ref
    exclusions_evidence: Ref


class LaunchCommand(Strict):
    executable: Pin
    executable_path: Annotated[str, Field(min_length=1)]
    arguments: list[str]
    working_directory: str
    environment: dict[str, str]
    reviewed_bootstrap: Ref


class LaunchProfile(Strict):
    schema_: Literal["strata/LaunchProfile/1"] = Field(alias="schema")
    is_example: bool
    client: LaunchCommand
    server: LaunchCommand


def validate_launch_environment(environment: dict[str, str]):
    """Explicit operator settings only; never fill gaps from inherited state."""
    directories = {"SystemRoot", "WINDIR", "TEMP", "TMP"}
    require(set(environment) <= {"JAVA_HOME", "PATH", "LANG", "TZ"} | directories,
            "ENVIRONMENT_NOT_ALLOWED")
    require(all("\x00" not in value for value in environment.values()), "INVALID_ENVIRONMENT")
    for name in directories & environment.keys():
        path = Path(environment[name])
        require(path.is_absolute(), "INVALID_ENVIRONMENT")
        reject_links(path)
        require(path.is_dir(), "INVALID_ENVIRONMENT")
    for first, second in (("TEMP", "TMP"), ("SystemRoot", "WINDIR")):
        if first in environment and second in environment:
            require(Path(environment[first]) == Path(environment[second]), "INVALID_ENVIRONMENT")


class ProvisioningEvidence(Strict):
    schema_: Literal["strata/ProvisioningEvidence/1"] = Field(alias="schema")
    is_example: bool
    request_id: Id
    inventory_digest: Digest
    receipt_digest: Digest
    launch_profile_digest: Digest
    # Every check points at a private evidence object; this is not a collection of
    # booleans an untrusted caller can manufacture to promote a pack.
    checks: dict[str, Ref]


class ProvisioningCheck(Strict):
    schema_: Literal["strata/ProvisioningCheck/1"] = Field(alias="schema")
    is_example: bool
    request_id: Id
    check_id: str
    result: Literal["pass", "fail", "not_run"]
    inventory_digest: Digest
    receipt_digest: Digest
    launch_profile_digest: Digest
    evidence_refs: Annotated[list[Ref], Field(min_length=1)]


def official_origin(value: str, target: str, role: str, file_id: int | None):
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and parsed.username is None and parsed.password is None
            and not parsed.query and not parsed.fragment and parsed.port in (None, 443),
            "UNAPPROVED_ORIGIN")
    if target == "e9e":
        require(parsed.hostname == "www.curseforge.com" and parsed.path ==
                f"/minecraft/modpacks/enigmatica9expert/files/{file_id}", "UNAPPROVED_ORIGIN")
        require(file_id == TARGETS[target][f"{role}_file_id"], "RELEASE_MISMATCH")
    else:
        require(file_id is None and parsed.hostname in {
            "www.curseforge.com", "support.curseforge.com", "piston-meta.mojang.com",
            "piston-data.mojang.com", "launchermeta.mojang.com", "launcher.mojang.com",
            "www.minecraft.net"}, "UNAPPROVED_ORIGIN")


class PackProvider:
    def __init__(self, database, cas, *, simulation=False, quota_bytes=64 * 1024**3):
        self.db, self.cas, self.simulation = database, cas, simulation
        self.quota = quota_bytes
        self.principal = Principal("provisioner", "operator")
        with self.db.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS provisioning_profile "
                       "(singleton INTEGER PRIMARY KEY CHECK(singleton=1), simulation INTEGER)")
            row = db.execute("SELECT simulation FROM provisioning_profile").fetchone()
            if row:
                require(bool(row[0]) == simulation, "SIMULATION_STORE")
            else:
                db.execute("INSERT INTO provisioning_profile VALUES(1,?)", (int(simulation),))
            db.execute("CREATE TABLE IF NOT EXISTS provisioning (id TEXT PRIMARY KEY, "
                       "target TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, "
                       "expires REAL NOT NULL, receipt TEXT, inventory TEXT, sealed TEXT)")

    def namespace(self, request_id):
        return "pack:" + request_id

    def _put(self, request_id, value):
        return self.cas.put(self.principal, self.namespace(request_id), "operator", canonical(value),
                            quota_bytes=self.quota, max_object_bytes=64 * 1024**2)

    def _json(self, request_id, ref):
        return self.cas.json(self.principal, self.namespace(request_id), ref)

    def _row(self, request_id, *, active=False, now=None):
        row = self.db.connection.execute("SELECT * FROM provisioning WHERE id=?",
                                         (request_id,)).fetchone()
        require(row is not None, "REQUEST_MISSING")
        if active:
            require((time.time() if now is None else now) < row["expires"], "REQUEST_EXPIRED")
        return row

    def resolve_candidate(self, request_id: str, target: str, *, now=None):
        require(target in TARGETS, "CAPABILITY_MISSING")
        now = time.time() if now is None else now
        # Canonical validation also checks opaque request ID before any filesystem use.
        candidate = PackLock.model_validate({"schema": "mcbench/PackLock/1",
            "is_example": self.simulation, "lock_id": request_id, "status": "candidate",
            "provider": "curseforge", **TARGETS[target], "distribution_refs": [],
            "resolved_inventory": None, "installed_root_digest": None, "java": None,
            "launcher": None, "launch_profile": None, "expert_assertions": None,
            "harness_additions": [], "acquisition_report": None, "sealed_at": None})
        with self.db.transaction() as db:
            old = db.execute("SELECT target FROM provisioning WHERE id=?", (request_id,)).fetchone()
            if old:
                require(old["target"] == target, "IDEMPOTENCY_CONFLICT")
            else:
                db.execute("INSERT INTO provisioning VALUES(?,?,?,?,?,NULL,NULL,NULL)",
                           (request_id, target, "RESOLVED", now, now + 7 * 86400))
                self.db.event(db, "pack.resolved", candidate.model_dump())
        return candidate

    def request_acquisition(self, request_id, *, now=None):
        row = self._row(request_id, active=True, now=now)
        target = TARGETS[row["target"]]
        with self.db.transaction() as db:
            db.execute("UPDATE provisioning SET state='AWAITING_ARTIFACT' "
                       "WHERE id=? AND state='RESOLVED'", (request_id,))
        return {"request_id": request_id, "state": self.status(request_id)["state"],
                "provider": "curseforge", "target": target,
                "action": "Use the official CurseForge app/site in dedicated directories; "
                "retain exact distributions and import acquisition receipts.",
                "download_started": False, "terms_accepted": False,
                "attempt_timeout_s": 1800, "expires_unix": row["expires"]}

    def import_acquisition_receipt(self, receipt: AcquisitionReceipt):
        request_id = receipt.request_id
        row = self._row(request_id, active=True)
        require(receipt.is_example == self.simulation, "EXAMPLE_NOT_EXECUTABLE")
        require(receipt.target == row["target"], "RELEASE_MISMATCH")
        require({d.role for d in receipt.distributions} == {"client", "server"}, "ROLE_MISMATCH")
        if row["receipt"]:
            require(self._json(request_id, row["receipt"])["receipt"] == receipt.model_dump(),
                    "IDEMPOTENCY_CONFLICT")
            return row["receipt"]
        require(row["state"] in {"RESOLVED", "AWAITING_ARTIFACT"}, "INVALID_TRANSITION")
        self._json(request_id, receipt.official_workflow_evidence)
        source_verification = None
        if isinstance(receipt, VanillaAcquisitionReceipt):
            from .vanilla_artifacts import distribution, metadata
            source_verification = metadata(
                self.cas.read(self.principal, self.namespace(request_id), receipt.vanilla_manifest,
                              max_bytes=4 * 1024**2),
                self.cas.read(self.principal, self.namespace(request_id), receipt.vanilla_version_metadata,
                              max_bytes=2 * 1024**2))
            source_verification["distributions"] = [distribution(item, source_verification["downloads"][item.role])
                                                    for item in receipt.distributions]
            source_verification.update(installed_roles_qualified=False, game_conformance_claim=None,
                                       metadata_authority="operator-retained-official-manifest")
        distributions = []
        for item in receipt.distributions:
            official_origin(item.origin, receipt.target, item.role, item.file_id)
            self._json(request_id, item.evidence_ref)
            path = Path(item.path)
            require(path.is_absolute(), "UNSAFE_PATH")
            require(file_hash(path) == item.sha256, "HASH_MISMATCH")
            archive = inspect_archive(path, reviewed_world_paths=reviewed_vendor_paths(
                receipt.target, archive=True)) if receipt.target == "e9e" else None
            if receipt.target == "e9e" and item.role == "client":
                self._verify_client_manifest(path)
            ref = self.cas.put_file(self.principal, self.namespace(request_id), "operator", path,
                                   item.sha256, quota_bytes=self.quota, max_object_bytes=8 * 1024**3)
            distributions.append({"role": item.role, "ref": ref, "archive": archive})
        imported = {"schema": "strata/AcquisitionImport/1",
                    "receipt": receipt.model_dump(), "distributions": distributions}
        if source_verification is not None:
            imported["source_verification"] = source_verification
        ref = self._put(request_id, imported)
        with self.db.transaction() as db:
            current = db.execute("SELECT receipt FROM provisioning WHERE id=?", (request_id,)).fetchone()
            require(current[0] in (None, ref), "IDEMPOTENCY_CONFLICT")
            if current[0] is None:
                db.execute("UPDATE provisioning SET receipt=?,state='ACQUIRED' WHERE id=?",
                           (ref, request_id))
                self.db.event(db, "pack.acquired", {"request_id": request_id, "receipt": ref})
        return ref

    @staticmethod
    def _verify_client_manifest(path):
        import zipfile
        with zipfile.ZipFile(path) as archive:
            require("manifest.json" in archive.namelist(), "MANIFEST_MISSING")
            require(archive.getinfo("manifest.json").file_size <= 4 * 1024**2, "ARTIFACT_QUOTA")
            manifest = json.loads(archive.read("manifest.json"))
        require(manifest.get("manifestType") == "minecraftModpack" and
                manifest.get("manifestVersion") == 1, "SCHEMA_UNSUPPORTED")
        require(manifest.get("version") == "1.27.0" and
                manifest.get("minecraft", {}).get("version") == "1.19.2", "RELEASE_MISMATCH")
        require(manifest["minecraft"].get("modLoaders") == [
            {"id": "forge-43.4.23", "primary": True}], "RELEASE_MISMATCH")
        require(isinstance(manifest.get("files"), list) and bool(manifest["files"]),
                "MANIFEST_MISSING")

    def verify_inventory(self, request_id, roles: list[RoleInventoryInput]):
        row = self._row(request_id, active=True)
        require(row["state"] in {"ACQUIRED", "VERIFIED"}, "INVALID_TRANSITION")
        require(len(roles) == 2 and {r.role for r in roles} == {"client", "server"}, "ROLE_MISMATCH")
        entries, role_evidence, prepared = [], [], []
        reviewed = reviewed_vendor_paths(row["target"])
        for role in sorted(roles, key=lambda r: r.role):
            root = Path(role.root)
            require(root.is_absolute(), "UNSAFE_PATH")
            require(not self.cas.root.is_relative_to(root), "UNSAFE_PATH")
            self._json(request_id, role.provenance_evidence)
            self._json(request_id, role.exclusions_evidence)
            scanned = scan_tree(root, max_bytes=self.quota, reviewed_world_paths=reviewed)
            declared = sorted(role.files, key=lambda f: f.path)
            require(len(declared) == len(scanned), "INCOMPLETE_INVENTORY")
            for actual, entry in zip(scanned, declared, strict=True):
                require(entry.role == role.role and entry.layer in {"resolved", "harness"},
                        "ROLE_MISMATCH")
                template_path(entry.path, reviewed_world_paths=reviewed)
                require(actual == {k: getattr(entry, k) for k in ("path", "digest", "bytes")},
                        "HASH_MISMATCH")
                require(bool(entry.origin) and bool(entry.license_ref), "PROVENANCE_MISSING")
            prepared.append((role, root, scanned, declared))
        # Validate BOTH roles completely before consuming storage or journaling
        # any installed file. A known missing provenance field in the second
        # role must not leave thousands of imported assets from the first.
        for role, root, scanned, declared in prepared:
            for entry in declared:
                self.cas.put_file(self.principal, self.namespace(request_id), "operator",
                                  root / entry.path, entry.digest, quota_bytes=self.quota,
                                  max_object_bytes=8 * 1024**3)
                entries.append(entry.model_dump())
            # A stopped-source contract plus a second complete scan catches changed,
            # added or removed files while copying; no partially frozen template.
            require(scan_tree(root, max_bytes=self.quota, reviewed_world_paths=reviewed) == scanned,
                    "SOURCE_CHANGED")
            role_evidence.append({"role": role.role, "provenance": role.provenance_evidence,
                                  "exclusions": role.exclusions_evidence})
        inventory = {"schema": "strata/InstalledInventory/1", "is_example": self.simulation,
                     "files": entries, "role_evidence": role_evidence}
        ref = self._put(request_id, inventory)
        with self.db.transaction() as db:
            current = db.execute("SELECT state,inventory FROM provisioning WHERE id=?",
                                 (request_id,)).fetchone()
            require(current[0] in {"ACQUIRED", "VERIFIED"}, "INVALID_TRANSITION")
            require(current[1] in (None, ref), "IDEMPOTENCY_CONFLICT")
            db.execute("UPDATE provisioning SET inventory=?,state='VERIFIED' WHERE id=?",
                       (ref, request_id))
            self.db.event(db, "pack.inventory_verified", {"request_id": request_id, "ref": ref})
        return ref

    def _vanilla_distribution(self, request_id, role):
        """Recheck the durable acquisition without reopening its old source paths."""
        import hashlib
        from .vanilla_artifacts import metadata

        row = self._row(request_id, active=True)
        require(row["target"] == "vanilla" and row["state"] in {"ACQUIRED", "VERIFIED", "SEALED"},
                "INVALID_TRANSITION")
        imported = self._json(request_id, row["receipt"])
        receipt = parse_acquisition(imported["receipt"])
        require(isinstance(receipt, VanillaAcquisitionReceipt) and receipt.request_id == request_id
                and receipt.is_example == self.simulation, "VANILLA_SOURCE_VERIFICATION_REQUIRED")
        namespace = self.namespace(request_id)
        version_raw = self.cas.read(self.principal, namespace, receipt.vanilla_version_metadata, max_bytes=2 * 1024**2)
        source = metadata(self.cas.read(self.principal, namespace, receipt.vanilla_manifest, max_bytes=4 * 1024**2),
                          version_raw)
        require({item.role for item in receipt.distributions} == {"client", "server"}, "ROLE_MISMATCH")
        selected = next(item for item in receipt.distributions if item.role == role)
        require(selected.origin == source["downloads"][role]["url"] and selected.file_id is None,
                "VANILLA_DISTRIBUTION_SOURCE")
        artifacts = [item for item in imported["distributions"] if item["role"] == role]
        require(len(artifacts) == 1 and artifacts[0]["ref"] == "cas:sha256:" + selected.sha256,
                "VANILLA_DISTRIBUTION_MISMATCH")
        raw = self.cas.read(self.principal, namespace, artifacts[0]["ref"], max_bytes=512 * 1024**2)
        require(len(raw) == source["downloads"][role]["bytes"] and
                hashlib.sha1(raw).hexdigest() == source["downloads"][role]["sha1"],
                "VANILLA_DISTRIBUTION_MISMATCH")
        binding = {"is_example": self.simulation, "request_id": request_id,
                   "acquisition_receipt": row["receipt"], "distribution_ref": artifacts[0]["ref"],
                   "source_verification": source}
        return raw, version_raw, binding

    def prepare_vanilla_server(self, request_id, root: Path, destination: Path):
        """Join exact installed server payloads to the durable acquired distribution."""
        from .vanilla_runtime import prepare_server
        raw, _, binding = self._vanilla_distribution(request_id, "server")
        require(not destination.is_relative_to(self.cas.root) and not self.cas.root.is_relative_to(destination),
                "UNSAFE_PATH")
        result = prepare_server(raw, root, destination)
        result.update(schema="strata/VanillaServerSoftware/1", **binding)
        return {"evidence": self._put(request_id, result), **result}

    def prepare_vanilla_client(self, request_id, assets: Path, library_roots: list[Path], destination: Path):
        """Prepare the exact acquired Windows client and its metadata-selected inputs."""
        from .vanilla_client import prepare_client
        raw, version_raw, binding = self._vanilla_distribution(request_id, "client")
        require(not destination.is_relative_to(self.cas.root) and not self.cas.root.is_relative_to(destination),
                "UNSAFE_PATH")
        result = prepare_client(raw, version_raw, assets, library_roots, destination)
        result.update(schema="strata/VanillaClientSoftware/1", **binding)
        return {"evidence": self._put(request_id, result), **result}

    def seal_template(self, request_id, launch: LaunchProfile, evidence: ProvisioningEvidence):
        row = self._row(request_id, active=True)
        require(row["state"] in {"VERIFIED", "SEALED"}, "INVALID_TRANSITION")
        require(launch.is_example == evidence.is_example == self.simulation,
                "EXAMPLE_NOT_EXECUTABLE")
        require(evidence.request_id == request_id, "SCOPE_MISMATCH")
        require(evidence.inventory_digest == row["inventory"][11:] and
                evidence.receipt_digest == row["receipt"][11:] and
                evidence.launch_profile_digest == digest(launch.model_dump()), "HASH_MISMATCH")
        checks = PROVISION_CHECKS | (EXPERT_CHECKS if row["target"] == "e9e" else set())
        require(set(evidence.checks) == checks, "PROVISIONING_UNVERIFIED")
        for check, ref in evidence.checks.items():
            proof = ProvisioningCheck.model_validate(self._json(request_id, ref))
            require(proof.is_example == self.simulation, "EVIDENCE_PROFILE_MISMATCH")
            require(proof.result == "pass" and proof.request_id == request_id and
                    proof.check_id == check and proof.inventory_digest == evidence.inventory_digest
                    and proof.receipt_digest == evidence.receipt_digest and
                    proof.launch_profile_digest == evidence.launch_profile_digest,
                    "PROVISIONING_UNVERIFIED")
            for raw in proof.evidence_refs:
                self.cas.read(self.principal, self.namespace(request_id), raw)
        for command in (launch.client, launch.server):
            require(command.working_directory == "." or
                    bool(template_path(command.working_directory)), "UNSAFE_PATH")
            validate_launch_environment(command.environment)
            require(all("\x00" not in arg for arg in command.arguments), "INVALID_ARGUMENT")
            executable = Path(command.executable_path)
            require(executable.is_absolute(), "UNSAFE_PATH")
            require(file_hash(executable) == command.executable.digest, "HASH_MISMATCH")
            self._json(request_id, command.reviewed_bootstrap)
        imported = self._json(request_id, row["receipt"])
        receipt = parse_acquisition(imported["receipt"])
        inventory = self._json(request_id, row["inventory"])
        launch_ref = self._put(request_id, launch.model_dump())
        evidence_ref = self._put(request_id, evidence.model_dump())
        if row["sealed"]:
            old = PackLock.model_validate(self._json(request_id, row["sealed"]))
            report = self._json(request_id, old.acquisition_report)
            require(old.launch_profile == launch_ref and report["evidence"] == evidence_ref,
                    "IDEMPOTENCY_CONFLICT")
            return row["sealed"]
        report = self._put(request_id, {"schema": "strata/AcquisitionReport/1",
            "is_example": self.simulation, "receipt": row["receipt"], "evidence": evidence_ref,
            "inventory": row["inventory"], "support_stage": "template_sealed",
            "authority": "operator_attestation", "game_conformance_claim": None})
        lock = PackLock.model_validate({"schema": "mcbench/PackLock/1",
            "is_example": self.simulation, "lock_id": request_id, "status": "sealed",
            "provider": "curseforge", **TARGETS[row["target"]],
            "distribution_refs": [a["ref"] for a in imported["distributions"]],
            "resolved_inventory": row["inventory"], "installed_root_digest": digest(inventory),
            "java": receipt.java, "launcher": receipt.launcher, "launch_profile": launch_ref,
            "expert_assertions": evidence_ref if row["target"] == "e9e" else None,
            "harness_additions": ["cas:sha256:" + f["digest"] for f in inventory["files"]
                                  if f["layer"] == "harness"],
            "acquisition_report": report, "sealed_at": datetime.now(UTC).isoformat().replace(
                "+00:00", "Z")})
        lock_ref = self._put(request_id, lock.model_dump())
        with self.db.transaction() as db:
            current = db.execute("SELECT sealed FROM provisioning WHERE id=?", (request_id,)).fetchone()
            require(current[0] is None, "IDEMPOTENCY_CONFLICT")
            db.execute("UPDATE provisioning SET sealed=?,state='SEALED' WHERE id=?",
                       (lock_ref, request_id))
            self.db.event(db, "pack.sealed", {"request_id": request_id, "lock": lock_ref})
        return lock_ref

    def materialize(self, request_id, destination: Path):
        row = self._row(request_id)
        require(row["state"] == "SEALED", "UNSEALED_PACK")
        lock = PackLock.model_validate(self._json(request_id, row["sealed"]))
        require(lock.is_example == self.simulation, "EXAMPLE_NOT_EXECUTABLE")
        inventory = self._json(request_id, lock.resolved_inventory)
        require(digest(inventory) == lock.installed_root_digest, "CORRUPT_EVIDENCE")
        destination = destination.absolute()
        reject_links(destination)
        require(not destination.exists(), "DESTINATION_EXISTS")
        require(not destination.is_relative_to(self.cas.root), "UNSAFE_PATH")
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".strata-instance-", dir=destination.parent))
        reviewed = reviewed_vendor_paths(row["target"])
        try:
            for entry in inventory["files"]:
                relative = template_path(entry["path"], reviewed_world_paths=reviewed)
                if entry["path"] in reviewed:
                    require(entry["digest"] == reviewed[entry["path"]], "VENDOR_CONTENT_MISMATCH")
                require(entry["role"] in {"client", "server"}, "ROLE_MISMATCH")
                path = staging / entry["role"] / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                self.cas.copy_to(self.principal, self.namespace(request_id),
                                 "cas:sha256:" + entry["digest"], path)
            marker = {"schema": "strata/Materialization/1", "is_example": self.simulation,
                      "lock": row["sealed"], "inventory_digest": lock.installed_root_digest}
            with (staging / ".strata-instance.json").open("xb") as stream:
                stream.write(canonical(marker))
                stream.flush()
                os.fsync(stream.fileno())
            require(not destination.exists(), "DESTINATION_EXISTS")
            # Windows rename refuses existing destination, preserving personal instances.
            staging.rename(destination)
        finally:
            if staging.exists():
                require(staging.parent == destination.parent and
                        staging.name.startswith(".strata-instance-"), "UNSAFE_PATH")
                shutil.rmtree(staging)
        with self.db.transaction() as db:
            self.db.event(db, "pack.materialized", marker)
        return marker

    def status(self, request_id):
        row = self._row(request_id)
        return {"request_id": row["id"], "target": row["target"], "state": row["state"],
                "receipt": row["receipt"], "inventory": row["inventory"], "lock": row["sealed"],
                "is_example": self.simulation, "game_conformance_claim": None}
