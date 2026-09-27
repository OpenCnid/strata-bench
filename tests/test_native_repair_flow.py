"""Controller repair completion with explicitly synthetic native and verification evidence."""

import copy

import pytest

from mcbench.native_repair_flow import NativeRepairFlow
from mcbench.native_settings_effects import EffectOutcomeUnknown
from mcbench.storage import Fault, digest
from test_native_control_plan import native_env as _native_env, repair_env as _repair_env

native_env, repair_env = _native_env, _repair_env


def verification(e):
    plan = e.controls.status("tx")["plan"]
    return e.adapter.verify_and_restart({name: c["after"] for name, c in plan["changes"].items()},
        transaction_id="tx", plan_digest=digest(plan), binding_checks=plan["binding_checks"])


@pytest.fixture
def flow_env(native_env, monkeypatch):
    e, worker, client, target, calls, _, _, snapshot = native_env
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    original = client.call
    phase, mode, decision = ["planned"], ["ok"], []
    def call(operation, args, **kwargs):
        if operation not in {"settings_apply", "settings_status", "settings_commit", "settings_commit_status", "settings_rollback"}:
            return original(operation, args, **kwargs)
        calls.append(operation)
        if operation == "settings_apply":
            assert phase[0] == "planned"
            for name, change in args["changes"].items():
                assert snapshot["bindings"][name]["runtime_value"] == change["before"]
                snapshot["bindings"][name] |= {"runtime_value": change["after"], "persisted_value": change["after"]}
            snapshot["active_transaction"], snapshot["active_phase"] = "tx", "applied_pending_verification"
            phase[0] = "applied_pending_verification"
        elif operation == "settings_commit":
            assert phase[0] == "applied_pending_verification"
            assert args["expected_revision"] == snapshot["revision"] and args["expected_digest"] == snapshot["digest"]
            decision.append(copy.deepcopy(args))
            phase[0] = "committed"
            snapshot["active_transaction"] = snapshot["active_phase"] = None
        elif operation == "settings_rollback":
            phase[0] = "rolled_back"
            snapshot["bindings"]["target"] |= {"runtime_value": "key.keyboard.b", "persisted_value": "key.keyboard.b"}
            snapshot["active_transaction"] = snapshot["active_phase"] = None
        if operation in {"settings_apply", "settings_commit", "settings_rollback"}:
            snapshot["revision"] += 1
            snapshot["digest"] = digest(snapshot["bindings"])
            if mode[0] == "lost-" + operation:
                raise EffectOutcomeUnknown("lost", operation, "tx", None)
        if operation in {"settings_commit", "settings_commit_status"}:
            return {"schema": "strata/NativeSettingsCommitState/1", "decision": decision[0],
                "phase": phase[0], "revision": snapshot["revision"], "committed": phase[0] == "committed",
                "input_resumed": False, "effects_verified_by_native": False}
        return {"transaction_id": "tx", "phase": phase[0], "revision": snapshot["revision"], "committed": phase[0] == "committed"}
    monkeypatch.setattr(client, "call", call)
    return e, worker, client, NativeRepairFlow(e.repairs), calls, mode, snapshot


