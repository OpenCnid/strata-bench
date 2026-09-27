"""Synthetic profile/runtime and real Windows leases; no game/provider dispatch."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench import inventory, pack_launch, pack_worker
from mcbench.launch_integrity import FileLease, IntegrityError, safe, snapshot
from mcbench.pack_launch import resolve_pack_launch
from mcbench.pack_worker import HeldPackWorker
from mcbench.storage import Fault
from test_pack_worker import inputs, candidate, pack

inputs, candidate, pack = inputs, candidate, pack
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows file custody")


def custody(binding):
    return FileLease(snapshot([], [Path(binding.instance)]))


def forbidden(*args, **kwargs):
    pytest.fail("unexpected process dispatch")


def test_workers_borrow_only_materialization_keep_separate_runtime_and_config(pack, tmp_path, monkeypatch):
    binding, invocation, _ = pack
    expected = resolve_pack_launch(binding, "client", worker_invocation=invocation)
    monkeypatch.setattr(pack_worker, "ManagedProcess", forbidden)
    root = safe(binding.instance)
    hashed, executable_hashes = [], []
    original_hash, launch_hash = inventory.file_hash, pack_launch.file_hash

    def hash_outside_materialization(path):
        assert not safe(path).is_relative_to(root)
        hashed.append(str(path))
        return original_hash(path)

    def hash_executable(path):
        executable_hashes.append(str(path))
        return launch_hash(path)

    (tmp_path / "second-state").mkdir()
    second_invocation = invocation | {"agent_id": "avatar-2", "lease_id": "lease-2",
        "state_directory": str(tmp_path / "second-state"),
        "configuration_path": str(tmp_path / "second.json")}
    with custody(binding) as lease:
        monkeypatch.setattr(inventory, "file_hash", hash_outside_materialization)
        monkeypatch.setattr(pack_launch, "file_hash", hash_executable)
        with HeldPackWorker(binding, invocation, defer_configuration=True,
                            _materialization_lease=lease) as first:
            assert first.resolved == expected
            with HeldPackWorker(binding, second_invocation, defer_configuration=True,
                                _materialization_lease=lease) as second:
                assert first.runtime is not second.runtime
                assert first._materialization_lease is second._materialization_lease is lease
                assert not Path(invocation["configuration_path"]).exists()
                first.commit_configuration()
                second.commit_configuration()
                assert first.config_lease is not second.config_lease
                assert first.resolved["worker_configuration_sha256"] != second.resolved["worker_configuration_sha256"]
                node = Path(first.runtime.body["node"])
                raw = node.read_bytes()
                with pytest.raises(PermissionError):
                    node.write_bytes(raw)
            first.runtime.recheck()
            lease.recheck()
        # Child release must not close the borrowed software owner's handles.
        lease.recheck()
        node.write_bytes(raw)
        with pytest.raises(PermissionError):
            (root / "server/server.properties").write_bytes(b"changed")
    assert executable_hashes == [expected["launch"]["executable_path"]] * 2
    assert all(not safe(p).is_relative_to(root) for p in hashed)


@pytest.mark.parametrize("failure", ["closed", "foreign", "untyped", "simulation", "own_server",
                                    "revoked", "extra_file", "extra_directory", "runtime"])
def test_invalid_borrowed_worker_refuses_before_config_or_process(pack, candidate, tmp_path, monkeypatch, failure):
    binding, invocation, profile = pack
    monkeypatch.setattr(pack_worker, "ManagedProcess", forbidden)
    if failure == "foreign":
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        (foreign / "file").write_bytes(b"foreign")
    with (FileLease(snapshot([], [foreign])) if failure == "foreign" else custody(binding)) as lease:
        selected = lease
        if failure == "closed":
            lease.close()
        elif failure == "untyped":
            selected = object()
        elif failure == "revoked":
            candidate[0].db.connection.execute("UPDATE provisioning SET state='VERIFIED'")
        elif failure == "extra_file":
            (Path(binding.instance) / "client/extra").write_bytes(b"unreviewed")
        elif failure == "extra_directory":
            (Path(binding.instance) / "client/extra").mkdir()
        elif failure == "runtime":
            import json
            body = json.loads(Path(profile.worker_runtime.path).read_bytes())
            Path(body["worker"]).write_bytes(b"unapproved runtime")
        with pytest.raises((Fault, IntegrityError)):
            with HeldPackWorker(binding, invocation, _materialization_lease=selected,
                                simulation=failure == "simulation", own_server=failure == "own_server"):
                pytest.fail("invalid custody accepted")
        assert not Path(invocation["configuration_path"]).exists()
        if failure not in ("closed", "extra_file"):
            lease.recheck()


@pytest.mark.parametrize("boundary", ["commit", "import", "worker", "receipt"])
@pytest.mark.parametrize("failure", ["closed", "new_file"])
def test_borrowed_owner_loss_refuses_later_effects_and_receipts(pack, monkeypatch, boundary, failure):
    binding, invocation, _ = pack
    monkeypatch.setattr(pack_worker, "ManagedProcess", forbidden)
    with custody(binding) as lease:
        with HeldPackWorker(binding, invocation, defer_configuration=True,
                            _materialization_lease=lease) as worker:
            if boundary != "commit":
                worker.commit_configuration()
            if boundary == "receipt":
                worker.processes["preflight"] = SimpleNamespace(poll=lambda: 0, job=SimpleNamespace(
                    accounting=lambda: {"active_processes": 0, "terminated_processes": 0, "total_processes": 1}))
            if failure == "closed":
                lease.close()
            else:
                (Path(binding.instance) / "client/extra").write_bytes(b"unreviewed")
            action = {"commit": worker.commit_configuration, "import": lambda: worker.start(preflight=True),
                      "worker": worker.start, "receipt": worker.receipt}[boundary]
            with pytest.raises(IntegrityError):
                action()
            if boundary == "commit":
                assert not Path(invocation["configuration_path"]).exists()


def test_private_server_entry_cannot_drop_its_required_custody(pack):
    with pytest.raises(Fault, match="MATERIALIZATION_CUSTODY_REQUIRED"):
        pack_launch._resolve_held_materialization(pack[0], None)
