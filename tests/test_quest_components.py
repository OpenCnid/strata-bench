"""Synthetic own-quest displays; native FTB tooltip/claim parity remains unverified."""
import copy
import json

import pytest

from mcbench.contracts import RpcRequest
from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault
from test_native_game import connection, response


@pytest.mark.parametrize("case", ["task", "reward", "rich", "private", "id", "kind", "task_null", "reward_extra",
    "boolean", "progress", "claim", "rich_leak", "page_break", "unicode", "tooltip_count", "entry_bytes", "echo",
    "cursor", "duplicate", "policy"])
def test_quest_components_strict_visibility_shape_and_no_replay(monkeypatch, case):
    reward = case in {"reward", "claim"}
    query = {"source": "ftb_quests", "chapter_id": "0000000000000001", "quest_id": "0000000000000002",
             "part": "rewards" if reward else "tasks", "after": 0}
    row = {"entry_id": "0000000000000003", "kind": "reward" if reward else "task", "title": "Visible entry",
           "tooltip": [{"kind": "text", "text": "Ordinary tooltip"}],
           "task": None if reward else {"completed": False, "optional": False, "progress_label": "2 / 4"},
           "reward": {"claim_state": "cannot_claim", "team_reward": False} if reward else None}
    page = {"schema": "strata/NativeQuestComponents/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
            "query": copy.deepcopy(query), "source_generation": 1,
            "policy": "ftb-visible-own-quest-task-reward-tooltips-pages32/1", "revision": 1, "entries": [row], "next_cursor": None}
    if case == "rich":
        row["tooltip"] = [{"kind": "unsupported", "text": None}]
    elif case == "private":
        row["command"] = "server-only reward command"
    elif case == "id":
        row["entry_id"] += "\n"
    elif case == "kind":
        row["kind"] = "reward"
    elif case == "task_null":
        row["task"] = None
    elif case == "reward_extra":
        row["reward"] = {"claim_state": "claimed", "team_reward": True}
    elif case == "boolean":
        row["task"]["completed"] = 1
    elif case == "progress":
        row["task"]["progress_label"] = "x" * 257
    elif case == "claim":
        row["reward"]["claim_state"] = "admin_complete"
    elif case == "rich_leak":
        row["tooltip"] = [{"kind": "unsupported", "text": "private raw component"}]
    elif case == "page_break":
        row["tooltip"] = [{"kind": "page_break", "text": None}]
    elif case == "unicode":
        row["title"] = "\ud800"
    elif case == "tooltip_count":
        row["tooltip"] *= 65
    elif case == "entry_bytes":
        row["tooltip"] = [{"kind": "text", "text": "😀" * 4096}]
    elif case == "echo":
        page["query"]["quest_id"] = "0000000000000004"
    elif case == "cursor":
        page["next_cursor"] = 2
    elif case == "duplicate":
        page["entries"] *= 2
    elif case == "policy":
        page["policy"] = "all-server-data"
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "quest_components" and request["args"] == query
        calls.append(method)
        return response(request, result=page)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if case in {"task", "reward", "rich"}:
        assert client.call("quest_components", query) == page
    else:
        with pytest.raises(Fault):
            client.call("quest_components", query)
    assert calls == ["POST"]
    for patch in [{"team_id": "sibling"}, {"part": "server_commands"}, {"chapter_id": None},
                  {"quest_id": query["quest_id"] + "\n"}, {"after": True}, {"after": 513}]:
        with pytest.raises(ValueError):
            client.call("quest_components", query | patch)
    assert calls == ["POST"]
    rpc = {"schema": "strata/GameRequest/1", "request_id": "quest", "campaign_id": "campaign", "agent_id": "avatar",
           "epoch": 1, "deadline_at": "2026-09-19T00:00:00Z", "method": "quests.components", "quest_components_query": query,
           "action": None, "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(rpc).quest_components_query.part == query["part"]
    for patch in [{"method": "quests.text"}, {"quest_components_query": None}, {"after": 0}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(rpc | patch)
