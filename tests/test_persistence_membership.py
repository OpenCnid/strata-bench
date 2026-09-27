"""Synthetic templates with real Windows custody; no game or model dispatch."""
import os

import pytest

from mcbench import vanilla_persistence as persistence
from mcbench.launch_integrity import IntegrityError, snapshot
from mcbench.storage import Fault
from test_vanilla_persistence import installed, sealed_installation

(installed, sealed_installation) = (installed, sealed_installation)
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows retained-file custody")


def test_immutable_membership_matches_fresh_snapshot_and_releases_all_handles(sealed_installation):
    root, binding, resolved, external = sealed_installation
    service = persistence.VanillaPersistence(root, pack=binding, resolved=resolved)
    try:
        actual = service.lease.inventory
        expected = snapshot([e["path"] for e in actual["files"]], [t["path"] for t in actual["trees"]])
        assert actual["trees"] == expected["trees"]
        assert sorted(actual["files"], key=lambda e: e["path"]) == expected["files"]
        for path in (root / "server.jar", root / "libraries/library.jar", external / "release"):
            with pytest.raises(PermissionError):
                path.write_bytes(b"blocked under custody")
    finally:
        service.close()
    for path in (root / "server.jar", external / "release"):
        path.write_bytes(b"released")


@pytest.mark.parametrize("change", ["add", "remove", "bytes", "external-add"])
def test_changes_after_layout_cannot_enter_immutable_custody(sealed_installation, monkeypatch, change):
    root, binding, resolved, external = sealed_installation
    acquire = persistence._immutable_lease

    def mutate(selected, roots):
        if change == "remove":
            (root / "libraries/library.jar").unlink()
        elif change == "bytes":
            (root / "libraries/library.jar").write_bytes(b"different bytes after checked layout")
        else:
            target = external / "extra.dll" if change == "external-add" else root / "libraries/extra.jar"
            target.write_bytes(b"unselected bytes")
        return acquire(selected, roots)

    monkeypatch.setattr(persistence, "_immutable_lease", mutate)
    with pytest.raises((Fault, IntegrityError), match="VANILLA_TEMPLATE_CHANGED|BOOTSTRAP_FILE_CHANGED"):
        persistence.VanillaPersistence(root, pack=binding, resolved=resolved)
    # Any handles opened before discovering a changed byte must be released.
    for path in (root / "server.jar", external / "release"):
        path.write_bytes(b"released after refusal")


def test_file_added_after_enumeration_refuses_and_closes_partial_custody(sealed_installation, monkeypatch):
    root, binding, resolved, external = sealed_installation
    acquire = persistence.FileLease

    def mutate(inventory):
        assert str(persistence.safe(root / "libraries")) in {t["path"] for t in inventory["trees"]}
        (root / "libraries/late.jar").write_bytes(b"after enumeration")
        return acquire(inventory)

    monkeypatch.setattr(persistence, "FileLease", mutate)
    with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
        persistence.VanillaPersistence(root, pack=binding, resolved=resolved)
    for path in (root / "server.jar", external / "release"):
        path.write_bytes(b"released after failed acquisition")
