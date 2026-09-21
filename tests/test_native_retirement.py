"""Synthetic retirement/receipt contracts; actual native lifecycle needs its own run."""

import copy
import json

import pytest

from mcbench.native import NativeExec
from mcbench.native_admission import NativeAdmission
from mcbench.native_retirement import POLICY
from mcbench.records import BudgetLedger
from mcbench.storage import CAS, Database, Fault, Principal, canonical
from test_native_admission import admitted as _admitted, begin, broker_meta

admitted = _admitted
OPERATOR = Principal("operator", "operator")


def settle(admitted, value, response=None, *, sse=False):
    _, gate, _, plan, _, _, _ = admitted
    response = response or {"output": [], "id": "response-" + value[1].operation_id}
    response = {"object": "response", "status": "completed", "model": plan.model,
        "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
            "input_tokens_details": {"cached_tokens": 2}, "output_tokens_details": {"reasoning_tokens": 0}},
        **response}
    raw = canonical(response)
    if sse:
        raw = b'event: response.completed\ndata: ' + canonical({"type": "response.completed",
            "response": response}) + b'\n\n'
    ref = gate.cas.put(OPERATOR, "operator", "operator", raw,
                      media_type="text/event-stream" if sse else "application/json")
    reserve = value[1]
    receipt = BudgetLedger.model_validate(reserve.model_dump() | {"posting": "settle",
        "source_event_id": reserve.operation_id + ":settle", "ledger_id": reserve.operation_id + ":receipt",
        "metering": "reported", "raw_usage_ref": ref, "usage": reserve.usage.model_dump() | {
            "input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 4,
            "reasoning_tokens": 0, "spend_microusd": 14}})
    gate.settle(reserve.operation_id, "receipt-" + reserve.operation_id, receipt)


def scenario(admitted, *, status=None, stale=False, pending=False, descendant=False,
             issue_change=None, observation_change=None, sse=False, reused=False):
    admission, gate, broker, plan, request, _, put = admitted
    plan.helper_limit = 2 if descendant else 1
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    broker.profile_digest = plan.profile_digest()
    def prior_call(body):
        if reused:
            body["input"].append({"type": "function_call_output", "call_id": "status-call",
                                  "output": "old compacted result"})
    root = request("root-call", mutate=prior_call)
    begin(admitted, root)
    settle(admitted, root)
    child = request("child-call", "child", "/root/child", "root", child=True)
    begin(admitted, child)
    if not pending:
        settle(admitted, child)
    if descendant:
        a, r, raw, envelope = request("grand-call", "grand", "/root/child/grand", "child", child=True)
        envelope.usage.model_calls = 2
        envelope.usage.input_tokens = 200
        envelope.usage.output_tokens = 40
        envelope.usage.spend_microusd = 200
        grand = (a, r, raw, envelope)
        begin(admitted, grand)
        settle(admitted, grand)
    if not stale:
        admission.revoke("job", "child")
    issued = request("status-issue")
    begin(admitted, issued)
    call = {"type": "function_call", "namespace": "collaboration", "name": "list_agents",
            "arguments": "{}", "call_id": "status-call"}
    altered = copy.deepcopy(call)
    if issue_change:
        issue_change(altered)
    settle(admitted, issued, {"output": [altered], "id": "response-status"}, sse=sse)
    if stale:
        admission.revoke("job", "child")
    status = {"completed": "owned synthetic result"} if status is None else status
    result = {"type": "function_call_output", "call_id": "status-call", "output": json.dumps({
        "agents": [{"agent_name": "/root", "agent_status": "running"},
                   {"agent_name": "/root/child", "agent_status": status}]})}
    def observation(body):
        body["input"].extend([call, result])
        if observation_change:
            observation_change(body)
    observed = request("status-observed", mutate=observation)
    begin(admitted, observed)
    proof = {"schema": "strata/NativeParticipantRetirement/1", "policy": POLICY,
        "is_example": True, "job_id": "job", "profile_digest": plan.profile_digest(),
        "thread_id": "child", "issuance_operation": "status-issue",
        "observation_operation": "status-observed", "call_id": "status-call"}
    return proof, put(proof), child, observed


