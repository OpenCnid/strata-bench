"""Reverted privilege remains tainted; synthetic data and an optional owned JVM."""

import copy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault, canonical, digest
from strata_evaluator.craft_reference import parse_plan
from strata_evaluator.operator_control import OperatorControl, OperatorControlPlan, saved_operators
from strata_evaluator.setup_history import HistorySupport, SetupHistory, ROUTES, POLICY, qualify_history
from test_craft_reference import ACTOR, pin, reference  # noqa: F401
from test_setup_control import nbt


def target():
    return {"policy": "private-operator-roundtrip/1", "purpose": "negative_control", "agent_id": "agent",
            "actor_uuid": ACTOR, "player_name": "FixtureActor", "operator_level": 4}


def prepare(reference):  # noqa: F811
    store, setup, _, directory, _ = reference
    game = Path(setup["game_directory"])
    (game / "ops.json").write_bytes(b"[]")
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %z")
    (game / "usercache.json").write_bytes(canonical([{"name": "FixtureActor", "uuid": ACTOR, "expiresOn": expires}]))
    for role, name in (("operator-roster", "ops.json"), ("profile-cache", "usercache.json")):
        path = game / name
        setup["supporting_files"][role] = {"path": str(path), **pin(path)}
    receipt = store.seal(setup, directory)
    return receipt, OperatorControl(OperatorControlPlan.model_validate(target()), parse_plan(setup), directory, 10)


@pytest.mark.parametrize("change", ["command", "name", "level", "roster", "source", "expired", "duplicate", "uuid"])
def test_target_and_preexisting_profile_must_be_exact_before_dispatch(reference, change):  # noqa: F811
    _, control = prepare(reference)
    plan = target()
    setup = parse_plan(reference[1])
    directory = reference[3]
    if change in {"command", "name", "level"}:
        plan.update({"command": "stop", "name": "bad\nstop", "level": 3} if change == "command" else
                    {"player_name": "bad\nstop"} if change == "name" else {"operator_level": 3})
        with pytest.raises(ValidationError):
            OperatorControlPlan.model_validate(plan)
        return
    if change == "roster":
        plan["actor_uuid"] = "22222222-2222-2222-2222-222222222222"
    elif change == "source":
        del setup.supporting_files["profile-cache"]
    else:
        cache = [{"name": "FixtureActor", "uuid": ACTOR, "expiresOn": "2099-01-01 00:00:00 +0000"}]
        if change == "expired":
            cache[0]["expiresOn"] = "2000-01-01 00:00:00 +0000"
        elif change == "duplicate":
            cache.append(dict(cache[0]))
        else:
            cache[0]["uuid"] = "22222222-2222-2222-2222-222222222222"
        (directory / "supporting" / digest("profile-cache")).write_bytes(canonical(cache))
    with pytest.raises(Fault, match="OPERATOR_CONTROL_ROSTER|OPERATOR_CONTROL_SOURCE|OPERATOR_CONTROL_PROFILE"):
        OperatorControl(OperatorControlPlan.model_validate(plan), setup, directory, 10)
    assert not control.attempted


def begin(control, tmp_path):
    log = tmp_path / "stdout.log"
    log.write_bytes(b"")
    prefix = {"campaign_id": "synthetic", "epoch": 1, "server_boot_id": "boot",
              "startup": {"fixture": True}, "launch_identity": {"module_sha256": "a" * 64}}
    writes = []
    proc = SimpleNamespace(send_input=writes.append)
    control.dispatch(prefix, proc, lambda: None, deadline=time.monotonic() + 10, exposure_s=1, log=log)
    return log, prefix, writes, proc


