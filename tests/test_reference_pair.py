"""Owned Windows/Python/JVM pair faults; no Minecraft, model or score."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from mcbench.storage import Fault, canonical
from mcbench.processes import ProcessInventoryFault
from strata_evaluator import reference_pair as module
from strata_evaluator.reference_pair import ReferencePair
from test_reference_launch import launch  # noqa: F401
from test_craft_reference import reference, pin  # noqa: F401


DRIVER = """
import json, sys, time
from pathlib import Path
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault
from strata_evaluator.reference_abort import ParticipantAbortGuard, failure_record
from strata_evaluator.reference_participant import ParticipantReady, publish, submit_completion
root = Path(__file__).parent
launch = json.loads((root/'launch.json').read_bytes())
mode = json.loads((root/'driver-mode.json').read_bytes())
evidence = Path(launch['evidence_directory'])
ready = ParticipantReady.model_validate_json((evidence/'participant-ready.json').read_bytes())
if mode == 'missing':
    time.sleep(.3)
    raise SystemExit(0)
if mode == 'hang':
    time.sleep(30)
guard = ParticipantAbortGuard(launch, evidence)
result = {'status':'fail', 'synthetic':True, 'scoring_eligible':False}
child = None
try:
    child = guard.start(lambda: ManagedProcess(
        [sys.executable, '-I', '-c', "import time;print('ready',flush=True);time.sleep(30)"], root, {}, ''))
    assert child.process.stdout.readline().strip() == b'ready'
    time.sleep(.1)  # Let the outer fixture observe the now-running full child chain.
    publish(root/'driver-ready.json', {'synthetic':True})
    deadline = time.monotonic() + (.4 if mode in ('normal', 'list') else 10)
    while time.monotonic() < deadline:
        guard.check()
        time.sleep(.025)
    result['status'] = 'pass'
except Exception as error:
    result['failure'] = failure_record('client_driver', error).model_dump()
finally:
    if child:
        child.stop()
    result['abort_guard'] = guard.close()
    if result['abort_guard']['abort']:
        result['status'] = 'fail'
    report = Path(launch['participant']['report_path'])
    publish(report, [] if mode == 'list' else result)
    submit_completion(evidence, ready, report, 'completed' if result['status']=='pass' else 'failed')
