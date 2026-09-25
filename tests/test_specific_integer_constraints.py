"""Specific native limits must survive Pydantic alias metadata precedence."""

import pytest
from pydantic import ValidationError

from mcbench.native_game import GameAuthority


@pytest.mark.parametrize("value", [0, 1, True, 2.0, "2", 2**53])
def test_game_authority_requires_at_least_two_primitives(value):
    body = {
        "schema": "strata/NativeGameAuthority/1",
        "campaign_id": "c1",
        "agent_id": "a1",
        "capability_digest": "a" * 64,
        "body_fingerprint": "b" * 64,
        "expires_unix_ms": 1000,
        "primitive_limit": value,
    }
    with pytest.raises(ValidationError):
        GameAuthority.model_validate(body)
    assert GameAuthority.model_validate(body | {"primitive_limit": 2}).primitive_limit == 2
    assert GameAuthority.model_json_schema()["properties"]["primitive_limit"]["minimum"] == 2
