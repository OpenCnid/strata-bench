"""Pre-forward denial versus missing admission history; synthetic native store."""

import json

import pytest

from mcbench.native import NativeExec
from mcbench.native_export import NativeExports, OPERATOR
from mcbench.storage import Fault, digest
from test_native_admission import admitted as _admitted
from test_native_retirement import scenario, settle

admitted = _admitted


@pytest.fixture
def denied_stop(admitted):
    admission, gate, _, plan, request, prepare, put = admitted
    def denied_request():
        attempt, reserve, raw, _ = request("budget-denied")
        reserve.usage.spend_microusd = 990  # Exceeds remaining parent envelope, not the account.
        bound = gate.cas.json(OPERATOR, "operator", attempt.bound_ref)
        bound["reservation_digest"] = digest(reserve.model_dump())
        attempt.bound_ref = put(bound)
        prepare((attempt, reserve, raw, None))
        with pytest.raises(Fault, match="ENVELOPE_EXHAUSTED"):
            gate.execute("a1", attempt, reserve, lambda: pytest.fail("denied request forwarded"))
    _, ref, _, observed = scenario(admitted, before_revoke=denied_request)
    settle(admitted, observed)
    admission.retire("job", "child", ref)
    gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED',returncode=0")
    seal = put({"schema": "strata/InferenceIngressSeal/1", "is_example": True, "job_id": "job",
        "profile_digest": plan.profile_digest(), "process_tree_dead": True, "ingress_closed": True,
        "handlers_fenced": True, "participant_threads": ["child", "root"],
        "attempt_ids": ["child-call", "root-call", "status-issue", "status-observed"]})
    return NativeExec(gate.db, gate.cas, simulation=True), seal


def test_proved_denial_exports_separately_without_charging_or_refunding(denied_stop):
    runtime, seal = denied_stop
    runtime.close_dispatch_budget("job", seal)
    before = runtime.budgets.status("a1")
    ref = runtime.export_broker_state("job")
    state = NativeExports(runtime).load(ref)
    source = runtime.cas.json(OPERATOR, "operator", state.source_ref)
    denied = source["pre_dispatch_rejections"]
    assert len(denied) == 1 and denied[0]["admission"]["operation"] == "budget-denied"
    assert denied[0]["rejection"]["reason"] == "ENVELOPE_EXHAUSTED"
    assert len(source["attempts"]) == 4 and all(a["state"] == "SETTLED" for a in source["attempts"])
    assert not any(o["id"] == "budget-denied" for o in source["operations"])
    assert runtime.budgets.status("a1") == before
    assert before["committed_and_reserved"]["spend_microusd"] == 56


@pytest.mark.parametrize("damage", ["absent", "event", "reason", "scope", "operation"])
def test_missing_or_altered_denial_keeps_closure_hold(denied_stop, damage):
    runtime, seal = denied_stop
    db = runtime.db.connection
    before = runtime.budgets.status("a1")
    if damage == "absent":
        db.execute("DELETE FROM inference_rejections")
    elif damage == "event":
        db.execute("DELETE FROM outbox WHERE kind='inference.rejected_before_dispatch'")
    elif damage in {"reason", "scope"}:
        body = json.loads(db.execute("SELECT body FROM inference_rejections").fetchone()[0])
        if damage == "reason":
            body["reason"] = "BUDGET_EXHAUSTED"
        else:
            body["attempt"]["runtime_job_id"] = "foreign"
        db.execute("UPDATE inference_rejections SET body=?", (json.dumps(body),))
    else:
        db.execute("INSERT INTO operations(id,account,parent,kind,reserved) SELECT 'budget-denied',account,parent,kind,reserved "
                   "FROM operations WHERE id='root-call'")
    with pytest.raises(Fault, match="METERING_UNKNOWN|DISPATCH_REJECTION_INVALID"):
        runtime.close_dispatch_budget("job", seal)
    assert runtime.status("job")["state"] == "UNSETTLED"
    assert db.execute("SELECT actual FROM operations WHERE id='job-envelope'").fetchone()[0] is None
    if damage != "operation":
        assert runtime.budgets.status("a1") == before


def test_removing_proof_after_export_does_not_relabel_legacy_absence(denied_stop):
    runtime, seal = denied_stop
    runtime.close_dispatch_budget("job", seal)
    ref = runtime.export_broker_state("job")
    runtime.db.connection.execute("DELETE FROM inference_rejections")
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        NativeExports(runtime).load(ref)
