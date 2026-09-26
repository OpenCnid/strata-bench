"""Synthetic pinned files, actual Windows custody, no process/model dispatch."""

from pathlib import Path

import pytest

from mcbench.launch_integrity import IntegrityError
from mcbench.storage import Fault
from mcbench.worker_bundle import HeldWorkerRuntimePool, _held_worker_runtime
from test_worker_bundle import inputs, prepare

inputs = inputs


def reference(inputs):
    result = prepare(inputs)
    return {"path": result["manifest"], "sha256": result["sha256"]}


def test_runtime_borrow_keeps_owner_custody_until_all_members_close(inputs):
    ref = reference(inputs)
    with HeldWorkerRuntimePool() as pool:
        with _held_worker_runtime(ref, pool) as first:
            with _held_worker_runtime(ref, pool) as second:
                assert first is second
                with pytest.raises(PermissionError):
                    Path(first.body["node"]).write_bytes(b"changed")
            first.recheck()
            assert not first.lease.closed
        first.recheck()
        assert not first.lease.closed
    assert first.lease.closed
    Path(first.body["node"]).write_bytes(b"owner released")
    with pytest.raises(Fault, match="WORKER_RUNTIME_POOL_CLOSED"):
        pool.acquire(ref)
    with pytest.raises(Fault, match="WORKER_RUNTIME_POOL_CONSUMED"):
        pool.__enter__()


@pytest.mark.parametrize("change", ["membership", "lease_closed", "reference", "runtime_reference"])
def test_changed_or_closed_custody_cannot_be_borrowed(inputs, change):
    ref = reference(inputs)
    with HeldWorkerRuntimePool() as pool:
        runtime = pool.acquire(ref)
        if change == "membership":
            (runtime.root / "unlisted").write_bytes(b"new")
            error, code = IntegrityError, "BOOTSTRAP_TREE_CHANGED"
        elif change == "lease_closed":
            runtime.lease.close()
            error, code = IntegrityError, "BOOTSTRAP_LEASE_CLOSED"
        elif change == "reference":
            ref = ref | {"sha256": "a" * 64}
            error, code = Fault, "WORKER_BUNDLE_CHANGED"
        else:
            runtime.reference["sha256"] = "a" * 64
            error, code = Fault, "WORKER_BUNDLE_CHANGED"
        with pytest.raises(error, match=code):
            pool.acquire(ref)
    assert runtime.lease.closed
    Path(runtime.body["node"]).write_bytes(b"closed even on failure")


def test_borrow_refuses_unentered_pool_and_non_pool(inputs):
    ref = reference(inputs)
    with pytest.raises(Fault, match="WORKER_RUNTIME_POOL_CLOSED"):
        HeldWorkerRuntimePool().acquire(ref)
    with pytest.raises(Fault, match="WORKER_RUNTIME_POOL_REQUIRED"):
        with _held_worker_runtime(ref, object()):
            pytest.fail("accepted arbitrary owner")


def test_separate_pools_never_share_ownership(inputs):
    ref = reference(inputs)
    with HeldWorkerRuntimePool() as first_pool:
        first = first_pool.acquire(ref)
        with HeldWorkerRuntimePool() as second_pool:
            second = second_pool.acquire(ref)
            assert first is not second and first.lease is not second.lease
        assert second.lease.closed
        first.recheck()
    assert first.lease.closed
