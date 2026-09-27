"""Scripted provider protocol only; authentic native execution is separate."""

import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_active_script_probe")


SOURCE = 'text({probe:"active_script",value:6*7});\n'
PATH = "active/learned-crafting/scripts/check.js"


def active():
    return {"skills": {"learned-crafting": {"revision": {"status": "active",
        "activated_at": "2026-09-24T00:00:00.000Z", "revision_id": "learned-crafting:1"},
        "files": {"scripts/check.js": "cas:sha256:" + hashlib.sha256(SOURCE.encode()).hexdigest()}}}}


def read(probe, actor, *, key="read", returned=None, register=True):
    if register:
        probe.expect_read(actor, key)
    value = returned or {"path": PATH, "ref": probe.ref, "text": SOURCE}
    output = {"type": "custom_tool_call_output", "call_id": key, "output": [
        {"type": "input_text", "text": json.dumps({"name": "artifact_read", "result": {
            "content": [{"type": "text", "text": json.dumps(value)}]}})}]}
    body = {"input": [output]}
    probe.observe(actor, body)
    return body


def completed(call):
    return {"input": [call, {"type": "custom_tool_call_output", "call_id": call["call_id"],
        "output": [{"type": "input_text", "text": "Script completed\nWall time 0.1 seconds\nOutput:\n"},
                   {"type": "input_text", "text": '{"probe":"active_script","value":42}'}]}]}


def test_both_roles_copy_exact_returned_bytes_and_require_native_completion(module):
    probe = module.ActiveScriptProbe(active(), PATH, SOURCE)
    assert probe.read_call() == ("artifact_read", {"path": PATH})
    assert not any(probe.report()["checks"].values())
    for index, actor in enumerate(module.ACTORS):
        body = read(probe, actor, key="read-" + str(index))
        probe.observe(actor, body)  # Repeated unchanged native context is not another execution.
        call = probe.issue(actor, "operation-" + str(index))
        assert call["input"].encode() == SOURCE.encode()
        probe.observe(actor, completed(call))
        with pytest.raises(Fault, match="SCRIPT_REPLAY"):
            probe.issue(actor, "new-operation")
    report = probe.report()
    assert all(report["checks"].values())
    assert report["revision_id"] == "learned-crafting:1"
    assert not report["operator_evaluated_script"] and not report["runtime_qualified"]
    assert not report["broker_effects_qualified"]


@pytest.mark.parametrize("path", ["skills/learned-crafting/scripts/check.js", "active/../scripts/check.js",
    "active/learned-crafting/references/check.js", "active/learned-crafting/scripts/check.py",
    "active/learned-crafting/scripts/check.JS", "C:/private/check.js"])
def test_only_explicit_active_javascript_path_is_selected(module, path):
    with pytest.raises(Fault):
        module.ActiveScriptProbe(active(), path, SOURCE)


@pytest.mark.parametrize("case", ["candidate", "no_time", "missing", "changed", "empty", "too_large"])
def test_nonactive_or_changed_bytes_cannot_be_issued(module, case):
    body = active()
    source = SOURCE
    record = body["skills"]["learned-crafting"]
    if case == "candidate":
        record["revision"]["status"] = "candidate"
    elif case == "no_time":
        record["revision"]["activated_at"] = None
    elif case == "missing":
        record["files"] = {}
    elif case == "changed":
        source += "text('changed');"
    elif case == "empty":
        source = ""
    else:
        source = "x" * (256 * 1024 + 1)
    with pytest.raises(Fault):
        module.ActiveScriptProbe(body, PATH, source)


@pytest.mark.parametrize("case", ["no_read", "input_only", "foreign_read", "unregistered", "wrong_ref", "wrong_text"])
def test_private_source_is_never_used_in_place_of_a_public_return(module, case):
    probe = module.ActiveScriptProbe(active(), PATH, SOURCE)
    if case in {"wrong_ref", "wrong_text"}:
        value = {"path": PATH, "ref": probe.ref, "text": SOURCE}
        value["ref" if case == "wrong_ref" else "text"] = "changed"
        with pytest.raises(Fault, match="SCRIPT_SOURCE_CHANGED"):
            read(probe, "/root", returned=value)
    else:
        if case == "input_only":
            probe.observe("/root", {"input": [{"type": "custom_tool_call", "input": SOURCE}]})
        elif case == "foreign_read":
            read(probe, "/root/identity_child")
        elif case == "unregistered":
            read(probe, "/root", register=False)
        with pytest.raises(Fault, match="SCRIPT_READ_REQUIRED"):
            probe.issue("/root", "operation")


@pytest.mark.parametrize("case,code", [("scalar", "SCRIPT_COMPLETION_FRAME"),
    ("foreign", "SCRIPT_RETURN_SCOPE"), ("changed_code", "SCRIPT_EXECUTION_CHANGED"),
    ("changed_result", "SCRIPT_RETURN_CHANGED"), ("missing_echo", "SCRIPT_EXECUTION_CHANGED")])
def test_completion_cannot_be_forged_or_transferred(module, case, code):
    probe = module.ActiveScriptProbe(active(), PATH, SOURCE)
    read(probe, "/root")
    call = probe.issue("/root", "operation")
    body = completed(call)
    actor = "/root/identity_child" if case == "foreign" else "/root"
    if case == "scalar":
        body["input"][1]["output"] = "Script completed\nWall time 0.0 seconds\nOutput:\n"
    elif case == "changed_code":
        body["input"][0]["input"] += "text('other');"
    elif case == "missing_echo":
        body["input"].pop(0)
    elif case == "changed_result":
        probe.observe(actor, copy.deepcopy(body))
        body["input"][1]["output"].append({"type": "input_text", "text": "changed"})
    with pytest.raises(Fault, match=code):
        probe.observe(actor, body)


def test_yielded_script_does_not_count_as_completed(module):
    probe = module.ActiveScriptProbe(active(), PATH, SOURCE)
    read(probe, "/root")
    call = probe.issue("/root", "operation")
    body = completed(call)
    body["input"][1]["output"][0]["text"] = "Script running with cell ID 1\nWall time 0.1 seconds\nOutput:\n"
    probe.observe("/root", body)
    assert not probe.report()["checks"]["both_native_calls_completed"]


@pytest.mark.parametrize("source,path", [(None, PATH), ({}, False), (None, "")])
def test_orchestrator_refuses_script_without_activation_before_creating_state(module, tmp_path, source, path):
    native = importlib.import_module("native_mcp_identity_probe")
    with pytest.raises(Fault, match="SCRIPT_ACTIVATION_REQUIRED"):
        native.run(Path(sys.executable), tmp_path / "unused", activation_source=source, activation_script=path)
    assert not list(tmp_path.iterdir())
