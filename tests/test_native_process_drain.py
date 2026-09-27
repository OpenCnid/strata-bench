"""Owned process evidence and corrupted proof tests; no model/game execution."""

import os
import sys
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mcbench.native_process_drain import HeldProcessDrain, require_process_drain
from mcbench.processes import ManagedProcess
from mcbench.records import BudgetLedger
from mcbench.storage import Fault, Principal, canonical
from test_native import command, make_plan as _make_plan, runtime as _runtime, wait_end

make_plan, runtime = _make_plan, _runtime
pytestmark = pytest.mark.skipif(os.name != "nt", reason="held Windows Job Object evidence")


@pytest.fixture
def drained(runtime, make_plan):
    plan, reserve = make_plan()
    runtime.start(plan, reserve, fixture_argv=command("pass"))
    wait_end(runtime, plan.job_id)
    with pytest.raises(Fault, match="NATIVE_PROCESS_DRAIN_NOT_FINAL"):
        require_process_drain(runtime.db.connection, runtime.cas, plan)
    assert runtime.budgets.status("a1")["uncertain"]
    runtime.budgets.post("a1", BudgetLedger.model_validate(reserve.model_dump() | {
        "posting": "settle", "source_event_id": "complete-synthetic-receipt",
        "metering": "reported", "reason": "synthetic complete receipt"}))
    runtime.finalize(plan.job_id)
    return runtime, plan


def test_held_job_proof_is_private_durable_and_does_not_settle_cost(drained):
    runtime, plan = drained
    proof = require_process_drain(runtime.db.connection, runtime.cas, plan)
    assert proof["active_processes"] == 0 and proof["total_processes"] >= 2
    with pytest.raises(Fault, match="FORBIDDEN"):
        runtime.cas.read(Principal("gameplay", "executor"), "operator", proof["proof_ref"])
    assert require_process_drain(runtime.db.connection, runtime.cas, plan) == proof


@pytest.mark.parametrize("case", ["missing", "not_final", "changed_plan", "changed_link", "missing_event",
                                  "wrong_event", "wrong_profile", "wrong_started", "wrong_exit",
                                  "late_observation", "live_member", "wrong_mode", "bool_zero"])
def test_corrupt_or_unbound_process_drain_never_qualifies(drained, case):
    runtime, plan = drained
    db = runtime.db.connection
    link = db.execute("SELECT * FROM native_process_drains WHERE job=?", (plan.job_id,)).fetchone()
    if case == "missing":
        db.execute("DELETE FROM native_process_drains")
    elif case == "not_final":
        db.execute("UPDATE native_jobs SET state='RUNNING'")
    elif case == "changed_plan":
        plan = plan.model_copy(update={"prompt": "different source"})
    elif case == "changed_link":
        db.execute("UPDATE native_process_drains SET proof_ref=?", ("cas:sha256:" + "e" * 64,))
    elif case == "missing_event":
        db.execute("UPDATE outbox SET kind='unrelated' WHERE cursor=?", (link["event"],))
    elif case == "wrong_event":
        db.execute("UPDATE outbox SET body='{}' WHERE cursor=?", (link["event"],))
    else:
        proof = runtime.cas.json(Principal("operator", "operator"), "operator", link["proof_ref"])
        if case == "wrong_profile":
            proof["profile_digest"] = "e" * 64
        elif case == "wrong_started":
            proof["started_unix_ms"] += 1
        elif case == "wrong_exit":
            proof["observation"]["root_returncode"] += 1
        elif case == "late_observation":
            proof["observation"]["observed_unix_ms"] += 100000
        elif case == "live_member":
            proof["observation"]["accounting"]["active_processes"] = 1
        elif case == "wrong_mode":
            proof["is_example"] = False
        else:
            proof["observation"]["accounting"]["active_processes"] = False
        ref = runtime.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(proof))
        db.execute("UPDATE native_process_drains SET proof_ref=?", (ref,))
        # Keep the source-event join coherent: otherwise an unrelated changed-ref
        # error masks an incorrectly accepted accounting/scope field.
        db.execute("UPDATE outbox SET body=? WHERE cursor=?", (canonical({"job_id": plan.job_id,
            "profile_digest": plan.profile_digest(), "proof_ref": ref}).decode(), link["event"]))
    with pytest.raises((Fault, ValidationError)):
        require_process_drain(db, runtime.cas, plan)


@pytest.mark.parametrize("value", [1, -1, False, True, 0.0, "0"])
def test_zero_active_is_an_exact_integer_constraint(value):
    from mcbench.native_process_drain import JobAccounting
    with pytest.raises(ValidationError):
        JobAccounting(total_processes=2, active_processes=value, terminated_processes=0)
    assert JobAccounting(total_processes=2, active_processes=0, terminated_processes=0).active_processes == 0
    assert JobAccounting.model_json_schema()["properties"]["active_processes"]["maximum"] == 0


def test_parent_exit_cannot_hide_live_owned_descendant(tmp_path):
    code = ("import subprocess,sys; subprocess.Popen([sys.executable,'-I','-c',"
            "'import time; time.sleep(30)']); print('owned-child-started',flush=True)")
    proc = ManagedProcess([sys.executable, "-I", "-c", code], tmp_path, {}, "")
    try:
        assert proc.process.stdout.readline().strip() == b"owned-child-started"
        assert proc.process.wait(timeout=5) == 0
        before = proc.job.accounting()
        assert before["total_processes"] >= 3 and before["active_processes"] >= 1
        with pytest.raises(Fault, match="PROCESS_DRAIN_PENDING"):
            proc.drain_evidence(timeout_s=0.02)
        proc.stop()
        proof = HeldProcessDrain.model_validate(proc.drain_evidence())
        assert proof.accounting.active_processes == 0
        assert proof.accounting.total_processes == before["total_processes"]
    finally:
        proc.stop()
        proc.close()
    with pytest.raises(Fault, match="PROCESS_DRAIN_UNSUPPORTED"):
        proc.drain_evidence()


def test_query_failure_and_missing_parent_exit_fail_closed(monkeypatch):
    proc = ManagedProcess.__new__(ManagedProcess)
    proc.job = SimpleNamespace(handle=1, accounting=lambda: {
        "total_processes": 2, "active_processes": 0, "terminated_processes": 0})
    proc.process = SimpleNamespace(poll=lambda: None)
    with pytest.raises(Fault, match="PROCESS_DRAIN_PENDING"):
        proc.drain_evidence(timeout_s=0.01)
    def failed():
        raise Fault("PROCESS_STATE_UNAVAILABLE")
    proc.job.accounting = failed
    with pytest.raises(Fault, match="PROCESS_STATE_UNAVAILABLE"):
        proc.drain_evidence()


def test_failed_drain_keeps_reservation_and_writes_no_proof(runtime, make_plan, monkeypatch):
    plan, reserve = make_plan()
    runtime.start(plan, reserve, fixture_argv=command("import time; time.sleep(30)"))
    managed = runtime.live[plan.job_id]["process"]
    def fail(**_):
        raise Fault("PROCESS_DRAIN_PENDING")
    monkeypatch.setattr(managed, "drain_evidence", fail)
    with pytest.raises(Fault, match="RUNTIME_CLEANUP_FAILED"):
        runtime.interrupt(plan.job_id, "owned-test-stop")
    assert managed.job.handle is None
    assert runtime.db.connection.execute("SELECT count(*) FROM native_process_drains").fetchone()[0] == 0
    assert runtime.status(plan.job_id)["state"] == "UNSETTLED"
    assert runtime.budgets.status("a1")["uncertain"]
