"""Conservative public-map route selection for operator cancellation references.

This is a fixed standing-player reference procedure, not a gameplay pathfinder
or an input authority. It reads only delivered cells. The native motor must
still validate actual body dimensions, shapes, current state and every movement.
"""

import math

from .storage import require

POLICY = "public-full-cube-standing-footprint-reference/2"
GROUND = frozenset({"minecraft:grass_block", "minecraft:stone", "minecraft:dirt",
                    "minecraft:cobblestone", "minecraft:oak_planks"})


def _distance(a, b):
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in ("x", "y", "z")))


def choose_cancel_target(state, cells):
    """Propose an observed 3–6 step route with at least two blocks displacement.

    A normal standing 0.6-wide / 1.8-high player may start off center. Prove
    support and clearance for the full bounding rectangle swept to the starting
    cell center, including adjacent cells at edges and corners. This conservative
    envelope can reject feasible routes; it never treats unknown cells as air.
    """
    point = state["position"]
    require(all(type(point[k]) in (int, float) and math.isfinite(point[k])
                and abs(point[k]) <= 30000000 for k in ("x", "y", "z")), "REFERENCE_POSITION_INVALID")
    require(len(cells) <= 640, "PUBLIC_MAP_QUOTA")
    require(all(isinstance(key, tuple) and len(key) == 3 and
                all(type(n) is int for n in key) and isinstance(value, str)
                for key, value in cells.items()), "REFERENCE_CELL_INVALID")
    x, y, z = (math.floor(point[k]) for k in ("x", "y", "z"))
    require(abs(point["y"] - y) < .0001, "LEVEL_START_UNAVAILABLE")
    center = {"x": x + .5, "y": point["y"], "z": z + .5}

    def clear(cx, cz):
        return cells.get((cx, y - 1, cz)) in GROUND and all(
            cells.get((cx, cy, cz)) == "minecraft:air" for cy in (y, y + 1))

    def span(axis):
        low = min(point[axis], center[axis]) - .3
        high = max(point[axis], center[axis]) + .3
        # Exact touching at the upper edge has no overlapping area. nextafter
        # excludes only that boundary, not small but genuine intersections.
        return range(math.floor(low), math.floor(math.nextafter(high, -math.inf)) + 1)

    footprint = [(cx, cz) for cx in span("x") for cz in span("z")]
    require(footprint and all(clear(cx, cz) for cx, cz in footprint),
            "OBSERVED_START_FOOTPRINT_UNAVAILABLE")
    queue = [(x, z, 0, [center])]
    seen = {(x, z)}
    candidates = []
    for cx, cz, depth, path in queue:
        target = {"x": cx + .5, "y": point["y"], "z": cz + .5}
        if depth >= 3 and _distance(point, target) >= 2:
            candidates.append({"target": target, "observed_steps": depth,
                               "distance": _distance(point, target), "observed_route": path,
                               "observed_route_length": _distance(point, center) + depth})
        if depth == 6:
            continue
        for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            adjacent = (cx + dx, cz + dz)
            if adjacent not in seen and clear(*adjacent):
                seen.add(adjacent)
                queue.append((*adjacent, depth + 1, path + [
                    {"x": adjacent[0] + .5, "y": point["y"], "z": adjacent[1] + .5}]))
    require(bool(candidates), "OBSERVED_LONG_ROUTE_UNAVAILABLE")
    return max(candidates, key=lambda item: (item["observed_route_length"], item["distance"])) | {
        "reference_policy": POLICY, "start_support_cells": [[cx, y - 1, cz] for cx, cz in footprint]}
