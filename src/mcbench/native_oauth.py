"""Native-owned OAuth headers with fixed-destination, single-request forwarding.

No login, refresh-token parser, account switch or alternate provider is supplied.
The trusted native runtime owns authentication. A live adapter requires private
qualification of this exact profile; a synthetic adapter accepts fixture tokens
only. Neither a header nor a source test qualifies the entire runtime boundary.
"""

import hashlib
import http.client
import re
import ssl
import time
from urllib.parse import urlsplit

from .inference_transport import (
    BUFFERED_SSE_POLICY,
    MAX_REQUEST_TIMEOUT_S,
    _ResponsesTransport,
    strict_json,
)
from .native_ingress import NativeIngress, active_binding
from .storage import require

POLICY = "native-chatgpt-fixed-https-responses/2"
HOST = "chatgpt.com"
PATHS = {"/v1/responses": "/backend-api/codex/responses",
         "/v1/responses/compact": "/backend-api/codex/responses/compact"}
CHECKS = {"native_oauth_wire", "credential_containment", "fixed_upstream_tls",
          "all_request_reservations", "usage_receipts", "no_redirect_or_replay"}
NATIVE_HEADERS = frozenset({"originator", "session-id", "thread-id", "user-agent",
    "x-client-request-id", "x-codex-beta-features", "x-codex-parent-thread-id",
    "x-codex-turn-metadata", "x-codex-window-id", "x-openai-internal-codex-responses-lite",
    "x-openai-subagent"})
TRANSPORT_HEADERS = frozenset({"authorization", "chatgpt-account-id", "x-strata-ingress",
    "host", "content-length", "content-type", "accept", "accept-encoding"})


class NativeOAuthRequest:
    """Short-lived private header capability. Never serialize or log this object."""

    def __init__(self, ingress, job, operation, request_digest, headers, path):
        require(isinstance(ingress, NativeIngress), "OAUTH_INGRESS_REQUIRED")
        profile = ingress.authenticate(job, headers, path)
        plan, binding = active_binding(ingress.db.connection, job, now=ingress.clock())
        require(binding["native_oauth"] and plan.auth_mode == "chatgpt_oauth", "OAUTH_MODE_REQUIRED")
        accounts = headers.get_all("ChatGPT-Account-ID", [])
        require(len(accounts) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", accounts[0]),
                "OAUTH_ACCOUNT_REQUIRED")
        token = headers.get_all("Authorization", [])[0][7:]
        require(token.isascii() and all(33 <= ord(c) <= 126 for c in token), "OAUTH_TOKEN_FORMAT")
        require(set(k.lower() for k in headers.keys()) <= NATIVE_HEADERS | TRANSPORT_HEADERS,
                "OAUTH_HEADER_UNSUPPORTED")
        content_types = headers.get_all("Content-Type", ["application/json"])
        accepts = headers.get_all("Accept", ["*/*"])
        require(len(content_types) == 1 and content_types[0].lower() in {
            "application/json", "application/json; charset=utf-8"}, "OAUTH_CONTENT_TYPE")
        require(len(accepts) == 1 and 0 < len(accepts[0]) <= 8192 and accepts[0].isascii() and
                all(32 <= ord(c) <= 126 for c in accepts[0]) and token not in accepts[0],
                "OAUTH_ACCEPT_HEADER")
        native_headers = {}
        for key in sorted(NATIVE_HEADERS):
            values = headers.get_all(key, [])
            require(len(values) <= 1, "OAUTH_HEADER_DUPLICATE")
            if values:
                require(0 < len(values[0]) <= 8192 and values[0].isascii() and
                        all(32 <= ord(c) <= 126 for c in values[0]), "OAUTH_HEADER_INVALID")
                # Auth must never enter ordinary diagnostics/protocol metadata.
                require(token not in values[0], "OAUTH_HEADER_INVALID")
                native_headers[key] = values[0]
        require(sum(map(len, native_headers.values())) <= 32768, "OAUTH_HEADER_SIZE")
        ingress.bind_request(job, operation, request_digest, headers, path)
        self.job, self.operation, self.profile = job, operation, profile
        self.request_digest, self.path = request_digest, path
        self.account_digest = hashlib.sha256(accounts[0].encode()).hexdigest()
        self._token, self._account = token, accounts[0]
        self._native_headers = native_headers
        self._accept, self._content_type = accepts[0], content_types[0]
        self._closed = False

    def __repr__(self):
        return "<NativeOAuthRequest redacted>"

    def close(self):
        # Python strings cannot promise zeroization; drop references promptly.
        self._token = self._account = ""
        self._native_headers = {}
        self._closed = True

    def headers(self):
        require(not self._closed, "OAUTH_CREDENTIAL_CLOSED")
        return {"Authorization": "Bearer " + self._token, "ChatGPT-Account-ID": self._account,
                "Content-Type": self._content_type, "Accept": self._accept, **self._native_headers}


class _SecretFilter:
    """Withhold a suffix so split credential reflections never reach output/CAS."""

    def __init__(self, values):
        self.values = tuple(v.encode("ascii") for v in values if v)
        self.keep = max(map(len, self.values), default=1) - 1
        self.pending = b""

    def feed(self, chunk, *, final=False):
        data = self.pending + chunk
        require(not any(value in data for value in self.values), "OAUTH_CREDENTIAL_REFLECTION")
        length = len(data) if final else max(0, len(data) - self.keep)
        result, self.pending = data[:length], data[length:]
        return result


