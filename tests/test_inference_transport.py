"""Actual local HTTP transport with synthetic rates/receipts; no external provider."""

import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
from mcbench.inference_transport import MAX_RESPONSE_BYTES, ResponsesUsage, SyntheticResponsesTransport
from mcbench.records import BudgetLedger
from mcbench.storage import Fault, Principal, canonical, digest


def response(**updates):
    return {"id": "synthetic-response-1", "model": "synthetic", "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
                      "input_tokens_details": {"cached_tokens": 2},
                      "output_tokens_details": {"reasoning_tokens": 1}}, **updates}


def stream(body):
    return b"event: response.completed\ndata: " + canonical({"type": "response.completed",
                                                           "response": body}) + b"\n\n"


@pytest.mark.parametrize("size", [1, 3, 65536])
def test_fragmented_sse_and_duplicate_final_receipt_are_one_usage(size):
    parser = ResponsesUsage("synthetic", "text/event-stream")
    wire = b": heartbeat\n\n" + stream(response()) * 2 + b"data: [DONE]\n\n"
    for pos in range(0, len(wire), size):
        parser.feed(wire[pos:pos + size])
    assert parser.finish() == {"event": "synthetic-response-1", "input_tokens": 10,
        "cached_input_tokens": 2, "output_tokens": 4, "reasoning_tokens": 1, "model_calls": 1}
    assert bytes(parser.raw) == wire


@pytest.mark.parametrize("wire,code", [
    (b"data: [DONE]\n\n", "AUTHORITATIVE_USAGE_REQUIRED"),
    (stream(response())[:-1], "TRUNCATED_EVENT_STREAM"),
    (stream(response(model="other")), "RESPONSE_SCOPE_MISMATCH"),
    (stream(response(usage=None)), "AUTHORITATIVE_USAGE_REQUIRED"),
    (stream(response()) + stream(response(id="other")), "CONFLICTING_USAGE_RECEIPT"),
    (stream(response()) + b'data: {"type":"response.output_text.delta"}\n\n',
     "EVENT_AFTER_TERMINAL_USAGE"),
    (b'data: {"type":"x","type":"response.completed"}\n\n', "DUPLICATE_JSON_KEY"),
    (b'data: {"type":"x","value":NaN}\n\n', "INVALID_JSON_NUMBER"),
    (stream(response()).replace(b'"input_tokens":10', b'"input_tokens":true'),
     "AUTHORITATIVE_USAGE_REQUIRED"),
    (stream(response()).replace(b'"cached_tokens":2', b'"cached_tokens":11'),
     "USAGE_TOTAL_MISMATCH"),
    (stream(response()).replace(b'"total_tokens":14', b'"total_tokens":15'),
     "USAGE_TOTAL_MISMATCH"),
    (stream(response()).replace(b'"reasoning_tokens":1', b'"reasoning_tokens":5'),
     "USAGE_TOTAL_MISMATCH"),
    (stream(response()).replace(b'"cached_tokens":2', b'"cached_tokens":2,"audio_tokens":1'),
     "USAGE_SEMANTICS_UNSUPPORTED"),
])
def test_malformed_missing_conflicting_and_unsupported_usage_fail_closed(wire, code):
    parser = ResponsesUsage("synthetic", "text/event-stream")
    with pytest.raises(Fault, match=code):
        parser.feed(wire)
        parser.finish()


def test_json_compaction_and_response_quota():
    parser = ResponsesUsage("synthetic", "application/json")
    parser.feed(canonical(response()))
    assert parser.finish()["model_calls"] == 1
    with pytest.raises(Fault, match="RESPONSE_SIZE"):
        parser.feed(b" " * MAX_RESPONSE_BYTES)


@pytest.fixture
def fixture_gateway(database, cas, example):
    gate = InferenceDispatches(database, cas, simulation=True)
    gate.budgets.create_account("a1", dict.fromkeys(DIMENSIONS, 1000000),
                                "c1", "a1", category="training")
    def put(value):
        return cas.put(Principal("operator", "operator"), "operator", "operator", canonical(value))
    price = put({"schema": "strata/SyntheticTokenPricing/1", "is_example": True, "currency": "USD",
                 "input_microusd_per_token": 3, "cached_microusd_per_token": 1,
                 "output_microusd_per_token": 5})
    request = canonical({"model": "synthetic", "stream": True})
    body = example("BudgetLedger")
    reserve = BudgetLedger.model_validate(body | {"is_example": False,
        "operation_id": "request1", "parent_operation_id": None, "pricing_ref": price,
        "model_identity": "synthetic", "posting": "reserve", "metering": "estimated",
        "usage": body["usage"] | {"model_calls": 1, "spend_microusd": 1000}})
    fields = {"runtime_job_id": "job1", "profile_digest": "a" * 64, "provider": "synthetic",
              "auth_mode": "api_key", "request_digest": hashlib.sha256(request).hexdigest()}
    bound = put({"schema": "strata/InferenceDispatchBound/1", "is_example": True, **fields,
        "reservation_digest": digest(reserve.model_dump()), "pricing_ref": price,
        "currency": "USD", "finite_dispatch_bound_verified": True, "pricing_semantics_verified": True,
        "expires_unix_ms": time.time_ns() // 1000000 + 60000})
    attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1", **fields,
                                              "bound_ref": bound})
    return gate, attempt, reserve, request


