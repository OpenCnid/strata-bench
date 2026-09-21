"""Retained-history proofs; synthetic API negatives and real owned Windows handles."""
# ruff: noqa: F811 -- pytest intentionally injects the imported fixture by name.

import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from mcbench.processes import ManagedProcess, ProcessInventoryFault
from mcbench.storage import Fault
from strata_evaluator import reference_pair
from test_processes import synthetic_member_job  # noqa: F401


def prepared(job, state):
    state.pids = [123, 124]
    job.observe_members()
    state.assigned, state.listed = 2, 1
    accounting = {"total_processes": 2, "active_processes": 1, "terminated_processes": 0}
    job.accounting = lambda: dict(accounting)
    return accounting


def test_incomplete_list_requires_opt_in_and_independent_complete_history(synthetic_member_job):
    job, state = synthetic_member_job
    accounting = prepared(job, state)
    before = dict(job.members)
    with pytest.raises(ProcessInventoryFault, match="PROCESS_MEMBER_INVENTORY_UNAVAILABLE"):
        job.observe_members()
    proof = job.observe_members(reconcile_history=True)
    assert proof == {"schema": "strata/ProcessInventoryReconciliation/1",
        "policy": "complete-retained-job-history/1", "assigned_processes": 2,
        "listed_processes": 1, "retained_processes": 2, "job": accounting,
        "held": {"held_processes": 2, "signaled_processes": 0}}
    assert state.queries == 3 and job.members == before  # Exactly one list query per call.
    assert [pid for _, _, pid in state.opened] == [123, 124]  # No new/guessed handle.


@pytest.mark.parametrize("failure", ["missing_handle", "unseen_history", "undercounted_history",
    "foreign_list_entry", "assigned_quota", "impossible_active", "limit_termination",
    "accounting_failure", "invalid_handle"])
def test_incomplete_list_cannot_hide_uncertainty(synthetic_member_job, failure):
    job, state = synthetic_member_job
    accounting = prepared(job, state)
    if failure == "missing_handle":
        job.members.pop(124)
    elif failure == "unseen_history":
        accounting["total_processes"] = 3
    elif failure == "undercounted_history":
        accounting["total_processes"] = 1
    elif failure == "foreign_list_entry":
        state.pids = [125]
    elif failure == "assigned_quota":
        state.assigned = 3
    elif failure == "impossible_active":
        accounting["active_processes"] = 3
    elif failure == "limit_termination":
        accounting["terminated_processes"] = 1
    elif failure == "accounting_failure":
        def unavailable():
            raise Fault("PROCESS_STATE_UNAVAILABLE")
        job.accounting = unavailable
    else:
        job.kernel.WaitForSingleObject = lambda *_: 0xFFFFFFFF
    before, opened, queries = dict(job.members), list(state.opened), state.queries
    with pytest.raises(Fault, match="PROCESS_(MEMBER_INVENTORY|STATE)_UNAVAILABLE"):
        job.observe_members(reconcile_history=True)
    assert job.members == before and state.opened == opened and state.queries == queries + 1


def test_duplicate_list_entries_never_establish_ownership(synthetic_member_job):
    job, state = synthetic_member_job
    state.pids = [123, 123]
    with pytest.raises(ProcessInventoryFault) as caught:
        job.observe_members(reconcile_history=True)
    assert caught.value.observation()["stage"] == "invalid_pid"
    assert not job.members and not state.opened


def observer(tmp_path):
    proof = {"schema": "strata/ProcessInventoryReconciliation/1",
        "policy": "complete-retained-job-history/1", "assigned_processes": 2,
        "listed_processes": 1, "retained_processes": 2,
        "job": {"total_processes": 2, "active_processes": 1, "terminated_processes": 0},
        "held": {"held_processes": 2, "signaled_processes": 1}}
    state = {"observations": 0, "polls": 0}
    def observe(*, reconcile_history):
        assert reconcile_history
        state["observations"] += 1
        return proof
    def poll():
        # The durable proof must precede successful admission.
        assert (tmp_path / "client-inventory-1.json").exists()
        state["polls"] += 1
    owned = reference_pair.OwnedCli.__new__(reference_pair.OwnedCli)
    owned.fired, owned.errors, owned.inventory_reconciliations = False, [], []
    owned.evidence, owned.role = tmp_path, "client"
    owned.process = SimpleNamespace(job=SimpleNamespace(observe_members=observe), poll=poll)
    return owned, state, proof


