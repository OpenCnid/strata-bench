"""M1 entry admission and preserved M0 boundaries; no game or native execution."""

from contextlib import ExitStack
import copy
import importlib
from pathlib import Path

import pytest

from mcbench.inventory import file_hash
from mcbench.pack_launch import parse_pack_binding
from mcbench.pack_restore import baseline_record
from mcbench.storage import Fault, digest


@pytest.fixture
def setup(tmp_path, monkeypatch, configs):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    module = importlib.import_module("m1_native_game")
    binary = tmp_path / "codex.exe"
    binary.write_bytes(b"synthetic executable; never run")
    monkeypatch.setattr(module, "BINARY_SHA256", file_hash(binary))
    checked = []
    monkeypatch.setattr(module, "native_companion_paths", lambda path: checked.append(path))
    campaign, agents = configs(2, "m1-fixture")
    binding = {"store": str(tmp_path / "store"), "request_id": "pack", "lock": "cas:sha256:" + "a" * 64,
               "instance": str(tmp_path / "instance"),
               "restoration": {"snapshot": str(tmp_path / "baseline"), "sha256": "b" * 64}}
    campaign = campaign.model_dump() | {"is_example": False, "pack_lock": binding["lock"],
        "world_baseline": "cas:sha256:" + digest(baseline_record(parse_pack_binding(binding)))}
    agents = [a.model_dump() | {"is_example": False, "requested_model": "gpt-6-luna", "provider": "local_scripted",
        "runtime": {"version": module.CODEX_VERSION, "digest": file_hash(binary)},
        "dovetail_commit": module.DOVETAIL_COMMIT, "helper_limit": 1, "helper_depth": 1} for a in agents]
    output = tmp_path / "run"
    plan = {"schema": module.SCHEMA, "output": str(output), "pack": binding, "codex": str(binary),
        "worker_invocation": {"campaign_id": "m1-fixture", "agent_id": "a1", "epoch": 1, "lease_id": "owned-lease",
            "state_directory": str(output / "worker"), "configuration_path": str(output / "worker-config.json")},
        "worker_runtime": {"path": str(tmp_path / "runtime.json"), "sha256": "c" * 64},
        "tool_projections": str(tmp_path / "projection.json"), "model_catalog": str(tmp_path / "catalog.json"),
        "campaign": campaign, "agents": agents}
    return module, plan, checked


def test_explicit_candidate_validates_native_pins_without_creating_output(setup):
    module, plan, checked = setup
    candidate = module.validate(plan)
    candidate.require_plan(plan)
    assert checked == [plan["codex"]]
    assert candidate.campaign.is_example is False and len(candidate.agents) == 2
    assert not Path(plan["output"]).exists()
    changed = copy.deepcopy(plan)
    changed["worker_invocation"]["epoch"] = 2
    with pytest.raises(Fault, match="M1_PLAN_CHANGED"):
        candidate.require_plan(changed)


@pytest.mark.parametrize("mutation,code", [
    ("paid-permit", "M1_PLAN_INVALID"), ("old-schema", "M1_PLAN_INVALID"), ("retention", "M1_PLAN_INVALID"),
    ("example-campaign", "M1_PLAN_ROSTER"), ("example-agent", "M1_PLAN_ROSTER"), ("missing-agent", "M1_PLAN_ROSTER"),
    ("wrong-model", "M1_PLAN_RUNTIME"), ("wrong-provider", "M1_PLAN_RUNTIME"), ("wrong-helper", "M1_PLAN_RUNTIME"),
    ("wrong-pack", "M1_PLAN_BASELINE"), ("wrong-baseline", "M1_PLAN_BASELINE"),
    ("no-baseline", "M1_PLAN_BASELINE"), ("wrong-epoch", "M1_PLAN_SCOPE"),
    ("wrong-avatar", "M1_PLAN_SCOPE"), ("wrong-output", "M1_PLAN_SCOPE"), ("existing-output", "M1_PLAN_SCOPE"),
])
def test_admission_refuses_changed_scope_before_game_resources(setup, mutation, code):
    module, plan, checked = setup
    if mutation == "paid-permit":
        plan["pilot"] = {}
    elif mutation == "old-schema":
        plan["schema"] = "strata/M0NativeGameSmoke/5"
    elif mutation == "retention":
        plan["retention_source"] = {}
    elif mutation == "example-campaign":
        plan["campaign"]["is_example"] = True
    elif mutation == "example-agent":
        plan["agents"][0]["is_example"] = True
    elif mutation == "missing-agent":
        plan["agents"].pop()
    elif mutation in {"wrong-model", "wrong-provider", "wrong-helper"}:
        key, value = {"wrong-model": ("requested_model", "other"), "wrong-provider": ("provider", "openai"),
                      "wrong-helper": ("helper_limit", 2)}[mutation]
        plan["agents"][0][key] = value
    elif mutation in {"wrong-pack", "wrong-baseline"}:
        plan["campaign"]["pack_lock" if mutation == "wrong-pack" else "world_baseline"] = "cas:sha256:" + "d" * 64
    elif mutation == "no-baseline":
        plan["pack"].pop("restoration")
    elif mutation in {"wrong-epoch", "wrong-avatar"}:
        plan["worker_invocation"]["epoch" if mutation == "wrong-epoch" else "agent_id"] = 2 if mutation == "wrong-epoch" else "a2"
    elif mutation == "wrong-output":
        plan["worker_invocation"]["state_directory"] += "-other"
    else:
        Path(plan["output"]).mkdir()
    with pytest.raises(Fault, match=code):
        module.validate(plan)
    assert checked == []


def test_validated_records_enter_only_the_synthetic_owned_controller(setup, tmp_path):
    module, plan, _ = setup
    from native_team_channel_probe import TeamChannelStore
    from mcbench.storage import Database
    candidate = module.validate(plan)
    with TeamChannelStore(tmp_path / "controller", candidate.campaign, candidate.agents) as store:
        store.healthy()
        db = Database(store.database)
        try:
            assert {row[0] for row in db.connection.execute("SELECT state FROM campaigns")} == {"RUNNING"}
            assert db.connection.execute("SELECT simulation FROM controller_profile").fetchone()[0] == 1
        finally:
            db.close()


def test_m1_cannot_enter_shared_lifecycle_without_validated_candidate(setup):
    _, plan, _ = setup
    runner = importlib.import_module("m0_native_game")
    with ExitStack() as resources, pytest.raises(Fault, match="M1_CANDIDATE_REQUIRED"):
        runner.run_plan(plan, resources)
    assert not Path(plan["output"]).exists()


def test_candidate_does_not_relax_m0_entry_schema(setup, tmp_path):
    _, plan, _ = setup
    runner = importlib.import_module("m0_native_game")
    from mcbench.storage import canonical
    source = tmp_path / "plan.json"
    source.write_bytes(canonical(plan))
    with pytest.raises(Fault, match="M0_PLAN_INVALID"):
        runner.run(source)
    assert not Path(plan["output"]).exists()
