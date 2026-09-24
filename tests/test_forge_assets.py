"""Synthetic PNGs and real Windows sharing semantics; no game/account calls."""

import hashlib
import os
import struct
import zlib

import pytest

from mcbench.forge_assets import HeldForgeAssets, SkinCachePin, skin_png
from mcbench.launch_integrity import FileLease, IntegrityError, snapshot
from mcbench.storage import Fault


def chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)


def png(height=64, pixels=None):
    header = struct.pack(">IIBBBBB", 64, height, 8, 6, 0, 0, 0)
    data = bytes(height * 257) if pixels is None else pixels
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(data)) + chunk(b"IEND", b"")


@pytest.mark.parametrize("height", [32, 64])
def test_bounded_skin_formats(height):
    assert skin_png(png(height)) == {"width": 64, "height": height, "encoding": "rgba8/noninterlaced"}


@pytest.mark.parametrize("case", ["crc", "trailing", "metadata", "oversized_inflate", "bad_filter", "truncated", "wrong_dimensions"])
def test_skin_payload_refusals(case):
    raw = png()
    if case == "crc":
        raw = raw[:-1] + bytes([raw[-1] ^ 1])
    elif case == "trailing":
        raw += b"executable payload"
    elif case == "metadata":
        raw = raw[:-12] + chunk(b"tEXt", b"unreviewed") + raw[-12:]
    elif case == "oversized_inflate":
        raw = png(pixels=bytes(1024 * 1024))
    elif case == "bad_filter":
        raw = png(pixels=b"\x05" + bytes(64 * 257 - 1))
    elif case == "truncated":
        raw = raw[:-12]
    else:
        raw = png(128)
    with pytest.raises(Fault, match="FORGE_SKIN_FORMAT"):
        skin_png(raw)


@pytest.mark.parametrize("name", ["../outside", "skins/aa/" + "b" * 40, "skins/aa/" + "a" * 40 + "\n",
                                 "skins/aa/" + "a" * 40 + ":stream"])
def test_cache_pin_is_a_canonical_partitioned_name(name):
    with pytest.raises(ValueError):
        SkinCachePin(path=name, sha256="a" * 64, bytes=100)


@pytest.fixture
def assets(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows file sharing")
    root = tmp_path / "assets"
    root.mkdir()
    original = root / "index.json"
    original.write_bytes(b"locked original")
    raw = png()
    pin = {"path": "skins/aa/" + "a" * 40, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return root, original, snapshot([original], []), pin, raw


def test_explicit_cache_pin_preserves_original_and_new_handles(assets):
    root, original, inventory, pin, raw = assets
    with HeldForgeAssets(root, inventory, [pin]) as lease:
        assert lease.receipt()["captured_cache"] == []
        path = root / pin["path"]
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        receipt = lease.receipt()
        assert receipt["captured_cache"] == [pin | skin_png(raw)]
        assert receipt["original_files"] == 1 and not receipt["renderer_qualified"]
        for target in (original, path):
            with pytest.raises(OSError):
                target.write_bytes(b"replaced")
            with pytest.raises(OSError):
                target.unlink()
        lease.recheck()
    path.write_bytes(b"released")
    with pytest.raises(Fault, match="FORGE_ASSET_LEASE_CLOSED"):
        lease.receipt()


@pytest.mark.parametrize("case", ["unlisted_skin", "new_jar", "changed_png", "missing_original", "duplicate_pin"])
def test_no_general_mutable_asset_exception(assets, case):
    root, original, inventory, pin, raw = assets
    pins = [pin]
    path = root / pin["path"]
    if case == "unlisted_skin":
        path = path.with_name("b" * 40)
    elif case == "new_jar":
        path = root / "injected.jar"
    elif case == "changed_png":
        raw = png(32)
    elif case == "missing_original":
        original.unlink()
    else:
        pins.append(pin)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    with pytest.raises((Fault, IntegrityError, OSError)):
        HeldForgeAssets(root, inventory, pins)
    if original.exists():
        original.write_bytes(b"failure released original handle")


def test_general_file_lease_still_rejects_the_same_addition(assets):
    root, _, _, pin, raw = assets
    with FileLease(snapshot([], [root])) as lease:
        path = root / pin["path"]
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
            lease.recheck()
