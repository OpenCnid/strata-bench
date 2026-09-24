"""Real local HTTP/lifecycle, synthetic native identity and provider usage only."""

import base64
import http.client
import json
import socket
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import test_inference_transport

from mcbench.accounting import EstimateBasis, FiniteExposure
from mcbench.broker import POLICY
from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceDispatches
from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_broker_policy import BROKER_TOOLS, restricted_settings
from mcbench.native_gateway import GatewayConfig, NativeGateway
from mcbench.native_ingress import HEADER, POLICY as INGRESS_POLICY
from mcbench.records import BudgetLedger
from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT
from mcbench.storage import Fault, Principal, canonical, digest

provider = test_inference_transport.provider


@pytest.fixture
def gateway(database, cas, tmp_path, example, provider):
    wire = test_inference_transport.stream(test_inference_transport.response(model="gpt-5.6-luna"))
    endpoint, upstream = provider(wire)
    runtime = NativeExec(database, cas, simulation=True)
    gate = InferenceDispatches(database, cas, simulation=True)
    gate.budgets.create_account("a1", dict.fromkeys(DIMENSIONS, 100_000_000), "c1", "a1",
                                category="training")
    service = NativeGateway(database.path, cas.root, simulation=True,
                            fixture_upstream=endpoint.removesuffix("/v1/responses"))
    def put(value):
        return cas.put(Principal("operator", "operator"), "operator", "operator", canonical(value))
    basis = EstimateBasis.model_validate(json.loads((Path(__file__).resolve().parents[1] /
        "configs/operator/legacy/live-validation-d11.json").read_text())["accounting_basis"])
    price = put(basis.model_dump())
    exposure = FiniteExposure.model_validate({"schema": "strata/FiniteInferenceExposure/1",
        "basis_digest": basis.fingerprint(), "max_input_tokens": 1050000,
        "max_output_tokens": 128000, "max_requests": 1,
        "input_bound_method": "provider_context_limit", "output_bound_method": "provider_model_limit",
        "enforcement_ref": "cas:sha256:" + "a" * 64})
    cfg = GatewayConfig.model_validate({"schema": "strata/NativeGatewayConfig/1", "job_id": "job",
        "profile_digest": "a" * 64, "pricing_ref": price, "exposure": exposure,
        "transport_qualification_ref": None, "authorization_id": None, "read_timeout_s": 1,
        "helper_calls_bound": 2, "request_timeout_s": 3, "max_requests": 6})
    config = restricted_settings() | {"mcp_servers.strata_broker": {
        "required": True, "enabled_tools": list(BROKER_TOOLS), "tools": {
            "artifact_write": {"approval_mode": "approve"}, "game": {"approval_mode": "approve"}}},
        "model_provider": "ingress", "model_providers.ingress.name": "strata",
        "model_providers.ingress.base_url": service.base_url,
        "model_providers.ingress.wire_api": "responses",
        "model_providers.ingress.requires_openai_auth": True,
        "model_providers.ingress.supports_websockets": False,
        "model_providers.ingress.http_headers": {HEADER: "s" * 43}}
    plan = NativeLaunch.model_validate({"schema": "strata/NativeLaunch/1", "job_id": "job",
        "campaign_id": "c1", "agent_id": "a1", "epoch": 1, "role": "executor",
        "parent_job_id": None, "depth": 0, "account": "a1", "operation_id": "job-envelope",
        "workspace": str(tmp_path / "workspace"), "profile_directory": str(tmp_path / "profile"),
        "executable": sys.executable, "binary_digest": "a" * 64, "binary_version": CODEX_VERSION,
        "dovetail_commit": DOVETAIL_COMMIT, "model": basis.model, "config_overrides": config,
        "environment": {}, "prompt": "ordinary goal", "hard_timeout_s": 120,
        "output_limit_bytes": 1048576, "qualification_ref": None, "budget_mode": "per_dispatch",
        "broker_policy": POLICY, "helper_limit": 2, "auth_mode": "chatgpt_oauth",
        "ingress_policy": INGRESS_POLICY, "accounting_basis_digest": basis.fingerprint(),
        "gateway_config_digest": cfg.profile_fingerprint()})
    cfg.profile_digest = plan.profile_digest()
    cfg.exposure.enforcement_ref = put({"schema": "strata/InferenceExposureEvidence/1",
        "is_example": True, "profile_digest": plan.profile_digest(), "basis_digest": basis.fingerprint(),
        "input_bound_method": "provider_context_limit", "output_bound_method": "provider_model_limit",
        "max_input_tokens": 1050000, "max_output_tokens": 128000, "result": "pass"})
    service.bind(plan, cfg)
    template = example("BudgetLedger")
    envelope = BudgetLedger.model_validate(template | {"is_example": False, "posting": "reserve",
        "operation_id": plan.operation_id, "parent_operation_id": None,
        "source_event_id": "envelope:reserve", "ledger_id": "envelope:ledger", "kind": "model",
        "model_identity": plan.model, "pricing_ref": price, "raw_usage_ref": None,
        "metering": "estimated", "usage": dict.fromkeys(template["usage"], 0) | {
            "input_tokens": 1050000 * 12, "output_tokens": 128000 * 12, "model_calls": 12,
            "spend_microusd": exposure.amount(basis) * 12}})
    gate.budgets.post("a1", envelope, envelope=True)
    with database.transaction() as db:
        db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            "job", "c1", "a1", 1, "executor", None, digest(plan.model_dump()),
            plan.model_dump_json(), "RUNNING", time.time(), None, None, None))
        db.execute("INSERT INTO native_events VALUES('job',1,'stdout',?)", (json.dumps({
            "raw_base64": base64.b64encode(canonical({"type": "thread.started", "thread_id": "root"})).decode()}),))
    def post(*, raw=None, headers=None, route="/v1/responses"):
        body = raw or canonical({"model": plan.model, "input": [], "client_metadata": {
            "x-codex-turn-metadata": json.dumps({"session_id": "root", "thread_id": "root",
                "turn_id": "turn", "agent_name": "/root", "parent_thread_id": None,
                "thread_source": "user"})}})
        conn = http.client.HTTPConnection("127.0.0.1", service.server.server_port, timeout=5)
        try:
            conn.request("POST", route, body, {"Content-Type": "application/json", HEADER: "s" * 43,
                "Authorization": "Bearer STRATA_SYNTHETIC_OAUTH_ACCESS",
                "ChatGPT-Account-ID": "strata-fixture-account"} | (headers or {}))
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()
    value = SimpleNamespace(service=service, runtime=runtime, gate=gate, plan=plan, cfg=cfg,
                            post=post, upstream=upstream, put=put, wire=wire)
    try:
        yield value
    finally:
        database.connection.execute("UPDATE native_jobs SET state='UNSETTLED' WHERE state='RUNNING'")
        if not service.finished.is_set():
            service.close(runtime)


