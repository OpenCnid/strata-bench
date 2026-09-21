import copy
import importlib.util
import json
from pathlib import Path

import pytest

from mcbench.storage import Fault

module = importlib.util.spec_from_file_location("broker_canaries",
    Path(__file__).resolve().parents[1] / "tools/native_broker_canaries.py")
canaries = importlib.util.module_from_spec(module)
module.loader.exec_module(canaries)


def output_fixture():
    names = ["apply_patch", "list_mcp_resource_templates", "list_mcp_resources", "read_mcp_resource"]
    names += ["mcp__strata_broker__" + n for n in ("artifact_list", "artifact_read", "artifact_write", "game")]
    controls = [{"probe": "catalog", "names": names, "process": "undefined", "require": "undefined",
        "fetch": "undefined"}] + [{"probe": key, "error": value} for key, value in {
            "disabled_shell": "TypeError: tools.exec_command is not a function",
            "disabled_image": "TypeError: tools.view_image is not a function",
            "resource_file": "Mcp error: -32600: BROKER_REQUEST_REJECTED",
            "resource_network": "Mcp error: -32600: BROKER_REQUEST_REJECTED",
            "outside_patch": "patch rejected: writing is blocked by read-only sandbox"}.items()]
    actors = ("/root", "/root/identity_child")
    outputs = [{"call_id": key, "native_agent": actor, "output": [{"text": json.dumps(c)} for c in controls]}
               for key, actor in zip(("root", "helper"), actors)]
    outputs += [{"call_id": key, "native_agent": actor, "output": "unsupported call: exec_command"}
                for key, actor in zip(("direct1", "direct2"), actors)]
    return outputs, ["direct1", "direct2"]


def test_exact_native_denials_require_positive_observation():
    outputs, direct = output_fixture()
    assert all(canaries.inspect_tool_outputs(outputs + copy.deepcopy(outputs), direct).values())
    for bad in (outputs[:-1], outputs[1:]):
        assert not all(canaries.inspect_tool_outputs(bad, direct).values())
    success = copy.deepcopy(outputs)
    success[-1]["output"] = "command completed"
    assert not canaries.inspect_tool_outputs(success, direct)["direct_shell_dispatch_denied"]
    expanded = copy.deepcopy(outputs)
    catalog = json.loads(expanded[0]["output"][0]["text"])
    catalog["names"].append("exec_command")
    expanded[0]["output"][0]["text"] = json.dumps(catalog)
    assert not canaries.inspect_tool_outputs(expanded, direct)["exact_root_helper_tool_catalogs"]


def test_two_root_outputs_or_unbound_outputs_cannot_stand_in_for_helper():
    outputs, direct = output_fixture()
    for actor in (None, "/root"):
        altered = copy.deepcopy(outputs)
        for item in altered:
            item["native_agent"] = actor
        assert not all(canaries.inspect_tool_outputs(altered, direct).values())


def test_writer_denials_require_both_actual_callers_and_exact_error():
    outputs, direct = output_fixture()
    for item in outputs[:2]:
        item["output"].extend({"text": json.dumps(value)} for value in [
            {"probe": "writer_resource", "error": "Mcp error: BROKER_REQUEST_REJECTED"},
            {"probe": "writer_artifact", "result": {"isError": True,
                "content": [{"type": "text", "text": "UNSAFE_PATH"}]}}])
    assert all(canaries.inspect_tool_outputs(outputs, direct, writer_target=True).values())
    for value in ({"isError": False, "content": [{"type": "text", "text": "UNSAFE_PATH"}]},
                  {"isError": True, "content": [{"type": "text", "text": "UNREGISTERED"}]}, {}):
        altered = copy.deepcopy(outputs)
        altered[1]["output"][-1]["text"] = json.dumps({"probe": "writer_artifact", "result": value})
        assert not canaries.inspect_tool_outputs(altered, direct, writer_target=True)["writer_artifact_both_denied"]


def test_writer_target_only_accepts_exact_synthetic_file(tmp_path):
    target = tmp_path / "world/level.dat"
    target.parent.mkdir()
    target.write_bytes(b"not a canary")
    output = tmp_path / "bad"
    output.mkdir()
    with pytest.raises(Fault, match="SYNTHETIC_WRITER_TARGET_REQUIRED"):
        canaries.Canaries(output, writer_target=target)
    target.write_bytes(b"synthetic-writer")
    output = tmp_path / "good"
    output.mkdir()
    probe = canaries.Canaries(output, writer_target=target)
    try:
        assert 'writer_artifact' in probe.code() and target.as_uri() in probe.code()
        assert str(target) in probe.command()
        assert 'synthetic-writer' not in probe.code()
    finally:
        probe.close()
