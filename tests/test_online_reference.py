"""Versioned private-server admission controls; fixtures do not certify isolation."""

import copy
from pathlib import Path
import sys

import pytest

from mcbench.storage import Fault, canonical, digest
from strata_evaluator.protected_reference import parse_protected_plan
from strata_evaluator.reference_client import validate_client_binding, validate_client_scope
from strata_evaluator.reference_pair import ReferencePair, protected_result_matches
from strata_evaluator.writer_preparation import native_argv, parse_preparation_plan
from test_craft_reference import pin, reference  # noqa: F401
from test_protected_reference import plan as base_plan  # noqa: F401
from test_reference_client import registration  # noqa: F401
from test_writer_custody import held  # noqa: F401


@pytest.fixture
def online(base_plan):  # noqa: F811
    value = copy.deepcopy(base_plan)
    value["schema"] = "strata/ProtectedReferencePlan/2"
    value["preparation"].update(schema="strata/PrivateWriterPreparationPlan/2", max_wall_s=100,
        network_policy="native-online-private-server/1")
    value["launch"].update(schema="strata/PrivateReferenceLaunch/5",
        network_policy="native-online-private-server/1")
    return value


@pytest.mark.parametrize("change", ["prep_schema", "launch_schema", "prep_network", "launch_network",
    "lifetime", "profile", "declared_kind"])
def test_online_scope_rejects_mixed_identity_and_insufficient_exposure(online, change):
    assert parse_protected_plan(online).schema_ == "strata/ProtectedReferencePlan/2"
    if change == "prep_schema":
        online["preparation"]["schema"] = "strata/PrivateWriterPreparationPlan/1"
    elif change == "launch_schema":
        online["launch"]["schema"] = "strata/PrivateReferenceLaunch/4"
    elif change == "prep_network":
        online["preparation"]["network_policy"] = "filtered"
    elif change == "launch_network":
        online["launch"]["network_policy"] = "filtered"
    elif change == "lifetime":
        online["preparation"]["max_wall_s"] = 60
    elif change == "profile":
        online["launch"]["mode"] = "e9e-serverstarter"
    else:
        online["preparation"]["evidence_kind"] = "authentic_operator_reference"
    with pytest.raises((Fault, ValueError)):
        parse_protected_plan(online)


def test_network_capability_and_legacy_limits_are_explicit(online, base_plan):  # noqa: F811
    for value, enabled, profile in [(online, True, "strata-private-server"),
            (base_plan, False, "strata-writer-preparation")]:
        plan = parse_preparation_plan(value["preparation"])
        argv = native_argv(plan, Path(plan.workspace_directory), ["fixed-helper"])
        assert f"permissions.{profile}.network.enabled={str(enabled).lower()}" in argv
        assert "features.network_proxy=false" in argv if enabled else "features.network_proxy=false" not in argv
        assert argv[-2:] == ["--", "fixed-helper"]
    base_plan["preparation"]["max_wall_s"] = 900
    with pytest.raises(ValueError):
        parse_preparation_plan(base_plan["preparation"])
    online["preparation"]["max_wall_s"] = 901
    with pytest.raises(ValueError):
        parse_preparation_plan(online["preparation"])


def test_preparation_scope_is_not_a_file_check_or_permission_to_dispatch(registration):  # noqa: F811
    _, binding, setup, launch = registration
    Path(binding["server_module"]["path"]).unlink()
    parsed, _, _ = validate_client_scope(binding, setup, launch)
    assert parsed.instance_id == binding["instance_id"]
    with pytest.raises((Fault, OSError)):
        validate_client_binding(binding, setup, launch)
    binding["epoch"] += 1
    with pytest.raises(Fault, match="REFERENCE_CLIENT_SCOPE"):
        validate_client_scope(binding, setup, launch)


@pytest.mark.parametrize("change", [None, "state", "plan", "plan_digest", "report", "launch",
    "preparation", "live", "custody"])
