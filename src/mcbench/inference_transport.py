"""Bounded Responses wire transport for credential-free integration qualification.

Only literal loopback HTTP and permanently simulated stores are admitted. This
does not implement an authenticated OAuth broker or supply its missing monetary,
exposure and isolation evidence. One invocation makes at most one upstream POST;
the caller must obtain a distinct durable reservation for each actual retry.
"""

import hashlib
import http.client
import json
import time
from urllib.parse import urlsplit

from .accounting import EstimateBasis, TokenUsage, UsageValuation
from .records import BudgetLedger
from .storage import Principal, require

MAX_RESPONSE_BYTES = 256 * 1024


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
            "output_tokens_details"}, "AUTHORITATIVE_USAGE_REQUIRED")
        inputs, outputs = count(usage.get("input_tokens")), count(usage.get("output_tokens"))
        details = usage.get("input_tokens_details")
        out_details = usage.get("output_tokens_details")
        require(isinstance(details, dict) and set(details) == {"cached_tokens"} and
                isinstance(out_details, dict) and set(out_details) == {"reasoning_tokens"},
                "USAGE_SEMANTICS_UNSUPPORTED")
        cached, reasoning = count(details["cached_tokens"]), count(out_details["reasoning_tokens"])
        require(cached <= inputs and reasoning <= outputs and
                count(usage.get("total_tokens")) == inputs + outputs, "USAGE_TOTAL_MISMATCH")
        receipt = {"event": event, "input_tokens": inputs, "cached_input_tokens": cached,
                   "output_tokens": outputs, "reasoning_tokens": reasoning, "model_calls": 1}
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


class SyntheticResponsesTransport:
    """Reusable one-request transport, explicitly unusable for live inference.

    ``on_headers``/``on_chunk`` are trusted bounded ingress writers. They must not
    retry, transform billing evidence or block indefinitely. Ingress closes/fences
    every writer before sealing a native job. This class owns the upstream socket.
    """

    def __init__(self, dispatches, endpoint, *, deadline_s=3):
        require(dispatches.simulation, "LIVE_TRANSPORT_UNQUALIFIED")
        url = urlsplit(endpoint)
        require(url.scheme == "http" and url.hostname == "127.0.0.1" and
                url.port is not None and 0 < url.port < 65536 and
                url.username is None and url.password is None and not url.query and
                not url.fragment and url.path in {"/v1/responses", "/v1/responses/compact"},
                "SYNTHETIC_ENDPOINT_REQUIRED")
        require(type(deadline_s) in {int, float} and 0 < deadline_s <= 30, "TRANSPORT_DEADLINE")
        self.gate, self.url, self.deadline_s = dispatches, url, deadline_s

    def execute(self, account, attempt, reserve, body, *, on_headers, on_chunk):
        require(isinstance(body, bytes) and 0 < len(body) <= 1024 * 1024, "REQUEST_SIZE")
        require(hashlib.sha256(body).hexdigest() == attempt.request_digest, "REQUEST_DIGEST_MISMATCH")
        parsed = strict_json(body)
        require(isinstance(parsed, dict) and parsed.get("model") == reserve.model_identity,
                "RESPONSE_SCOPE_MISMATCH")
        # These are synthetic per-token integer rates, not OpenAI prices. Pin the
        # exact private price record also named by the qualified bound/reservation.
        price = strict_json(self.gate._private_ref(reserve.pricing_ref, 16384))
        basis = None
        if price.get("schema", price.get("schema_")) == "strata/ApiEquivalentEstimateBasis/1":
            basis = EstimateBasis.model_validate(price)
        else:
            require(price.get("schema") == "strata/SyntheticTokenPricing/1" and
                    price.get("is_example") is True and price.get("currency") == "USD",
                    "SYNTHETIC_PRICING_REQUIRED")
            rates = {key: count(price.get(key)) for key in (
                "input_microusd_per_token", "cached_microusd_per_token", "output_microusd_per_token")}

        def forward():
            started = time.monotonic()
            deadline = started + self.deadline_s
            connection = http.client.HTTPConnection("127.0.0.1", self.url.port,
                                                     timeout=self.deadline_s)
            capture = None
            raw_ref = None
            try:
                connection.connect()
                sock = connection.sock
                connection.request("POST", self.url.path, body=body,
                                   headers={"Content-Type": "application/json"})
                remaining = deadline - time.monotonic()
                require(remaining > 0, "TRANSPORT_DEADLINE")
                sock.settimeout(remaining)
                response = connection.getresponse()
                require(response.status not in range(300, 400), "REDIRECT_REJECTED")
                media = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
                require(response.getheader("Content-Encoding", "identity") == "identity",
                        "RESPONSE_ENCODING")
                capture = ResponsesUsage(reserve.model_identity, media)
                on_headers(response.status, media)
                while not response.isclosed():
                    remaining = deadline - time.monotonic()
                    require(remaining > 0, "TRANSPORT_DEADLINE")
                    sock.settimeout(remaining)
                    chunk = response.read1(16384)
                    if not chunk:
                        break
                    capture.feed(chunk)
                    on_chunk(chunk)
                observed = capture.finish()
                event = observed.pop("event")
                # Cached input and reasoning output are subsets, never added twice.
                if basis:
                    tokens = TokenUsage.model_validate({k: observed[k] for k in (
                        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")}
                        | {"model": reserve.model_identity, "cache_write_tokens": None})
                    spend = basis.estimate(tokens)
                else:
                    spend = ((observed["input_tokens"] - observed["cached_input_tokens"]) *
                             rates["input_microusd_per_token"] + observed["cached_input_tokens"] *
                             rates["cached_microusd_per_token"] + observed["output_tokens"] *
                             rates["output_microusd_per_token"])
                count(spend)
                raw_ref = self._save(capture, reserve.operation_id)
                event_id = "wire-" + hashlib.sha256(reserve.operation_id.encode()).hexdigest()
                receipt = BudgetLedger.model_validate(reserve.model_dump() | {
                    "posting": "settle", "source_event_id": event_id + ":settle",
                    "ledger_id": event_id + ":receipt",
                    "metering": "estimated" if basis else "reported",
                    "raw_usage_ref": raw_ref, "usage": reserve.usage.model_dump() | observed |
                    {"spend_microusd": spend, "wall_ms": int((time.monotonic() - started) * 1000)}})
                if basis:
                    valuation = UsageValuation.model_validate({"schema": "strata/UsageValuation/1",
                        "kind": "api_equivalent_estimate", "basis_digest": basis.fingerprint(),
                        "raw_usage_ref": raw_ref, "usage": tokens, "amount_microusd": spend,
                        "token_evidence": "synthetic_fixture"})
                    return event, receipt, valuation
                return event, receipt
            finally:
                connection.close()
                if capture is not None and raw_ref is None:
                    # Retain even malformed/partial usage; no zero-cost settlement.
                    self._save(capture, reserve.operation_id)

        return self.gate.execute(account, attempt, reserve, forward)

    def _save(self, capture, operation):
        ref = self.gate.cas.put(Principal(self.gate.namespace, "operator"), self.gate.namespace,
                                "operator", bytes(capture.raw), media_type=capture.content_type)
        with self.gate.db.transaction() as db:
            self.gate.db.event(db, "inference.wire_capture", {"operation_id": operation,
                "raw_usage_ref": ref,
                "bytes": len(capture.raw), "simulation": True})
        return ref