def test_native_controller_apply_verified_commit_and_rollback_preserve_hold(flow_env):
    e, worker, client, flow, calls, _, _ = flow_env
    assert flow.apply("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "verifying"
    proofs = verification(e)
    receipt = flow.commit("tx", "owner", e.epoch, worker, client, proofs)
    assert receipt["control"]["phase"] == "committed"
    assert receipt["repair"]["phase"] == "AWAITING_OBSERVATION"
    witness = e.cas.json(e.operator, "operator", receipt["source_ref"])
    proof = e.cas.json(e.operator, "operator", witness["request"]["verification_ref"])
    assert proof["verification"] == proofs and proof["is_example"] is True
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
    assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
    with pytest.raises(Fault, match="NATIVE_SETTINGS_ADAPTER_REQUIRED"):
        e.repairs.rollback("tx", "owner", e.epoch)
    with pytest.raises(Fault, match="NATIVE_SETTINGS_ADAPTER_REQUIRED"):
        e.controls.rollback("tx")
    assert flow.rollback("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "rolled_back"
    assert [op for op in calls if op in {"settings_apply", "settings_commit", "settings_rollback"}] == ["settings_apply", "settings_commit", "settings_rollback"]
    assert not e.adapter.requests  # No independent generic settings writer.


@pytest.mark.parametrize("operation", ["apply", "commit", "rollback"])
def test_lost_native_write_reply_only_queries_status(flow_env, operation):
    e, worker, client, flow, calls, mode, _ = flow_env
    if operation != "apply":
        flow.apply("tx", "owner", e.epoch, worker, client)
    args = (verification(e),) if operation == "commit" else ()
    mode[0] = "lost-settings_" + operation
    method = getattr(flow, operation)
    with pytest.raises(EffectOutcomeUnknown):
        method("tx", "owner", e.epoch, worker, client, *args)
    mode[0] = "ok"
    result = method("tx", "owner", e.epoch, worker, client, *args)
    assert result["control"]["phase"] == {"apply": "verifying", "commit": "committed", "rollback": "rolled_back"}[operation]
    assert calls.count("settings_" + operation) == 1
    assert ("settings_commit_status" if operation == "commit" else "settings_status") in calls


@pytest.mark.parametrize("missing", ["restart-persistence", "intended-effect", "binding", "source", "wrong-plan"])
def test_incomplete_or_foreign_verification_never_dispatches_commit(flow_env, missing):
    e, worker, client, flow, calls, _, _ = flow_env
    flow.apply("tx", "owner", e.epoch, worker, client)
    proofs = verification(e)
    if missing in proofs["checks"]:
        del proofs["checks"][missing]
    elif missing == "binding":
        proofs["binding_checks"].pop()
    elif missing == "source":
        proofs["checks"]["restart-persistence"]["refs"] = ["cas:sha256:" + "0" * 64]
    else:
        proofs["plan_digest"] = "0" * 64
    with pytest.raises(Fault):
        flow.commit("tx", "owner", e.epoch, worker, client, proofs)
    assert "settings_commit" not in calls
    assert e.controls.status("tx")["phase"] == "verifying"


def test_unrelated_native_key_change_prevents_commit(flow_env):
    e, worker, client, flow, calls, _, snapshot = flow_env
    flow.apply("tx", "owner", e.epoch, worker, client)
    snapshot["bindings"]["competing"]["runtime_value"] = "key.keyboard.f"
    with pytest.raises(Fault, match="REPAIR_STATE_MISMATCH"):
        flow.commit("tx", "owner", e.epoch, worker, client, verification(e))
    assert "settings_commit" not in calls


def test_unpublished_native_success_requires_recovery_and_can_rollback(flow_env, monkeypatch):
    e, worker, client, flow, _, _, _ = flow_env
    put = flow._put
    monkeypatch.setattr(flow, "_put", lambda _: (_ for _ in ()).throw(OSError("synthetic storage fault")))
    with pytest.raises(OSError):
        flow.apply("tx", "owner", e.epoch, worker, client)
    assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"
    monkeypatch.setattr(flow, "_put", put)
    assert flow.rollback("tx", "owner", e.epoch, worker, client)["control"]["phase"] == "rolled_back"


def test_consumed_commit_intent_cannot_adopt_different_verification(flow_env):
    e, worker, client, flow, calls, mode, _ = flow_env
    flow.apply("tx", "owner", e.epoch, worker, client)
    proofs = verification(e)
    mode[0] = "lost-settings_commit"
    with pytest.raises(EffectOutcomeUnknown):
        flow.commit("tx", "owner", e.epoch, worker, client, proofs)
    mode[0] = "ok"
    changed = copy.deepcopy(proofs) | {"unexpected": "different immutable decision"}
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        flow.commit("tx", "owner", e.epoch, worker, client, changed)
    assert calls.count("settings_commit") == 1 and "settings_commit_status" not in calls


def test_profile_writer_lock_covers_native_dispatch(flow_env):
    from mcbench.control_lock import profile_operation
    e, worker, client, flow, calls, _, _ = flow_env
    with profile_operation(e.database, e.controls.status("tx")["plan"]["profile_id"]):
        with pytest.raises(Fault, match="SETTINGS_BUSY"):
            flow.apply("tx", "owner", e.epoch, worker, client)
    assert "settings_apply" not in calls


def test_profile_writer_lock_covers_native_admission(native_env):
    from mcbench.control_lock import profile_operation
    e, worker, client, target, calls, _, _, _ = native_env
    with profile_operation(e.database, e.controls.status("tx")["plan"]["profile_id"]):
        with pytest.raises(Fault, match="SETTINGS_BUSY"):
            e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert "settings_repair_bind" not in calls
