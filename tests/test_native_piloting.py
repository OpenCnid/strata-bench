"""D14 source fixtures; no actual model, credentials or Minecraft invocation."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import sqlite3
import time

import pytest
from pydantic import ValidationError

from mcbench.contracts import RpcRequest
from mcbench.native_piloting import (
    MAX_REQUESTS, MAX_SPEND, PRECHECKS, PURPOSE, SCHEMA, prompt,
    require_bounded_game_request, require_profile, validate_permit,
)
from mcbench.storage import Fault, canonical
from native_pilot_report import movement_checks
import test_native_conformance as receipt_tests
from test_contracts import EXAMPLES

gateway = receipt_tests.gateway
provider = receipt_tests.provider
permit = receipt_tests.permit


@pytest.fixture
def pilot(permit, tmp_path):
    gate, proof, plan, config, data, broker = permit
    scope = {k: getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch")}
    grant = tmp_path / "grant.json"
    grant.write_bytes(canonical(scope | {"url": "http://127.0.0.1:1/v1/game", "token": "synthetic-secret-0000"}))
    broker.write_bytes(canonical({"worker_grant": str(grant)}))
    manifest = tmp_path / "manifest.json"
    names = ("codex-code-mode-host.exe", "codex-command-runner.exe", "codex-windows-sandbox-setup.exe")
    raw = canonical({"schema": "strata/NativeBootstrap/2", "broker_config": str(broker),
        "native_executable": "C:/synthetic/codex.exe", "native_companions": {n: "a"*64 for n in names},
        "inventory": {"files": [{"path": "C:/synthetic/"+n, "sha256": "a"*64, "bytes": 1} for n in names]}})
    manifest.write_bytes(raw)
    config.max_requests = MAX_REQUESTS
    plan = plan.model_copy(update={"purpose": PURPOSE, "hard_timeout_s": 90,
        "prompt": prompt(scope, "lease-1"), "bootstrap_digest": hashlib.sha256(raw).hexdigest(),
        "gateway_config_digest": config.profile_fingerprint()})
    config.profile_digest = plan.profile_digest()
    proof.update(schema=SCHEMA, purpose=PURPOSE, scope_decision="D14", isolation_qualified=False,
        lease_id="lease-1", maximum_microusd=MAX_SPEND, max_requests=MAX_REQUESTS,
        gateway_config_digest=plan.gateway_config_digest, profile_digest=plan.profile_digest(),
        prechecks={check: check for check in PRECHECKS})
    for check in PRECHECKS:
        data[check] = canonical({"schema": "strata/NativePreDispatchEvidence/1", "is_example": False,
            "profile_digest": plan.profile_digest(), "check": check, "scope": PURPOSE,
            "result": "pass", "evidence_refs": ["synthetic-evidence"]})
    return gate, proof, plan, config, data


def test_development_does_not_require_or_fabricate_isolation_proof(pilot):
    gate, proof, plan, config, _ = pilot
    assert validate_permit(gate, proof, plan, config, account_digest="c"*64)
    assert not proof["isolation_qualified"] and "isolated_tools_and_egress" not in proof["prechecks"]


@pytest.mark.parametrize("field,value", [("purpose", "campaign"), ("helper_limit", 1),
    ("prompt", "unbounded free play"), ("hard_timeout_s", 91), ("role", "helper"),
    ("model", "different"), ("budget_mode", "whole_job")])
def test_development_permit_cannot_expand_runtime_scope(pilot, field, value):
    _, _, plan, config, _ = pilot
    plan = plan.model_copy(update={field: value})
    config.profile_digest = plan.profile_digest()
    with pytest.raises(Fault, match="PILOT_SCOPE"):
        require_profile(plan, config, "lease-1")


@pytest.mark.parametrize("field,value", [("isolation_qualified", True), ("production_qualified", True),
    ("scope_decision", "D12"), ("maximum_microusd", 1000001), ("max_requests", 7),
    ("expires_unix", 1), ("account_digest", "d"*64), ("is_example", True), ("host", "example.invalid")])
def test_development_permit_cannot_claim_qualification_or_new_budget(pilot, field, value):
    gate, proof, plan, config, _ = pilot
    proof[field] = value
    with pytest.raises(Fault, match="PILOT_UNADMITTED"):
        validate_permit(gate, proof, plan, config, account_digest="c"*64)


def test_every_pilot_precheck_is_required(pilot):
    gate, proof, plan, config, data = pilot
    for check in PRECHECKS:
        original = data[check]
        data[check] = canonical(json.loads(original) | {"result": "fail"})
        with pytest.raises(Fault, match="PILOT_EVIDENCE"):
            validate_permit(gate, proof, plan, config, account_digest="c"*64)
        data[check] = original


def action(kind="look_at", seq=1):
    value = deepcopy(EXAMPLES["mcbench/ActionBatch/1"])
    value.update(is_example=False, seq=seq, request_id=f"action-{seq}", observation_id=f"before-{seq}",
        expected_state_revision=seq, duration_ms=2000, release_at_end=True, mode="structured", events=[],
        deadline_at=datetime.fromtimestamp(time.time()+2, timezone.utc).isoformat().replace("+00:00", "Z"),
        action={"kind": kind, "target": {"x": 1., "y": 64., "z": 0.}})
    if kind == "move_to":
        value["action"]["tolerance"] = .3
    return value


def rpc(batch):
    return RpcRequest.model_validate({"schema": "strata/GameRequest/1", "request_id": "rpc-1",
        **{k: batch[k] for k in ("campaign_id", "agent_id", "epoch")}, "method": "act", "action": batch,
        "deadline_at": batch["deadline_at"], "target_request_id": None, "after": None})


@pytest.mark.parametrize("fault", [None, "third", "long", "release", "distant-deadline", "dig"])
def test_bound_is_enforced_before_game_forwarding(fault):
    db = sqlite3.connect(":memory:")
    try:
        db.execute("CREATE TABLE native_jobs(id TEXT,plan TEXT)")
        db.execute("INSERT INTO native_jobs VALUES('pilot',?)", (json.dumps({"purpose": PURPOSE}),))
        db.execute("CREATE TABLE broker_game_requests(runtime TEXT,body TEXT)")
        batch = action()
        if fault == "third":
            db.executemany("INSERT INTO broker_game_requests VALUES('pilot',?)", [(json.dumps({"method": "act"}),)]*2)
        elif fault == "long":
            batch["duration_ms"] = 2001
        elif fault == "release":
            batch["release_at_end"] = False
        elif fault == "distant-deadline":
            batch["deadline_at"] = "2099-01-01T00:00:00Z"
        elif fault == "dig":
            batch["action"] |= {"kind": "dig", "expected_block_id": "minecraft:stone"}
        if fault == "release":
            with pytest.raises(ValidationError, match="release_at_end"):
                rpc(batch)
        elif fault:
            with pytest.raises(Fault, match="PILOT_ACTION"):
                require_bounded_game_request(db, "pilot", rpc(batch))
        else:
            require_bounded_game_request(db, "pilot", rpc(batch))
    finally:
        db.close()


def trajectory():
    calls = []
    for seq, kind in enumerate(("look_at", "move_to"), 1):
        batch = action(kind, seq)
        before = deepcopy(EXAMPLES["mcbench/Observation/1"])
        before.update(is_example=False, observation_id=f"before-{seq}", state_revision=seq,
            **{k: batch[k] for k in ("campaign_id", "agent_id", "epoch", "capability_digest", "control_revision")},
            held_keys=[], last_action_seq=seq-1)
        before["state"].update(connected=True, position={"x": 0., "y": 64., "z": 0.}, yaw=0., health=20.)
        after = deepcopy(before)
        after.update(observation_id=f"after-{seq}", state_revision=seq+1, last_action_seq=seq)
        if seq == 1:
            after["state"]["yaw"] = 1.
        else:
            after["state"]["position"]["x"] = 1.
        ack = deepcopy(EXAMPLES["mcbench/ActionAck/1"])
        ack.update(is_example=False, request_id=batch["request_id"], action_seq=seq, status="completed",
            **{k: batch[k] for k in ("campaign_id", "agent_id", "epoch")},
            result_observation_id=after["observation_id"], completed_mono_ms=1000,
            release_confirmed=True, requires_resync=False)
        if seq == 1:
            after["state"]["yaw"] = -math.pi/2
        calls.extend([
            {"body": {"method": "observe"}, "result": {"status": "ok", "result": before}, "state": "SETTLED"},
            {"body": {"method": "act", "action": batch}, "result": {"status": "ok", "result": ack}, "state": "SETTLED"},
            {"body": {"method": "observe"}, "result": {"status": "ok", "result": after}, "state": "SETTLED"}])
    return calls


def test_public_before_after_evidence_proves_both_effects():
    checks, changes = movement_checks(trajectory())
    assert all(checks.values())
    assert changes[-1]["horizontal_distance"] == 1. and changes[-1]["target_distance"] == 0.


@pytest.mark.parametrize("fault", [None, "missing-ack", "no-release", "stale", "no-turn", "missing-after"])
def test_partial_turn_is_retained_without_claiming_complete_pilot(fault):
    calls = trajectory()[:3]
    if fault == "missing-ack":
        calls[1]["result"] = None
    elif fault == "no-release":
        calls[1]["result"]["result"]["release_confirmed"] = False
    elif fault == "stale":
        calls[2]["result"]["result"]["state_revision"] = 1
    elif fault == "no-turn":
        calls[2]["result"]["result"]["state"]["yaw"] = 0
    elif fault == "missing-after":
        calls.pop()
    checks, changes = movement_checks(calls)
    assert checks["turn_observed"] == (fault is None)
    assert not checks["two_model_selected_actions"] and not checks["walk_observed"]
    if fault is None:
        assert checks["bounded_actions_observed"] and len(changes) == 1


def test_twelve_request_profile_requires_matching_prompt_and_permit(pilot):
    gate, proof, plan, config, _ = pilot
    config.max_requests = 12
    scope = {k: getattr(plan, k) for k in ("campaign_id", "agent_id", "epoch")}
    plan = plan.model_copy(update={"prompt": prompt(scope, "lease-1", 12),
                                  "gateway_config_digest": config.profile_fingerprint()})
    config.profile_digest = plan.profile_digest()
    require_profile(plan, config, "lease-1")
    with pytest.raises(Fault, match="PILOT_UNADMITTED"):
        validate_permit(gate, proof, plan, config, account_digest="c"*64)
    with pytest.raises(Fault, match="PILOT_SCOPE"):
        require_profile(plan.model_copy(update={"prompt": prompt(scope, "lease-1", 6)}), config, "lease-1")


@pytest.mark.parametrize("fault", ["no-move", "no-turn", "no-release", "stale", "wrong-target", "damage",
    "foreign-scope", "fixture", "held-key", "missing-observation", "unsettled", "extra-action"])
def test_successful_receipt_alone_cannot_pass_piloting(fault):
    calls = trajectory()
    after = calls[-1]["result"]["result"]
    if fault == "no-move":
        after["state"]["position"]["x"] = 0
    elif fault == "no-turn":
        calls[2]["result"]["result"]["state"]["yaw"] = 0
    elif fault == "no-release":
        calls[4]["result"]["result"]["release_confirmed"] = False
    elif fault == "stale":
        after["state_revision"] = 2
    elif fault == "wrong-target":
        after["state"]["position"]["x"] = 3
    elif fault == "damage":
        after["state"]["health"] = 19
    elif fault == "foreign-scope":
        after["agent_id"] = "sibling"
    elif fault == "fixture":
        after["is_example"] = True
    elif fault == "held-key":
        after["held_keys"] = [{"backend": "glfw", "representation": "keysym",
            "code": 87, "modifiers": [], "name": "W", "persisted": "key.keyboard.w"}]
    elif fault == "missing-observation":
        calls.pop()
    elif fault == "unsettled":
        calls[1]["state"] = "DISPATCHING"
    else:
        calls.append(deepcopy(calls[4]))
    assert not all(movement_checks(calls)[0].values())


def test_pilot_rejects_d12_before_opening_any_path():
    from types import SimpleNamespace
    from native_oauth_conformance import run_native_trial
    with pytest.raises(Fault, match="PILOT_D12_FORBIDDEN"):
        run_native_trial(SimpleNamespace(metering_trial="D12"), pilot={})


def test_pilot_contract_probe_requires_exact_native_fixture_dependencies():
    from native_mcp_identity_probe import run
    with pytest.raises(Fault, match="PILOT_CONTRACT_PROFILE_REQUIRED"):
        run(None, None, piloting_contract=True)


def test_old_canary_preflight_cannot_stand_in_for_public_contract_read(tmp_path):
    from native_oauth_conformance import inspect_preflight
    (tmp_path / "result.json").write_bytes(canonical({"is_example": True, "checks": {"old_canary": True}}))
    (tmp_path / "manifest.json").write_bytes(canonical({}))
    with pytest.raises(Fault, match="PREFLIGHT_SCOPE_MISMATCH"):
        inspect_preflight(tmp_path, None, None, piloting=True)


@pytest.mark.parametrize("state,code,reason,completed", [
    ("FINALIZED", 0, "native_exit", True), ("FINALIZED", 1, "native_exit", False),
    ("UNSETTLED", 0, "runtime_hard_timeout", False)])
def test_native_error_or_timeout_cannot_be_reported_as_clean_completion(database, cas, state, code, reason, completed):
    from types import SimpleNamespace
    from native_pilot_report import record_outcome
    db = database.connection
    db.execute("CREATE TABLE native_jobs(id TEXT,state TEXT,returncode INTEGER,reason TEXT)")
    db.execute("INSERT INTO native_jobs VALUES('pilot',?,?,?)", (state, code, reason))
    db.execute("CREATE TABLE inference_attempts(operation TEXT,state TEXT,reason TEXT,receipt_digest TEXT,request TEXT)")
    db.execute("CREATE TABLE inference_valuations(operation TEXT,body TEXT)")
    db.execute("CREATE TABLE native_worker_bindings(job TEXT,state TEXT)")
    gate = SimpleNamespace(db=database, cas=cas, simulation=True)
    plan = SimpleNamespace(job_id="pilot", profile_digest=lambda: "a"*64)
    _, report = record_outcome(gate, plan, None)
    assert report["checks"]["native_completed"] is completed
    assert report["receipt_result"] == "fail" and not report["isolation_qualified"]


def test_unknown_accounting_stops_before_any_game_launch(tmp_path, monkeypatch):
    from mcbench.authorization import Authorizations
    from mcbench.budgets import DIMENSIONS
    from mcbench.storage import Database
    from mcbench.native import NativeExec
    from native_pilot_trial import check_inputs
    from native_dispatch_probe import ledger, put
    from test_authorization import install, policy
    from types import SimpleNamespace
    from mcbench.storage import CAS
    import m0_native_game
    db = Database(tmp_path / "authority.sqlite")
    try:
        cas = CAS(db, tmp_path / "objects")
        auth = Authorizations(db)
        approved = policy()
        authority = install(auth, approved)
        NativeExec(db, cas, authorization_id=approved.authorization_id)
        auth.budgets.create_account("old", dict.fromkeys(DIMENSIONS, None), "c1", "a1", authority, category="development")
        plan = SimpleNamespace(campaign_id="c1", agent_id="a1", epoch=1, role="executor", model="gpt-5.6-luna")
        record = ledger(plan, "old-request", parent=None, calls=1, spend=755400,
                        pricing=put(cas, approved.accounting_basis.model_dump()))
        auth.budgets.post("old", record)
        auth.budgets.hold_uncertain("old", "old-request", "synthetic lost receipt")
        credentials = tmp_path / "unread-credentials.json"
        credentials.write_text("not valid credentials; must never be read")
        inputs = {"database": str(db.path), "objects": str(cas.root), "credentials": str(credentials),
            "preflight": str(tmp_path), "authorization": approved.authorization_id,
            "job_id": approved.authorization_id+":m0-pilot-01"}
        snapshot = auth.snapshot()
        with pytest.raises(Fault, match="PILOT_ACCOUNTING_BLOCKED"):
            check_inputs(inputs)
        path = tmp_path / "pilot-plan.json"
        path.write_bytes(canonical({"schema": "strata/M0NativePilot/1", "pilot": inputs}))
        monkeypatch.setattr(m0_native_game, "run_plan", lambda *_: pytest.fail("game launch reached"))
        with pytest.raises(Fault, match="PILOT_ACCOUNTING_BLOCKED"):
            m0_native_game.run(path)
        assert auth.snapshot() == snapshot
        assert db.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 0
    finally:
        db.close()