class NativeOAuthTransport(_ResponsesTransport):
    """Production HTTPS adapter, closed until private exact-profile evidence exists."""

    buffered_sse_policy = BUFFERED_SSE_POLICY

    def __init__(self, dispatches, credentials, qualification_ref, *, deadline_s=30):
        require(not dispatches.simulation, "OAUTH_LIVE_STORE_REQUIRED")
        self._init(dispatches, credentials, deadline_s)
        self.qualification_ref = qualification_ref

    def _init(self, dispatches, credentials, deadline_s):
        require(isinstance(credentials, NativeOAuthRequest) and not credentials._closed,
                "OAUTH_CREDENTIAL_REQUIRED")
        require(type(deadline_s) in {int, float} and 0 < deadline_s <= MAX_REQUEST_TIMEOUT_S,
                "TRANSPORT_DEADLINE")
        require(credentials.path in PATHS, "INGRESS_ROUTE")
        self.gate, self.credentials, self.deadline_s = dispatches, credentials, deadline_s
        self._init_lifetime()

    def _preflight(self, attempt, reserve):
        c = self.credentials
        require(not c._closed and attempt.runtime_job_id == c.job and
                attempt.profile_digest == c.profile and reserve.operation_id == c.operation and
                attempt.request_digest == c.request_digest and attempt.auth_mode == "chatgpt_oauth",
                "OAUTH_REQUEST_SCOPE")
        # Revalidation happens again in the durable dispatch transaction.
        plan, binding = active_binding(self.gate.db.connection, c.job, now=time.time())
        require(plan.profile_digest() == c.profile and binding["native_oauth"], "OAUTH_REQUEST_SCOPE")
        self._qualify(attempt, reserve)
        self.filter = _SecretFilter((c._token, c._account))

    def _qualify(self, attempt, reserve):
        require(attempt.provider == "openai" and reserve.model_identity in {"gpt-5.6-luna", "gpt-6-luna"},
                "OAUTH_PROVIDER_SCOPE")
        proof = strict_json(self.gate._private_ref(self.qualification_ref, 65536))
        if proof.get("schema") == "strata/NativePilotPermit/1":
            from .native_piloting import require_permit_for_request
            require_permit_for_request(self.gate, proof, self.credentials, attempt, reserve)
            return
        if proof.get("schema") == "strata/NativeOAuthConformancePermit/1":
            from .native_conformance import require_permit_for_request
            require_permit_for_request(self.gate, proof, self.credentials, attempt, reserve)
            return
        require(proof.get("schema") == "strata/NativeOAuthTransportQualification/1" and
                proof.get("is_example") is False and proof.get("policy") == POLICY and
                proof.get("profile_digest") == attempt.profile_digest and
                proof.get("account_digest") == self.credentials.account_digest and
                proof.get("host") == HOST and proof.get("paths") == PATHS and
                proof.get("native_headers") == sorted(NATIVE_HEADERS) and
                type(proof.get("expires_unix")) in {int, float} and
                time.time() < proof["expires_unix"] <= time.time() + 3600 and
                isinstance(proof.get("checks"), dict) and set(proof["checks"]) == CHECKS,
                "OAUTH_TRANSPORT_UNQUALIFIED")
        for check, ref in proof["checks"].items():
            item = strict_json(self.gate._private_ref(ref, 65536))
            require(item.get("is_example") is False and item.get("check") == check and
                    item.get("result") == "pass" and item.get("policy") == POLICY and
                    item.get("profile_digest") == attempt.profile_digest and
                    item.get("account_digest") == self.credentials.account_digest,
                    "OAUTH_TRANSPORT_UNQUALIFIED")

    def _request(self):
        return (http.client.HTTPSConnection(HOST, 443, timeout=self.deadline_s,
                                            context=ssl.create_default_context()),
                PATHS[self.credentials.path], self.credentials.headers())

    def _filter(self, chunk, *, final=False):
        return self.filter.feed(chunk, final=final)

    def execute(self, *args, **kwargs):
        try:
            return super().execute(*args, **kwargs)
        finally:
            self.credentials.close()
            if hasattr(self, "filter"):
                self.filter.pending = b""
                self.filter.values = ()


class SyntheticOAuthTransport(NativeOAuthTransport):
    """Owned loopback fixture only, incapable of accepting a real OAuth token."""

    def __init__(self, dispatches, credentials, endpoint, *, deadline_s=3):
        require(dispatches.simulation, "SYNTHETIC_STORE_REQUIRED")
        self._init(dispatches, credentials, deadline_s)
        require(re.fullmatch(r"STRATA_SYNTHETIC_OAUTH_[A-Za-z0-9_-]{1,128}", credentials._token)
                and credentials._account == "strata-fixture-account", "SYNTHETIC_CREDENTIAL_REQUIRED")
        require(re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}/v1/responses(?:/compact)?", endpoint),
                "SYNTHETIC_ENDPOINT_REQUIRED")
        self.url = urlsplit(endpoint)
        require(0 < self.url.port <= 65535 and self.url.path == credentials.path,
                "SYNTHETIC_ENDPOINT_REQUIRED")

    def _qualify(self, attempt, reserve):
        require(self.gate.simulation and attempt.auth_mode == "chatgpt_oauth", "SYNTHETIC_STORE_REQUIRED")
        require(re.fullmatch(r"STRATA_SYNTHETIC_OAUTH_[A-Za-z0-9_-]{1,128}", self.credentials._token)
                and self.credentials._account == "strata-fixture-account", "SYNTHETIC_CREDENTIAL_REQUIRED")

    def _request(self):
        return (http.client.HTTPConnection("127.0.0.1", self.url.port, timeout=self.deadline_s),
                self.url.path, self.credentials.headers())
