"""Selected-profile fixture scope refusals; no model or native launch in tests."""

import importlib.util
import copy
import json
from pathlib import Path
import sys

import pytest

from mcbench.storage import Fault

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("state_fixture", TOOLS / "native_mcp_identity_probe.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
sys.path.pop(0)


@pytest.mark.parametrize("change", [
    {"selected_state_boundary": 1}, {"state_mode": False}, {"bootstrap_mode": False},
    {"ingress_mode": False}, {"oauth_mode": False}, {"model": "gpt-5.6-luna"},
    {"tool_projections": None}, {"no_patch_catalog": None}, {"canary_mode": True},
    {"inherited_helper": True}, {"gateway_mode": True}, {"skills_mode": True},
    {"retirement_mode": True}, {"interrupt_mode": True}, {"activation_source": "other"},
    {"game_probe": object()}, {"piloting_contract": True}, {"runtime_boundary": True},
])
def test_incompatible_selected_state_profile_refuses_before_setup(tmp_path, change, monkeypatch):
    monkeypatch.syspath_prepend(str(TOOLS))
    options = dict(broker_mode=True, admission_mode=True, state_mode=True, bootstrap_mode=True,
                   ingress_mode=True, oauth_mode=True, model="gpt-6-luna", tool_projections={},
                   no_patch_catalog=tmp_path / "absent-catalog", selected_state_boundary=True)
    options.update(change)
    with pytest.raises(Fault, match="SELECTED_STATE_BOUNDARY_REQUIRED"):
        fixture.run(tmp_path / "absent-binary", tmp_path / "absent-output", **options)
    assert not (tmp_path / "absent-output").exists()


@pytest.mark.parametrize("change", [
    {"selected_retirement_boundary": 1}, {"retirement_mode": False}, {"bootstrap_mode": False},
    {"ingress_mode": False}, {"oauth_mode": False}, {"model": "gpt-5.6-luna"},
    {"tool_projections": None}, {"no_patch_catalog": None}, {"canary_mode": True},
    {"inherited_helper": True}, {"gateway_mode": True}, {"skills_mode": True},
    {"state_mode": True}, {"interrupt_mode": True}, {"activation_source": "other"},
    {"game_probe": object()}, {"piloting_contract": True}, {"runtime_boundary": True},
    {"selected_state_boundary": True},
])
def test_incompatible_selected_retirement_profile_refuses_before_setup(tmp_path, change, monkeypatch):
    monkeypatch.syspath_prepend(str(TOOLS))
    options = dict(broker_mode=True, admission_mode=True, retirement_mode=True, bootstrap_mode=True,
                   ingress_mode=True, oauth_mode=True, model="gpt-6-luna", tool_projections={},
                   no_patch_catalog=tmp_path / "absent-catalog", selected_retirement_boundary=True)
    options.update(change)
    with pytest.raises(Fault, match="SELECTED_RETIREMENT_BOUNDARY_REQUIRED"):
        fixture.run(tmp_path / "absent-binary", tmp_path / "absent-output", **options)
    assert not (tmp_path / "absent-output").exists()


@pytest.mark.parametrize("value", [True, 1, "true"])
def test_notification_retirement_requires_selected_profile(tmp_path, monkeypatch, value):
    monkeypatch.syspath_prepend(str(TOOLS))
    with pytest.raises(Fault, match="RETIREMENT_NOTIFICATIONS_REQUIRE_SELECTED_PROFILE"):
        fixture.run(tmp_path / "absent-binary", tmp_path / "absent-output", retirement_notifications=value)
    assert not (tmp_path / "absent-output").exists()


@pytest.mark.parametrize("case", ["positive", "missing", "rejected_forwarded", "wrong_digest", "duplicate",
                                  "no_credential", "unknown_forwarded", "duplicate_admitted", "empty",
                                  "received_unforwarded", "malformed_identity"])
def test_upstream_credentials_join_only_exact_forwarded_requests(case):
    rows = [{"operation_id": "accepted", "request_digest": "a" * 64, "forwarded": True},
            {"operation_id": "denied", "request_digest": "b" * 64, "forwarded": False}]
    upstream = [{"operation_id": "accepted", "request_digest": "a" * 64, "authorization_present": True}]
    if case == "missing":
        upstream.clear()
    elif case == "rejected_forwarded":
        upstream.append({"operation_id": "denied", "request_digest": "b" * 64, "authorization_present": True})
    elif case == "wrong_digest":
        upstream[0]["request_digest"] = "b" * 64
    elif case == "duplicate":
        upstream.append(copy.deepcopy(upstream[0]))
    elif case == "no_credential":
        upstream[0]["authorization_present"] = False
    elif case == "unknown_forwarded":
        rows[1]["forwarded"] = None
    elif case == "duplicate_admitted":
        rows.append(copy.deepcopy(rows[0]))
    elif case == "empty":
        rows.clear()
        upstream.clear()
    elif case == "received_unforwarded":
        rows[1].pop("forwarded")
        rows[1]["state"] = "RECEIVED"
    elif case == "malformed_identity":
        rows[0]["operation_id"] = upstream[0]["operation_id"] = None
    assert fixture.upstream_credential_coverage(rows, upstream) == (case in {"positive", "received_unforwarded"})


@pytest.fixture
def notification_fixture(monkeypatch):
    monkeypatch.syspath_prepend(str(TOOLS))
    from native_state_boundary import SelectedStateCanaries
    probe = SelectedStateCanaries()
    actor = "/root"
    call = probe.start(actor, "op", "")
    output = {"type": "custom_tool_call_output", "call_id": call["call_id"],
              "output": [{"type": "input_text", "text": '{"probe":"state_notification_return","result":"returned"}'}]}
    notification = {"type": "custom_tool_call_output", "call_id": call["call_id"],
                    "output": json.dumps({"probe": "state_notification", "value": probe.markers[actor]})}
    return probe, actor, {"input": [output, notification]}


def test_owned_notification_is_separate_and_retains_unfiltered_evidence(notification_fixture):
    probe, actor, body = notification_fixture
    probe.observe(actor, body)
    probe.observe(actor, copy.deepcopy(body))
    assert len(probe.notifications) == 1
    assert len(probe.outputs) == 1
    assert probe.notification_requests[0]["body"] == body
    assert probe.outputs[body["input"][0]["call_id"]]["output"] == body["input"][0]["output"]
    assert not probe.report()["checks"]["notification_exact_owned_outputs"]


@pytest.mark.parametrize("case", ["foreign_actor", "foreign_marker", "wrong_call", "wrong_type",
                                  "extra_payload", "wrong_phase", "changed_result", "changed_notification"])
def test_notify_exception_cannot_hide_wrong_actor_or_changed_result(notification_fixture, case):
    probe, actor, body = notification_fixture
    probe.observe(actor, body)
    changed = copy.deepcopy(body)
    item = changed["input"][1]
    if case == "foreign_actor":
        actor = "/root/identity_child"
    elif case == "foreign_marker":
        item["output"] = item["output"].replace("ROOT", "HELPER")
    elif case == "wrong_call":
        item["call_id"] = "foreign"
    elif case == "wrong_type":
        item["type"] = "function_call_output"
    elif case == "extra_payload":
        item["output"] = json.dumps(json.loads(item["output"]) | {"extra": "leak"})
    elif case == "wrong_phase":
        probe.calls[item["call_id"]]["phase"] = "own_wait"
    elif case == "changed_result":
        changed["input"][0]["output"][0]["text"] += "changed"
    else:
        item["output"] += " "
    with pytest.raises(Fault, match="STATE_(NOTIFICATION_(INVALID|CHANGED)|OUTPUT_CHANGED)"):
        probe.observe(actor, changed)


@pytest.mark.parametrize("case", ["positive", "duplicate", "contradictory", "extra", "integer_boolean",
                                  "missing", "duplicate_end", "boolean_end", "wrong_owner"])
def test_state_records_require_exact_single_positive_controls(monkeypatch, case):
    monkeypatch.syspath_prepend(str(TOOLS))
    from native_state_boundary import ACTORS, SelectedStateCanaries, inspect_state_records
    probe = SelectedStateCanaries()
    for actor in ACTORS:
        own = probe.markers[actor]
        rows = {
            "initialize": [{"probe": "initial_state", "empty": True, "foreign": True},
                           {"probe": "own_initial", "value": own}],
            "store_read": [{"probe": "own_later", "value": own, "foreign": True}],
            "own_wait": [{"probe": "own_completion", "value": own}, {"probe": "cell_end", "at_ms": 2000}],
        }
        if actor == ACTORS[1]:
            if case in {"duplicate", "contradictory"}:
                value = copy.deepcopy(rows["store_read"][0])
                if case == "contradictory":
                    value["foreign"] = False
                rows["store_read"].append(value)
            elif case == "extra":
                rows["store_read"][0]["unexpected"] = "private"
            elif case == "integer_boolean":
                rows["initialize"][0]["empty"] = 1
            elif case == "missing":
                rows["initialize"].pop()
            elif case == "duplicate_end":
                rows["own_wait"].append(copy.deepcopy(rows["own_wait"][-1]))
            elif case == "boolean_end":
                rows["own_wait"][-1]["at_ms"] = True
            elif case == "wrong_owner":
                rows["store_read"][0]["value"] = probe.markers[ACTORS[0]]
        for phase, values in rows.items():
            key = actor + phase
            probe.calls[key] = {"agent": actor, "phase": phase}
            probe.outputs[key] = {"output": "\n".join(json.dumps(v) for v in values)}
    assert all(inspect_state_records(probe).values()) == (case == "positive")
