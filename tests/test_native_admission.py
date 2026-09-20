"""Synthetic native wire shapes and durable admission; no model/game execution."""

import base64
import copy
import hashlib
import json
import sys
import time
from xml.sax.saxutils import escape

import pytest

from mcbench.broker import NativeBroker, POLICY
from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_admission import NativeAdmission
from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings
from mcbench.records import BudgetLedger
from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest


@pytest.fixture
def admitted(database, cas, tmp_path, example):
    NativeExec(database, cas, simulation=True)
    gate = InferenceDispatches(database, cas, simulation=True)
    gate.budgets.create_account("a1", dict.fromkeys(DIMENSIONS, 100000), "c1", "a1",
                                category="training")
    config = restricted_settings() | {"mcp_servers.strata_broker": {
        "required": True, "enabled_tools": list(BROKER_TOOLS), "tools": {
            "artifact_write": {"approval_mode": "approve"}, "game": {"approval_mode": "approve"}}}}
    plan = NativeLaunch.model_validate({"schema": "strata/NativeLaunch/1", "job_id": "job",
        "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "role": "executor",
        "parent_job_id": None, "depth": 0, "account": "a1", "operation_id": "job-envelope",
        "workspace": str(tmp_path / "workspace"), "profile_directory": str(tmp_path / "profile"),
        "executable": sys.executable, "binary_digest": "a" * 64, "binary_version": CODEX_VERSION,
        "dovetail_commit": DOVETAIL_COMMIT, "model": "gpt-5.6-luna", "config_overrides": config,
        "environment": {}, "prompt": "ordinary goal", "hard_timeout_s": 120,
        "output_limit_bytes": 1048576, "qualification_ref": None, "budget_mode": "per_dispatch",
        "broker_policy": POLICY, "helper_limit": 2})
    def put(value):
        return cas.put(Principal("operator", "operator"), "operator", "operator", canonical(value))
    price = put({"is_example": True, "schema": "synthetic-price"})
    body = example("BudgetLedger")
    def reserve(op, parent, *, calls=1, spend=100, kind="model"):
        return BudgetLedger.model_validate(body | {"is_example": False, "posting": "reserve",
            "operation_id": op, "parent_operation_id": parent, "source_event_id": op + ":reserve",
            "ledger_id": op + ":ledger", "kind": kind, "model_identity": plan.model,
            "pricing_ref": price, "raw_usage_ref": None, "metering": "estimated",
            "usage": dict.fromkeys(body["usage"], 0) | {"input_tokens": 100 * calls,
                "output_tokens": 20 * calls, "model_calls": calls, "spend_microusd": spend,
                "reasoning_tokens": None}})
    envelope = reserve(plan.operation_id, None, calls=10, spend=1000)
    gate.budgets.post("a1", envelope, envelope=True)
    with database.transaction() as db:
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            "job", "c1", "a1", 1, "executor", None, digest(plan.model_dump()),
            plan.model_dump_json(), "RUNNING", time.time(), None, None, None))
        db.execute("INSERT INTO native_events VALUES('job',1,'stdout',?)", (json.dumps({
            "raw_base64": base64.b64encode(canonical({"type": "thread.started", "thread_id": "root"})).decode()}),))
    admission = NativeAdmission(database, cas)
    broker = NativeBroker(database, cas, "job", plan.profile_digest())
    def request(op, thread="root", name="/root", parent=None, *, mutate=None, child=False):
        meta = {"session_id": "root", "thread_id": thread, "turn_id": "turn-" + op,
                "agent_name": name, "parent_thread_id": parent,
                "thread_source": "user" if parent is None else "subagent"}
        if parent:
            meta["subagent_kind"] = "thread_spawn"
        environment = ('<environment_context><cwd>' + escape(plan.workspace) + '</cwd>'
            '<shell>powershell</shell><current_date>2026-09-20</current_date>'
            '<timezone>America/Chicago</timezone><filesystem><workspace_roots><root>' +
            escape(plan.workspace) + '</root></workspace_roots><permission_profile type="managed">'
            '<file_system type="restricted"><entry access="read"><special>:root</special>'
            '</entry></file_system></permission_profile></filesystem></environment_context>')
        body = {"model": plan.model, "client_metadata": {"x-codex-turn-metadata": json.dumps(meta)},
                "input": [{"type": "message", "role": "developer", "content": []},
                          {"type": "message", "role": "user", "content": [
                              {"type": "input_text", "text": environment}]}]}
        if parent:
            parent_name = name.rsplit("/", 1)[0]
            body["input"].append({"type": "agent_message", "author": parent_name, "recipient": name,
                "content": [{"type": "input_text", "text": "Message Type: NEW_TASK\nTask name: " +
                    name + "\nSender: " + parent_name + "\nPayload:\n"},
                    {"type": "encrypted_content", "encrypted_content": "synthetic assigned task"}]})
        if mutate:
            mutate(body)
        raw = canonical(body)
        envelope_id = admission.child_envelope_id("job", thread) if parent else plan.operation_id
        r = reserve(op, envelope_id, kind="helper" if parent else "model")
        fields = {"runtime_job_id": "job", "profile_digest": plan.profile_digest(),
                  "provider": plan.provider, "auth_mode": plan.auth_mode,
                  "request_digest": hashlib.sha256(raw).hexdigest()}
        bound = put({"schema": "strata/InferenceDispatchBound/1", "is_example": True, **fields,
            "reservation_digest": digest(r.model_dump()), "pricing_ref": price, "currency": "USD",
            "finite_dispatch_bound_verified": True, "pricing_semantics_verified": True,
            "expires_unix_ms": time.time_ns() // 1000000 + 60000})
        attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1", **fields,
                                                  "bound_ref": bound})
        parent_envelope = (plan.operation_id if parent == "root" else
                           admission.child_envelope_id("job", parent))
        child_envelope = reserve(envelope_id, parent_envelope, calls=6, spend=600,
                                 kind="helper") if child else None
        return attempt, r, raw, child_envelope
    def prepare(value):
        a, r, raw, child = value
        return admission.prepare("a1", a, r, raw, child_envelope=child)
    return admission, gate, broker, plan, request, prepare, put


