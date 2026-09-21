"""Private per-boot spool authentication, not game/setup/scoring qualification.

Keep authority, key and claim outside gameplay access. A valid MAC establishes
possession of the launch key; OS/process isolation remains a separate gate.
"""

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import secrets
from pathlib import Path
from typing import Literal

from pydantic import Field, TypeAdapter

from mcbench.contracts import Digest, Id, Positive, Strict
from mcbench.inference_transport import strict_json
from mcbench.storage import canonical, digest, reject_links, require

POLICY = "private-telemetry-hmac-sha256-chain/1"
MAX_RECORD = 1048576
MAX_WIRE_RECORD = 1400000
SOURCE_ROOT = Path(__file__).resolve().parents[3]


class SpoolAuthority(Strict):
    schema_: Literal["strata/TelemetrySpoolAuthority/1"] = Field(alias="schema")
    policy: Literal["private-telemetry-hmac-sha256-chain/1"]
    instance_id: Id
    campaign_id: Id
    epoch: Positive
    challenge: Digest
    key_file: str
    key_sha256: Digest

    def fingerprint(self):
        # Paths may relocate in an operator archive; identity, scope and key bytes
        # cannot change. Never authenticate a received event's self-chosen scope.
        return digest(self.model_dump(by_alias=True, exclude={"key_file"}))

    def producer_config(self):
        return {"challenge": self.challenge, "key_file": self.key_file,
                "key_sha256": self.key_sha256, "authority_digest": self.fingerprint()}


class BoundSpoolAuthority(SpoolAuthority):
    schema_: Literal["strata/TelemetrySpoolAuthority/2"] = Field(alias="schema")
    setup_digest: Digest


def parse_authority(value):
    return TypeAdapter(SpoolAuthority | BoundSpoolAuthority).validate_python(value)


def private_read(path, limit):
    path = Path(path)
    require(path.is_absolute(), "TELEMETRY_AUTH_PATH")
    reject_links(path)
    require(path.is_file() and path.stat().st_nlink == 1 and path.stat().st_size <= limit,
            "TELEMETRY_AUTH_FILE")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "TELEMETRY_AUTH_FILE")
    return data


def issue_authority(directory, game_directory, *, instance_id, campaign_id, epoch, setup_digest=None):
    """Fresh operator directory only; never overwrite or renew a consumed grant."""
    directory, game_directory = Path(directory), Path(game_directory)
    require(directory.is_absolute() and game_directory.is_absolute(), "TELEMETRY_AUTH_PATH")
    reject_links(directory)
    reject_links(game_directory)
    directory, game_directory = directory.resolve(), game_directory.resolve()
    require(not directory.exists() and not directory.is_relative_to(game_directory) and
            not game_directory.is_relative_to(directory) and not directory.is_relative_to(SOURCE_ROOT)
            and not any((parent / ".git").exists() for parent in directory.parents),
            "TELEMETRY_AUTH_PRIVATE_DIRECTORY")
    key = secrets.token_bytes(32)
    authority = parse_authority({"schema": "strata/TelemetrySpoolAuthority/2" if setup_digest is not None
                                else "strata/TelemetrySpoolAuthority/1",
        "policy": POLICY, "instance_id": instance_id, "campaign_id": campaign_id, "epoch": epoch,
        "challenge": secrets.token_hex(32), "key_file": str(directory / "producer.key"),
        "key_sha256": hashlib.sha256(key).hexdigest(),
        **({"setup_digest": setup_digest} if setup_digest is not None else {})})
    directory.mkdir()  # Parent must already be an operator-owned location.
    for path, data in [(directory / "producer.key", key),
                       (directory / "authority.json", canonical(authority.model_dump(by_alias=True))),
                       (directory / "producer-authentication.json", canonical(authority.producer_config()))]:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return authority