@pytest.mark.parametrize("phase", ["grant", "revoke"])
@pytest.mark.parametrize("fault", ["journal", "write", "after_write"])
def test_uncertain_grant_or_revoke_never_replays_and_retains_intermediate(reference, tmp_path, phase, fault):  # noqa: F811
    _, control = prepare(reference)
    log = tmp_path / "stdout.log"
    log.write_bytes(b"")
    writes, records = [], []
    if phase == "revoke":
        log, _, writes, _ = begin(control, tmp_path)
        log.write_text("Made FixtureActor a server operator\n")
        control.ops.write_bytes(canonical([control.expected]))
    def record():
        records.append(copy.deepcopy(control.result))
        if fault == "journal" or fault == "after_write" and len(records) == 2:
            raise OSError("synthetic journal failure")
    def send(value):
        writes.append(value)
        if fault == "write":
            raise OSError("synthetic uncertain pipe write")
    def call():
        kwargs = dict(deadline=time.monotonic() + 10, exposure_s=1, log=log)
        if phase == "grant":
            control.dispatch({}, SimpleNamespace(send_input=send), record, **kwargs)
        else:
            control.advance(SimpleNamespace(send_input=send), record, world="unused", **kwargs)
    with pytest.raises(OSError):
        call()
    if phase == "revoke":
        assert saved_operators(tmp_path / "operator-control.intermediate-ops.json")["operators"] == [control.expected]
    before = list(writes)
    with pytest.raises(Fault, match="ALREADY_ATTEMPTED"):
        call()
    assert writes == before


@pytest.mark.parametrize("change", [None, "wrong_target", "missing_effect", "restore", "counter", "extra_command",
                                  "clear", "scope", "avatar", "intermediate", "log", "feedback", "phase", "off_thread"])
def test_complete_roundtrip_requires_saved_effect_restore_and_permanent_taint(reference, tmp_path, change):  # noqa: F811
    _, control = prepare(reference)
    log, prefix, writes, proc = begin(control, tmp_path)
    assert not control.advance(proc, lambda: None, world="unused", log=log,
                               deadline=time.monotonic()+10, exposure_s=1)
    assert writes == ["op FixtureActor\n"]
    log.write_text("[native] Made FixtureActor a server operator\n")
    entry = control.expected.copy()
    if change == "wrong_target":
        entry["uuid"] = "22222222-2222-2222-2222-222222222222"
    control.ops.write_bytes(canonical([] if change == "missing_effect" else [entry]))
    if change in {"wrong_target", "missing_effect"}:
        with pytest.raises(Fault, match="OPERATOR_CONTROL_INTERMEDIATE_UNPROVEN"):
            control.advance(proc, lambda: None, world="unused", log=log, deadline=time.monotonic()+10, exposure_s=1)
        assert writes == ["op FixtureActor\n"]
        return
    control.advance(proc, lambda: None, world="unused", log=log, deadline=time.monotonic()+10, exposure_s=1)
    assert writes == ["op FixtureActor\n", "deop FixtureActor\n"]
    log.write_text(log.read_text() + "Made FixtureActor no longer a server operator\n")
    control.ops.write_bytes(b"[]")
    terminal = SetupHistory(policy=POLICY, phase="stop", transaction_id=None,
        attempts=dict.fromkeys(ROUTES, 0) | {"command_attempt": 3, "native_stop_command": 1,
            "operator_add": 1, "operator_remove": 1}, off_thread_attempts=0, overflowed=False)
    support = HistorySupport(policy=POLICY, vanilla_hooks_verified=True, team_hooks_verified=True,
                             all_mutation_routes_covered=False)
    history = qualify_history(support, terminal)
    report = {k: prefix[k] for k in ("campaign_id", "epoch", "server_boot_id", "launch_identity")}
    report.update(setup_startup=prefix["startup"], setup_history=history, avatar_ticks_at_last_sample={}, craft_witnesses=[])
    errors = {"restore": "RESTORE_UNPROVEN", "counter": "HISTORY_MISMATCH", "extra_command": "HISTORY_MISMATCH",
              "clear": "HISTORY_MISMATCH", "scope": "INSPECTION_SCOPE", "avatar": "HISTORY_MISMATCH",
              "intermediate": "INTERMEDIATE_CHANGED", "log": "LOG_CHANGED", "feedback": "FEEDBACK",
              "phase": "HISTORY_MISMATCH", "off_thread": "HISTORY_MISMATCH"}
    if change == "restore":
        control.ops.write_bytes(canonical([entry]))
    elif change in {"counter", "extra_command"}:
        history["terminal"]["attempts"]["operator_remove" if change == "counter" else "command_attempt"] += 1
    elif change == "clear":
        history["observed_history_clear"] = True
    elif change == "scope":
        report["epoch"] = 2
    elif change == "avatar":
        report["avatar_ticks_at_last_sample"] = {ACTOR: 1}
    elif change == "intermediate":
        (tmp_path / "operator-control.intermediate-ops.json").write_bytes(b"[]")
    elif change == "log":
        log.write_text(log.read_text().replace("[native]", "[changed]"))
    elif change == "feedback":
        log.write_text(log.read_text().split("Made FixtureActor no longer")[0])
    elif change == "phase":
        history["terminal"]["phase"] = "startup"
    elif change == "off_thread":
        history["terminal"]["off_thread_attempts"] = 1
    if change:
        with pytest.raises(Fault, match="OPERATOR_CONTROL_" + errors[change]):
            control.finish(report, "unused", log)
    else:
        result = control.finish(report, "unused", log)
        assert result["state"] == "completed_negative_control" and result["intermediate_operator_verified"]
        assert not result["terminal_history"]["observed_history_clear"] and not result["scoring_eligible"]


