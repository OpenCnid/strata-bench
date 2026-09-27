"""Synthetic output corruption cases against actual pinned official class bytes."""

import copy
import gzip
import os
from pathlib import Path
import uuid

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator.player_body_evidence import (
    MODULE_SHA, POLICY, REQUIRED_CLASSES, SERVER_SHA, TRANSFORMED,
    official_body_class_pins, sha, verify_player_body_output,
)
from test_probe_saved_bodies import PLAYER, payload, player

SCOPE = {"campaign_id": "synthetic", "run_id": "capture", "epoch": 1}
CONFIG_SHA = "a" * 64


@pytest.fixture(scope="module")
def official():
    path = os.environ.get("STRATA_VANILLA_SERVER_JAR")
    if not path:
        pytest.skip("explicit installed official server required")
    raw = Path(path).read_bytes()
    return raw, official_body_class_pins(raw)


def fixture(official, roster=None):
    _, classes = official
    roster = [PLAYER] if roster is None else roster
    files, bodies = {}, []
    for identity in roster:
        value = player()
        del value["DataVersion"]  # The live saveWithoutId serializer has no file wrapper.
        value["UUID"] = (11, uuid.UUID(identity).bytes)
        raw = gzip.decompress(payload(value))
        files[identity + ".nbt"] = raw
        bodies.append({"uuid": identity, "bytes": len(raw), "sha256": sha(raw)})
    bindings = "\n".join(name + "=" + classes[name] + ":" + TRANSFORMED.get(name, classes[name])
                         for name in sorted(REQUIRED_CLASSES)).encode()
    files["loaded-classes.txt"] = bindings
    values = [
        {"schema": "strata/PrivateBodyStart/1", "policy": POLICY, **SCOPE, "pid": 123,
         "module_sha256": MODULE_SHA, "server_sha256": SERVER_SHA, "config_sha256": CONFIG_SHA, "roster": roster},
        {"schema": "strata/PrivateBodyRunning/1"},
        {"schema": "strata/PrivateBodyCapture/1", "tick": 7, "begin_ns": 250, "bodies": bodies},
        {"schema": "strata/PrivateBodyStop/1", "tick": 9, "loaded_classes": len(REQUIRED_CLASSES), "bindings_sha256": sha(bindings)},
    ]
    records = [{"seq": i, "elapsed_ns": i * 100, "body": value} for i, value in enumerate(values, 1)]
    return files, records


def verify(official, files, records, roster=None, **overrides):
    files = dict(files)
    files["events.jsonl"] = b"".join(canonical(record) + b"\n" for record in records)
    arguments = {"server_bytes": official[0], "scope": SCOPE, "roster": roster or [PLAYER],
                 "config_sha256": CONFIG_SHA, "pid": 123} | overrides
    return verify_player_body_output(lambda name, limit: files[name], list(files), **arguments)


def test_complete_content_preserves_unknown_fields_without_producer_claim(official):
    files, records = fixture(official)
    result = verify(official, files, records)
    assert result["content_verified"] and result["capture_tick"] == 7
    assert result["bodies"][PLAYER]["nbt_sha256"] == sha(files[PLAYER + ".nbt"])
    assert result["bodies"][PLAYER]["root_fields"] == len(player()) - 1
    assert not any(result[key] for key in ("owned_producer_verified", "live_initial_state_verified",
                                          "transient_state_verified", "native_probe_admission"))


def test_all_roster_members_required_in_exact_declared_order(official):
    roster = [PLAYER, str(uuid.UUID(int=2))]
    files, records = fixture(official, roster)
    assert set(verify(official, files, records, roster)["bodies"]) == set(roster)
    records[2]["body"]["bodies"].reverse()
    with pytest.raises(Fault, match="BODY_CAPTURE_ROSTER"):
        verify(official, files, records, roster)


