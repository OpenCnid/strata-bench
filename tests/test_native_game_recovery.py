"""Focused recovery-start controls; synthetic player tags and worker responses."""

from copy import deepcopy
import json
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


@pytest.mark.parametrize("element_kind", [0, 10])
def test_empty_saved_inventory_accepts_vanilla_end_or_compound_list(saved, element_kind):
    player, state = deepcopy(saved)
    player["Inventory"] = Tag(9, (element_kind, ()))
    state["inventory"] = []
    assert player_matches(player, state)
    state["inventory"] = [{"slot": 36, "item_id": "minecraft:stick", "count": 1}]
    assert not player_matches(player, state)


def test_end_typed_inventory_with_an_element_is_invalid(saved):
    player, state = deepcopy(saved)
    player["Inventory"] = Tag(9, (0, player["Inventory"].value[1]))
    with pytest.raises(Fault, match="GAME_RECOVERY_PLAYER"):
        player_matches(player, state)


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


@pytest.fixture
def sealed_recovery(tmp_path):
    from mcbench.pack_launch import RestoredPackLaunchBinding
    recovery = GameRecovery.__new__(GameRecovery)
    recovery.sealed = True
    recovery.worker = {"campaign_id": "c1", "agent_id": "a1", "epoch": 1, "lease_id": "old-lease"}
    recovery.world_root = tmp_path / "source/run/server/stopped-instance"
    recovery.world = {"pack": {"lock": "cas:sha256:" + "a"*64, "request_id": "sealed-pack"}}
    recovery.retention = SimpleNamespace(config=SimpleNamespace(pack_lock=recovery.world["pack"]["lock"]))
    recovery.server = {"stopped_snapshot": {"manifest_sha256": "b"*64}}
    binding = RestoredPackLaunchBinding.model_validate({"store": str(tmp_path / "store"),
        "request_id": "sealed-pack", "lock": recovery.world["pack"]["lock"], "instance": str(tmp_path / "new-instance"),
        "restoration": {"snapshot": str(recovery.world_root), "sha256": "b"*64}})
    invocation = recovery.worker | {"epoch": 2, "lease_id": "new-lease"}
    return recovery, binding, invocation


@pytest.mark.parametrize("change", [None, "pack", "request", "snapshot-hash", "snapshot-path", "campaign", "agent", "epoch", "lease"])
def test_sealed_recovery_requires_the_same_stopped_world_and_fresh_scope(sealed_recovery, tmp_path, change):
    recovery, binding, invocation = sealed_recovery
    if change == "pack":
        binding.lock = "cas:sha256:" + "c"*64
    elif change == "request":
        binding.request_id = "different-pack"
    elif change == "snapshot-hash":
        binding.restoration.sha256 = "c"*64
    elif change == "snapshot-path":
        binding.restoration.snapshot = str(tmp_path / "different-source")
    elif change in {"campaign", "agent"}:
        invocation[change + "_id"] = "sibling"
    elif change == "epoch":
        invocation["epoch"] = 1
    elif change == "lease":
        invocation["lease_id"] = "old-lease"
    if change:
        with pytest.raises(Fault, match="GAME_RECOVERY_(SOURCE|SCOPE)"):
            recovery.validate_sealed_binding(binding, invocation)
    else:
        recovery.validate_sealed_binding(binding, invocation)


def test_sealed_worker_handoff_records_parent_component_and_copies_only_prior_player(sealed_recovery, tmp_path):
    recovery, binding, invocation = sealed_recovery
    recovery.source = {"bundle": str(tmp_path / "source"), "seal_sha256": "d"*64}
    recovery.retained = {"component_ref": "cas:sha256:" + "e"*64}
    recovery.result, recovery.old_actions = {"status": "pass"}, [("original-action",)]
    journal = tmp_path / "source/run/worker/actions.sqlite"
    recovery.bundle = SimpleNamespace(path=lambda name: journal if name == "run/worker/actions.sqlite" else None,
        files={"run/worker/actions.sqlite": SimpleNamespace(sha256="f"*64)},
        read=lambda name: b"synthetic own saved player" if name == "run/player-after.dat" else pytest.fail(name))
    calls = []
    prepared = SimpleNamespace(binding=binding, resolved={"worker_configuration": invocation}, restore_journal=calls.append)
    output = tmp_path / "run"
    output.mkdir()
    recovery.restore_worker(prepared, output)
    assert calls == [{"path": str(journal), "sha256": "f"*64, "campaign_id": "c1", "agent_id": "a1", "epoch": 1}]
    assert {p.name for p in output.iterdir()} == {"player-before.dat", "recovery-source.json"}
    receipt = json.loads((output / "recovery-source.json").read_bytes())
    assert receipt["source"] == recovery.source and receipt["component"] == recovery.retained["component_ref"]
    assert receipt["epoch"] == 2 and receipt["worker_rows_preserved"] == 1 and not receipt["full_checkpoint"]
    with pytest.raises(FileExistsError):
        recovery.record_source(output, invocation)


@pytest.mark.parametrize("change", [None, "retention", "template", "command"])
def test_recovery_three_accepts_only_the_explicit_sealed_plan(tmp_path, monkeypatch, change):
    import m0_native_game as runner
    from mcbench.storage import canonical
    plan = {"schema": "strata/M0NativeGameRecovery/3", "output": "unused", "pack": {},
        "worker_invocation": {}, "worker_runtime": {}, "codex": "unused", "tool_projections": "unused",
        "model_catalog": "unused", "recovery_source": {}}
    if change:
        plan[{"retention": "retention_source", "template": "template_directory", "command": "worker_config"}[change]] = "unreviewed"
    path = tmp_path / "plan.json"
    path.write_bytes(canonical(plan))
    calls = []
    monkeypatch.setattr(runner, "run_plan", lambda body, _resources: calls.append(body))
    if change:
        with pytest.raises(Fault, match="M0_PLAN_INVALID"):
            runner.run(path)
        assert not calls
    else:
        runner.run(path)
        assert calls == [plan]
