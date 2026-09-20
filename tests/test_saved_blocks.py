"""Synthetic save-format fixtures; never evidence of authentic game mechanics."""

import gzip
import hashlib
from pathlib import Path
import struct
import zlib

import pytest

from mcbench.storage import Fault
from strata_evaluator import saved_blocks as saved


def string(value):
    # Modified UTF-8, via UTF-16 code units as Java DataOutput.writeUTF does.
    units = struct.unpack(">" + "H" * (len(value.encode("utf-16-be", "surrogatepass")) // 2),
                          value.encode("utf-16-be", "surrogatepass"))
    raw = b"".join(b"\xc0\x80" if n == 0 else chr(n).encode("utf-8", "surrogatepass")
                   for n in units)
    return struct.pack(">H", len(raw)) + raw


def tag(kind, value):
    if kind in (1, 3):
        return struct.pack({1: ">b", 3: ">i"}[kind], value)
    if kind == 8:
        return string(value)
    if kind == 9:
        subtype, entries = value
        return struct.pack(">Bi", subtype, len(entries)) + b"".join(tag(subtype, x) for x in entries)
    if kind == 10:
        return b"".join(bytes([k]) + string(n) + tag(k, v) for n, (k, v) in value.items()) + b"\0"
    if kind == 12:
        return struct.pack(">i", len(value)) + b"".join(struct.pack(">Q", n) for n in value)
    raise AssertionError(kind)


def root_bytes(value):
    return b"\x0a\0\0" + tag(10, value)


def section(y=0, palette=None, words=None):
    palette = palette or [{"Name": (8, "minecraft:stone")}]
    states = {"palette": (9, (10, palette))}
    if words is not None:
        states["data"] = (12, words)
    return {"Y": (1, y), "block_states": (10, states)}


def chunk(cx=0, cz=0, sections=None):
    return {"DataVersion": (3, 3120), "xPos": (3, cx), "zPos": (3, cz),
            "Status": (8, "full"), "sections": (9, (10, sections if sections is not None else [section()]))}


def region_file(folder, root=None, *, cx=0, cz=0, compression=2, external=False):
    raw = root_bytes(root if root is not None else chunk(cx, cz))
    payload = {1: gzip.compress, 2: zlib.compress, 3: lambda b: b}[compression](raw)
    body = struct.pack(">IB", 1 if external else len(payload) + 1,
                       compression | (128 if external else 0)) + (b"" if external else payload)
    sectors = (len(body) + 4095) // 4096
    header = bytearray(8192)
    struct.pack_into(">I", header, 4 * (cx % 32 + (cz % 32) * 32), (2 << 8) | sectors)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"r.{cx // 32}.{cz // 32}.mca"
    path.write_bytes(header + body + b"\0" * (sectors * 4096 - len(body)))
    if external:
        (folder / f"c.{cx}.{cz}.mcc").write_bytes(payload)
    return path, raw


@pytest.mark.parametrize("compression", [1, 2, 3])
@pytest.mark.parametrize("external", [False, True])
def test_compressions_external_streams_and_source_hashes(tmp_path, compression, external):
    path, raw = region_file(tmp_path, cx=-33, cz=-1, compression=compression, external=external)
    actual, source = saved.read_region(path, -33, -1)
    assert actual == raw
    assert source["nbt_sha256"] == hashlib.sha256(raw).hexdigest()
    assert source["external"] is external and source["compression"] == compression
    assert source["region_name"] == "r.-2.-1.mca"


@pytest.mark.parametrize("dimension,relative", [
    ("minecraft:overworld", "region"), ("minecraft:the_nether", "DIM-1/region"),
    ("minecraft:the_end", "DIM1/region"),
    ("test:custom/nested", "dimensions/test/custom/nested/region")])
def test_dimension_negative_coordinates_order_and_no_claims(tmp_path, dimension, relative):
    props = {"axis": (8, "z")}
    root = chunk(-1, -1, [section(-1, [{"Name": (8, "test:log"), "Properties": (10, props)}])])
    region_file(tmp_path / relative, root, cx=-1, cz=-1)
    points = [(-1, -1, -1), (-16, -16, -16), (-8, -7, -6)]
    result = saved.read_saved_blocks(tmp_path, dimension, points, is_example=True)
    assert result["blocks"] == [{"position": dict(zip(("x", "y", "z"), p)),
                                 "block_id": "test:log", "properties": {"axis": "z"}} for p in points]
    assert result["is_example"] and len(result["sources"]) == 1
    assert all(result[k] is False for k in ("snapshot_consistency_proven", "action_causality_proven",
                                          "registry_membership_verified", "scoring_provenance_supported"))


def test_padding_word_boundary_unsigned_word_and_axis_order():
    # 17 entries use five bits, twelve entries per word (four unused high bits).
    # Known words exercise x=11/12, z=1 and y=1, not a mirrored packing routine.
    palette = [{"Name": (8, f"test:block_{i}")} for i in range(17)]
    words = [0] * 342
    words[0] = 0xF800000000000000  # index 11 = 16; high padding bits do not count.
    words[1] = 1 | (2 << 20)  # index 12 = 1; index 16 = 2.
    words[21] = 3 << 20  # index 256 = 3.
    raw = root_bytes(chunk(sections=[section(palette=palette, words=words)]))
    result = saved.block_states(raw, 0, 0, [(11, 0, 0), (12, 0, 0), (0, 0, 1), (0, 1, 0)])
    assert [x["block_id"] for x in result] == ["test:block_16", "test:block_1", "test:block_2", "test:block_3"]


@pytest.mark.parametrize("size,bits,long_count", [(2, 4, 256), (16, 4, 256), (17, 5, 342),
    (33, 6, 410), (65, 7, 456), (129, 8, 512), (257, 9, 586), (513, 10, 683),
    (1025, 11, 820), (2049, 12, 820), (4096, 12, 820)])
def test_serialized_local_palette_widths(size, bits, long_count):
    palette = [{"Name": (8, f"test:block_{i}")} for i in range(size)]
    words = [0] * long_count
    words[0] = (size - 1) << bits
    raw = root_bytes(chunk(sections=[section(palette=palette, words=words)]))
    assert saved.block_states(raw, 0, 0, [(1, 0, 0)])[0]["block_id"] == f"test:block_{size - 1}"


@pytest.mark.parametrize("field,value,code", [
    ("DataVersion", (3, 3121), "SAVED_VERSION_UNSUPPORTED"),
    ("DataVersion", (8, "3120"), "SAVED_CHUNK_FIELD_INVALID"),
    ("xPos", (3, 1), "SAVED_CHUNK_COORDINATE_MISMATCH"),
    ("zPos", (3, -1), "SAVED_CHUNK_COORDINATE_MISMATCH"),
    ("Status", (8, "light"), "SAVED_CHUNK_INCOMPLETE"),
    ("Status", (8, "minecraft:full"), "SAVED_CHUNK_INCOMPLETE"),
    ("sections", (9, (10, [])), "SAVED_SECTION_MISSING"),
    ("sections", (9, (10, [section(), section()])), "SAVED_SECTION_DUPLICATE"),
    ("sections", (9, (10, [{"Y": (1, 0)}])), "SAVED_SECTION_MISSING"),
    ("sections", (9, (8, [])), "SAVED_SECTION_INVALID")])
def test_wrong_version_location_status_and_missing_sections_are_not_air(field, value, code):
    root = chunk()
    root[field] = value
    with pytest.raises(Fault, match=f"^{code}$"):
        saved.block_states(root_bytes(root), 0, 0, [(0, 0, 0)])


@pytest.mark.parametrize("case,code", [
    ("singleton_data", "SAVED_PALETTE_DATA_INVALID"), ("short", "SAVED_PALETTE_DATA_INVALID"),
    ("long", "SAVED_PALETTE_DATA_INVALID"), ("hidden_bad_index", "SAVED_PALETTE_INDEX_INVALID"),
    ("extra_palette_field", "SAVED_PALETTE_UNSUPPORTED"), ("name", "SAVED_PALETTE_INVALID"),
    ("property", "SAVED_PALETTE_INVALID"), ("empty", "SAVED_PALETTE_INVALID")])
def test_palette_integrity_including_unrequested_positions(case, code):
    palette = [{"Name": (8, "minecraft:air")}, {"Name": (8, "minecraft:stone")}]
    words = [0] * 256
    if case == "singleton_data":
        palette.pop()
    elif case == "short":
        words.pop()
    elif case == "long":
        words.append(0)
    elif case == "hidden_bad_index":
        words[-1] = 15 << 60
    elif case == "extra_palette_field":
        palette[0]["unknown"] = (8, "private")
    elif case == "name":
        palette[0]["Name"] = (8, "bad namespace:name")
    elif case == "property":
        palette[0]["Properties"] = (10, {"bad": (3, 1)})
    states = section(palette=palette, words=words)
    if case == "empty":
        states["block_states"][1]["palette"] = (9, (10, []))
    with pytest.raises(Fault, match=f"^{code}$"):
        saved.block_states(root_bytes(chunk(sections=[states])), 0, 0, [(0, 0, 0)])


def test_modified_utf8_and_unrelated_nbt_arrays():
    value = {"text": (8, "nul\0 astral\U0001f600 lone\ud800")}
    raw = root_bytes(value)
    assert saved.NbtReader(raw).root()["text"].value == value["text"][1]
    for kind, width in [(7, 1), (11, 4), (12, 8)]:
        raw = b"\x0a\0\0" + bytes([kind]) + string("a") + struct.pack(">i", 2) + b"\xff" * (2 * width) + b"\0"
        assert bytes(saved.NbtReader(raw).root()["a"].value) == b"\xff" * (2 * width)


@pytest.mark.parametrize("raw,code", [
    (b"\x01\0\0\0", "SAVED_NBT_ROOT_INVALID"),
    (b"\x0a\0\x01x\0", "SAVED_NBT_ROOT_INVALID"),
    (b"\x0a\0\0\0extra", "SAVED_NBT_TRAILING_DATA"),
    (b"\x0a\0\0\x08\0\x01x\0\x04\xf0\x9f\x98\x80\0", "SAVED_NBT_STRING_INVALID"),
    (b"\x0a\0\0\x08\0\x01x\0\x01\x80\0", "SAVED_NBT_STRING_INVALID"),
    (b"\x0a\0\0\x07\0\0\xff\xff\xff\xff\0", "SAVED_NBT_QUOTA"),
    (b"\x0a\0\0\x09\0\0\0\0\0\0\x01\0", "SAVED_NBT_TYPE_INVALID"),
    (b"\x0a\0\0\x0d\0\0\0", "SAVED_NBT_TYPE_INVALID"),
    (b"\x0a\0\0\x01\0\x01x\0\x01\0\x01x\0\0", "SAVED_NBT_DUPLICATE_KEY")])
def test_malformed_nbt_is_typed(raw, code):
    with pytest.raises(Fault, match=f"^{code}$"):
        saved.NbtReader(raw).root()


def test_truncation_at_every_byte_and_depth_node_limits(monkeypatch):
    raw = root_bytes(chunk())
    for end in range(len(raw)):
        with pytest.raises(Fault):
            saved.NbtReader(raw[:end]).root()
    deep = {}
    for _ in range(66):
        deep = {"nested": (10, deep)}
    with pytest.raises(Fault, match="SAVED_NBT_QUOTA"):
        saved.NbtReader(root_bytes(deep)).root()
    monkeypatch.setattr(saved, "MAX_TAGS", 4)
    with pytest.raises(Fault, match="SAVED_NBT_QUOTA"):
        saved.NbtReader(raw).root()


@pytest.mark.parametrize("compression", [1, 2])
def test_compression_truncation_trailing_concatenation_and_expansion(compression, monkeypatch):
    encode = gzip.compress if compression == 1 else zlib.compress
    payload = encode(root_bytes(chunk()))
    for bad in (payload[:-1], payload + b"x", payload + payload, b"broken"):
        with pytest.raises(Fault, match="SAVED_CHUNK_COMPRESSION_INVALID"):
            saved.unpack_chunk(bad, compression)
    monkeypatch.setattr(saved, "MAX_NBT", 64)
    with pytest.raises(Fault, match="SAVED_NBT_QUOTA"):
        saved.unpack_chunk(encode(b"x" * 65), compression)
    with pytest.raises(Fault, match="SAVED_COMPRESSION_UNSUPPORTED"):
        saved.unpack_chunk(payload, 4)


@pytest.mark.parametrize("case,code", [
    ("short", "SAVED_REGION_INVALID"), ("unaligned", "SAVED_REGION_INVALID"),
    ("header_overlap", "SAVED_REGION_LOCATION_INVALID"), ("zero_sectors", "SAVED_REGION_LOCATION_INVALID"),
    ("past_eof", "SAVED_REGION_LOCATION_INVALID"), ("overlap", "SAVED_REGION_OVERLAP"),
    ("missing", "SAVED_CHUNK_MISSING"), ("zero_length", "SAVED_CHUNK_LENGTH_INVALID"),
    ("long_length", "SAVED_CHUNK_LENGTH_INVALID"), ("compression", "SAVED_COMPRESSION_UNSUPPORTED"),
    ("external_conflict", "SAVED_CHUNK_STREAM_CONFLICT")])
def test_region_envelope_corruption(tmp_path, case, code):
    path, _ = region_file(tmp_path)
    raw = bytearray(path.read_bytes())
    if case == "short":
        raw = raw[:4096]
    elif case == "unaligned":
        raw.append(0)
    elif case in ("header_overlap", "zero_sectors", "past_eof", "missing"):
        struct.pack_into(">I", raw, 0, {"header_overlap": 257, "zero_sectors": 512,
                                      "past_eof": 769, "missing": 0}[case])
    elif case == "overlap":
        struct.pack_into(">I", raw, 4, 513)
    elif case in ("zero_length", "long_length"):
        struct.pack_into(">I", raw, 8192, 0 if case == "zero_length" else 4093)
    elif case == "compression":
        raw[8196] = 4
    elif case == "external_conflict":
        raw[8196] = 130
    path.write_bytes(raw)
    with pytest.raises(Fault, match=f"^{code}$"):
        saved.read_region(path, 0, 0)


def test_missing_external_stream_wrong_region_and_io_failure(tmp_path):
    path, _ = region_file(tmp_path, external=True)
    (tmp_path / "c.0.0.mcc").unlink()
    with pytest.raises(Fault, match="SAVED_SOURCE_UNAVAILABLE"):
        saved.read_region(path, 0, 0)
    with pytest.raises(Fault, match="SAVED_REGION_COORDINATE_MISMATCH"):
        saved.read_region(path, 32, 0)


def test_detected_source_change_rejects_result(tmp_path, monkeypatch):
    path, _ = region_file(tmp_path)
    real_stat = saved.stable_signature
    calls = []

    def changed(value):
        calls.append(1)
        return (*real_stat(value), len(calls))

    monkeypatch.setattr(saved, "stable_signature", changed)
    with pytest.raises(Fault, match="SAVED_SOURCE_CHANGED"):
        saved.read_region(path, 0, 0)


@pytest.mark.parametrize("dimension,points,code", [
    ("test:../escape", [(0, 0, 0)], "UNSAFE_PATH"), ("test:dir/", [(0, 0, 0)], "UNSAFE_PATH"),
    ("test:dir.", [(0, 0, 0)], "UNSAFE_PATH"), ("test:con", [(0, 0, 0)], "UNSAFE_PATH"),
    ("test:bad\\path", [(0, 0, 0)], "SAVED_DIMENSION_INVALID"),
    ("test:ok", [], "SAVED_POINT_QUOTA"), ("test:ok", [(0, 0, 0)] * 257, "SAVED_POINT_QUOTA"),
    ("test:ok", [(0, 0, 0)] * 2, "SAVED_POSITION_DUPLICATE"),
    ("test:ok", [(True, 0, 0)], "SAVED_POSITION_INVALID"),
    ("test:ok", [(0, -2049, 0)], "SAVED_POSITION_INVALID"),
    ("test:ok", [(30000001, 0, 0)], "SAVED_POSITION_INVALID")])
def test_paths_and_point_quotas(tmp_path, dimension, points, code):
    with pytest.raises(Fault, match=f"^{code}$"):
        saved.read_saved_blocks(tmp_path, dimension, points, is_example=True)


def test_reference_cumulative_byte_bound(tmp_path, monkeypatch):
    _, raw = region_file(tmp_path / "region")
    monkeypatch.setattr(saved, "MAX_TOTAL_NBT", len(raw) - 1)
    with pytest.raises(Fault, match="SAVED_REFERENCE_QUOTA"):
        saved.read_saved_blocks(tmp_path, "minecraft:overworld", [(0, 0, 0)], is_example=True)


def test_linked_world_rejected_before_read(tmp_path, monkeypatch):
    # Injection makes this portable without asking Windows for symlink privileges.
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda p: p == tmp_path or real(p))
    import stat
    info = tmp_path.lstat()
    from types import SimpleNamespace
    real_lstat = Path.lstat
    monkeypatch.setattr(Path, "lstat", lambda p: SimpleNamespace(st_mode=stat.S_IFLNK)
                        if p == tmp_path else real_lstat(p))
    assert info
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        saved.read_saved_blocks(tmp_path, "minecraft:overworld", [(0, 0, 0)], is_example=True)
