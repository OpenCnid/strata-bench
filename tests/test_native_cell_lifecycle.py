"""Native agent termination alone is not proof that yielded cells have drained."""

import json

import pytest

from mcbench.storage import Fault
from test_native_admission import admitted as _admitted, begin
from test_native_retirement import scenario, settle

admitted = _admitted


def exec_call(key="cell-start"):
    return {"type": "custom_tool_call", "namespace": "functions", "name": "exec", "call_id": key,
            "input": "await yield_control(); await new Promise(r=>setTimeout(r,60000));"}


def wait_call(key, *, target="2", terminate=False):
    return {"type": "function_call", "namespace": "functions", "name": "wait", "call_id": key,
            "arguments": json.dumps({"cell_id": target, "yield_time_ms": 1, "terminate": terminate})}


def output(call, text):
    return {"type": "custom_tool_call_output" if call["name"] == "exec" else "function_call_output",
            "call_id": call["call_id"], "output": text}


PENDING = "Script running with cell ID 2\nWall time 0.0 seconds\nOutput:\n"
COMPLETED = "Script completed\nWall time 0.0 seconds\nOutput:\n"
TERMINATED = "Script terminated\nWall time 0.0 seconds\nOutput:\n"
ABSENT = "Script failed\nWall time 0.0 seconds\nOutput:\nScript error:\nexec cell 2 not found"


def exercise(admitted, case):
    admission, gate, _, _, request, _, _ = admitted
    def history():
        def turn(name, input_items, emitted):
            value = request(name, "child", "/root/child", "root", mutate=lambda b:b["input"].extend(input_items))
            begin(admitted, value)
            settle(admitted, value, {"id": "response-"+name, "output": emitted})
        start = exec_call()
        initial = [start, output(start, COMPLETED)] if case == "old_id" else []
        turn("helper-start", initial, [start])
        if case == "missing":
            return
        result = "aborted by user after 0.7s" if case == "aborted_exec" else PENDING
        first = [start, output(start, result)]
        if case == "duplicate":
            first.append(output(start, result))
        if case in {"pending", "aborted_exec", "duplicate"}:
            turn("helper-observed", first, [])
            return
        if case == "reused":
            turn("helper-observed", first, [start])
            return
        original = wait_call("original-wait")
        turn("helper-observed", first, [original])
        if case == "aborted_wait":
            turn("helper-aborted", [original, output(original, "aborted by user after 0.7s")], [])
            return
        target = "foreign" if case == "wrong_target" else "2"
        cancel = wait_call("owner-cancel", target=target, terminate=case != "false_cancel")
        # Old cell creation falls out of current context; private earlier captures
        # must still reconstruct it. No fabricated context expansion is required.
        items = [original, output(original, "aborted by user after 0.7s")]
        if case == "changed_output":
            items += [start, output(start, COMPLETED)]
        turn("helper-aborted", items, [cancel])
        final = ABSENT if case == "absent" else COMPLETED if case == "completed" else TERMINATED
        turn("helper-cleaned", [cancel, output(cancel, final)], [])
    _, ref, _, _ = scenario(admitted, before_revoke=history)
    return admission, gate, ref


@pytest.mark.parametrize("case", ["cancelled", "absent", "completed"])
def test_fresh_own_terminal_evidence_drains_cell_despite_compacted_context(admitted, case):
    admission, gate, ref = exercise(admitted, case)
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"
    row = gate.db.connection.execute("SELECT body FROM outbox WHERE kind='native.participant_cells_drained'").fetchone()
    body = json.loads(row[0])
    assert body["issued_tools"] == 3 and body["yielded_cells"] == 1 and body["pending_cells"] == 0


@pytest.mark.parametrize("case,code", [("pending", "NATIVE_CELL_DRAIN_PENDING"),
    ("missing", "NATIVE_CELL_RESULT_MISSING"), ("aborted_exec", "NATIVE_CELL_DRAIN_UNKNOWN"),
    ("aborted_wait", "NATIVE_CELL_DRAIN_PENDING"), ("duplicate", "NATIVE_CELL_RESULT_DUPLICATE"),
    ("reused", "NATIVE_CELL_ISSUANCE_REUSED"), ("old_id", "NATIVE_CELL_ISSUANCE_REUSED"),
    ("changed_output", "NATIVE_CELL_RESULT_CHANGED"), ("wrong_target", "NATIVE_CELL_WAIT_SCOPE"),
    ("false_cancel", "NATIVE_CELL_WAIT_SCOPE")])
def test_terminal_agent_with_unresolved_cell_cannot_retire_or_refund(admitted, case, code):
    admission, gate, ref = exercise(admitted, case)
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match=code):
        admission.retire("job", "child", ref)
    assert gate.budgets.status("a1")["committed_and_reserved"] == before
    assert gate.db.connection.execute("SELECT state FROM native_participants WHERE thread='child'").fetchone()[0] == "REVOKED"
