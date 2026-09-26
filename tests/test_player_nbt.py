"""Private serializer output bounds and opt-in installed-code format conformance.

No live server, player capture, paid model, producer authentication or G1 claim.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from strata_evaluator.saved_blocks import NbtReader
from test_saved_blocks import string


SERVER_SHA = "d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6"


@pytest.fixture(scope="module")
def codec(tmp_path_factory):
    javac = shutil.which("javac")
    if not javac:
        pytest.skip("pinned JDK17 compiler required")
    expected = json.loads(Path("java/build-inputs.json").read_text())["compiler"]["javac_sha256"]
    assert hashlib.sha256(Path(javac).read_bytes()).hexdigest() == expected
    output = tmp_path_factory.mktemp("player-nbt-classes")
    result = subprocess.run([javac, "--release", "17", "-d", str(output),
        "evaluator/java/livebody/PlayerNbt.java", "tests/java/livebody/PlayerNbtTest.java"],
        capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()

    def run(*args):
        result = subprocess.run([str(Path(javac).with_name("java.exe" if os.name == "nt" else "java")),
            "-Xmx256m", "-cp", str(output), "io.github.opencnid.strata.livebody.PlayerNbtTest", *map(str, args)],
            capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode()
        return result.stdout.decode().strip()
    return run


@pytest.fixture(scope="module")
def server():
    value = os.environ.get("STRATA_VANILLA_SERVER_JAR")
    if not value:
        pytest.skip("explicit installed official server required")
    path = Path(value)
    assert path.is_absolute() and hashlib.sha256(path.read_bytes()).hexdigest() == SERVER_SHA
    return path


def test_output_quota_refuses_without_returning_partial_capture(codec):
    assert codec("bounds") == "bounded-output-pass"


def test_installed_descriptors_and_wrong_receiver_rejections(codec, server):
    assert codec("bindings", server) == "actual-descriptors-pass; no game initialization"


def test_all_tag_types_survive_actual_nbt_codec(codec, server, tmp_path):
    # Independent binary fixture: numeric widths, arrays, ordered
    # nested lists, compounds, modified UTF-8 and an unknown future field.
    values = [(1, struct.pack(">b", -7)), (2, struct.pack(">h", -1024)),
              (3, struct.pack(">i", 123456)), (4, struct.pack(">q", -(2**60))),
              (5, struct.pack(">f", -12.5)), (6, struct.pack(">d", 0.125)),
              (7, struct.pack(">i", 3) + b"\x00\x80\xff"),
              (8, string("nul\0emoji\U0001f419surrogate\ud800")),
              (9, struct.pack(">Biqq", 4, 2, 55, -33)),
              (10, b"\x08" + string("unknown") + string("preserved") + b"\0"),
              (11, struct.pack(">iii", 2, -123, 456)),
              (12, struct.pack(">iqq", 2, 2**60, -(2**60)))]
    raw = b"\x0a\0\0" + b"".join(bytes([kind]) + string(str(kind)) + value
                                    for kind, value in values) + b"\0"
    source, target = tmp_path / "input.nbt", tmp_path / "output.nbt"
    source.write_bytes(raw)
    assert codec("roundtrip", server, source, target).startswith("actual-nbt-roundtrip")
    actual, expected = NbtReader(target.read_bytes()).root(), NbtReader(raw).root()
    assert actual == expected
    assert struct.pack(">f", actual["5"].value) == struct.pack(">f", -12.5)


def test_actual_nbt_signed_zero_normalization_is_explicit(codec, server, tmp_path):
    # Retain the discovered limitation: Java NBT caches zero-valued floating
    # tags. Python numeric equality alone would silently hide this difference.
    raw = (b"\x0a\0\0\x05" + string("float") + struct.pack(">f", -0.0)
           + b"\x06" + string("double") + struct.pack(">d", -0.0) + b"\0")
    source, target = tmp_path / "negative-zero.nbt", tmp_path / "normalized.nbt"
    source.write_bytes(raw)
    codec("roundtrip", server, source, target)
    before, after = NbtReader(raw).root(), NbtReader(target.read_bytes()).root()
    for name, fmt in (("float", ">f"), ("double", ">d")):
        assert struct.pack(fmt, before[name].value) != struct.pack(fmt, after[name].value)
        assert struct.pack(fmt, after[name].value) == struct.pack(fmt, 0.0)


def test_actual_serializer_rejects_oversize_compound(codec, server, tmp_path):
    source = tmp_path / "oversize.nbt"
    source.write_bytes(b"\x0a\0\0\x07" + string("large") + struct.pack(">i", 16 * 1024**2)
                       + bytes(16 * 1024**2) + b"\0")
    assert codec("oversize", server, source) == "actual-oversize-refused"
