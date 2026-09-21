"""Owned Windows/JVM fixtures; no Minecraft or inference, no scoring claim."""

import copy
import os
from pathlib import Path
import sys

import pytest

from mcbench.storage import Fault
from strata_evaluator.craft_reference import CraftReferencePlan
from strata_evaluator.reference_launch import ReferenceLaunchPlan, ReferenceLauncher, bind_identity
from strata_evaluator.telemetry import LaunchIdentity
from test_craft_reference import reference, pin  # noqa: F401


@pytest.fixture
def launch(reference, tmp_path):  # noqa: F811 - imported shared pytest fixture
    java, classpath = os.environ.get("STRATA_TELEMETRY_TEST_JAVA"), os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if os.name != "nt" or not java or not classpath:
        pytest.skip("Explicit pinned Windows/JVM profile required")
    store, setup, _, directory, _ = reference
    seal = store.seal(setup, directory)
    module = tmp_path / "synthetic-module.jar"
    module.write_bytes(b"synthetic artifact identity; not an installed game mod")
    bootstrap = Path(__file__).resolve().parents[1] / "src/mcbench/process_bootstrap.py"
    files = [Path(java), Path(sys.executable), bootstrap, module]
    value = {"schema": "strata/PrivateReferenceLaunch/1", "instance_id": "i",
        "setup_digest": seal["setup_digest"], "mode": "synthetic-fixture",
        "executable": {"path": java, **pin(Path(java))}, "module_file": {"path": str(module), **pin(module)},
        "immutable_files": [{"path": str(path), **pin(path)} for path in files], "immutable_trees": [],
        "fixture_arguments": ["-cp", Path(classpath).read_text(),
            "io.github.opencnid.strata.telemetry.OwnedLaunchFixture", "{config}", "{game}", "{module}", "25569", "normal"],
        "evidence_directory": str(tmp_path / "launch"), "server_port": 25569,
        "max_wall_s": 8, "ready_run_s": 1, "graceful_stop_s": 2}
    return ReferenceLauncher(store), value, setup


def test_actual_jvm_signed_identity_binds_to_retained_job_handle_and_private_world(launch):
    launcher, plan, setup = launch
    result = launcher.run(plan)
    assert result["status"] == "stopped_reference", result
    assert result["launch_binding_verified"] and result["exit_code"] == 0 and not result["forced_stop"]
    assert result["held_members"]["held_processes"] == result["job_accounting"]["total_processes"]
    assert result["held_members"]["signaled_processes"] == result["held_members"]["held_processes"]
    assert result["records"] == 3 and result["sampled_server_ticks"] == 20
    spool = next((Path(plan["evidence_directory"]) / "telemetry").glob("*.authenticated.jsonl"))
    report = launcher.store.inspect("i", spool)
    assert report["launch_binding_verified"] and not report["scoring_eligible"]
    assert not report["candidate_complete"]  # No craft was fabricated by the empty fixture.
    with pytest.raises(Fault):
        launcher.run(plan)
    with launcher.database.transaction() as db:
        db.execute("UPDATE reference_dispatches SET state='UNCERTAIN' WHERE instance='i'")
    with pytest.raises(Fault, match="CRAFT_LAUNCH_UNQUALIFIED"):
        launcher.store.inspect("i", spool)


@pytest.mark.parametrize("mode,error", [("wrong-world", "REFERENCE_WORLD_MISMATCH"),
    ("hang", "REFERENCE_LIFECYCLE_FAILED"), ("missing-stop", "TELEMETRY_CLEAN_STOP_MISSING"),
    ("early-exit", "REFERENCE_LIFECYCLE_FAILED|PROCESS_IDENTITY_UNAVAILABLE|PROCESS_MEMBER_INVENTORY_UNAVAILABLE")])