def broker_meta(thread="root", parent=None):
    return {"callId": "call", "threadId": thread, "x-codex-turn-metadata": {
        "thread_id": thread, "session_id": "root", "parent_thread_id": parent,
        "codex_version": CODEX_VERSION.removeprefix("codex-cli "), "model": "gpt-5.6-luna",
        "thread_source": "subagent" if parent else "user", "subagent_kind": "thread_spawn"}}


def begin(admitted, value):
    admission, gate, _, _, _, prepare, _ = admitted
    prepare(value)
    assert gate._begin("a1", value[0], value[1])
    return admission.enroll(value[1].operation_id)


def test_native_root_and_clean_helper_enroll_only_after_dispatch(admitted):
    admission, gate, broker, _, request, prepare, _ = admitted
    root = request("one")
    with pytest.raises(Fault, match="NATIVE_REQUEST_NOT_ADMITTED"):
        gate._begin("a1", root[0], root[1])
    prepare(root)
    with pytest.raises(Fault, match="NATIVE_DISPATCH_NOT_ADMITTED"):
        admission.enroll("one")
    begin(admitted, root)
    child = request("two", "child", "/root/child", "root", child=True)
    child_grant = begin(admitted, child)
    assert child_grant.role == "helper" and child_grant.parent_thread_id == "root"
    assert broker.call("artifact_list", {}, broker_meta("child", "root")) == {"files": []}
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000
    assert gate.db.connection.execute("SELECT count(*) FROM operations").fetchone()[0] == 4


@pytest.mark.parametrize("change", [
    lambda b: b["input"].insert(2, {"type": "message", "role": "user", "content": "parent history"}),
    lambda b: b["input"].insert(2, {"type": "message", "role": "assistant", "content": []}),
    lambda b: b.update(previous_response_id="inherited-response"),
    lambda b: b["input"][1]["content"][0].update(text=b["input"][1]["content"][0]["text"].replace(
        "<environment_context>", "<environment_context>hidden parent history")),
    lambda b: b["input"][1]["content"][0].update(text=b["input"][1]["content"][0]["text"].replace(
        "<shell>powershell</shell>", "<shell>parent history</shell>")),
    lambda b: b["input"][1]["content"][0].update(text=b["input"][1]["content"][0]["text"].replace(
        "</filesystem>", "<history>hidden</history></filesystem>")),
    lambda b: b["input"][-1].update(author="/root/sibling"),
    lambda b: b["input"][-1]["content"].append({"type": "input_text", "text": "history"}),
])
def test_inherited_or_smuggled_context_rejected_before_child_reservation(admitted, change):
    _, gate, _, _, request, prepare, _ = admitted
    begin(admitted, request("one"))
    with pytest.raises(Fault, match="HELPER_CONTEXT_INHERITED"):
        prepare(request("two", "child", "/root/child", "root", child=True, mutate=change))
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1
    assert gate.db.connection.execute("SELECT count(*) FROM operations").fetchone()[0] == 2
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 1


