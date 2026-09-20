"""Synthetic native quest catalog; authentic FTB UI/team isolation is not inferred."""
import copy
import json

import pytest

from mcbench.contracts import RpcRequest
from mcbench.native_game import NativeGameClient, QUEST_POLICY
from mcbench.storage import Fault
from test_native_game import connection, response


@pytest.mark.parametrize("case", ["root", "quest", "hidden", "sibling", "id", "kind", "progress", "complete",
    "boolean", "flags", "flags_null", "title", "unicode", "policy", "echo", "duplicate", "cursor", "id_newline"])
def test_native_quest_catalog_strict_boundaries_and_no_replay(monkeypatch, case):
    query = {"source": "ftb_quests", "chapter_id": None if case == "root" else "0000000000000001", "after": 0}
    row = {"kind": "chapter" if case == "root" else "quest", "entry_id": "0000000000000002", "title": "Visible quest",
           "progress_percent": 25, "completed": False, "startable": None if case == "root" else False,
           "details_visible": None if case == "root" else True}
    page = {"schema": "strata/NativeQuestPage/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
            "query": copy.deepcopy(query), "source_generation": 1, "policy": QUEST_POLICY, "revision": 1,
            "entries": [row], "next_cursor": None}
    if case == "hidden":
        row["description"] = "hidden canary"
    elif case == "sibling":
        row["team_id"] = "private sibling"
    elif case == "id":
        row["entry_id"] = "private-id"
    elif case == "id_newline":
        row["entry_id"] += "\n"
    elif case == "kind":
        row["kind"] = "chapter"
    elif case == "progress":
        row["progress_percent"] = 101
    elif case == "complete":
        row["completed"] = True
    elif case == "boolean":
        row["completed"] = 0
    elif case == "flags":
        row["startable"], row["details_visible"] = True, False
    elif case == "flags_null":
        row["startable"] = None
    elif case == "title":
        row["title"] = "x" * 1025
    elif case == "unicode":
        row["title"] = "\ud800"
    elif case == "policy":
        page["policy"] = "all-quests"
    elif case == "echo":
        page["query"]["chapter_id"] = "0000000000000003"
    elif case == "duplicate":
        page["entries"] *= 2
    elif case == "cursor":
        page["next_cursor"] = 2
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "quests" and request["args"] == query
        calls.append(method)
        return response(request, result=page)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if case in {"root", "quest"}:
        assert client.call("quests", query) == page
    else:
        with pytest.raises(Fault):
            client.call("quests", query)
    assert calls == ["POST"]
    for patch in [{"team_id": "sibling"}, {"source": "server"}, {"chapter_id": "*"}, {"chapter_id": "0000000000000001\n"}, {"after": True}, {"after": 4097}]:
        with pytest.raises(ValueError):
            client.call("quests", query | patch)
    assert calls == ["POST"]
    rpc = {"schema": "strata/GameRequest/1", "request_id": "quest", "campaign_id": "campaign", "agent_id": "avatar",
           "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "quests.list", "quest_query": query,
           "action": None, "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(rpc).quest_query.source == "ftb_quests"
    for patch in [{"method": "observe"}, {"quest_query": None}, {"after": 0}, {"quest_query": query | {"team_id": "sibling"}}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(rpc | patch)
