import copy
import hashlib

import pytest

from mcbench.controls import REQUIRED_CHECKS, Controls as OperatorControls, physical_conflict
from mcbench.storage import Fault, canonical, require

SOURCE = b"Explicitly synthetic control-input witness; no game or physical effects."
REF = "cas:sha256:" + hashlib.sha256(SOURCE).hexdigest()


def Controls(database, adapter):
    return OperatorControls(database, adapter, evidence_reader=adapter.read_evidence, simulation=True)


def key(code):
    return {"backend": "glfw", "representation": "keysym", "code": code, "name": str(code),
            "modifiers": [], "persisted": f"fixture.{code}"}


class SyntheticSettings:
    def __init__(self):
        self.state = {"supported": True, "atomic_cas": True, "restart_tested": True,
            "profile_id": "synthetic-profile-1",
            "fingerprint": "fixture-only", "revision": 1, "backend": "glfw", "tested_pool": [
                {"key": key(67), "evidence_ref": REF}, {"key": key(68), "evidence_ref": REF}],
            "bindings": {name: {"key": key(66), "contexts": ["IN_GAME"], "context_confidence": "known",
                "protected": False, "consumer_tested": True, "owner_evidence": REF}
                for name in ("target", "competing")}}
        self.fail_effect = False
        self.stops = 0
        self.requests = []
        self.evidence = {REF: SOURCE}

    def snapshot(self):
        return copy.deepcopy(self.state)

    def compare_and_swap(self, expected_revision, changes, *, transaction_id, rollback=False):
        self.requests.append((transaction_id, rollback, copy.deepcopy(changes)))
        require(expected_revision == self.state["revision"], "REVISION_CONFLICT")
        for name, key_value in changes.items():
            self.state["bindings"][name]["key"] = key_value
        self.state["revision"] += 1
        return self.snapshot()

    def verify_and_restart(self, changes, *, transaction_id, plan_digest, binding_checks):
        def check(expected):
            status = "fail" if self.fail_effect else "pass"
            proof = {"schema": "strata/ControlCheck/1", "transaction_id": transaction_id,
                "plan_digest": plan_digest, "status": status, "is_example": True,
                "source_refs": [REF]} | expected
            raw = canonical(proof)
            ref = "cas:sha256:" + hashlib.sha256(raw).hexdigest()
            self.evidence[ref] = raw
            return {"status": status, "refs": [ref]}
        return {"transaction_id": transaction_id, "plan_digest": plan_digest,
                "checks": {name: check({"check": name, "binding_id": None, "context": None, "stage": None})
                           for name in REQUIRED_CHECKS},
                "binding_checks": [dict(item) | check(item) for item in binding_checks]}

    def read_evidence(self, ref, *, max_bytes):
        require(len(self.evidence[ref]) <= max_bytes, "ARTIFACT_QUOTA")
        return self.evidence[ref]

    def stop_all(self):
        self.stops += 1


