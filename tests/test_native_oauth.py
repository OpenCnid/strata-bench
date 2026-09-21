"""Owned HTTP/fabricated-token qualification cases, never real OAuth inference."""

import json
import ssl
import time
from types import SimpleNamespace

import pytest
import test_inference_transport
import test_native_ingress

from mcbench.native_oauth import NativeOAuthRequest, NativeOAuthTransport, SyntheticOAuthTransport
from mcbench.storage import Fault, Principal, digest

admitted = test_native_ingress.admitted
ingress = test_native_ingress.ingress
provider = test_inference_transport.provider


@pytest.fixture
def oauth(admitted, ingress):
    _, gate, _, plan, request, prepare, put = admitted
    service, headers = ingress
    plan.config_overrides["model_providers.ingress.requires_openai_auth"] = True
    gate.db.connection.execute("DELETE FROM native_ingress")
    gate.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    service.register(plan)
    headers["Authorization"] = "Bearer STRATA_SYNTHETIC_OAUTH_ACCESS"
    headers["ChatGPT-Account-ID"] = "strata-fixture-account"
    value = list(request("one"))
    price = put({"schema": "strata/SyntheticTokenPricing/1", "is_example": True, "currency": "USD",
                 "input_microusd_per_token": 1, "cached_microusd_per_token": 1,
                 "output_microusd_per_token": 1})
    value[1] = value[1].model_copy(update={"pricing_ref": price})
    bound = gate._bound(value[0]).model_copy(update={"pricing_ref": price,
                                               "reservation_digest": digest(value[1].model_dump())})
    value[0] = value[0].model_copy(update={"bound_ref": put(bound.model_dump())})
    def credential():
        return NativeOAuthRequest(service, "job", "one", value[0].request_digest, headers, "/v1/responses")
    c = credential()
    prepare(value)
    return gate, value, c, credential, headers


def wire(**updates):
    return test_inference_transport.stream(test_inference_transport.response(model="gpt-5.6-luna", **updates))


@pytest.mark.parametrize("case", ["valid", "truncated", "missing", "wrong_model", "html", "error_status"])
def test_native_unknown_media_is_withheld_until_complete_receipt(oauth, provider, case):
    gate, (attempt, reserve, raw, _), c, _, _ = oauth
    data = wire()
    if case == "truncated":
        data = data[:-1]
    elif case == "missing":
        data = wire(usage=None)
    elif case == "wrong_model":
        data = test_inference_transport.stream(test_inference_transport.response(model="other"))
    elif case == "html":
        data = b"<html>upstream error</html>\n"
    endpoint, requests = provider(data, media="application/octet-stream", status=503 if case == "error_status" else 200)
    delivered, headers = [], []
    t = SyntheticOAuthTransport(gate, c, endpoint)
    def execute():
        return t.execute("a1", attempt, reserve, raw, on_headers=lambda *v: headers.append(v),
                         on_chunk=delivered.append)
    if case == "valid":
        assert execute()["state"] == "SETTLED"
        assert headers == [(200, "text/event-stream")] and delivered == [data]
        assert gate.db.connection.execute("SELECT count(*) FROM outbox WHERE kind='inference.media_normalized'").fetchone()[0] == 1
    else:
        with pytest.raises(Fault):
            execute()
        assert headers == delivered == []
        assert gate.status("one")["state"] == "UNSETTLED"
    assert len(requests) == 1


def test_native_header_capture_fixed_forward_and_no_replay(oauth, provider):
    gate, (attempt, reserve, raw, _), c, credential, headers = oauth
    endpoint, requests = provider(wire())
    delivered = []
    for c in (c, credential()):
        t = SyntheticOAuthTransport(gate, c, endpoint)
        result = t.execute("a1", attempt, reserve, raw, on_headers=lambda *args: None,
                           on_chunk=delivered.append)
        assert result["state"] == "SETTLED" and c._closed
    assert requests == [{"body": raw, "authorization": "Bearer STRATA_SYNTHETIC_OAUTH_ACCESS"}]
    assert b"".join(delivered) == wire()
    assert gate.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 1000
    # The enclosing job remains reserved; this call's actual receipt is fourteen.
    receipt = json.loads(gate.db.connection.execute("SELECT actual FROM operations WHERE id='one'").fetchone()[0])
    assert receipt["spend_microusd"] == 14
    assert "STRATA_SYNTHETIC_OAUTH_ACCESS" not in repr(c)
    outbox = json.dumps([dict(r) for r in gate.db.connection.execute("SELECT * FROM outbox")])
    assert headers["Authorization"] not in outbox


