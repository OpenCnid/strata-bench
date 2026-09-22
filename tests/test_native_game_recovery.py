"""Focused recovery-start controls; synthetic player tags and worker responses."""

from copy import deepcopy
import math
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault
from native_game_recovery import GameRecovery, player_matches
from strata_evaluator.saved_blocks import Tag


@pytest.fixture
def saved():
    player = {"Pos": Tag(9, (6, tuple(Tag(6, x) for x in (10., 64., 20.)))),
        "Rotation": Tag(9, (5, (Tag(5, 90.), Tag(5, 0.)))), "Dimension": Tag(8, "minecraft:overworld"),
        "Health": Tag(5, 20.), "foodLevel": Tag(3, 18),
        "Inventory": Tag(9, (10, tuple(Tag(10, {"Slot": Tag(1, slot), "id": Tag(8, item), "Count": Tag(1, n)})
            for slot, item, n in ((0, "minecraft:stick", 2), (103, "minecraft:iron_helmet", 1),
                                  (-106, "minecraft:torch", 3)))))}
    state = {"connected": True, "dimension": "minecraft:overworld", "position": {"x": 10., "y": 64., "z": 20.},
        "yaw": math.pi / 2, "pitch": 0., "health": 20, "food": 18, "active_request_id": None,
        "inventory": [{"slot": slot, "item_id": item, "count": n} for slot, item, n in
            ((36, "minecraft:stick", 2), (5, "minecraft:iron_helmet", 1), (45, "minecraft:torch", 3))]}
    return player, state


def test_saved_own_state_matches_hotbar_armor_and_offhand(saved):
    assert player_matches(*saved)


@pytest.mark.parametrize("change", ["position", "rotation", "health", "food", "inventory", "dimension", "connection"])
def test_restored_state_mismatch_cannot_start_native(saved, change):
    player, state = saved
    state = deepcopy(state)
    if change == "position":
        state["position"]["x"] += 1
    elif change == "rotation":
        state["yaw"] += .1
    elif change == "inventory":
        state["inventory"][0]["count"] += 1
    elif change == "dimension":
        state["dimension"] = "minecraft:the_nether"
    elif change == "connection":
        state["connected"] = False
    else:
        state[change] -= 1
    assert not player_matches(player, state)


@pytest.mark.parametrize("broken", [None, "old_token", "old_epoch", "replayed"])
def test_start_checks_old_token_and_epoch_without_replaying_action(saved, monkeypatch, broken):
    recovery = GameRecovery.__new__(GameRecovery)
    recovery.player, state = saved
    recovery.worker, recovery.result = {"epoch": 1}, {"status": "fail"}
    recovery.bundle = SimpleNamespace(json=lambda _: {"token": "old-worker-token", "epoch": 1})
    descriptor = {"token": "new-worker-token", "epoch": 2, "campaign_id": "c", "agent_id": "a"}
    requests = []
    def transport(grant):
        def send(request):
            requests.append(request)
            case = request.request_id.removeprefix("recovery-denied-")
            if case == broken:
                return {"status": "ok"}
            return {"status": "error", "error": {"code": "FORBIDDEN" if case == "old_token" else "STALE_EPOCH"}}
        return send
    monkeypatch.setattr("mcbench.broker_stdio.WorkerTransport", transport)
    observed = {"result": {"state": state, "last_action_seq": 1 if broken == "replayed" else None}}
    if broken:
        with pytest.raises(Fault, match="GAME_RECOVERY_(STALE_ACCEPTED|REPLAYED)"):
            recovery.verify_start(descriptor, observed)
    else:
        assert recovery.verify_start(descriptor, observed)["original_outer_result"] == "fail"
        assert len(requests) == 2
    assert all(r.method == "observe" and r.action is None for r in requests)
