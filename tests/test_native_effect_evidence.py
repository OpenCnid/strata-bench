"""Synthetic predicate failures and immutable evidence plans; no native qualification."""

import copy

import pytest

from mcbench.native_effect_evidence import EffectExpectation, NativeEffectEvidence, evaluate_effect
from mcbench.storage import Fault, digest
from test_native_settings_effects import result as effect_result
from test_native_repair_flow import flow_env as _flow_env, native_env as _native_env, repair_env as _repair_env, verification

flow_env, native_env, repair_env = _flow_env, _native_env, _repair_env


def expectation(raw):
    return {"schema": "strata/NativeEffectExpectation/1", "request": raw["request"],
        "settings_fingerprint": raw["observations"][0]["value"]["settings_fingerprint"],
        "predicate": "screen_transition", "initial_screen": "none", "final_screen": "fixture.Screen",
        "required_openings": [], "forbidden_openings": ["fixture.CompetingScreen"],
        "min_horizontal_distance": 0.0, "max_horizontal_distance": .25}


def test_evaluator_cannot_turn_raw_observation_into_qualification_or_resume():
    raw = effect_result()
    verdict = evaluate_effect(expectation(raw), raw)
    assert verdict["status"] == "pass" and not verdict["qualification_implied"] and not verdict["input_resume_authorized"]
    assert raw["verified"] is False and raw["committed"] is False


@pytest.mark.parametrize("failure,reason", [
    ("inactive", "WINDOW_INACTIVE"), ("wrong_final", "SETTLED_SCREEN_MISMATCH"),
    ("wrong_initial", "INITIAL_SCREEN_MISMATCH"), ("missing_open", "REQUIRED_OPENING_MISSING"),
    ("competing", "COMPETING_SCREEN_OPENED"), ("movement", "MOVEMENT_BOUND_EXCEEDED"),
    ("incomplete", "EFFECT_NOT_OBSERVED"),
])
def test_missing_or_competing_effect_is_retained_as_failure(failure, reason):
    raw = effect_result()
    expected = expectation(raw)
    if failure == "inactive":
        raw["observations"][-1]["value"]["window_active"] = False
    elif failure == "wrong_final":
        raw["observations"][-1]["value"]["screen"] = "fixture.WrongScreen"
    elif failure == "wrong_initial":
        expected["initial_screen"] = "fixture.OtherScreen"
    elif failure == "missing_open":
        expected["required_openings"] = ["fixture.Screen"]
    elif failure == "movement":
        raw["observations"][-1]["value"]["x"] += 10
    elif failure == "incomplete":
        raw["state"] = "running"
        raw["observations"].pop()
    else:
        raw["observations"].insert(2, {"index": 2, "phase": "screen_opening", "value": {
            "client_tick": 1, "from_screen": "none", "requested_screen": "fixture.CompetingScreen", "cancelled_at_observer": False}})
        for i, item in enumerate(raw["observations"]):
            item["index"] = i
    verdict = evaluate_effect(expected, raw)
    assert verdict["status"] == "fail" and reason in verdict["reasons"]


@pytest.mark.parametrize("failure", ["plan", "fingerprint", "request_id", "revision", "stage"])
def test_foreign_identity_is_rejected_without_a_verdict(failure):
    raw = effect_result()
    expected = copy.deepcopy(expectation(raw))
    if failure == "fingerprint":
        expected["settings_fingerprint"] = "0" * 64
    else:
        key, value = {"plan": ("plan_digest", "0" * 64), "request_id": ("id", "foreign"),
            "revision": ("expected_revision", 99), "stage": ("stage", "after_restart")}[failure]
        expected["request"][key] = value
    with pytest.raises(Fault, match="EFFECT_EVIDENCE_IDENTITY_MISMATCH"):
        evaluate_effect(expected, raw)