def test_outer_pair_requires_the_exact_durable_closed_protected_lifetime(reference, online, change):  # noqa: F811
    store, _, _, _, _ = reference
    protected = parse_protected_plan(online)
    server = {"status": "stopped_reference", "spool_sha256": "a" * 64}
    result = {"status": "stopped", "plan_digest": digest(online), "launch": server,
        "preparation": {"status": "stopped_reference", "custody": {"live": False, "status": "stopped"}}}
    row_plan, row_body, state = copy.deepcopy(online), copy.deepcopy(result), "STOPPED"
    if change == "state":
        state = "DISPATCH_RETURNED"
    elif change == "plan":
        row_plan["evidence_directory"] += "-other"
    elif change == "plan_digest":
        row_body["plan_digest"] = result["plan_digest"] = "b" * 64
    elif change == "report":
        row_body["different"] = True
    elif change == "launch":
        server = {**server, "spool_sha256": "b" * 64}
    elif change == "preparation":
        result["preparation"]["status"] = row_body["preparation"]["status"] = "uncertain"
    elif change == "live":
        result["preparation"]["custody"]["live"] = row_body["preparation"]["custody"]["live"] = True
    elif change == "custody":
        result["preparation"]["custody"]["status"] = row_body["preparation"]["custody"]["status"] = "uncertain"
    with store.database.transaction() as db:
        db.execute("CREATE TABLE protected_references (instance TEXT, state TEXT, plan TEXT, body TEXT)")
        db.execute("INSERT INTO protected_references VALUES (?,?,?,?)", (protected.setup.instance_id,
            state, canonical(row_plan).decode(), canonical(row_body).decode()))
    assert protected_result_matches(store.database, protected.setup.instance_id, protected,
                                    result, server) is (change is None)


@pytest.mark.parametrize("change", ["launch", "legacy"])
def test_mixed_outer_pair_cannot_reserve_or_dispatch(reference, online, tmp_path, change):  # noqa: F811
    store, _, _, _, _ = reference
    protected_file, launch_file = tmp_path / "protected.json", tmp_path / "launch.json"
    protected_file.write_bytes(canonical(online))
    launch = copy.deepcopy(online["launch"])
    if change == "launch":
        launch["outer_challenge"] = "b" * 64
    launch_file.write_bytes(canonical(launch))
    def pinned(path):
        return {"path": str(path), **pin(path)}
    root = Path(__file__).resolve().parents[1]
    plan = {"schema": "strata/PrivateReferencePair/2", "protected_file": pinned(protected_file),
        "launch_file": pinned(launch_file), "client_driver": pinned(launch_file),
        "python": pinned(Path(sys.executable)), "bootstrap": pinned(root / "src/mcbench/process_bootstrap.py"),
        "source_root": str(root), "inputs": [pinned(launch_file)],
        "evidence_directory": str(tmp_path / "pair"), "client_window_ms": 1000, "finalize_ms": 1000}
    if change == "legacy":
        plan["schema"] = "strata/PrivateReferencePair/1"
        del plan["protected_file"]
    runner = ReferencePair(store.database)
    with pytest.raises(Fault, match="REFERENCE_PAIR_PROTECTED_BINDING" if change == "launch" else "REFERENCE_PAIR_PROFILE"):
        runner.run(plan)
    assert store.database.connection.execute("SELECT COUNT(*) FROM reference_pairs").fetchone()[0] == 0
    assert not Path(plan["evidence_directory"]).exists()


def test_direct_authentic_entrypoint_rejects_bad_registration_before_preparation(reference, online):  # noqa: F811
    from strata_evaluator.protected_reference import ProtectedReferences
    store, _, _, _, _ = reference
    online["preparation"]["evidence_kind"] = online["setup"]["evidence_kind"] = "authentic_operator_reference"
    online["launch"].update(mode="e9e-serverstarter", setup_digest=digest(online["setup"]))
    runner = ProtectedReferences(store.database)
    for binding in (None, {"schema": "invalid"}):
        with pytest.raises((Fault, ValueError)):
            runner.run(online, client_binding=binding)
    assert store.database.connection.execute("SELECT COUNT(*) FROM protected_references").fetchone()[0] == 0
    assert not Path(online["evidence_directory"]).exists()


