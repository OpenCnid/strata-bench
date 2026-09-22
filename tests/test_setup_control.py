"""Fixed private negative control: synthetic data, real signing and optional owned JVM."""

import copy
import gzip
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault
from strata_evaluator.setup_control import COMMANDS, SetupControl, SetupControlPlan, saved_mode, startup_prefix
from strata_evaluator.telemetry_auth import inspect_authenticated_spool
from test_craft_reference import reference, seal  # noqa: F401
from test_setup_facts import native  # noqa: F401
from test_setup_history import history, histories  # noqa: F401
from test_saved_blocks import root_bytes
from test_craft_reference import pin


def nbt(path, mode):
    path.write_bytes(gzip.compress(root_bytes({"Data": (10, {"GameType": (3, mode)})})))


def source(history, tmp_path):  # noqa: F811 - shared pytest fixture
    _, authority, _ = seal(history)
    folder = tmp_path / "live-spool"
    folder.mkdir()
    path = folder / "boot.authenticated.jsonl"
    path.write_bytes(history[-1].read_bytes())
    return folder, authority, path, history[2][0]["server_boot_id"]


def test_prefix_waits_for_complete_authenticated_startup_then_returns_bound_facts(history, tmp_path):  # noqa: F811
    folder, authority, path, boot = source(history, tmp_path)
    full = path.read_bytes()
    lines = full.splitlines(keepends=True)
    path.write_bytes(b"".join(lines[:3]) + lines[3][:-1])
    assert startup_prefix(folder, authority, boot) is None
    path.write_bytes(full)
    prefix = startup_prefix(folder, authority, boot)
    assert prefix["last_event_seq"] == 4 and prefix["startup"]["phase"] == "startup"
    assert prefix["server_boot_id"] == boot


@pytest.mark.parametrize("change", ["module", "hooks", "taint", "creative", "operator", "scope", "order", "signature"])
def test_unqualified_or_unauthenticated_prefix_cannot_admit_control(history, tmp_path, change):  # noqa: F811
    events = history[2]
    if change == "module":
        events[0]["payload_schema"] = "strata/ServerStarted/7"
    elif change == "hooks":
        events[0]["payload"]["setup_history_support"]["team_hooks_verified"] = False
    elif change == "taint":
        histories(events)[0]["payload"]["attempts"]["operator_add"] = 1
    elif change in {"creative", "operator"}:
        server = next(e for e in events if e["kind"] == "setup_snapshot")["payload"]["server"]
        if change == "creative":
            server["world_game_mode"] = "creative"
        else:
            server["operator_levels"] = [4]
    elif change == "scope":
        events[2]["actor_ids"] = ["foreign"]
    elif change == "order":
        events[2]["kind"] = "server_health"
    folder, authority, path, boot = source(history, tmp_path)
    if change == "signature":
        path.write_bytes(path.read_bytes().replace(b'"mac":"', b'"mac":"0', 1))
    with pytest.raises((Fault, ValidationError)):
        startup_prefix(folder, authority, boot)


@pytest.mark.parametrize("stage", ["none", "journal", "write", "after_write"])
def test_dispatch_is_fixed_journalled_and_never_replayed_after_uncertainty(stage, tmp_path):
    control = SetupControl({"mode": 0, "file_sha256": "a" * 64})
    log = tmp_path / "server.log"
    log.write_bytes(b"")
    calls = []
    def record():
        calls.append(("record", copy.deepcopy(control.result)))
        if stage == "journal" or stage == "after_write" and len(calls) == 3:
            raise OSError("synthetic journal fault")
    def send(value):
        calls.append(("send", value))
        if stage == "write":
            raise OSError("synthetic ambiguous pipe write")
    def dispatch():
        control.dispatch({"scope": "synthetic"}, SimpleNamespace(send_input=send), record,
                         deadline=time.monotonic() + 10, exposure_s=1, log=log)
    if stage == "none":
        dispatch()
        assert control.result["state"] == "awaiting_saved_effect"
    else:
        with pytest.raises(OSError):
            dispatch()
    assert calls[0][0] == "record" and calls[0][1]["state"] == "dispatching"
    assert [value for kind, value in calls if kind == "send"] == ([] if stage == "journal" else ["\n".join(COMMANDS[:2]) + "\n"])
    before = len(calls)
    with pytest.raises(Fault, match="SETUP_CONTROL_ALREADY_ATTEMPTED"):
        dispatch()
    assert len(calls) == before


