"""Private abort controls and owned Windows/JVM fixtures, never Minecraft."""

import copy
import json
import os
from pathlib import Path
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from mcbench.processes import ManagedProcess
from mcbench.storage import Fault
from strata_evaluator.reference_abort import (
    ABORT_FILE,
    AbortSignal,
    ParticipantAbortGuard,
    failure_record,
    request_abort,
)
from strata_evaluator.reference_launch import parse_launch_plan
from strata_evaluator.reference_participant import ParticipantReady, publish, submit_completion
from test_reference_launch import launch  # noqa: F401
from test_craft_reference import reference  # noqa: F401


def controlled(value, tmp_path, *, window=2, cleanup=500):
    value = copy.deepcopy(value)
    value.pop("ready_run_s")
    value.update(
        schema="strata/PrivateReferenceLaunch/3",
        outer_challenge="a" * 64,
        abort_cleanup_ms=cleanup,
        participant={
            "participant_id": "client",
            "window_s": window,
            "report_path": str(tmp_path / "client-report.json"),
        },
    )
    return value


@pytest.fixture
def scope(tmp_path):
    # A wire-only synthetic scope; never passed to a server launcher.
    return {
        "schema": "strata/PrivateReferenceLaunch/3",
        "instance_id": "reference",
        "participant": {"participant_id": "client"},
        "outer_challenge": "a" * 64,
        "abort_cleanup_ms": 2000,
    }


def wait_file(path, seconds=6):
    until = time.monotonic() + seconds
    while not path.exists():
        assert time.monotonic() < until, str(path)
        time.sleep(0.01)


def wait_terminal(process, seconds=3):
    until = time.monotonic() + seconds
    while process.poll() is None:
        assert time.monotonic() < until
        time.sleep(0.01)


def test_typed_failure_preserves_fault_code_without_exception_message():
    value = failure_record("client_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE"))
    assert value.code == "PROCESS_MEMBER_INVENTORY_UNAVAILABLE" and value.error_type == "Fault"
    value = failure_record("client_driver", RuntimeError("private credential value"))
    assert value.code == "REFERENCE_MONITOR_EXCEPTION" and "private" not in value.model_dump_json()
    assert (
        failure_record("client_driver", Fault("secret: not a code")).code
        == "REFERENCE_UNCLASSIFIED_FAULT"
    )
    with pytest.raises(ValidationError):
        failure_record("undeclared-phase", RuntimeError())


def test_abort_is_scope_bound_non_replacing_and_sticky(scope, tmp_path):
    signal = AbortSignal(scope, tmp_path)
    assert not signal.poll()
    request = request_abort(
        tmp_path, scope, "client_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
    )
    raw = (tmp_path / ABORT_FILE).read_bytes()
    assert signal.poll() and signal.result["request"] == request.model_dump(by_alias=True)
    with pytest.raises(FileExistsError):
        request_abort(tmp_path, scope, "outer_cleanup", RuntimeError())
    assert (tmp_path / ABORT_FILE).read_bytes() == raw
    (tmp_path / ABORT_FILE).unlink()  # Test attacker cannot clear an observed abort.
    assert signal.poll() and not signal.result["scoring_eligible"]


@pytest.mark.parametrize(
    "change", ["scope", "challenge", "plan", "extra", "truncated", "quota", "hardlink"]
)
def test_foreign_malformed_and_linked_control_abort_instead_of_admitting(scope, tmp_path, change):
    request_abort(tmp_path, scope, "server_monitor", Fault("PROCESS_STATE_UNAVAILABLE"))
    path = tmp_path / ABORT_FILE
    value = json.loads(path.read_bytes())
    if change == "scope":
        value["instance_id"] = "another"
    elif change == "challenge":
        value["challenge"] = "b" * 64
    elif change == "plan":
        value["launch_plan_digest"] = "b" * 64
    elif change == "extra":
        value["override"] = True
    if change == "hardlink":
        os.link(path, tmp_path / "alias")
    else:
        path.write_text(
            "{"
            if change == "truncated"
            else "x" * 8193
            if change == "quota"
            else json.dumps(value),
            encoding="utf-8",
        )
    signal = AbortSignal(scope, tmp_path)
    assert signal.poll() and signal.result["status"] == "invalid"
    assert not signal.result["scoring_eligible"]


