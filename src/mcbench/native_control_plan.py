"""Exact private controller/native translation; no input or capability qualification."""

from typing import Literal

from pydantic import Field

from .contracts import Digest, Id, Key, Strict
from .native_settings import NativeSnapshot
from .native_settings_effects import NativeRepairAdmission
from .storage import digest, require


class NativeControlTarget(Strict):
    schema_: Literal["strata/NativeControlTarget/1"] = Field(alias="schema")
    profile_id: Id
    control_fingerprint: str = Field(min_length=1, max_length=256)
    policy_digest: Digest
    game_fingerprint: Digest
    settings_fingerprint: Digest
    body_fingerprint: Digest


# Minecraft1.19.2 InputConstants.Type's exact keysym names; this is encoding,
# never a tested physical-key pool. Unknown codes have no admitted translation.
KEYSYMS = {**{i: chr(i).lower() for i in range(65, 91)},
           **{i: chr(i) for i in range(48, 58)},
           **{i: f"f{i - 289}" for i in range(290, 315)},
           **{i: f"keypad.{i - 320}" for i in range(320, 330)},
           32: "space", 39: "apostrophe", 44: "comma", 45: "minus", 46: "period",
           47: "slash", 59: "semicolon", 61: "equal", 91: "left.bracket", 92: "backslash",
           93: "right.bracket", 96: "grave.accent", 161: "world.1", 162: "world.2",
           256: "escape", 257: "enter", 258: "tab", 259: "backspace", 260: "insert",
           261: "delete", 262: "right", 263: "left", 264: "down", 265: "up",
           266: "page.up", 267: "page.down", 268: "home", 269: "end", 280: "caps.lock",
           281: "scroll.lock", 282: "num.lock", 283: "print.screen", 284: "pause",
           330: "keypad.decimal", 331: "keypad.divide", 332: "keypad.multiply",
           333: "keypad.subtract", 334: "keypad.add", 335: "keypad.enter", 336: "keypad.equal",
           340: "left.shift", 341: "left.control", 342: "left.alt", 343: "left.win",
           344: "right.shift", 345: "right.control", 346: "right.alt", 347: "right.win", 348: "menu"}


def native_key(raw):
    key = Key.model_validate(raw)
    require(key.backend == "glfw" and len(key.modifiers) <= 1, "SETTINGS_KEY_ENCODING_UNSUPPORTED")
    if key.representation == "unbound":
        value = "key.keyboard.unknown"
    elif key.representation == "keysym":
        require(key.code in KEYSYMS, "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        value = "key.keyboard." + KEYSYMS[key.code]
    elif key.representation == "mouse_button":
        require(0 <= key.code <= 7, "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        value = "key.mouse." + ({0: "left", 1: "right", 2: "middle"}.get(key.code) or str(key.code + 1))
    else:
        require(key.representation == "scancode", "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        value = "scancode." + str(key.code)
    if key.modifiers:
        value += ":" + key.modifiers[0]
    require(key.persisted == value, "SETTINGS_KEY_ENCODING_MISMATCH")
    return value


def native_admission(plan, worker_plan, target: NativeControlTarget, snapshot):
    """Translate the entire immutable map, preserving native CAS independently."""
    native = NativeSnapshot.model_validate(snapshot)
    require(plan["profile_id"] == target.profile_id and plan["fingerprint"] == target.control_fingerprint
            and plan["policy_digest"] == target.policy_digest
            and native.fingerprint == target.settings_fingerprint, "REPAIR_PROFILE_MISMATCH")
    require(plan["transaction_id"] == worker_plan.transaction_id and plan["agent"] == worker_plan.agent_id
            and digest(plan) == worker_plan.plan_digest, "REPAIR_NOT_OWNED")
    require(native.active_transaction is None and set(native.bindings) == set(plan["backup"]),
            "SETTINGS_REVISION_CONFLICT")
    before = {name: native_key(key) for name, key in plan["backup"].items()}
    require(digest(plan["backup"]) == plan["keymap_digest"] and all(
        not binding.persisted_ambiguous and binding.runtime_value == binding.persisted_value == before[name]
        for name, binding in native.bindings.items()), "SETTINGS_REVISION_CONFLICT")
    changes = {}
    for name, change in plan["changes"].items():
        require(name in native.bindings and native.bindings[name].operator_mutable
                and change["before"] == plan["backup"][name], "PROTECTED_OR_UNKNOWN_BINDING")
        after = native_key(change["after"])
        require(change["after"]["representation"] != "unbound", "SETTINGS_KEY_ENCODING_UNSUPPORTED")
        changes[name] = {"before": before[name], "after": after}
    require(all(check["binding_id"] in before for check in plan["binding_checks"]), "BINDING_MISSING")
    # The complete reviewed map permits essential-control checks as well as
    # changed/competing bindings. Native consumer qualification still applies.
    return NativeRepairAdmission.model_validate({"schema": "strata/NativeSettingsRepairAdmission/1",
        "policy": "operator-owned-native-settings-repair/1", "worker_plan": worker_plan.model_dump(),
        "settings_fingerprint": target.settings_fingerprint, "effect_bindings": sorted(before),
        "patch": {"transaction_id": plan["transaction_id"], "expected_revision": native.revision,
                  "expected_digest": native.digest, "changes": changes}})
