"""Private client prerequisites, not authentication or permission to replay a run."""

import hashlib
from pathlib import Path
import time
from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Positive, Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, IntegrityError
from mcbench.storage import Fault, digest, require

from .craft_reference import PrivateFile, check_file, private_path
from .telemetry_auth import private_read


class SessionPreparationReceipt(Strict):
    status: Literal["prepared"]
    credentials_printed: Literal[False]
    minimum_lifetime_ms: Positive
    expires_unix_ms: Positive
    argfile_sha256: Digest


class ClientPreparation(Strict):
    schema_: Literal["strata/PrivateReferenceClientPreparation/1"] = Field(alias="schema")
    client_binding_digest: Digest
    client_driver_sha256: Digest
    prepared_unix_ms: Positive
    session_receipt: PrivateFile
    session_arguments: PrivateFile


def read_private_preparation(path, limit):
    try:
        path = private_path(path)
        require(path.is_file(), "REFERENCE_CLIENT_PREPARATION_MISSING")
        return private_read(path, limit)
    except OSError:
        raise Fault("REFERENCE_CLIENT_PREPARATION_MISSING") from None


def read_preparation(pin):
    require(pin.bytes <= 8192, "REFERENCE_CLIENT_PREPARATION_QUOTA")
    raw = read_private_preparation(pin.path, 8192)
    require(len(raw) == pin.bytes and hashlib.sha256(raw).hexdigest() == pin.sha256,
            "REFERENCE_CLIENT_PREPARATION_CHANGED")
    try:
        preparation = ClientPreparation.model_validate(strict_json(raw))
    except ValueError:
        raise Fault("REFERENCE_CLIENT_PREPARATION_INVALID") from None
    require(preparation.session_receipt.bytes <= 8192 and preparation.session_arguments.bytes <= 65536,
            "REFERENCE_CLIENT_PREPARATION_QUOTA")
    for item in (preparation.session_receipt, preparation.session_arguments):
        private_path(item.path)
    return preparation


def validate_preparation(preparation, binding_digest, driver_digest, required_ms):
    """Recheck before server/client dispatch; never read credentials into a report.

    The argument lease lasts only for verification. The driver must independently
    recheck before launch and retire its credential file afterward. This does not
    attest sign-in validity or isolate another process with equivalent access.
    """
    require(type(required_ms) is int and 0 < required_ms <= 1_200_000,
            "REFERENCE_CLIENT_PREPARATION_EXPOSURE")
    require(preparation.client_binding_digest == binding_digest
            and preparation.client_driver_sha256 == driver_digest,
            "REFERENCE_CLIENT_PREPARATION_BINDING")
    now = time.time_ns() // 1_000_000
    require(0 <= now - preparation.prepared_unix_ms <= 1_800_000,
            "REFERENCE_CLIENT_PREPARATION_AGE")
    receipt_pin = preparation.session_receipt
    raw = read_private_preparation(receipt_pin.path, 8192)
    require(len(raw) == receipt_pin.bytes and hashlib.sha256(raw).hexdigest() == receipt_pin.sha256,
            "REFERENCE_CLIENT_PREPARATION_CHANGED")
    # The existing Node operator helper writes UTF-8; a BOM from a shell wrapper
    # is allowed only at the start, never by permissive JSON token conversion.
    try:
        value = strict_json(raw.decode("utf-8-sig"))
        require(isinstance(value, dict) and value.get("credentials_printed") is False,
                "REFERENCE_CLIENT_PREPARATION_INVALID")
        receipt = SessionPreparationReceipt.model_validate(value)
    except ValueError:
        raise Fault("REFERENCE_CLIENT_PREPARATION_INVALID") from None
    require(receipt.argfile_sha256 == preparation.session_arguments.sha256,
            "REFERENCE_CLIENT_PREPARATION_BINDING")
    require(receipt.minimum_lifetime_ms >= required_ms
            and receipt.expires_unix_ms - now >= required_ms,
            "REFERENCE_CLIENT_PREPARATION_EXPIRED")
    arguments = preparation.session_arguments
    try:
        with FileLease({"schema": "strata/LaunchFileInventory/1", "trees": [],
                        "files": [arguments.model_dump()]}):
            check_file(Path(arguments.path), arguments)
    except IntegrityError as error:
        code = ("REFERENCE_CLIENT_ARGUMENTS_CHANGED" if error.args == ("BOOTSTRAP_FILE_CHANGED",)
                else "REFERENCE_CLIENT_ARGUMENTS_UNAVAILABLE")
        raise Fault(code) from None
    return {"preparation_digest": digest(preparation.model_dump(by_alias=True)),
            "checked_unix_ms": now, "required_ms": required_ms,
            "prepared_bytes_verified": True, "authentication_verified": False}
