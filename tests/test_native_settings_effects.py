"""Strict private wire records and synthetic transport faults; no Minecraft effect claim."""

import copy
import json

import pytest
from pydantic import ValidationError

from mcbench.native_game import GameConnection, GameResponse, NativeGameClient
from mcbench.native_settings_effects import (
    EffectOutcomeUnknown, EffectRequest, EffectResult, NativeSettingsEffectsClient,
)
from mcbench.storage import Fault

FP = "b" * 64


def connection():
    return GameConnection.model_validate({"schema": "strata/NativeGameConnection/1", "host": "127.0.0.1",
        "port": 12345, "session_id": "session", "bearer_token": "c" * 64, "fingerprint": "a" * 64,
        "operator_development_only": True})


def request():
    return {"id": "effect", "transaction_id": "transaction", "expected_revision": 3,
        "expected_digest": "d" * 64, "plan_digest": "e" * 64, "binding_id": "curios:key.curios.open.desc:0",
        "context": "IN_GAME", "stage": "before_restart", "hold_ms": 50, "settle_ticks": 2}


def visible(tick=1, context="IN_GAME"):
    return {"client_tick": tick, "context": context, "screen": "none" if context == "IN_GAME" else "fixture.Screen",
        "window_active": True, "menu_id": 0, "menu_type": "fixture.Menu", "x": 1.0, "y": 64.0, "z": 2.0,
        "sneaking": False, "sprinting": False, "using_item": False}


def result():
    return {"schema": "strata/NativeSettingsEffects/2", "request": request(), "state": "observed",
        "error_code": None, "verified": False, "committed": False, "observations": [
            {"index": 0, "phase": "admission", "value": {"schema": "strata/NativeSettingsEffectAdmission/2",
                "settings_fingerprint": FP, "request": request()}},
            {"index": 1, "phase": "before", "value": visible()},
            {"index": 2, "phase": "released", "value": visible(2, "GUI")},
            {"index": 3, "phase": "released", "value": visible(3, "GUI")}]}


def client():
    return NativeSettingsEffectsClient(connection(), FP)


def test_valid_trace_is_observed_never_verified_or_committed():
    value = EffectResult.model_validate(result())
    assert value.state == "observed" and value.verified is False and value.committed is False
    assert client()._result("settings_effect_start", request(), result()) == result()


def test_baseline_has_no_transaction_and_never_accepts_legacy_result_schema():
    baseline = request() | {"stage": "baseline", "transaction_id": None}
    assert EffectRequest.model_validate(baseline).transaction_id is None
    for invalid in [baseline | {"transaction_id": "invented"},
                    request() | {"transaction_id": None},
                    request() | {"stage": "after_restart", "transaction_id": None}]:
        with pytest.raises((ValidationError, Fault)):
            EffectRequest.model_validate(invalid)
    with pytest.raises(ValidationError):
        EffectResult.model_validate(result() | {"schema": "strata/NativeSettingsEffects/1"})


@pytest.mark.parametrize("field,value", [("hold_ms", 0), ("hold_ms", 2001), ("hold_ms", True),
    ("settle_ticks", 0), ("settle_ticks", 201), ("expected_revision", 0), ("expected_revision", 2**53),
    ("stage", "unverified"), ("context", "UNKNOWN"), ("expected_digest", "x"), ("raw_key", 302)])
def test_request_rejects_unbounded_or_untyped_input(field, value):
    with pytest.raises((ValidationError, Fault)):
        EffectRequest.model_validate(request() | {field: value})


@pytest.mark.parametrize("field,value", [("verified", True), ("committed", True), ("verified", 0),
    ("committed", 0), ("error_code", "FAILURE"), ("state", "pass"), ("source", "private")])
def test_result_cannot_invent_a_pass_or_unknown_contract(field, value):
    with pytest.raises((ValidationError, Fault)):
        EffectResult.model_validate(result() | {field: value})


@pytest.mark.parametrize("mutation", [
    lambda v: v["observations"].pop(0),
    lambda v: v["observations"].pop(),
    lambda v: v["observations"][1].update(index=0),
    lambda v: v["observations"][0]["value"]["request"].update(transaction_id="foreign"),
    lambda v: v["observations"][1]["value"].update(context="GUI", screen="fixture.Screen"),
    lambda v: v["observations"][3].update(phase="held"),
    lambda v: v["observations"][3]["value"].update(client_tick=0),
    lambda v: v["observations"][2]["value"].update(x=float("nan")),
    lambda v: v["observations"][2]["value"].update(window_active=1),
    lambda v: v["observations"][2]["value"].update(hidden_inventory=[]),
])
def test_trace_order_identity_and_visible_payload_are_strict(mutation):
    value = result()
    mutation(value)
    with pytest.raises((ValidationError, Fault)):
        EffectResult.model_validate(value)


