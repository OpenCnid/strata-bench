"""Private synthetic signatures; optional actual Java writer, never a game launch."""

import base64
import hashlib
import hmac
import json
import os
import subprocess
from pathlib import Path

import pytest

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical
from strata_evaluator.scorer import Scorer
from strata_evaluator.telemetry import inspect_spool
from strata_evaluator.telemetry_auth import (
    POLICY, MAX_WIRE_RECORD, SpoolVerifier, inspect_authenticated_spool, issue_authority,
)
from test_evaluator import predicate
from test_telemetry import records


def claim(authority, key, boot="boot"):
    data = f"{POLICY}\nclaim\n{authority.fingerprint()}\n{authority.challenge}\n{boot}\n".encode()
    value = {"schema": "strata/TelemetryBootClaim/1", "challenge": authority.challenge,
        "authority_digest": authority.fingerprint(), "server_boot_id": boot,
        "mac": hmac.digest(key, data, "sha256").hex()}
    Path(authority.key_file + ".claimed").write_bytes(canonical(value) + b"\n")


def signed(authority, key, values):
    previous, lines = "0" * 64, []
    for seq, event in enumerate(values, 1):
        body = canonical(event) + b"\n"
        data = f"{POLICY}\n{authority.fingerprint()}\n{authority.challenge}\n{seq}\n{previous}\n{hashlib.sha256(body).hexdigest()}\n"
        mac = hmac.digest(key, data.encode(), "sha256").hex()
        lines.append({"schema": "strata/AuthenticatedTelemetry/1", "policy": POLICY,
            "challenge": authority.challenge, "authority_digest": authority.fingerprint(),
            "sequence": seq, "previous_mac": previous, "mac": mac,
            "event_base64": base64.b64encode(body).decode()})
        previous = mac
    return lines


def write(path, lines):
    path.write_bytes(b"".join(canonical(line) + b"\n" for line in lines))


@pytest.fixture
def source(tmp_path, example):
    game = tmp_path / "game"
    game.mkdir()
    authority = issue_authority(tmp_path / "private", game,
        instance_id="instance", campaign_id="synthetic", epoch=1)
    key = Path(authority.key_file).read_bytes()
    claim(authority, key)
    values = records(example)
    values[0]["payload_schema"] = "strata/ServerStarted/4"
    values[0]["payload"].update(module="strata-forge1192-telemetry/0.3.3", config_queries=[],
        craft_capture_policy="server-result-pickup-fastbench-bound/2",
        craft_capture_support={"hook_verified": True, "fastbench_sha256": None})
    path = tmp_path / "events.authenticated.jsonl"
    write(path, signed(authority, key, values))
    return authority, key, values, path


def inspect(source):
    authority, _, _, path = source
    return inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))


