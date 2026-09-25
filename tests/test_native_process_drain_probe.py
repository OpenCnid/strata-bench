"""Focused fixture sequence/negative tests; native evidence is separate."""

import importlib
import json
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_process_drain_probe")


def test_no_claim_before_each_owned_yield_and_reply(module):
    probe = module.ProcessDrainCanaries()
    assert not all(probe.report()["checks"].values())
    root, helper = module.ACTORS
    assert "setTimeout(r,90000)" in probe.next(root, 1, "root-start")[0]["input"]
    assert "text(" not in probe.next(helper, 1, "child-start")[0]["input"].split("await yield_control()")[0]
    for actor in (root, helper):
        with pytest.raises(Fault):
            if actor == helper:
                probe.next(actor, 2, "no-yield")
            else:
                probe.delivered = True
                probe.next(actor, 6, "no-yield")


def test_join_waits_for_observed_delivery_not_provider_completion_flag(module):
    probe = module.ProcessDrainCanaries()
    root, helper = module.ACTORS
    probe.finished.add(helper)
    for step in (3, 4, 5):
        call = probe.next(root, step, "join" + str(step))[0]
        assert call["name"] == "wait_agent" and json.loads(call["arguments"])["timeout_ms"] == 10000
    with pytest.raises(Fault, match="PROCESS_DRAIN_HELPER_DELIVERY_BOUND"):
        probe.next(root, 6, "exhausted")


@pytest.mark.parametrize("change", [{"author": "/foreign"}, {"recipient": "/foreign"},
                                  {"type": "message"}, {"content": []}])
def test_wrong_actor_or_shape_cannot_fake_helper_delivery(module, change):
    probe = module.ProcessDrainCanaries()
    root, helper = module.ACTORS
    item = {"type": "agent_message", "author": helper, "recipient": root,
            "content": [{"type": "input_text", "text": "Message Type: FINAL_ANSWER\nPayload:\n" + module.CHILD_DONE}]}
    probe.observe(root, {"input": [item | change]})
    assert not probe.delivered
    probe.observe(root, {"input": [item]})
    assert probe.delivered


@pytest.mark.parametrize("value", [True, 1, "true"])
def test_process_drain_mode_cannot_escape_selected_scope(module, tmp_path, value):
    from native_mcp_identity_probe import run
    with pytest.raises(Fault, match="PROCESS_DRAIN_REQUIRES_SELECTED_STATE"):
        run(tmp_path / "absent", tmp_path / "uncreated", process_drain_mode=value)
    assert not (tmp_path / "uncreated").exists()
