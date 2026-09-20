"""Synthetic contract/UI responses; actual FTB navigation remains a live gate."""
import json

import pytest

from mcbench.contracts import QuestNavigate, RpcRequest
from mcbench.native_game import NativeGameClient
from mcbench.storage import Fault
from test_native_game import connection, response


def screen():
    return {"schema": "strata/NativeQuestScreen/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
            "policy": "ftb-own-team-book-and-task-recipes-state/2", "source_generation": 1, "screen_generation": 2,
            "revision": 3, "kind": "quest_book", "chapter_id": "0000000000000001", "quest_id": "0000000000000002"}


@pytest.mark.parametrize("patch", [{}, {"quest_id": None}, {"kind": "closed", "chapter_id": None, "quest_id": None},
    {"kind": "editor"}, {"kind": "closed"}, {"chapter_id": None}, {"quest_id": "0000000000000002\n"},
    {"screen_generation": True}, {"revision": -1}, {"source_generation": 2**53}, {"screen_object": "private"},
    {"policy": "unfiltered"}, {"body_fingerprint": "account-identifier"}, {"kind": "task_recipes"},
    {"kind": "task_recipes", "quest_id": None}, {"kind": "task_recipes", "chapter_id": None},
    {"policy": "ftb-own-team-book-state-navigation/1"}, {"focus": "hidden"}, {"parent_screen": "private"}])
def test_screen_response_scope_shape_and_no_retry(monkeypatch, patch):
    value = screen() | patch
    calls = []

    def exchange(method, path, body, timeout):
        request = json.loads(body)
        assert request["operation"] == "quest_screen" and request["args"] == {}
        calls.append(method)
        return response(request, result=value)

    client = NativeGameClient(connection())
    monkeypatch.setattr(client._transport, "_exchange", exchange)
    if patch in [{}, {"quest_id": None}, {"kind": "closed", "chapter_id": None, "quest_id": None}, {"kind": "task_recipes"}]:
        assert client.call("quest_screen", {}) == value
    else:
        with pytest.raises((Fault, ValueError)):
            client.call("quest_screen", {})
    assert calls == ["POST"]
    with pytest.raises(Fault):
        client.call("quest_screen", {"team_id": "sibling"})
    assert calls == ["POST"]


def test_navigation_contract_distinguishes_selection_and_back_close():
    base = {"kind": "quest_navigate", "operation": "back", "source": "ftb_quests", "source_generation": 1,
            "expected_screen_generation": 2, "expected_screen_revision": 3, "selection": None}
    assert QuestNavigate.model_validate(base).model_dump() == base
    select = {"query": {"source": "ftb_quests", "chapter_id": "0000000000000001", "after": 0},
              "revision": 1, "entry_id": "0000000000000002"}
    quest = base | {"operation": "quest", "selection": select}
    assert QuestNavigate.model_validate(quest).model_dump() == quest
    for patch in [{"selection": None}, {"operation": "close"}, {"operation": "chapter"}, {"operation": "claim"},
                  {"source_generation": True}, {"expected_screen_revision": -1}, {"expected_screen_generation": 1.0},
                  {"team_id": "private"}, {"selection": select | {"entry_id": select["entry_id"] + "\n"}}]:
        with pytest.raises(ValueError):
            QuestNavigate.model_validate(quest | patch)


def test_screen_rpc_cannot_carry_unrelated_queries():
    base = {"schema": "strata/GameRequest/1", "request_id": "screen", "campaign_id": "campaign", "agent_id": "avatar",
            "epoch": 1, "deadline_at": "2026-09-19T12:00:00Z", "method": "quests.screen", "action": None,
            "target_request_id": None, "after": None}
    assert RpcRequest.model_validate(base).method == "quests.screen"
    for patch in [{"after": 1}, {"quest_query": {"source": "ftb_quests", "chapter_id": None, "after": 0}},
                  {"quest_menu_query": {"source": "ftb_quests", "after": 0}}, {"team_id": "sibling"}]:
        with pytest.raises(ValueError):
            RpcRequest.model_validate(base | patch)
