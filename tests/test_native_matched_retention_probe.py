"""Matched synthetic seed and native fixture protocol; no scientific result."""

import copy

import pytest

from mcbench.native_skill_activation import active_files
from mcbench.storage import Fault, Principal
from test_native_selected_activation import selected_seed
from native_matched_retention_probe import MatchedActivationProbe, READS, PUBLICATION_CODE, HELPER_TASK, fresh_context
from native_mcp_identity_probe import run


@pytest.mark.parametrize("arm,boundary,has_skills", [
    ("full", "recovery", True), ("frozen-persistence", "recovery", True),
    ("full", "episode", True), ("frozen-persistence", "episode", False)])
def test_selected_seed_retains_within_episode_but_frozen_resets_at_boundary(
        database, cas, tmp_path, example, configs, arm, boundary, has_skills):
    source, service, ref = selected_seed(database, cas, tmp_path, example, configs, arm=arm, boundary=boundary)
    body = service.load(ref)
    assert bool(body["skills"]) is has_skills
    assert service.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 56
    probe = object.__new__(MatchedActivationProbe)
    probe.ref, probe.output = ref, tmp_path
    prepared = probe.prepare(source[0], source[1])
    assert prepared.helper_skill_activation_ref == prepared.skill_activation_ref == ref
    assert probe.arm == arm and probe.reset is (not has_skills)
    assert probe.calls("/root") == probe.calls("/root/identity_child")
    assert probe.publish_code() == PUBLICATION_CODE.replace("PUBLIC_EPOCH", "2")
    assert {p for p in active_files(body) if p.startswith("active/learned-crafting/")} <= set(READS)
    if not has_skills:
        assert body["workspace"] == database.checkpoint_fixture["initial"]
        assert probe.discarded
    else:
        assert cas.read(Principal("operator", "operator"), "operator",
                        body["skills"]["learned-crafting"]["files"]["SKILL.md"])


@pytest.mark.parametrize("value", [True, 1, None, "true"])
def test_matched_run_requires_selected_checkpoint_profile(tmp_path, value):
    with pytest.raises(Fault, match="MATCHED_RETENTION_PROFILE_REQUIRED"):
        run(tmp_path / "missing.exe", tmp_path, matched_retention=value)
    assert not list(tmp_path.iterdir())


def test_source_bound_native_completion_cannot_change_or_cross_actor():
    probe = object.__new__(MatchedActivationProbe)
    probe.calls_issued, probe.outputs, probe.initial = {}, {}, {}
    call = {"type": "custom_tool_call", "call_id": "owned", "namespace": "functions",
            "name": "exec", "input": "text(1);"}
    probe.expect_call("/root", call)
    body = {"input": [call, {"type": "custom_tool_call_output", "call_id": "owned", "output": [
        {"type": "input_text", "text": "Script completed\nWall time 0.1 seconds\nOutput:\n"}]}]}
    probe.observe("/root", body)
    probe.observe("/root", body)
    changed = copy.deepcopy(body)
    changed["input"][0]["input"] = "text(2);"
    with pytest.raises(Fault, match="MATCHED_RETENTION_CALL_CHANGED"):
        probe.observe("/root", changed)
    changed = copy.deepcopy(body)
    changed["input"][1]["output"] = "Script completed"
    with pytest.raises(Fault, match="MATCHED_RETENTION_RETURN_CHANGED"):
        probe.observe("/root", changed)
    with pytest.raises(Fault, match="MATCHED_RETENTION_REPLAY"):
        probe.expect_call("/root", call)
    with pytest.raises(Fault, match="MATCHED_RETENTION_ACTOR"):
        probe.observe("/foreign", body)


@pytest.mark.parametrize("change", [None, "foreign-author", "foreign-recipient", "extra-task", "old-tool", "old-answer", "extra-content", "secret-payload"])
def test_clean_helper_admits_only_exact_public_launch_message(change):
    task = {"type": "agent_message", "id": "opaque-native-message", "author": "/root", "recipient": "/root/identity_child",
        "content": [{"type": "input_text", "text": "Message Type: NEW_TASK\nTask name: /root/identity_child\nSender: /root\nPayload:\n"},
                    {"type": "encrypted_content", "encrypted_content": HELPER_TASK}]}
    body = {"input": [{"type": "message", "role": "developer", "content": []}, task]}
    if change == "foreign-author":
        task["author"] = "/other"
    elif change == "foreign-recipient":
        task["recipient"] = "/other"
    elif change == "extra-task":
        body["input"].append(copy.deepcopy(task))
    elif change == "old-tool":
        body["input"].append({"type": "custom_tool_call_output", "output": "old"})
    elif change == "old-answer":
        body["input"].append({"type": "message", "role": "assistant", "content": []})
    elif change == "extra-content":
        task["content"].append({"type": "input_text", "text": "old state"})
    elif change == "secret-payload":
        task["content"][1]["encrypted_content"] = "old state"
    assert fresh_context("/root/identity_child", body) is (change is None)
    assert not fresh_context("/root", body)
    assert fresh_context("/root", {"input": []})
    assert not fresh_context("/root/identity_child", {"input": []})
