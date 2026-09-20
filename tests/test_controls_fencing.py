import copy
import hashlib
import json
from functools import partial
import os
import subprocess
import sys
import time

import pytest

from mcbench.control_lock import profile_operation
from mcbench.controls import Controls as OperatorControls
from mcbench.storage import CAS, Database, Fault, Principal, canonical
from test_controls import REF, Controls, SyntheticSettings, key


def test_repeated_plan_returns_original_without_contacting_changed_adapter(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    original = controls.plan("a1", "tx1", ["target"])
    controls.apply("tx1")
    adapter.snapshot = lambda: pytest.fail("an identical plan retry must use durable state")
    assert controls.plan("a1", "tx1", ["target"]) == original
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        controls.plan("a1", "tx1", ["competing"])
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        controls.plan("another-avatar", "tx1", ["target"])


@pytest.mark.parametrize("change", ["owner", "protected", "contexts", "pool", "qualification"])
def test_policy_drift_fences_apply_even_if_revision_and_keys_are_unchanged(database, change):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx1", ["target"])
    if change == "owner":
        adapter.state["bindings"]["target"]["owner_evidence"] = "cas:sha256:" + "b" * 64
    elif change == "protected":
        adapter.state["bindings"]["target"]["protected"] = True
    elif change == "contexts":
        adapter.state["bindings"]["target"]["contexts"] = ["GUI"]
    elif change == "pool":
        adapter.state["tested_pool"] = []
    else:
        adapter.state["atomic_cas"] = False
    with pytest.raises(Fault, match="SETTINGS_POLICY_CHANGED|CAPABILITY_MISSING"):
        controls.apply("tx1")
    assert not adapter.requests and adapter.stops == 0
    assert controls.status("tx1")["phase"] == "planned"


def test_failed_profile_and_avatar_remain_fenced_across_reopen(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "bad", ["target"])
    controls._phase("bad", "applying")
    adapter.state["bindings"]["target"]["key"] = key(99)
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        controls.rollback("bad")
    reopened_db = Database(database.path)
    try:
        reopened = Controls(reopened_db, adapter)
        with pytest.raises(Fault, match="SETTINGS_BUSY"):
            reopened.plan("a2", "same-profile", ["target"])
        adapter.state["profile_id"] = "another-profile"
        with pytest.raises(Fault, match="SETTINGS_BUSY"):
            reopened.plan("a1", "same-avatar", ["target"])
        adapter.state["profile_id"] = "synthetic-profile-1"
        adapter.state["bindings"]["target"]["key"] = key(66)
        assert reopened.rollback("bad")["phase"] == "rolled_back"
        assert reopened.plan("a1", "after-repair", ["target"])["changes"]
    finally:
        reopened_db.close()


def test_unresolved_legacy_transaction_is_preserved_and_blocks_admission(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    with database.transaction() as db:
        db.execute("INSERT INTO control_transactions (id,agent,fingerprint,phase,plan,receipt) "
                   "VALUES ('legacy','a1','old','applying',?,NULL)",
                   (canonical({"agent": "a1", "changes": {}}).decode(),))
    with pytest.raises(Fault, match="SETTINGS_LEGACY_RECOVERY_REQUIRED"):
        controls.plan("a1", "new", ["target"])
    with pytest.raises(Fault, match="SETTINGS_PLAN_UPGRADE_REQUIRED"):
        controls.rollback("legacy")
    assert controls.status("legacy")["phase"] == "applying"
    assert not adapter.requests


@pytest.mark.parametrize("case", ["transaction", "plan", "missing-competitor", "missing-restart",
    "duplicate", "wrong-context", "invalid-ref", "unverified-context"])
def test_incomplete_or_replayed_effect_matrix_rolls_back(database, case):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    plan = controls.plan("a1", "tx1", ["target"])
    assert {item["binding_id"] for item in plan["binding_checks"]} == {"target", "competing"}
    assert {item["stage"] for item in plan["binding_checks"]} == {"before_restart", "after_restart"}
    original = adapter.verify_and_restart

    def verify(*args, **kwargs):
        result = original(*args, **kwargs)
        if case == "transaction":
            result["transaction_id"] = "other-transaction"
        elif case == "plan":
            result["plan_digest"] = "0" * 64
        elif case == "missing-competitor":
            result["binding_checks"] = [item for item in result["binding_checks"] if item["binding_id"] == "target"]
        elif case == "missing-restart":
            result["binding_checks"] = [item for item in result["binding_checks"] if item["stage"] == "before_restart"]
        elif case == "duplicate":
            result["binding_checks"][-1] = copy.deepcopy(result["binding_checks"][0])
        elif case == "wrong-context":
            result["binding_checks"][0]["context"] = "OTHER"
        elif case == "invalid-ref":
            result["checks"]["essential-controls"]["refs"] = ["not-evidence"]
        else:
            result["binding_checks"][0]["status"] = "unverified_context"
        return result

    adapter.verify_and_restart = verify
    with pytest.raises(Fault, match="EFFECT_VERIFICATION_FAILED"):
        controls.apply("tx1")
    assert controls.status("tx1")["phase"] == "rolled_back"
    assert adapter.state["bindings"]["target"]["key"] == key(66)
    assert [item[:2] for item in adapter.requests] == [("tx1", False), ("tx1", True)]


def test_universal_and_gui_contexts_require_chat_and_postrestart_checks(database):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["competing"]["contexts"] = ["UNIVERSAL"]
    adapter.state["bindings"]["target"]["contexts"] = ["GUI"]
    plan = Controls(database, adapter).plan("a1", "tx", ["target"])
    target = [item for item in plan["binding_checks"] if item["binding_id"] == "target"]
    competing = [item for item in plan["binding_checks"] if item["binding_id"] == "competing"]
    assert {item["context"] for item in target} == {"GUI", "CHAT"}
    assert {item["context"] for item in competing} == {"IN_GAME", "GUI", "CHAT"}


def test_release_failure_never_commits_and_keeps_recovery_hold(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx", ["target"])

    def broken_release():
        raise Fault("NATIVE_RELEASE_FAILED")

    adapter.stop_all = broken_release
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        controls.apply("tx")
    assert controls.status("tx")["phase"] == "failed"
    assert not adapter.requests
    with pytest.raises(Fault, match="SETTINGS_BUSY"):
        controls.plan("a1", "next", ["target"])


def test_final_release_failure_restores_values_instead_of_committing(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx", ["target"])

    def stop():
        adapter.stops += 1
        if adapter.stops == 2:
            raise Fault("NATIVE_RELEASE_FAILED")

    adapter.stop_all = stop
    with pytest.raises(Fault, match="NATIVE_RELEASE_FAILED"):
        controls.apply("tx")
    assert controls.status("tx")["phase"] == "rolled_back"
    assert adapter.state["bindings"]["target"]["key"] == key(66)


def test_noop_plan_does_not_write_or_restart(database):
    adapter = SyntheticSettings()
    adapter.state["bindings"]["competing"]["contexts"] = ["GUI"]
    controls = Controls(database, adapter)
    assert not controls.plan("a1", "tx", ["target"])["changes"]
    with pytest.raises(Fault, match="NO_CHANGE_REQUIRED"):
        controls.apply("tx")
    assert not adapter.requests and adapter.stops == 0


def test_committed_rollback_does_not_overwrite_a_newer_revision(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx", ["target"])
    committed_revision = controls.apply("tx")["receipt"]["revision"]
    adapter.state["revision"] += 1
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        controls.rollback("tx")
    reopened_db = Database(database.path)
    try:
        recovered = Controls(reopened_db, adapter)
        # A failed recovery must not turn a stale committed transaction into an
        # unfenced pending transaction, including when the keys happen to match.
        for _ in range(2):
            with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
                recovered.rollback("tx")
            assert recovered.status("tx")["receipt"]["committed_revision"] == committed_revision
    finally:
        reopened_db.close()
    assert [(transaction_id, rollback) for transaction_id, rollback, _ in adapter.requests] == [("tx", False)]
    assert adapter.state["bindings"]["target"]["key"] == key(67)


def test_committed_rollback_can_retry_release_failure_without_revision_drift(database):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx", ["target"])
    committed_revision = controls.apply("tx")["receipt"]["revision"]
    release = adapter.stop_all

    def unavailable_release():
        raise Fault("NATIVE_RELEASE_FAILED")

    adapter.stop_all = unavailable_release
    with pytest.raises(Fault, match="ROLLBACK_REQUIRES_OPERATOR"):
        controls.rollback("tx")
    assert controls.status("tx")["receipt"]["committed_revision"] == committed_revision
    adapter.stop_all = release
    assert controls.rollback("tx")["phase"] == "rolled_back"
    assert adapter.state["bindings"]["target"]["key"] == key(66)


@pytest.mark.parametrize("case", ["missing-reader", "example-proof"])
def test_production_workflow_cannot_commit_synthetic_or_unavailable_evidence(database, case):
    adapter = SyntheticSettings()
    controls = OperatorControls(database, adapter,
        evidence_reader=adapter.read_evidence if case == "example-proof" else None)
    controls.plan("a1", "tx", ["target"])
    with pytest.raises(Fault, match="EVIDENCE_STORE_REQUIRED|EFFECT_EVIDENCE_INVALID"):
        controls.apply("tx")
    assert controls.status("tx")["phase"] == "rolled_back"
    assert adapter.state["bindings"]["target"]["key"] == key(66)


def test_simulation_database_cannot_be_reopened_as_production_controls(database):
    adapter = SyntheticSettings()
    Controls(database, adapter)
    with pytest.raises(Fault, match="PROFILE_MISMATCH"):
        OperatorControls(database, adapter, evidence_reader=adapter.read_evidence)


@pytest.mark.parametrize("case", ["hash", "transaction", "context", "missing-source", "duplicate-field",
                                "missing-source-bytes", "source-hash"])
def test_evidence_bytes_are_hashed_and_bound_to_each_check(database, case):
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    controls.plan("a1", "tx", ["target"])
    original = adapter.verify_and_restart

    def verify(*args, **kwargs):
        result = original(*args, **kwargs)
        check = result["binding_checks"][0]
        old_ref = check["refs"][0]
        if case == "missing-source-bytes":
            del adapter.evidence[REF]
            return result
        if case == "source-hash":
            adapter.evidence[REF] = b"incorrect source content"
            return result
        if case == "hash":
            adapter.evidence[old_ref] += b" "
            return result
        proof = json.loads(adapter.evidence[old_ref])
        if case == "transaction":
            proof["transaction_id"] = "unrelated-transaction"
        elif case == "context":
            proof["context"] = "unverified-context"
        elif case == "missing-source":
            proof["source_refs"] = []
        raw = canonical(proof)
        if case == "duplicate-field":
            raw = b'{"status":"fail",' + raw[1:]
        ref = "cas:sha256:" + hashlib.sha256(raw).hexdigest()
        adapter.evidence[ref] = raw
        check["refs"] = [ref]
        return result

    adapter.verify_and_restart = verify
    with pytest.raises(Fault, match="EFFECT_EVIDENCE_INVALID"):
        controls.apply("tx")
    assert controls.status("tx")["phase"] == "rolled_back"


def test_old_table_is_migrated_without_inventing_legacy_profile_authority(database):
    with database.transaction() as db:
        db.execute("CREATE TABLE control_transactions (id TEXT PRIMARY KEY, agent TEXT, "
                   "fingerprint TEXT, phase TEXT, plan TEXT, receipt TEXT)")
        db.execute("INSERT INTO control_transactions VALUES ('legacy','a1','old','verifying','{}',NULL)")
    controls = Controls(database, SyntheticSettings())
    assert controls.status("legacy")["profile_id"] is None
    with pytest.raises(Fault, match="SETTINGS_LEGACY_RECOVERY_REQUIRED"):
        controls.plan("a1", "new", ["target"])


def test_verification_budget_is_reserved_before_reading_large_evidence(database, monkeypatch):
    monkeypatch.setattr("mcbench.controls.VERIFICATION_BYTE_LIMIT", 128)
    adapter = SyntheticSettings()
    controls = Controls(database, adapter)
    assert controls.plan("a1", "tx", ["target"])["verification_byte_limit"] == 128
    with pytest.raises(Fault, match="EFFECT_EVIDENCE_INVALID"):
        controls.apply("tx")
    assert controls.status("tx")["phase"] == "rolled_back"


def test_scoped_cas_reader_checks_size_before_reading_evidence(database, tmp_path, monkeypatch):
    cas = CAS(database, tmp_path / "objects")
    operator = Principal("operator", "operator")
    ref = cas.put(operator, "controls", "operator", b"a" * 200)
    original = type(tmp_path).open

    def forbidden_read(path, *args, **kwargs):
        if path == cas._path(ref):
            pytest.fail("over-quota evidence must not be read")
        return original(path, *args, **kwargs)

    with monkeypatch.context() as patching:
        patching.setattr(type(tmp_path), "open", forbidden_read)
        with pytest.raises(Fault, match="ARTIFACT_QUOTA"):
            cas.read(operator, "controls", ref, max_bytes=128)
    assert cas.read(operator, "controls", ref, max_bytes=200) == b"a" * 200
    with pytest.raises(Fault, match="FORBIDDEN"):
        cas.read(Principal("other", "executor"), "controls", ref, max_bytes=0)


def test_simulated_workflow_reads_all_proofs_and_sources_through_private_cas(database, tmp_path):
    adapter = SyntheticSettings()
    cas = CAS(database, tmp_path / "control-evidence")
    operator = Principal("operator", "operator")
    original = adapter.verify_and_restart

    def verify(*args, **kwargs):
        result = original(*args, **kwargs)
        for ref, content in adapter.evidence.items():
            assert cas.put(operator, "control-verification", "operator", content) == ref
        return result

    adapter.verify_and_restart = verify
    controls = OperatorControls(database, adapter, simulation=True,
        evidence_reader=partial(cas.read, operator, "control-verification"))
    controls.plan("a1", "cas-verified-simulation", ["target"])
    transaction = controls.apply("cas-verified-simulation")
    assert transaction["phase"] == "committed"
    assert transaction["plan"]["simulation"] is True
    for item in transaction["receipt"]["verification"]["binding_checks"]:
        for ref in item["refs"]:
            proof = json.loads(cas.read(operator, "control-verification", ref))
            assert proof["is_example"] is True
            assert all(cas.verify(operator, "control-verification", source) > 0
                       for source in proof["source_refs"])


@pytest.mark.parametrize("crash", [False, True])
def test_actual_process_operation_lock_excludes_other_controller_and_releases(database, tmp_path, crash):
    ready = tmp_path / "lock-ready"
    code = """
import sys
from pathlib import Path
from mcbench.storage import Database
from mcbench.control_lock import profile_operation
database = Database(Path(sys.argv[1]))
with profile_operation(database, 'synthetic-profile-1'):
    Path(sys.argv[2]).write_text('ready')
    sys.stdin.readline()
database.close()
"""
    process = subprocess.Popen([sys.executable, "-c", code, str(database.path), str(ready)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        expires = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < expires and process.poll() is None:
            time.sleep(0.02)
        assert ready.exists() and process.poll() is None
        with pytest.raises(Fault, match="SETTINGS_BUSY"), profile_operation(database, "synthetic-profile-1"):
            pytest.fail("second controller acquired an active profile operation")
        with profile_operation(database, "independent-profile"):
            pass
        if crash:
            process.kill()
        else:
            process.stdin.write(b"stop\n")
            process.stdin.flush()
        process.wait(timeout=5)
        with profile_operation(database, "synthetic-profile-1"):
            pass
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
