"""Private, transaction-aware Forge settings transport; never a gameplay capability.

Connection files contain bearer credentials and belong in operator broker storage.
One POST is sent per request. Uncertain responses require status/recovery, not replay.
"""

import argparse
import http.client
import json
import re
import time
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator

from .client_discovery import bounded_read, unique_fields
from .contracts import Digest, Id, Positive, Strict
from .storage import Fault, canonical, require

MAX_REQUEST = 32768
MAX_RESPONSE = 524288
PHASES = Literal["prepared", "applied_pending_verification", "rollback_prepared",
                 "rolled_back", "rollback_conflict"]


class Connection(Strict):
    wire_schema: Literal["strata/NativeSettingsConnection/1"] = Field(alias="schema")
    host: Literal["127.0.0.1"]
    port: int = Field(ge=1, le=65535)
    session_id: Id
    bearer_token: SecretStr
    fingerprint: Digest
    operator_development_only: Literal[True]

    @model_validator(mode="after")
    def credential(self):
        require(bool(re.fullmatch(r"[0-9a-f]{64}", self.bearer_token.get_secret_value())),
                "SETTINGS_CONNECTION_INVALID")
        return self


class NativeBinding(Strict):
    translation: str = Field(min_length=1, max_length=256)
    runtime_value: str = Field(min_length=1, max_length=256)
    persisted_value: str | None = Field(max_length=256)
    persisted_ambiguous: bool
    operator_mutable: bool

    @model_validator(mode="after")
    def persistence(self):
        require(not self.persisted_ambiguous or self.persisted_value is None,
                "SETTINGS_RESPONSE_INVALID")
        return self


class NativeSnapshot(Strict):
    fingerprint: Digest
    revision: Positive
    digest: Digest
    active_transaction: Id | None
    active_phase: PHASES | None
    options_sha256: Digest
    bindings: dict[Id, NativeBinding] = Field(min_length=1, max_length=2048)
    supported: Literal[False]
    operator_development_only: Literal[True]

    @model_validator(mode="after")
    def state(self):
        require((self.active_transaction is None) == (self.active_phase is None),
                "SETTINGS_RESPONSE_INVALID")
        require(self.active_phase != "rolled_back", "SETTINGS_RESPONSE_INVALID")
        return self


class NativeReceipt(Strict):
    transaction_id: Id
    phase: PHASES
    revision: Positive
    committed: Literal[False]


class NativeChange(Strict):
    before: str = Field(min_length=1, max_length=256)
    after: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def changed(self):
        require(self.before != self.after, "SETTINGS_PATCH_INVALID")
        return self


class NativePatch(Strict):
    transaction_id: Id
    expected_revision: Positive
    expected_digest: Digest
    changes: dict[Id, NativeChange] = Field(min_length=1, max_length=32)


class Response(Strict):
    wire_schema: Literal["strata/NativeSettingsResponse/1"] = Field(alias="schema")
    request_id: Id
    session_id: Id
    status: Literal["accepted", "completed", "failed"]
    result: dict | None
    error_code: str | None = Field(pattern=r"^[A-Z][A-Z0-9_]{1,95}$")

    @model_validator(mode="after")
    def result_shape(self):
        require((self.result is not None) == (self.status == "completed")
                and (self.error_code is not None) == (self.status == "failed"),
                "SETTINGS_RESPONSE_INVALID")
        return self


class OutcomeUnknown(Fault):
    def __init__(self, request_id: str, operation: str, transaction_id: str | None):
        super().__init__("SETTINGS_OUTCOME_UNKNOWN")
        self.request_id, self.operation, self.transaction_id = request_id, operation, transaction_id


def strict_json(raw: bytes):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(Fault("SETTINGS_JSON_INVALID")))


