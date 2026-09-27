"""Synthetic workers/process receipts; actual runtime/configuration file custody."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.launch_integrity import IntegrityError
from mcbench.pack_worker import HeldPackWorker
from mcbench.storage import Fault
from strata_evaluator.probe_worker_runtime import PairedWorkerReference
from test_pack_worker import inputs, candidate, pack

inputs, candidate, pack = inputs, candidate, pack
pytestmark = pytest.mark.skipif(os.name != "nt", reason="actual Windows runtime custody")


def coordinator(worker, phase):
    owner = PairedWorkerReference.__new__(PairedWorkerReference)
    owner.workers = {"initial": {"a1": worker}}
    owner.phases = {("initial", "a1"): phase}
    owner.exports = []
    if phase != "HELD":
        worker.processes["preflight"] = SimpleNamespace(poll=lambda: 0, job=SimpleNamespace(
            accounting=lambda: {"total_processes": 1, "active_processes": 0, "terminated_processes": 0}))
    if phase in {"RUNNING", "STOPPED"}:
        worker.processes["worker"] = SimpleNamespace(poll=lambda: None if phase == "RUNNING" else 0,
            job=SimpleNamespace(accounting=lambda: {
                "total_processes": 1, "active_processes": int(phase == "RUNNING"), "terminated_processes": 0}))
    return owner


@pytest.mark.parametrize("phase", ["HELD", "IMPORTED", "RUNNING", "STOPPED"])
@pytest.mark.parametrize("loss", ["closed", "new_file"])
def test_every_phase_revalidates_runtime_and_refuses_later_custody_loss(pack, monkeypatch, phase, loss):
    with HeldPackWorker(pack[0], pack[1]) as worker:
        owner = coordinator(worker, phase)
        original = worker.runtime.recheck
        calls = []

        def check():
            calls.append(True)
            return original()

        monkeypatch.setattr(worker.runtime, "recheck", check)
        owner._check_worker_phases()
        owner._check_worker_phases()
        assert len(calls) == 2  # Each new check observes current custody.
        if loss == "closed":
            worker.runtime.lease.close()
        else:
            (Path(worker.runtime.root) / "unreviewed.txt").write_bytes(b"changed membership")
        with pytest.raises(IntegrityError):
            owner._check_worker_phases()
        assert len(calls) == 3


def test_unknown_worker_phase_cannot_bypass_runtime_or_process_checks(pack):
    with HeldPackWorker(pack[0], pack[1]) as worker:
        owner = coordinator(worker, "STOPPED")
        owner.phases["initial", "a1"] = "UNRECOGNIZED"
        with pytest.raises(Fault, match="PROBE_WORKER_PHASE"):
            owner._check_worker_phases()
