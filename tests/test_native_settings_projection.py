"""Qualification consumption and full native projection; all reports are synthetic."""

import copy
import hashlib
from types import SimpleNamespace

import pytest

from mcbench.controls import Controls
from mcbench.native_control_plan import KEYSYMS, native_key
from mcbench.native_settings_projection import CHECKS, NativeSettingsProjection, decode_native_key
from mcbench.storage import Fault, canonical, digest
from test_native_settings_effects import connection
from mcbench.native_settings_effects import NativeSettingsEffectsClient


def qualified_fixture(snapshot, client, *, profile="fixture-native-projection", clock=lambda: 100.0):
    data = {}
    def put(value):
        raw = value if isinstance(value, bytes) else canonical(value)
        ref = "cas:sha256:" + hashlib.sha256(raw).hexdigest()
        data[ref] = raw
        return ref
    def read(ref, *, max_bytes):
        raw = data[ref]
        assert len(raw) <= max_bytes
        return raw
    identity = {"profile_id": profile, "game_fingerprint": client.connection.fingerprint,
        "settings_fingerprint": client.settings_fingerprint, "body_fingerprint": "b" * 64,
        "input_policy": "native-window-key-mouse-fixed-escape/5", "layout_digest": "e" * 64}
    source = put(b"Synthetic qualification source. No Minecraft or real input qualification.")
    def check(name, subject):
        return put({"schema": "strata/NativeSettingsQualificationCheck/1", "is_example": True,
            "identity_digest": digest(identity), "check": name, "subject_digest": digest(subject),
            "result": "pass", "source_refs": [source]})
    bindings = {name: {"translation": b["translation"], "contexts": ["IN_GAME"],
        "context_confidence": "known", "protected": not b["operator_mutable"], "consumer_tested": True,
        "owner_evidence": check("owner", {"binding_id": name, "translation": b["translation"]})}
        for name, b in snapshot["bindings"].items()}
    pool_key = decode_native_key("key.keyboard.f13")
    proof = {"schema": "strata/NativeSettingsQualification/1", "is_example": True, "identity": identity,
        "expires_unix_ms": int(clock() * 1000) + 100000, "bindings": bindings,
        "tested_pool": [{"key": pool_key, "evidence_ref": check("physical_key", pool_key)}],
        "checks": {name: check(name, bindings if name == "binding_metadata" else identity) for name in CHECKS},
        "consumers": {name: check("consumer", {"binding_id": name, "policy": policy}) for name, policy in bindings.items()}}
    ref = put(proof)
    projection = NativeSettingsProjection(client, ref, read, simulation=True, clock=clock)
    return SimpleNamespace(**locals())


@pytest.fixture
def projected(monkeypatch):
    client = NativeSettingsEffectsClient(connection(), "d" * 64)
    snapshot = {"fingerprint": "d" * 64, "revision": 1, "digest": "f" * 64, "options_sha256": "e" * 64,
        "active_transaction": None, "active_phase": None, "supported": False, "operator_development_only": True,
        "bindings": {name: {"translation": name, "runtime_value": "key.keyboard.g", "persisted_value": "key.keyboard.g",
            "persisted_ambiguous": False, "operator_mutable": name == "target"} for name in ("target", "competing")}}
    e = qualified_fixture(snapshot, client)
    e.calls = []
    def read(operation, args, **kwargs):
        e.calls.append(operation)
        assert operation == "settings_snapshot" and args == {}
        return copy.deepcopy(snapshot)
    monkeypatch.setattr(client, "call", read)
    e.identity_state = {"schema": "strata/NativeGameIdentity/1", "body_fingerprint": "b" * 64, "connection_generation": 1}
    monkeypatch.setattr(e.projection.game, "call", lambda *a, **kw: copy.deepcopy(e.identity_state))
    return e


def test_actual_state_drives_plan_without_synthetic_adapter_state(projected, database):
    e = projected
    controls = Controls(database, e.projection, simulation=True, evidence_reader=e.read)
    plan = controls.plan("avatar", "tx", ["target"])
    assert plan["changes"]["target"]["before"]["code"] == 71
    assert plan["changes"]["target"]["after"]["code"] == 302
    assert {c["binding_id"] for c in plan["binding_checks"]} == {"target", "competing"}
    target = e.projection.target()
    assert target.policy_digest == plan["policy_digest"] and target.fixed_controls == ["escape"]
    assert e.snapshot["supported"] is False  # Native diagnostic claim is never rewritten.
    e.snapshot["revision"] = 2
    e.snapshot["bindings"]["target"].update(runtime_value="key.keyboard.f13", persisted_value="key.keyboard.f13")
    changed = e.projection.snapshot()
    assert changed["revision"] == 2 and changed["bindings"]["target"]["key"]["code"] == 302
    assert Controls._policy(changed) == plan["policy_digest"]
    for method in (e.projection.compare_and_swap, e.projection.verify_and_restart, e.projection.stop_all):
        with pytest.raises(Fault, match="NATIVE_SETTINGS_ADAPTER_REQUIRED"):
            method()
    assert set(e.calls) == {"settings_snapshot"}


