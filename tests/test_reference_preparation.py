"""Prepared-byte and finite-expiry admission; no real sign-in or game launch."""

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator import reference_preparation as module
from strata_evaluator.craft_reference import PrivateFile

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Selected Windows pair and native file leases")


def pin(path):
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(module.time, "time_ns", lambda: 2_000_000_000_000)
    args = tmp_path / "private-arguments.txt"
    args.write_bytes(b"synthetic-secret-never-in-report")
    receipt = tmp_path / "session-preparation.json"
    receipt.write_bytes(canonical({"status": "prepared", "credentials_printed": False,
        "minimum_lifetime_ms": 1200000, "expires_unix_ms": 3300000,
        "argfile_sha256": pin(args)["sha256"]}))
    proof = tmp_path / "preparation.json"
    proof.write_bytes(canonical({"schema": "strata/PrivateReferenceClientPreparation/1",
        "client_binding_digest": "a" * 64, "client_driver_sha256": "b" * 64,
        "prepared_unix_ms": 1999000, "session_receipt": pin(receipt), "session_arguments": pin(args)}))
    return module.read_preparation(PrivateFile.model_validate(pin(proof))), proof


def test_finite_prepared_bytes_are_verified_without_revealing_or_retaining_credentials(prepared):
    value, _ = prepared
    result = module.validate_preparation(value, "a" * 64, "b" * 64, 915000)
    assert result["prepared_bytes_verified"] and not result["authentication_verified"]
    assert "secret" not in json.dumps(result) and "arguments" not in json.dumps(result)
    Path(value.session_arguments.path).unlink()  # Verification must release its lease for retirement.


@pytest.mark.parametrize("change,code", [
    ("binding", "REFERENCE_CLIENT_PREPARATION_BINDING"),
    ("driver", "REFERENCE_CLIENT_PREPARATION_BINDING"),
    ("future", "REFERENCE_CLIENT_PREPARATION_AGE"),
    ("old", "REFERENCE_CLIENT_PREPARATION_AGE"),
    ("expired", "REFERENCE_CLIENT_PREPARATION_EXPIRED"),
    ("changed_receipt", "REFERENCE_CLIENT_PREPARATION_CHANGED"),
    ("changed_arguments", "REFERENCE_CLIENT_ARGUMENTS_CHANGED"),
    ("missing_arguments", "REFERENCE_CLIENT_ARGUMENTS_UNAVAILABLE"),
    ("exposure", "REFERENCE_CLIENT_PREPARATION_EXPOSURE")])
def test_bad_preparation_cannot_become_ready(prepared, monkeypatch, change, code):
    value, _ = prepared
    binding, driver, required = "a" * 64, "b" * 64, 915000
    if change == "binding":
        binding = "c" * 64
    elif change == "driver":
        driver = "c" * 64
    elif change == "future":
        value = value.model_copy(update={"prepared_unix_ms": 2000001})
    elif change == "old":
        value = value.model_copy(update={"prepared_unix_ms": 1})
    elif change == "expired":
        monkeypatch.setattr(module.time, "time_ns", lambda: 3_200_000_000_000)
    elif change == "changed_receipt":
        Path(value.session_receipt.path).write_bytes(b"{}")
    elif change == "changed_arguments":
        Path(value.session_arguments.path).write_bytes(b"changed")
    elif change == "missing_arguments":
        Path(value.session_arguments.path).unlink()
    elif change == "exposure":
        required = 1200001
    with pytest.raises((Fault, RuntimeError), match=code):
        module.validate_preparation(value, binding, driver, required)


@pytest.mark.parametrize("change", ["unknown", "credentials", "numeric_flag", "arg_digest", "short_bound"])
def test_resealed_invalid_receipt_is_not_accepted(prepared, change):
    value, _ = prepared
    path = Path(value.session_receipt.path)
    receipt = json.loads(path.read_bytes())
    if change == "unknown":
        receipt["token"] = "synthetic"
    elif change == "credentials":
        receipt["credentials_printed"] = True
    elif change == "numeric_flag":
        receipt["credentials_printed"] = 0
    elif change == "arg_digest":
        receipt["argfile_sha256"] = "c" * 64
    else:
        receipt["minimum_lifetime_ms"] = 1000
    path.write_bytes(canonical(receipt))
    value = value.model_copy(update={"session_receipt": PrivateFile.model_validate(pin(path))})
    with pytest.raises((Fault, ValueError)):
        module.validate_preparation(value, "a" * 64, "b" * 64, 915000)


