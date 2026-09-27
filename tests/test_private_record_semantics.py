"""Operator-only shared cross-language cases; no private instance or credential."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import RECORDS
from test_public_record_semantics import assign, at

CORPUS = json.loads((Path(__file__).parent / "fixtures/private_record_semantics.json").read_text())


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_private_record_semantics(example, case):
    profile = CORPUS["profiles"][case["base"]]
    body = example(profile["record"])
    for path, value in profile["set"].items():
        assign(body, path, value)
    for target, source in case.get("copy", {}).items():
        assign(body, target, at(body, source))
    for path, value in case["set"].items():
        assign(body, path, value)
    before = copy.deepcopy(body)
    model = RECORDS[f"mcbench/{profile['record']}/1"]
    if case["valid"]:
        assert model.model_validate_json(json.dumps(body)).model_dump() == body
    else:
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(body))
    assert body == before
