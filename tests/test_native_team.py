"""Synthetic native admission/broker integration; no actual CLI or game run."""

import copy
import json
import time
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mcbench.broker import NativeBroker
from mcbench.broker_stdio import respond
from mcbench.controller import Controller
from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_broker_policy import (
    POLICY, TEAM_POLICY, TEAM_SETTINGS_POLICY, broker_approvals, broker_tools,
    validate_broker_settings,
)
from mcbench.native_team import inspect_team_calls, require_team_plan
from mcbench.native_tool_projection import pin_tool_projection, read_tool_projection, require_tool_projection
from mcbench.storage import Fault, Principal, canonical, digest
from test_native_admission import admitted as _admitted, begin, broker_meta
from test_native_tool_projection import wire_tools
from test_storage_controller import setup_campaign, start
from test_team_protocol import POLICY as COMMUNICATION_POLICY

admitted = _admitted


@pytest.fixture
def native_team(admitted, configs):
    admission, gate, _, plan, request, prepare, put = admitted
    original = plan.model_dump()
    ref = put(COMMUNICATION_POLICY)
    controller = Controller(gate.db, simulation=True)

    def configured(n, campaign, admission):
        c, agents = configs(n, campaign, admission)
        return c.model_copy(update={"communication_policy": ref}), agents

    config, epoch = setup_campaign(controller, configured)
    start(controller, config, epoch)
    plan.broker_policy, plan.team_policy_ref = TEAM_POLICY, ref
    server = plan.config_overrides["mcp_servers.strata_broker"]
    server["enabled_tools"], server["tools"] = list(broker_tools(TEAM_POLICY)), broker_approvals(TEAM_POLICY)
    plan = NativeLaunch.model_validate(plan.model_dump())
    # The fixture request closure holds the original object, whose explicit
    # mutations above match this separately validated durable copy.
    gate.db.connection.execute("UPDATE native_jobs SET plan=?,plan_digest=? WHERE id='job'",
                               (plan.model_dump_json(), digest(plan.model_dump())))
    broker = NativeBroker(gate.db, gate.cas, "job", plan.profile_digest())
    context = (admission, gate, broker, plan, request, prepare, put)
    begin(context, request("one"))
    return context, controller, original


def team_request(**updates):
    return {"schema": "strata/TeamRequest/1", "request_id": "send-one", "campaign_id": "c1",
        "agent_id": "a1", "epoch": 1,
        "deadline_at": datetime.fromtimestamp(time.time() + 3, timezone.utc).isoformat().replace("+00:00", "Z"),
        "operation": {"kind": "send", "message_id": "m1", "recipients": ["a2"], "body": "hello", "ttl_s": 600},
        **updates}


def call(broker, request=None, meta=None):
    return broker.call("team", {"request": request or team_request()}, meta or broker_meta())


def stopped_calls(db):
    return [dict(r) for r in db.execute("SELECT o.cursor,o.body,l.state,l.result_digest FROM outbox o "
        "JOIN broker_call_lifecycle l ON l.event=o.cursor WHERE o.kind='broker.call'")]


def test_catalog_extension_requires_explicit_identity_and_preserves_old_plan(native_team):
    context, _, original = native_team
    _, gate, broker, plan, _, _, _ = context
    old = NativeLaunch.model_validate(original)
    assert "team_policy_ref" not in old.model_dump()
    assert old.profile_digest() != plan.profile_digest()
    assert "team" not in broker_tools(POLICY) and "team" in broker_tools(TEAM_POLICY)
    catalog = respond(broker, {"jsonrpc": "2.0", "method": "tools/list"})
    assert [v["name"] for v in catalog["tools"]] == list(broker_tools(TEAM_POLICY))
    assert catalog["tools"][-1]["annotations"]["readOnlyHint"] is False
    for body in (original | {"team_policy_ref": plan.team_policy_ref}, plan.model_dump() | {"team_policy_ref": None}):
        with pytest.raises(ValidationError):
            NativeLaunch.model_validate(body)
    validate_broker_settings(plan.config_overrides, policy=TEAM_POLICY)
    with pytest.raises(Fault, match="BROKER_SERVER_POLICY"):
        validate_broker_settings(plan.config_overrides)
    with pytest.raises(Fault, match="BROKER_SCOPE"):
        NativeBroker(gate.db, gate.cas, "job", old.profile_digest())


