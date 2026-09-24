"""Bounded Responses receipt transport with separate concrete admission adapters.

SyntheticResponsesTransport admits only credential-free literal loopback HTTP
and permanently simulated stores. The OAuth adapter lives in native_oauth.py.
Shared parsing/accounting does not qualify either adapter. One invocation makes
at most one upstream POST; each actual retry needs a distinct reservation.
"""

import hashlib
import http.client
import json
import socket
import threading
import time
import uuid
from urllib.parse import urlsplit

from .accounting import EstimateBasis, TokenUsage, UsageValuation
from .records import BudgetLedger
from .storage import Fault, Principal, require

MAX_RESPONSE_BYTES = 256 * 1024
MAX_REQUEST_TIMEOUT_S = 60
BUFFERED_SSE_POLICY = "native-complete-receipt-before-media-normalization/1"
DELIVERY_POLICY = "durable-settled-receipt-before-delivery/1"


def transport_failure_code(error, *, cancelled=False):
    """Stable diagnosis without exception messages, URLs, headers or credentials."""
    if cancelled:
        return "TRANSPORT_CANCELLED"
    if isinstance(error, Fault):
        return error.code
    if isinstance(error, TimeoutError):
        return "TRANSPORT_TIMEOUT"
    if isinstance(error, http.client.IncompleteRead):
        return "TRANSPORT_TRUNCATED_BODY"
    if isinstance(error, http.client.HTTPException):
        return "TRANSPORT_HTTP_ERROR"
    if isinstance(error, OSError):
        return "TRANSPORT_IO_ERROR"
    return "TRANSPORT_INTERNAL_ERROR"


def strict_json(raw):
    def constant(_):
        require(False, "INVALID_JSON_NUMBER")

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def count(value):
    require(type(value) is int and 0 <= value <= 2**53 - 1, "AUTHORITATIVE_USAGE_REQUIRED")
    return value


class ResponsesUsage:
    """Incremental bounded SSE/JSON receipt capture, never a turn-total estimate."""

    def __init__(self, model, content_type):
        require(content_type in {"text/event-stream", "application/json"}, "RESPONSE_CONTENT_TYPE")
        self.model, self.content_type = model, content_type
        self.raw = bytearray()
        self.pending = bytearray()
        self.data_lines = []
        self.event_name = None
        self.receipt = None

    def feed(self, chunk):
        require(isinstance(chunk, bytes) and len(self.raw) + len(chunk) <= MAX_RESPONSE_BYTES,
                "RESPONSE_SIZE")
        self.raw.extend(chunk)
        if self.content_type == "application/json":
            return
        self.pending.extend(chunk)
        while b"\n" in self.pending:
            line, _, rest = self.pending.partition(b"\n")
            self.pending = bytearray(rest)
            text = line.rstrip(b"\r").decode("utf-8", errors="strict")
            if not text:
                self._event()
            elif text.startswith("data:"):
                self.data_lines.append(text[5:].lstrip(" "))
            elif text.startswith("event:"):
                self.event_name = text[6:].lstrip(" ")
            elif text.startswith(":") or text.startswith(("id:", "retry:")):
                pass
            else:
                require(False, "INVALID_EVENT_STREAM")

    def _event(self):
        if self.data_lines:
            data = "\n".join(self.data_lines)
            if data != "[DONE]":
                item = strict_json(data)
                require(isinstance(item, dict), "INVALID_EVENT_STREAM")
                kind = item.get("type")
                require(self.event_name is None or self.event_name == kind, "EVENT_TYPE_MISMATCH")
                require(self.receipt is None or kind in {
                    "response.completed", "response.failed", "response.incomplete"},
                    "EVENT_AFTER_TERMINAL_USAGE")
                if kind in {"response.completed", "response.failed", "response.incomplete"}:
                    require(isinstance(item.get("response"), dict) and
                            item["response"].get("status") == kind.split(".")[1],
                            "RESPONSE_SCOPE_MISMATCH")
                    self._receipt(item.get("response"))
        self.data_lines = []
        self.event_name = None

    def _receipt(self, response):
        require(isinstance(response, dict) and response.get("model") == self.model and
                response.get("status") in {"completed", "failed", "incomplete"},
                "RESPONSE_SCOPE_MISMATCH")
        event = response.get("id")
        require(isinstance(event, str) and 0 < len(event) <= 256 and
                all(ord(c) >= 33 for c in event), "PROVIDER_EVENT_INVALID")
        usage = response.get("usage")
        require(isinstance(usage, dict) and set(usage) <= {
            "input_tokens", "output_tokens", "total_tokens", "input_tokens_details",
            "output_tokens_details", "attribution"}, "AUTHORITATIVE_USAGE_REQUIRED")
        inputs, outputs = count(usage.get("input_tokens")), count(usage.get("output_tokens"))
        details = usage.get("input_tokens_details")
        out_details = usage.get("output_tokens_details")
        require(isinstance(details, dict) and set(details) in (
                    {"cached_tokens"}, {"cached_tokens", "cache_write_tokens"}) and
                isinstance(out_details, dict) and set(out_details) == {"reasoning_tokens"},
                "USAGE_SEMANTICS_UNSUPPORTED")
        cached, reasoning = count(details["cached_tokens"]), count(out_details["reasoning_tokens"])
        writes = count(details["cache_write_tokens"]) if "cache_write_tokens" in details else None
        from .native_usage import validate_no_hosted_usage
        validate_no_hosted_usage(response.get("tool_usage"))
        require(cached + (writes or 0) <= inputs, "USAGE_TOTAL_MISMATCH")
        if "attribution" in usage:
            from .native_usage import validate_attribution
            require(writes is not None, "USAGE_ATTRIBUTION_UNSUPPORTED")
            validate_attribution(usage["attribution"], {"input_tokens": inputs, "output_tokens": outputs,
                "cached_tokens": cached, "cache_write_tokens": writes})
        require(cached <= inputs and reasoning <= outputs and
                count(usage.get("total_tokens")) == inputs + outputs, "USAGE_TOTAL_MISMATCH")
        receipt = {"event": event, "input_tokens": inputs, "cached_input_tokens": cached,
                   "output_tokens": outputs, "reasoning_tokens": reasoning, "model_calls": 1}
        if writes is not None:
            receipt["cache_write_tokens"] = writes
        require(self.receipt is None or self.receipt == receipt, "CONFLICTING_USAGE_RECEIPT")
        self.receipt = receipt

    def finish(self):
        if self.content_type == "application/json":
            self._receipt(strict_json(bytes(self.raw)))
        else:
            # Do not accept a final event whose SSE frame was truncated, even if
            # its JSON happens to look complete. Preserve the raw bytes as evidence.
            require(not self.pending and not self.data_lines and self.event_name is None,
                    "TRUNCATED_EVENT_STREAM")
        require(self.receipt is not None, "AUTHORITATIVE_USAGE_REQUIRED")
        return self.receipt.copy()


