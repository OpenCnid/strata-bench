"""Same RPC envelope and nested-action fixtures as the TypeScript validator."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcbench.contracts import RpcRequest
from test_public_record_semantics import CORPUS, assign, at

RPC = json.loads((Path(__file__).parent / "fixtures/rpc_semantics.json").read_text())
ACTIONS = [case for case in CORPUS["cases"] if CORPUS["profiles"][case["base"]]["record"] == "ActionBatch"]


def check(body, valid):
    before = copy.deepcopy(body)
    if valid:
        result = RpcRequest.model_validate_json(json.dumps(body)).model_dump(exclude_unset=True)
        assert result == body
    else:
        with pytest.raises(ValidationError):
            RpcRequest.model_validate_json(json.dumps(body))
    assert body == before


@pytest.mark.parametrize("case", RPC["cases"], ids=lambda c: c["id"])
def test_rpc_envelope(case):
    check(copy.deepcopy(RPC["base"] | case["set"]), case["valid"])


@pytest.mark.parametrize("case", ACTIONS, ids=lambda c: c["id"])
def test_rpc_nested_action(example, case):
    action = example("ActionBatch")
    for path, value in CORPUS["profiles"][case["base"]]["set"].items():
        assign(action, path, value)
    for target, source in case.get("copy", {}).items():
        assign(action, target, at(action, source))
    for path, value in case["set"].items():
        assign(action, path, value)
    check(RPC["base"] | {"method": "act", "action": action}, case["valid"])