def test_private_observer_persists_each_proof_before_continuing(tmp_path):
    owned, state, proof = observer(tmp_path)
    assert owned.observe() is None
    retained = json.loads((tmp_path / "client-inventory-1.json").read_bytes())
    assert retained == owned.inventory_reconciliations[0]
    assert {k: v for k, v in retained.items() if k != "observed_mono_ns"} == proof
    assert type(retained["observed_mono_ns"]) is int
    assert state == {"observations": 1, "polls": 1}


@pytest.mark.parametrize("failure", ["publication", "quota"])
def test_private_observer_evidence_failure_is_sticky(tmp_path, monkeypatch, failure):
    owned, state, _ = observer(tmp_path)
    if failure == "publication":
        def denied(*_):
            raise PermissionError()
        monkeypatch.setattr(reference_pair, "publish", denied)
    else:
        owned.inventory_reconciliations = [{} for _ in range(64)]
    with pytest.raises((PermissionError, Fault)):
        owned.observe()
    assert owned.errors and state["polls"] == 0
    with pytest.raises(Fault, match="REFERENCE_PAIR_LOG_UNAVAILABLE"):
        owned.observe()
    assert state["observations"] == 1  # A later disk recovery cannot erase the failure.


@pytest.mark.skipif(os.name != "nt", reason="Actual retained Windows Job handles")
def test_native_nested_job_history_proves_only_an_injected_incomplete_list(tmp_path):
    """Mask one API list entry; actual handles/accounting/terminal state stay native."""
    import ctypes
    from ctypes import wintypes
    child_code = ("import pathlib,time; p=pathlib.Path('release');print('ready',flush=True);\n"
                  "while not p.exists(): time.sleep(.01)")
    parent_code = (
        "import pathlib,sys;sys.path.insert(0," + repr(str(Path(__file__).resolve().parents[1] / "src"))
        + ");from mcbench.processes import ManagedProcess;"
        "p=ManagedProcess([sys.executable,'-I','-c'," + repr(child_code)
        + "],pathlib.Path.cwd(),{},'')\ntry:\n"
        " assert p.process.stdout.readline().strip()==b'ready'\n"
        " p.job.observe_members();print('ready',flush=True);sys.stdin.readline()\n"
        " pathlib.Path('release').touch();p.process.wait(timeout=5)\n"
        "finally:p.close()")
    proc = ManagedProcess([sys.executable, "-I", "-c", parent_code], tmp_path, {}, "", interactive=True)
    watchdog = threading.Timer(12, proc.stop)
    watchdog.start()
    original = proc.job.kernel.QueryInformationJobObject
    try:
        assert proc.process.stdout.readline().strip() == b"ready"
        proc.job.observe_members()
        total = proc.job.accounting()["total_processes"]
        assert len(proc.job.members) == total >= 3
        class Members(ctypes.Structure):
            _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                        ("pids", ctypes.c_size_t * proc.job.MAX_TRACKED_PROCESSES)]
        def masked(handle, kind, pointer, size, returned):
            success = original(handle, kind, pointer, size, returned)
            if success and kind == 3:
                value = ctypes.cast(pointer, ctypes.POINTER(Members)).contents
                assert value.count == value.assigned and value.count > 1
                value.count -= 1
            return success
        proc.job.kernel.QueryInformationJobObject = masked
        with pytest.raises(ProcessInventoryFault):
            proc.job.observe_members()
        # Withhold an actual retained handle without closing it; no count waiver.
        pid, handle = next(iter(proc.job.members.items()))
        del proc.job.members[pid]
        try:
            with pytest.raises(ProcessInventoryFault):
                proc.job.observe_members(reconcile_history=True)
        finally:
            proc.job.members[pid] = handle
        proof = proc.job.observe_members(reconcile_history=True)
        assert proof["job"]["total_processes"] == proof["retained_processes"] == total
        assert proof["listed_processes"] + 1 == proof["assigned_processes"]
        assert len(proc.job.members) == total
        proc.job.kernel.QueryInformationJobObject = original
        proc.send_input("stop\n")
        assert proc.process.wait(timeout=5) == 0
        until = time.monotonic() + 2
        while proc.job.member_status()["signaled_processes"] != total and time.monotonic() < until:
            time.sleep(.01)
        assert proc.job.accounting()["active_processes"] == 0
        assert proc.job.member_status() == {"held_processes": total, "signaled_processes": total}
    finally:
        proc.job.kernel.QueryInformationJobObject = original
        watchdog.cancel()
        watchdog.join(2)
        proc.stop()
        proc.close()
