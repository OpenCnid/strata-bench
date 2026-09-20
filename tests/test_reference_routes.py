"""Public standing-footprint reference geometry; no native game qualification."""

import copy

import pytest

from mcbench.reference_routes import choose_cancel_target
from mcbench.storage import Fault


def cells():
    return {(x, y, z): "minecraft:grass_block" if y == 6 else "minecraft:air"
            for x in range(-5, 6) for z in range(-5, 6) for y in (6, 7, 8)}


@pytest.mark.parametrize("position,footprint", [
    ((.5, .5), [[0, 6, 0]]),
    ((.5, .067667867500754), [[0, 6, -1], [0, 6, 0]]),
    ((-.01, .01), [[-1, 6, -1], [-1, 6, 0], [0, 6, -1], [0, 6, 0]]),
    ((.7, .5), [[0, 6, 0]]),
    ((.70000000001, .5), [[0, 6, 0], [1, 6, 0]]),
])
def test_proves_swept_footprint_without_reducing_route_requirements(position, footprint):
    state = {"position": {"x": position[0], "y": 7., "z": position[1]}}
    delivered = cells()
    original = copy.deepcopy((state, delivered))
    selected = choose_cancel_target(state, delivered)
    assert selected["start_support_cells"] == footprint
    assert 3 <= selected["observed_steps"] <= 6 and selected["distance"] >= 2
    route = selected["observed_route"]
    assert len(route) == selected["observed_steps"] + 1
    assert all(abs(a["x"]-b["x"]) + abs(a["z"]-b["z"]) == 1 for a, b in zip(route, route[1:]))
    assert selected["target"] == route[-1]
    assert (state, delivered) == original


@pytest.mark.parametrize("bad_cell,replacement", [
    ((0, 6, -1), None), ((0, 6, -1), "minecraft:stone_slab"),
    ((0, 7, -1), "minecraft:stone"), ((0, 8, -1), "minecraft:stone"),
])
def test_unknown_or_obstructed_adjacent_footprint_rejects(bad_cell, replacement):
    delivered = cells()
    if replacement is None:
        del delivered[bad_cell]
    else:
        delivered[bad_cell] = replacement
    with pytest.raises(Fault, match="OBSERVED_START_FOOTPRINT_UNAVAILABLE"):
        choose_cancel_target({"position": {"x": .5, "y": 7., "z": .06}}, delivered)


def test_short_route_does_not_become_a_cancellation_pass():
    delivered = {key: value for key, value in cells().items() if key[0] == 0 and 0 <= key[2] < 3}
    with pytest.raises(Fault, match="OBSERVED_LONG_ROUTE_UNAVAILABLE"):
        choose_cancel_target({"position": {"x": .5, "y": 7., "z": .5}}, delivered)
