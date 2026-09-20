"""Strict public selectors only; no native game or rendered input qualification."""
import pytest

from mcbench.contracts import RecipeNavigate


def action():
    return {"kind": "recipe_navigate", "source": "jei", "control": "page_next", "source_generation": 1,
            "expected_screen_generation": 2, "expected_screen_revision": 3, "expected_page_revision": "a" * 64}


@pytest.mark.parametrize("control", ["category_next", "category_previous", "page_next", "page_previous", "history_back"])
def test_navigation_selectors_round_trip(control):
    value = action() | {"control": control}
    assert RecipeNavigate.model_validate(value).model_dump() == value


@pytest.mark.parametrize("patch", [
    {"source": "recipe_manager"}, {"control": "history"}, {"control": "close"}, {"control": "page_next\n"},
    {"mouse_x": 10}, {"widget": "private"}, {"source_generation": True}, {"source_generation": "1"},
    {"expected_screen_generation": -1}, {"expected_screen_revision": 1.0}, {"expected_screen_revision": 2**53},
    {"expected_page_revision": "a" * 64 + "\n"}, {"expected_page_revision": "A" * 64},
    {"expected_page_revision": None}, {"expected_page_revision": "a" * 63}, {"button": 0},
])
def test_invalid_or_private_selectors_cannot_enter_action(patch):
    with pytest.raises(ValueError):
        RecipeNavigate.model_validate(action() | patch)


@pytest.mark.parametrize("field", list(action()))
def test_every_selector_and_revision_is_required(field):
    value = action()
    del value[field]
    with pytest.raises(ValueError):
        RecipeNavigate.model_validate(value)
