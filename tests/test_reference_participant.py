"""Actual Windows leases and JVM coordinator fixtures, not authentic gameplay."""

from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import time

from pydantic import ValidationError
import pytest

from mcbench.storage import Fault, digest
from strata_evaluator.reference_launch import parse_launch_plan
from strata_evaluator.reference_participant import (
    ParticipantPlan, ParticipantWindow, publish, submit_completion, validate_paths,
)
from test_craft_reference import reference  # noqa: F401
from test_reference_launch import launch  # noqa: F401


def coordinated(plan, tmp_path):
    plan = copy.deepcopy(plan)
    plan["schema"] = "strata/PrivateReferenceLaunch/2"
    del plan["ready_run_s"]
    plan["participant"] = {"participant_id": "client", "window_s": 2,
                           "report_path": str(tmp_path / "client-report.json")}
    return plan


def wait_file(path):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_bytes())
        time.sleep(0.02)
    raise AssertionError("Coordinator never published its readiness")


def driver(plan, mode):
    evidence = Path(plan["evidence_directory"])
    ready = wait_file(evidence / "participant-ready.json")
    assert ready["launch_plan_digest"] == digest(plan)
    assert ready["setup_digest"] == plan["setup_digest"]
    assert ready["instance_id"] == plan["instance_id"]
    if mode == "missing":
        return
    if mode == "foreign":
        ready["server_boot_id"] = "other-boot"
    report = Path(plan["participant"]["report_path"])
    report.write_text('{"synthetic_fixture":true,"execution_certified":false}', encoding="utf-8")
    submit_completion(evidence, ready, report, "failed" if mode == "failed" else "completed")


@pytest.mark.parametrize("mode,error", [("completed", None), ("foreign", "REFERENCE_PARTICIPANT_SCOPE"),
    ("failed", "REFERENCE_PARTICIPANT_FAILED"), ("missing", "REFERENCE_PARTICIPANT_TIMEOUT")])
def test_actual_jvm_bound_readiness_terminal_receipt_and_missing_or_wrong_scope_fail_closed(launch, tmp_path, mode, error):  # noqa: F811
    launcher, original, _ = launch
    plan = coordinated(original, tmp_path)
    with ThreadPoolExecutor(max_workers=1) as executor:
        client = executor.submit(driver, plan, mode)
        result = launcher.run(plan)
        client.result()
    assert result["launch_binding_verified"] and result["stop_sent"] and not result["forced_stop"], result
    assert result["exit_code"] == 0
    assert result["held_members"]["signaled_processes"] == result["job_accounting"]["total_processes"]
    assert not result["scoring_eligible"] and not result["participant"]["participant_execution_verified"]
    assert result["status"] == ("uncertain" if error else "stopped_reference"), result
    if error:
        assert result["error"] == error
        spool = next((Path(plan["evidence_directory"]) / "telemetry").glob("*.authenticated.jsonl"))
        with pytest.raises(Fault, match="CRAFT_LAUNCH_UNQUALIFIED"):
            launcher.store.inspect("i", spool)
    else:
        preserved = (Path(plan["evidence_directory"]) / "participant-report.json").read_bytes()
        assert hashlib.sha256(preserved).hexdigest() == result["participant"]["receipt"]["report_sha256"]
        assert launcher.store.inspect("i", next((Path(plan["evidence_directory"]) / "telemetry")
            .glob("*.authenticated.jsonl")))["launch_binding_verified"]
    with pytest.raises(Fault):
        launcher.run(plan)


@pytest.mark.parametrize("change", ["mixed_version", "long_window", "excess_exposure", "old_report", "game_report"])
def test_invalid_participant_plan_rejected_before_consuming_launch(launch, tmp_path, change):  # noqa: F811
    launcher, original, setup = launch
    plan = coordinated(original, tmp_path)
    if change == "mixed_version":
        plan["ready_run_s"] = 1
    elif change == "long_window":
        plan["participant"]["window_s"] = 421
    elif change == "excess_exposure":
        plan["participant"]["window_s"] = 9
    elif change == "old_report":
        Path(plan["participant"]["report_path"]).write_text("{}")
    else:
        plan["participant"]["report_path"] = str(Path(setup["game_directory"]) / "report.json")
    with pytest.raises((Fault, ValidationError)):
        launcher.run(plan)
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM craft_reference_launches").fetchone()[0] == 0


