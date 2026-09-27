"""Controller/native handoff with synthetic replies; no input qualification."""

import copy
import json

import pytest

from mcbench.native_control_plan import NativeControlTarget, native_key
from mcbench.native_settings_effects import EffectOutcomeUnknown, NativeRepairAdmission, NativeSettingsEffectsClient
from mcbench.storage import Fault, digest
from mcbench.worker_repair import POLICY, WorkerRepairClient, WorkerRepairGrant, WorkerRepairReply
from test_native_settings_effects import connection
from test_reconfiguration import repair_env as _repair_env

repair_env = _repair_env


def physical(code, name):
    return {"backend": "glfw", "representation": "keysym", "code": code, "name": name,
            "modifiers": [], "persisted": "key.keyboard." + name}


def prepare(e, *, ids=("target", "competing"), initial=(66, "b"), replacement=(67, "c")):
    old = list(e.adapter.state["bindings"].values())
    e.adapter.state["bindings"] = {name: copy.deepcopy(value) | {"key": physical(*initial)}
                                   for name, value in zip(ids, old)}
    e.adapter.state["tested_pool"] = [{"key": physical(*replacement), "evidence_ref": old[0]["owner_evidence"]}]
    e.repairs.configure("c1", "owner", e.epoch, e.put(e.policy))
    from test_storage_controller import start
    start(e.controller, e.config, e.epoch)
    e.controls.plan("a1", "tx", [ids[0]])
    e.budget()


def target_for(e, client):
    plan = e.controls.status("tx")["plan"]
    return NativeControlTarget.model_validate({"schema": "strata/NativeControlTarget/1",
        "profile_id": plan["profile_id"], "control_fingerprint": plan["fingerprint"],
        "policy_digest": plan["policy_digest"], "game_fingerprint": client.connection.fingerprint,
        "settings_fingerprint": client.settings_fingerprint, "body_fingerprint": "b" * 64})


