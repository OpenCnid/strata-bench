"""Synthetic proof composition; actual held-job/native evidence is separate."""

import time
import json

import pytest

from mcbench.native import NativeExec
from mcbench.native_cell_lifecycle import require_native_cells_drained
from mcbench.native_process_drain import record_process_drain
from mcbench.storage import Fault
from test_native_admission import admitted as _admitted
from test_native_cell_lifecycle import exercise

admitted = _admitted


def synthetic_fence(gate, plan, *, record=True, finalized=True):
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    if record:
        record_process_drain(runtime, plan, {"schema": "strata/HeldProcessDrain/1",
            "policy": "held-windows-job-zero-active/1", "root_returncode": 0,
            "accounting": {"total_processes": 4, "active_processes": 0, "terminated_processes": 2},
            "observed_unix_ms": time.time_ns() // 1_000_000, "observation_elapsed_ns": 1})
    if finalized:
        # Deliberate synthetic state: validates read-only proof composition, not
        # real budget finalization. Remaining unknown costs must still stop export.
        gate.db.connection.execute("UPDATE native_jobs SET state='FINALIZED',ended=?,returncode=0", (time.time(),))
    return runtime


@pytest.mark.parametrize("case", ["pending", "missing", "aborted_exec", "aborted_wait"])
def test_stopped_fence_disposes_unresolved_cells_without_claiming_success_or_settling(admitted, case):
    _, gate, _ = exercise(admitted, case)
    plan = admitted[3]
    before = gate.budgets.status("a1")
    runtime = synthetic_fence(gate, plan)
    with pytest.raises(Fault):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child")
    result = require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
    assert result["policy"] == "native-process-fenced-cell-disposal/1"
    assert result["pending_cells"] == 0 and result["tool_success_inferred"] is False
    assert result["observed_pending_before_fence"] or result["unresolved_call_ids"]
    assert gate.budgets.status("a1") == before
    with pytest.raises(Fault, match="NATIVE_EXPORT_PARTICIPANTS"):
        runtime.export_broker_state(plan.job_id)


@pytest.mark.parametrize("record,finalized", [(False, True), (True, False)])
def test_stopped_option_alone_never_releases_unknown_cells(admitted, record, finalized):
    _, gate, _ = exercise(admitted, "missing")
    plan = admitted[3]
    synthetic_fence(gate, plan, record=record, finalized=finalized)
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="NATIVE_PROCESS_DRAIN_(MISSING|NOT_FINAL)"):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
    assert gate.budgets.status("a1") == before


@pytest.mark.parametrize("case,code", [("duplicate", "NATIVE_CELL_RESULT_DUPLICATE"),
    ("changed_output", "NATIVE_CELL_RESULT_CHANGED"), ("reused", "NATIVE_CELL_ISSUANCE_REUSED"),
    ("wrong_target", "NATIVE_CELL_WAIT_SCOPE"), ("false_cancel", "NATIVE_CELL_WAIT_SCOPE"),
    ("scalar_wait_completion", "NATIVE_CELL_RESULT_SHAPE")])
def test_process_fence_cannot_bypass_invalid_source_or_authority(admitted, case, code):
    _, gate, _ = exercise(admitted, case)
    plan = admitted[3]
    synthetic_fence(gate, plan)
    with pytest.raises(Fault, match=code):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)


@pytest.mark.parametrize("bad", [{"cell_id": True}, {"terminate": 1}, {"yield_time_ms": False},
                                  {"max_tokens": "100"}, {"cell_id": "../foreign"}])
def test_malformed_wait_arguments_remain_invalid_with_a_stopped_fence(admitted, monkeypatch, bad):
    import test_native_cell_lifecycle as fixture
    original = fixture.wait_call
    def malformed(*args, **kwargs):
        call = original(*args, **kwargs)
        call["arguments"] = json.dumps(json.loads(call["arguments"]) | bad)
        return call
    monkeypatch.setattr(fixture, "wait_call", malformed)
    _, gate, _ = exercise(admitted, "aborted_wait")
    plan = admitted[3]
    synthetic_fence(gate, plan)
    with pytest.raises(Fault, match="NATIVE_CELL_WAIT_SCOPE"):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