class RejectedResponseCapture:
    """Private bounded diagnostics; never a usage receipt or agent response."""

    content_type = "application/octet-stream"

    def __init__(self):
        self.raw = bytearray()

    def feed(self, chunk):
        require(len(self.raw) + len(chunk) <= MAX_RESPONSE_BYTES, "RESPONSE_SIZE")
        self.raw.extend(chunk)

    def finish(self):
        require(False, "RESPONSE_CONTENT_TYPE")


class _ResponsesTransport:
    """Shared bounded receipt transport. Concrete adapters enforce admission.

    ``on_headers``/``on_chunk`` are trusted bounded ingress writers. They must not
    retry, transform billing evidence or block indefinitely. Ingress closes/fences
    every writer before sealing a native job. This class owns the upstream socket.
    """

    def _preflight(self, attempt, reserve):
        pass

    def _init_lifetime(self):
        self.cancelled = threading.Event()
        self.connection_lock = threading.Lock()
        self.active_socket = None

    def cancel(self):
        self.cancelled.set()
        with self.connection_lock:
            sock = self.active_socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _filter(self, chunk, *, final=False):
        return chunk

    def execute(self, account, attempt, reserve, body, *, on_headers, on_chunk, after_begin=None):
        require(not self.cancelled.is_set(), "TRANSPORT_CANCELLED")
        require(isinstance(body, bytes) and 0 < len(body) <= 1024 * 1024, "REQUEST_SIZE")
        require(hashlib.sha256(body).hexdigest() == attempt.request_digest, "REQUEST_DIGEST_MISMATCH")
        parsed = strict_json(body)
        require(isinstance(parsed, dict) and parsed.get("model") == reserve.model_identity,
                "RESPONSE_SCOPE_MISMATCH")
        self._preflight(attempt, reserve)
        # These are synthetic per-token integer rates, not OpenAI prices. Pin the
        # exact private price record also named by the qualified bound/reservation.
        price = strict_json(self.gate._private_ref(reserve.pricing_ref, 16384))
        basis = None
        if price.get("schema", price.get("schema_")) == "strata/ApiEquivalentEstimateBasis/1":
            basis = EstimateBasis.model_validate(price)
        else:
            require(self.gate.simulation, "VERSIONED_ESTIMATE_REQUIRED")
            require(price.get("schema") == "strata/SyntheticTokenPricing/1" and
                    price.get("is_example") is True and price.get("currency") == "USD",
                    "SYNTHETIC_PRICING_REQUIRED")
            rates = {key: count(price.get(key)) for key in (
                "input_microusd_per_token", "cached_microusd_per_token", "output_microusd_per_token")}

        from .storage_capacity import reserve as reserve_space, release
        principal = Principal(self.gate.namespace, "operator")
        space_token = None
        if self.gate.db.connection.execute("SELECT 1 FROM inference_attempts WHERE operation=?",
                                           (reserve.operation_id,)).fetchone() is None:
            space_token = "receipt:" + uuid.uuid4().hex
            reserve_space(self.gate.cas, principal, self.gate.namespace, space_token, MAX_RESPONSE_BYTES)
        delivery = []
        forwarded = False

        def forward():
            nonlocal forwarded
            require(space_token is not None, "ARTIFACT_RESERVATION_INVALID")
            forwarded = True
            started = time.monotonic()
            deadline = started + self.deadline_s
            require(not self.cancelled.is_set(), "TRANSPORT_CANCELLED")
            if after_begin is not None:
                after_begin()
            connection, path, headers = self._request()
            capture = None
            raw_ref = None
            phase = "connect"
            try:
                connection.connect()
                sock = connection.sock
                with self.connection_lock:
                    self.active_socket = sock
                require(not self.cancelled.is_set(), "TRANSPORT_CANCELLED")
                phase = "send_request"
                connection.request("POST", path, body=body, headers=headers)
                remaining = deadline - time.monotonic()
                require(remaining > 0, "TRANSPORT_DEADLINE")
                sock.settimeout(remaining)
                phase = "response_headers"
                response = connection.getresponse()
                media = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
                # Preserve safe diagnostic metadata even when the wire format is
                # unsupported. Do not retain arbitrary header values or infer cost.
                with self.gate.db.transaction() as db:
                    self.gate.db.event(db, "inference.http_response", {
                        "operation_id": reserve.operation_id, "status": response.status,
                        "media_class": media if media in {"application/json", "text/event-stream",
                            "text/html", "text/plain", "application/x-ndjson", "application/jsonl"} else "other",
                        "identity_encoding": response.getheader("Content-Encoding", "identity") == "identity",
                        "simulation": self.gate.simulation})
                require(response.status not in range(300, 400), "REDIRECT_REJECTED")
                require(response.getheader("Content-Encoding", "identity") == "identity",
                        "RESPONSE_ENCODING")
                supported = media in {"application/json", "text/event-stream"}
                buffered_sse = (not supported and response.status == 200 and
                                getattr(self, "buffered_sse_policy", None) == BUFFERED_SSE_POLICY)
                capture = ResponsesUsage(reserve.model_identity, media if supported else "text/event-stream") if (
                    supported or buffered_sse) else RejectedResponseCapture()
                while not response.isclosed():
                    phase = "response_body"
                    remaining = deadline - time.monotonic()
                    require(remaining > 0, "TRANSPORT_DEADLINE")
                    sock.settimeout(remaining)
                    chunk = response.read1(16384)
                    if not chunk:
                        break
                    safe = self._filter(chunk)
                    if safe:
                        capture.feed(safe)
                phase = "receipt_validation"
                safe = self._filter(b"", final=True)
                if safe:
                    capture.feed(safe)
                phase = "receipt_validation"
                observed = capture.finish()
                if buffered_sse:
                    # Only the fixed native adapter opts in. Withhold the entire
                    # bounded body until strict framing, scope and usage pass;
                    # errors/HTML/partial output never reach the native runtime.
                    with self.gate.db.transaction() as db:
                        self.gate.db.event(db, "inference.media_normalized", {
                            "operation_id": reserve.operation_id, "policy": BUFFERED_SSE_POLICY,
                            "raw_sha256": hashlib.sha256(capture.raw).hexdigest(),
                            "simulation": self.gate.simulation})
                phase = "receipt_recording"
                event = observed.pop("event")
                writes = observed.pop("cache_write_tokens", None)
                # Cached input and reasoning output are subsets, never added twice.
                if basis:
                    tokens = TokenUsage.model_validate({k: observed[k] for k in (
                        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")}
                        | {"model": reserve.model_identity, "cache_write_tokens": writes})
                    spend = basis.estimate(tokens)
                else:
                    spend = ((observed["input_tokens"] - observed["cached_input_tokens"]) *
                             rates["input_microusd_per_token"] + observed["cached_input_tokens"] *
                             rates["cached_microusd_per_token"] + observed["output_tokens"] *
                             rates["output_microusd_per_token"])
                count(spend)
                raw_ref = self._save(capture, reserve.operation_id, space_token)
                event_id = "wire-" + hashlib.sha256(reserve.operation_id.encode()).hexdigest()
                receipt = BudgetLedger.model_validate(reserve.model_dump() | {
                    "posting": "settle", "source_event_id": event_id + ":settle",
                    "ledger_id": event_id + ":receipt",
                    "metering": "estimated" if basis else "reported",
                    "raw_usage_ref": raw_ref, "usage": reserve.usage.model_dump() | observed |
                    {"spend_microusd": spend, "wall_ms": int((time.monotonic() - started) * 1000)}})
                delivery.append((response.status, "text/event-stream" if buffered_sse else media,
                                 bytes(capture.raw)))
                if basis:
                    valuation = UsageValuation.model_validate({"schema": "strata/UsageValuation/1",
                        "kind": "api_equivalent_estimate", "basis_digest": basis.fingerprint(),
                        "raw_usage_ref": raw_ref, "usage": tokens, "amount_microusd": spend,
                        "token_evidence": "synthetic_fixture" if self.gate.simulation else "provider_reported"})
                    return event, receipt, valuation
                return event, receipt
            except Exception as error:
                with self.gate.db.transaction() as db:
                    self.gate.db.event(db, "inference.transport_failure", {
                        "operation_id": reserve.operation_id, "phase": phase,
                        "reason": transport_failure_code(error, cancelled=self.cancelled.is_set()),
                        "elapsed_ms": int((time.monotonic() - started) * 1000),
                        "deadline_ms": int(self.deadline_s * 1000),
                        "captured_bytes": len(capture.raw) if capture is not None else 0,
                        "simulation": self.gate.simulation})
                raise
            finally:
                connection.close()
                with self.connection_lock:
                    self.active_socket = None
                if capture is not None and raw_ref is None:
                    # Retain even malformed/partial usage; no zero-cost settlement.
                    self._save(capture, reserve.operation_id, space_token)

        try:
            result = self.gate.execute(account, attempt, reserve, forward)
        finally:
            if space_token is not None and not forwarded:
                release(self.gate.cas, self.gate.namespace, space_token)
        # Idempotent status reads never redeliver output. A delivery failure does
        # not erase a known durable cost or replay a settled provider request.
        if delivery:
            require(result["state"] == "SETTLED", "RECEIPT_NOT_SETTLED")
            status, media, wire = delivery[0]
            try:
                on_headers(status, media)
                on_chunk(wire)
            except Exception as error:
                with self.gate.db.transaction() as db:
                    self.gate.db.event(db, "inference.delivery_failure", {
                        "operation_id": reserve.operation_id, "policy": DELIVERY_POLICY,
                        "reason": transport_failure_code(error, cancelled=self.cancelled.is_set()),
                        "receipt_settled": True, "simulation": self.gate.simulation})
                raise
        return result

    def _save(self, capture, operation, space_token):
        ref = self.gate.cas.put(Principal(self.gate.namespace, "operator"), self.gate.namespace,
                                "operator", bytes(capture.raw), media_type=capture.content_type, reservation=space_token)
        with self.gate.db.transaction() as db:
            self.gate.db.event(db, "inference.wire_capture", {"operation_id": operation,
                "raw_usage_ref": ref,
                "bytes": len(capture.raw), "simulation": self.gate.simulation})
        return ref


class SyntheticResponsesTransport(_ResponsesTransport):
    """Credential-free loopback adapter. Its simulation-only guard is mandatory."""

    def __init__(self, dispatches, endpoint, *, deadline_s=3):
        require(dispatches.simulation, "LIVE_TRANSPORT_UNQUALIFIED")
        url = urlsplit(endpoint)
        require(url.scheme == "http" and url.hostname == "127.0.0.1" and
                url.port is not None and 0 < url.port < 65536 and
                url.username is None and url.password is None and not url.query and
                not url.fragment and url.path in {"/v1/responses", "/v1/responses/compact"},
                "SYNTHETIC_ENDPOINT_REQUIRED")
        require(type(deadline_s) in {int, float} and 0 < deadline_s <= MAX_REQUEST_TIMEOUT_S,
                "TRANSPORT_DEADLINE")
        self.gate, self.url, self.deadline_s = dispatches, url, deadline_s
        self._init_lifetime()

    def _request(self):
        return (http.client.HTTPConnection("127.0.0.1", self.url.port, timeout=self.deadline_s),
                self.url.path, {"Content-Type": "application/json"})