@pytest.mark.parametrize("change,code", [("legacy", "WRITER_LAUNCH_PROFILE"),
    ("evidence", "WRITER_LAUNCH_PROFILE"), ("arguments", "WRITER_LAUNCH_PROFILE"),
    ("bootstrap", "WRITER_LAUNCH_BOOTSTRAP_UNREVIEWED"), ("descriptor", "WRITER_LAUNCH_UNPINNED"),
    ("installed_state", "WRITER_LAUNCH_INSTALLED_STATE_UNREVIEWED"),
    ("missing_installed_state", "WRITER_LAUNCH_INSTALLED_STATE_UNREVIEWED"),
    ("exposure", "WRITER_EXPOSURE_INSUFFICIENT")])
def test_authentic_gate_rejects_unreviewed_or_unbounded_launches_before_dispatch(
        held, tmp_path, monkeypatch, change, code):  # noqa: F811
    from types import SimpleNamespace
    from strata_evaluator import writer_custody
    from strata_evaluator.reference_launch import E9E_BOOTSTRAP_PINS, E9E_INSTALLED_STATE_PINS
    custody, _, _ = held
    workspace, game = tmp_path / "workspace", tmp_path / "workspace/guarded"
    java, module = tmp_path / "java.exe", game / "module.jar"
    custody.workspace.path, custody.tree.path = workspace, game
    custody.plan.schema_ = "strata/PrivateWriterPreparationPlan/2"
    custody.plan.evidence_kind, custody.plan.writer_sid = "authentic_operator_reference", "writer"
    custody.plan.java = SimpleNamespace(path=str(java))
    broker = SimpleNamespace(setup=SimpleNamespace(game_directory=str(game)),
        plan=SimpleNamespace(executable=SimpleNamespace(path=str(java)), module_file=SimpleNamespace(path=str(module))),
        writer_sid="writer", group_sid="group", scope_sid="scope", deadline=custody.deadline)
    def pin_value(path, sha="a" * 64):
        return {"path": str(path), "bytes": 1, "sha256": sha}
    files = [pin_value(game / name, sha) for name, sha in E9E_BOOTSTRAP_PINS.items()]
    files += [pin_value(game / name, sha) for name, sha in E9E_INSTALLED_STATE_PINS.items()]
    files += [pin_value(module), pin_value(workspace / "control/reference-telemetry.json")]
    plan = {"schema": "strata/PrivateWriterLaunch/2", "mode": "e9e-serverstarter",
        "network_policy": "native-online-private-server/1", "helper_class": pin_value(tmp_path / "StrataWriterLaunch.class"),
        "immutable_files": files, "immutable_trees": [], "arguments": ["-jar", "serverstarter-2.4.0.jar"],
        "max_wall_s": 720}
    if change == "legacy":
        custody.plan.schema_ = "strata/PrivateWriterPreparationPlan/1"
    elif change == "evidence":
        custody.plan.evidence_kind = "synthetic"
    elif change == "arguments":
        plan["arguments"] += ["unreviewed"]
    elif change == "bootstrap":
        files[0]["sha256"] = "b" * 64
    elif change == "descriptor":
        files.pop()
    elif change == "installed_state":
        files[2]["sha256"] = "b" * 64
    elif change == "missing_installed_state":
        files.pop(2)
    def forbidden(*_):
        raise AssertionError("Must reject before reading files or dispatching")
    monkeypatch.setattr(writer_custody, "check_file", forbidden)
    monkeypatch.setattr(writer_custody, "ManagedProcess", forbidden)
    with pytest.raises(Fault, match=code):
        custody.launch(plan, broker)