def test_old_profile_and_unbounded_cleanup_are_rejected(scope, tmp_path):
    for version in ("1", "2"):
        with pytest.raises(Fault, match="REFERENCE_ABORT_PROFILE"):
            AbortSignal(scope | {"schema": "strata/PrivateReferenceLaunch/" + version}, tmp_path)
    for value in (0, 499, 15001, True):
        with pytest.raises(Fault, match="REFERENCE_ABORT_EXPOSURE"):
            ParticipantAbortGuard(scope | {"abort_cleanup_ms": value}, tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Owned Windows process handles")
def test_abort_watch_stops_owned_child_while_driver_is_blocked_and_denies_new_work(scope, tmp_path):
    marker = tmp_path / "late-effect"
    guard = ParticipantAbortGuard(scope, tmp_path)
    child = None
    try:
        child = guard.start(
            lambda: ManagedProcess(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    "import pathlib,sys,time;print('ready',flush=True);time.sleep(1);"
                    "pathlib.Path(sys.argv[1]).touch();time.sleep(30)",
                    str(marker),
                ],
                tmp_path,
                {},
                "",
            )
        )
        assert child.process.stdout.readline().strip() == b"ready"
        request_abort(
            tmp_path, scope, "client_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
        )
        # No driver check() needed for the independent stop path.
        wait_terminal(child)
        with pytest.raises(Fault, match="REFERENCE_OUTER_ABORT_REQUESTED"):
            guard.check()
        with pytest.raises(Fault, match="REFERENCE_OUTER_ABORT_REQUESTED"):
            guard.start(lambda: pytest.fail("late work admitted"))
        result = guard.close()
        assert (
            result["stop_attempted"] and result["watcher_terminal"] and not result["cleanup_errors"]
        )
        assert (
            result["abort"]["request"]["failure"]["code"] == "PROCESS_MEMBER_INVENTORY_UNAVAILABLE"
        )
        assert not result["guardian_qualified"] and not result["participant_execution_verified"]
        time.sleep(1.05)
        assert not marker.exists()
    finally:
        guard.close()
        if child:
            child.close()


@pytest.mark.skipif(os.name != "nt", reason="Owned Windows process handles")
def test_abort_during_creation_retains_and_stops_child_even_before_factory_returns(scope, tmp_path):
    guard = ParticipantAbortGuard(scope, tmp_path)
    created = []

    def factory():
        child = ManagedProcess(
            [sys.executable, "-I", "-c", "import time;time.sleep(30)"], tmp_path, {}, ""
        )
        created.append(child)
        request_abort(tmp_path, scope, "client_monitor", Fault("PROCESS_STATE_UNAVAILABLE"))
        return child

    try:
        with pytest.raises(Fault, match="REFERENCE_OUTER_ABORT_REQUESTED"):
            guard.start(factory)
        wait_terminal(created[0])
        assert guard.close()["stop_attempted"]
    finally:
        guard.close()
        for process in created:
            process.close()


@pytest.mark.skipif(os.name != "nt", reason="Owned Windows process handles")
def test_stalled_cleanup_does_not_claim_confirmed_guard_close(scope, tmp_path):
    scope = scope | {"abort_cleanup_ms": 500}
    guard = ParticipantAbortGuard(scope, tmp_path)
    release, entered = threading.Event(), threading.Event()
    child = guard.start(
        lambda: ManagedProcess(
            [sys.executable, "-I", "-c", "import time;time.sleep(30)"], tmp_path, {}, ""
        )
    )
    original_stop = child.stop

    def held_stop():
        entered.set()
        assert release.wait(3)
        original_stop()

    child.stop = held_stop
    try:
        request_abort(tmp_path, scope, "client_deadline", Fault("REFERENCE_CLIENT_DEADLINE"))
        assert entered.wait(2)
        began = time.monotonic()
        with pytest.raises(Fault, match="REFERENCE_ABORT_GUARD_UNCONFIRMED"):
            guard.close()
        assert time.monotonic() - began < 1.5 and child.poll() is None
        assert not guard.report()["watcher_terminal"]
    finally:
        release.set()
        wait_terminal(child)
        guard.close()