@pytest.mark.parametrize("mode", ["redirect", "missing", "truncated", "reflection", "timeout"])
def test_fault_retains_reservation_and_never_retries(oauth, provider, mode):
    gate, (attempt, reserve, raw, _), c, _, _ = oauth
    data = wire(usage=None) if mode == "missing" else wire()
    if mode == "truncated":
        data = data[:-1]
    if mode == "reflection":
        data = b'data: {"type":"response.output_text.delta","delta":"STRATA_SYNTHETIC_OAUTH_ACCESS"}\n\n'
    endpoint, requests = provider(data, status=302 if mode == "redirect" else 200,
        redirect="https://example.invalid/forbidden" if mode == "redirect" else None,
        delay=.2 if mode == "timeout" else 0)
    t = SyntheticOAuthTransport(gate, c, endpoint, deadline_s=.05 if mode == "timeout" else 3)
    delivered = []
    with pytest.raises((Fault, TimeoutError)):
        t.execute("a1", attempt, reserve, raw, on_headers=lambda *args: None, on_chunk=delivered.append)
    assert gate.status("one")["state"] == "UNSETTLED" and c._closed
    assert len(requests) == 1
    assert b"STRATA_SYNTHETIC_OAUTH_ACCESS" not in b"".join(delivered)
    for path in gate.cas.root.rglob('*'):
        if path.is_file():
            assert b"STRATA_SYNTHETIC_OAUTH_ACCESS" not in path.read_bytes()
    assert gate.db.connection.execute("SELECT actual FROM operations WHERE id='one'").fetchone()[0] is None


def test_expansion_and_real_tokens_cannot_enter_fixture(oauth, provider):
    gate, _, c, _, _ = oauth
    endpoint, requests = provider(wire())
    for target in ("https://chatgpt.com/backend-api/codex/responses", endpoint + "?x=1",
                   endpoint.replace("127.0.0.1", "localhost")):
        with pytest.raises(Fault, match="SYNTHETIC_ENDPOINT_REQUIRED"):
            SyntheticOAuthTransport(gate, c, target)
    c._token = "not-a-fixture-token"
    with pytest.raises(Fault, match="SYNTHETIC_CREDENTIAL_REQUIRED"):
        SyntheticOAuthTransport(gate, c, endpoint)
    with pytest.raises(Fault, match="OAUTH_LIVE_STORE_REQUIRED"):
        NativeOAuthTransport(gate, c, None)
    assert not requests


def test_wrong_account_duplicate_headers_and_request_rebinding(oauth, ingress, provider):
    gate, value, c, credential, headers = oauth
    headers["ChatGPT-Account-ID"] = "other"
    with pytest.raises(Fault, match="OAUTH_ACCOUNT_REQUIRED"):
        credential()
    endpoint, requests = provider(wire())
    t = SyntheticOAuthTransport(gate, c, endpoint)
    with pytest.raises(Fault, match="OAUTH_REQUEST_SCOPE"):
        t.execute("a1", value[0].model_copy(update={"profile_digest": "f" * 64}), value[1], value[2],
                  on_headers=lambda *args: None, on_chunk=lambda *args: None)
    assert not requests and gate.db.connection.execute("SELECT count(*) FROM inference_attempts").fetchone()[0] == 0


def test_split_reflection_never_reaches_output():
    from mcbench.native_oauth import _SecretFilter
    guard = _SecretFilter(("private-token",))
    output = guard.feed(b"some safe prefix private-")
    with pytest.raises(Fault, match="OAUTH_CREDENTIAL_REFLECTION"):
        output += guard.feed(b"token remaining bytes")
    assert b"private" not in output


@pytest.mark.parametrize("media,body,code", [
    ("text/html", b"<html>Owned rejection fixture</html>", "RESPONSE_CONTENT_TYPE"),
    ("application/x-ndjson", wire(), "RESPONSE_CONTENT_TYPE"),
    ("secret-header-value", b"Unsupported media fixture", "RESPONSE_CONTENT_TYPE"),
    ("text/plain", b"STRATA_SYNTHETIC_OAUTH_ACCESS", "OAUTH_CREDENTIAL_REFLECTION"),
])
def test_rejected_wire_is_private_bounded_and_does_not_release_hold(oauth, provider, media, body, code):
    gate, (attempt, reserve, raw, _), credentials, fresh_credentials, _ = oauth
    endpoint, requests = provider(body, status=403, media=media)
    delivered, delivered_headers = [], []
    adapter = SyntheticOAuthTransport(gate, credentials, endpoint)
    with pytest.raises(Fault, match=code):
        adapter.execute("a1", attempt, reserve, raw,
            on_headers=lambda *args: delivered_headers.append(args), on_chunk=delivered.append)
    assert not delivered and not delivered_headers and credentials._closed
    assert len(requests) == 1 and gate.status("one")["state"] == "UNSETTLED"
    assert gate.db.connection.execute("SELECT actual FROM operations WHERE id='one'").fetchone()[0] is None
    events = [(r["kind"], json.loads(r["body"])) for r in gate.db.connection.execute("SELECT * FROM outbox")]
    response = [event for kind, event in events if kind == "inference.http_response"]
    assert response == [{"operation_id": "one", "status": 403,
        "media_class": media if media != "secret-header-value" else "other",
        "identity_encoding": True, "simulation": True}]
    capture = [event for kind, event in events if kind == "inference.wire_capture"]
    assert len(capture) == 1
    raw_capture = gate.cas.read(Principal("operator", "operator"), "operator", capture[0]["raw_usage_ref"])
    assert raw_capture == (b"" if code == "OAUTH_CREDENTIAL_REFLECTION" else body)
    assert "secret-header-value" not in json.dumps(events)
    for path in gate.cas.root.rglob("*"):
        if path.is_file():
            assert b"STRATA_SYNTHETIC_OAUTH_ACCESS" not in path.read_bytes()
    # Same durable operation cannot be forwarded again, even with a new adapter.
    previous = SyntheticOAuthTransport(gate, fresh_credentials(), endpoint).execute(
        "a1", attempt, reserve, raw, on_headers=lambda *args: None, on_chunk=delivered.append)
    assert previous["state"] == "UNSETTLED"
    assert len(requests) == 1


