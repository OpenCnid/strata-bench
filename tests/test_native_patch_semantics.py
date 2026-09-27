"""Shared Python/Java wire cases; these do not claim real keybinding effects."""
import copy
import json
from pathlib import Path

import pytest

from mcbench.native_settings import NativePatch
from test_public_record_semantics import assign

CORPUS = json.loads((Path(__file__).parent / "fixtures/native_patch_semantics.json").read_text())


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_native_patch_semantics(case):
    body = copy.deepcopy(CORPUS["base"])
    for path, value in case["set"].items():
        assign(body, path, value)
    before = copy.deepcopy(body)
    if case["valid"]:
        assert NativePatch.model_validate_json(json.dumps(body)).model_dump() == body
    else:
        with pytest.raises(ValueError):
            NativePatch.model_validate_json(json.dumps(body))
    assert body == before
