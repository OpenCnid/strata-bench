"""Synthetic choice response validation; no live menu or reward authority."""
import copy

import pytest

from mcbench.native_game import GameQuestMenu


@pytest.mark.parametrize("case", ["visible", "empty", "item_kind", "task_context", "both_contexts", "item_row",
    "controls", "table", "raw_index", "weight", "command", "enabled", "title", "tooltip", "rich", "index", "old_policy", "old_choice_policy"])
def test_choice_menu_is_visible_shape_only(case):
    row = {"index": 0, "title": "Visible choice", "enabled": True, "tooltip": [{"kind": "text", "text": "Visible"}]}
    page = {"schema": "strata/NativeQuestMenu/1", "body_fingerprint": "a" * 64, "connection_generation": 1,
        "query": {"source": "ftb_quests", "after": 0}, "source_generation": 1, "menu_generation": 1, "revision": 1,
        "policy": "ftb-current-item-choice-clipped-pages32/4", "menu_kind": "reward_choices",
        "context": {"chapter_id": "0000000000000001", "quest_id": "0000000000000002", "reward_id": "0000000000000003", "title": "Choose"},
        "controls": [], "entries": [row], "next_cursor": None}
    if case == "empty":
        page["entries"] = []
    elif case == "item_kind":
        page["menu_kind"] = "item_alternatives"
    elif case == "task_context":
        page["context"]["task_id"] = page["context"].pop("reward_id")
    elif case == "both_contexts":
        page["context"]["task_id"] = page["context"]["reward_id"]
    elif case == "item_row":
        page["entries"] = [{"index": 0, "item_id": "minecraft:stone", "count": 1, "name": "Stone", "tooltip": []}]
    elif case == "controls":
        page["controls"] = [{"control": "submit", "title": "Submit", "enabled": True, "tooltip": []}]
    elif case in {"table", "raw_index", "weight", "command"}:
        row[case] = "private"
    elif case == "enabled":
        row["enabled"] = 1
    elif case == "title":
        row["title"] = "x" * 1025
    elif case == "tooltip":
        row["tooltip"] *= 65
    elif case == "rich":
        row["tooltip"] = [{"kind": "unsupported", "text": "private"}]
    elif case == "index":
        row["index"] = 1
    elif case == "old_policy":
        page["policy"] = "ftb-current-item-alternatives-clipped-pages32/2"
    elif case == "old_choice_policy":
        page["policy"] = "ftb-current-item-choice-clipped-pages32/3"
    original = copy.deepcopy(page)
    if case in {"visible", "empty"}:
        assert GameQuestMenu.model_validate(page).model_dump(by_alias=True) == original
    else:
        with pytest.raises(ValueError):
            GameQuestMenu.model_validate(page)
