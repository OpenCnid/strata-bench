"""Operator-only leases for original assets and explicitly pinned skin-cache inputs.

FileLease remains strict. This separate policy accepts only declared, byte-pinned
PNG cache entries; it is not general mutable-directory or renderer qualification.
The caller must retain these leases until its owned client is terminal.
"""

import hashlib
from pathlib import Path
import re
import struct
import zlib

from pydantic import Field, model_validator

from .contracts import Digest, Strict
from .launch_integrity import FileLease, safe, tree_files
from .storage import digest, require

POLICY = "forge-pinned-skin-cache/1"
MAX_BYTES = 262144


class SkinCachePin(Strict):
    path: str = Field(pattern=r"^skins/[a-f0-9]{2}/[a-f0-9]{40}$")
    sha256: Digest
    bytes: int = Field(strict=True, ge=1, le=MAX_BYTES)

    @model_validator(mode="after")
    def cache_path(self):
        require(re.fullmatch(r"skins/[a-f0-9]{2}/[a-f0-9]{40}", self.path) is not None
                and self.path.split('/')[1] == self.path.split('/')[2][:2], "FORGE_ASSET_PLAN")
        return self


def skin_png(raw):
    """Validate the narrow observed vanilla RGBA skin format, with bounded inflate."""
    require(8 < len(raw) <= MAX_BYTES and raw[:8] == b"\x89PNG\r\n\x1a\n", "FORGE_SKIN_FORMAT")
    offset, chunks, compressed, height = 8, [], bytearray(), None
    while offset < len(raw):
        require(len(chunks) < 32 and offset + 12 <= len(raw), "FORGE_SKIN_FORMAT")
        length, = struct.unpack_from(">I", raw, offset)
        kind = raw[offset + 4:offset + 8]
        end = offset + 8 + length
        require(end + 4 <= len(raw) and kind in {b"IHDR", b"IDAT", b"IEND"}, "FORGE_SKIN_FORMAT")
        body = raw[offset + 8:end]
        require(zlib.crc32(kind + body) & 0xffffffff == struct.unpack_from(">I", raw, end)[0],
                "FORGE_SKIN_FORMAT")
        if kind == b"IHDR":
            require(not chunks and length == 13, "FORGE_SKIN_FORMAT")
            width, height, depth, colour, compression, filtering, interlace = struct.unpack(">IIBBBBB", body)
            require(width == 64 and height in {32, 64} and (depth, colour, compression, filtering, interlace)
                    == (8, 6, 0, 0, 0), "FORGE_SKIN_FORMAT")
        elif kind == b"IDAT":
            require(chunks and chunks[-1] in {b"IHDR", b"IDAT"}, "FORGE_SKIN_FORMAT")
            compressed.extend(body)
        else:
            require(chunks and chunks[-1] == b"IDAT" and length == 0 and end + 4 == len(raw),
                    "FORGE_SKIN_FORMAT")
        chunks.append(kind)
        offset = end + 4
    require(chunks and chunks[-1] == b"IEND" and height is not None, "FORGE_SKIN_FORMAT")
    expected = height * 257
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(compressed, expected + 1)
    except zlib.error:
        require(False, "FORGE_SKIN_FORMAT")
    require(len(pixels) == expected and decoder.eof and not decoder.unused_data
            and not decoder.unconsumed_tail and all(pixels[i * 257] <= 4 for i in range(height)),
            "FORGE_SKIN_FORMAT")
    return {"width": 64, "height": height, "encoding": "rgba8/noninterlaced"}


class HeldForgeAssets:
    def __init__(self, root, inventory, expected):
        self.root = safe(root)
        require(self.root.is_dir() and len(expected) <= 16, "FORGE_ASSET_PLAN")
        pins = [SkinCachePin.model_validate(p) for p in expected]
        require(len({p.path for p in pins}) == len(pins) and
                all(p.path.split('/')[1] == p.path.split('/')[2][:2] for p in pins), "FORGE_ASSET_PLAN")
        require(inventory.get("schema") == "strata/LaunchFileInventory/1" and inventory.get("trees") == [],
                "FORGE_ASSET_PLAN")
        self.original = {str(safe(e["path"])) for e in inventory["files"]}
        require(self.original and all(Path(p).is_relative_to(self.root) for p in self.original), "FORGE_ASSET_PLAN")
        self.expected = {str(self.root / p.path): p for p in pins}
        require(not self.original.intersection(self.expected), "FORGE_ASSET_PLAN")
        self.leases, self.captured, self.closed = [], {}, False
        self.inventory_digest = digest(inventory)
        self.plan_digest = digest([p.model_dump() for p in pins])
        try:
            self.leases.append(FileLease(inventory))
            self.recheck()
        except BaseException:
            self.close()
            raise

    def recheck(self):
        require(not self.closed, "FORGE_ASSET_LEASE_CLOSED")
        current = set(tree_files(self.root))
        require(self.original <= current and current <= self.original | set(self.expected), "FORGE_ASSET_TREE_CHANGED")
        require(set(self.captured) <= current, "FORGE_ASSET_TREE_CHANGED")
        for name in sorted(current - self.original - set(self.captured)):
            path, pin = safe(name), self.expected[name]
            require(path.stat().st_nlink == 1, "FORGE_ASSET_LINK")
            entry = {"path": str(path), "sha256": pin.sha256, "bytes": pin.bytes}
            lease = FileLease({"schema": "strata/LaunchFileInventory/1", "files": [entry], "trees": []})
            self.leases.append(lease)
            raw = path.read_bytes()
            require(hashlib.sha256(raw).hexdigest() == pin.sha256, "FORGE_SKIN_CHANGED")
            self.captured[name] = pin.model_dump() | skin_png(raw)
        require(set(tree_files(self.root)) == current, "FORGE_ASSET_TREE_CHANGED")
        for lease in self.leases:
            lease.recheck()

    def receipt(self):
        self.recheck()
        return {"schema": "strata/ForgeAssetLease/1", "policy": POLICY,
                "original_inventory_digest": self.inventory_digest, "expected_cache_digest": self.plan_digest,
                "original_files": len(self.original), "captured_cache": list(self.captured.values()),
                "renderer_qualified": False, "isolation_qualified": False}

    def close(self):
        self.closed = True
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