@pytest.mark.parametrize("patch", [
    {"min_horizontal_distance": 1.0}, {"max_horizontal_distance": 0.0},
    {"predicate": "horizontal_motion"}, {"final_screen": "none"},
    {"required_openings": ["fixture.CompetingScreen"]}, {"required_openings": ["fixture.Screen"] * 2},
    {"max_horizontal_distance": float("nan")}, {"extra": True},
])
def test_ambiguous_or_unbounded_expectations_are_refused(patch):
    with pytest.raises(ValueError):
        EffectExpectation.model_validate(expectation(effect_result()) | patch)


@pytest.mark.parametrize("failure", ["failed_effect", "witness_storage"])
def test_failed_or_unpublished_effect_cannot_be_rerun_or_reinterpreted(flow_env, monkeypatch, failure):
    e, worker, native, flow, calls, _, snapshot = flow_env
    flow.apply("tx", "owner", e.epoch, worker, native)
    producer = NativeEffectEvidence(e.repairs)
    plan = e.controls.status("tx")["plan"]
    values = []
    for i, slot in enumerate(plan["binding_checks"]):
        raw = effect_result()
        raw["request"] |= {"id": "check-" + str(i), "transaction_id": "tx", "plan_digest": digest(plan),
            "expected_revision": snapshot["revision"], "expected_digest": snapshot["digest"],
            **{k: slot[k] for k in ("binding_id", "context", "stage")}}
        expected = expectation(raw)
        expected["settings_fingerprint"] = native.settings_fingerprint
        values.append(expected)
    with pytest.raises(Fault, match="EFFECT_EXPECTATION_INCOMPLETE"):
        producer.register("tx", "owner", e.epoch, worker, native, values[:-1])
    producer.register("tx", "owner", e.epoch, worker, native, values)
    original = native.call
    emitted = []

    def effect(operation, args, **kwargs):
        if operation not in {"settings_effect_start", "settings_effect_status"}:
            return original(operation, args, **kwargs)
        emitted.append(operation)
        raw = effect_result()
        raw["request"] = values[0]["request"]
        raw["observations"][0]["value"] |= {"request": raw["request"], "settings_fingerprint": native.settings_fingerprint}
        if failure == "failed_effect":
            raw["observations"][-1]["value"]["window_active"] = False
        return raw

    monkeypatch.setattr(native, "call", effect)
    if failure == "witness_storage":
        original_put = producer.flow._put
        monkeypatch.setattr(producer.flow, "_put", lambda _: (_ for _ in ()).throw(OSError("synthetic CAS publication failure")))
        with pytest.raises(OSError):
            producer.capture("tx", "owner", e.epoch, worker, native, "check-0")
        monkeypatch.setattr(producer.flow, "_put", original_put)
    outcome = producer.capture("tx", "owner", e.epoch, worker, native, "check-0")
    assert producer.capture("tx", "owner", e.epoch, worker, native, "check-0") == outcome
    assert emitted == (["settings_effect_start", "settings_effect_status"] if failure == "witness_storage"
                       else ["settings_effect_start"])
    assert outcome["check"]["status"] == ("fail" if failure == "failed_effect" else "pass")
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        producer.register("tx", "owner", e.epoch, worker, native, [dict(v, final_screen="fixture.Other") for v in values])
    if failure == "failed_effect":
        proofs = verification(e)
        proofs["binding_checks"][0] = outcome["check"]
        with pytest.raises(Fault, match="EFFECT_VERIFICATION_FAILED"):
            flow.commit("tx", "owner", e.epoch, worker, native, proofs)
        assert "settings_commit" not in calls