def test_real_jvm_faults_retain_uncertainty_and_never_replay(launch, mode, error):
    launcher, plan, _ = launch
    plan["fixture_arguments"][-1] = mode
    plan.update(max_wall_s=3, graceful_stop_s=1)
    result = launcher.run(plan)
    # An early exit can precede either handle observation or the lifecycle
    # check. All are missing required evidence, never a reason to relaunch.
    assert result["status"] == "uncertain" and result["error"] in error.split("|"), result
    row = launcher.database.connection.execute("SELECT state FROM reference_dispatches WHERE instance='i'").fetchone()
    assert row[0] == "UNCERTAIN"
    with pytest.raises(Fault):
        launcher.run(plan)
    with pytest.raises(Fault, match="CRAFT_GRANT_ALREADY_USED"):
        launcher.store.preflight("i")


@pytest.mark.parametrize("change,code", [("setup", "REFERENCE_SETUP_CHANGED"),
    ("executable", "CRAFT_FILE_CHANGED"), ("bootstrap", "REFERENCE_BOOTSTRAP_UNPINNED"),
    ("game_output", "REFERENCE_EVIDENCE_PATH")])
def test_substituted_launch_inputs_fail_before_reservation(launch, change, code):
    launcher, plan, setup = launch
    if change == "setup":
        plan["setup_digest"] = "a" * 64
    elif change == "executable":
        plan["immutable_files"][0]["sha256"] = "a" * 64
    elif change == "bootstrap":
        plan["immutable_files"].pop(2)
    else:
        plan["evidence_directory"] = str(Path(setup["game_directory"]) / "private-evidence")
    with pytest.raises(Fault, match=code):
        launcher.run(plan)
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM craft_reference_launches").fetchone()[0] == 0


@pytest.mark.parametrize("field", ["pid", "process_started_unix_ms", "executable", "world_directory",
    "game_directory", "module_file", "module_sha256", "online_mode", "server_port"])
def test_signed_but_wrong_process_world_or_configuration_is_not_bound(launch, field):
    _, plan, setup = launch
    observed = {"policy": "native-server-launch-observation/1", "pid": 123, "process_started_unix_ms": 1000,
        "executable": plan["executable"]["path"], "game_directory": setup["game_directory"],
        "world_directory": setup["fixture_directory"], "module_file": plan["module_file"]["path"],
        "module_sha256": plan["module_file"]["sha256"], "online_mode": True, "server_port": 25569}
    held = {key: observed[key] for key in ("pid", "process_started_unix_ms", "executable")}
    bad = copy.deepcopy(observed)
    bad[field] = (False if field == "online_mode" else "a" * 64 if field == "module_sha256"
                  else bad[field] + 1 if isinstance(bad[field], int) else str(Path(setup["game_directory"]) / "wrong"))
    with pytest.raises(Fault):
        bind_identity(ReferenceLaunchPlan.model_validate(plan), CraftReferencePlan.model_validate(setup),
                      LaunchIdentity.model_validate(bad), held)


@pytest.mark.parametrize("change,code", [("arguments", "REFERENCE_ARGUMENTS"),
    ("missing", "REFERENCE_BOOTSTRAP_UNPINNED"), ("unreviewed", "REFERENCE_BOOTSTRAP_UNREVIEWED")])
def test_real_pack_profile_cannot_admit_arbitrary_bootstrap_or_restart_configuration(launch, change, code):
    launcher, plan, setup = launch
    plan["mode"] = "e9e-serverstarter"
    if change != "arguments":
        plan["fixture_arguments"] = []
    if change == "unreviewed":
        for name in ("serverstarter-2.4.0.jar", "server-setup-config.yaml"):
            path = Path(setup["game_directory"]) / name
            path.write_bytes(b"unreviewed bootstrap or autoRestart: true")
            plan["immutable_files"].append({"path": str(path), **pin(path)})
    with pytest.raises(Fault, match=code):
        launcher.run(plan)
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM craft_reference_launches").fetchone()[0] == 0
    assert launcher.database.connection.execute("SELECT COUNT(*) FROM reference_dispatches").fetchone()[0] == 0