def test_authenticated_send_dedup_and_private_audit_join(native_team):
    context, _, _ = native_team
    _, gate, broker, _, _, _, _ = context
    first = call(broker)
    assert call(broker) == first
    db = gate.db.connection
    assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 1
    events = [json.loads(r[0]) for r in db.execute("SELECT body FROM outbox WHERE kind='team.request'")]
    assert len(events) == 2
    for event in events:
        source = db.execute("SELECT body FROM outbox WHERE cursor=?", (event["native_call_event"],)).fetchone()
        assert json.loads(source[0])["team_arguments"]["request"] == event["request"]
        assert event["result_digest"] == digest(first)
    messages = broker.team.request(Principal("campaign:c1:agent:a2", "executor"), team_request(
        agent_id="a2", request_id="receive-one", operation={"kind": "receive", "after": 0,
        "limit": 100, "acknowledge": []}), gate.cas)
    assert [m["body"] for m in messages["result"]["messages"]] == ["hello"]
    assert len(inspect_team_calls(db, context[3], stopped_calls(db))) == 2


def test_native_receive_and_ack_private_reconstruction(native_team):
    context, _, _ = native_team
    _, gate, broker, plan, _, _, _ = context
    broker.team.request(Principal("campaign:c1:agent:a2", "executor"), team_request(agent_id="a2",
        operation={"kind": "send", "message_id": "m2", "body": "answer", "recipients": ["a1"], "ttl_s": 600}), gate.cas)
    receive = {"kind": "receive", "after": 0, "limit": 10, "acknowledge": []}
    reply = call(broker, team_request(request_id="receive", operation=receive))
    assert reply["result"]["messages"][0]["body"] == "answer"
    call(broker, team_request(request_id="ack", operation=receive | {"acknowledge": ["m2"]}))
    assert len(inspect_team_calls(gate.db.connection, plan, stopped_calls(gate.db.connection))) == 2


@pytest.mark.parametrize("change", ["missing", "duplicate", "policy", "request", "result", "journal",
                                  "message", "recipient", "expiry", "grant", "arguments"])
def test_stopped_team_reconstruction_rejects_changed_evidence(native_team, change):
    context, _, _ = native_team
    _, gate, broker, plan, _, _, _ = context
    call(broker)
    db = gate.db.connection
    row = db.execute("SELECT cursor,body FROM outbox WHERE kind='team.request'").fetchone()
    body = json.loads(row["body"])
    if change == "missing":
        db.execute("DELETE FROM outbox WHERE cursor=?", (row["cursor"],))
    elif change == "duplicate":
        db.execute("INSERT INTO outbox(kind,body) VALUES('team.request',?)", (row["body"],))
    elif change in {"policy", "request", "result"}:
        if change == "policy":
            body["policy_ref"] = "cas:sha256:" + "d" * 64
        elif change == "request":
            body["request"]["agent_id"] = "a2"
        else:
            body["result"]["result"]["sender_seq"] = 99
            body["result_digest"] = digest(body["result"])
            db.execute("UPDATE broker_call_lifecycle SET result_digest=?", (body["result_digest"],))
        db.execute("UPDATE outbox SET body=? WHERE cursor=?", (canonical(body).decode(), row["cursor"]))
    elif change == "grant":
        row = db.execute("SELECT body FROM broker_grants WHERE thread='root'").fetchone()
        grant = json.loads(row[0]) | {"role": "helper"}
        db.execute("UPDATE broker_grants SET body=?", (canonical(grant).decode(),))
    elif change == "arguments":
        row = db.execute("SELECT cursor,body FROM outbox WHERE kind='broker.call'").fetchone()
        value = json.loads(row["body"])
        value.pop("team_arguments")
        db.execute("UPDATE outbox SET body=? WHERE cursor=?", (canonical(value).decode(), row["cursor"]))
    else:
        db.execute({"journal": "DELETE FROM team_requests", "message": "UPDATE messages SET body='changed'",
            "recipient": "DELETE FROM deliveries", "expiry": "UPDATE messages SET expires=expires+1"}[change])
    with pytest.raises(Fault, match="TEAM_"):
        inspect_team_calls(db, plan, stopped_calls(db))


