"""Menu input contract only; no native or Minecraft effects supplied."""

import pytest

from mcbench.contracts import QuestMenuAction


@pytest.mark.parametrize(("operation", "direction"), [("back", None), ("scroll", "up"), ("scroll", "down")])
def test_menu_actions_bind_current_menu_and_exact_one_step(operation, direction):
    action = {"kind": "quest_menu", "operation": operation, "direction": direction, "source": "ftb_quests",
              "source_generation": 1, "expected_menu_generation": 2, "expected_menu_revision": 3}
    assert QuestMenuAction.model_validate(action).model_dump() == action
    for patch in [{"operation": "submit"}, {"direction": 1}, {"direction": "left"}, {"steps": 200},
                  {"source_generation": True}, {"expected_menu_generation": -1}, {"expected_menu_revision": 1.5},
                  {"source": "admin"}, {"team_id": "private"},
                  {"direction": "down" if operation == "back" else None}]:
        with pytest.raises(ValueError):
            QuestMenuAction.model_validate(action | patch)