@pytest.mark.parametrize("mode,code", [("normal", None), ("no-effect", "OPERATOR_CONTROL_INTERMEDIATE_UNPROVEN"),
                                     ("wrong-restore", "OPERATOR_CONTROL_RESTORE_UNPROVEN")])
def test_owned_signed_jvm_operator_roundtrip_and_failed_effects(reference, tmp_path, mode, code):  # noqa: F811
    java, cp = os.environ.get("STRATA_TELEMETRY_TEST_JAVA"), os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if os.name != "nt" or not java or not cp:
        pytest.skip("Explicit Windows/JVM fixture profile required")
    from strata_evaluator.reference_launch import ReferenceLauncher
    store, setup, _, _, _ = reference
    level = Path(setup["fixture_directory"]) / "level.dat"
    nbt(level, 0)
    setup["fixture_files"]["level.dat"] = pin(level)
    receipt, _ = prepare(reference)
    module = tmp_path / "synthetic-module.jar"
    module.write_bytes(b"fixture identity, not a game mod")
    bootstrap = Path(__file__).resolve().parents[1] / "src/mcbench/process_bootstrap.py"
    files = [Path(java), Path(sys.executable), bootstrap, module]
    plan = {"schema": "strata/PrivateReferenceLaunch/7", "instance_id": "i", "setup_digest": receipt["setup_digest"],
        "mode": "synthetic-fixture", "executable": {"path": java, **pin(Path(java))},
        "module_file": {"path": str(module), **pin(module)},
        "immutable_files": [{"path": str(p), **pin(p)} for p in files], "immutable_trees": [],
        "fixture_arguments": ["-cp", Path(cp).read_text(), "io.github.opencnid.strata.telemetry.SetupControlFixture",
            "{config}", "{game}", "{module}", "25569", "operator-" + mode],
        "evidence_directory": str(tmp_path / "launch"), "server_port": 25569,
        "max_wall_s": 10, "ready_run_s": 1, "graceful_stop_s": 2, "setup_control": target()}
    launcher = ReferenceLauncher(store)
    result = launcher.run(plan)
    if code:
        assert result["status"] == "uncertain" and result["error"] == code, result
    else:
        assert result["status"] == "stopped_reference", result
        assert result["setup_control"]["state"] == "completed_negative_control"
        assert not result["setup_control"]["terminal_history"]["observed_history_clear"]
        assert not result["scoring_eligible"]
    with pytest.raises(Fault):
        launcher.run(plan)
