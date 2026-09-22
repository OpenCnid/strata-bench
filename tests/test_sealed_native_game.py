"""Synthetic sealed-pack/native joins; no Minecraft or model dispatch."""
from copy import deepcopy
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.pack_launch import resolve_pack_launch
from mcbench.pack_worker import HeldPackWorker
from mcbench.storage import Fault, canonical, digest
from strata_evaluator.native_game_evidence import sealed_pack_evidence
import test_pack_worker as worker_tests

inputs = worker_tests.inputs
candidate = worker_tests.candidate
pack = worker_tests.pack


@pytest.fixture
def archive(pack, candidate, tmp_path, monkeypatch):
    import mcbench.pack_worker as module
    binding, invocation, profile = pack
    output = tmp_path / "run"
    (output / "worker").mkdir(parents=True)
    invocation |= {"state_directory": str(output / "worker"), "configuration_path": str(output / "worker-config.json")}
    calls = []
    monkeypatch.setattr(module, "ManagedProcess", worker_tests.fake_process_factory(calls))
    server = resolve_pack_launch(binding, "server")
    with HeldPackWorker(binding, invocation) as worker:
        worker.start(preflight=True)
        worker.start()
        launch, receipt = worker.resolved, worker.receipt()
    service = candidate[0]
    lock = service._json(binding.request_id, binding.lock)
    bodies = {"run/pack-lock.json": lock, "run/pack-launch-profile.json": profile.model_dump(),
        "run/pack-inventory.json": service._json(binding.request_id, lock["resolved_inventory"]),
        "run/pack-worker-launch.json": launch, "run/server/pack-launch.json": server}
    plan = {"schema": "strata/M0NativeGameSmoke/4", "pack": binding.model_dump(),
        "worker_runtime": profile.worker_runtime.model_dump(), "worker_invocation": invocation, "output": str(output)}
    result = {"sealed_worker_receipt": receipt, "worker_runtime": receipt["runtime"]}
    server_plan = {"schema": "strata/DevelopmentServer/4", "pack": binding.model_dump()}
    server_result = {"pack_launch_digest": digest(server)}
    config = launch["worker_configuration"]
    return bodies, {"plan": plan}, result, config, server_plan, server_result


def inspect(archive):
    bodies, *rest = archive
    return sealed_pack_evidence(SimpleNamespace(json=lambda name: deepcopy(bodies[name])), *rest)


def test_retained_pack_binds_both_commands_configuration_and_owned_exit(archive):
    result = inspect(archive)
    assert result["both_roles_bound"] and result["generated_configuration_held"]
    assert not result["full_game_conformance_qualified"]


@pytest.mark.parametrize("change", ["lock", "inventory", "command", "environment", "settings", "state", "receipt", "forced-child", "server-join", "schema"])
def test_changed_pack_commands_settings_or_stop_proof_do_not_reconcile(archive, change):
    bodies, intent, result, config, server_plan, server_result = archive
    if change == "lock":
        intent["plan"]["pack"]["lock"] = "cas:sha256:" + "a"*64
    elif change == "inventory":
        bodies["run/pack-inventory.json"]["files"].pop()
    elif change == "command":
        bodies["run/server/pack-launch.json"]["launch"]["arguments"].append("--unreviewed")
    elif change == "environment":
        bodies["run/pack-worker-launch.json"]["launch"]["environment"]["PRIVATE_OVERRIDE"] = "fixture"
    elif change == "settings":
        config["primitive_limit"] += 1
    elif change == "state":
        config["state_directory"] = str(Path(config["state_directory"]).parent / "sibling")
    elif change == "receipt":
        result["sealed_worker_receipt"]["configuration_sha256"] = "a"*64
    elif change == "forced-child":
        result["sealed_worker_receipt"]["owned_processes"]["worker"]["job"]["terminated_processes"] = 1
    elif change == "schema":
        bodies["run/pack-worker-launch.json"]["schema"] = "strata/UnreviewedLaunch/1"
    else:
        server_result["pack_launch_digest"] = "a"*64
    with pytest.raises(Fault):
        inspect(archive)


def test_sealed_native_plan_rejects_literal_command_overrides_before_composition(tmp_path, monkeypatch):
    import m0_native_game as runner
    path = tmp_path / "plan.json"
    body = {"schema": "strata/M0NativeGameSmoke/4", "output": "unused", "pack": {},
        "worker_invocation": {}, "worker_runtime": {}, "codex": "unused", "tool_projections": "unused",
        "model_catalog": "unused", "retention_source": {}, "worker_config": "unreviewed"}
    path.write_bytes(canonical(body))
    monkeypatch.setattr(runner, "run_plan", lambda *_: pytest.fail("unreviewed plan reached composition"))
    with pytest.raises(Fault, match="M0_PLAN_INVALID"):
        runner.run(path)


@pytest.mark.parametrize("change", [None, "future-observation", "wrong-scope", "changed-save", "invented-prior-save"])
def test_fresh_player_join_uses_initial_scope_and_final_saved_state(example, monkeypatch, change):
    import strata_evaluator.native_game_evidence as module
    initial = example("Observation") | {"seq": 1}
    initial["state"] |= {"connected": True, "yaw": 0., "pitch": 0., "position": {"x": 1., "y": 65., "z": 2.}}
    latest = deepcopy(initial) | {"seq": 2}
    latest["state"]["yaw"] = 1.
    saved = {"Rotation": (5, [SimpleNamespace(value=180-math.degrees(1.)), SimpleNamespace(value=0.)]),
             "Pos": (6, [SimpleNamespace(value=n) for n in (1.,65.,2.)])}
    bodies = {"run/intent.json": {"plan": {"schema": "strata/M0NativeGameSmoke/4"}},
              "run/initial-observation.json": {"status": "ok", "result": initial}}
    files = set(bodies) | {"run/player-after.dat"}
    if change == "future-observation":
        initial["seq"] = 3
    elif change == "wrong-scope":
        initial["epoch"] += 1
    elif change == "changed-save":
        saved["Pos"][1][0].value = 99.
    elif change == "invented-prior-save":
        files.add("run/player-before.dat")
    # Only the packet/save join is under test; binary NBT parsing has its own
    # source cases and is not represented by this synthetic decoder.
    monkeypatch.setattr(module,"unpack_chunk",lambda *_: b"synthetic")
    monkeypatch.setattr(module,"NbtReader",lambda _: SimpleNamespace(root=lambda: saved))
    monkeypatch.setattr(module,"field",lambda value,key,_kind: value[key])
    bundle = SimpleNamespace(files=files, json=lambda name: bodies[name], read=lambda _: b"synthetic")
    if change:
        with pytest.raises(Fault, match="NATIVE_GAME_SAVED_PLAYER"):
            module.saved_player_evidence(bundle,[(0,latest)])
    else:
        assert module.saved_player_evidence(bundle,[(0,latest)])["orientation_changed"]
