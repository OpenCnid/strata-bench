import copy
import importlib.util
import hashlib
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


def deferred_fixture():
    outputs, direct = output_fixture()
    for item in outputs[:2]:
        actor = item["native_agent"]
        probes = [{"probe": name, "error": canaries.EXACT_PATCH_DENIAL}
                  for name in canaries.DEFERRED_PATCHES]
        probes += [{"probe": name, "result": json.dumps({key: []})} for name, key in (
            ("resources_global", "resources"), ("templates_global", "resourceTemplates"))]
        probes += [{"probe": name, "error": method + " failed: " + method +
            " failed for `strata_broker`: Mcp error: -32600: BROKER_REQUEST_REJECTED"}
            for name, method in (("resources_broker", "resources/list"),
                                  ("templates_broker", "resources/templates/list"))]
        probes.append({"probe": "own_artifact_roundtrip", "actor": actor, "result": {"content": [{
            "type": "text", "text": json.dumps({"path": "notes/root.md" if actor == "/root" else
                "results/advice.md", "ref": "cas:sha256:" + hashlib.sha256(b"STRATA_OWN_ARTIFACT").hexdigest(),
                "text": "STRATA_OWN_ARTIFACT"})}]}})
        item["output"] += [{"text": json.dumps(p)} for p in probes]
    return outputs, direct


def test_deferred_probe_requires_denials_empty_catalogs_and_permitted_roundtrips():
    outputs, direct = deferred_fixture()
    assert all(canaries.inspect_tool_outputs(outputs, direct, deferred_tools=True).values())
    for index in range(6, len(outputs[0]["output"])):
        altered = copy.deepcopy(outputs)
        altered[1]["output"].pop(index)
        assert not all(canaries.inspect_tool_outputs(altered, direct, deferred_tools=True).values())


@pytest.mark.parametrize("kind", ["success", "unrelated_error", "nonempty_catalog", "wrong_content",
                                  "wrong_actor", "error_wrapped_success"])
def test_deferred_verifier_cannot_mistake_other_outcomes_for_denial(kind):
    outputs, direct = deferred_fixture()
    name = "patch_delete" if kind in {"success", "unrelated_error"} else (
        "resources_global" if kind == "nonempty_catalog" else "own_artifact_roundtrip")
    for part in outputs[1]["output"]:
        p = json.loads(part["text"])
        if p["probe"] != name:
            continue
        if kind == "success":
            p = {"probe": name, "result": "patch applied"}
        elif kind == "unrelated_error":
            p["error"] = "cannot decode private bytes"
        elif kind == "nonempty_catalog":
            p["result"] = json.dumps({"resources": [{"uri": "file:///private"}]})
        elif kind == "wrong_content":
            p["result"]["content"][0]["text"] = '{}'
        elif kind == "wrong_actor":
            p["actor"] = "/root"
        else:
            p["result"]["isError"] = True
        part["text"] = json.dumps(p)
    assert not all(canaries.inspect_tool_outputs(outputs, direct, deferred_tools=True).values())


def test_deferred_targets_and_code_never_embed_private_marker(tmp_path):
    probe = canaries.Canaries(tmp_path, deferred_tools=True)
    try:
        for actor in ("/root", "/root/identity_child"):
            code = probe.code(agent=actor)
            assert all(name in code for name in canaries.DEFERRED_PATCHES)
            assert probe.secrets["file"] not in code
            assert "list_mcp_resource_templates" in code and "list_mcp_resources" in code
        report = probe.report([])
        assert report["checks"]["private_binary_unchanged"]
        assert report["checks"]["no_patch_targets_created"]
        assert not report["checks"]["patch_delete_both_denied"]
        probe.protected.unlink()
        probe.absent_targets[0].write_text("unexpected", encoding="utf-8")
        report = probe.report([])
        assert not report["checks"]["private_file_unchanged"]
        assert not report["checks"]["no_patch_targets_created"]
    finally:
        probe.close()


def test_removed_patch_requires_absence_and_direct_dispatch_rejection_for_both_actors():
    outputs, direct = deferred_fixture()
    for item in outputs[:2]:
        for part in item["output"]:
            p = json.loads(part["text"])
            if p["probe"] == "catalog":
                p["names"].remove("apply_patch")
            elif p["probe"] == "outside_patch" or p["probe"] in canaries.DEFERRED_PATCHES:
                p["error"] = "TypeError: tools.apply_patch is not a function"
            part["text"] = json.dumps(p)
    patches = ["patch-root", "patch-child"]
    outputs += [{"call_id": name, "native_agent": actor, "output": "unsupported custom tool call: apply_patch"}
        for name, actor in zip(patches, ("/root", "/root/identity_child"))]
    functions = ["patch-function-root", "patch-function-child"]
    outputs += [{"call_id": name, "native_agent": actor, "output": "unsupported call: apply_patch"}
        for name, actor in zip(functions, ("/root", "/root/identity_child"))]
    assert all(canaries.inspect_tool_outputs(outputs, direct, deferred_tools=True,
        patch_disabled=True, patch_direct_calls=patches, patch_function_calls=functions).values())
    outputs[-1]["output"] = "apply_patch verification failed: read private bytes"
    assert not canaries.inspect_tool_outputs(outputs, direct, deferred_tools=True,
        patch_disabled=True, patch_direct_calls=patches,
        patch_function_calls=functions)["direct_patch_function_dispatch_both_denied"]
