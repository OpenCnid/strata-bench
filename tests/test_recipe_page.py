"""Synthetic current-page payloads; authentic JEI visibility remains unqualified."""

import copy
import hashlib

import pytest

from mcbench.contracts import RpcRequest
from mcbench.native_game import GameRecipePage
from mcbench.storage import Fault, canonical


def page():
    content = {"policy": "jei-task-drawn-slot-header-controls-empty-loop/4", "source": "jei", "coverage": "slot_header_control_draw_operands", "complete": False,
               "source_generation": 1, "screen_generation": 2, "screen_revision": 3,
               "chapter_id": "0000000000000001", "quest_id": "0000000000000002",
               "headers": [{"kind": "category", "state": "text", "text": "Visible café <&> \"title\" \\u2028 \u2028\u2029 😀"},
                           {"kind": "page", "state": "text", "text": "1/4"}],
               "controls": [{"kind": kind, "state": state} for kind, state in zip(
                   ("category_next", "category_previous", "page_next", "page_previous"), ("enabled", "disabled", "clipped", "clipped"))],
               "layouts": [{"category_id": "minecraft:crafting", "clipped": False, "slots": [
                   {"index": 0, "role": "input", "display": {"kind": "item", "id": "minecraft:stone", "amount": 2}},
                   {"index": 1, "role": "output", "display": {"kind": "fluid", "id": "minecraft:water", "amount": 1000}},
                   {"index": 2, "role": "catalyst", "display": {"kind": "unsupported"}},
                   {"index": 3, "role": "render_only", "display": {"kind": "empty"}},
               ]}]}
    return {"schema": "strata/NativeRecipePage/4", "body_fingerprint": "a" * 64, "connection_generation": 1,
            **content, "revision": hashlib.sha256(canonical(content)).hexdigest()}


def rehash(value):
    content = {key: item for key, item in value.items() if key not in {"schema", "body_fingerprint", "connection_generation", "revision"}}
    value["revision"] = hashlib.sha256(canonical(content)).hexdigest()
    return value


def test_partial_page_roundtrip_and_explicit_clipping():
    value = page()
    assert GameRecipePage.model_validate(value).model_dump(mode="json", by_alias=True) == value
    value["layouts"][0]["slots"][3]["index"] = 7
    value["layouts"][0]["clipped"] = True
    assert GameRecipePage.model_validate(rehash(value)).layouts[0].slots[3].index == 7


def test_empty_page_requires_new_policy_full_headers_controls_and_matching_digest():
    value = page() | {"layouts": []}
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(value)
    rehash(value)
    assert GameRecipePage.model_validate(value).layouts == []
    for patch in ({"headers": []}, {"controls": []}, {"schema": "strata/NativeRecipePage/3"},
                  {"policy": "jei-task-drawn-slot-header-controls/3"}):
        with pytest.raises((ValueError, Fault)):
            GameRecipePage.model_validate(rehash(value | patch))


@pytest.mark.parametrize("patch", [
    {"complete": True}, {"complete": 0}, {"coverage": "complete"}, {"policy": "old"},
    {"source": "private"}, {"chapter_id": None}, {"quest_id": "0000000000000002\n"},
    {"source_generation": -1}, {"screen_revision": True}, {"screen_generation": 2**53},
    {"focus": "private"}, {"layouts": None}, {"schema": "strata/NativeRecipePage/0"},
])
def test_malformed_page_headers_rejected_even_with_matching_digest(patch):
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(rehash(page() | patch))


@pytest.mark.parametrize("display", [
    {"kind": "empty", "id": "private:value"}, {"kind": "unsupported", "raw": "private"},
    {"kind": "item", "id": "minecraft:stone", "amount": 0},
    {"kind": "item", "id": "minecraft:stone", "amount": True},
    {"kind": "fluid", "id": "minecraft:water", "amount": 2147483648},
    {"kind": "item", "id": "minecraft:stone\n", "amount": 1},
    {"kind": "component", "id": "private:secret", "amount": 1},
])
def test_malformed_or_raw_slot_payloads_rejected(display):
    value = page()
    value["layouts"][0]["slots"][0]["display"] = display
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(rehash(value))


