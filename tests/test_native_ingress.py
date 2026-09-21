"""Synthetic HTTP credentials and durable job/request fencing; no OAuth usage."""

import json
import time
from email.message import Message

import pytest
import test_native_admission

from mcbench.native_ingress import HEADER, POLICY, NativeIngress, credential, provider_binding
from mcbench.storage import Database, Fault

admitted = test_native_admission.admitted


@pytest.fixture
def ingress(admitted):
    _, gate, _, plan, _, _, _ = admitted
    secret = credential()
    plan.ingress_policy = POLICY
    plan.config_overrides |= {"model_provider": "ingress", **{
        "model_providers.ingress." + k: v for k, v in {
            "base_url": "http://127.0.0.1:19201/v1", "wire_api": "responses",
            "supports_websockets": False, "requires_openai_auth": False,
            "http_headers": {HEADER: secret}}.items()}}
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    ingress = NativeIngress(gate.db)
    ingress.register(plan)
    headers = Message()
    headers[HEADER], headers["Host"] = secret, "127.0.0.1:19201"
    return ingress, headers


def bind(ingress, value):
    service, headers = ingress
    service.bind_request("job", value[1].operation_id, value[0].request_digest, headers, "/v1/responses")


@pytest.mark.parametrize("missing", [False, True])
def test_finalization_atomically_revokes_ingress_or_retains_envelope(admitted, ingress, missing):
    from mcbench.native import NativeExec
    from test_native_retirement import settle
    _, gate, _, plan, request, prepare, put = admitted
    value = request("one")
    bind(ingress, value)
    prepare(value)
    gate._begin("a1", value[0], value[1])
    settle(admitted, value)
    gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED',returncode=0")
    seal = put({"schema": "strata/InferenceIngressSeal/1", "is_example": True, "job_id": "job",
        "profile_digest": plan.profile_digest(), "process_tree_dead": True, "ingress_closed": True,
        "handlers_fenced": True, "participant_threads": ["root"], "attempt_ids": ["one"]})
    runtime = NativeExec(gate.db, gate.cas, simulation=True)
    if missing:
        gate.db.connection.execute("DELETE FROM native_ingress")
        with pytest.raises(Fault, match="INGRESS_NOT_REGISTERED"):
            runtime.close_dispatch_budget("job", seal)
        assert gate.db.connection.execute("SELECT actual FROM operations WHERE id='job-envelope'").fetchone()[0] is None
        assert gate.db.connection.execute("SELECT state FROM native_jobs").fetchone()[0] == "UNSETTLED"
    else:
        runtime.close_dispatch_budget("job", seal)
        assert gate.db.connection.execute("SELECT revoked FROM native_ingress").fetchone()[0] == 1
        assert gate.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='native.ingress_revoked'").fetchone()[0] == 1
        with pytest.raises(Fault, match="INGRESS_REVOKED"):
            ingress[0].authenticate("job", ingress[1], "/v1/responses")


def test_historical_capture_check_never_reopens_revoked_admission(admitted, ingress):
    from mcbench.native_ingress import require_ingress_capture, require_ingress_request
    _, gate, _, plan, request, prepare, _ = admitted
    value = request("one")
    bind(ingress, value)
    ingress[0].revoke("job")
    gate.db.connection.execute("UPDATE native_jobs SET state='FINALIZED'")
    require_ingress_capture(gate.db.connection, plan, "one", value[0].request_digest)
    for action in (lambda:require_ingress_request(gate.db.connection, plan, "one", value[0].request_digest),
                   lambda:prepare(value)):
        with pytest.raises(Fault, match="INGRESS_REVOKED|RUNTIME_NOT_RUNNING"):
            action()
    with pytest.raises(Fault, match="INGRESS_REQUEST_NOT_AUTHENTICATED"):
        require_ingress_capture(gate.db.connection, plan, "one", "b" * 64)
    with pytest.raises(Fault, match="INGRESS_REQUEST_NOT_AUTHENTICATED"):
        require_ingress_capture(gate.db.connection, plan, "other", value[0].request_digest)
    gate.db.connection.execute("UPDATE native_ingress SET body='{}'")
    with pytest.raises(Fault, match="INGRESS_PROFILE_CHANGED"):
        require_ingress_capture(gate.db.connection, plan, "one", value[0].request_digest)


def test_authenticated_request_required_before_budget_and_rechecked_at_dispatch(admitted, ingress):
    _, gate, _, _, request, prepare, _ = admitted
    value = request("one")
    with pytest.raises(Fault, match="INGRESS_REQUEST_NOT_AUTHENTICATED"):
        prepare(value)
    assert gate.db.connection.execute("SELECT count(*) FROM operations").fetchone()[0] == 1
    bind(ingress, value)
    bind(ingress, value)
    prepare(value)
    assert gate._begin("a1", value[0], value[1])
    assert not gate._begin("a1", value[0], value[1])
    second = request("two")
    bind(ingress, second)
    prepare(second)
    ingress[0].revoke("job")
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="INGRESS_REVOKED"):
        gate._begin("a1", second[0], second[1])
    assert gate.budgets.status("a1") == before
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 1


@pytest.mark.parametrize("case", ["missing", "wrong", "duplicate", "host", "double_host", "route",
                                  "bearer", "cookie", "proxy", "expired", "stopping", "profile"])