def test_gateway_root_receipt_and_fenced_envelope(gateway):
    g = gateway
    assert g.post() == (200, g.wire)
    assert len(g.upstream) == 1
    db = g.gate.db.connection
    assert db.execute("SELECT state FROM inference_attempts").fetchone()[0] == "SETTLED"
    value = json.loads(db.execute("SELECT body FROM inference_valuations").fetchone()[0])
    assert value["kind"] == "api_equivalent_estimate" and value["token_evidence"] == "synthetic_fixture"
    before = g.gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"]
    assert before == 755400 * 12
    with pytest.raises(Fault, match="RUNTIME_NOT_QUIESCENT"):
        g.service.close(g.runtime)
    # Revoked listener still owns the port until native process termination.
    contender = socket.socket()
    try:
        with pytest.raises(OSError):
            contender.bind(("127.0.0.1", g.service.server.server_port))
    finally:
        contender.close()
    assert g.post()[0] == 403 and len(g.upstream) == 1
    db.execute("UPDATE native_jobs SET state='UNSETTLED'")
    seal = g.service.close(g.runtime)
    assert g.runtime.close_dispatch_budget("job", seal)["state"] == "FINALIZED"
    assert g.gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == value["amount_microusd"]
    assert value["amount_microusd"] == 7


@pytest.mark.parametrize("headers,route", [({HEADER: "x" * 43}, "/v1/responses"),
    ({"Authorization": "Bearer real-not-fixture"}, "/v1/responses"),
    ({}, "/v1/responses?redirect=x"), ({"Content-Encoding": "gzip"}, "/v1/responses")])