def test_minimal_binding_plan_effect_restart_commit_and_dedup(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    plan = controls.plan("a1", "tx1", ["target"])
    assert plan["changes"] == {"target": {"before": key(66), "after": key(67)}}
    assert controls.apply("tx1")["phase"] == "committed"
    assert controls.apply("tx1")["phase"] == "committed"
    assert adapter.state["revision"] == 2
    assert adapter.state["bindings"]["competing"]["key"] == key(66)
    assert adapter.stops >= 2


@pytest.mark.parametrize("case", ["unsupported", "protected", "unknown", "exhausted", "backend"])
def test_rejected_binding_repairs(database, case):
    adapter = SyntheticSettings()
    if case == "unsupported":
        adapter.state["supported"] = False
    if case == "protected":
        adapter.state["bindings"]["target"]["protected"] = True
    if case == "unknown":
        adapter.state["bindings"]["target"]["consumer_tested"] = False
    if case == "exhausted":
        adapter.state["tested_pool"] = []
    if case == "backend":
        adapter.state["tested_pool"][0]["key"]["backend"] = "lwjgl2"
    with pytest.raises(Fault):
        Controls(database, adapter).plan("a1", "tx1", ["target"])
    assert adapter.state["revision"] == 1


def test_disjoint_contexts_unchanged_and_unknown_context_conservative(database):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["competing"]["contexts"] = ["GUI"]
    controls = Controls(database, adapter)
    assert controls.plan("a1", "disjoint", ["target"])["changes"] == {}
    adapter.state["bindings"]["competing"]["context_confidence"] = "unknown"
    assert controls.plan("a1", "unknown", ["target"])["changes"]


@pytest.mark.parametrize("context", ["UNIVERSAL", "CUSTOM", None])
def test_universal_and_unproven_custom_contexts_conflict(database, context):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["competing"]["contexts"] = [context] if context else []
    assert Controls(database, adapter).plan("a1", "tx", ["target"])["changes"]


def test_modified_chord_cannot_hide_main_key_or_modifier_key_conflict(database):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["target"]["key"]["modifiers"] = ["SHIFT"]
    plan = Controls(database, adapter).plan("a1", "tx", ["target"])
    assert plan["changes"]["target"]["after"] == key(67)
    # Escape is protected at the adapter/pool layer; modifier-only actions like
    # movement/sneak must also remain protected from newly allocated chords.
    assert physical_conflict(key(340), key(67) | {"modifiers": ["SHIFT"]})
    assert physical_conflict(key(344), key(67) | {"modifiers": ["SHIFT"]})
    assert physical_conflict(key(66), key(66) | {"modifiers": ["CONTROL"]})
    assert not physical_conflict(key(66), key(67) | {"modifiers": ["CONTROL"]})
    assert physical_conflict(key(66), key(12) | {"representation": "scancode"})


def test_allocator_skips_chord_that_would_activate_protected_modifier(database):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["sneak"] = copy.deepcopy(adapter.state["bindings"]["target"])
    adapter.state["bindings"]["sneak"].update(key=key(340), protected=True)
    adapter.state["tested_pool"][0]["key"]["modifiers"] = ["SHIFT"]
    plan = Controls(database, adapter).plan("a1", "tx", ["target"])
    assert plan["changes"]["target"]["after"] == key(68)


def test_failure_rolls_back_and_stale_plan_never_overwrites(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx1", ["target"])
    adapter.fail_effect = True
    with pytest.raises(Fault, match="EFFECT_VERIFICATION_FAILED"):
        controls.apply("tx1")
    assert controls.status("tx1")["phase"] == "rolled_back"
    assert adapter.state["bindings"]["target"]["key"] == key(66)
    controls.plan("a1", "tx2", ["target"])
    adapter.state["revision"] += 1
    with pytest.raises(Fault, match="REVISION_CONFLICT"):
        controls.apply("tx2")


def test_crash_recovery_preserves_unrelated_edits_and_conflicts(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    plan = controls.plan("a1", "tx1", ["target"])
    # Crash after persisted intent and applied settings, before effect verification.
    controls._phase("tx1", "applying")
    adapter.compare_and_swap(plan["revision"], {"target": key(67)}, transaction_id="tx1")
    adapter.state["bindings"]["competing"]["key"] = key(70)
    recovered = Controls(database, adapter)
    with pytest.raises(Fault, match="RECOVERY_REQUIRED"):
        recovered.apply("tx1")
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        recovered.rollback("tx1")
    assert adapter.state["bindings"]["competing"]["key"] == key(70)
    assert recovered.status("tx1")["phase"] == "failed"
    with pytest.raises(Fault, match="SETTINGS_BUSY"):
        recovered.plan("a1", "blocked-new", ["target"])
    # A user edit to the patched field is not blindly overwritten on recovery.
    adapter.state["bindings"]["competing"]["key"] = key(66)
    assert recovered.rollback("tx1")["phase"] == "rolled_back"
    plan = controls.plan("a1", "tx2", ["target"])
    controls._phase("tx2", "applying")
    adapter.state["bindings"]["target"]["key"] = key(99)
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        controls.rollback("tx2")
