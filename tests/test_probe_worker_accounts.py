"""Strict private account declaration checks; no token or provider access."""

import json
from pathlib import Path

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator import probe_worker_inputs as module
from test_probe_saved_bodies import PLAYER


def account(cache):
    path = Path(cache) / "account.json"
    path.write_bytes(canonical({"schema": "strata/MinecraftAccount/1", "account": "synthetic-avatar",
                               "profile_id": PLAYER.replace("-", "")}))
    return path


def test_account_declaration_is_strict_and_never_reads_tokens(tmp_path, monkeypatch):
    path = account(tmp_path)
    original = json.loads(path.read_bytes())
    config = {"auth_cache": str(tmp_path), "username": "synthetic-avatar", "expected_player_uuid": PLAYER}
    reads = []
    real = module.private_read
    monkeypatch.setattr(module, "private_read", lambda p, limit: (reads.append(Path(p).name), real(p, limit))[1])
    assert module.account_declaration(config)[0].samefile(path)
    for patch, code in [({"schema": "unknown"}, "PROBE_WORKER_ACCOUNT"),
                        ({"account": "foreign"}, "PROBE_WORKER_ACCOUNT"),
                        ({"account": 2}, "PROBE_WORKER_ACCOUNT"),
                        ({"extra": True}, "PROBE_WORKER_ACCOUNT"),
                        ({"profile_id": None}, "AWAITING_OPERATOR_AUTH"),
                        ({"profile_id": 1}, "AWAITING_OPERATOR_AUTH"),
                        ({"profile_id": "Z" * 32}, "AWAITING_OPERATOR_AUTH"),
                        ({"profile_id": "b" * 32}, "PROBE_WORKER_ACCOUNT_MISMATCH")]:
        path.write_bytes(canonical(original | patch))
        with pytest.raises(Fault, match=code):
            module.account_declaration(config)
    path.write_bytes(b'{"schema":"x","schema":"y"}')
    with pytest.raises(Fault):
        module.account_declaration(config)
    assert set(reads) == {"account.json"}