class SpoolVerifier:
    def __init__(self, authority):
        self.authority = parse_authority(authority)
        self._key = private_read(self.authority.key_file, 32)
        require(len(self._key) == 32 and hmac.compare_digest(hashlib.sha256(self._key).hexdigest(),
            self.authority.key_sha256), "TELEMETRY_AUTH_KEY_CHANGED")
        claim = strict_json(private_read(self.authority.key_file + ".claimed", 4096))
        require(isinstance(claim, dict) and set(claim) == {"schema", "challenge", "authority_digest", "server_boot_id", "mac"}
                and claim["schema"] == "strata/TelemetryBootClaim/1"
                and claim["authority_digest"] == self.authority.fingerprint()
                and claim["challenge"] == self.authority.challenge,
                "TELEMETRY_AUTH_CLAIM")
        self.boot = TypeAdapter(Id).validate_python(claim["server_boot_id"])
        claimed = f"{POLICY}\nclaim\n{self.authority.fingerprint()}\n{self.authority.challenge}\n{self.boot}\n".encode("ascii")
        require(isinstance(claim["mac"], str) and re.fullmatch(r"[a-f0-9]{64}", claim["mac"]) and hmac.compare_digest(
            claim["mac"], hmac.digest(self._key, claimed, "sha256").hex()), "TELEMETRY_AUTH_CLAIM")
        self.count, self.previous = 0, "0" * 64

    def __repr__(self):
        return "<SpoolVerifier private-key redacted>"

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._key = b""  # Drop the reference; Python cannot guarantee zeroization.

    def require_scope(self, campaign, epoch):
        require(self.authority.campaign_id == campaign and self.authority.epoch == epoch,
                "TELEMETRY_AUTH_SCOPE")

    def verify(self, line):
        require(bool(self._key), "TELEMETRY_AUTH_CLOSED")
        require(len(line) <= MAX_WIRE_RECORD and line.endswith(b"\n"), "TELEMETRY_AUTH_PARTIAL")
        value = strict_json(line)
        require(isinstance(value, dict) and set(value) == {"schema", "policy", "challenge", "authority_digest", "sequence",
            "previous_mac", "event_base64", "mac"} and value["schema"] == "strata/AuthenticatedTelemetry/1"
            and value["policy"] == POLICY and value["challenge"] == self.authority.challenge
            and value["authority_digest"] == self.authority.fingerprint(),
            "TELEMETRY_AUTH_ENVELOPE")
        require(type(value["sequence"]) is int and value["sequence"] == self.count + 1
                and value["previous_mac"] == self.previous, "TELEMETRY_AUTH_SEQUENCE")
        try:
            event = base64.b64decode(value["event_base64"], validate=True)
        except (binascii.Error, ValueError, TypeError):
            require(False, "TELEMETRY_AUTH_ENCODING")
        require(0 < len(event) <= MAX_RECORD and event.endswith(b"\n"), "TELEMETRY_AUTH_ENCODING")
        content = f"{POLICY}\n{self.authority.fingerprint()}\n{self.authority.challenge}\n{value['sequence']}\n{self.previous}\n{hashlib.sha256(event).hexdigest()}\n"
        expected = hmac.digest(self._key, content.encode("ascii"), "sha256").hex()
        require(isinstance(value["mac"], str) and re.fullmatch(r"[a-f0-9]{64}", value["mac"]) and hmac.compare_digest(value["mac"], expected),
                "TELEMETRY_AUTH_MAC")
        self.count += 1
        self.previous = expected
        return event

    def receipt(self, boot, count):
        require(self.boot == boot and self.count == count, "TELEMETRY_AUTH_BOOT")
        return {"policy": POLICY, "authority_digest": self.authority.fingerprint(),
                "instance_id": self.authority.instance_id, "challenge": self.authority.challenge,
                "server_boot_id": self.boot, "records": count, "last_mac": self.previous,
                "stream_authentication_verified": True, "process_identity_qualified": False}


def inspect_authenticated_spool(path, authority_path):
    from .telemetry import inspect_spool
    authority = parse_authority(strict_json(private_read(authority_path, 65536)))
    with SpoolVerifier(authority) as verifier:
        return inspect_spool(path, authority.campaign_id, authority.epoch, authentication=verifier)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue")
    for name in ("directory", "game-directory"):
        issue.add_argument("--" + name, type=Path, required=True)
    for name in ("instance", "campaign"):
        issue.add_argument("--" + name, required=True)
    issue.add_argument("--epoch", type=int, required=True)
    inspect = commands.add_parser("inspect")
    for name in ("spool", "authority", "output"):
        inspect.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == "issue":
        authority = issue_authority(args.directory, args.game_directory, instance_id=args.instance,
                                    campaign_id=args.campaign, epoch=args.epoch)
        print(json.dumps({"authority": str(args.directory / "authority.json"),
                          "authority_digest": authority.fingerprint()}))
    else:
        from .cli import write_report
        result = inspect_authenticated_spool(args.spool, args.authority)
        print(json.dumps(write_report(args.output, result)))


if __name__ == "__main__":
    main()
