import json

import pytest
from pydantic import ValidationError

from mcbench.native_settings import (
    Connection, NativePatch, NativeSettingsClient, OutcomeUnknown, Response, main, strict_json,
)
from mcbench.storage import Fault

FINGERPRINT = "a" * 64
TOKEN = "b" * 64


def connection(**changes):
    return Connection.model_validate({"schema": "strata/NativeSettingsConnection/1",
        "host": "127.0.0.1", "port": 12345, "session_id": "session-1", "bearer_token": TOKEN,
        "fingerprint": FINGERPRINT, "operator_development_only": True} | changes)


def patch():
    return NativePatch(transaction_id="tx-1", expected_revision=2, expected_digest="c" * 64,
        changes={"fixture:key.mod.action:0": {"before": "key.keyboard.g", "after": "key.keyboard.f13"}})


def receipt(request, **changes):
    return Response.model_validate({"schema": "strata/NativeSettingsResponse/1",
        "request_id": request["request_id"], "session_id": "session-1", "status": "completed",
        "result": {"transaction_id": "tx-1", "phase": "applied_pending_verification",
                   "revision": 4, "committed": False}, "error_code": None} | changes)


def test_request_is_posted_once_then_only_read_polled(monkeypatch):
    client = NativeSettingsClient(connection())
    calls = []
    request = None

    def exchange(method, path, body, timeout):
        nonlocal request
        calls.append(method)
        if method == "POST":
            request = json.loads(body)
            assert request["args"]["transaction_id"] == "tx-1"
            assert "bearer_token" not in request
            return receipt(request, status="accepted", result=None)
        assert path.endswith(request["request_id"])
        return receipt(request)

    monkeypatch.setattr(client, "_exchange", exchange)
    result = client.apply(patch())
    assert result["phase"] == "applied_pending_verification" and result["committed"] is False
    assert calls == ["POST", "GET"]


@pytest.mark.parametrize("case", ["timeout", "session", "transaction", "committed", "unknown-field"])
def test_uncertain_or_forged_response_never_repeats_mutation(monkeypatch, case):
    client = NativeSettingsClient(connection())
    calls = []

    def exchange(method, path, body, timeout):
        calls.append(method)
        if case == "timeout":
            raise TimeoutError("private details must not escape")
        value = receipt(json.loads(body))
        if case == "session":
            value.session_id = "other-session"
        elif case == "transaction":
            value.result["transaction_id"] = "other-transaction"
        elif case == "committed":
            value.result["committed"] = True
        else:
            value.result["arbitrary"] = "untrusted"
        return value

    monkeypatch.setattr(client, "_exchange", exchange)
    with pytest.raises(OutcomeUnknown) as failure:
        client.apply(patch())
    assert failure.value.transaction_id == "tx-1"
    assert failure.value.operation == "apply"
    assert calls == ["POST"]
    assert "private" not in str(failure.value)


@pytest.mark.parametrize("changes", [{"host": "example.com"}, {"port": 0}, {"port": True},
    {"bearer_token": "short"}, {"fingerprint": "no-hash"}, {"unknown": True}])
def test_invalid_connection_cannot_select_remote_or_unbound_endpoint(changes):
    with pytest.raises((ValidationError, Fault)):
        connection(**changes)


def test_request_validation_and_unknown_operations_happen_before_network(monkeypatch):
    client = NativeSettingsClient(connection())
    monkeypatch.setattr(client, "_exchange", lambda *args: pytest.fail("must not send invalid request"))
    with pytest.raises(Fault, match="SETTINGS_OPERATION_UNSUPPORTED"):
        client.call("commit", {})
    with pytest.raises(Fault, match="SETTINGS_ID_INVALID"):
        client.status("../other")
    with pytest.raises(Fault, match="SETTINGS_DEADLINE_INVALID"):
        client.call("snapshot", {}, timeout_ms=True)
    with pytest.raises((ValidationError, Fault)):
        client.call("apply", patch().model_dump() | {"arbitrary": True})


def test_duplicate_and_nonfinite_json_is_rejected():
    for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{} {}']:
        with pytest.raises(ValueError):
            strict_json(raw)


def test_credentials_are_redacted_and_cli_does_not_print_validation_inputs(tmp_path, capsys):
    assert TOKEN not in str(connection())
    assert TOKEN not in connection().model_dump_json()
    secret_file = tmp_path / "connection.json"
    secret_file.write_text(json.dumps({"bearer_token": TOKEN, "unknown": TOKEN}))
    with pytest.raises(Fault) as failure:
        NativeSettingsClient.from_file(secret_file)
    assert TOKEN not in str(failure.value)
    assert main(["--connection", str(secret_file), "snapshot"]) == 1
    output = capsys.readouterr().out
    assert TOKEN not in output
    assert json.loads(output)["error_code"] == "SETTINGS_CONNECTION_INVALID"