@pytest.mark.parametrize("sse", [False, True])
def test_retire_reuses_one_slot_with_fresh_identity_and_closes_full_job_once(admitted, sse):
    admission, gate, broker, plan, request, prepare, put = admitted
    proof, ref, _, observed = scenario(admitted, sse=sse)
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match="HELPER_CAPACITY"):
        prepare(request("replacement", "replacement", "/root/replacement", "root", child=True))
    assert gate.budgets.status("a1")["committed_and_reserved"] == before
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"
    admission.revoke("job", "child")
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        admission.retire("job", "child", put(proof | {"call_id": "other"}))
    with pytest.raises(Fault, match="BROKER_RUNTIME_REVOKED"):
        broker.call("artifact_list", {}, broker_meta("child", "root"))
    with pytest.raises(Fault, match="NATIVE_ADMISSION_SCOPE"):
        prepare(request("resumed", "child", "/root/child", "root"))
    with pytest.raises(Fault, match="NATIVE_PARTICIPANT_NAME_REUSED"):
        prepare(request("same-name", "new-thread", "/root/child", "root", child=True))
    fresh = request("fresh-call", "replacement", "/root/replacement", "root", child=True)
    grant = begin(admitted, fresh)
    old = gate.db.connection.execute("SELECT namespace FROM broker_grants WHERE thread='child'").fetchone()[0]
    assert grant.namespace != old
    assert broker.call("artifact_list", {}, broker_meta("replacement", "root")) == {"files": []}
    settle(admitted, fresh)
    settle(admitted, observed)
    gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED'")
    seal = put({"schema": "strata/InferenceIngressSeal/1", "is_example": True, "job_id": "job",
        "profile_digest": plan.profile_digest(), "process_tree_dead": True, "ingress_closed": True,
        "handlers_fenced": True, "participant_threads": ["child", "replacement", "root"],
        "attempt_ids": ["child-call", "fresh-call", "root-call", "status-issue", "status-observed"]})
    assert NativeExec(gate.db, gate.cas, simulation=True).close_dispatch_budget("job", seal)["state"] == "FINALIZED"
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 70
    assert gate.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='native.participant_retired'").fetchone()[0] == 1
    restored = Database(gate.db.path)
    try:
        service = NativeAdmission(restored, CAS(restored, gate.cas.root))
        assert service.retire("job", "child", ref)["state"] == "CLOSED"
    finally:
        restored.close()


@pytest.mark.parametrize("status", ["running", "idle", "unknown", {"completed": True},
    {"completed": "done", "running": True}, {}, False])
def test_nonterminal_or_coerced_native_status_cannot_release_hold(admitted, status):
    admission, gate, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, status=status)
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match="NATIVE_HELPER_NOT_TERMINAL"):
        admission.retire("job", "child", ref)
    assert gate.budgets.status("a1")["committed_and_reserved"] == before


def test_stale_snapshot_cannot_be_laundered_through_new_root_request(admitted):
    admission, _, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, stale=True)
    with pytest.raises(Fault, match="RETIREMENT_OBSERVATION_SCOPE"):
        admission.retire("job", "child", ref)


@pytest.mark.parametrize("change", [lambda c:c.update(name="interrupt_agent"),
    lambda c:c.update(namespace="functions"), lambda c:c.update(call_id="other"),
    lambda c:c.update(arguments='{"path_prefix":"/root/sibling"}')])
def test_output_needs_exact_captured_post_fence_native_tool_issuance(admitted, change):
    admission, _, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, issue_change=change)
    with pytest.raises(Fault, match="RETIREMENT_TOOL_ISSUANCE"):
        admission.retire("job", "child", ref)


