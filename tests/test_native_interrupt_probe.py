"""Synthetic verifier tests; native interruption evidence requires the pinned CLI."""

import copy
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "tools"))
    return importlib.import_module("native_interrupt_probe")


def listing():
    return {"content": [{"type": "text", "text": json.dumps({"files": [
        {"path": "supplied/plan.md", "ref": "cas:sha256:" + "a" * 64, "immutable": 1},
        {"path": "results/advice.md", "ref": "cas:sha256:" + "b" * 64, "immutable": 0}]})}]}


def sample(module, database, *, absent=False):
    db = database.connection
    db.execute("CREATE TABLE broker_call_lifecycle(event,state,elapsed_ns)")
    db.execute("INSERT INTO broker_call_lifecycle VALUES(1,'RETURNED',10)")
    db.execute("CREATE TABLE broker_files(path)")
    p = module.InterruptProbe()
    p.cell, p.cell_started_ms = "2", 1000
    p.post_interrupt = "cell_absent_after_interrupt" if absent else "surviving_pending_cell"
    p.retired, p.finished, p.root_phase = {"state": "CLOSED"}, True, "done"
    absent_result = "Script failed\nWall time 0.0 seconds\nOutput:\nScript error:\nexec cell 2 not found"
    outputs = {"pending": "Script running with cell ID 2\nWall time 0.0 seconds\nOutput:\n" +
        json.dumps({"probe": "cell_start", "at_ms": 1000}),
        "interrupt": json.dumps({"previous_status": "running"}),
        "after_interrupt": absent_result if absent else "Script running with cell ID 2\nWall time 0.0 seconds\nOutput:",
        "owner_cancel": absent_result if absent else "Script terminated\nWall time 0.0 seconds\nOutput:",
        "after_cleanup": json.dumps({"probe": "after_cleanup", "result": listing()}),
        "after_deadline": json.dumps({"probe": "after_deadline", "at_ms": 62000, "result": listing()})}
    for phase, output in outputs.items():
        p.calls[phase] = {"actor": module.ROOT if phase == "interrupt" else module.CHILD,
                          "phase": phase, "issued_ms": 1000}
        p.outputs[phase] = output
        p.observed_ms[phase] = 62000 if phase == "after_deadline" else 2000
    return p, SimpleNamespace(requests=[{}]*16), database


@pytest.mark.parametrize("absent", [False, True])
def test_distinguishes_interrupt_removal_from_explicit_owner_cancellation(module, database, absent):
    p, provider, db = sample(module, database, absent=absent)
    assert all(p.report(provider, db)["checks"].values())


@pytest.mark.parametrize("case", ["not_running", "missing_cancel", "wrong_cell", "late_cleanup", "early_observation",
    "late_effect", "error_listing", "unretired", "pending_broker", "request_overrun", "missing_timestamp"])
def test_no_missing_or_contradictory_evidence_passes(module, database, case):
    p, provider, db = sample(module, database)
    if case == "not_running":
        p.outputs["interrupt"] = json.dumps({"previous_status": {"completed": "done"}})
    elif case == "missing_cancel":
        del p.outputs["owner_cancel"]
    elif case == "wrong_cell":
        p.outputs["owner_cancel"] = "Script failed\nWall time 0.0 seconds\nOutput:\nScript error:\nexec cell other not found"
    elif case == "late_cleanup":
        p.observed_ms["after_cleanup"] = 62000
    elif case == "early_observation":
        body = json.loads(p.outputs["after_deadline"])
        body["at_ms"] = 60000
        p.outputs["after_deadline"] = json.dumps(body)
    elif case == "late_effect":
        db.connection.execute("INSERT INTO broker_files VALUES(?)", (module.LATE_PATH,))
    elif case == "error_listing":
        p.outputs["after_deadline"] = json.dumps({"probe": "after_deadline", "at_ms": 62000,
            "result": {"isError": True, "content": [{"text": "results/advice.md"}]}})
    elif case == "unretired":
        p.retired = None
    elif case == "pending_broker":
        db.connection.execute("UPDATE broker_call_lifecycle SET state='STARTED'")
    elif case == "request_overrun":
        provider.requests = [{}] * 21
    else:
        p.cell_started_ms = None
    assert not all(p.report(provider, db)["checks"].values())


def test_actual_caller_binding_and_unchanged_native_result(module):
    p = module.InterruptProbe()
    call = p.call(module.CHILD, "pending", "operation", code="owned fixture")
    output = {"type": "custom_tool_call_output", "call_id": call["call_id"],
        "output": "Script running with cell ID 2\nWall time 0.0 seconds\nOutput:\n" +
        json.dumps({"probe": "cell_start", "at_ms": 1000})}
    with pytest.raises(Fault, match="INTERRUPT_WRONG_ACTOR"):
        p.observe(module.ROOT, {"input": [output]})
    p.observe(module.CHILD, {"input": [output]})
    p.observe(module.CHILD, {"input": [output]})
    changed = copy.deepcopy(output)
    changed["output"] += "altered"
    with pytest.raises(Fault, match="INTERRUPT_RESULT_CHANGED"):
        p.observe(module.CHILD, {"input": [changed]})
    assert p.cell == "2" and p.cell_started_ms == 1000


@pytest.mark.parametrize("value", ["exec cell 2 not found", "Script completed\nWall time 0.0 seconds\nOutput:",
    "Script terminated\nWall time 0.0 seconds\nOutput:\nlate side effect", "Script running with cell ID other\nWall time 0.0 seconds\nOutput:"])
def test_unrelated_or_successful_wait_is_not_cancellation(module, value):
    assert module.cell_state(value, "2") is None
