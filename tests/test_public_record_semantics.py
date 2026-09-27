"""Shared wire fixtures; passing these does not qualify native settings effects."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.records import RECORDS

CORPUS = json.loads((Path(__file__).parent / "fixtures/public_record_semantics.json").read_text())


def at(body, path):
    for part in path.split("/"):
        body = body[int(part)] if isinstance(body, list) else body[part]
    return body


def assign(body, path, value):
    parts = path.split("/")
    parent = at(body, "/".join(parts[:-1])) if len(parts) > 1 else body
    key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
    if isinstance(parent, list) and key == len(parent):
        parent.append(copy.deepcopy(value))
    else:
        parent[key] = copy.deepcopy(value)


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_shared_public_record_semantics(example, case):
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