@pytest.mark.parametrize("change", [lambda b:b["input"][-1].update(type="message"),
    lambda b:b["input"].append(copy.deepcopy(b["input"][-1])),
    lambda b:b["input"][-2].update(arguments='{"path_prefix":"/root/child"}'),
    lambda b:b["input"][-1].update(output='{"agents":[]}'),
    lambda b:b["input"][-1].update(output='{"agents":[{"agent_name":"/root/child","agent_status":"interrupted"},{"agent_name":"/root/child","agent_status":"interrupted"}]}')])
def test_fabricated_missing_duplicate_or_changed_tool_result_rejected(admitted, change):
    admission, _, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, observation_change=change)
    with pytest.raises(Fault, match="RETIREMENT_TOOL_RESULT"):
        admission.retire("job", "child", ref)


@pytest.mark.parametrize("case", ["pending", "unknown", "descendant"])
def test_native_terminal_state_never_refunds_unsettled_consumption(admitted, case):
    admission, gate, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, pending=case != "descendant", descendant=case == "descendant")
    if case == "unknown":
        gate.db.connection.execute("UPDATE inference_attempts SET state='UNSETTLED' WHERE operation='child-call'")
        gate.budgets.hold_uncertain("a1", "child-call", "owned missing receipt")
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match="METERING_UNKNOWN|DESCENDANT_UNSETTLED"):
        admission.retire("job", "child", ref)
    assert gate.budgets.status("a1")["committed_and_reserved"] == before
    assert gate.db.connection.execute("SELECT state FROM native_participants WHERE thread='child'").fetchone()[0] == "REVOKED"


@pytest.mark.parametrize("field,value", [("is_example", False), ("job_id", "other"),
    ("profile_digest", "b" * 64), ("thread_id", "sibling"),
    ("observation_operation", "child-call"), ("issuance_operation", "status-observed")])
def test_proof_scope_and_source_order_are_bound(admitted, field, value):
    admission, gate, _, _, _, _, put = admitted
    proof, _, _, _ = scenario(admitted)
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match="RETIREMENT_EVIDENCE_SCOPE|RETIREMENT_OBSERVATION_SCOPE|RETIREMENT_ISSUANCE_UNSETTLED"):
        admission.retire("job", "child", put(proof | {field: value}))
    assert gate.budgets.status("a1")["committed_and_reserved"] == before


def test_root_and_unrevoked_helpers_cannot_retire_and_proof_stays_private(admitted):
    admission, gate, _, _, _, _, _ = admitted
    proof, ref, _, _ = scenario(admitted)
    with pytest.raises(Fault, match="NATIVE_HELPER_REQUIRED"):
        admission.retire("job", "root", ref)
    visible = gate.cas.put(OPERATOR, "operator", "agent", canonical(proof | {"call_id": "visible"}))
    with pytest.raises(Fault, match="RETIREMENT_EVIDENCE_PRIVATE"):
        admission.retire("job", "child", visible)
    gate.db.connection.execute("UPDATE native_participants SET state='ACTIVE' WHERE thread='child'")
    with pytest.raises(Fault, match="RETIREMENT_FENCE_REQUIRED"):
        admission.retire("job", "child", ref)


@pytest.mark.parametrize("legacy", [False, True])
def test_reissued_call_id_cannot_refresh_compacted_old_status(admitted, legacy):
    admission, gate, _, _, _, _, _ = admitted
    _, ref, _, _ = scenario(admitted, reused=True)
    if legacy:
        gate.db.connection.execute("DELETE FROM native_tool_call_ids")
        gate.db.connection.execute("DELETE FROM native_tool_call_indexed_requests")
    before = gate.budgets.status("a1")["committed_and_reserved"]
    with pytest.raises(Fault, match="RETIREMENT_TOOL_CALL_REUSED"):
        admission.retire("job", "child", ref)
    assert gate.budgets.status("a1")["committed_and_reserved"] == before


