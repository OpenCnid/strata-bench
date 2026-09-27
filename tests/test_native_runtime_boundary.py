"""Verifier corruption cases; these fixtures do not establish native isolation."""

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("runtime_boundary", TOOLS / "native_runtime_boundary.py")
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
sys.path.pop(0)


def output_fixture(monkeypatch):
    probes = [{"probe": "boundary_globals", "result": dict.fromkeys(boundary.IO_GLOBALS, "undefined")}]
    probes += [{"probe": "boundary_" + name, "result": "undefined"} for name in (
        "function_constructor", "host_constructor", "async_constructor")]
    probes += [{"probe": "boundary_" + name, "error": "unsupported import in exec"} for name in (
        "import_fs", "import_credentials", "import_process", "import_child_process", "import_file", "import_http")]
    probes += [{"probe": "boundary_artifact_" + name,
                "result": {"isError": True, "content": [{"type": "text", "text": code}]}}
               for name, code in {"absolute": "UNSAFE_PATH", "traversal": "UNSAFE_PATH",
                                  "ads": "UNSAFE_PATH", "cas": "UNSAFE_PATH",
                                  "foreign": "BROKER_FORBIDDEN"}.items()]
    return [{"call_id": actor + "-call", "native_agent": actor,
             "output": [{"text": json.dumps(p)} for p in probes]} for actor in sorted(boundary.ACTORS)]


def verdict(outputs):
    return all(boundary.inspect_boundary_outputs(outputs)["checks"].values())


def test_repeated_identical_context_is_deduplicated_but_changed_output_fails(monkeypatch):
    outputs = output_fixture(monkeypatch)
    assert verdict(outputs + copy.deepcopy(outputs))
    changed = copy.deepcopy(outputs)
    changed[0]["output"][0]["text"] += " "
    assert not verdict(outputs + changed)


@pytest.mark.parametrize("position", range(15))
def test_each_missing_helper_route_prevents_pass(monkeypatch, position):
    outputs = output_fixture(monkeypatch)
    outputs[1]["output"].pop(position)
    assert not verdict(outputs)


@pytest.mark.parametrize("route,value", [
    ("globals", {"process": "object"}),
    ("function_constructor", "object"), ("host_constructor", "object"),
    ("async_constructor", "object"), ("import_fs", "private content"),
    ("import_credentials", "private credential"),
    ("import_process", "private credential"), ("import_child_process", "function"),
    ("import_file", "private module"), ("import_http", {}),
    ("artifact_absolute", {"isError": False, "content": []}),
    ("artifact_traversal", {"isError": True, "content": [{"text": "unrelated"}]}),
    ("artifact_ads", None), ("artifact_cas", {}), ("artifact_foreign", "foreign note"),
])
def test_successful_private_access_or_unrelated_failure_is_never_a_denial(monkeypatch, route, value):
    outputs = output_fixture(monkeypatch)
    for row in outputs[0]["output"]:
        probe = json.loads(row["text"])
        if probe["probe"] == "boundary_" + route:
            row["text"] = json.dumps({"probe": probe["probe"], "result": value})
    assert not verdict(outputs)


@pytest.mark.parametrize("actor", [None, "/root", "/foreign"])
def test_unbound_or_duplicate_actor_cannot_supply_helper_evidence(monkeypatch, actor):
    outputs = output_fixture(monkeypatch)
    for item in outputs:
        item["native_agent"] = actor
    assert not verdict(outputs)


def test_unknown_import_exception_and_duplicate_probe_fail(monkeypatch):
    outputs = output_fixture(monkeypatch)
    bad = copy.deepcopy(outputs)
    bad[0]["output"][4]["text"] = json.dumps({"probe": "boundary_import_fs", "error": "unrelated error"})
    assert not verdict(bad)
    outputs[0]["output"].append(copy.deepcopy(outputs[0]["output"][0]))
    assert not verdict(outputs)


def test_runtime_canaries_only_target_owned_resources(tmp_path):
    canary = boundary.RuntimeBoundaryCanaries(tmp_path, deferred_tools=True, patch_disabled=True)
    try:
        for actor in boundary.ACTORS:
            script = canary.code(agent=actor)
            assert canary.module.as_uri() in script
            assert canary.url in script
            assert 'm.env.TEMP' in script
            assert 'auth.json' in script
            assert all(value not in script for value in canary.secrets.values())
        assert not canary.unauthorized
        assert canary.controls == ["/owned-control"]
    finally:
        canary.close()


def test_denial_cannot_hide_simultaneous_success_or_extra_fields(monkeypatch):
    outputs = output_fixture(monkeypatch)
    for extra in ({"result": "private content"}, {"extra": "private content"}):
        bad = copy.deepcopy(outputs)
        value = json.loads(bad[0]["output"][4]["text"])
        value.update(extra)
        bad[0]["output"][4]["text"] = json.dumps(value)
        assert not verdict(bad)