@pytest.fixture
def window(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows deny-write/atomic-publication profile")
    from types import SimpleNamespace
    evidence = tmp_path / "private-coordinator"
    evidence.mkdir()
    participant = ParticipantPlan(participant_id="client", window_s=2, report_path=str(tmp_path / "report.json"))
    launch_plan = {"instance_id": "i", "setup_digest": "a" * 64}
    identity = SimpleNamespace(**launch_plan, model_dump=lambda **_: launch_plan)
    value = ParticipantWindow(participant, evidence, identity, "boot", 100, 1000, 110, clock=lambda: 100)
    value.publish()
    yield value
    value.close()


def receipt(window):
    Path(window.plan.report_path).write_text('{"fixture":true}')
    submit_completion(window.evidence, window.ready, Path(window.plan.report_path), "completed")


@pytest.mark.parametrize("change,code", [("wrong_digest", "REFERENCE_PARTICIPANT_REPORT"),
    ("missing_report", "TELEMETRY_AUTH_FILE"), ("too_large", "TELEMETRY_AUTH_FILE"),
    ("malformed", "ValidationError"), ("late", "REFERENCE_PARTICIPANT_TIMEOUT"),
    ("late_during_read", "REFERENCE_PARTICIPANT_TIMEOUT")])
def test_report_failures_are_retained_without_acceptance(window, change, code):
    receipt(window)
    report = Path(window.plan.report_path)
    if change == "wrong_digest":
        report.write_text('{"changed":true}')
    elif change == "missing_report":
        report.unlink()
    elif change == "too_large":
        with report.open("wb") as stream:
            stream.truncate(8 * 1024**2 + 1)
    elif change == "malformed":
        (window.evidence / "participant-completion.json").write_text('{"schema":"wrong"}')
    elif change == "late_during_read":
        window.clock = lambda: 102
    assert window.poll(102 if change == "late" else 100)
    assert window.result["status"] == "uncertain" and window.result["error"] == code
    with pytest.raises(Fault, match=code):
        window.finish()


def test_receipt_and_report_locked_until_close_and_publisher_does_not_replace(window):
    receipt(window)
    assert window.poll(100) and window.result["status"] == "completed"
    window.finish()
    for path in (Path(window.plan.report_path), window.evidence / "participant-completion.json"):
        with pytest.raises(PermissionError):
            path.write_text("changed")
    with pytest.raises(OSError):
        publish(window.evidence / "participant-ready.json", {})
    assert json.loads((window.evidence / "participant-ready.json").read_bytes())["challenge"] == window.ready.challenge
    window.close()
    Path(window.plan.report_path).write_text("now unlocked")


def test_full_window_must_fit_remaining_server_exposure(window):
    from types import SimpleNamespace
    with pytest.raises(Fault, match="REFERENCE_PARTICIPANT_EXPOSURE"):
        ParticipantWindow(window.plan, window.evidence, SimpleNamespace(), "boot", 100, 1000, 101)


def test_report_cannot_be_placed_in_authority_or_coordinator(window, tmp_path):
    for root in (window.evidence, tmp_path / "authority"):
        plan = window.plan.model_copy(update={"report_path": str(root / "report.json")})
        with pytest.raises(Fault):
            validate_paths(plan, window.evidence, tmp_path / "game", tmp_path / "authority")


def test_legacy_timing_policy_stays_distinct(launch, tmp_path):  # noqa: F811
    _, plan, _ = launch
    assert parse_launch_plan(plan).ready_run_s == 1
    assert not hasattr(parse_launch_plan(coordinated(plan, tmp_path)), "ready_run_s")


def test_report_alias_is_rejected(window, tmp_path):
    receipt(window)
    alias = tmp_path / "report-alias.json"
    os.link(window.plan.report_path, alias)
    assert window.poll(100) and window.result["status"] == "uncertain"
    assert window.result["error"] == "TELEMETRY_AUTH_FILE"


def test_premature_completion_cannot_trigger_early_stop_or_be_reused(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    plan = coordinated(original, tmp_path)
    evidence = Path(plan["evidence_directory"])

    def premature():
        wait_file(evidence / "launch-plan.json")
        publish(evidence / "participant-completion.json", {})

    with ThreadPoolExecutor(max_workers=1) as executor:
        attempt = executor.submit(premature)
        result = launcher.run(plan)
        attempt.result()
    assert result["status"] == "uncertain" and result["error"] == "REFERENCE_PARTICIPANT_PREMATURE", result
    assert not (evidence / "participant-ready.json").exists()
    with pytest.raises(Fault):
        launcher.run(plan)


def test_boot_cannot_silently_shorten_registered_participant_window(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    plan = coordinated(original, tmp_path)
    plan["participant"]["window_s"] = plan["max_wall_s"]
    result = launcher.run(plan)
    assert result["status"] == "uncertain" and result["error"] == "REFERENCE_PARTICIPANT_EXPOSURE", result
    assert result["launch_binding_verified"]
    assert not (Path(plan["evidence_directory"]) / "participant-ready.json").exists()
    with pytest.raises(Fault):
        launcher.run(plan)


def test_actual_pack_participant_requires_explicit_client_registration_before_reservation(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    plan = coordinated(original, tmp_path)
    plan.update(mode="e9e-serverstarter", fixture_arguments=[])
    with pytest.raises(Fault, match="REFERENCE_CLIENT_BINDING_REQUIRED"):
        launcher.run(plan)
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM craft_reference_launches").fetchone()[0] == 0


def test_synthetic_or_legacy_profile_cannot_silently_accept_real_client_binding(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    for plan in (original, coordinated(original, tmp_path)):
        with pytest.raises(Fault, match="REFERENCE_CLIENT_PROFILE"):
            launcher.run(plan, client_binding={})
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM craft_reference_launches").fetchone()[0] == 0
