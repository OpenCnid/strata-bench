"""Protected launch binding/admission controls, separate from native evidence."""

import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, canonical, digest
from strata_evaluator.protected_reference import ProtectedReferencePlan
from strata_evaluator.reference_launch import ReferenceLauncher
from strata_evaluator.writer_preparation import CODEX_SHA256
from test_craft_reference import reference, seal  # noqa: F401


@pytest.fixture
def plan(reference, tmp_path):  # noqa: F811
    _, setup, _, _, _ = reference
    setup = copy.deepcopy(setup)
    workspace, evidence = tmp_path / "workspace", tmp_path / "protected"
    game = workspace / "guarded"
    setup.update(game_directory=str(game), fixture_directory=str(game / "world"))
    def pin(path, sha="a" * 64):
        return {"path": str(path), "sha256": sha, "bytes": 1}
    java, module = pin(tmp_path / "java.exe"), pin(game / "module.jar")
    preparation = {"schema": "strata/PrivateWriterPreparationPlan/1", "id": "prep",
        "evidence_kind": "synthetic", "codex": pin(tmp_path / "codex.exe", CODEX_SHA256),
        "java": java, "helper_class": pin(tmp_path / "StrataWriterPreparation.class"),
        "sandbox_home": str(tmp_path / "home"), "writer_sid": "S-1-5-21-1-2-3-1003",
        "source_root": str(tmp_path / "sources"), "sources": {"world/level.dat": pin(tmp_path / "sources/level.dat")},
        "workspace_directory": str(workspace), "evidence_directory": str(evidence / "preparation"), "max_wall_s": 60}
    launch = {"schema": "strata/PrivateReferenceLaunch/4", "instance_id": setup["instance_id"],
        "setup_digest": digest(setup), "mode": "synthetic-fixture", "executable": java, "module_file": module,
        "immutable_files": [java, module], "immutable_trees": [], "fixture_arguments": [],
        "evidence_directory": str(evidence / "launch"), "server_port": 25569, "max_wall_s": 12,
        "graceful_stop_s": 2, "participant": {"participant_id": "p", "window_s": 2,
            "report_path": str(tmp_path / "participant.json")}, "outer_challenge": "a" * 64,
        "abort_cleanup_ms": 500, "custody_id": "prep", "gate_helper": pin(tmp_path / "StrataWriterLaunch.class")}
    return {"schema": "strata/ProtectedReferencePlan/1", "preparation": preparation, "setup": setup,
            "launch": launch, "evidence_directory": str(evidence)}


@pytest.mark.parametrize("change", ["world", "preparation_output", "launch_output", "custody_id",
                                   "setup_digest", "java", "authentic"])
def test_mixed_lifetimes_or_profiles_reject_before_preparation(plan, change):
    assert ProtectedReferencePlan.model_validate(plan).launch.custody_id == "prep"
    if change == "world":
        plan["setup"]["game_directory"] += "-foreign"
    elif change == "preparation_output":
        plan["preparation"]["evidence_directory"] += "-foreign"
    elif change == "launch_output":
        plan["launch"]["evidence_directory"] += "-foreign"
    elif change == "custody_id":
        plan["launch"]["custody_id"] = "other"
    elif change == "setup_digest":
        plan["launch"]["setup_digest"] = "b" * 64
    elif change == "java":
        plan["launch"]["executable"]["path"] = str(Path(plan["launch"]["executable"]["path"]).with_name("other.exe"))
    else:
        plan["launch"]["mode"] = "e9e-serverstarter"
    with pytest.raises((Fault, ValueError)):
        ProtectedReferencePlan.model_validate(plan)


def test_protected_launch_cannot_deserialize_live_custody(plan):
    launcher = object.__new__(ReferenceLauncher)
    with pytest.raises(Fault, match="REFERENCE_CUSTODY_REQUIRED"):
        launcher.run(plan["launch"])
    legacy = dict(plan["launch"], schema="strata/PrivateReferenceLaunch/3")
    del legacy["custody_id"], legacy["gate_helper"]
    with pytest.raises(Fault, match="REFERENCE_CUSTODY_REQUIRED"):
        launcher.run(legacy, custody=SimpleNamespace())


def test_protected_abort_binds_the_full_new_launch_identity(plan, tmp_path):
    from strata_evaluator.reference_abort import AbortSignal, request_abort
    evidence = tmp_path / "abort"
    evidence.mkdir()
    protected = plan["launch"]
    signal = AbortSignal(protected, evidence)
    legacy = dict(protected, schema="strata/PrivateReferenceLaunch/3")
    del legacy["custody_id"], legacy["gate_helper"]
    request_abort(evidence, legacy, "server_monitor", Fault("INJECTED_ABORT"))
    assert signal.poll() and signal.result["status"] == "invalid"
    assert signal.result["failure"]["code"] == "REFERENCE_ABORT_SCOPE"


@pytest.mark.parametrize("state", ["INTENT", "DISPATCH_RETURNED", "UNCERTAIN"])
def test_candidate_import_waits_for_complete_protected_lifetime(reference, state):  # noqa: F811
    store, setup, _, _, spool = reference
    seal(reference)
    with store.database.transaction() as db:
        db.execute("CREATE TABLE protected_references (instance TEXT PRIMARY KEY, state TEXT)")
        db.execute("INSERT INTO protected_references VALUES(?,?)", (setup["instance_id"], state))
    with pytest.raises(Fault, match="CRAFT_PROTECTED_REFERENCE_UNQUALIFIED"):
        store.inspect(setup["instance_id"], spool)


@pytest.mark.parametrize("change", ["plan_digest", "setup", "open_custody", "uncertain_custody", "spool"])
def test_stopped_row_alone_cannot_replace_protected_evidence_binding(reference, change):  # noqa: F811
    store, setup, _, _, spool = reference
    seal(reference)
    # Synthetic database corruption control, not native qualification.
    plan = {"setup": copy.deepcopy(setup)}
    body = {"plan_digest": digest(plan), "preparation": {"status": "stopped_reference",
            "custody": {"status": "stopped", "live": False}},
            "launch": {"status": "stopped_reference", "spool_sha256": hashlib.sha256(spool.read_bytes()).hexdigest()}}
    if change == "plan_digest":
        body["plan_digest"] = "a" * 64
    elif change == "setup":
        plan["setup"]["epoch"] += 1
        body["plan_digest"] = digest(plan)
    elif change == "open_custody":
        body["preparation"]["custody"]["live"] = True
    elif change == "uncertain_custody":
        body["preparation"]["custody"]["status"] = "uncertain"
    else:
        body["launch"]["spool_sha256"] = "a" * 64
    with store.database.transaction() as db:
        db.execute("CREATE TABLE protected_references (instance TEXT PRIMARY KEY, state TEXT, plan TEXT, body TEXT)")
        db.execute("INSERT INTO protected_references VALUES(?,?,?,?)",
            (setup["instance_id"], "STOPPED", canonical(plan).decode(), canonical(body).decode()))
    with pytest.raises(Fault, match="CRAFT_PROTECTED_REFERENCE_UNQUALIFIED"):
        store.inspect(setup["instance_id"], spool)