@pytest.mark.parametrize("change", [
    lambda r: r.pop(), lambda r: r.pop(1), lambda r: r.append(copy.deepcopy(r[-1])),
    lambda r: r[1].update(seq=1), lambda r: r[0].update(seq=True),
    lambda r: r[1].update(elapsed_ns=-1), lambda r: r[2].update(elapsed_ns=199),
    lambda r: r[0]["body"].update(pid=124), lambda r: r[0]["body"].update(pid=True),
    lambda r: r[0]["body"].update(epoch=True), lambda r: r[0]["body"].update(extra="hidden"),
    lambda r: r[0]["body"].update(config_sha256="b" * 64),
    lambda r: r[0]["body"].update(module_sha256="b" * 64),
    lambda r: r[0]["body"].update(server_sha256="b" * 64),
    lambda r: r[0]["body"].update(roster=[]), lambda r: r[1]["body"].update(extra=True),
    lambda r: r[2]["body"].update(tick=0), lambda r: r[2]["body"].update(tick=True),
    lambda r: r[2]["body"].update(begin_ns=199), lambda r: r[2]["body"].update(begin_ns=301),
    lambda r: r[2]["body"].update(bodies=[]), lambda r: r[2]["body"]["bodies"][0].update(bytes=True),
    lambda r: r[2]["body"]["bodies"][0].update(bytes=16 * 1024**2 + 1),
    lambda r: r[2]["body"]["bodies"][0].update(sha256="b" * 64),
    lambda r: r[3]["body"].update(tick=6), lambda r: r[3]["body"].update(loaded_classes=True),
    lambda r: r[3]["body"].update(bindings_sha256="b" * 64),
])
def test_partial_foreign_and_malformed_claims_refuse(official, change):
    files, records = fixture(official)
    change(records)
    with pytest.raises(Fault):
        verify(official, files, records)


@pytest.mark.parametrize("case", ["missing", "extra", "duplicate", "foreign", "transformed", "original", "trailing"])
def test_loaded_class_inventory_is_independently_checked(official, case):
    files, records = fixture(official)
    lines = files["loaded-classes.txt"].decode().splitlines()
    if case == "missing":
        lines.pop()
    elif case == "extra":
        lines.append("unknown=bad:bad")
    elif case == "duplicate":
        lines.append(lines[0])
    elif case == "foreign":
        lines[0] = lines[0].replace("agh=", "foreign=")
    elif case == "transformed":
        lines[0] = lines[0].split(":")[0] + ":" + "b" * 64
    elif case == "original":
        name, value = lines[0].split("=")
        lines[0] = name + "=" + "b" * 64 + ":" + value.split(":")[1]
    else:
        lines.append("")
    files["loaded-classes.txt"] = "\n".join(lines).encode()
    records[3]["body"].update(loaded_classes=len(lines), bindings_sha256=sha(files["loaded-classes.txt"]))
    with pytest.raises(Fault):
        verify(official, files, records)


@pytest.mark.parametrize("case", ["missing", "extra", "changed", "wrong_uuid", "trailing_nbt"])
def test_exact_files_and_nbt_identity_are_required(official, case):
    files, records = fixture(official)
    name = PLAYER + ".nbt"
    if case == "missing":
        del files[name]
    elif case == "extra":
        files["foreign.nbt"] = b"extra"
    elif case == "changed":
        files[name] += b"x"
    elif case == "wrong_uuid":
        value = player()
        value["UUID"] = (11, uuid.UUID(int=2).bytes)
        files[name] = gzip.decompress(payload(value))
    else:
        files[name] += b"\0"
    if case in {"wrong_uuid", "trailing_nbt"}:
        records[2]["body"]["bodies"][0].update(bytes=len(files[name]), sha256=sha(files[name]))
    with pytest.raises(Fault):
        verify(official, files, records)


def test_changed_reread_cannot_verify(official):
    files, records = fixture(official)
    files["events.jsonl"] = b"".join(canonical(record) + b"\n" for record in records)
    reads = {}
    def read(name, limit):
        reads[name] = reads.get(name, 0) + 1
        return files[name] if reads[name] == 1 else b"changed"
    with pytest.raises(Fault, match="BODY_OUTPUT_CHANGED"):
        verify_player_body_output(read, list(files), server_bytes=official[0], scope=SCOPE,
                                  roster=[PLAYER], config_sha256=CONFIG_SHA, pid=123)


def test_original_server_pin_is_not_caller_declared(official):
    files, records = fixture(official)
    with pytest.raises(Fault, match="BODY_SERVER_PIN"):
        verify(official, files, records, server_bytes=official[0] + b"changed")


def test_incomplete_actual_jvm_header_is_not_a_capture(official):
    files, records = fixture(official)
    records[:] = records[:1]
    with pytest.raises(Fault, match="BODY_JOURNAL_INCOMPLETE"):
        verify(official, files, records)