@pytest.mark.parametrize("updates", [
    {"campaign_id": "foreign"}, {"agent_id": "a2"}, {"epoch": 2},
    {"operation": {"kind": "send", "message_id": "m1", "body": "foreign", "recipients": ["outsider"], "ttl_s": 600}},
])
def test_scope_and_foreign_recipient_refuse_before_effects(native_team, updates):
    context, _, _ = native_team
    _, gate, broker, _, _, _, _ = context
    with pytest.raises(Fault, match="BROKER_SCOPE|FORBIDDEN"):
        call(broker, team_request(**updates))
    assert gate.db.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


def test_native_helper_has_artifacts_but_no_campaign_team_authority(native_team):
    context, _, _ = native_team
    _, gate, broker, _, request, _, _ = context
    begin(context, request("helper-one", "child", "/root/child", "root", child=True))
    meta = broker_meta("child", "root")
    assert broker.call("artifact_list", {}, meta) == {"files": []}
    with pytest.raises(Fault, match="BROKER_TEAM_FORBIDDEN"):
        call(broker, meta=meta)
    assert gate.db.connection.execute("SELECT count(*) FROM team_requests").fetchone()[0] == 0


@pytest.mark.parametrize("change,fault", [
    ("policy", "TEAM_POLICY_CHANGED"), ("lease", "LEASE_EXPIRED"),
    ("epoch", "TEAM_CAMPAIGN_SCOPE"), ("state", "CAMPAIGN_NOT_RUNNING"),
    ("simulation", "TEAM_POLICY_SCOPE"), ("private", "TEAM_POLICY_PRIVATE"),
    ("job", "BROKER_RUNTIME_REVOKED"), ("grant", "BROKER_FORBIDDEN"),
])
def test_live_authority_changes_fence_existing_native_grant(native_team, change, fault):
    context, _, _ = native_team
    _, gate, broker, plan, _, _, _ = context
    db = gate.db.connection
    if change == "policy":
        config = json.loads(db.execute("SELECT config FROM campaigns WHERE id='c1'").fetchone()[0])
        config["communication_policy"] = "cas:sha256:" + "e" * 64
        db.execute("UPDATE campaigns SET config=?", (canonical(config).decode(),))
    elif change == "private":
        db.execute("UPDATE objects SET visibility='agent' WHERE ref=?", (plan.team_policy_ref,))
    else:
        db.execute({"lease": "UPDATE campaigns SET lease_until=0", "epoch": "UPDATE campaigns SET epoch=2",
            "state": "UPDATE campaigns SET state='STOPPING'", "simulation": "UPDATE controller_profile SET simulation=0",
            "job": "UPDATE native_jobs SET state='STOPPING'", "grant": "UPDATE broker_grants SET revoked=1"}[change])
    with pytest.raises(Fault, match=fault):
        call(broker)
    assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


@pytest.mark.parametrize("stage", ["before_effect", "before_commit"])
def test_revocation_between_auth_and_team_commit_rolls_back(native_team, monkeypatch, stage):
    context, _, _ = native_team
    _, gate, broker, _, _, _, _ = context
    original = broker._grant
    calls = []

    def guard(db, thread):
        calls.append(thread)
        if len(calls) == (2 if stage == "before_effect" else 3):
            # Simulates an expiry/revocation failure from the exact production
            # authority guard, after initial authentication succeeded.
            raise Fault("BROKER_EXPIRED")
        return original(db, thread)

    monkeypatch.setattr(broker, "_grant", guard)
    with pytest.raises(Fault, match="BROKER_EXPIRED"):
        call(broker)
    db = gate.db.connection
    for table in ("messages", "deliveries", "team_requests"):
        assert db.execute("SELECT count(*) FROM " + table).fetchone()[0] == 0
    assert db.execute("SELECT count(*) FROM outbox WHERE kind='team.request'").fetchone()[0] == 0