@pytest.mark.skipif(os.name != "nt", reason="Owned Windows process handles")
def test_cleanup_fault_is_preserved_and_handle_close_remains_a_backstop(scope, tmp_path):
    guard = ParticipantAbortGuard(scope, tmp_path)
    child = guard.start(
        lambda: ManagedProcess(
            [sys.executable, "-I", "-c", "import time;time.sleep(30)"], tmp_path, {}, ""
        )
    )

    def failed_stop():
        raise Fault("PROCESS_STOP_FAILED")

    child.stop = failed_stop
    try:
        request_abort(tmp_path, scope, "outer_cleanup", Fault("PROCESS_STATE_UNAVAILABLE"))
        report = guard.close()
        assert report["cleanup_errors"] == [
            {"phase": "outer_cleanup", "error_type": "Fault", "code": "PROCESS_STOP_FAILED"}
        ]
        assert not report["guardian_qualified"] and not report["scoring_eligible"]
        assert child.process.wait(timeout=3) is not None
    finally:
        child.close()


@pytest.mark.skipif(os.name != "nt", reason="Owned Windows process handles")
def test_owned_resource_quota_and_closed_admission(scope, tmp_path):
    guard = ParticipantAbortGuard(scope, tmp_path)
    children = []
    try:
        for _ in range(2):
            children.append(
                guard.start(
                    lambda: ManagedProcess(
                        [sys.executable, "-I", "-c", "import time;time.sleep(30)"], tmp_path, {}, ""
                    )
                )
            )
        with pytest.raises(Fault, match="REFERENCE_ABORT_OWNER_QUOTA"):
            guard.start(lambda: pytest.fail("third child admitted"))
        for child in children:
            child.stop()
        assert guard.close()["abort"] is None
        with pytest.raises(Fault, match="REFERENCE_ABORT_GUARD_CLOSED"):
            guard.check()
        with pytest.raises(Fault, match="REFERENCE_ABORT_GUARD_CLOSED"):
            guard.start(lambda: pytest.fail("closed guard admitted child"))
    finally:
        guard.close()


@pytest.mark.parametrize("outcome", ["failed", "completed", "missing"])
def test_actual_jvm_outer_abort_stops_normally_but_never_qualifies_reference(
    launch,  # noqa: F811 - imported shared pytest fixture
    tmp_path,
    outcome,
):
    launcher, original, setup = launch
    value = controlled(original, tmp_path)
    evidence = Path(value["evidence_directory"])

    def driver():
        wait_file(evidence / "participant-ready.json")
        ready = ParticipantReady.model_validate_json(
            (evidence / "participant-ready.json").read_bytes()
        )
        request_abort(
            evidence, value, "client_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
        )
        if outcome != "missing":
            report = Path(value["participant"]["report_path"])
            report.write_text(json.dumps({"status": outcome, "synthetic": True}), encoding="utf-8")
            submit_completion(evidence, ready, report, outcome)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(driver)
        result = launcher.run(value)
        future.result()
    assert result["status"] == "uncertain" and result["error"] == "REFERENCE_OUTER_ABORTED", result
    assert (
        result["outer_abort"]["request"]["failure"]["code"]
        == "PROCESS_MEMBER_INVENTORY_UNAVAILABLE"
    )
    assert result["exit_code"] == 0 and result["stop_sent"] and not result["forced_stop"]
    assert result["job_accounting"]["active_processes"] == 0
    assert (
        result["held_members"]["signaled_processes"] == result["job_accounting"]["total_processes"]
    )
    spool = next((evidence / "telemetry").glob("*.authenticated.jsonl"))
    with pytest.raises(Fault, match="CRAFT_LAUNCH_UNQUALIFIED"):
        launcher.store.inspect(setup["instance_id"], spool)
    with pytest.raises(Fault):
        launcher.run(value)
    assert (
        launcher.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 1
    )


