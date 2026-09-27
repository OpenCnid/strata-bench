"""Registered synthetic probe worlds, real immutable leases and stopped captures."""

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.pack_launch import RestoredPackLaunchBinding
from mcbench.pack_restore import load_restoration
from mcbench.storage import Fault, canonical, digest
from mcbench.vanilla_persistence import (
    MUTABLE,
    RegisteredProbeWorld,
    VanillaPersistence,
    verify_snapshot,
)
from test_vanilla_persistence import installed, sealed_installation, stopped

installed, sealed_installation = installed, sealed_installation


@pytest.fixture
def registered(sealed_installation, installed):
    root, binding, resolved, external = sealed_installation
    for name in [*MUTABLE, "world/level.dat"]:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((installed / name).read_bytes())
    (root / "world/datapacks").mkdir()
    files = {
        (name if name.startswith("world/") else "external/" + name): "cas:sha256:"
        + hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in [*MUTABLE, "world/level.dat"]
    }
    directories = ["external", "world", "world/datapacks"]
    value = {
        "schema": "strata/RegisteredProbeVanillaWorld/1",
        "namespace": "evaluation:test",
        "pair_id": "pair1",
        "arm": "initial",
        "fixture_ref": "cas:sha256:" + "a" * 64,
        "pack_lock": binding.lock,
        "pair_plan_digest": "b" * 64,
        "world_digest": digest(
            {"pack_lock": binding.lock, "files": files, "directories": directories}
        ),
        "world_files": files,
        "world_directories": directories,
    }
    return root, binding, resolved, external, value


def test_probe_snapshot_keeps_initial_provenance_and_cannot_restore_into_campaign(
    registered, tmp_path
):
    root, binding, resolved, external, value = registered
    service = VanillaPersistence(root, pack=binding, resolved=resolved, probe_world=value)
    try:
        with pytest.raises(PermissionError):
            (external / "release").write_bytes(b"changed immutable java")
        (root / "world/session.lock").write_bytes(b"fresh game lock")
        (root / "world/level.dat").write_bytes(b"changed probe outcome")
        receipt = service.capture(tmp_path / "probe-export", stopped(), plan_digest="c" * 64)
        body = verify_snapshot(Path(receipt["path"]), receipt["manifest_sha256"])
        assert body["schema"] == "strata/StoppedVanillaSnapshot/3"
        assert body["policy"] == "vanilla1192-registered-probe-stopped-instance/1"
        assert body["probe_world"] == value
        assert (
            body["files"]["world/level.dat"]["sha256"]
            != value["world_files"]["world/level.dat"][11:]
        )
        assert not body["dispatch_authorized"] and not body["complete_checkpoint"]
        forbidden = RestoredPackLaunchBinding(
            **(binding.model_dump() | {"instance": str(tmp_path / "campaign-copy")}),
            restoration={
                "snapshot": str(tmp_path / "probe-export"),
                "sha256": receipt["manifest_sha256"],
            },
        )
        with pytest.raises(Fault, match="PROBE_FEEDBACK_FORBIDDEN"):
            load_restoration(forbidden, body["installed_inventory"])
    finally:
        service.close()


@pytest.mark.parametrize(
    "change", ["state", "extra", "empty_directory", "session_lock", "immutable", "pack"]
)
def test_registered_initial_state_must_match_before_capture_custody(registered, change):
    root, binding, resolved, _, value = registered
    if change == "state":
        (root / "world/level.dat").write_bytes(b"changed input")
    elif change == "extra":
        (root / "world/level.dat_old").write_bytes(b"undeclared state")
    elif change == "empty_directory":
        (root / "world/data").mkdir()
    elif change == "session_lock":
        (root / "world/session.lock").write_bytes(b"old session")
    elif change == "immutable":
        (root / "eula.txt").write_bytes(b"changed immutable")
    else:
        value["pack_lock"] = "cas:sha256:" + "d" * 64
        value["world_digest"] = digest(
            {
                "pack_lock": value["pack_lock"],
                "files": value["world_files"],
                "directories": value["world_directories"],
            }
        )
    with pytest.raises(
        Fault, match="PROBE_WORLD_CHANGED|VANILLA_TEMPLATE_CHANGED|PROBE_WORLD_PROFILE"
    ):
        VanillaPersistence(root, pack=binding, resolved=resolved, probe_world=value)


@pytest.mark.parametrize(
    "change",
    ["digest", "directory", "namespace", "incomplete", "session_lock", "collision", "spelling"],
)
def test_probe_provenance_rejects_unbound_or_incomplete_identity(registered, change):
    *_, value = registered
    if change == "digest":
        value["world_digest"] = "f" * 64
    else:
        if change == "directory":
            value["world_directories"].append("world/datapacks/.aws")
        elif change == "namespace":
            value["namespace"] = "operator"
        elif change == "incomplete":
            del value["world_files"]["external/ops.json"]
        elif change == "collision":
            value["world_files"]["world/data/item"] = "cas:sha256:" + "a" * 64
            value["world_directories"] = sorted(
                [*value["world_directories"], "world/data", "world/data/item"]
            )
        elif change == "spelling":
            value["world_files"]["world/LEVEL.dat"] = value["world_files"]["world/level.dat"]
        else:
            value["world_files"]["world/session.lock"] = "cas:sha256:" + "a" * 64
        value["world_digest"] = digest(
            {
                "pack_lock": value["pack_lock"],
                "files": value["world_files"],
                "directories": value["world_directories"],
            }
        )
    with pytest.raises(ValidationError):
        RegisteredProbeWorld.model_validate(value)


def test_stopped_capture_limit_refuses_before_output_copy(registered, tmp_path):
    root, binding, resolved, _, value = registered
    service = VanillaPersistence(
        root, pack=binding, resolved=resolved, probe_world=value, capture_state_limit=1
    )
    try:
        (root / "world/session.lock").write_bytes(b"fresh")
        with pytest.raises(Fault, match="VANILLA_CAPTURE_QUOTA"):
            service.capture(tmp_path / "too-large", stopped(), plan_digest="c" * 64)
        assert not (tmp_path / "too-large").exists()
    finally:
        service.close()


def test_probe_export_cannot_drop_its_provenance_but_keep_version3(registered, tmp_path):
    root, binding, resolved, _, value = registered
    service = VanillaPersistence(root, pack=binding, resolved=resolved, probe_world=value)
    try:
        (root / "world/session.lock").write_bytes(b"fresh")
        receipt = service.capture(tmp_path / "export", stopped(), plan_digest="c" * 64)
        body = verify_snapshot(Path(receipt["path"]), receipt["manifest_sha256"])
        del body["probe_world"]
        raw = canonical(body)
        (Path(receipt["path"]) / "manifest.json").write_bytes(raw)
        with pytest.raises(Fault, match="VANILLA_CAPTURE_MANIFEST"):
            verify_snapshot(Path(receipt["path"]), hashlib.sha256(raw).hexdigest())
    finally:
        service.close()