def test_authentication_is_not_scoring_or_process_qualification(source, database):
    authority, key, values, path = source
    result = inspect(source)
    assert result["file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result["authentication"]["stream_authentication_verified"] is True
    assert result["authentication"]["instance_id"] == "instance"
    assert result["authentication"]["process_identity_qualified"] is False
    assert not result["scoring_eligible"] and not result["transport_identity_verified"]
    assert result == inspect(source)  # Deterministic offline replay, not new credit.
    assert key.hex() not in json.dumps(result) and base64.b64encode(key).decode() not in json.dumps(result)
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        Scorer(database).score("instance", predicate(), GameEvent.model_validate(values[1]))
    with SpoolVerifier(authority) as verifier:
        with pytest.raises(Fault, match="TELEMETRY_AUTH_SCOPE"):
            inspect_spool(path, "different", 1, authentication=verifier)
    with pytest.raises(Fault, match="TELEMETRY_AUTH_CLOSED"):
        verifier.verify(path.read_bytes().splitlines(keepends=True)[0])


@pytest.mark.parametrize("mutation", ["payload", "challenge", "authority", "mac", "mac_unicode",
    "duplicate", "reorder", "previous", "sequence_bool", "base64", "extra", "partial", "missing_stop"])
def test_modified_forged_replayed_or_incomplete_records_fail(source, mutation):
    authority, key, values, path = source
    lines = signed(authority, key, values)
    if mutation == "payload":
        values[0]["payload"]["recipe_count"] += 1
        lines[0]["event_base64"] = base64.b64encode(canonical(values[0]) + b"\n").decode()
    elif mutation in {"challenge", "authority", "mac", "mac_unicode", "previous", "sequence_bool", "base64", "extra"}:
        key_name, value = {"challenge": ("challenge", "f" * 64),
            "authority": ("authority_digest", "f" * 64), "mac": ("mac", "f" * 64),
            "mac_unicode": ("mac", "\u0100" * 64), "previous": ("previous_mac", "f" * 64),
            "sequence_bool": ("sequence", True), "base64": ("event_base64", "?"),
            "extra": ("unknown", True)}[mutation]
        lines[0][key_name] = value
    elif mutation == "duplicate":
        lines.insert(1, lines[0])
    elif mutation == "reorder":
        lines[0], lines[1] = lines[1], lines[0]
    elif mutation == "missing_stop":
        lines.pop()
    write(path, lines)
    if mutation == "partial":
        path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(Fault, match="TELEMETRY_"):
        inspect(source)


@pytest.mark.parametrize("field,value,code", [("campaign_id", "foreign", "TELEMETRY_SCOPE_MISMATCH"),
    ("epoch", 2, "TELEMETRY_SCOPE_MISMATCH"), ("server_boot_id", "foreign", "TELEMETRY_AUTH_BOOT")])
def test_signed_event_cannot_choose_scope(source, field, value, code):
    authority, key, values, path = source
    values[0][field] = value
    write(path, signed(authority, key, values))
    with pytest.raises(Fault, match=code):
        inspect(source)


@pytest.mark.parametrize("field,value", [("instance_id", "foreign"), ("campaign_id", "foreign"), ("epoch", 2)])
def test_same_key_cannot_relabel_the_registered_authority(source, field, value):
    authority, _, _, _ = source
    with pytest.raises(Fault, match="TELEMETRY_AUTH_CLAIM"):
        SpoolVerifier(authority.model_copy(update={field: value}))


def test_key_claim_duplicate_fields_and_quota_are_checked(source):
    authority, key, _, path = source
    Path(authority.key_file).write_bytes(b"x" * 32)
    with pytest.raises(Fault, match="TELEMETRY_AUTH_KEY_CHANGED"):
        SpoolVerifier(authority)
    Path(authority.key_file).write_bytes(key)
    raw = path.read_bytes()
    path.write_bytes(raw.replace(b'"sequence":1', b'"sequence":1,"sequence":1', 1))
    with pytest.raises(Fault, match="DUPLICATE_JSON_KEY"):
        inspect(source)
    path.write_bytes(b"x" * (MAX_WIRE_RECORD + 1) + b"\n")
    with pytest.raises(Fault, match="TELEMETRY_PARTIAL_RECORD"):
        inspect(source)
    Path(authority.key_file + ".claimed").unlink()
    with pytest.raises(Fault, match="TELEMETRY_AUTH_FILE"):
        SpoolVerifier(authority)


def test_authority_issuance_is_fresh_private_and_never_renews(source, tmp_path):
    authority, _, _, _ = source
    for directory in (tmp_path / "private", tmp_path / "game" / "new"):
        with pytest.raises(Fault, match="TELEMETRY_AUTH_PRIVATE_DIRECTORY"):
            issue_authority(directory, tmp_path / "game", instance_id="i", campaign_id="c", epoch=1)
    assert json.loads((tmp_path / "private" / "producer-authentication.json").read_bytes()) == authority.producer_config()
    checkout = tmp_path / "other-checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: private-worktree-reference")
    with pytest.raises(Fault, match="TELEMETRY_AUTH_PRIVATE_DIRECTORY"):
        issue_authority(checkout / "keys", tmp_path / "game", instance_id="i", campaign_id="c", epoch=1)


def test_wire_growth_after_initial_stat_cannot_bypass_total_quota(source, monkeypatch):
    import io
    import strata_evaluator.telemetry as telemetry
    authority, _, _, path = source
    data = path.read_bytes()
    path.write_bytes(b"initial")
    original = Path.open
    def growing_open(self, *args, **kwargs):
        return io.BytesIO(data) if self == path else original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", growing_open)
    monkeypatch.setattr(telemetry, "MAX_SPOOL_BYTES", len(data) - 1)
    with pytest.raises(Fault, match="TELEMETRY_QUOTA_EXHAUSTED"):
        inspect(source)


def test_actual_java_producer_verifies_in_python_without_game(source, tmp_path):
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if not java or not classpath:
        pytest.skip("Explicit pinned Java/classpath required; synthetic source test only")
    authority = issue_authority(tmp_path / "java-private", tmp_path / "game",
        instance_id="java-instance", campaign_id="java-synthetic", epoch=1)
    spool = tmp_path / "spool"
    spool.mkdir()
    config = {"schema": "strata/ForgeTelemetryConfig/3", "campaign_id": authority.campaign_id,
        "epoch": 1, "spool_directory": str(spool), "max_bytes": 65536, "max_events": 10,
        "recipe_ids": [], "config_queries": [], "authentication": authority.producer_config()}
    config_file = tmp_path / "java-private" / "config.json"
    config_file.write_bytes(canonical(config))
    command = [java, "-cp", Path(classpath).read_text(),
        "io.github.opencnid.strata.telemetry.AuthenticatedSpoolFixture", str(config_file), str(tmp_path / "game")]
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    result = subprocess.run(command, capture_output=True, timeout=15, **options)
    assert result.returncode == 0, result.stderr.decode()
    files = list(spool.glob("*.authenticated.jsonl"))
    assert len(files) == 1
    report = inspect_authenticated_spool(files[0], config_file.with_name("authority.json"))
    assert report["records"] == 3 and report["sampled_server_ticks"] == 20
    assert report["authentication"]["stream_authentication_verified"] is True
    assert report["scoring_eligible"] is False
    before = files[0].read_bytes()
    repeated = subprocess.run(command, capture_output=True, timeout=15, **options)
    assert repeated.returncode != 0 and len(list(spool.glob("*.authenticated.jsonl"))) == 1
    assert files[0].read_bytes() == before