def test_control_rejects_arbitrary_text_baseline_and_expired_dispatch():
    with pytest.raises(ValidationError):
        SetupControlPlan.model_validate({"policy": "private-world-mode-roundtrip/1", "purpose": "negative_control",
                                         "command": "give @a minecraft:diamond"})
    with pytest.raises(Fault, match="SETUP_CONTROL_BASELINE_MODE"):
        SetupControl({"mode": 1})
    control = SetupControl({"mode": 0})
    with pytest.raises(Fault, match="SETUP_CONTROL_DEADLINE"):
        control.dispatch({}, None, None, deadline=time.monotonic(), exposure_s=1, log="unused")
    assert not control.attempted


@pytest.mark.parametrize("stage", ["journal", "write", "after_write"])
def test_restore_intent_and_snapshot_survive_ambiguous_failure_without_replay(tmp_path, stage):
    world = tmp_path / "world"
    world.mkdir()
    nbt(world / "level.dat", 0)
    log = tmp_path / "server.log"
    log.write_bytes(b"")
    control = SetupControl(saved_mode(world / "level.dat"))
    control.dispatch({}, SimpleNamespace(send_input=lambda text: None), lambda: None,
                     deadline=time.monotonic() + 10, exposure_s=1, log=log)
    # Repeated reads while the two-command response is incomplete perform no write.
    writes = []
    proc = SimpleNamespace(send_input=writes.append)
    for _ in range(2):
        assert not control.advance(proc, lambda: None, world=world, log=log,
                                   deadline=time.monotonic() + 10, exposure_s=1)
    assert not writes and not control.restore_attempted
    log.write_text("The default game mode is now Creative Mode\nSaved the game\n")
    nbt(world / "level.dat", 1)
    records = []
    def record():
        records.append(copy.deepcopy(control.result))
        if stage == "journal" or stage == "after_write" and len(records) == 2:
            raise OSError("synthetic durable restore failure")
    def send(text):
        writes.append(text)
        if stage == "write":
            raise OSError("synthetic ambiguous restore write")
    def advance():
        return control.advance(SimpleNamespace(send_input=send), record, world=world, log=log,
                               deadline=time.monotonic() + 10, exposure_s=1)
    with pytest.raises(OSError):
        advance()
    assert records[0]["state"] == "restore_dispatching" and records[0]["intermediate_saved"]["mode"] == 1
    assert saved_mode(tmp_path / "setup-control.intermediate-level.dat")["mode"] == 1
    assert writes == ([] if stage == "journal" else ["defaultgamemode survival\n"])
    with pytest.raises(Fault, match="SETUP_CONTROL_RESTORE_ALREADY_ATTEMPTED"):
        advance()


@pytest.mark.parametrize("change", ["none", "counter", "extra_command", "avatar", "restore", "feedback", "scope",
                                   "intermediate_archive", "log_prefix"])
def test_finished_control_joins_signed_taint_feedback_and_restored_independent_save(history, tmp_path, change):  # noqa: F811
    # Remove the fabricated craft: this profile admits no participant.
    events = history[2]
    events[:] = [e for e in events if e["kind"] not in {"craft_begin", "craft_end", "craft_callback"}
                 and not (e["kind"] in {"setup_snapshot", "setup_history"}
                          and e["payload"]["phase"] in {"craft_begin", "craft_end"})]
    for event in events:
        if event["kind"] == "server_health":
            event["payload"]["avatar_ticks_since_boot"] = {}
    from test_setup_facts import renumber
    renumber(events)
    histories(events)[-1]["payload"]["attempts"].update(command_attempt=4, native_stop_command=1, world_mode=2)
    folder, authority, path, boot = source(history, tmp_path)
    prefix = startup_prefix(folder, authority, boot)
    report = inspect_authenticated_spool(path, Path(authority.key_file).with_name("authority.json"))
    world = tmp_path / "saved-world"
    world.mkdir()
    nbt(world / "level.dat", 0)
    baseline = saved_mode(world / "level.dat")
    control = SetupControl(baseline)
    log = tmp_path / "server.log"
    log.write_bytes(b"")
    control.dispatch(prefix, SimpleNamespace(send_input=lambda text: None), lambda: None,
                     deadline=time.monotonic() + 10, exposure_s=1, log=log)
    log.write_text("[native] The default game mode is now Creative Mode\n[native] Saved the game\n")
    nbt(world / "level.dat", 1)
    control.advance(SimpleNamespace(send_input=lambda text: None), lambda: None, world=world, log=log,
                    deadline=time.monotonic() + 10, exposure_s=1)
    with log.open("a") as stream:
        stream.write("[native] The default game mode is now Survival Mode\n")
    nbt(world / "level.dat", 0)
    if change in {"counter", "extra_command"}:
        report["setup_history"]["terminal"]["attempts"]["world_mode" if change == "counter" else "command_attempt"] += 1
    elif change == "avatar":
        report["avatar_ticks_at_last_sample"] = {"foreign": 1}
    elif change == "restore":
        nbt(world / "level.dat", 1)
    elif change == "feedback":
        log.write_text("The default game mode is now Survival Mode\n")
    elif change == "scope":
        report["epoch"] += 1
    elif change == "intermediate_archive":
        nbt(tmp_path / "setup-control.intermediate-level.dat", 0)
    elif change == "log_prefix":
        log.write_bytes(log.read_bytes().replace(b"[native]", b"[altered]", 1))
    if change != "none":
        code = {"counter": "SETUP_CONTROL_HISTORY_MISMATCH", "extra_command": "SETUP_CONTROL_HISTORY_MISMATCH",
                "avatar": "SETUP_CONTROL_HISTORY_MISMATCH", "restore": "SETUP_CONTROL_RESTORE_UNPROVEN",
                "feedback": "SETUP_CONTROL_FEEDBACK_MISSING", "scope": "SETUP_CONTROL_INSPECTION_SCOPE",
                "intermediate_archive": "SETUP_CONTROL_INTERMEDIATE_CHANGED",
                "log_prefix": "SETUP_CONTROL_LOG_CHANGED"}[change]
        with pytest.raises(Fault, match=code):
            control.finish(report, world, log)
    else:
        result = control.finish(report, world, log)
        assert result["state"] == "completed_negative_control" and result["native_mutation_observed"]
        assert result["final_mode_matches_baseline"] and not result["scoring_eligible"]


