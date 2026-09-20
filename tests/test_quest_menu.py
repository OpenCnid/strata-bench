"""Strict current-menu projections with synthetic data, not loaded FTB conformance."""
import copy
import json

import pytest

from mcbench.contracts import RpcRequest
from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault
from test_native_game import connection, response


@pytest.mark.parametrize("case", ["visible", "empty", "rich", "private", "context", "context_id", "kind", "generation", "policy",
    "index", "count", "item_id", "name", "raw", "line_count", "line_bytes", "unicode", "control", "enabled", "duplicate_control",
    "control_bytes", "cursor", "echo", "extra_entry"])
def test_menu_contract_is_current_scoped_bounded_and_never_retried(monkeypatch, case):
    query = {"source": "ftb_quests", "after": 0}
    row = {"index": 0, "item_id": "minecraft:stone", "count": 1, "name": "Stone", "tooltip": [{"kind": "text", "text": "Stone"}]}
    control = {"control": "submit", "title": "Submit", "enabled": False, "tooltip": []}
    page = {"schema": "strata/NativeQuestMenu/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
        "query": copy.deepcopy(query), "source_generation": 1, "menu_generation": 1, "revision": 1,
        "policy": "ftb-current-item-choice-clipped-pages32/4", "menu_kind": "item_alternatives",
        "context": {"chapter_id": "0000000000000001", "quest_id": "0000000000000002", "task_id": "0000000000000003", "title": "Valid items"},
        "controls": [control], "entries": [row], "next_cursor": None}
    if case == "empty":
        page["entries"] = []
    elif case == "rich":
        row["tooltip"] = [{"kind": "unsupported", "text": None}]
    elif case == "private":
        page["parent_screen"] = "hidden identity"
    elif case == "context":
        page["context"]["team_id"] = "sibling"
    elif case == "context_id":
        page["context"]["task_id"] += "\n"
    elif case == "kind":
        page["menu_kind"] = "server_reward_table"
    elif case == "generation":
        page["menu_generation"] = 0
    elif case == "policy":
        page["policy"] = "all-items"
    elif case == "index":
        row["index"] = 1
    elif case == "count":
        row["count"] = True
    elif case == "item_id":
        row["item_id"] += "\n"
    elif case == "name":
        row["name"] = "x" * 1025
    elif case == "raw":
        row["nbt"] = {"private": True}
    elif case == "line_count":
        row["tooltip"] *= 65
    elif case == "line_bytes":
        row["tooltip"] = [{"kind": "text", "text": "😀" * 4096}]
    elif case == "unicode":
        page["context"]["title"] = "\ud800"
    elif case == "control":
        control["control"] = "admin_submit"
    elif case == "enabled":
        control["enabled"] = 1
    elif case == "duplicate_control":
        page["controls"] *= 2
    elif case == "control_bytes":
        control["tooltip"] = [{"kind": "text", "text": "x" * 4096}] * 2
    elif case == "cursor":
        page["next_cursor"] = 2
    elif case == "echo":
        page["query"]["after"] = 1
    elif case == "extra_entry":
        page["entries"] *= 2
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["args"] == query and request["operation"] == "quest_menu"
        calls.append(method)
        return response(request, result=page)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if case in {"visible", "empty", "rich"}:
        assert client.call("quest_menu", query) == page
    else:
        with pytest.raises(Fault):
            client.call("quest_menu", query)
    assert calls == ["POST"]
    for patch in [{"team_id": "sibling"}, {"task_id": "hidden"}, {"source": "server"}, {"after": True}, {"after": -1}, {"after": 513}]:
        with pytest.raises(ValueError):
            client.call("quest_menu", query | patch)
    assert calls == ["POST"]
    rpc = {"schema": "strata/GameRequest/1", "request_id": "menu", "campaign_id": "campaign", "agent_id": "avatar",
           "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "quests.menu", "quest_menu_query": query,
           "action": None, "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(rpc).quest_menu_query.after == 0
    for patch in [{"method": "observe"}, {"quest_menu_query": None}, {"after": 0}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(rpc | patch)