def test_team_projection4_cannot_relabel_older_projection(native_team):
    context, _, _ = native_team
    _, gate, _, plan, _, _, _ = context
    plan = plan.model_copy(update={"purpose": "conformance", "model": "gpt-6-luna"})
    block = wire_tools("executor")
    reviewed = {role: [{k: v for k, v in block.items() if k != "id"}] for role in ("executor", "helper")}
    plan.tool_projection_ref = pin_tool_projection(gate.cas, plan, reviewed, conformance_helpers=True)
    pin = gate.cas.json(Principal("operator", "operator"), "operator", plan.tool_projection_ref)
    assert pin["schema"] == "strata/NativeToolProjection/4" and pin["settings_policy"] == TEAM_SETTINGS_POLICY
    assert require_tool_projection(gate.cas, plan, {"input": [block]}, "helper") == digest(reviewed["helper"])
    for changes in ({"broker_policy": POLICY}, {"team_policy_ref": None}, {"purpose": "campaign"}):
        changed = plan.model_copy(update=changes)
        with pytest.raises(Fault, match="BROKER_SERVER_POLICY|NATIVE_TOOL_PROJECTION_SCOPE"):
            read_tool_projection(gate.cas, changed)
    legacy = copy.deepcopy(pin) | {"schema": "strata/NativeToolProjection/3", "policy": "native-additional-tools-exact/3",
                                 "settings_policy": "native-broker-closed-features-stdio/2"}
    legacy_ref = gate.cas.put(Principal("operator", "operator"), "operator", "operator", canonical(legacy))
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        read_tool_projection(gate.cas, plan.model_copy(update={"tool_projection_ref": legacy_ref}))


@pytest.mark.parametrize("helpers", [1, 2])
def test_campaign_team_projection_has_distinct_pin_and_preserves_qualification_gate(native_team, helpers):
    from mcbench.native import REQUIRED_PROOFS, CONFORMANCE_PREREQUISITES

    context, _, _ = native_team
    _, gate, _, plan, _, _, put = context
    plan = plan.model_copy(update={"purpose": "campaign", "model": "gpt-6-luna",
                                   "helper_limit": helpers, "accounting_basis_digest": "a" * 64})
    block = wire_tools("executor")
    reviewed = {role: [{k: v for k, v in block.items() if k != "id"}] for role in ("executor", "helper")}
    conformance = plan.model_copy(update={"purpose": "conformance"})
    old_ref = pin_tool_projection(gate.cas, conformance, reviewed, conformance_helpers=True)
    plan.tool_projection_ref = pin_tool_projection(gate.cas, plan, reviewed, campaign_team=True)
    assert old_ref != plan.tool_projection_ref
    pin = gate.cas.json(Principal("operator", "operator"), "operator", plan.tool_projection_ref)
    assert pin["schema"] == "strata/NativeToolProjection/5" and pin["settings_policy"] == TEAM_SETTINGS_POLICY
    for role in ("executor", "helper"):
        assert require_tool_projection(gate.cas, plan, {"input": [block]}, role) == digest(reviewed[role])
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        read_tool_projection(gate.cas, plan.model_copy(update={"tool_projection_ref": old_ref}))
    changed = copy.deepcopy(block)
    changed["tools"][0]["tools"][0]["description"] += " changed"
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_MISMATCH"):
        require_tool_projection(gate.cas, plan, {"input": [changed]}, "helper")

    # Synthetic parser evidence, never an actual qualification or native launch.
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    with pytest.raises(Fault, match="RUNTIME_UNQUALIFIED"):
        runtime._proof(plan)
    refs = {check: put({"result": "pass", "is_example": False, "check": check,
        "profile_digest": plan.profile_digest(), "workspace": plan.workspace,
        "profile_directory": plan.profile_directory, "role": plan.role,
        "environment_digest": digest(plan.environment), "currency": "USD",
        "auth_mode": plan.auth_mode, "pricing_semantics_verified": True,
        "finite_dispatch_bound_verified": True, "accounting_basis_digest": plan.accounting_basis_digest})
        for check in REQUIRED_PROOFS}
    proof = {"schema": "strata/RuntimeQualification/1", "is_example": False, "purpose": "campaign",
             "profile_digest": plan.profile_digest(), "expires_unix": time.time() + 60, "checks": refs}
    for checks in [CONFORMANCE_PREREQUISITES, *(REQUIRED_PROOFS - {v} for v in REQUIRED_PROOFS)]:
        ref = put(proof | {"checks": {k: refs[k] for k in checks}})
        with pytest.raises(Fault, match="RUNTIME_UNQUALIFIED"):
            runtime._proof(plan.model_copy(update={"qualification_ref": ref}))
    runtime._proof(plan.model_copy(update={"qualification_ref": put(proof)}))
    assert runtime.live == {}