def test_cancelled_screen_opening_is_only_raw_evidence():
    value = result()
    value["observations"].insert(2, {"phase": "screen_opening", "index": 2,
        "value": {"client_tick": 1, "from_screen": "none", "requested_screen": "fixture.Screen",
                  "cancelled_at_observer": True}})
    for index, observation in enumerate(value["observations"]):
        observation["index"] = index
    assert not EffectResult.model_validate(value).verified


@pytest.mark.parametrize("state,error", [("prepared", None), ("refused", "SETTINGS_CONTEXT_UNVERIFIED"),
                                         ("unknown", "EVIDENCE_UNAVAILABLE")])
def test_empty_failure_or_prepared_trace_does_not_fabricate_admission(state, error):
    value = result() | {"state": state, "error_code": error, "observations": []}
    assert EffectResult.model_validate(value).state == state


def test_status_requires_original_expected_plan_even_for_matching_effect_id():
    value = result()
    value["request"]["plan_digest"] = "f" * 64
    value["observations"][0]["value"]["request"] = copy.deepcopy(value["request"])
    with pytest.raises(Fault, match="IDENTITY_MISMATCH"):
        client()._result("settings_effect_status", {"id": "effect"}, value, EffectRequest.model_validate(request()))
    with pytest.raises(Fault, match="REQUEST_INVALID"):
        client().call("settings_effect_status", {"id": "effect"})


def test_admission_source_fingerprint_must_match_separately_pinned_settings_runtime():
    value = result()
    value["observations"][0]["value"]["settings_fingerprint"] = "f" * 64
    with pytest.raises(Fault, match="IDENTITY_MISMATCH"):
        client()._result("settings_effect_start", request(), value)


def test_actual_gameplay_client_still_refuses_operator_settings():
    with pytest.raises(Fault, match="CAPABILITY_MISSING"):
        NativeGameClient(connection()).call("settings_effect_start", request())


def exchange_result(c, monkeypatch, transform=lambda v: v, accepted=False):
    sent = []
    request_id = None

    def exchange(method, path, body, timeout):
        nonlocal request_id
        sent.append((method, path))
        if body is not None:
            request_id = json.loads(body)["request_id"]
        pending = accepted and len(sent) == 1
        return GameResponse.model_validate({"schema": "strata/NativeGameResponse/1",
            "request_id": request_id, "session_id": c.connection.session_id,
            "status": "accepted" if pending else "completed", "error_code": None,
            "result": None if pending else transform(result())})

    monkeypatch.setattr(c._transport, "_exchange", exchange)
    return sent


def test_single_post_and_session_fenced_get_polling(monkeypatch):
    c = client()
    sent = exchange_result(c, monkeypatch, accepted=True)
    assert c.call("settings_effect_start", request()) == result()
    assert [method for method, _ in sent] == ["POST", "GET"]


@pytest.mark.parametrize("mode", ["lost_reply", "invalid_result", "wrong_identity"])
def test_ambiguous_mutation_never_posts_twice(monkeypatch, mode):
    c = client()
    sent = []

    def exchange(method, path, body, timeout):
        sent.append(method)
        if mode == "lost_reply":
            raise TimeoutError()
        value = result()
        if mode == "invalid_result":
            value["verified"] = True
        return GameResponse.model_validate({"schema": "strata/NativeGameResponse/1",
            "request_id": "foreign" if mode == "wrong_identity" else json.loads(body)["request_id"],
            "session_id": "session", "status": "completed", "error_code": None, "result": value})

    monkeypatch.setattr(c._transport, "_exchange", exchange)
    with pytest.raises(EffectOutcomeUnknown) as caught:
        c.call("settings_effect_start", request())
    assert sent == ["POST"]
    assert caught.value.transaction_id == "transaction" and caught.value.effect_id == "effect"
    assert "c" * 64 not in str(caught.value)


def test_invalid_request_never_reaches_transport(monkeypatch):
    c = client()
    monkeypatch.setattr(c._transport, "_exchange", lambda *args: pytest.fail("must reject before network"))
    with pytest.raises(Fault, match="REQUEST_INVALID"):
        c.call("settings_effect_start", request() | {"password": "private-canary"})


def test_descriptor_requires_both_pins_and_never_prints_credentials(tmp_path):
    path = tmp_path / "connection.json"
    value = connection().model_dump(mode="json", by_alias=True)
    value["bearer_token"] = "c" * 64
    path.write_text(json.dumps(value))
    assert NativeSettingsEffectsClient.from_file(path, game_fingerprint="a" * 64,
                                                settings_fingerprint=FP).connection.session_id == "session"
    for broken in [value | {"fingerprint": "f" * 64}, value | {"unknown": "private-canary"},
                   value | {"operator_development_only": 1}]:
        path.write_text(json.dumps(broken))
        with pytest.raises(Fault) as caught:
            NativeSettingsEffectsClient.from_file(path, game_fingerprint="a" * 64, settings_fingerprint=FP)
        assert "private-canary" not in str(caught.value) and "c" * 64 not in str(caught.value)
