"""Private client prerequisites, not authentication or permission to replay a run."""

import hashlib
import json
from pathlib import Path
import time
from typing import Literal

from pydantic import Field, TypeAdapter

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


class ClientPreparationV2(ClientPreparation):
    schema_: Literal["strata/PrivateReferenceClientPreparation/2"] = Field(alias="schema")
    jvm_resource_policy: Literal["hotspot-active-processors4/1"]


class ClientPreparationV3(ClientPreparationV2):
    schema_: Literal["strata/PrivateReferenceClientPreparation/3"] = Field(alias="schema")
    jvm_resource_policy: Literal["hotspot-processors4-heap512-6144mib/1"]


def check_resource_arguments(raw, policy="hotspot-active-processors4/1"):
    """Verify the selected quoted argument-file form without reporting secrets.

    This checks a launch input, not OS CPU reservation or shutdown qualification.
    Legacy CPU4 keeps its template-pinned heap. The new candidate also requires
    one exact initial/maximum heap pair; neither policy proves OS reservation.
    """
    try:
        require(policy in {"hotspot-active-processors4/1", "hotspot-processors4-heap512-6144mib/1"},
                "REFERENCE_CLIENT_RESOURCE_POLICY")
        lines = raw.decode("utf-8").splitlines()
        require(0 < len(lines) <= 256, "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
        args = [json.loads(line) for line in lines]
        require(all(isinstance(value, str) and all(ord(c) >= 32 for c in value)
                    and line == '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
                    for line, value in zip(lines, args)), "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
        require(args.count("cpw.mods.bootstraplauncher.BootstrapLauncher") == 1,
                "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
        end, cursor, processor_args = args.index("cpw.mods.bootstraplauncher.BootstrapLauncher"), 0, []
        heap_args = []
        operands = {"-cp", "-classpath", "--class-path", "-p", "--module-path",
                    "--add-modules", "--add-opens", "--add-exports"}
        while cursor < end:
            arg = args[cursor]
            if arg in operands:
                require(cursor + 1 < end and args[cursor + 1], "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
                cursor += 2
                continue
            require(arg.startswith(("-Xms", "-Xmx", "-Xlog:", "-D", "-XX:HeapDumpPath=",
                                    "-XX:ActiveProcessorCount=")), "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
            if arg.startswith("-XX:ActiveProcessorCount="):
                processor_args.append(arg)
            if arg.startswith(("-Xms", "-Xmx")):
                heap_args.append(arg)
            cursor += 1
        require(processor_args == ["-XX:ActiveProcessorCount=4"], "REFERENCE_CLIENT_RESOURCE_ARGUMENTS")
        if policy == "hotspot-processors4-heap512-6144mib/1":
            require(sorted(heap_args) == ["-Xms512m", "-Xmx6144m"], "REFERENCE_CLIENT_HEAP_ARGUMENTS")
    except Fault:
        raise
    except (UnicodeError, ValueError, TypeError):
        raise Fault("REFERENCE_CLIENT_RESOURCE_ARGUMENTS") from None
    return {"policy": policy, "reported_processors_argument": 4,
            **({"initial_heap_mib": 512, "maximum_heap_mib": 6144}
               if policy == "hotspot-processors4-heap512-6144mib/1" else {}),
            "argument_bytes_verified": True, "os_reservation": False, "shutdown_qualified": False}


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
        preparation = TypeAdapter(ClientPreparation | ClientPreparationV2 | ClientPreparationV3).validate_python(strict_json(raw))
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
    resource = None
    try:
        with FileLease({"schema": "strata/LaunchFileInventory/1", "trees": [],
                        "files": [arguments.model_dump()]}):
            check_file(Path(arguments.path), arguments)
            if isinstance(preparation, ClientPreparationV2):
                resource = check_resource_arguments(read_private_preparation(arguments.path, 65536),
                                                    preparation.jvm_resource_policy)
    except IntegrityError as error:
        code = ("REFERENCE_CLIENT_ARGUMENTS_CHANGED" if error.args == ("BOOTSTRAP_FILE_CHANGED",)
                else "REFERENCE_CLIENT_ARGUMENTS_UNAVAILABLE")
        raise Fault(code) from None
    return {"preparation_digest": digest(preparation.model_dump(by_alias=True)),
            "checked_unix_ms": now, "required_ms": required_ms,
            "prepared_bytes_verified": True, "authentication_verified": False,
            **({"jvm_resource_input": resource} if resource is not None else {})}