@pytest.mark.parametrize("updates", [
    {"purpose": "conformance"}, {"purpose": "development_piloting"}, {"model": "gpt-5.6-luna"},
    {"helper_limit": 0}, {"helper_limit": 3}, {"helper_limit": True},
    {"team_policy_ref": None}, {"broker_policy": POLICY},
])
def test_campaign_team_projection_refuses_scope_changes_before_pin(native_team, updates):
    context, _, _ = native_team
    _, gate, _, plan, _, _, _ = context
    plan = plan.model_copy(update={"purpose": "campaign", "model": "gpt-6-luna"})
    block = wire_tools("executor")
    reviewed = {role: [{k: v for k, v in block.items() if k != "id"}] for role in ("executor", "helper")}
    plan.tool_projection_ref = pin_tool_projection(gate.cas, plan, reviewed, campaign_team=True)
    changed = plan.model_copy(update=updates)
    for operation in (lambda: read_tool_projection(gate.cas, changed),
                      lambda: pin_tool_projection(gate.cas, changed, reviewed, campaign_team=True)):
        with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE|BROKER_SERVER_POLICY"):
            operation()


@pytest.mark.parametrize("modes", [
    {"campaign_team": 1}, {"campaign_team": "true"},
    {"campaign_team": True, "conformance_helpers": True},
    {"campaign_team": True, "helper_collaboration": True}, {},
])
def test_campaign_team_projection_requires_one_explicit_mode(native_team, modes):
    context, _, _ = native_team
    _, gate, _, plan, _, _, _ = context
    plan = plan.model_copy(update={"purpose": "campaign", "model": "gpt-6-luna"})
    block = wire_tools("executor")
    reviewed = {role: [{k: v for k, v in block.items() if k != "id"}] for role in ("executor", "helper")}
    with pytest.raises(Fault, match="NATIVE_TOOL_PROJECTION_SCOPE"):
        pin_tool_projection(gate.cas, plan, reviewed, **modes)


def test_no_controller_cannot_gain_team_capability(admitted):
    _, gate, _, plan, _, _, put = admitted
    plan = plan.model_copy(update={"broker_policy": TEAM_POLICY, "team_policy_ref": put(COMMUNICATION_POLICY)})
    with pytest.raises(Fault, match="TEAM_CONTROLLER_REQUIRED"):
        require_team_plan(gate.db.connection, gate.cas, plan)


def test_old_broker_does_not_expose_team(admitted):
    _, _, broker, _, _, _, _ = admitted
    assert "team" not in broker.arguments
    with pytest.raises(Fault, match="BROKER_TOOL_FORBIDDEN"):
        call(broker)


def test_copied_unpinned_team_plan_refuses_before_start(admitted):
    _, gate, _, plan, _, _, _ = admitted
    invalid = plan.model_copy(update={"broker_policy": TEAM_POLICY})
    with pytest.raises(ValidationError):
        NativeExec(gate.db, gate.cas, simulation=True).start(invalid, None)


def test_bad_team_arguments_do_not_echo_rejected_content(native_team):
    context, _, _ = native_team
    broker = context[2]
    answer = respond(broker, {"jsonrpc": "2.0", "method": "tools/call", "params": {
        "name": "team", "arguments": {"request": team_request() | {"private-marker": "sensitive"}},
        "_meta": broker_meta()}})
    assert answer == {"isError": True, "content": [{"type": "text", "text": "BROKER_ARGUMENTS_INVALID"}]}
