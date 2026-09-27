"""Native bootstrap file preparation with synthetic checkpoint/world sources."""

import json
import os
import sqlite3

import pytest

from mcbench.storage import Fault, Principal, digest
from strata_evaluator.native_probe_views import INSTRUCTIONS, ProbeNativeViews
from test_probe_pairs import EVALUATOR, pair_source as _pair_source

pair_source = _pair_source


@pytest.fixture
def views(pair_source, tmp_path):
    pairs, request, _, runtime = pair_source
    pairs.prepare(EVALUATOR, request(), tmp_path / "pair")
    return ProbeNativeViews(pairs), runtime


def state(service):
    return service.db.connection.execute("SELECT state FROM probe_native_views WHERE pair='p1'").fetchone()[0]


def test_both_native_catalogs_and_role_inventories_derive_only_approved_artifacts(views, tmp_path):
    service, runtime = views
    before = runtime.budgets.status("a1")
    target = tmp_path / "native"
    plan = service.prepare(EVALUATOR, "p1", target, max_bytes=1024*1024)
    assert service.verify(EVALUATOR, "p1") == plan
    assert state(service) == "PREPARED"
    assert plan["instructions"] == INSTRUCTIONS
    assert not any(plan[k] for k in ("dispatch_authorized", "campaign_feedback_allowed",
                                   "native_loader_verified", "broker_projection_verified"))
    for arm in ("initial", "experienced"):
        view = plan["views"][arm]["a1"]
        root = target / view["directory"]
        assert not list((root / "profile").iterdir())
        assert not (root / "workspace/views.json").exists()
        assert set(view["broker_files"]) == {"executor", "helper"}
        assert view["helper_set_requires_explicit_admission"]
        assert "notes/root.md" not in view["broker_files"]["helper"]
        assert not any(p.startswith(("notes/", "handoff/", "skills/", "results/"))
                       for p in view["broker_files"]["helper"])
        for name, value in view["catalog"].items():
            for path in value["files"]:
                assert (root / "workspace/.agents/skills" / name / path).read_bytes() == (
                    root / "workspace/active" / name / path).read_bytes()
                assert not os.path.samefile(root / "workspace/.agents/skills" / name / path,
                                           root / "workspace/active" / name / path)
                assert "active/" + name + "/" + path in view["broker_files"]["helper"]
        assert json.loads((root / "workspace/active/revisions.json").read_bytes()) == view["index"]
    assert not plan["views"]["initial"]["a1"]["catalog"]
    assert set(plan["views"]["experienced"]["a1"]["catalog"]) == {"learned-crafting"}
    assert "notes/root.md" in plan["views"]["experienced"]["a1"]["broker_files"]["executor"]
    assert runtime.budgets.status("a1") == before
    # Returned mutable Python dictionaries cannot replace the registered source.
    plan["instructions"] = "injected operator text"
    assert service.verify(EVALUATOR, "p1")["instructions"] == INSTRUCTIONS


@pytest.mark.parametrize("pair_source", [True], indirect=True)
def test_time_zero_native_views_are_identical_with_empty_profiles(views, tmp_path):
    service, _ = views
    target = tmp_path / "native"
    plan = service.prepare(EVALUATOR, "p1", target, max_bytes=1024*1024)
    def files(arm):
        root = target / plan["views"][arm]["a1"]["directory"]
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert files("initial") == files("experienced")
    assert service.verify(EVALUATOR, "p1") == plan


def test_all_broker_inputs_resolve_without_private_evaluator_manifests(views, tmp_path):
    service, _ = views
    plan = service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    operator = Principal("operator", "operator")
    for arm in plan["views"].values():
        for view in arm.values():
            for files in view["broker_files"].values():
                for ref in files.values():
                    service.cas.verify(operator, "operator", ref)
    assert service.db.connection.execute("SELECT 1 FROM objects WHERE namespace='operator' AND ref=?",
        ("cas:sha256:" + digest(plan),)).fetchone() is None
    assert service.verify(EVALUATOR, "p1") == plan


