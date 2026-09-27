"""Paired release identity and sprint observations; synthetic bodies only."""

import copy

import pytest

from mcbench.native_essential_plan import evaluate_case, require_release_identity
from mcbench.native_settings_effects import EffectResult
from mcbench.native_settings_projection import decode_native_key
from mcbench.storage import Fault
from test_native_essential_plan import motion_case
from test_native_effect_evidence import expectation
from test_native_settings_effects_jvm import effects_jvm as _effects_jvm, apply, effect, terminal, ORIGINAL

effects_jvm = _effects_jvm


def paired_case():
    case, raw = motion_case("sprint", (.5, 0.0, 0.0))
    raw["schema"] = "strata/NativeSettingsEffects/5"
    receipt = next(o["value"] for o in raw["observations"] if o["phase"] == "input_release")
    receipt.update(schema="strata/NativeInputRelease/3", key=341, companion=87, release_order=[87, 341])
    held = copy.deepcopy(raw["observations"][1])
    held["phase"] = "held"
    held["value"]["sprinting"] = True
    raw["observations"].insert(2, held)
    for i, o in enumerate(raw["observations"]):
        o["index"] = i
    plan = {"changes": {}, "backup": {raw["request"]["binding_id"]: decode_native_key("key.keyboard.left.control"),
        "forward": decode_native_key("key.keyboard.w")}}
    return case, raw, plan


def test_paired_release_requires_both_exact_planned_controls():
    case, raw, plan = paired_case()
    assert evaluate_case(case, raw)["status"] == "pass"
    request = EffectResult.model_validate(raw).request
    require_release_identity(request, raw, plan, "forward")
    with pytest.raises(Fault, match="ESSENTIAL_RELEASE_IDENTITY_MISMATCH"):
        require_release_identity(request, raw, plan)
    plan["backup"]["forward"] = decode_native_key("key.keyboard.s")
    with pytest.raises(Fault, match="ESSENTIAL_RELEASE_IDENTITY_MISMATCH"):
        require_release_identity(request, raw, plan, "forward")


@pytest.mark.parametrize("change", [
    {"companion": 341, "release_order": [341, 341]}, {"companion": 340, "release_order": [340, 341]},
    {"companion": 0, "release_order": [0, 341]}, {"release_order": [341, 87]},
    {"modifier": "SHIFT"}, {"device": "mouse"}, {"callbacks_confirmed": False}, {"clear_confirmed": False}])
def test_invalid_paired_receipt_refuses(change):
    _, raw, _ = paired_case()
    next(o["value"] for o in raw["observations"] if o["phase"] == "input_release").update(change)
    with pytest.raises(ValueError):
        EffectResult.model_validate(raw)


@pytest.mark.parametrize("version", [2, 3, 4])
def test_old_effect_profiles_cannot_carry_paired_input(version):
    _, raw, _ = paired_case()
    raw["schema"] = f"strata/NativeSettingsEffects/{version}"
    with pytest.raises(ValueError):
        EffectResult.model_validate(raw)


def test_actual_java_pair_reports_movement_sprint_and_reverse_release(effects_jvm):
    options = ORIGINAL + "key_key.forward:key.keyboard.w\r\nkey_key.sprint:key.keyboard.left.control\r\n"
    with effects_jvm(options_text=options) as (client, process, profile, _):
        snapshot = apply(client)
        request = effect(snapshot, hold=150).model_copy(update={"binding_id": "minecraft:key.sprint:0"})
        client.call("settings_effect_start", request.model_dump())
        raw = terminal(client, request)
        assert raw["schema"] == "strata/NativeSettingsEffects/5" and raw["state"] == "observed"
        case = {"role": "sprint", "context": "IN_GAME", "stage": "before_restart",
            "expectation": expectation(raw) | {"predicate": "horizontal_motion", "final_screen": "none",
                "min_horizontal_distance": .1, "max_horizontal_distance": 2.0}, "unverified_reason": None,
            "motion_axis": [1.0, 0.0, 0.0], "minimum_motion": .1}
        assert evaluate_case(case, raw)["status"] == "pass"
        require_release_identity(request, raw, {"changes": {}, "backup": {
            request.binding_id: decode_native_key("key.keyboard.left.control"),
            "forward": decode_native_key("key.keyboard.w")}}, "forward")
        client.call("settings_rollback", {"transaction_id": "tx"})
        assert (profile / "options.txt").read_bytes() == options.encode()
        assert process.poll() is None
