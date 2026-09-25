"""Standalone role scans retain their own whole-lease checks."""

from pathlib import Path
import os

import pytest

from mcbench import inventory
from mcbench.launch_integrity import IntegrityError
from test_held_materialization import held
from test_pack_restore import source, inputs, candidate, installed, sealed_installation

(source, inputs, candidate, installed, sealed_installation) = (
    source, inputs, candidate, installed, sealed_installation)
pytestmark = [pytest.mark.skipif(os.name != "nt", reason="Windows held-file custody"),
              pytest.mark.parametrize("source", [True], indirect=True)]


@pytest.mark.parametrize("boundary", ["before", "after"])
@pytest.mark.parametrize("change", ["closed", "file"])
def test_standalone_role_scan_does_not_skip_its_own_custody(source, monkeypatch, boundary, change):
    binding, _, _ = source
    root = Path(binding.instance)
    expected = inventory.scan_layout(root / "server")
    _, lease = held(binding)
    original = inventory._scan_layout

    def mutate():
        if change == "closed":
            lease.close()
        else:
            # The changed file is outside the requested role but inside the
            # retained installation. Role-only scanning must not miss it.
            (root / "client/unreviewed.txt").write_bytes(b"new")

    def changed(path, **kwargs):
        result = original(path, **kwargs)
        mutate()
        return result

    with lease:
        assert inventory.scan_layout(root / "server", _lease=lease) == expected
        if boundary == "before":
            mutate()
        else:
            monkeypatch.setattr(inventory, "_scan_layout", changed)
        with pytest.raises(IntegrityError, match="BOOTSTRAP_LEASE_CLOSED|BOOTSTRAP_TREE_CHANGED"):
            inventory.scan_layout(root / "server", _lease=lease)
