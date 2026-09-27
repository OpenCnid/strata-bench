"""Synthetic fault injection after a known worker resume response.

The connected JVM tests cover evidence/adoption. These tests isolate failures
of the controller's evidence store, recovery ledger and emergency stop.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mcbench.native_repair_resume import NativeRepairResume
from mcbench.storage import canonical
from mcbench.worker_restart import WorkerRestartClient
from mcbench.worker_resume import WorkerResumeClient, WorkerResumeState
from test_worker_resume import state
from test_reconfiguration import repair_env as _repair_env

repair_env = _repair_env


@pytest.mark.parametrize("ledger_failure", [False, True])
@pytest.mark.parametrize("stop_failure", [False, True])
def test_known_resume_stops_even_when_evidence_and_recovery_writes_fail(database, example, monkeypatch,
                                                                     ledger_failure, stop_failure):
    repairs = Mock(database=database)
    repairs.controls.status.return_value = {"plan": {"profile_id": "synthetic-profile"}}
    joined = NativeRepairResume(repairs)
    result = WorkerResumeState.model_validate(state(example))
    decision = result.decision
    transaction = decision.worker_plan.transaction_id
    restart, resume = Mock(spec=WorkerRestartClient), Mock(spec=WorkerResumeClient)
    resume.binding_digest = "a" * 64
    with database.transaction() as db:
        db.execute("INSERT INTO repair_worker_resumes VALUES (?,?,?,?,'UNKNOWN',NULL)",
            (transaction, resume.binding_digest, canonical(decision.model_dump()).decode(), result.native.current_instance))
    monkeypatch.setattr(joined.flow, "_context", Mock(return_value=({}, {"phase": "committed"}, None)))
    monkeypatch.setattr(joined, "_evidence", Mock(return_value=(
        SimpleNamespace(verification_ref=decision.verification_ref), result.native.current_instance, 1, None)))
    monkeypatch.setattr(joined.flow, "_put", Mock(side_effect=OSError("synthetic evidence-store failure")))
    resume.call.return_value = SimpleNamespace(result=result)
    stop = Mock()
    if stop_failure:
        stop.call.side_effect = OSError("synthetic stop transport failure")
    monkeypatch.setattr("mcbench.native_repair_resume.NativeGameClient", Mock(return_value=stop))
    real_transaction = database.transaction

    @contextmanager
    def recovery_transaction():
        if ledger_failure:
            raise OSError("synthetic recovery-ledger failure")
        with real_transaction() as db:
            yield db

    monkeypatch.setattr(database, "transaction", recovery_transaction)
    with pytest.raises(OSError):
        joined.resume_committed(transaction, "owner", 1, Mock(), restart, resume, Mock())
    resume.call.assert_called_once_with("status", decision, timeout_ms=1000)
    stop.call.assert_called_once_with("stop_all", {}, timeout_ms=200)
    repairs._fail.assert_called_once_with(transaction, "RESUME_EVIDENCE_UNAVAILABLE")
    assert database.connection.execute("SELECT phase FROM repair_worker_resumes").fetchone()[0] == "UNKNOWN"


@pytest.mark.parametrize("damage", [None, "missing_binding", "changed_binding", "changed_window"])
def test_resume_inference_binding_cannot_be_lost_or_replaced(repair_env, damage):
    e = repair_env
    e.begin()
    e.request()
    joined = NativeRepairResume(e.repairs)
    # No historical proof becomes an implicit empty-call certificate.
    assert joined._inference("tx", "owner", e.epoch, required=False) is None
    with pytest.raises(ValueError, match="REPAIR_INFERENCE_REQUIRED"):
        joined._inference("tx", "owner", e.epoch)
    proof = joined.inference.freeze("tx", "owner", e.epoch)
    ref = e.put(proof)
    with e.database.transaction() as db:
        db.execute("INSERT INTO repair_resume_inference VALUES ('tx',?)", (ref,))
        e.database.event(db, "repair.resume_intent", {"transaction_id": "tx", "inference_ref": ref})
    assert joined._inference("tx", "owner", e.epoch) == ref
    with e.database.transaction() as db:
        assert joined._inference("tx", "owner", e.epoch, db=db) == ref
    if damage is None:
        return
    with e.database.transaction() as db:
        if damage == "missing_binding":
            db.execute("DELETE FROM repair_resume_inference")
        elif damage == "changed_binding":
            db.execute("UPDATE repair_resume_inference SET source_ref=?", ("cas:sha256:" + "0" * 64,))
        else:
            db.execute("UPDATE repair_inference_windows SET closing_cursor=NULL")
    with pytest.raises(ValueError, match="REPAIR_INFERENCE_REQUIRED|REPAIR_INFERENCE_CHANGED"):
        joined._inference("tx", "owner", e.epoch, required=False)