@pytest.fixture
def control_launch(reference, tmp_path):  # noqa: F811
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if os.name != "nt" or not java or not classpath:
        pytest.skip("Explicit pinned Windows/JVM profile required; synthetic world only")
    from strata_evaluator.reference_launch import ReferenceLauncher
    store, setup, _, directory, _ = reference
    level = Path(setup["fixture_directory"]) / "level.dat"
    nbt(level, 0)
    setup["fixture_files"]["level.dat"] = pin(level)
    seal_receipt = store.seal(setup, directory)
    module = tmp_path / "synthetic-module.jar"
    module.write_bytes(b"synthetic identity, not a game mod")
    bootstrap = Path(__file__).resolve().parents[1] / "src/mcbench/process_bootstrap.py"
    files = [Path(java), Path(sys.executable), bootstrap, module]
    plan = {"schema": "strata/PrivateReferenceLaunch/6", "instance_id": "i",
        "setup_digest": seal_receipt["setup_digest"], "mode": "synthetic-fixture",
        "executable": {"path": java, **pin(Path(java))}, "module_file": {"path": str(module), **pin(module)},
        "immutable_files": [{"path": str(path), **pin(path)} for path in files], "immutable_trees": [],
        "fixture_arguments": ["-cp", Path(classpath).read_text(),
            "io.github.opencnid.strata.telemetry.SetupControlFixture", "{config}", "{game}", "{module}", "25569", "normal"],
        "evidence_directory": str(tmp_path / "launch"), "server_port": 25569,
        "max_wall_s": 10, "ready_run_s": 1, "graceful_stop_s": 2,
        "setup_control": {"policy": "private-world-mode-roundtrip/1", "purpose": "negative_control"}}
    return ReferenceLauncher(store), plan


@pytest.mark.parametrize("mode,expected", [("normal", "stopped_reference"), ("no-effect", "uncertain"),
                                         ("wrong-restore", "uncertain")])
def test_actual_owned_jvm_control_and_failed_effects_keep_exact_terminal_evidence(control_launch, mode, expected):
    launcher, plan = control_launch
    plan["fixture_arguments"][-1] = mode
    result = launcher.run(plan)
    assert result["status"] == expected, result
    if mode != "no-effect":
        assert result["job_accounting"]["active_processes"] == 0
        assert result["held_members"]["signaled_processes"] == result["job_accounting"]["total_processes"]
    rows = launcher.database.connection.execute("SELECT state,body FROM reference_dispatches").fetchall()
    assert len(rows) == 1 and rows[0]["state"] == ("STOPPED" if mode == "normal" else "UNCERTAIN")
    if mode == "normal":
        assert result["setup_control"]["state"] == "completed_negative_control"
        assert result["setup_control"]["native_mutation_observed"] and not result["scoring_eligible"]
    else:
        assert result["error"] == ("SETUP_CONTROL_INTERMEDIATE_UNPROVEN" if mode == "no-effect" else "SETUP_CONTROL_RESTORE_UNPROVEN")
    with pytest.raises(Fault):
        launcher.run(plan)
