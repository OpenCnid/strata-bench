"""Fixture verifier negatives; actual pinned runtime evidence stays separate."""

import importlib
import json
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def m(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_helper_pair_probe")


def test_empty_report_proves_nothing(m):
    assert not any(m.HelperPairProbe().report()["checks"][k] for k in (
        "pair_native_simultaneous_running", "pair_three_finished", "pair_all_routed_messages_delivered"))


def test_root_waits_for_delivered_readiness_before_overlap_and_refusal(m):
    p = m.HelperPairProbe()
    for step, helper in enumerate(m.HELPERS, 1):
        call = p.next(m.ROOT, step, str(step))[0]
        assert json.loads(call["arguments"])["task_name"] == helper.rsplit("/", 1)[-1]
    assert p.next(m.ROOT, 3, "wait")[0]["name"] == "wait_agent"
    p.messages.update((h, m.ROOT, "MESSAGE", m.READY[h]) for h in m.HELPERS)
    assert p.next(m.ROOT, 4, "list")[0]["name"] == "list_agents"
    assert json.loads(p.next(m.ROOT, 5, "overflow")[0]["arguments"])["task_name"] == "overflow"


def test_helper_never_finishes_on_root_release_without_peer_delivery(m):
    p = m.HelperPairProbe()
    actor, peer = m.HELPERS
    p.next(actor, 1, "ready")
    assert p.next(actor, 2, "wait-release")[0]["name"] == "wait_agent"
    p.messages.add((m.ROOT, actor, "MESSAGE", m.RELEASE[actor]))
    assert json.loads(p.next(actor, 3, "advice")[0]["arguments"])["target"] == peer
    assert p.next(actor, 4, "wait-peer")[0]["name"] == "wait_agent"
    p.messages.add((peer, actor, "MESSAGE", m.ADVICE[peer]))
    assert p.next(actor, 5, "read")[0]["name"] == "exec"
    assert actor not in p.finished
    assert p.next(actor, 6, "final")[0]["content"][0]["text"] == m.DONE[actor]


@pytest.mark.parametrize("change", [{"author": "/foreign"}, {"recipient": "/foreign"},
                                   {"type": "message"}, {"content": []}])
def test_wrong_native_message_does_not_satisfy_delivery(m, change):
    p = m.HelperPairProbe()
    h = m.HELPERS[0]
    item = {"type": "agent_message", "author": h, "recipient": m.ROOT,
            "content": [{"type": "input_text", "text": "Message Type: MESSAGE\nTask name: /root\nSender: " +
                         h + "\nPayload:\n" + m.READY[h]}]}
    p.observe(m.ROOT, {"input": [item | change]})
    assert not p.received(h, m.ROOT, m.READY[h])
    p.observe(m.ROOT, {"input": [item]})
    assert p.received(h, m.ROOT, m.READY[h])


@pytest.mark.parametrize("payload_type", ["input_text", "encrypted_content"])
def test_separate_native_header_payload_requires_exact_shape(m, payload_type):
    p = m.HelperPairProbe()
    h = m.HELPERS[0]
    key = "text" if payload_type == "input_text" else "encrypted_content"
    header = "Message Type: MESSAGE\nTask name: /root\nSender: " + h + "\nPayload:\n"
    item = {"type": "agent_message", "author": h, "recipient": m.ROOT,
            "content": [{"type": "input_text", "text": header}, {"type": payload_type, key: m.READY[h]}]}
    p.observe(m.ROOT, {"input": [item]})
    assert p.received(h, m.ROOT, m.READY[h])
    for parts in ([item["content"][0]], [item["content"][0], item["content"][1] | {"extra": True}],
                  [{"type": "input_text", "text": header.replace(h, "/wrong")}, item["content"][1]]):
        p = m.HelperPairProbe()
        p.observe(m.ROOT, {"input": [item | {"content": parts}]})
        assert not p.received(h, m.ROOT, m.READY[h])


def test_waits_are_bounded(m):
    p = m.HelperPairProbe()
    for i in range(3):
        p.wait(m.ROOT, str(i))
    with pytest.raises(Fault, match="PAIR_DELIVERY_BOUND"):
        p.wait(m.ROOT, "over")


def test_root_readiness_and_completion_have_separate_bounded_rendezvous(m):
    p = m.HelperPairProbe()
    for phase in (2, 6):
        p.phases[m.ROOT] = phase
        for i in range(3):
            p.wait(m.ROOT, f"{phase}-{i}")
    assert p.waits[m.ROOT] == 6
    with pytest.raises(Fault, match="PAIR_DELIVERY_BOUND"):
        p.wait(m.ROOT, "seven")


def test_wrong_caller_and_changed_native_output_refuse(m):
    p = m.HelperPairProbe()
    call = p.start(m.ROOT, "one", "")
    out = {"type": "custom_tool_call_output", "call_id": call["call_id"], "output": "original"}
    with pytest.raises(Fault, match="PAIR_WRONG_CALLER"):
        p.observe(m.HELPERS[0], {"input": [out]})
    p.observe(m.ROOT, {"input": [out]})
    with pytest.raises(Fault, match="PAIR_CHANGED_OUTPUT"):
        p.observe(m.ROOT, {"input": [out | {"output": "changed"}]})


@pytest.mark.parametrize("value", [True, 1, "true"])
def test_requires_selected_profile_before_creating_files(m, tmp_path, value):
    from native_mcp_identity_probe import run
    with pytest.raises(Fault, match="SELECTED_HELPER_PAIR_REQUIRED"):
        run(tmp_path / "missing", tmp_path / "out", selected_helper_pair=value)
    assert not (tmp_path / "out").exists()
