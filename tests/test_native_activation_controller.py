"""Actual controller API with synthetic checkpoint/readiness dependency records."""

import importlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.controller import Controller, READINESS
from mcbench.native import NativeExec
from mcbench.native_broker_policy import TEAM_POLICY
from mcbench.storage import Fault, Principal, canonical


@pytest.fixture
def setup(database, cas, configs, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    module = importlib.import_module("native_activation_controller")
    policy = importlib.import_module("native_team_channel_probe").POLICY
    operator = Principal("operator", "operator")
    ref = cas.put(operator, "operator", "operator", canonical(policy))
    evidence = cas.put(operator, "operator", "operator", canonical({"is_example": True,
        "scope": "synthetic checkpoint/readiness dependency only"}))
    config, agents = configs()
    config = config.model_copy(update={"communication_policy": ref})
    agents = [a.model_copy(update={"requested_model": "gpt-6-luna"}) for a in agents]
    # Source campaign already checkpointed; its original lease is expired.
    clock = time.time() - 20
    controller = Controller(database, simulation=True, clock=lambda: clock)
    controller.create(config, agents)
    resources = {"bodies": 1, "memory_mib": 10, "disk_bytes": 1000, "model_slots": 1}
    controller.certify("synthetic", "fixture", resources, evidence, simulation=True)
    epoch = controller.claim("c1", "source-owner", 0)
    for state in ("PROVISIONING", "VALIDATING"):
        controller.transition("c1", "source-owner", epoch, controller.status("c1")["revision"], state, "fixture")
    controller.admit("c1", "source-owner", epoch, controller.status("c1")["revision"], "synthetic", "fixture", resources)
    controller.ready("c1", "source-owner", epoch, controller.status("c1")["revision"], {"a1": dict.fromkeys(READINESS, evidence)})
    controller.transition("c1", "source-owner", epoch, controller.status("c1")["revision"], "CHECKPOINTING", "fixture")
    runtime = NativeExec(database, cas, simulation=True)
    body = {"is_example": True, "campaign_id": "c1", "agent_id": "a1", "source_epoch": 1,
            "model_identity": "gpt-6-luna", "system_digest": config.system_digest, "checkpoint_ref": evidence}
    plan = SimpleNamespace(campaign_id="c1", agent_id="a1", epoch=2, model="gpt-6-luna",
                           broker_policy=TEAM_POLICY, team_policy_ref=ref)
    return module, runtime, body, plan


def test_claim_ready_heartbeat_and_drain_preserve_original_config_and_reservations(setup):
    module, runtime, body, plan = setup
    db = runtime.db.connection
    old = dict(db.execute("SELECT * FROM campaigns WHERE id='c1'").fetchone())
    reservations = [tuple(r) for r in db.execute("SELECT * FROM reservations")]
    with module.ActivationController(runtime, body, plan) as owned:
        owned.healthy(plan)
        current = dict(db.execute("SELECT * FROM campaigns WHERE id='c1'").fetchone())
        assert current["epoch"] == 2 and current["state"] == "RUNNING"
        assert all(current[k] == old[k] for k in ("config", "agents", "request_digest"))
        assert [tuple(r) for r in db.execute("SELECT * FROM reservations")] == reservations
        assert owned.policy_ref == plan.team_policy_ref
    assert owned.report()["thread_stopped"] and not owned.errors and owned.heartbeats
    assert not owned.report()["production_qualified"]
    with pytest.raises(Fault, match="ACTIVATION_CONTROLLER_REARM"):
        owned.__enter__()
    with pytest.raises(Fault, match="ACTIVATION_CONTROLLER_HEARTBEAT"):
        owned.healthy(plan)


@pytest.mark.parametrize("case", ["busy", "wrong_epoch", "wrong_model", "changed_system", "wrong_state",
                                 "production", "wrong_policy", "missing_campaign"])
def test_invalid_continuation_never_rewrites_configuration_or_claims_epoch(setup, case):
    module, runtime, body, plan = setup
    db = runtime.db.connection
    if case == "busy":
        db.execute("UPDATE campaigns SET lease_until=?", (time.time() + 100,))
    elif case == "wrong_epoch":
        plan.epoch = 3
    elif case == "wrong_model":
        plan.model = "gpt-5.6-luna"
    elif case == "changed_system":
        body["system_digest"] = "f" * 64
    elif case == "wrong_state":
        db.execute("UPDATE campaigns SET state='RUNNING'")
    elif case == "production":
        runtime.simulation = False
    elif case == "wrong_policy":
        config = json.loads(db.execute("SELECT config FROM campaigns").fetchone()[0])
        config["communication_policy"] = "cas:sha256:" + "f" * 64
        db.execute("UPDATE campaigns SET config=?", (json.dumps(config),))
    else:
        plan.campaign_id = body["campaign_id"] = "missing"
    before = [tuple(r) for r in db.execute("SELECT * FROM campaigns")]
    owned = module.ActivationController(runtime, body, plan)
    with pytest.raises(Fault):
        owned.__enter__()
    assert [tuple(r) for r in db.execute("SELECT * FROM campaigns")] == before
    assert owned.thread is None


def test_missing_held_reservation_keeps_failed_new_epoch_without_claiming_readiness(setup):
    module, runtime, body, plan = setup
    db = runtime.db.connection
    db.execute("DELETE FROM reservations")
    owned = module.ActivationController(runtime, body, plan)
    with pytest.raises(Fault, match="RESERVATION_EXPIRED"):
        owned.__enter__()
    assert tuple(db.execute("SELECT epoch,state FROM campaigns").fetchone()) == (2, "CHECKPOINTING")
    assert owned.thread is None
    with pytest.raises(Fault, match="ACTIVATION_CONTROLLER_REARM"):
        owned.__enter__()


def test_failed_first_heartbeat_is_drained_before_entry_returns(setup, monkeypatch):
    module, runtime, body, plan = setup
    def fail(*args):
        raise Fault("OWNED_HEARTBEAT_FAILURE")
    monkeypatch.setattr(module.Controller, "heartbeat", fail)
    owned = module.ActivationController(runtime, body, plan)
    with pytest.raises(Fault, match="ACTIVATION_CONTROLLER_HEARTBEAT"):
        owned.__enter__()
    assert not owned.thread.is_alive() and owned.errors and not owned.heartbeats


@pytest.mark.parametrize("flag,model", [(True, "gpt-5.6-luna"), (True, "gpt-6-luna"), (1, "gpt-6-luna")])
def test_selected_orchestrator_requires_exact_complete_profile_before_copy(setup, tmp_path, flag, model):
    native = importlib.import_module("native_mcp_identity_probe")
    with pytest.raises(Fault, match="SELECTED_ACTIVATION_REQUIRED"):
        native.run(Path("missing.exe"), tmp_path / "unused", selected_activation=flag, model=model)
    assert not (tmp_path / "unused").exists()