raise SystemExit(0 if result['status']=='pass' else 1)
"""


@pytest.fixture
def pair(launch, tmp_path):  # noqa: F811
    launcher, launch_plan, setup = launch
    launch_plan = copy.deepcopy(launch_plan)
    launch_plan.pop("ready_run_s")
    launch_plan.update(
        schema="strata/PrivateReferenceLaunch/3",
        outer_challenge="a" * 64,
        abort_cleanup_ms=1000,
        participant={
            "participant_id": "client",
            "window_s": 4,
            "report_path": str(tmp_path / "client-report.json"),
        },
    )
    (tmp_path / "launch.json").write_bytes(canonical(launch_plan))
    (tmp_path / "client.py").write_text(DRIVER, encoding="utf-8")
    (tmp_path / "driver-mode.json").write_text('"normal"', encoding="utf-8")
    root = Path(__file__).resolve().parents[1]

    def pinned(path):
        return {"path": str(path), **pin(path)}

    plan = {
        "schema": "strata/PrivateReferencePair/1",
        "launch_file": pinned(tmp_path / "launch.json"),
        "client_driver": pinned(tmp_path / "client.py"),
        "python": pinned(Path(sys.executable)),
        "bootstrap": pinned(root / "src/mcbench/process_bootstrap.py"),
        "source_root": str(root),
        "inputs": [
            pinned(root / "evaluator/src/strata_evaluator" / name)
            for name in (
                "reference_pair.py",
                "reference_abort.py",
                "reference_launch.py",
                "reference_participant.py",
            )
        ]
        + [pinned(tmp_path / "driver-mode.json")],
        "evidence_directory": str(tmp_path / "pair"),
        "client_window_ms": 2500,
        "finalize_ms": 1000,
    }
    return ReferencePair(launcher.database), plan, launch_plan, setup


def mode(plan, name):
    path = Path(plan["client_driver"]["path"]).with_name("driver-mode.json")
    path.write_text(json.dumps(name), encoding="utf-8")
    plan["inputs"][-1] = {"path": str(path), **pin(path)}


def test_actual_owned_pair_completes_only_coordination_and_preserves_exact_reports(pair):
    runner, plan, launch_plan, _ = pair
    result = runner.run(plan)
    assert result["status"] == "stopped_pair", result
    assert not result["failures"] and not result["scoring_eligible"]
    assert not result["guardian_qualified"] and not result["participant_execution_verified"]
    for role in ("client", "server"):
        state = result[role + "_process"]
        assert state["terminal_verified"] and not state["forced"] and state["logs_complete"]
        assert state["exit_code"] == 0 and not state["errors"]
    assert (Path(plan["evidence_directory"]) / "client_result.json").read_bytes() == Path(
        launch_plan["participant"]["report_path"]
    ).read_bytes()
    before = list(runner.database.connection.execute("SELECT * FROM reference_pairs"))
    with pytest.raises(Fault, match="REFERENCE_PAIR_PATH"):
        runner.run(plan)
    assert [tuple(row) for row in before] == [
        tuple(row) for row in runner.database.connection.execute("SELECT * FROM reference_pairs")
    ]


def test_owned_pair_observes_dynamic_desktop_guardian_jobs_through_close(pair):
    """The real nested lifecycle used by the client, with a disposable JVM body."""
    java = os.environ.get("STRATA_CLIENT_TEST_JAVA")
    classpath = os.environ.get("STRATA_CLIENT_TEST_CLASSPATH")
    if not java or not classpath:
        pytest.skip("Explicit pinned client JVM fixture required")
    runner, plan, _, _ = pair
    driver = Path(plan["client_driver"]["path"])
    driver.write_bytes((Path(__file__).parent / "fixtures/reference_desktop_guardian.py").read_bytes())
    plan["client_driver"] = {"path": str(driver), **pin(driver)}
    config = driver.with_name("desktop-config.json")
    config.write_bytes(canonical({"java": java, "classpath": Path(classpath).read_text().strip()}))
    plan["inputs"].append({"path": str(config), **pin(config)})
    result = runner.run(plan)
    assert result["status"] == "stopped_pair", result
    assert not result["failures"] and not result["process_observations"]
    assert not result["scoring_eligible"] and not result["guardian_qualified"]
    for role in ("client", "server"):
        owned = result[role + "_process"]
        assert owned["terminal_verified"] and not owned["forced"] and owned["logs_complete"]
    child = result["client_result"]["value"]
    assert child["status"] == "pass" and child["input_desktop_unchanged"]
    assert child["inner_job"]["total_processes"] >= 1
    assert (child["inner_job"]["total_processes"] == child["inner_members"]["held_processes"]
            == child["inner_members"]["signaled_processes"])
    timing = child["guardian_timing"]
    assert timing["tree_result"] == "empty" and timing["wait_bound_ms"] == 500
    assert timing["tree_checked_after_ns"] - timing["wait_started_after_ns"] <= 500_000_000


@pytest.mark.parametrize("diagnostic", [False, True])
def test_monitor_fault_is_durable_before_cooperative_abort_and_never_becomes_pass(
    pair, monkeypatch, diagnostic
):
    runner, plan, launch_plan, setup = pair
    mode(plan, "cooperative")
    original = module.OwnedCli.observe
    once = []

    def observe(self):
        if (
            self.role == "client"
            and not once
            and Path(plan["client_driver"]["path"]).with_name("driver-ready.json").exists()
        ):
            once.append(True)
            if diagnostic:
                raise ProcessInventoryFault("membership_query", assigned=8, listed=8,
                                            retained=7, win32_error=5)
            raise Fault("PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
        return original(self)

    monkeypatch.setattr(module.OwnedCli, "observe", observe)
    request = module.request_abort

    def abort(*args):
        row = runner.database.connection.execute(
            "SELECT state,body FROM reference_pairs WHERE instance=?", (launch_plan["instance_id"],)
        ).fetchone()
        assert row["state"] == "ABORT_REQUESTED"
        assert (
            json.loads(row["body"])["failures"][0]["code"] == "PROCESS_MEMBER_INVENTORY_UNAVAILABLE"
        )
        observations = json.loads(row["body"])["process_observations"]
        assert len(observations) == int(diagnostic)
        if diagnostic:
            assert observations[0] == {
                "phase": "client_monitor", "schema": "strata/ProcessInventoryObservation/1",
                "stage": "membership_query", "assigned_processes": 8, "listed_processes": 8,
                "retained_processes": 7, "win32_error": 5,
            }
        return request(*args)

    monkeypatch.setattr(module, "request_abort", abort)
    result = runner.run(plan)
    assert result["status"] == "uncertain" and once
    assert result["failures"][0] == {
        "phase": "client_monitor",
        "error_type": "ProcessInventoryFault" if diagnostic else "Fault",
        "code": "PROCESS_MEMBER_INVENTORY_UNAVAILABLE",
    }
    assert result["client_result"]["value"]["status"] == "fail", result
    assert result["server_result"]["value"]["stop_sent"]
    assert not result["server_result"]["value"]["forced_stop"]
    assert (
        result["client_process"]["terminal_verified"]
        and result["server_process"]["terminal_verified"]
    )
    assert not result["client_process"]["forced"] and not result["server_process"]["forced"]
    spool = next(Path(launch_plan["evidence_directory"]).glob("telemetry/*.authenticated.jsonl"))
    with pytest.raises(Fault, match="CRAFT_PAIR_UNQUALIFIED"):
        runner.store.inspect(setup["instance_id"], spool)


@pytest.mark.parametrize(
    "kind,code",
    [("missing", "REFERENCE_PAIR_CLIENT_REPORT_MISSING"), ("hang", "REFERENCE_PAIR_HARD_DEADLINE")],
)
def test_missing_receipt_or_stalled_driver_retains_uncertainty_and_hard_deadline(pair, kind, code):
    runner, plan, launch_plan, _ = pair
    mode(plan, kind)
    started = time.monotonic()
    result = runner.run(plan)
    assert result["status"] == "uncertain" and any(f["code"] == code for f in result["failures"]), (
        result
    )
    assert time.monotonic() - started < 10
    assert result["client_result"]["missing_or_invalid"]
    assert not Path(launch_plan["participant"]["report_path"]).exists()
    assert (
        result["client_process"]["terminal_verified"]
        and result["server_process"]["terminal_verified"]
    )
    assert (Path(plan["evidence_directory"]) / "client-watchdog.json").exists() == (kind == "hang")


@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_first_monitor_never_starts_client(pair, monkeypatch, interrupted):
    runner, plan, _, _ = pair
    original = module.OwnedCli.observe

    def observe(self):
        if self.role == "server":
            if interrupted:
                raise KeyboardInterrupt()
            raise Fault("PROCESS_STATE_UNAVAILABLE")
        return original(self)

    monkeypatch.setattr(module.OwnedCli, "observe", observe)
    result = runner.run(plan)
    assert result["status"] == "uncertain" and "client_process" not in result
    assert not (Path(plan["evidence_directory"]) / "client-intent.json").exists()
    assert result["failures"][0]["code"] == (
        "REFERENCE_MONITOR_EXCEPTION" if interrupted else "PROCESS_STATE_UNAVAILABLE"
    )
    if interrupted:
        assert result["failures"][0]["error_type"] == "KeyboardInterrupt"
        row = runner.database.connection.execute("SELECT body FROM reference_pairs").fetchone()
        assert json.loads(row["body"])["failures"][0] == result["failures"][0]


def test_prior_interrupted_intent_cannot_be_overwritten_by_new_output_paths(pair):
    runner, plan, launch_plan, _ = pair
    original = {"status": "uncertain", "original": "retained missing terminal proof"}
    with runner.database.transaction() as db:
        db.execute(
            "INSERT INTO reference_pairs VALUES (?,?,?,?)",
            (launch_plan["instance_id"], "{}", "INTENT", canonical(original).decode()),
        )
    with pytest.raises(Fault, match="REFERENCE_PAIR_ALREADY_DISPATCHED"):
        runner.run(plan)
    row = runner.database.connection.execute("SELECT state,body FROM reference_pairs").fetchone()
    assert row["state"] == "INTENT" and json.loads(row["body"]) == original
    assert not Path(plan["evidence_directory"]).exists()
    assert (
        runner.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 0
    )


def test_independent_deadline_stops_owned_client_while_monitor_is_blocked(pair, monkeypatch):
    runner, plan, _, _ = pair
    mode(plan, "hang")
    original = module.OwnedCli.observe
    blocked = []

    def observe(self):
        if self.role == "client" and not blocked:
            blocked.append(True)
            original(self)
            time.sleep(3)
            assert self.process.poll() is not None
            assert (self.evidence / "client-watchdog.json").exists()
        return original(self)

    monkeypatch.setattr(module.OwnedCli, "observe", observe)
    result = runner.run(plan)
    assert blocked and result["status"] == "uncertain"
    assert (
        result["client_process"]["forced"]
        and result["client_process"]["job"]["active_processes"] == 0
    )


@pytest.mark.parametrize("change", ["scope", "unrecorded_challenge", "expired"])
def test_bad_readiness_never_dispatches_client(pair, monkeypatch, change):
    runner, plan, _, _ = pair
    original = module.private_read

    def read(path, limit):
        raw = original(path, limit)
        if Path(path).name == "participant-ready.json":
            value = json.loads(raw)
            if change == "scope":
                value["participant_id"] = "foreign"
            elif change == "unrecorded_challenge":
                value["challenge"] = "b" * 64
            else:
                value["expires_unix_ms"] = 1
            raw = canonical(value)
        return raw

    monkeypatch.setattr(module, "private_read", read)
    result = runner.run(plan)
    assert result["status"] == "uncertain" and "client_process" not in result
    assert not (Path(plan["evidence_directory"]) / "client-intent.json").exists()


def test_completed_but_invalid_driver_report_cannot_pass_outer_reconciliation(pair):
    runner, plan, launch_plan, setup = pair
    mode(plan, "list")
    result = runner.run(plan)
    assert result["status"] == "uncertain" and result["client_result"]["missing_or_invalid"]
    assert result["client_result"]["failure"]["code"] == "REFERENCE_PAIR_REPORT_INVALID"
    assert result["server_result"]["value"]["status"] == "stopped_reference"
    spool = next(Path(launch_plan["evidence_directory"]).glob("telemetry/*.authenticated.jsonl"))
    with pytest.raises(Fault, match="CRAFT_PAIR_UNQUALIFIED"):
        runner.store.inspect(setup["instance_id"], spool)


@pytest.mark.parametrize("abrupt", [False, True])
def test_actual_module_cli_and_abrupt_coordinator_keep_one_use_state(pair, tmp_path, abrupt):
    runner, plan, launch_plan, setup = pair
    path = tmp_path / "pair-plan.json"
    path.write_bytes(canonical(plan))
    args = [
        sys.executable,
        "-m",
        "strata_evaluator.reference_pair",
        "--database",
        str(runner.database.path),
        "--plan",
        str(path),
    ]
    if abrupt:
        wrapper = tmp_path / "crash-pair.py"
        wrapper.write_text(
            """