class NativeSettingsClient:
    """Operator bridge client. The native instance currently advertises supported=False."""

    response_type = Response

    def __init__(self, connection: Connection):
        self.connection = connection

    @classmethod
    def from_file(cls, path: Path):
        try:
            return cls(Connection.model_validate(strict_json(bounded_read(path, 4096))))
        except (OSError, ValueError):
            # ValidationError can embed the input bearer token, including unknown
            # fields. Sanitize at the library boundary as well as the CLI boundary.
            raise Fault("SETTINGS_CONNECTION_INVALID") from None

    def _exchange(self, method: str, path: str, body: bytes | None, timeout: float):
        connection = http.client.HTTPConnection("127.0.0.1", self.connection.port,
                                                 timeout=min(timeout, 3.0))
        try:
            connection.request(method, path, body=body, headers={
                "Authorization": "Bearer " + self.connection.bearer_token.get_secret_value(),
                "Content-Type": "application/json", "Connection": "close",
            })
            response = connection.getresponse()
            require(response.getheader("Content-Type") == "application/json", "SETTINGS_RESPONSE_INVALID")
            raw = response.read(MAX_RESPONSE + 1)
            require(len(raw) <= MAX_RESPONSE, "SETTINGS_RESPONSE_TOO_LARGE")
            length = response.getheader("Content-Length")
            require(length is not None and length.isdecimal() and int(length) == len(raw),
                    "SETTINGS_RESPONSE_INVALID")
            value = strict_json(raw)
            if response.status not in {200, 202}:
                require(isinstance(value, dict) and set(value) == {"error_code"}
                        and isinstance(value["error_code"], str)
                        and re.fullmatch(r"[A-Z][A-Z0-9_]{1,95}", value["error_code"]),
                        "SETTINGS_RESPONSE_INVALID")
                raise Fault(value["error_code"])
            result = self.response_type.model_validate(value)
            require((response.status == 202) == (result.status == "accepted"), "SETTINGS_RESPONSE_INVALID")
            return result
        finally:
            connection.close()

    def call(self, operation: str, args: dict, *, timeout_ms: int = 5000) -> dict:
        require(type(timeout_ms) is int and 100 <= timeout_ms <= 30000, "SETTINGS_DEADLINE_INVALID")
        require(operation in {"snapshot", "apply", "status", "rollback", "stop_all"},
                "SETTINGS_OPERATION_UNSUPPORTED")
        # Validate before any network request, including strict unknown fields/types.
        if operation == "apply":
            args = NativePatch.model_validate(args).model_dump(mode="json")
        elif operation in {"status", "rollback"}:
            require(set(args) == {"transaction_id"} and isinstance(args["transaction_id"], str)
                    and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", args["transaction_id"]), "SETTINGS_ID_INVALID")
        else:
            require(args == {}, "SETTINGS_ARGUMENTS_INVALID")
        request_id = str(uuid.uuid4())
        request = {"schema": "strata/NativeSettingsRequest/1", "request_id": request_id,
                   "session_id": self.connection.session_id,
                   "deadline_unix_ms": int(time.time() * 1000) + timeout_ms,
                   "operation": operation, "args": args}
        body = canonical(request)
        require(len(body) <= MAX_REQUEST, "SETTINGS_REQUEST_TOO_LARGE")
        expires = time.monotonic() + timeout_ms / 1000
        try:
            response = self._exchange("POST", "/v1/settings", body, timeout_ms / 1000)
            while True:
                require(response.request_id == request_id
                        and response.session_id == self.connection.session_id,
                        "SETTINGS_RESPONSE_IDENTITY_MISMATCH")
                if response.status == "failed":
                    raise Fault(response.error_code)
                if response.status == "completed":
                    return self._result(operation, args, response.result)
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                time.sleep(min(0.05, remaining))
                remaining = expires - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                response = self._exchange("GET", "/v1/settings/" + request_id, None, remaining)
        except (OSError, http.client.HTTPException, ValueError) as error:
            # Server failures can leave a durable prepared transaction. They are
            # not permission to repeat a write; query status with the same tx ID.
            if isinstance(error, Fault) and error.code not in {
                    "SETTINGS_RESPONSE_INVALID", "SETTINGS_RESPONSE_TOO_LARGE",
                    "SETTINGS_RESPONSE_IDENTITY_MISMATCH", "DUPLICATE_JSON_FIELD",
                    "SETTINGS_JSON_INVALID", "SETTINGS_REQUEST_UNKNOWN"}:
                raise
            raise OutcomeUnknown(request_id, operation, args.get("transaction_id")) from None

    def _result(self, operation, args, value):
        if operation == "snapshot":
            snapshot = NativeSnapshot.model_validate(value)
            require(snapshot.fingerprint == self.connection.fingerprint, "SETTINGS_RESPONSE_IDENTITY_MISMATCH")
            return snapshot.model_dump(mode="json")
        if operation in {"apply", "rollback", "status"}:
            receipt = NativeReceipt.model_validate(value)
            require(receipt.transaction_id == args["transaction_id"], "SETTINGS_RESPONSE_IDENTITY_MISMATCH")
            if operation == "rollback":
                require(receipt.phase == "rolled_back", "SETTINGS_RESPONSE_INVALID")
            return receipt.model_dump(mode="json")
        require(value == {"native_inputs_released": True}
                and value["native_inputs_released"] is True, "SETTINGS_RESPONSE_INVALID")
        return value

    def snapshot(self):
        return self.call("snapshot", {})

    def apply(self, patch: NativePatch):
        return self.call("apply", patch.model_dump(mode="json"))

    def status(self, transaction_id: str):
        return self.call("status", {"transaction_id": transaction_id})

    def rollback(self, transaction_id: str):
        return self.call("rollback", {"transaction_id": transaction_id})

    def stop_all(self):
        return self.call("stop_all", {})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", type=Path, required=True)
    parser.add_argument("operation", choices=["snapshot", "apply", "status", "rollback", "stop_all"])
    parser.add_argument("--transaction-id")
    parser.add_argument("--patch", type=Path)
    args = parser.parse_args(argv)
    try:
        client = NativeSettingsClient.from_file(args.connection)
        arguments = {}
        if args.operation == "apply":
            require(args.patch is not None and args.transaction_id is None, "SETTINGS_ARGUMENTS_INVALID")
            arguments = strict_json(bounded_read(args.patch, MAX_REQUEST))
        elif args.operation in {"status", "rollback"}:
            require(args.patch is None, "SETTINGS_ARGUMENTS_INVALID")
            arguments = {"transaction_id": args.transaction_id}
        else:
            require(args.patch is None and args.transaction_id is None, "SETTINGS_ARGUMENTS_INVALID")
        print(json.dumps({"status": "completed", "result": client.call(args.operation, arguments)}))
    except (ValueError, OSError, http.client.HTTPException) as error:
        # Pydantic exceptions may contain a secret connection value. Never print them.
        print(json.dumps({"status": "failed", "error_code": error.code if isinstance(error, Fault)
                          else "SETTINGS_OPERATOR_REQUEST_INVALID"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
