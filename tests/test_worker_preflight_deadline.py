"""Synthetic worker bytes and real file custody; forbidden process dispatch."""
import pytest

from mcbench import pack_worker as module
from mcbench.storage import Fault
from test_pack_worker import inputs, candidate, pack

(inputs, candidate, pack) = (inputs, candidate, pack)


@pytest.mark.parametrize("deadline", [True, float("nan"), float("inf"), -1])
def test_invalid_or_expired_import_deadline_never_dispatches(pack, monkeypatch, deadline):
    binding, invocation, _ = pack
    def forbidden(*args, **kwargs):
        pytest.fail("invalid deadline dispatched a process")
    monkeypatch.setattr(module, "ManagedProcess", forbidden)
    with module.HeldPackWorker(binding, invocation) as worker:
        with pytest.raises(Fault, match="WORKER_PREFLIGHT_DEADLINE"):
            worker.start(preflight=True, _deadline=deadline)
        assert not worker.processes


def test_input_rechecks_cannot_spend_past_parent_deadline_then_dispatch(pack, monkeypatch):
    binding, invocation, _ = pack
    def forbidden(*args, **kwargs):
        pytest.fail("expired input checks dispatched a process")
    monkeypatch.setattr(module, "ManagedProcess", forbidden)
    with module.HeldPackWorker(binding, invocation) as worker:
        clock = [100.]
        monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
        check = worker.config_lease.recheck
        def expires():
            check()
            clock[0] = 102.
        monkeypatch.setattr(worker.config_lease, "recheck", expires)
        with pytest.raises(Fault, match="WORKER_PREFLIGHT_DEADLINE"):
            worker.start(preflight=True, _deadline=101.)
        assert not worker.processes
