"""Synthetic quest text and hidden-content rejection; not authentic FTB conformance."""
import copy
import json

import pytest

from mcbench.contracts import RpcRequest
from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault
from test_native_game import connection, response


@pytest.mark.parametrize("case", ["visible", "locked", "rich", "hidden", "private", "subtitle", "line_size", "unicode",
    "line_kind", "line_null", "rich_leak", "cursor", "empty_cursor", "echo", "policy", "boolean", "too_many", "newline"])
def test_quest_text_transport_and_scoped_contract(monkeypatch, case):
    query = {"source": "ftb_quests", "chapter_id": "0000000000000001", "quest_id": "0000000000000002", "after": 0}
    page = {"schema": "strata/NativeQuestText/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
            "query": copy.deepcopy(query), "source_generation": 1, "policy": "ftb-visible-own-quest-plain-text-pages32/1",
            "revision": 1, "title": "Visible quest", "subtitle": "Public subtitle", "description_visible": True,
            "lines": [{"kind": "text", "text": "Readable description"}], "next_cursor": None}
    if case == "locked":
        page.update(description_visible=False, lines=[])
    elif case == "rich":
        page["lines"] = [{"kind": "page_break", "text": None}, {"kind": "unsupported", "text": None}]
    elif case == "hidden":
        page["description_visible"] = False
    elif case == "private":
        page["team_id"] = "sibling"
    elif case == "subtitle":
        page["subtitle"] = "x" * 1025
    elif case == "line_size":
        page["lines"][0]["text"] = "x" * 4097
    elif case == "unicode":
        page["lines"][0]["text"] = "\ud800"
    elif case == "line_kind":
        page["lines"][0]["kind"] = "raw_nbt"
    elif case == "line_null":
        page["lines"][0]["text"] = None
    elif case == "rich_leak":
        page["lines"][0]["kind"] = "unsupported"
    elif case == "cursor":
        page["next_cursor"] = 2
    elif case == "empty_cursor":
        page.update(lines=[], next_cursor=0)
    elif case == "echo":
        page["query"]["quest_id"] = "0000000000000003"
    elif case == "policy":
        page["policy"] = "all-text"
    elif case == "boolean":
        page["description_visible"] = 1
    elif case == "too_many":
        page["lines"] *= 33
    elif case == "newline":
        page["query"]["quest_id"] += "\n"
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "quest_text" and request["args"] == query
        calls.append(method)
        return response(request, result=page)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if case in {"visible", "locked", "rich"}:
        assert client.call("quest_text", query) == page
    else:
        with pytest.raises(Fault):
            client.call("quest_text", query)
    assert calls == ["POST"]
    for patch in [{"team_id": "sibling"}, {"source": "server"}, {"chapter_id": None}, {"quest_id": query["quest_id"] + "\n"},
                  {"after": True}, {"after": 513}]:
        with pytest.raises(ValueError):
            client.call("quest_text", query | patch)
    assert calls == ["POST"]
    rpc = {"schema": "strata/GameRequest/1", "request_id": "quest", "campaign_id": "campaign", "agent_id": "avatar",
           "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "quests.text", "quest_text_query": query,
           "action": None, "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(rpc).quest_text_query.quest_id == query["quest_id"]
    for patch in [{"method": "quests.list"}, {"quest_text_query": None}, {"after": 0}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(rpc | patch)
