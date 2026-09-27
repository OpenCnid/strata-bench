"""Essential case completeness and declared effects; synthetic input only."""

import copy

import pytest

from mcbench.native_essential_plan import EssentialCase, NativeEssentialInputs, evaluate_case
from mcbench.storage import Fault
from mcbench.native_control_plan import FIXED_ESCAPE
from test_native_effect_evidence import expectation
from test_native_settings_effects import device_release_result
from test_native_repair_flow import flow_env as _flow_env, native_env as _native_env, repair_env as _repair_env

flow_env, native_env, repair_env = _flow_env, _native_env, _repair_env


def unavailable(requirements):
    return [{k: s[k] for k in ("role", "context", "stage")} | {"expectation": None,
        "unverified_reason": "NATURAL_PREREQUISITE_UNAVAILABLE", "motion_axis": None, "minimum_motion": 0.0}
        for s in requirements]


def test_complete_manifest_retains_unavailable_cases_and_cannot_authorize_commit(flow_env):
    e, worker, native, flow, calls, _, _ = flow_env
    flow.apply("tx", "owner", e.epoch, worker, native)
    essentials = NativeEssentialInputs(e.repairs)
    slots, _, _ = essentials.requirements("tx", "owner", e.epoch, worker, native)
    assert len(slots) == 66 and all(s["binding_id"] is None for s in slots)
    cases = unavailable(slots)
    with pytest.raises(Fault, match="ESSENTIAL_CASES_INCOMPLETE"):
        essentials.register("tx", "owner", e.epoch, worker, native, cases[:-1])
    ref = essentials.register("tx", "owner", e.epoch, worker, native, cases)
    assert essentials.register("tx", "owner", e.epoch, worker, native, cases) == ref
    changed = copy.deepcopy(cases)
    changed[0]["unverified_reason"] = "DIFFERENT_PREREQUISITE"
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        essentials.register("tx", "owner", e.epoch, worker, native, changed)
    with pytest.raises(Fault, match="ESSENTIAL_CONTEXT_UNVERIFIED"):
        essentials.capture("tx", "owner", e.epoch, worker, native, "escape", "GUI", "before_restart")
    coverage = essentials.coverage("tx")
    assert all(c["status"] == "unverified_context" for c in coverage["cases"])
    assert coverage["recovery_qualification_required"] and not coverage["input_cases_complete"]
    assert not coverage["essential_controls_verified"] and "settings_effect_start" not in calls
    # A mutable database declaration cannot replace the immutable private plan.
    with e.database.transaction() as db:
        db.execute("UPDATE repair_essential_plans SET body='{}' WHERE id='tx'")
    with pytest.raises(Fault, match="ESSENTIAL_EVIDENCE_INVALID"):
        essentials.coverage("tx")


def motion_case(role, delta):
    raw = device_release_result("keyboard", 32 if role == "jump" else 87)
    for o in raw["observations"]:
        if o["phase"] == "released":
            o["value"] |= {"context": "IN_GAME", "screen": "none"}
            for key, change in zip(("x", "y", "z"), delta):
                o["value"][key] += change
    case = {"role": role, "context": "IN_GAME", "stage": "before_restart",
        "expectation": expectation(raw) | {"predicate": "screen_unchanged" if role == "jump" else "horizontal_motion",
            "final_screen": "none", "min_horizontal_distance": 0.0 if role == "jump" else .1,
            "max_horizontal_distance": 2.0}, "unverified_reason": None,
        "motion_axis": [0.0, 1.0, 0.0] if role == "jump" else [1.0, 0.0, 0.0], "minimum_motion": .1}
    return case, raw


@pytest.mark.parametrize("role", ["forward", "back", "left", "right", "jump"])
@pytest.mark.parametrize("direction", [1, -1, 0])
def test_essential_movement_requires_declared_direction_not_any_displacement(role, direction):
    delta = (0.0, .5 * direction, 0.0) if role == "jump" else (.5 * direction, 0.0, 0.0)
    case, raw = motion_case(role, delta)
    result = evaluate_case(case, raw)
    assert result["status"] == ("pass" if direction == 1 else "fail")
    assert not result["qualification_implied"]


def test_sprint_needs_visible_new_sprint_not_just_motion():
    case, raw = motion_case("sprint", (.5, 0.0, 0.0))
    assert evaluate_case(case, raw)["status"] == "fail"
    held = copy.deepcopy(raw["observations"][1])
    held["phase"] = "held"
    held["value"]["sprinting"] = True
    raw["observations"].insert(2, held)
    for i, o in enumerate(raw["observations"]):
        o["index"] = i
    assert evaluate_case(case, raw)["status"] == "pass"
    raw["observations"][1]["value"]["sprinting"] = True
    assert evaluate_case(case, raw)["status"] == "fail"


@pytest.mark.parametrize("change", [
    {"motion_axis": None}, {"motion_axis": [0.0, 0.0, 0.0]}, {"motion_axis": [1.0, 1.0, 0.0]},
    {"motion_axis": [float("nan"), 0.0, 0.0]}, {"minimum_motion": 0.0}, {"unverified_reason": "MISSING"},
    {"stage": "after_restart"}])
def test_essential_cases_cannot_omit_or_change_the_effect_declaration(change):
    case, _ = motion_case("forward", (.5, 0.0, 0.0))
    with pytest.raises(ValueError):
        EssentialCase.model_validate(case | change)


def test_offline_coverage_rejoins_physical_release_to_declared_binding(flow_env, monkeypatch):
    e, _, _, _, _, _, _ = flow_env
    essential = NativeEssentialInputs(e.repairs)
    raw = device_release_result("keyboard", 256)
    raw["request"]["binding_id"] = FIXED_ESCAPE
    raw["observations"][0]["value"]["request"]["binding_id"] = FIXED_ESCAPE
    case = {"role": "escape", "context": raw["request"]["context"], "stage": raw["request"]["stage"],
        "expectation": expectation(raw), "unverified_reason": None, "motion_axis": None, "minimum_motion": 0.0}
    case_id = ":".join((case["role"], case["context"], case["stage"]))
    plan_ref = essential.flow._put({"fixture": "declared-essential-input"})
    monkeypatch.setattr(essential, "_plan", lambda transaction: ({"source_ref": plan_ref}, {"cases": [case]}))
    witness = {"schema": "strata/NativeEssentialInputWitness/1", "transaction_id": "tx",
        "is_example": e.controller.simulation, "case_id": case_id, "binding_digest": "b" * 64,
        "plan_ref": plan_ref, "result": raw, "verdict": evaluate_case(case, raw)}
    source = essential.flow._put(witness)
    with e.database.transaction() as db:
        db.execute("INSERT INTO repair_essential_cases VALUES (?,?,?,'TERMINAL',?)", ("tx", case_id, "b" * 64, source))
    assert essential.coverage("tx")["cases"][0]["status"] == witness["verdict"]["status"]
    # An internally consistent effect/verdict can still refer to the wrong physical key.
    receipt = next(o["value"] for o in raw["observations"] if o["phase"] == "input_release")
    receipt.update(key=257, release_order=[257])
    witness["verdict"] = evaluate_case(case, raw)
    wrong = essential.flow._put(witness)
    with e.database.transaction() as db:
        db.execute("UPDATE repair_essential_cases SET source_ref=? WHERE id='tx'", (wrong,))
    with pytest.raises(Fault, match="ESSENTIAL_RELEASE_IDENTITY_MISMATCH"):
        essential.coverage("tx")
