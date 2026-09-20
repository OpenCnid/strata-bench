"""Private, read-only Minecraft 1.19.2 saved-block references.

Never install in gameplay environments. This decodes selected persisted block
states, not live state, snapshot consistency, registry validity or causal credit.
Use immutable operator copies captured after a proven normal server save/stop.
Filesystem consistency checks here are not authentication or an isolation boundary.
"""

import hashlib
import os
from pathlib import Path
import re
import stat
import struct
from dataclasses import dataclass
import zlib

from mcbench.storage import Fault, reject_links, require, safe_relative

POLICY = "saved-anvil-1192-blocks/1"
DATA_VERSION = 3120
MAX_COMPRESSED = 8 * 1024**2
MAX_NBT = 16 * 1024**2
MAX_TAGS = 200000
MAX_POINTS = 256
MAX_TOTAL_COMPRESSED = 32 * 1024**2
MAX_TOTAL_NBT = 64 * 1024**2
NAME = re.compile(r"[a-z0-9_.-]+:[a-z0-9_./-]+")


@dataclass(frozen=True)
class Tag:
    kind: int
    value: object


class NbtReader:
    """Big-endian NBT with explicit byte, node, depth and allocation bounds."""

    def __init__(self, raw: bytes):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_NBT, "SAVED_NBT_QUOTA")
        self.raw = memoryview(raw)
        self.offset = 0
        self.nodes = 0

    def take(self, size):
        require(0 <= size <= len(self.raw) - self.offset, "SAVED_NBT_TRUNCATED")
        value = self.raw[self.offset:self.offset + size]
        self.offset += size
        return value

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self):
        raw = bytes(self.take(self.number(">H")))
        # Java DataInput/DataOutput use modified UTF-8: encoded NUL and UTF-16
        # surrogate code units, never four-byte UTF-8. Preserve unpaired units.
        require(all(x < 0xF0 for x in raw), "SAVED_NBT_STRING_INVALID")
        try:
            decoded = raw.replace(b"\xc0\x80", b"\0").decode("utf-8", "surrogatepass")
            return decoded.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")
        except UnicodeError:
            raise Fault("SAVED_NBT_STRING_INVALID") from None

    def payload(self, kind, depth=0):
        self.nodes += 1
        require(self.nodes <= MAX_TAGS and depth <= 64, "SAVED_NBT_QUOTA")
        require(type(kind) is int and 1 <= kind <= 12, "SAVED_NBT_TYPE_INVALID")
        if kind <= 6:
            value = self.number({1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}[kind])
        elif kind in (7, 11, 12):
            count = self.number(">i")
            width = {7: 1, 11: 4, 12: 8}[kind]
            require(0 <= count <= MAX_NBT // width, "SAVED_NBT_QUOTA")
            value = self.take(count * width)
        elif kind == 8:
            value = self.string()
        elif kind == 9:
            subtype, count = self.number(">B"), self.number(">i")
            require(0 <= subtype <= 12 and (subtype != 0 or count == 0), "SAVED_NBT_TYPE_INVALID")
            require(0 <= count <= MAX_TAGS - self.nodes, "SAVED_NBT_QUOTA")
            value = (subtype, tuple(self.payload(subtype, depth + 1) for _ in range(count)))
        else:
            value = {}
            while child := self.number(">B"):
                key = self.string()
                require(key not in value, "SAVED_NBT_DUPLICATE_KEY")
                value[key] = self.payload(child, depth + 1)
        return Tag(kind, value)

    def root(self):
        require(self.number(">B") == 10, "SAVED_NBT_ROOT_INVALID")
        require(self.string() == "", "SAVED_NBT_ROOT_INVALID")
        value = self.payload(10).value
        require(self.offset == len(self.raw), "SAVED_NBT_TRAILING_DATA")
        return value


def field(compound, name, kind):
    tag = compound.get(name)
    require(isinstance(tag, Tag) and tag.kind == kind, "SAVED_CHUNK_FIELD_INVALID")
    return tag.value


def unpack_chunk(payload: bytes, compression: int):
    require(type(payload) is bytes and 0 < len(payload) <= MAX_COMPRESSED, "SAVED_CHUNK_QUOTA")
    require(type(compression) is int and compression in (1, 2, 3), "SAVED_COMPRESSION_UNSUPPORTED")
    if compression == 3:
        require(len(payload) <= MAX_NBT, "SAVED_NBT_QUOTA")
        return payload
    decoder = zlib.decompressobj(31 if compression == 1 else 15)
    try:
        raw = decoder.decompress(payload, MAX_NBT + 1)
    except zlib.error:
        raise Fault("SAVED_CHUNK_COMPRESSION_INVALID") from None
    require(len(raw) <= MAX_NBT and not decoder.unconsumed_tail, "SAVED_NBT_QUOTA")
    require(decoder.eof and not decoder.unused_data, "SAVED_CHUNK_COMPRESSION_INVALID")
    return raw


def block_states(raw: bytes, chunk_x: int, chunk_z: int, points):
    """Decode only requested block states; missing sections never become guessed air."""
    root = NbtReader(raw).root()
    require(field(root, "DataVersion", 3) == DATA_VERSION, "SAVED_VERSION_UNSUPPORTED")
    require((field(root, "xPos", 3), field(root, "zPos", 3)) == (chunk_x, chunk_z),
            "SAVED_CHUNK_COORDINATE_MISMATCH")
    # 1.19.2 ChunkSerializer writes ChunkStatus.getName(), not toString().
    require(field(root, "Status", 8) == "full", "SAVED_CHUNK_INCOMPLETE")
    subtype, sections = field(root, "sections", 9)
    require(subtype == 10 and len(sections) <= 256, "SAVED_SECTION_INVALID")
    by_y = {}
    for section in sections:
        y = field(section.value, "Y", 1)
        require(y not in by_y, "SAVED_SECTION_DUPLICATE")
        by_y[y] = section.value
    decoded = {}
    for y in {point[1] // 16 for point in points}:
        require(y in by_y and "block_states" in by_y[y], "SAVED_SECTION_MISSING")
        states = field(by_y[y], "block_states", 10)
        subtype, entries = field(states, "palette", 9)
        require(subtype == 10 and 1 <= len(entries) <= 4096, "SAVED_PALETTE_INVALID")
        palette = []
        for entry in entries:
            value = entry.value
            require(set(value) <= {"Name", "Properties"}, "SAVED_PALETTE_UNSUPPORTED")
            name = field(value, "Name", 8)
            require(0 < len(name) <= 256 and NAME.fullmatch(name), "SAVED_PALETTE_INVALID")
            props = field(value, "Properties", 10) if "Properties" in value else {}
            require(len(props) <= 64, "SAVED_PALETTE_QUOTA")
            properties = {}
            for key, prop in props.items():
                require(0 < len(key) <= 256 and prop.kind == 8 and len(prop.value) <= 256,
                        "SAVED_PALETTE_INVALID")
                properties[key] = prop.value
            palette.append({"block_id": name, "properties": properties})
        if len(palette) == 1:
            require("data" not in states, "SAVED_PALETTE_DATA_INVALID")
            indexes = (0,) * 4096
        else:
            data = field(states, "data", 12)
            bits = max(4, (len(palette) - 1).bit_length())
            per_long = 64 // bits
            require(len(data) == ((4096 + per_long - 1) // per_long) * 8, "SAVED_PALETTE_DATA_INVALID")
            words = struct.unpack(">" + "Q" * (len(data) // 8), data)
            indexes = tuple((words[i // per_long] >> ((i % per_long) * bits)) & ((1 << bits) - 1)
                            for i in range(4096))
            require(all(index < len(palette) for index in indexes), "SAVED_PALETTE_INDEX_INVALID")
        decoded[y] = palette, indexes
    result = []
    for x, y, z in points:
        palette, indexes = decoded[y // 16]
        index = ((y % 16) << 8) | ((z % 16) << 4) | (x % 16)
        result.append({"position": {"x": x, "y": y, "z": z}, **palette[indexes[index]]})
    return result


def stable_signature(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def read_region(region: Path, chunk_x: int, chunk_z: int):
    """Bounded seek reads, including official external .mcc streams; no world writes."""
    require(region.is_absolute(), "UNSAFE_PATH")
    require(region.name == f"r.{chunk_x // 32}.{chunk_z // 32}.mca", "SAVED_REGION_COORDINATE_MISMATCH")
    reject_links(region)
    try:
        with region.open("rb") as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode), "SAVED_REGION_INVALID")
            require(before.st_size >= 8192 and before.st_size % 4096 == 0, "SAVED_REGION_INVALID")
            header = stream.read(8192)
            require(len(header) == 8192, "SAVED_REGION_INVALID")
            intervals = []
            locations = struct.unpack(">1024I", header[:4096])
            for location in locations:
                if location == 0:
                    continue
                offset, count = location >> 8, location & 255
                require(offset >= 2 and count > 0 and (offset + count) * 4096 <= before.st_size,
                        "SAVED_REGION_LOCATION_INVALID")
                intervals.append((offset, offset + count))
            intervals.sort()
            require(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), "SAVED_REGION_OVERLAP")
            slot = chunk_x % 32 + (chunk_z % 32) * 32
            location = locations[slot]
            require(location != 0, "SAVED_CHUNK_MISSING")
            offset, count = location >> 8, location & 255
            stream.seek(offset * 4096)
            envelope = stream.read(5)
            require(len(envelope) == 5, "SAVED_CHUNK_TRUNCATED")
            length, flag = struct.unpack(">IB", envelope)
            external = bool(flag & 128)
            require(1 <= length <= count * 4096 - 4, "SAVED_CHUNK_LENGTH_INVALID")
            if external:
                require(length == 1, "SAVED_CHUNK_STREAM_CONFLICT")
                path = region.parent / f"c.{chunk_x}.{chunk_z}.mcc"
                reject_links(path)
                with path.open("rb") as source:
                    ext_before = os.fstat(source.fileno())
                    require(stat.S_ISREG(ext_before.st_mode), "SAVED_REGION_INVALID")
                    require(0 < ext_before.st_size <= MAX_COMPRESSED, "SAVED_CHUNK_QUOTA")
                    payload = source.read(MAX_COMPRESSED + 1)
                    require(stable_signature(ext_before) == stable_signature(os.fstat(source.fileno())),
                            "SAVED_SOURCE_CHANGED")
                    require(len(payload) == ext_before.st_size, "SAVED_SOURCE_CHANGED")
            else:
                payload = stream.read(length - 1)
                require(len(payload) == length - 1, "SAVED_CHUNK_TRUNCATED")
            require(stable_signature(before) == stable_signature(os.fstat(stream.fileno())), "SAVED_SOURCE_CHANGED")
    except OSError:
        raise Fault("SAVED_SOURCE_UNAVAILABLE") from None
    raw = unpack_chunk(payload, flag & 127)
    return raw, {"region_name": region.name, "chunk_x": chunk_x, "chunk_z": chunk_z,
        "header_sha256": hashlib.sha256(header).hexdigest(),
        "compressed_sha256": hashlib.sha256(payload).hexdigest(), "nbt_sha256": hashlib.sha256(raw).hexdigest(),
        "external": external, "compression": flag & 127, "compressed_bytes": len(payload), "nbt_bytes": len(raw)}


def read_saved_blocks(world: Path, dimension: str, points: list[tuple[int, int, int]], *, is_example: bool):
    require(type(is_example) is bool, "INVALID_ARGUMENT")
    require(isinstance(world, Path) and world.is_absolute() and world.is_dir(), "UNSAFE_PATH")
    reject_links(world)
    require(isinstance(dimension, str) and 0 < len(dimension) <= 256 and NAME.fullmatch(dimension),
            "SAVED_DIMENSION_INVALID")
    namespace, name = dimension.split(":", 1)
    safe_relative(namespace + "/" + name)
    require(type(points) is list and 1 <= len(points) <= MAX_POINTS, "SAVED_POINT_QUOTA")
    require(all(type(point) is tuple and len(point) == 3 and all(type(n) is int for n in point)
                and abs(point[0]) <= 30000000 and abs(point[2]) <= 30000000
                and -2048 <= point[1] <= 2047 for point in points), "SAVED_POSITION_INVALID")
    require(len(set(points)) == len(points), "SAVED_POSITION_DUPLICATE")
    folders = {"minecraft:overworld": world, "minecraft:the_nether": world / "DIM-1",
               "minecraft:the_end": world / "DIM1"}
    folder = folders.get(dimension, world / "dimensions" / namespace / name) / "region"
    require(folder.resolve().is_relative_to(world.resolve()), "UNSAFE_PATH")
    grouped = {}
    for point in points:
        grouped.setdefault((point[0] // 16, point[2] // 16), []).append(point)
    blocks, sources = [], []
    compressed_bytes = nbt_bytes = 0
    for (cx, cz), selected in grouped.items():
        raw, source = read_region(folder / f"r.{cx // 32}.{cz // 32}.mca", cx, cz)
        compressed_bytes += source["compressed_bytes"]
        nbt_bytes += source["nbt_bytes"]
        require(compressed_bytes <= MAX_TOTAL_COMPRESSED and nbt_bytes <= MAX_TOTAL_NBT,
                "SAVED_REFERENCE_QUOTA")
        blocks.extend(block_states(raw, cx, cz, selected))
        sources.append(source)
    by_position = {tuple(row["position"][axis] for axis in ("x", "y", "z")): row for row in blocks}
    return {"schema": "strata/SavedBlockReference/1", "policy": POLICY, "is_example": is_example,
        "data_version": DATA_VERSION, "dimension": dimension, "blocks": [by_position[p] for p in points],
        "sources": sources, "snapshot_consistency_proven": False, "action_causality_proven": False,
        "registry_membership_verified": False, "scoring_provenance_supported": False}