def test_gateway_rejects_before_provider(gateway, headers, route):
    assert gateway.post(headers=headers, route=route)[0] == 403
    assert gateway.upstream == []
    assert gateway.gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_missing_receipt_keeps_hold_and_blocks_next_request(gateway, provider):
    endpoint, calls = provider(b'data: {"type":"response.created"}\n\n')
    gateway.service.fixture_upstream = endpoint.removesuffix("/v1/responses")
    # Receipt-before-delivery rejects an incomplete response before forwarding
    # its headers/body; the provider request still retains its uncertain hold.
    first_status, first_raw = gateway.post()
    assert first_status == 403 and b"response.created" not in first_raw
    status, raw = gateway.post()
    assert status == 403 and json.loads(raw)["error"]["code"] == "METERING_UNKNOWN"
    assert len(calls) == 1
    db = gateway.gate.db.connection
    assert db.execute("SELECT state FROM inference_attempts").fetchone()[0] == "UNSETTLED"
    db.execute("UPDATE native_jobs SET state='UNSETTLED'")
    seal = gateway.service.close(gateway.runtime)
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        gateway.runtime.close_dispatch_budget("job", seal)
    assert gateway.gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 755400 * 12


def test_slow_partial_body_cancelled_without_dispatch(gateway):
    sock = socket.create_connection(("127.0.0.1", gateway.service.server.server_port))
    try:
        sock.sendall((f"POST /v1/responses HTTP/1.1\r\nHost: 127.0.0.1:{gateway.service.server.server_port}\r\n"
            f"{HEADER}: {'s' * 43}\r\nAuthorization: Bearer STRATA_SYNTHETIC_OAUTH_ACCESS\r\n"
            "Content-Length: 100\r\n\r\n{").encode())
        sock.settimeout(2)
        assert sock.recv(1) == b""
    finally:
        sock.close()
    assert gateway.upstream == []
    assert gateway.gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_shutdown_cancels_ambiguous_upstream_once(gateway, provider):
    endpoint, calls = provider(gateway.wire, delay=2)
    gateway.service.fixture_upstream = endpoint.removesuffix("/v1/responses")
    failures = []
    def request():
        try:
            gateway.post()
        except (OSError, http.client.HTTPException) as error:
            failures.append(type(error).__name__)
    thread = threading.Thread(target=request)
    thread.start()
    deadline = time.monotonic() + 2
    while not calls and time.monotonic() < deadline:
        time.sleep(.01)
    assert len(calls) == 1
    gateway.service.stop_admission()
    thread.join(1)
    assert not thread.is_alive()
    gateway.gate.db.connection.execute("UPDATE native_jobs SET state='UNSETTLED'")
    seal = gateway.service.close(gateway.runtime)
    assert gateway.gate.db.connection.execute("SELECT state FROM inference_attempts").fetchone()[0] == "UNSETTLED"
    with pytest.raises(Fault, match="METERING_UNKNOWN"):
        gateway.runtime.close_dispatch_budget("job", seal)


def test_no_rebind_or_config_alias_mutation(gateway):
    gateway.cfg.max_requests = 1
    assert gateway.service.config.max_requests == 6
    with pytest.raises(Fault, match="GATEWAY_ALREADY_BOUND"):
        gateway.service.bind(gateway.plan, gateway.cfg)


def test_request_cap_returns_typed_error_without_dispatch_or_charge(gateway, provider):
    g = gateway
    upstreams = []
    for ordinal in range(6):
        wire = test_inference_transport.stream(test_inference_transport.response(
            model=g.plan.model, id=f"response-{ordinal}"))
        endpoint, calls = provider(wire)
        upstreams.append(calls)
        g.service.fixture_upstream = endpoint.removesuffix("/v1/responses")
        raw = canonical({"model": g.plan.model, "input": [{"role": "user", "content": str(ordinal)}],
            "client_metadata": {"x-codex-turn-metadata": json.dumps({"session_id": "root", "thread_id": "root",
                "turn_id": f"turn-{ordinal}", "agent_name": "/root", "parent_thread_id": None,
                "thread_source": "user"})}})
        assert g.post(raw=raw) == (200, wire)
    before = g.gate.budgets.status("a1")
    status, raw = g.post()
    assert status == 403
    assert json.loads(raw)["error"]["code"] == "GATEWAY_REQUEST_LIMIT"
    assert sum(map(len, upstreams)) == 6
    db = g.gate.db.connection
    assert db.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 6
    assert db.execute("SELECT count(*) FROM native_gateway_requests").fetchone()[0] == 6
    assert g.gate.budgets.status("a1") == before
    audit = json.loads(db.execute("SELECT body FROM outbox WHERE kind='native.gateway_refused'").fetchone()[0])
    assert audit == {"job": "job", "reason": "GATEWAY_REQUEST_LIMIT", "max_requests": 6}
