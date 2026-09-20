"""Synthetic contract checks; no task or Minecraft authority is supplied."""

import pytest

from mcbench.contracts import QuestTask


def test_task_open_requires_a_visible_task_page_and_screen_binding():
    selection = {"query": {"source": "ftb_quests", "chapter_id": "0000000000000001", "quest_id": "0000000000000002", "part": "tasks", "after": 0},
                 "revision": 1, "entry_id": "0000000000000003"}
    action = {"kind": "quest_task", "operation": "open", "source": "ftb_quests", "source_generation": 1,
              "expected_screen_generation": 2, "expected_screen_revision": 3, "selection": selection}
    assert QuestTask.model_validate(action).model_dump() == action
    for patch in [{"operation": "submit"}, {"source": "admin"}, {"team_id": "private"}, {"selection": None},
                  {"source_generation": True}, {"expected_screen_generation": 1.0}, {"expected_screen_revision": -1},
                  {"selection": selection | {"query": selection["query"] | {"part": "rewards"}}},
                  {"selection": selection | {"entry_id": selection["entry_id"] + "\n"}},
                  {"selection": selection | {"query": selection["query"] | {"after": 513}}},
                  {"selection": selection | {"include_hidden": True}}]:
        with pytest.raises(ValueError):
            QuestTask.model_validate(action | patch)