def test_live_transport_requires_exact_private_proof_before_any_connection(oauth, monkeypatch):
    from mcbench.native_oauth import CHECKS, HOST, NATIVE_HEADERS, PATHS, POLICY
    from mcbench.storage import canonical
    gate, (attempt, reserve, _, _), c, _, _ = oauth
    proof = {"schema": "strata/NativeOAuthTransportQualification/1", "is_example": False,
        "policy": POLICY, "profile_digest": attempt.profile_digest, "account_digest": c.account_digest,
        "host": HOST, "paths": PATHS, "native_headers": sorted(NATIVE_HEADERS),
        "expires_unix": time.time() + 60, "checks": {key: "evidence:" + key for key in CHECKS}}
    evidence = {ref: {"is_example": False, "check": key, "result": "pass", "policy": POLICY,
        "profile_digest": attempt.profile_digest, "account_digest": c.account_digest}
        for key, ref in proof["checks"].items()}
    # Isolated unit seam: no live accounting store, authority, socket or provider.
    reads = []
    def read(ref, limit):
        reads.append((ref, limit))
        return canonical(proof if ref == "private-proof" else evidence[ref])
    adapter = NativeOAuthTransport(SimpleNamespace(simulation=False, _private_ref=read), c, "private-proof")
    adapter._qualify(attempt, reserve)
    assert reads[0] == ("private-proof", 65536) and len(reads) == 1 + len(CHECKS)
    for key in ("is_example", "profile_digest", "account_digest", "host", "paths", "native_headers", "checks"):
        before = proof[key]
        proof[key] = True if key == "is_example" else "different"
        with pytest.raises(Fault, match="OAUTH_TRANSPORT_UNQUALIFIED"):
            adapter._qualify(attempt, reserve)
        proof[key] = before
    proof["expires_unix"] = time.time() - 1
    with pytest.raises(Fault, match="OAUTH_TRANSPORT_UNQUALIFIED"):
        adapter._qualify(attempt, reserve)
    proof["expires_unix"] = time.time() + 60
    evidence["evidence:usage_receipts"]["is_example"] = True
    with pytest.raises(Fault, match="OAUTH_TRANSPORT_UNQUALIFIED"):
        adapter._qualify(attempt, reserve)
    calls = []
    def connection(*args, **kwargs):
        calls.append((args, kwargs))
        return "no-socket-unit-sentinel"
    monkeypatch.setattr("mcbench.native_oauth.http.client.HTTPSConnection", connection)
    conn, path, headers = adapter._request()
    assert conn == "no-socket-unit-sentinel" and path == "/backend-api/codex/responses"
    assert calls[0][0] == ("chatgpt.com", 443)
    context = calls[0][1]["context"]
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    assert set(headers) == {"Authorization", "ChatGPT-Account-ID", "Content-Type", "Accept"}


@pytest.mark.parametrize("case", ["unknown", "duplicate", "control", "secret", "size"])
def test_protocol_headers_are_bounded_and_cannot_smuggle_authority(oauth, case):
    _, _, _, credential, headers = oauth
    headers["x-codex-beta-features"] = "fixture-beta"
    c = credential()
    assert c.headers()["x-codex-beta-features"] == "fixture-beta"
    assert "X-Strata-Ingress" not in c.headers()
    if case == "unknown":
        headers["x-unapproved"] = "extra"
    elif case == "duplicate":
        headers["x-codex-beta-features"] = "again"
    else:
        headers.replace_header("x-codex-beta-features", {
            "control": "bad\x00value", "secret": "STRATA_SYNTHETIC_OAUTH_ACCESS", "size": "a" * 8193}[case])
    with pytest.raises(Fault, match="OAUTH_HEADER_"):
        credential()


@pytest.mark.parametrize("case", ["duplicate", "type", "secret", "control"])
def test_native_media_negotiation_is_preserved_and_validated(oauth, case):
    _, _, _, credential, headers = oauth
    headers["Accept"] = "application/json, text/event-stream"
    headers["Content-Type"] = "application/json; charset=utf-8"
    assert credential().headers()["Accept"] == headers["Accept"]
    assert credential().headers()["Content-Type"] == headers["Content-Type"]
    if case == "duplicate":
        headers["Accept"] = "again"
    elif case == "type":
        headers.replace_header("Content-Type", "text/plain")
    else:
        headers.replace_header("Accept", "STRATA_SYNTHETIC_OAUTH_ACCESS" if case == "secret" else "bad\x00")
    with pytest.raises(Fault, match="OAUTH_ACCEPT_HEADER|OAUTH_CONTENT_TYPE"):
        credential()