@pytest.mark.parametrize("change", ["missing", "visibility"])
def test_public_index_requires_its_own_committed_artifact_store_binding(views, tmp_path, change):
    service, _ = views
    plan = service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    ref = plan["views"]["experienced"]["a1"]["broker_files"]["executor"]["active/revisions.json"]
    if change == "missing":
        service.db.connection.execute("DELETE FROM objects WHERE namespace='operator' AND ref=?", (ref,))
    else:
        service.db.connection.execute("UPDATE objects SET visibility='agent' WHERE namespace='operator' AND ref=?", (ref,))
    with pytest.raises(Fault, match="PROBE_ARTIFACT_SOURCE"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "FAILED"


@pytest.mark.parametrize("pair_source", [{"arm": "no-self-play"}, {"arm": "frozen-skills"},
                                       {"arm": "frozen-persistence"}], indirect=True)
def test_registered_controls_define_catalog_and_helper_views(views, tmp_path):
    service, _ = views
    plan = service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    source, _ = service._source("p1")
    arm = source["projections"]["a1"]["arm"]
    for treatment in ("initial", "experienced"):
        view = plan["views"][treatment]["a1"]
        if arm == "no-self-play":
            assert set(view["broker_files"]) == {"executor"}
            assert not view["helper_set_requires_explicit_admission"]
        else:
            assert view["catalog"] == {}
            assert set(view["broker_files"]) == {"executor", "helper"}
    if arm == "frozen-persistence":
        assert plan["views"]["initial"]["a1"]["broker_files"] == plan["views"]["experienced"]["a1"]["broker_files"]
    assert service.verify(EVALUATOR, "p1") == plan


def test_interrupted_verification_commits_intent_and_never_rearms(views, tmp_path, monkeypatch):
    service, _ = views
    service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    def interrupted(*_):
        with sqlite3.connect(service.db.path.as_uri() + "?mode=ro", uri=True) as reader:
            assert reader.execute("SELECT state FROM probe_native_views").fetchone()[0] == "VERIFYING"
        raise KeyboardInterrupt("synthetic controller interruption")
    monkeypatch.setattr(service, "_derive", interrupted)
    with pytest.raises(KeyboardInterrupt, match="synthetic controller interruption"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "FAILED"
    with pytest.raises(Fault, match="PROBE_VIEWS_NOT_PREPARED"):
        service.verify(EVALUATOR, "p1")


@pytest.mark.parametrize("change", ["catalog", "hardlink", "session", "empty_directory", "private_manifest"])
def test_changed_views_fail_permanently_without_rearming(views, tmp_path, change):
    service, _ = views
    target = tmp_path / "native"
    plan = service.prepare(EVALUATOR, "p1", target, max_bytes=1024*1024)
    root = target / plan["views"]["experienced"]["a1"]["directory"]
    file = root / "workspace/.agents/skills/learned-crafting/SKILL.md"
    original = file.read_bytes()
    if change == "catalog":
        file.write_bytes(b"unapproved revision")
    elif change == "hardlink":
        file.unlink()
        os.link(root / "workspace/active/learned-crafting/SKILL.md", file)
    elif change == "session":
        (root / "profile/session.json").write_text("inherited context", encoding="utf-8")
    elif change == "empty_directory":
        (root / "profile/old-cache").mkdir()
    else:
        (target / "views.json").write_text("{}", encoding="utf-8")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE|MIXED_SNAPSHOT|UNSAFE_PATH"):
        service.verify(EVALUATOR, "p1")
    assert state(service) == "FAILED"
    if change == "catalog":
        file.write_bytes(original)
    with pytest.raises(Fault, match="PROBE_VIEWS_NOT_PREPARED"):
        service.verify(EVALUATOR, "p1")
    with pytest.raises(Fault, match="PROBE_VIEWS_CONSUMED"):
        service.prepare(EVALUATOR, "p1", tmp_path / "retry", max_bytes=1024*1024)


def test_pair_drift_during_copy_never_commits_native_views(views, tmp_path, monkeypatch):
    service, _ = views
    original = service.cas.copy_to
    touched = []
    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        if not touched:
            touched.append(True)
            (tmp_path / "pair/copy-0/server/world/level.dat").write_bytes(b"changed source fixture")
        return result
    monkeypatch.setattr(service.cas, "copy_to", change)
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE|MIXED_SNAPSHOT"):
        service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    assert state(service) == "FAILED"
    assert (tmp_path / "native/views.json").is_file()
    assert not service.db.connection.execute("SELECT 1 FROM outbox WHERE kind='probe.native_views_prepared'").fetchone()


def test_copy_failure_keeps_partial_files_and_one_use_intent(views, tmp_path, monkeypatch):
    service, _ = views
    original = service.cas.copy_to
    count = []
    def failed(*args, **kwargs):
        if count:
            raise OSError("synthetic partial copy")
        count.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(service.cas, "copy_to", failed)
    with pytest.raises(OSError, match="synthetic partial copy"):
        service.prepare(EVALUATOR, "p1", tmp_path / "native", max_bytes=1024*1024)
    assert state(service) == "FAILED"
    assert len([p for p in (tmp_path / "native").rglob("*") if p.is_file()]) == 1
    with pytest.raises(Fault, match="PROBE_VIEWS_CONSUMED"):
        service.prepare(EVALUATOR, "p1", tmp_path / "retry", max_bytes=1024*1024)


@pytest.mark.parametrize("caller", [Principal("evaluation:other", "evaluator"), Principal("a1", "executor"),
                                   Principal("helper:a1", "helper")])
def test_authorization_precedes_source_and_target_access(views, tmp_path, caller):
    service, _ = views
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.prepare(caller, "unknown", tmp_path / "native", max_bytes=1024*1024)
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.verify(caller, "unknown")
    assert not (tmp_path / "native").exists()
    assert service.db.connection.execute("SELECT count(*) FROM probe_native_views").fetchone()[0] == 0


@pytest.mark.parametrize("case", ["quota", "bool_quota", "source_subdirectory", "cas_subdirectory"])
def test_preflight_constraints_do_not_consume_a_pair(views, tmp_path, case):
    service, _ = views
    target = tmp_path / "native"
    if case == "source_subdirectory":
        target = tmp_path / "pair/nested"
    elif case == "cas_subdirectory":
        target = service.cas.root / "native"
    ceiling = True if case == "bool_quota" else 1 if case == "quota" else 1024*1024
    with pytest.raises(Fault, match="PROBE_STORAGE_LIMIT|TARGET_EXISTS"):
        service.prepare(EVALUATOR, "p1", target, max_bytes=ceiling)
    assert not target.exists()
    assert service.db.connection.execute("SELECT count(*) FROM probe_native_views").fetchone()[0] == 0