@pytest.mark.parametrize("value", ["key.keyboard." + name for name in KEYSYMS.values()] +
    ["key.keyboard.unknown", "key.mouse.left", "key.mouse.right", "key.mouse.middle", "key.mouse.4", "key.mouse.8",
     "scancode.4", "key.keyboard.f13:SHIFT", "key.mouse.left:ALT"])
def test_exact_native_encoding_roundtrips(value):
    assert native_key(decode_native_key(value)) == value


@pytest.mark.parametrize("value", ["key.mouse.1", "key.mouse.9", "key.keyboard.F13", "scancode.04",
    "scancode.-1", "scancode.４", "key.keyboard.g:NONE", "key.keyboard.g:SHIFT:ALT", "key.keyboard.unknown:SHIFT"])
def test_noncanonical_or_unrepresentable_native_encoding_refuses(value):
    with pytest.raises(ValueError):
        decode_native_key(value)


@pytest.mark.parametrize("fault", ["missing_check", "missing_consumer", "changed_policy", "changed_pool", "profile",
    "expired", "example", "failed_check", "foreign_check", "missing_source", "source_tamper", "unknown_field"])
def test_incomplete_or_changed_qualification_refuses_before_native_read(projected, fault):
    e = projected
    proof = copy.deepcopy(e.proof)
    if fault == "missing_check":
        proof["checks"].pop("essential_controls")
    elif fault == "missing_consumer":
        proof["consumers"].pop("target")
    elif fault == "changed_policy":
        proof["bindings"]["target"]["contexts"] = ["GUI"]
    elif fault == "changed_pool":
        proof["tested_pool"][0]["key"] = decode_native_key("key.keyboard.f14")
    elif fault == "profile":
        proof["identity"]["settings_fingerprint"] = "0" * 64
    elif fault == "expired":
        proof["expires_unix_ms"] = 100000
    elif fault == "example":
        proof["is_example"] = False
    elif fault in {"failed_check", "foreign_check", "missing_source"}:
        import json
        item = json.loads(e.data[proof["checks"]["essential_controls"]])
        if fault == "failed_check":
            item["result"] = "fail"
        elif fault == "foreign_check":
            item["identity_digest"] = "0" * 64
        else:
            item["source_refs"] = []
        proof["checks"]["essential_controls"] = e.put(item)
    elif fault == "source_tamper":
        e.data[e.source] = b"Changed bytes"
    else:
        proof["supported"] = True
    e.projection.qualification_ref = e.put(proof)
    with pytest.raises(ValueError):
        e.projection.snapshot()
    assert not e.calls


@pytest.mark.parametrize("fault", ["missing_binding", "extra_binding", "translation", "ambiguous", "different_persisted", "immutable", "body"])
def test_current_native_map_and_body_must_match_qualified_scope(projected, fault):
    e = projected
    if fault == "missing_binding":
        e.snapshot["bindings"].pop("competing")
    elif fault == "extra_binding":
        e.snapshot["bindings"]["extra"] = copy.deepcopy(e.snapshot["bindings"]["competing"])
    elif fault == "body":
        e.identity_state["body_fingerprint"] = "0" * 64
    else:
        field, value = {"translation": ("translation", "other"), "ambiguous": ("persisted_ambiguous", True),
            "different_persisted": ("persisted_value", "key.keyboard.h"), "immutable": ("operator_mutable", False)}[fault]
        e.snapshot["bindings"]["target"][field] = value
    with pytest.raises(ValueError):
        e.projection.snapshot()


def test_simulated_reports_cannot_admit_production(projected):
    projected.projection.simulation = False
    with pytest.raises(Fault, match="SETTINGS_UNQUALIFIED"):
        projected.projection.snapshot()


def test_relabeling_only_the_qualification_cannot_promote_example_sources(projected):
    e = projected
    e.projection.simulation = False
    e.projection.qualification_ref = e.put(e.proof | {"is_example": False})
    with pytest.raises(Fault, match="SETTINGS_UNQUALIFIED"):
        e.projection.snapshot()
    assert not e.calls


def test_disappeared_evidence_is_a_typed_blocker(projected):
    e = projected
    del e.data[e.source]
    with pytest.raises(Fault, match="SETTINGS_EVIDENCE_UNAVAILABLE"):
        e.projection.snapshot()
    assert not e.calls


def test_connection_change_during_snapshot_refuses_mixed_state(projected, monkeypatch):
    e = projected
    original = e.client.call
    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        e.identity_state["connection_generation"] += 1
        return result
    monkeypatch.setattr(e.client, "call", change)
    with pytest.raises(Fault, match="SETTINGS_PROFILE_MISMATCH"):
        e.projection.snapshot()


def test_qualification_expiry_is_rechecked_after_native_reads(projected):
    values = iter([100.0, 200.0])
    projected.projection.clock = lambda: next(values)
    with pytest.raises(Fault, match="SETTINGS_UNQUALIFIED"):
        projected.projection.snapshot()
    assert projected.calls == ["settings_snapshot"]
