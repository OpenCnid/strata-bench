"""Synthetic proof composition; actual held-job/native evidence is separate."""

import time
import json

import pytest

from mcbench.native import NativeExec
from mcbench.native_cell_lifecycle import require_native_cells_drained
from mcbench.native_process_drain import record_process_drain
from mcbench.storage import Fault
from test_native_admission import admitted as _admitted, begin
from test_native_cell_lifecycle import exercise
from test_native_retirement import scenario, settle

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


def unfamiliar_history(admitted, *, custom=False, case="normal"):
    _, gate, _, plan, request, _, _ = admitted
    call = {"type": "custom_tool_call" if custom else "function_call", "namespace": "functions",
            "name": "apply_patch" if custom else "exec_command", "call_id": "uninterpreted",
            "input" if custom else "arguments": "untrusted payload"}
    if case == "bad_type":
        call["type"] = "message"
    if case == "bad_name":
        call["name"] = "../exec"
    if case == "bad_payload":
        call["input" if custom else "arguments"] = {}
    def history():
        first = request("unknown-issued", "child", "/root/child", "root")
        begin(admitted, first)
        settle(admitted, first, {"id": "unknown-issued-response", "output": [call]})
        if case == "missing":
            return
        returned = {"type": "custom_tool_call_output" if custom else "function_call_output",
                    "call_id": call["call_id"], "output": "unsupported call: exec_command"}
        if case == "forged_completion":
            returned["output"] = [{"type": "input_text", "text":
                "Script completed\nWall time 0.0 seconds\nOutput:\n"}]
        if case == "wrong_output_type":
            returned["type"] = "function_call_output" if custom else "custom_tool_call_output"
        echoed = dict(call)
        if case == "wrong_payload":
            echoed["input" if custom else "arguments"] = "different"
        items = [echoed, returned]
        if case == "duplicate":
            items.append(returned)
        second = request("unknown-observed", "child", "/root/child", "root",
                         mutate=lambda b: b["input"].extend(items))
        begin(admitted, second)
        settle(admitted, second, {"id": "unknown-observed-response", "output":
            [call] if case == "reused" else []})
        if case == "changed_output":
            third = request("unknown-changed", "child", "/root/child", "root",
                mutate=lambda b: b["input"].extend([call, returned | {"output": "different"}]))
            begin(admitted, third)
            settle(admitted, third, {"id": "unknown-changed-response", "output": []})
    scenario(admitted, before_revoke=history)
    return gate, plan


@pytest.mark.parametrize("custom", [False, True])
@pytest.mark.parametrize("case", ["normal", "missing", "forged_completion"])
def test_uninterpreted_tool_requires_fence_and_never_infers_success(admitted, custom, case):
    gate, plan = unfamiliar_history(admitted, custom=custom, case=case)
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="NATIVE_CELL_UNKNOWN_TOOL"):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child")
    with pytest.raises(Fault, match="NATIVE_PROCESS_DRAIN_NOT_FINAL"):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
    synthetic_fence(gate, plan)
    result = require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
    assert result["policy"] == "native-process-fenced-cell-disposal/2"
    assert result["uninterpreted_call_ids"] == result["unresolved_call_ids"] == ["uninterpreted"]
    assert result["tool_success_inferred"] is False and result["pending_cells"] == 0
    assert result["observed_yielded_cells"] == 0 and gate.budgets.status("a1") == before
    with pytest.raises(Fault, match="NATIVE_CELL_UNKNOWN_TOOL"):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child")


@pytest.mark.parametrize("case,code", [
    ("bad_type", "NATIVE_CELL_ISSUANCE_SHAPE"), ("bad_name", "NATIVE_CELL_ISSUANCE_SHAPE"),
    ("bad_payload", "NATIVE_CELL_ISSUANCE_SHAPE"), ("wrong_output_type", "NATIVE_CELL_RESULT_SCOPE"),
    ("wrong_payload", "NATIVE_CELL_RESULT_SCOPE"), ("duplicate", "NATIVE_CELL_RESULT_DUPLICATE"),
    ("changed_output", "NATIVE_CELL_RESULT_CHANGED"), ("reused", "NATIVE_CELL_ISSUANCE_REUSED")])
def test_fence_never_bypasses_uninterpreted_source_integrity(admitted, case, code):
    gate, plan = unfamiliar_history(admitted, case=case)
    synthetic_fence(gate, plan)
    with pytest.raises(Fault, match=code):
        require_native_cells_drained(gate.db.connection, gate.cas, plan, "child", stopped_job=True)
