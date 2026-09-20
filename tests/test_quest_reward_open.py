"""Synthetic contract checks; no task or Minecraft authority is supplied."""

import pytest

from mcbench.contracts import QuestReward


def test_reward_open_requires_a_visible_reward_page_and_screen_binding():
    selection = {"query": {"source": "ftb_quests", "chapter_id": "0000000000000001", "quest_id": "0000000000000002", "part": "rewards", "after": 0},
                 "revision": 1, "entry_id": "0000000000000003"}
    action = {"kind": "quest_reward", "operation": "open", "source": "ftb_quests", "source_generation": 1,
              "expected_screen_generation": 2, "expected_screen_revision": 3, "selection": selection}
    assert QuestReward.model_validate(action).model_dump() == action
    for patch in [{"operation": "submit"}, {"operation": "claim"}, {"choice_index": 2}, {"table_id": "private"},
                  {"source": "admin"}, {"team_id": "private"}, {"selection": None},
                  {"source_generation": True}, {"expected_screen_generation": 1.0}, {"expected_screen_revision": -1},
                  {"selection": selection | {"query": selection["query"] | {"part": "tasks"}}},
                  {"selection": selection | {"entry_id": selection["entry_id"] + "\n"}},
                  {"selection": selection | {"query": selection["query"] | {"after": 513}}},
                  {"selection": selection | {"include_hidden": True}}]:
        with pytest.raises(ValueError):
            QuestReward.model_validate(action | patch)
