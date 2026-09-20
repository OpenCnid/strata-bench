import copy
import importlib.util
import json
from pathlib import Path

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
    outputs = [{"call_id": key, "output": [{"text": json.dumps(c)} for c in controls]}
               for key in ("root", "helper")]
    outputs += [{"call_id": key, "output": "unsupported call: exec_command"} for key in ("direct1", "direct2")]
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