@pytest.mark.parametrize("failure", [None, "missing", "legacy", "wrong_key", "failed_effect", "forged_verdict", "foreign_source"])
def test_complete_matrix_uses_recorded_release_and_effects_without_essential_claim(flow_env, monkeypatch, failure):
    from test_native_settings_effects import release_result
    e, worker, native, flow, calls, _, snapshot = flow_env
    flow.apply("tx", "owner", e.epoch, worker, native)
    producer = NativeEffectEvidence(e.repairs)
    plan = e.controls.status("tx")["plan"]
    values = []
    for i, slot in enumerate(plan["binding_checks"]):
        raw = effect_result()
        raw["request"] |= {"id": "matrix-" + str(i), "transaction_id": "tx", "plan_digest": digest(plan),
            "expected_revision": snapshot["revision"], "expected_digest": snapshot["digest"],
            **{k: slot[k] for k in ("binding_id", "context", "stage")}}
        values.append(expectation(raw) | {"settings_fingerprint": native.settings_fingerprint})
    producer.register("tx", "owner", e.epoch, worker, native, values)
    original = native.call
    def effect(operation, args, **kwargs):
        if operation != "settings_effect_start":
            return original(operation, args, **kwargs)
        key = plan["changes"].get(args["binding_id"], {}).get("after", plan["backup"][args["binding_id"]])
        raw = effect_result() if failure == "legacy" else release_result(key["code"] if failure != "wrong_key" else 69)
        raw["request"] = args
        raw["observations"][0]["value"] |= {"request": args, "settings_fingerprint": native.settings_fingerprint}
        if failure == "failed_effect":
            raw["observations"][-1]["value"]["window_active"] = False
        return raw
    monkeypatch.setattr(native, "call", effect)
    for value in values[:-1] if failure == "missing" else values:
        producer.capture("tx", "owner", e.epoch, worker, native, value["request"]["id"])
    if failure in {"forged_verdict", "foreign_source"}:
        row = e.database.connection.execute("SELECT * FROM repair_effects WHERE id='tx' LIMIT 1").fetchone()
        body = e.cas.json(e.operator, "operator", row["source_ref"])
        if failure == "forged_verdict":
            body["verdict"]["reasons"] = ["fabricated"]
        else:
            body["transaction_id"] = "foreign"
        bad = producer.flow._put(body)
        with e.database.transaction() as db:
            db.execute("UPDATE repair_effects SET source_ref=? WHERE id='tx' AND effect_id=?", (bad, row["effect_id"]))
    errors = {"missing": "EFFECT_EVIDENCE_INCOMPLETE", "legacy": "EFFECT_RELEASE_EVIDENCE_REQUIRED",
        "wrong_key": "EFFECT_RELEASE_EVIDENCE_MISMATCH", "forged_verdict": "EFFECT_EVIDENCE_INVALID",
        "foreign_source": "EFFECT_EVIDENCE_IDENTITY_MISMATCH"}
    if failure in errors:
        with pytest.raises(Fault, match=errors[failure]):
            producer.effect_checks("tx", "owner", e.epoch, worker, native)
        return
    actual = producer.effect_checks("tx", "owner", e.epoch, worker, native)
    assert set(actual["checks"]) == {"intended-effect", "competing-effect", "keys-released"}
    assert all(c["status"] == ("fail" if failure == "failed_effect" else "pass") for c in actual["checks"].values())
    assert len(actual["binding_checks"]) == len(values)
    assert "settings_commit" not in calls
    assert producer.effect_checks("tx", "owner", e.epoch, worker, native) == actual
    if failure is None:
        original_reader = e.controls.evidence_reader
        e.controls.evidence_reader = lambda ref, max_bytes: (original_reader(ref, max_bytes=max_bytes)
            if ref in e.adapter.evidence else e.cas.read(e.operator, "operator", ref, max_bytes=max_bytes))
        proofs = verification(e)
        proofs["checks"].update(actual["checks"])
        proofs["binding_checks"] = actual["binding_checks"]
        del proofs["checks"]["essential-controls"]
        with pytest.raises(Fault, match="EFFECT_VERIFICATION_FAILED"):
            flow.commit("tx", "owner", e.epoch, worker, native, proofs)
        assert "settings_commit" not in calls