@pytest.mark.parametrize("failure", ["no_stdout", "wrong_session", "unknown_parent", "no_budget"])
def test_identity_and_child_budget_required(admitted, failure):
    _, gate, _, _, request, prepare, _ = admitted
    begin(admitted, request("one"))
    value = request("two", "child", "/root/child", "missing" if failure == "unknown_parent" else "root",
                    child=failure != "no_budget")
    if failure == "no_stdout":
        gate.db.connection.execute("DELETE FROM native_events")
    elif failure == "wrong_session":
        def mutate(body):
            meta = json.loads(body["client_metadata"]["x-codex-turn-metadata"])
            meta["session_id"] = "sibling"
            body["client_metadata"]["x-codex-turn-metadata"] = json.dumps(meta)
        value = request("two", "child", "/root/child", "root", child=True, mutate=mutate)
    with pytest.raises(Fault, match="NATIVE_ROOT_EVENT_REQUIRED|NATIVE_LINEAGE|CHILD_BUDGET_REQUIRED"):
        prepare(value)


@pytest.mark.parametrize("cause", ["job_stopped", "participant_revoked", "broker_revoked", "unknown_usage"])
def test_runtime_and_ancestor_revocation_survive_restart_without_releasing_holds(admitted, cause):
    admission, gate, broker, plan, request, prepare, _ = admitted
    begin(admitted, request("one"))
    begin(admitted, request("two", "child", "/root/child", "root", child=True))
    before = gate.budgets.status("a1")["committed_and_reserved"]
    if cause == "job_stopped":
        gate.db.connection.execute("UPDATE native_jobs SET state='STOPPING'")
    elif cause == "participant_revoked":
        admission.revoke("job", "root")
    elif cause == "broker_revoked":
        broker.revoke("root")
    else:
        gate.recover()
    restored = Database(gate.db.path)
    try:
        restored_broker = NativeBroker(restored, CAS(restored, gate.cas.root), "job", plan.profile_digest())
        with pytest.raises(Fault, match="BROKER_RUNTIME_REVOKED|BROKER_FORBIDDEN|BROKER_BUDGET_UNCERTAIN"):
            restored_broker.call("artifact_list", {}, broker_meta("child", "root"))
        next_request = request("next", "child", "/root/child", "root")
        with pytest.raises(Fault):
            prepare(next_request)
            gate._begin("a1", next_request[0], next_request[1])
        assert gate.budgets.status("a1")["committed_and_reserved"] == before
    finally:
        restored.close()


def test_admission_cannot_be_rebound_to_a_different_reservation(admitted):
    _, gate, _, _, request, prepare, _ = admitted
    value = request("one")
    prepare(value)
    changed = copy.deepcopy(value[1])
    changed.usage.spend_microusd -= 1
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        prepare((value[0], changed, value[2], None))


def test_prepared_request_cannot_dispatch_after_job_deadline(admitted):
    admission, gate, _, _, request, prepare, _ = admitted
    value = request("one")
    prepare(value)
    gate.db.connection.execute("UPDATE native_jobs SET started=1")
    with pytest.raises(Fault, match="RUNTIME_EXPIRED"):
        gate._begin("a1", value[0], value[1])
    with pytest.raises(Fault, match="RUNTIME_EXPIRED"):
        admission.enroll("one")
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_grant_reenrollment_does_not_undo_revocation(admitted):
    admission, _, broker, _, request, _, _ = admitted
    begin(admitted, request("one"))
    broker.revoke("root")
    with pytest.raises(Fault, match="BROKER_FORBIDDEN"):
        admission.enroll("one")


def test_child_envelope_exhaustion_rolls_back_participant(admitted):
    _, gate, _, _, request, prepare, _ = admitted
    begin(admitted, request("one"))
    begin(admitted, request("two", "child", "/root/child", "root", child=True))
    with pytest.raises(Fault, match="ENVELOPE_EXHAUSTED"):
        prepare(request("three", "child2", "/root/child2", "root", child=True))
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 2