def test_missing_or_changed_preparation_rejects_before_dispatch(prepared):
    _, path = prepared
    expected = PrivateFile.model_validate(pin(path))
    path.write_bytes(b"{}")
    with pytest.raises(Fault, match="REFERENCE_CLIENT_PREPARATION_CHANGED"):
        module.read_preparation(expected)
    path.unlink()
    with pytest.raises(Fault, match="REFERENCE_CLIENT_PREPARATION_MISSING"):
        module.read_preparation(expected)


def test_legacy_production_pair_cannot_create_an_intent_or_spawn(monkeypatch):
    from strata_evaluator import reference_pair as pair
    plan = pair.ReferencePairPlanV2.model_construct(launch_file=None)
    monkeypatch.setattr(pair, "parse_pair_plan", lambda _: plan)
    monkeypatch.setattr(pair, "read_pinned", lambda *args: {})
    monkeypatch.setattr(pair, "parse_launch_plan", lambda _: SimpleNamespace(mode="e9e-serverstarter"))
    runner = pair.ReferencePair.__new__(pair.ReferencePair)
    # No database/store is provided: this denial must precede all durable intent and processes.
    with pytest.raises(Fault, match="REFERENCE_CLIENT_PREPARATION_REQUIRED"):
        runner.run({})


def argument_file(args):
    return '\n'.join('"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"' for value in args).encode()


@pytest.mark.parametrize("change", [None, "missing", "duplicate", "different", "after_main", "nested", "flags", "options", "escape", "jar", "other_main", "operand"])
def test_resource_policy_checks_effective_jvm_argument_position_without_disclosing_tokens(change):
    flag, main = "-XX:ActiveProcessorCount=4", "cpw.mods.bootstraplauncher.BootstrapLauncher"
    args = ["-Xms512m", "-Xmx3072m", flag, "-cp", r"C:\fixture\bootstrap.jar", main,
            "--accessToken", "synthetic-private-value"]
    if change == "missing":
        args.remove(flag)
    elif change == "duplicate":
        args.insert(0, flag)
    elif change == "different":
        args[2] = "-XX:ActiveProcessorCount=16"
    elif change == "after_main":
        args.remove(flag)
        args.append(flag)
    elif change == "jar":
        args[:0] = ["-jar", "other.jar"]
    elif change == "other_main":
        args.insert(0, "other.Main")
    elif change == "operand":
        args.insert(2, "-cp")
    elif change in {"nested", "flags", "options"}:
        args.insert(0, {"nested": "@hidden.args", "flags": "-XX:Flags=hidden", "options": "-XX:VMOptionsFile=hidden"}[change])
    raw = argument_file(args)
    if change == "escape":
        raw = raw.replace(b"ActiveProcessorCount", b"ActiveProcessor\\u0043ount")
    if change:
        with pytest.raises(Fault, match="REFERENCE_CLIENT_RESOURCE_ARGUMENTS") as error:
            module.check_resource_arguments(raw)
        assert "synthetic-private-value" not in str(error.value)
    else:
        report = module.check_resource_arguments(raw)
        assert report["argument_bytes_verified"] and not report["shutdown_qualified"]
        assert "synthetic-private-value" not in json.dumps(report)


def test_v2_preparation_rechecks_resource_input_under_argument_lease(prepared):
    value, proof = prepared
    args = Path(value.session_arguments.path)
    args.write_bytes(argument_file(["-XX:ActiveProcessorCount=4", "cpw.mods.bootstraplauncher.BootstrapLauncher"]))
    receipt = Path(value.session_receipt.path)
    body = json.loads(receipt.read_bytes()) | {"argfile_sha256": pin(args)["sha256"]}
    receipt.write_bytes(canonical(body))
    proof.write_bytes(canonical(value.model_dump(by_alias=True) | {
        "schema": "strata/PrivateReferenceClientPreparation/2", "jvm_resource_policy": "hotspot-active-processors4/1",
        "session_arguments": pin(args), "session_receipt": pin(receipt)}))
    read = module.read_preparation(PrivateFile.model_validate(pin(proof)))
    report = module.validate_preparation(read, "a" * 64, "b" * 64, 915000)
    assert report["jvm_resource_input"]["reported_processors_argument"] == 4
    assert not report["authentication_verified"]