import os
from strata_evaluator import reference_pair as module
original = module.OwnedCli.observe
def crash(self):
    if self.role == 'client':
        os._exit(127)
    return original(self)
module.OwnedCli.observe = crash
module.main()
""",
            encoding="utf-8",
        )
        args = [sys.executable, str(wrapper), *args[3:]]
    root = Path(__file__).resolve().parents[1]
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ}
    env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root / "evaluator/src")])
    run = subprocess.run(
        args, env=env, capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
    )
    assert run.returncode == (127 if abrupt else 0), (run.stdout, run.stderr)
    row = runner.database.connection.execute("SELECT state,body FROM reference_pairs").fetchone()
    if abrupt:
        assert row["state"] == "CLIENT_DISPATCHING"
        assert not (Path(plan["evidence_directory"]) / "result.json").exists()
        with pytest.raises(Fault, match="CRAFT_PAIR_UNQUALIFIED"):
            runner.store.inspect(setup["instance_id"], tmp_path / "missing-spool.jsonl")
    else:
        assert row["state"] == "STOPPED" and json.loads(run.stdout)["status"] == "stopped_pair"
    assert (
        runner.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 1
    )
    before = tuple(row)
    with pytest.raises(Fault):
        runner.run(plan)
    assert (
        tuple(
            runner.database.connection.execute("SELECT state,body FROM reference_pairs").fetchone()
        )
        == before
    )


@pytest.mark.parametrize(
    "change,code",
    [
        ("pin", "CRAFT_FILE_CHANGED"),
        ("source", "REFERENCE_PAIR_SOURCE_UNPINNED"),
        ("exposure", "REFERENCE_PAIR_EXPOSURE"),
        ("path", "REFERENCE_PAIR_PATH"),
    ],
)
def test_pair_rejects_unsafe_inputs_before_durable_dispatch(pair, change, code):
    runner, plan, launch_plan, _ = pair
    if change == "pin":
        plan["client_driver"]["sha256"] = "a" * 64
    elif change == "source":
        plan["inputs"].pop(0)
    elif change == "exposure":
        plan["client_window_ms"] = 5000
    else:
        plan["evidence_directory"] = str(Path(launch_plan["evidence_directory"]) / "nested")
        Path(launch_plan["evidence_directory"]).mkdir()
    with pytest.raises(Fault, match=code):
        runner.run(plan)
    assert (
        runner.database.connection.execute("SELECT COUNT(*) FROM reference_pairs").fetchone()[0]
        == 0
    )
    assert (
        runner.database.connection.execute(
            "SELECT COUNT(*) FROM craft_reference_launches"
        ).fetchone()[0]
        == 0
    )