def test_grandchild_lineage_and_capacity_fail_closed(admitted):
    admission, gate, broker, _, request, prepare, _ = admitted
    begin(admitted, request("one"))
    begin(admitted, request("two", "child", "/root/child", "root", child=True))
    a, r, raw, envelope = request("three", "grandchild", "/root/child/grandchild", "child", child=True)
    envelope = envelope.model_copy(update={"usage": envelope.usage.model_copy(update={
        "model_calls": 4, "input_tokens": 400, "output_tokens": 80, "spend_microusd": 400})})
    grant = begin(admitted, (a, r, raw, envelope))
    assert grant.depth == 2 and grant.parent_thread_id == "child"
    with pytest.raises(Fault, match="HELPER_CAPACITY"):
        prepare(request("four", "sibling", "/root/sibling", "root", child=True))
    with pytest.raises(Fault, match="NATIVE_LINEAGE"):
        prepare(request("deep", "deep", "/root/child/grandchild/deep", "grandchild", child=True))
    admission.revoke("job", "child")
    assert broker.call("artifact_list", {}, broker_meta()) == {"files": []}
    with pytest.raises(Fault, match="BROKER_RUNTIME_REVOKED"):
        broker.call("artifact_list", {}, broker_meta("grandchild", "child"))
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000


@pytest.mark.parametrize("unknown", [False, True])
def test_terminal_seal_closes_child_envelope_only_with_exact_inventory_and_settled_calls(admitted, unknown):
    _, gate, _, plan, request, _, put = admitted
    values = [request("one"), request("two", "child", "/root/child", "root", child=True)]
    for value in values:
        begin(admitted, value)
        reserve = value[1]
        if not unknown or reserve.operation_id == "one":
            receipt = BudgetLedger.model_validate(reserve.model_dump() | {"posting": "settle",
                "source_event_id": reserve.operation_id + ":settle", "ledger_id": reserve.operation_id + ":receipt",
                "metering": "reported", "raw_usage_ref": put({"is_example": True, "usage": 14}),
                "usage": reserve.usage.model_dump() | {"input_tokens": 10, "output_tokens": 4,
                                                       "spend_microusd": 14}})
            gate.settle(reserve.operation_id, "receipt-" + reserve.operation_id, receipt)
    gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED'")
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    proof = {"schema": "strata/InferenceIngressSeal/1", "is_example": True,
        "job_id": "job", "profile_digest": plan.profile_digest(), "process_tree_dead": True,
        "ingress_closed": True, "handlers_fenced": True, "attempt_ids": ["one", "two"]}
    with pytest.raises(Fault, match="DISPATCH_SEAL_UNVERIFIED|METERING_UNKNOWN"):
        runtime.close_dispatch_budget("job", put(proof))
    proof["participant_threads"] = ["child", "root"]
    if unknown:
        gate.recover()
        with pytest.raises(Fault, match="METERING_UNKNOWN"):
            runtime.close_dispatch_budget("job", put(proof))
        assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000
    else:
        assert runtime.close_dispatch_budget("job", put(proof))["state"] == "FINALIZED"
        assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 28
        assert not gate.budgets.status("a1")["uncertain"]
        assert {r[0] for r in gate.db.connection.execute("SELECT state FROM native_participants")} == {"CLOSED"}


def test_fabricated_example_admission_cannot_grant_live_broker_access(database, cas, operator):
    NativeExec(database, cas, simulation=False)
    b = NativeBroker(database, cas, "job", "a" * 64)
    from mcbench.broker import BrokerGrant
    evidence = cas.put(operator, "operator", "operator", canonical({"is_example": True}))
    grant = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1", "runtime_id": "job",
        "session_id": "root", "thread_id": "root", "parent_thread_id": None,
        "profile_digest": "a" * 64, "model": "gpt-5.6-luna", "role": "executor",
        "namespace": "fixture", "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "depth": 0,
        "expires_unix_ms": time.time_ns() // 1000000 + 60000, "tool_calls": 10, "admission_ref": evidence})
    with pytest.raises(Fault, match="BROKER_RUNTIME_ADMISSION_REQUIRED"):
        b.admit(grant)