def test_bad_headers_route_job_and_profile_rejected_without_cost(admitted, ingress, case):
    _, gate, _, plan, _, _, _ = admitted
    service, headers = ingress
    route = "/v1/responses"
    if case == "missing":
        del headers[HEADER]
    elif case == "wrong":
        headers.replace_header(HEADER, credential())
    elif case == "duplicate":
        headers[HEADER] = headers[HEADER]
    elif case == "host":
        headers.replace_header("Host", "localhost:19201")
    elif case == "double_host":
        headers["Host"] = headers["Host"]
    elif case == "route":
        route += "?redirect=elsewhere"
    elif case in {"bearer", "cookie", "proxy"}:
        headers[{"bearer": "Authorization", "cookie": "Cookie", "proxy": "Proxy-Authorization"}[case]] = "secret"
    elif case == "expired":
        service.clock = lambda: time.time() + 1000
    elif case == "stopping":
        gate.db.connection.execute("UPDATE native_jobs SET state='STOPPING'")
    else:
        plan.helper_limit = 1
        gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="INGRESS_"):
        service.authenticate("job", headers, route)
    assert gate.budgets.status("a1") == before
    assert gate.db.connection.execute("SELECT count(*) FROM native_ingress_requests").fetchone()[0] == 0


def test_restart_and_same_registration_cannot_renew_revocation_or_refund(admitted, ingress):
    _, gate, _, plan, request, prepare, _ = admitted
    value = request("one")
    bind(ingress, value)
    prepare(value)
    gate._begin("a1", value[0], value[1])
    ingress[0].revoke("job")
    before = gate.budgets.status("a1")
    restored = Database(gate.db.path)
    try:
        service = NativeIngress(restored)
        service.register(plan)
        with pytest.raises(Fault, match="INGRESS_REVOKED"):
            service.authenticate("job", ingress[1], "/v1/responses")
    finally:
        restored.close()
    assert gate.budgets.status("a1") == before
    assert not gate._begin("a1", value[0], value[1])  # Old intent never forwards again.


def test_authenticated_digest_cannot_be_rebound_or_headers_journaled(admitted, ingress, tmp_path):
    _, gate, _, _, request, _, _ = admitted
    value = request("one")
    bind(ingress, value)
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        ingress[0].bind_request("job", "one", "a" * 64, ingress[1], "/v1/responses")
    target = tmp_path / "journal.jsonl"
    gate.db.export_journal(target)
    assert ingress[1][HEADER] not in target.read_text()
    assert "Authorization" not in target.read_text()


def test_root_credential_cannot_authenticate_another_job(admitted, ingress):
    with pytest.raises(Fault, match="INGRESS_REVOKED"):
        ingress[0].authenticate("sibling-job", ingress[1], "/v1/responses")


def test_unauthenticated_helper_cannot_create_child_envelope(admitted, ingress):
    admission, gate, _, _, request, prepare, _ = admitted
    root = request("root-call")
    bind(ingress, root)
    prepare(root)
    gate._begin("a1", root[0], root[1])
    admission.enroll("root-call")
    child = request("child-call", "child", "/root/child", "root", child=True)
    before = gate.budgets.status("a1")
    with pytest.raises(Fault, match="INGRESS_REQUEST_NOT_AUTHENTICATED"):
        prepare(child)
    assert gate.budgets.status("a1") == before
    assert gate.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1
    assert gate.db.connection.execute("SELECT count(*) FROM operations WHERE kind='helper'").fetchone()[0] == 0


def test_authenticated_body_digest_is_required_at_admission(admitted, ingress):
    _, _, _, _, request, prepare, _ = admitted
    value = request("one")
    ingress[0].bind_request("job", "one", "a" * 64, ingress[1], "/v1/responses")
    with pytest.raises(Fault, match="INGRESS_REQUEST_NOT_AUTHENTICATED"):
        prepare(value)


@pytest.mark.parametrize("suffix,value", [("auth.command", "echo"), ("env_key", "SECRET"),
    ("http_headers.Authorization", "secret"), ("env_http_headers", {}), ("query_params", {}),
    ("base_url", "http://localhost:19201/v1"), ("base_url", "http://127.0.0.1:99999/v1"),
    ("supports_websockets", True)])
def test_unsupported_authentication_and_endpoint_overrides_rejected(admitted, ingress, suffix, value):
    plan = admitted[3]
    plan.config_overrides["model_providers.ingress." + suffix] = value
    with pytest.raises(Fault, match="INGRESS_"):
        provider_binding(plan)


def test_oauth_header_is_separate_and_never_persisted(admitted, ingress):
    _, gate, _, plan, request, _, _ = admitted
    plan.config_overrides["model_providers.ingress.requires_openai_auth"] = True
    gate.db.connection.execute("DELETE FROM native_ingress")
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    service, headers = ingress
    service.register(plan)
    for invalid in (None, "Bearer ", "Bearer a b", "Basic synthetic"):
        if "Authorization" in headers:
            del headers["Authorization"]
        if invalid is not None:
            headers["Authorization"] = invalid
        with pytest.raises(Fault, match="INGRESS_AUTH_MODE"):
            service.authenticate("job", headers, "/v1/responses")
    headers.replace_header("Authorization", "Bearer SYNTHETIC_UPSTREAM_SECRET")
    bind(ingress, request("one"))
    rows = [dict(r) for r in gate.db.connection.execute("SELECT * FROM native_ingress_requests")]
    events = [dict(r) for r in gate.db.connection.execute("SELECT * FROM outbox")]
    assert "SYNTHETIC_UPSTREAM_SECRET" not in json.dumps(rows + events)