def test_actual_jvm_foreign_abort_cannot_qualify(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    value = controlled(original, tmp_path)
    evidence = Path(value["evidence_directory"])

    def foreign():
        wait_file(evidence / "participant-ready.json")
        publish(evidence / ABORT_FILE, {"schema": "not-authorized"})

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(foreign)
        result = launcher.run(value)
        future.result()
    assert result["status"] == "uncertain" and result["outer_abort"]["status"] == "invalid"
    assert result["exit_code"] == 0 and not result["forced_stop"]


def test_actual_v3_normal_receipt_still_passes_only_coordination(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    value = controlled(original, tmp_path)
    evidence = Path(value["evidence_directory"])

    def driver():
        wait_file(evidence / "participant-ready.json")
        ready = ParticipantReady.model_validate_json(
            (evidence / "participant-ready.json").read_bytes()
        )
        report = Path(value["participant"]["report_path"])
        report.write_text('{"status":"completed","synthetic":true}', encoding="utf-8")
        submit_completion(evidence, ready, report, "completed")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(driver)
        result = launcher.run(value)
        future.result()
    assert result["status"] == "stopped_reference" and "outer_abort" not in result
    assert not result["participant"]["participant_execution_verified"]
    assert not result["scoring_eligible"]


def test_abort_before_readiness_never_publishes_client_admission(launch, tmp_path, monkeypatch):  # noqa: F811
    from strata_evaluator import reference_launch as module

    launcher, original, _ = launch
    value = controlled(original, tmp_path)
    evidence = Path(value["evidence_directory"])
    real = module.ManagedProcess

    def factory(*args, **kwargs):
        process = real(*args, **kwargs)
        request_abort(
            evidence, value, "server_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
        )
        return process

    monkeypatch.setattr(module, "ManagedProcess", factory)
    result = launcher.run(value)
    assert result["status"] == "uncertain" and "outer_abort" in result
    assert not (evidence / "participant-ready.json").exists()


def test_owned_child_abort_report_reaches_jvm_before_normal_server_stop(launch, tmp_path):  # noqa: F811
    launcher, original, _ = launch
    value = controlled(original, tmp_path, window=3, cleanup=2000)
    evidence = Path(value["evidence_directory"])

    def driver():
        wait_file(evidence / "participant-ready.json")
        ready = ParticipantReady.model_validate_json(
            (evidence / "participant-ready.json").read_bytes()
        )
        guard = ParticipantAbortGuard(value, evidence)
        child = None
        try:
            child = guard.start(
                lambda: ManagedProcess(
                    [
                        sys.executable,
                        "-I",
                        "-c",
                        "import time;print('ready',flush=True);time.sleep(30)",
                    ],
                    tmp_path,
                    {},
                    "",
                )
            )
            assert child.process.stdout.readline().strip() == b"ready"
            request_abort(
                evidence, value, "client_monitor", Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
            )
            wait_terminal(child)
            report = guard.close()
            assert not (evidence / "result.json").exists()
            path = Path(value["participant"]["report_path"])
            from strata_evaluator.craft_reference import write_new

            write_new(path, report)
            submit_completion(evidence, ready, path, "failed")
            return report
        finally:
            guard.close()
            if child:
                child.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(driver)
        result = launcher.run(value)
        report = future.result()
    assert result["status"] == "uncertain" and not result["forced_stop"]
    assert result["exit_code"] == 0 and result["participant"]["receipt"]["outcome"] == "failed"
    assert json.loads((evidence / "participant-report.json").read_bytes()) == report
    assert report["stop_attempted"] and report["watcher_terminal"] and not report["cleanup_errors"]


def test_abort_arriving_during_final_receipt_check_cannot_become_a_pass(
    launch,  # noqa: F811 - imported shared pytest fixture
    tmp_path,
    monkeypatch,
):
    from strata_evaluator import reference_launch as module

    launcher, original, _ = launch
    value = controlled(original, tmp_path)
    evidence = Path(value["evidence_directory"])
    finish = module.ParticipantWindow.finish

    def late_abort(self):
        finish(self)
        request_abort(evidence, value, "outer_cleanup", Fault("PROCESS_STATE_UNAVAILABLE"))

    monkeypatch.setattr(module.ParticipantWindow, "finish", late_abort)

    def driver():
        wait_file(evidence / "participant-ready.json")
        ready = ParticipantReady.model_validate_json(
            (evidence / "participant-ready.json").read_bytes()
        )
        path = Path(value["participant"]["report_path"])
        path.write_text('{"synthetic":true}', encoding="utf-8")
        submit_completion(evidence, ready, path, "completed")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(driver)
        result = launcher.run(value)
        future.result()
    assert result["status"] == "uncertain" and result["error"] == "REFERENCE_OUTER_ABORTED"
    assert result["participant"]["status"] == "completed"
    assert result["outer_abort"]["request"]["failure"]["code"] == "PROCESS_STATE_UNAVAILABLE"


def test_v3_retains_strict_limits_and_requires_explicit_policy(launch, tmp_path):  # noqa: F811
    _, original, _ = launch
    value = controlled(original, tmp_path)
    assert parse_launch_plan(value).abort_cleanup_ms == 500
    for key, bad in (
        ("abort_cleanup_ms", 15001),
        ("max_wall_s", 601),
        ("outer_challenge", "unknown"),
    ):
        with pytest.raises(ValidationError):
            parse_launch_plan(value | {key: bad})
