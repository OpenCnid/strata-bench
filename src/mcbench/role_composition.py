"""Bounded operator composition of initial E9E roles for inventory admission.

The operator supplies reviewed FileEntry provenance and explicit source paths.
This is a copy/consistency boundary, not an authority for arbitrary license or
effective-config claims. Source reports and dispositions remain private.
"""

import hashlib
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .contracts import Ref, Strict
from .inventory import file_hash, scan_tree, template_path
from .pack_modes import inspect_e9e_mode
from .pack_policies import reviewed_vendor_paths
from .records import FileEntry
from .storage import reject_links, require


class RoleSourceFile(Strict):
    source: str
    entry: FileEntry


class RoleSources(Strict):
    role: Literal["client", "server"]
    files: Annotated[list[RoleSourceFile], Field(min_length=1, max_length=24000)]
    directories: Annotated[list[str], Field(max_length=12000)]


class E9ERoleComposition(Strict):
    schema_: Literal["strata/E9ERoleComposition/1"] = Field(alias="schema")
    request_id: str
    acquisition_receipt: Ref
    source_reports: Annotated[list[Ref], Field(min_length=1, max_length=32)]
    component_notices: Ref
    exclusions: Ref
    roles: Annotated[list[RoleSources], Field(min_length=2, max_length=2)]


def prepare_roles(plan: E9ERoleComposition, destination: Path):
    """Validate both complete copy plans before any output; retain partial failure."""
    require(destination.is_absolute() and destination == destination.resolve(), "UNSAFE_PATH")
    reject_links(destination)
    require(not destination.exists(), "DESTINATION_EXISTS")
    require({r.role for r in plan.roles} == {"client", "server"}, "ROLE_MISMATCH")
    reviewed = reviewed_vendor_paths("e9e")
    total = 0
    for role in plan.roles:
        paths = set()
        for item in role.files:
            entry, source = item.entry, Path(item.source)
            require(entry.role == role.role and entry.layer in {"resolved", "harness"}, "ROLE_MISMATCH")
            template_path(entry.path, reviewed_world_paths=reviewed)
            require(entry.path.casefold() not in paths, "PATH_COLLISION")
            paths.add(entry.path.casefold())
            require(source.is_absolute() and source == source.resolve() and
                    not source.is_relative_to(destination), "UNSAFE_PATH")
            reject_links(source)
            require(source.is_file() and source.stat().st_nlink == 1, "UNSAFE_PATH")
            total += entry.bytes
            require(total <= 4 * 1024**3 and entry.bytes <= 512 * 1024**2, "ARTIFACT_QUOTA")
            require(source.stat().st_size == entry.bytes and file_hash(source) == entry.digest, "SOURCE_CHANGED")
        directories = set()
        for name in role.directories:
            template_path(name, reviewed_world_paths=reviewed)
            require(name.casefold() not in paths | directories, "PATH_COLLISION")
            directories.add(name.casefold())
        # Detect a declared file used as another entry's parent before copying.
        for name in [x.entry.path for x in role.files] + role.directories:
            require(all(p.as_posix().casefold() not in paths for p in Path(name).parents if str(p) != "."), "PATH_COLLISION")
    destination.mkdir(parents=True, exist_ok=False)
    roles = []
    for role in sorted(plan.roles, key=lambda r: r.role):
        root = destination / role.role
        root.mkdir()
        for name in role.directories:
            (root / name).mkdir(parents=True, exist_ok=True)
        for item in sorted(role.files, key=lambda r: r.entry.path):
            entry, source = item.entry, Path(item.source)
            reject_links(source)
            target = root / entry.path
            target.parent.mkdir(parents=True, exist_ok=True)
            copied, sha = 0, hashlib.sha256()
            with source.open("rb") as stream, target.open("xb") as output:
                while chunk := stream.read(1024**2):
                    copied += len(chunk)
                    require(copied <= entry.bytes, "SOURCE_CHANGED")
                    sha.update(chunk)
                    output.write(chunk)
            require(copied == entry.bytes and sha.hexdigest() == entry.digest, "SOURCE_CHANGED")
        expected = sorted(({"path": x.entry.path, "digest": x.entry.digest, "bytes": x.entry.bytes}
                           for x in role.files), key=lambda r: r["path"])
        require(scan_tree(root, max_files=24000, max_bytes=4 * 1024**3,
                          reviewed_world_paths=reviewed) == expected, "ROLE_COMPOSITION_MISMATCH")
        for item in role.files:
            source = Path(item.source)
            reject_links(source)
            require(source.stat().st_nlink == 1 and file_hash(source) == item.entry.digest, "SOURCE_CHANGED")
        inspection = inspect_e9e_mode(root, role=role.role, effective=False)
        require(inspection["file_result"] == "pass", "INITIAL_EXPERT_SETUP_MISMATCH")
        roles.append({"role": role.role, "root": str(root), "files": [x.entry.model_dump() for x in role.files],
                      "initial_expert_setup": inspection, "directories": role.directories})
    return {"schema": "strata/PreparedE9ERoles/1", "roles": roles, "source_reports": plan.source_reports,
            "component_notices": plan.component_notices, "exclusions": plan.exclusions,
            "independent_copies_verified": True, "initial_roles_only": True,
            "effective_configuration_qualified": False, "launch_qualified": False,
            "license_certificate": False, "game_conformance_claim": None}
