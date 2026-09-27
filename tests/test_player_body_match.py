"""Synthetic whole-NBT equality/refusal tests; not live matching evidence."""
import copy
import gzip
import struct
import uuid

import pytest

from mcbench.storage import Fault
from strata_evaluator.player_body_match import body_fingerprint, compare_player_bodies
from test_probe_saved_bodies import PLAYER, payload, player
from test_saved_blocks import string


def raw(value):
    return gzip.decompress(payload(value))


def compare(a, b, identity=PLAYER):
    return compare_player_bodies(lambda _: a, lambda _: b, [identity])


def test_compound_order_is_not_state_but_original_bytes_are_retained():
    a = player()
    b = dict(reversed(list(a.items())))
    b["Inventory"][1][1][0]["tag"] = (10, {"custom": (8, "retained")})
    result = compare(raw(a), raw(b))
    assert result["save_format_state_equal"]
    row = result["members"][PLAYER]
    assert row["first"]["raw_sha256"] != row["second"]["raw_sha256"]
    assert row["first"]["typed_sha256"] == row["second"]["typed_sha256"]
    assert row["first"]["field_count"] == len(a)
    assert not any(result[k] for k in ("owned_producers_verified", "live_initial_state_verified",
                                      "transient_state_verified", "native_probe_admission"))


@pytest.mark.parametrize("change", ["item_tag", "selected", "mode", "health", "ability", "unknown", "missing", "type", "list_order"])
def test_no_saved_state_difference_is_ignored(change):
    a, b = player(), player()
    if change == "item_tag":
        b["Inventory"][1][1][0]["tag"][1]["custom"] = (8, "different")
    elif change == "selected":
        b["SelectedItemSlot"] = (3, 1)
    elif change == "mode":
        b["playerGameType"] = (3, 1)
    elif change == "health":
        b["Health"] = (5, 19.)
    elif change == "ability":
        b["AbilitiesExtension"][1]["custom"] = (1, 0)
    elif change == "unknown":
        b["unprojected"] = (10, {"data": (8, "private")})
    elif change == "missing":
        del b["SpawnX"]
    elif change == "type":
        b["foodLevel"] = (1, 20)
    else:
        b["Pos"] = (9, (6, list(reversed(b["Pos"][1][1]))))
    result = compare(raw(a), raw(b))
    assert not result["save_format_state_equal"]
    assert result["members"][PLAYER]["changed_fields"]


@pytest.mark.parametrize("kind,fmt,negative,positive", [(5, ">f", "80000000", "00000000"),
    (6, ">d", "8000000000000000", "0000000000000000"),
    (5, ">f", "7fc00001", "7fc00002"), (6, ">d", "7ff8000000000001", "7ff8000000000002")])
def test_float_zero_sign_and_nan_payloads_remain_distinct(kind, fmt, negative, positive):
    base = raw({"UUID": (11, uuid.UUID(PLAYER).bytes)})[:-1]
    prefix = bytes([kind]) + string("value")
    a, b = base + prefix + bytes.fromhex(negative) + b"\0", base + prefix + bytes.fromhex(positive) + b"\0"
    assert len(bytes.fromhex(negative)) == struct.calcsize(fmt)
    assert not compare(a, b)["save_format_state_equal"]
    assert compare(a, a)["save_format_state_equal"]


@pytest.mark.parametrize("kind,value,changed", [(2, b"\0\1", b"\0\2"), (4, b"\0"*7+b"\1", b"\0"*7+b"\2"),
    (7, struct.pack(">i", 2)+b"ab", struct.pack(">i", 2)+b"ac"),
    (12, struct.pack(">i", 1)+b"\0"*8, struct.pack(">i", 1)+b"\0"*7+b"\1")])
def test_additional_numeric_and_array_types_are_not_dropped(kind, value, changed):
    prefix = raw({"UUID": (11, uuid.UUID(PLAYER).bytes)})[:-1] + bytes([kind]) + string("private")
    assert compare(prefix+value+b"\0", prefix+value+b"\0")["save_format_state_equal"]
    assert not compare(prefix+value+b"\0", prefix+changed+b"\0")["save_format_state_equal"]


def test_nested_unicode_nul_and_unpaired_utf16_units_remain_comparable():
    a = player() | {"nested": (10, {"\ud800": (8, "\0\udfff😀")})}
    assert compare(raw(a), raw(copy.deepcopy(a)))["save_format_state_equal"]


def test_complete_two_body_roster_detects_second_body_only_change():
    second = "00000000-0000-4000-8000-000000000002"
    a = {PLAYER: raw(player()), second: raw(player() | {"UUID": (11, uuid.UUID(second).bytes)})}
    b = a | {second: raw(player() | {"UUID": (11, uuid.UUID(second).bytes), "Health": (5, 19.)})}
    result = compare_player_bodies(a.__getitem__, b.__getitem__, [PLAYER, second])
    assert not result["save_format_state_equal"] and result["members"][PLAYER]["equal"]
    assert result["members"][second]["changed_fields"] == ["Health"]


def test_diagnostic_bound_does_not_hide_late_differences_or_modify_nbt():
    from mcbench.storage import canonical
    a = player() | {str(i).zfill(4): (8, "before") for i in range(300)}
    b = player() | {str(i).zfill(4): (8, "after") for i in range(300)}
    result = compare(raw(a), raw(b))
    row = result["members"][PLAYER]
    assert not result["save_format_state_equal"] and row["changed_field_count"] == 300
    assert row["diagnostics_truncated"] and len(row["changed_fields"]) == 256
    assert len(canonical(result)) < 16000
    b = copy.deepcopy(a)
    b["0299"] = (8, "last-only")
    result = compare(raw(a), raw(b))
    assert not result["save_format_state_equal"]
    assert result["members"][PLAYER]["changed_fields"] == ["0299"]


def test_long_and_unpaired_root_names_have_bounded_serializable_diagnostics():
    from mcbench.storage import canonical
    names = ["long"*10000, "\ud800"]
    a = player() | {n: (8, "before") for n in names}
    b = player() | {n: (8, "after") for n in names}
    result = compare(raw(a), raw(b))
    assert not result["save_format_state_equal"]
    assert max(map(len, result["members"][PLAYER]["changed_fields"])) <= 196
    assert len(canonical(result)) < 3000


@pytest.mark.parametrize("roster", [[], [PLAYER, PLAYER], ["not-uuid"], [{}], ["ABCDEF00-0000-4000-8000-000000000001"]])
def test_invalid_rosters_refuse(roster):
    with pytest.raises(Fault, match="BODY_MATCH_ROSTER"):
        compare_player_bodies(lambda _: raw(player()), lambda _: raw(player()), roster)


@pytest.mark.parametrize("change", ["uuid", "truncated", "trailing", "oversize"])
def test_malformed_or_foreign_nbt_refuses(change):
    a = raw(player())
    if change == "uuid":
        a = raw(player() | {"UUID": (11, uuid.uuid4().bytes)})
    elif change == "truncated":
        a = a[:-1]
    elif change == "trailing":
        a += b"x"
    else:
        a = b"x"*(16*1024**2+1)
    with pytest.raises(Fault):
        body_fingerprint(a, PLAYER)