@pytest.fixture
def native_env(repair_env, monkeypatch):
    e = repair_env
    prepare(e)
    lease = e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"]
    worker = WorkerRepairClient(WorkerRepairGrant.model_validate({"schema": "strata/WorkerRepairGrant/1",
        "policy": POLICY, "url": "http://127.0.0.1:12345/v1/repair", "token": "a" * 64,
        "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease}))
    def pause(operation, plan, **kwargs):
        return WorkerRepairReply.model_validate({"schema": "strata/WorkerRepairResponse/1",
            "request_id": "synthetic", "status": "ok", "result": {"schema": "strata/WorkerRepairState/1",
            "policy": POLICY, "plan": plan.model_dump(), "phase": "paused", "reason": None,
            "inputs_released": True, "primitive_events": 2, "gameplay_suspended": True, "resume_authorized": False}})
    monkeypatch.setattr(worker, "call", pause)
    e.request()
    client = NativeSettingsEffectsClient(connection(), "d" * 64)
    target = target_for(e, client)
    snapshot = {"fingerprint": "d" * 64, "revision": 3, "digest": "f" * 64, "options_sha256": "e" * 64,
        "active_transaction": None, "active_phase": None, "supported": False, "operator_development_only": True,
        "bindings": {name: {"translation": name, "runtime_value": "key.keyboard.b", "persisted_value": "key.keyboard.b",
            "persisted_ambiguous": False, "operator_mutable": name == "target"} for name in ("target", "competing")}}
    calls, retained, mode = [], [], ["ok"]
    def call(operation, args, **kwargs):
        calls.append(operation)
        if operation == "settings_snapshot":
            return copy.deepcopy(snapshot)
        if operation == "settings_repair_bind":
            retained.append(NativeRepairAdmission.model_validate(args).model_dump())
            if mode[0] == "lost":
                raise EffectOutcomeUnknown("request", operation, "tx", None)
        else:
            assert kwargs["expected_repair"].model_dump() == retained[0]
        return {"schema": "strata/NativeSettingsRepairState/1", "admission": retained[0],
            "phase": "recovery_required" if mode[0] == "expired" else "bound",
            "reason": "REPAIR_DEADLINE_EXPIRED" if mode[0] == "expired" else None,
            "body_fingerprint": "0" * 64 if mode[0] == "foreign" else "b" * 64,
            "connection_generation": 1, "primitive_events": 4, "resume_authorized": False}
    monkeypatch.setattr(client, "call", call)
    return e, worker, client, target, calls, retained, mode, snapshot


def test_controller_translates_once_and_retains_native_and_worker_authority(native_env):
    e, worker, client, target, calls, _, _, _ = native_env
    receipt = e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert receipt["admission"]["patch"] == {"transaction_id": "tx", "expected_revision": 3,
        "expected_digest": "f" * 64, "changes": {"target": {"before": "key.keyboard.b", "after": "key.keyboard.c"}}}
    assert receipt["admission"]["worker_plan"]["plan_digest"] == digest(e.controls.status("tx")["plan"])
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert calls == ["settings_snapshot", "settings_repair_bind", "settings_repair_status"]
    witness = e.cas.json(e.operator, "operator", receipt["source_ref"])
    assert "bearer_token" not in str(witness) and witness["is_example"] is True
    assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20
    assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
    with pytest.raises(Fault, match="NATIVE_SETTINGS_ADAPTER_REQUIRED"):
        e.repairs.apply("tx", "owner", e.epoch)
    with pytest.raises(Fault, match="REPAIR_WORKER_RESUME_REQUIRED"):
        e.repairs.finish("tx", "owner", e.epoch, e.proof(True))


def test_lost_native_bind_reply_reconciles_only_by_status(native_env):
    e, worker, client, target, calls, _, mode, _ = native_env
    mode[0] = "lost"
    with pytest.raises(EffectOutcomeUnknown):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    mode[0] = "ok"
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert calls == ["settings_snapshot", "settings_repair_bind", "settings_repair_status"]


@pytest.mark.parametrize("mode_value", ["expired", "foreign"])
def test_native_recovery_or_foreign_body_revokes_controller_permission(native_env, mode_value):
    e, worker, client, target, _, _, mode, _ = native_env
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    mode[0] = mode_value
    with pytest.raises(Fault, match="REPAIR_NATIVE_UNAVAILABLE"):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"


@pytest.mark.parametrize("mutation", ["extra-binding", "persisted", "immutable", "wrong-key-code", "target"])
def test_translation_mismatches_cannot_dispatch_native_bind(native_env, mutation):
    e, worker, client, target, calls, _, _, snapshot = native_env
    if mutation == "extra-binding":
        snapshot["bindings"]["foreign"] = snapshot["bindings"]["competing"]
    elif mutation == "persisted":
        snapshot["bindings"]["target"]["persisted_value"] = "key.keyboard.e"
    elif mutation == "immutable":
        snapshot["bindings"]["target"]["operator_mutable"] = False
    elif mutation == "wrong-key-code":
        # Plan remained immutable; changed current adapter state must be rejected.
        e.adapter.state["bindings"]["target"]["key"]["code"] = 69
    else:
        target = target.model_copy(update={"profile_id": "foreign"})
    with pytest.raises(Fault):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert "settings_repair_bind" not in calls
    assert e.database.connection.execute("SELECT count(*) FROM repair_native_handoffs").fetchone()[0] == 0


def test_changed_native_descriptor_cannot_take_over_consumed_intent(native_env):
    e, worker, client, target, calls, _, _, _ = native_env
    e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    from pydantic import SecretStr
    client.connection.bearer_token = SecretStr("f" * 64)
    with pytest.raises(Fault, match="REPAIR_NOT_OWNED"):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert calls == ["settings_snapshot", "settings_repair_bind"]


def test_key_encoding_rejects_false_numeric_and_backend_claims():
    assert native_key(physical(302, "f13")) == "key.keyboard.f13"
    for patch in ({"code": 303}, {"backend": "lwjgl2"}, {"modifiers": ["SHIFT", "ALT"]}, {"code": 99999}):
        with pytest.raises(Fault):
            native_key(physical(302, "f13") | patch)


def test_native_witness_storage_failure_keeps_one_consumed_admission(native_env, monkeypatch):
    e, worker, client, target, calls, _, _, _ = native_env
    put = e.cas.put
    def fail(principal, namespace, owner, raw, **kwargs):
        if json.loads(raw).get("schema") == "strata/NativeRepairWitness/1":
            raise OSError("synthetic native witness storage failure")
        return put(principal, namespace, owner, raw, **kwargs)
    monkeypatch.setattr(e.cas, "put", fail)
    with pytest.raises(OSError, match="native witness"):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    # A received native reply followed by failed evidence publication cannot
    # continue forward under a controller record that failed to confirm it.
    assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"
    assert calls == ["settings_snapshot", "settings_repair_bind"]
    assert e.database.connection.execute("SELECT phase FROM repair_native_handoffs").fetchone()[0] == "UNKNOWN"


def test_native_late_reply_retains_hold_without_success(native_env, monkeypatch):
    e, worker, client, target, _, _, _, _ = native_env
    original = client.call
    def late(operation, args, **kwargs):
        result = original(operation, args, **kwargs)
        if operation == "settings_repair_bind":
            e.now[0] = 151
            e.mono[0] += 51
        return result
    monkeypatch.setattr(client, "call", late)
    with pytest.raises(Fault, match="REPAIR_DEADLINE_EXPIRED|LEASE_EXPIRED"):
        e.repairs.admit_native("tx", "owner", e.epoch, worker, client, target)
    assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"
