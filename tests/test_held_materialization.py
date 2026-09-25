"""Synthetic sealed vanilla profile; real Windows custody and authority reads."""

import json
import os
from pathlib import Path

import pytest

from mcbench.launch_integrity import FileLease, IntegrityError, snapshot
from mcbench.pack_launch import _resolve_held_materialization, resolve_pack_launch
from mcbench.storage import Fault
from test_pack_restore import source, inputs, candidate, installed, sealed_installation

(source, inputs, candidate, installed, sealed_installation) = (
    source, inputs, candidate, installed, sealed_installation)
pytestmark = [pytest.mark.skipif(os.name != "nt", reason="Windows held-file custody"),
              pytest.mark.parametrize("source", [True], indirect=True)]


def held(binding, *, executable=True):
    resolved = resolve_pack_launch(binding, "server")
    files = [Path(resolved["launch"]["executable_path"])] if executable else []
    return resolved, FileLease(snapshot(files, [Path(binding.instance)]))


def test_held_rechecks_match_public_resolution_without_reopening_file_hashes(source, monkeypatch):
    from mcbench import inventory, pack_launch
    binding, _, service = source
    expected, lease = held(binding)
    with lease:
        def no_hash(*args, **kwargs):
            pytest.fail("held immutable bytes rehashed by path")
        monkeypatch.setattr(inventory, "file_hash", no_hash)
        monkeypatch.setattr(pack_launch, "file_hash", no_hash)
        assert _resolve_held_materialization(binding, lease) == expected
        for path in (Path(binding.instance) / "server/server.jar", Path(binding.instance) / ".strata-instance.json",
                     Path(expected["launch"]["executable_path"])):
            with pytest.raises(PermissionError):
                with path.open("ab"):
                    pass
        assert _resolve_held_materialization(binding, lease) == expected
        service.db.connection.execute("UPDATE provisioning SET state='VERIFIED'")
        with pytest.raises(Fault, match="UNSEALED_PACK"):
            _resolve_held_materialization(binding, lease)
    with pytest.raises(IntegrityError, match="BOOTSTRAP_LEASE_CLOSED"):
        _resolve_held_materialization(binding, lease)


@pytest.mark.parametrize("change", ["extra_directory", "missing_empty_directory", "root_directory", "file",
                                     "simulation", "lock", "target", "launch_blob", "visibility"])
def test_held_resolution_rechecks_complete_layout_and_current_authority(source, change):
    binding, _, service = source
    _, lease = held(binding)
    with lease:
        root = Path(binding.instance)
        if change == "extra_directory":
            (root / "client/extra").mkdir()
        elif change == "missing_empty_directory":
            (root / "server/java/empty").rmdir()
        elif change == "root_directory":
            (root / "extra").mkdir()
        elif change == "file":
            (root / "server/extra.txt").write_text("unreviewed")
        elif change == "simulation":
            service.db.connection.execute("UPDATE provisioning_profile SET simulation=1")
        elif change == "lock":
            service.db.connection.execute("UPDATE provisioning SET sealed=?", ("cas:sha256:" + "a" * 64,))
        elif change == "target":
            service.db.connection.execute("UPDATE provisioning SET target='e9e'")
        elif change == "visibility":
            service.db.connection.execute("UPDATE objects SET visibility='evaluator' WHERE ref=?", (binding.lock,))
        else:
            lock = json.loads((Path(binding.store) / "objects" / binding.lock[11:]).read_bytes())
            (Path(binding.store) / "objects" / lock["launch_profile"][11:]).write_bytes(b"corrupt")
        with pytest.raises((Fault, IntegrityError)):
            _resolve_held_materialization(binding, lease)


@pytest.mark.parametrize("scope", ["missing_executable", "foreign_tree", "closed", "untyped"])
def test_incomplete_or_foreign_custody_cannot_resolve(source, tmp_path, scope):
    binding, _, _ = source
    _, lease = held(binding, executable=scope != "missing_executable")
    with lease:
        if scope == "foreign_tree":
            other = tmp_path / "foreign"
            other.mkdir()
            (other / "file").write_bytes(b"foreign")
            with FileLease(snapshot([], [other])) as foreign:
                with pytest.raises(Fault, match="MATERIALIZATION_CUSTODY_SCOPE"):
                    _resolve_held_materialization(binding, foreign)
        else:
            if scope == "closed":
                lease.close()
            with pytest.raises((Fault, IntegrityError)):
                _resolve_held_materialization(binding, object() if scope == "untyped" else lease)


def test_held_bytes_still_have_to_match_sealed_inventory(source):
    binding, _, _ = source
    resolved = resolve_pack_launch(binding, "server")
    (Path(binding.instance) / "server/server.jar").write_bytes(b"new unapproved bytes")
    with FileLease(snapshot([Path(resolved["launch"]["executable_path"])], [Path(binding.instance)])) as lease:
        with pytest.raises(Fault, match="MATERIALIZATION_CHANGED"):
            _resolve_held_materialization(binding, lease)


def test_new_hardlink_is_denied_or_detected_while_bytes_are_held(source, tmp_path):
    binding, _, _ = source
    _, lease = held(binding)
    with lease:
        try:
            (tmp_path / "outside-alias").hardlink_to(Path(binding.instance) / "server/server.jar")
        except PermissionError:
            return  # The OS already refused the mutation under held custody.
        with pytest.raises(Fault, match="UNSAFE_PATH"):
            _resolve_held_materialization(binding, lease)