def test_bounds_order_and_content_tampering():
    for mutation in ("duplicate", "gap", "category", "layout_limit", "slot_limit", "digest", "bytes"):
        value = page()
        layout = value["layouts"][0]
        if mutation == "duplicate":
            layout["slots"][1]["index"] = 0
        elif mutation == "gap":
            layout["slots"][3]["index"] = 7
        elif mutation == "category":
            layout["category_id"] += "\n"
        elif mutation == "layout_limit":
            value["layouts"] *= 33
        elif mutation == "slot_limit":
            layout["slots"] *= 33
        elif mutation == "bytes":
            layout["slots"] = [{"index": i, "role": "input", "display": {
                "kind": "item", "id": "minecraft:" + "x" * 220, "amount": 1}} for i in range(128)]
        rehash(value)
        if mutation == "digest":
            layout["slots"][0]["display"]["amount"] += 1
        with pytest.raises((ValueError, Fault)):
            GameRecipePage.model_validate(value)


def test_public_request_has_no_query_or_mutation_selector():
    request = {"schema": "strata/GameRequest/1", "request_id": "request", "campaign_id": "campaign", "agent_id": "avatar",
               "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "recipes.page", "action": None,
               "target_request_id": None, "after": None, "cursor": None}
    RpcRequest.model_validate(request)
    for patch in ({"after": 0}, {"target_request_id": "private"}, {"team_id": "sibling"}, {"cursor": "private"}):
        with pytest.raises(ValueError):
            RpcRequest.model_validate(copy.deepcopy(request) | patch)


@pytest.mark.parametrize("headers", [
    [], [{"kind": "category", "state": "text", "text": "only one"}],
    [{"kind": "page", "state": "text", "text": "1/4"}, {"kind": "category", "state": "text", "text": "wrong order"}],
    [{"kind": "category", "state": "clipped", "text": "private"}, {"kind": "page", "state": "text", "text": "1/4"}],
    [{"kind": "category", "state": "text", "text": None}, {"kind": "page", "state": "text", "text": "1/4"}],
    [{"kind": "category", "state": "text", "text": "x" * 1025}, {"kind": "page", "state": "text", "text": "1/4"}],
    [{"kind": "category", "state": "text", "text": "ok", "full_title": "private"}, {"kind": "page", "state": "text", "text": "1/4"}],
])
def test_invalid_header_authority_shape_and_bounds(headers):
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(rehash(page() | {"headers": headers}))


def test_header_unicode_markers_and_lone_surrogate():
    value = page()
    value["headers"][0]["text"] = "😀" * 1024
    GameRecipePage.model_validate(rehash(value))
    for state in ("clipped", "unsupported"):
        value["headers"][0] = {"kind": "category", "state": state, "text": None}
        GameRecipePage.model_validate(rehash(value))
    value["headers"][0] = {"kind": "category", "state": "text", "text": "\ud800"}
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(value)


@pytest.mark.parametrize("change", ["missing", "extra", "order", "duplicate", "state", "coerced", "raw", "digest"])
def test_control_authority_order_schema_and_digest(change):
    value = page()
    controls = value["controls"]
    if change == "missing":
        controls.pop()
    elif change == "extra":
        controls.append(copy.deepcopy(controls[0]))
    elif change == "order":
        controls.reverse()
    elif change == "duplicate":
        controls[1]["kind"] = controls[0]["kind"]
    elif change == "state":
        controls[0]["state"] = "unknown"
    elif change == "coerced":
        controls[0]["state"] = ["enabled"]
    elif change == "raw":
        controls[0]["widget"] = "private"
    rehash(value)
    if change == "digest":
        controls[0]["state"] = "disabled"
    with pytest.raises((ValueError, Fault)):
        GameRecipePage.model_validate(value)