def test_legacy_index_backfill_accepts_fresh_status_and_preserves_first_seen(admitted):
    from mcbench.native_retirement import index_native_tool_calls
    admission, gate, _, _, request, _, _ = admitted
    _, ref, _, _ = scenario(admitted)
    gate.db.connection.execute("DELETE FROM native_tool_call_ids")
    gate.db.connection.execute("DELETE FROM native_tool_call_indexed_requests")
    assert admission.retire("job", "child", ref)["state"] == "CLOSED"
    db = gate.db.connection
    first = db.execute("SELECT first_ordinal FROM native_tool_call_ids WHERE call_id='status-call'").fetchone()[0]
    later = request("later", mutate=lambda b: b["input"].append({
        "type": "function_call_output", "call_id": "status-call", "output": "unchanged history"}))
    begin(admitted, later)
    row = db.execute("SELECT rowid ordinal,* FROM native_request_admissions WHERE operation='later'").fetchone()
    index_native_tool_calls(db, gate.cas, row)
    assert db.execute("SELECT first_ordinal FROM native_tool_call_ids WHERE call_id='status-call'").fetchone()[0] == first


@pytest.mark.parametrize("state", [None, "UNKNOWN", "REVOKED"])
def test_unknown_or_revoked_helper_still_occupies_slot(admitted, state):
    admission, gate, _, _, request, prepare, _ = admitted
    scenario(admitted)
    gate.db.connection.execute("UPDATE native_participants SET state=? WHERE thread='child'", (state,))
    with pytest.raises(Fault, match="HELPER_CAPACITY"):
        prepare(request("extra", "extra", "/root/extra", "root", child=True))
    admission.revoke("job", "child")
    assert gate.db.connection.execute("SELECT state FROM native_participants WHERE thread='child'").fetchone()[0] == "REVOKED"


@pytest.mark.parametrize("state", ["SETTLED", "DISPATCHING", "UNSETTLED", "missing"])
def test_fixture_wait_only_drains_known_receipt_race(admitted, monkeypatch, state):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("retirement_probe", Path(__file__).parents[1] /
                                                  "tools/native_retirement_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, gate, _, _, _, _, _ = admitted
    scenario(admitted)
    db = gate.db.connection
    db.execute("UPDATE inference_attempts SET state=? WHERE operation='status-issue'", (state,))
    before = gate.budgets.status("a1")["committed_and_reserved"]
    sleeps = []
    def drain(delay):
        sleeps.append(delay)
        db.execute("UPDATE inference_attempts SET state='SETTLED' WHERE operation='status-issue'")
    monkeypatch.setattr(module.time, "sleep", drain)
    if state in {"SETTLED", "DISPATCHING"}:
        module.wait_for_issuance(gate.db, "status-issue")
        assert sleeps == ([0.005] if state == "DISPATCHING" else [])
    else:
        with pytest.raises(Fault, match="RETIREMENT_FIXTURE_ISSUANCE_FAILED"):
            module.wait_for_issuance(gate.db, "absent" if state == "missing" else "status-issue")
        assert not sleeps
    assert gate.budgets.status("a1")["committed_and_reserved"] == before


def test_fixture_wait_is_finite_and_does_not_settle(admitted, monkeypatch):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("retirement_probe", Path(__file__).parents[1] /
                                                  "tools/native_retirement_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, gate, _, _, _, _, _ = admitted
    scenario(admitted)
    gate.db.connection.execute("UPDATE inference_attempts SET state='DISPATCHING' WHERE operation='status-issue'")
    for invalid in (0, -1, 0.501):
        with pytest.raises(Fault, match="RETIREMENT_FIXTURE_WAIT_BOUND"):
            module.wait_for_issuance(gate.db, "status-issue", timeout_s=invalid)
    clock = iter([0, 0.5])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(clock))
    with pytest.raises(Fault, match="RETIREMENT_FIXTURE_ISSUANCE_TIMEOUT"):
        module.wait_for_issuance(gate.db, "status-issue")
    assert gate.db.connection.execute("SELECT state FROM inference_attempts WHERE operation='status-issue'").fetchone()[0] == "DISPATCHING"
