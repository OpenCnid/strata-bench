"""Corruption tests for media evidence; synthetic outputs do not prove isolation."""

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("output_boundary", TOOLS / "native_output_boundary.py")
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
sys.path.pop(0)


def captured():
    probes = [{"probe": "output_boundary_globals", "result": dict.fromkeys(
        ("image", "audio", "generatedImage", "notify"), "function")},
        {"probe": "output_boundary_public_data_image", "result": "returned"}]
    probes += [{"probe": "output_boundary_" + name, "error": error}
               for name, error in boundary.MEDIA_DENIALS.items()]
    return [{"call_id": actor + "-call", "native_agent": actor,
             "output": [{"type": "input_text", "text": json.dumps(p)} for p in probes]
             + [{"type": "input_image", "image_url": boundary.PUBLIC_PNG}]}
            for actor in sorted(boundary.ACTORS)]


def passes(outputs):
    return all(boundary.inspect_output_boundary(outputs)["checks"].values())


def test_identical_context_repeats_are_allowed_conflicts_are_not():
    outputs = captured()
    assert passes(outputs + copy.deepcopy(outputs))
    changed = copy.deepcopy(outputs)
    changed[0]["output"][0]["text"] += " "
    assert not passes(outputs + changed)


@pytest.mark.parametrize("index", range(9))
def test_missing_helper_case_or_image_fails(index):
    outputs = captured()
    outputs[1]["output"].pop(index)
    assert not passes(outputs)


@pytest.mark.parametrize("index", range(9))
def test_duplicate_case_or_image_fails(index):
    outputs = captured()
    outputs[0]["output"].append(copy.deepcopy(outputs[0]["output"][index]))
    assert not passes(outputs)


@pytest.mark.parametrize("value", ["file:///private.png", "C:/private.png", "http://localhost/private.png",
                                  "data:image/png;base64,cHJpdmF0ZQ==", None])
def test_arbitrary_media_cannot_substitute_for_public_control(value):
    outputs = captured()
    outputs[0]["output"][-1]["image_url"] = value
    assert not passes(outputs)


@pytest.mark.parametrize("index", range(2, 8))
@pytest.mark.parametrize("change", [{"error": "unrelated failure"}, {"result": "private data"},
                                    {"unexpected": "private data"}])
def test_unrecognized_denial_and_error_with_success_or_extra_fields_fail(index, change):
    outputs = captured()
    chunk = outputs[0]["output"][index]
    value = json.loads(chunk["text"])
    value.update(change)
    chunk["text"] = json.dumps(value)
    assert not passes(outputs)


@pytest.mark.parametrize("actor", [None, "/foreign", "/root"])
def test_actor_provenance_cannot_be_missing_foreign_or_duplicated(actor):
    outputs = captured()
    outputs[1]["native_agent"] = actor
    assert not passes(outputs)


@pytest.mark.parametrize("chunk", [None, {"type": "input_audio", "data": "private"},
                                    {"type": "input_text", "text": '{"probe":"output_boundary_unknown","result":true}'}])
def test_extra_unknown_route_or_output_type_fails(chunk):
    outputs = captured()
    outputs[0]["output"].append(chunk)
    assert not passes(outputs)


def test_private_image_target_is_owned_and_not_the_positive_control(tmp_path):
    fixture = boundary.OutputBoundaryCanaries(tmp_path, deferred_tools=True, patch_disabled=True)
    try:
        assert fixture.private_png.parent == tmp_path
        for actor in boundary.ACTORS:
            code = fixture.code(agent=actor)
            assert fixture.private_png.as_uri() in code
            assert fixture.public_png in code
            assert fixture.url in code
        assert not fixture.unauthorized
    finally:
        fixture.close()