@pytest.fixture
def provider():
    providers = []
    def start(wire, *, status=200, media="text/event-stream", delay=0, redirect=None):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                requests.append({"body": self.rfile.read(int(self.headers["Content-Length"])),
                                 "authorization": self.headers.get("Authorization")})
                self.send_response(status)
                self.send_header("Content-Type", media)
                self.send_header("Content-Length", str(len(wire)))
                if redirect:
                    self.send_header("Location", redirect)
                self.end_headers()
                time.sleep(delay)
                try:
                    self.wfile.write(wire)
                except OSError:
                    pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        providers.append((server, thread))
        return f"http://127.0.0.1:{server.server_port}/v1/responses", requests
    yield start
    for server, thread in providers:
        server.shutdown()
        server.server_close()
        thread.join(2)


def test_actual_http_single_forward_and_wire_receipt(fixture_gateway, provider):
    gate, attempt, reserve, request = fixture_gateway
    wire = stream(response())
    endpoint, requests = provider(wire)
    transport = SyntheticResponsesTransport(gate, endpoint)
    delivered, headers = [], []
    def header(status, media):
        assert gate.status(reserve.operation_id)["state"] == "SETTLED"
        headers.append((status, media))
    for _ in range(2):
        result = transport.execute("a1", attempt, reserve, request,
                                   on_headers=header, on_chunk=delivered.append)
        assert result["state"] == "SETTLED"
    assert requests == [{"body": request, "authorization": None}]
    assert headers == [(200, "text/event-stream")] and b"".join(delivered) == wire
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 46
    row = gate.db.connection.execute("SELECT body FROM ledger WHERE "
                                    "json_extract(body,'$.posting')='settle'").fetchone()
    receipt = BudgetLedger.model_validate_json(row[0])
    assert gate.cas.read(Principal("operator", "operator"), "operator", receipt.raw_usage_ref) == wire


@pytest.mark.parametrize("mode", ["missing", "truncated", "redirect", "timeout"])
def test_transport_fault_never_retries_or_refunds(fixture_gateway, provider, mode):
    gate, attempt, reserve, request = fixture_gateway
    wire = stream(response(usage=None)) if mode == "missing" else stream(response())
    if mode == "truncated":
        wire = wire[:-1]
    endpoint, requests = provider(wire, status=302 if mode == "redirect" else 200,
        redirect="http://192.0.2.1/forbidden" if mode == "redirect" else None,
        delay=0.2 if mode == "timeout" else 0)
    transport = SyntheticResponsesTransport(gate, endpoint, deadline_s=0.05 if mode == "timeout" else 3)
    def write(chunk):
        if mode == "writer_failure":
            raise BrokenPipeError("synthetic-secret-do-not-record")
    with pytest.raises((Fault, TimeoutError, BrokenPipeError)):
        transport.execute("a1", attempt, reserve, request, on_headers=lambda *_: None, on_chunk=write)
    assert len(requests) == 1
    assert gate.status(reserve.operation_id)["state"] == "UNSETTLED"
    assert gate.budgets.status("a1")["uncertain"]
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000
    audit = json.loads(gate.db.connection.execute(
        "SELECT body FROM outbox WHERE kind='inference.transport_failure'").fetchone()[0])
    reason, phase = {
        "missing": ("AUTHORITATIVE_USAGE_REQUIRED", "response_body"),
        "truncated": ("TRUNCATED_EVENT_STREAM", "receipt_validation"),
        "redirect": ("REDIRECT_REJECTED", "response_headers"),
        "timeout": ("TRANSPORT_TIMEOUT", "response_body"),
        "writer_failure": ("TRANSPORT_IO_ERROR", "deliver_body"),
    }[mode]
    assert audit["reason"] == reason and audit["phase"] == phase
    assert audit["deadline_ms"] == (50 if mode == "timeout" else 3000)
    assert 0 <= audit["elapsed_ms"] < 4000 and audit["captured_bytes"] <= len(wire)
    assert "synthetic-secret-do-not-record" not in json.dumps(audit)
    assert set(audit) == {"operation_id", "phase", "reason", "elapsed_ms", "deadline_ms", "captured_bytes", "simulation"}
    transport.execute("a1", attempt, reserve, request, on_headers=lambda *_: None, on_chunk=write)
    assert len(requests) == 1
    assert gate.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='inference.transport_failure'").fetchone()[0] == 1


@pytest.mark.parametrize("endpoint", ["https://api.openai.com/v1/responses",
    "http://localhost:80/v1/responses", "http://127.0.0.1:80/other",
    "http://user:password@127.0.0.1:80/v1/responses", "http://127.0.0.1:80/v1/responses?x=1"])
def test_nonliteral_loopback_or_credential_endpoints_reject(fixture_gateway, endpoint):
    with pytest.raises(Fault, match="SYNTHETIC_ENDPOINT_REQUIRED"):
        SyntheticResponsesTransport(fixture_gateway[0], endpoint)


def test_live_stores_cannot_enable_this_fixture_transport(database, cas):
    live = InferenceDispatches(database, cas, simulation=False)
    with pytest.raises(Fault, match="LIVE_TRANSPORT_UNQUALIFIED"):
        SyntheticResponsesTransport(live, "http://127.0.0.1:1/v1/responses")


def test_changed_request_digest_rejects_before_any_reservation(fixture_gateway):
    gate, attempt, reserve, _ = fixture_gateway
    transport = SyntheticResponsesTransport(gate, "http://127.0.0.1:1/v1/responses")
    with pytest.raises(Fault, match="REQUEST_DIGEST_MISMATCH"):
        transport.execute("a1", attempt, reserve, b'{"model":"changed"}',
                          on_headers=lambda *_: None, on_chunk=lambda *_: None)
    assert gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0
