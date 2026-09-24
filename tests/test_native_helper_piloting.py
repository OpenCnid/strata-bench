"""The explicit one-helper profile cannot widen the existing zero-helper case."""
import pytest

from mcbench.native_piloting import prompt, require_profile
from mcbench.storage import Fault
import test_native_piloting as old
from native_pilot_report import delivered_helper_reply

gateway, provider, permit, pilot = old.gateway, old.provider, old.permit, old.pilot


@pytest.fixture
def helper_profile(pilot):
    _, _, plan, config, _ = pilot
    scope = {k: getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch")}
    config.max_requests = 16
    config.max_handlers = 2
    plan = plan.model_copy(update={"helper_limit": 1, "hard_timeout_s": 240, "model": "gpt-6-luna",
        "prompt": prompt(scope, "lease-1", 16, 240, helper_limit=1),
        "gateway_config_digest": config.profile_fingerprint()})
    config.profile_digest = plan.profile_digest()
    return plan, config


def test_explicit_helper_profile_preserves_root_action_selection(helper_profile):
    plan, config = helper_profile
    require_profile(plan, config, "lease-1")
    assert "fork_turns=none" in plan.prompt
    assert "one model response" in plan.prompt and "Only you control the avatar" in plan.prompt
    assert "16 combined root/helper model requests and 240 seconds" in plan.prompt
    assert "Choose a support block yourself" in plan.prompt
    assert "At most two act calls" in plan.prompt


@pytest.mark.parametrize("field,value", [("helper_limit", 0), ("helper_limit", 2),
    ("hard_timeout_s", 241), ("hard_timeout_s", 180), ("model", "gpt-5.6-luna"), ("role", "helper")])
def test_mismatched_helper_scope_rejected(helper_profile, field, value):
    plan, config = helper_profile
    plan = plan.model_copy(update={field: value})
    config.profile_digest = plan.profile_digest()
    with pytest.raises(Fault, match="PILOT_SCOPE"):
        require_profile(plan, config, "lease-1")


@pytest.mark.parametrize("field,value", [("max_requests", 17), ("max_requests", 12),
    ("helper_calls_bound", 2), ("max_handlers", 3), ("max_handlers", 1)])
def test_helper_gateway_bounds_are_exact(helper_profile, field, value):
    plan, config = helper_profile
    setattr(config, field, value)
    plan = plan.model_copy(update={"gateway_config_digest": config.profile_fingerprint()})
    config.profile_digest = plan.profile_digest()
    with pytest.raises(Fault, match="PILOT_SCOPE"):
        require_profile(plan, config, "lease-1")


def final_message():
    return {"type": "agent_message", "author": "/root/review", "recipient": "/root", "content": [{
        "type": "input_text", "text": "Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/review\nPayload:\nIndependent assessment"}]}


def test_native_single_part_and_split_reply_delivery():
    message = final_message()
    assert delivered_helper_reply(message, "/root/review")
    message["content"][0]["text"] = message["content"][0]["text"].removesuffix("Independent assessment")
    assert not delivered_helper_reply(message, "/root/review")
    message["content"].append({"type": "encrypted_content", "encrypted_content": "synthetic-opaque-reply"})
    assert delivered_helper_reply(message, "/root/review")


@pytest.mark.parametrize("case", ["root_copy", "foreign_helper", "wrong_recipient", "new_task", "false_header", "blank", "tool_output"])
def test_spoofed_or_empty_delivery_does_not_count(case):
    message = final_message()
    if case == "root_copy":
        message["author"] = "/root"
    elif case == "foreign_helper":
        message["author"] = "/root/other"
    elif case == "wrong_recipient":
        message["recipient"] = "/root/other"
    elif case == "tool_output":
        message["type"] = "function_call_output"
    else:
        message["content"][0]["text"] = message["content"][0]["text"].replace(
            "FINAL_ANSWER" if case == "new_task" else "Sender: /root/review" if case == "false_header" else "Independent assessment",
            "NEW_TASK" if case == "new_task" else "Sender: /root/other" if case == "false_header" else " ")
    assert not delivered_helper_reply(message, "/root/review")
