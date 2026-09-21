"""Synthetic checkpoint activation; actual CLI loading needs separate evidence."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.checkpoints import Checkpoints
from mcbench.native import NativeExec, NativeLaunch
from mcbench.native_skill_activation import NativeSkillSets, active_files, require_catalog, skill_metadata
from mcbench.storage import CAS, Database, Fault, canonical
from test_native_checkpoint import stage
from test_native_export import OPERATOR, stopped as _stopped
from test_native_revisions import admitted as _admitted, publication

admitted = _admitted
stopped = _stopped


def activate(stopped, *, commit=True):
    runtime, _, _ = stopped
    publication(stopped)
    _, _, ref, manifest = stage(stopped)
    if commit:
        Checkpoints(runtime.db, runtime.cas).commit(runtime.db.checkpoint_fixture["config"], manifest, "operator")
    return NativeSkillSets(runtime), ref


def test_complete_checkpoint_atomic_activation_and_restart(stopped, tmp_path):
    runtime, _, _ = stopped
    before = runtime.budgets.status("a1")
    service, checkpoint = activate(stopped)
    ref = service.create(checkpoint)
    body = service.load(ref)
    assert len(body["skills"]) == 2
    assert all(s["revision"]["status"] == "active" and s["revision"]["activated_at"] == body["activated_at"]
               for s in body["skills"].values())
    assert not body["native_loader_qualified"] and not body["dispatch_authorized"] and not body["executes_scripts"]
    assert service.create(checkpoint) == ref
    assert runtime.db.connection.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0] == 1
    view = service.materialize(ref, tmp_path / "active-workspace")
    root = Path(view["path"])
    assert (root / "initial/SKILL.md").read_text() == "Immutable initial body."
    assert (root / ".agents/skills/learned-crafting/SKILL.md").read_bytes() == (
        root / "active/learned-crafting/SKILL.md").read_bytes()
    assert json.loads((root / "active/revisions.json").read_bytes()) == {
        "schema": "strata/ActiveSkillIndex/1", "skills": {"learned-crafting": "learned-crafting:1",
                                                        "learned-movement": "learned-movement:1"}}
    assert "publication_ref" not in "\n".join(p.read_text() for p in root.rglob("*") if p.is_file())
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        service.materialize(ref, root)
    database = Database(runtime.db.path)
    try:
        reopened = NativeSkillSets(NativeExec(database, CAS(database, runtime.cas.root), simulation=True))
        assert reopened.load(ref) == body
        assert reopened.create(checkpoint) == ref
    finally:
        database.close()
    assert runtime.budgets.status("a1") == before


def test_uncommitted_component_is_not_activation_authority(stopped):
    service, checkpoint = activate(stopped, commit=False)
    with pytest.raises(Fault, match="CHECKPOINT"):
        service.create(checkpoint)
    assert service.db.connection.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0] == 0


def test_activation_crash_before_commit_and_view_crash_after_rename(stopped, tmp_path, monkeypatch):
    service, checkpoint = activate(stopped)
    original = service.db.event
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic activation crash")
    monkeypatch.setattr(service.db, "event", fail)
    with pytest.raises(RuntimeError, match="synthetic activation crash"):
        service.create(checkpoint)
    assert service.db.connection.execute("SELECT count(*) FROM native_skill_sets").fetchone()[0] == 0
    monkeypatch.setattr(service.db, "event", original)
    ref = service.create(checkpoint)
    service.db.connection.execute("CREATE TRIGGER fail_view BEFORE INSERT ON native_skill_views "
                                  "BEGIN SELECT RAISE(ABORT,'synthetic view crash'); END")
    target = tmp_path / "view"
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError, match="synthetic view crash"):
        service.materialize(ref, target)
    assert target.exists() and not service.db.connection.execute("SELECT 1 FROM native_skill_views").fetchone()
    service.db.connection.execute("DROP TRIGGER fail_view")
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        service.materialize(ref, target)


@pytest.mark.parametrize("bad", ["missing", "alias", "foreign-name", "nested", "dependency", "malformed"])
def test_metadata_cannot_add_nested_skills_or_dependency_configuration(stopped, bad):
    service, checkpoint = activate(stopped)
    body = service.load(service.create(checkpoint))
    files = dict(body["skills"]["learned-crafting"]["files"])
    def put(text):
        return service.cas.put(OPERATOR, "operator", "operator", text.encode())
    if bad == "missing":
        files.pop("SKILL.md")
    elif bad == "nested":
        files["references/nested/SKILL.md"] = files["SKILL.md"]
    elif bad == "dependency":
        files["agents/openai.yaml"] = put("dependencies: unapproved")
    else:
        files["SKILL.md"] = put({"alias": "---\nname: learned-crafting\ndescription: *unapproved\n---\n",
            "foreign-name": "---\nname: foreign\ndescription: Synthetic procedure\n---\n",
            "malformed": "name: learned-crafting"}[bad])
    with pytest.raises(Fault, match="NATIVE_SKILL_METADATA"):
        skill_metadata("learned-crafting", files, service.cas)


def catalog(body, workspace):
    entries = [f'- {name}: {s["metadata"]["description"]} (file: r0/{name}/SKILL.md)'
               for name, s in body["skills"].items()]
    return {"input": [{"type": "message", "role": "developer", "content": [{"type": "input_text",
        "text": '<skills_instructions>\n- `r0` = `' + Path(workspace).as_posix() + '/.agents/skills`\n' +
        '\n'.join(entries) + '\n</skills_instructions>'}]}]}


@pytest.mark.parametrize("case", ["valid-root", "valid-helper", "helper-not-supplied", "omitted", "foreign",
                                 "duplicate", "forged-user", "wrong-agent", "stale-epoch"])
def test_native_catalog_and_explicit_helper_scope(stopped, tmp_path, case):
    runtime, _, _ = stopped
    service, checkpoint = activate(stopped)
    ref = service.create(checkpoint)
    body = service.load(ref)
    plan = NativeLaunch.model_validate_json(runtime.db.connection.execute("SELECT plan FROM native_jobs").fetchone()[0])
    old = json.loads(plan.model_dump_json())
    assert "skill_activation_ref" not in old and "helper_skill_activation_ref" not in old
    plan = plan.model_copy(update={"workspace": str(tmp_path / "view"), "epoch": 2, "skill_activation_ref": ref,
                                   "helper_skill_activation_ref": ref if case == "valid-helper" else None})
    assert plan.profile_digest() != NativeLaunch.model_validate(old).profile_digest()
    request = catalog(body, plan.workspace)
    role = "helper" if "helper" in case else "executor"
    code = "NATIVE_SKILL_CATALOG"
    if case == "omitted":
        request["input"][0]["content"][0]["text"] = "<skills_instructions></skills_instructions>"
    elif case == "foreign":
        request["input"][0]["content"][0]["text"] = request["input"][0]["content"][0]["text"].replace("r0/learned-crafting", "r0/foreign")
    elif case == "duplicate":
        request["input"] *= 2
    elif case == "forged-user":
        request["input"][0]["role"] = "user"
    elif case == "wrong-agent":
        plan = plan.model_copy(update={"agent_id": "foreign"})
        code = "NATIVE_SKILL_SCOPE"
    elif case == "stale-epoch":
        plan = plan.model_copy(update={"epoch": 1})
        code = "NATIVE_SKILL_SCOPE"
    elif case == "helper-not-supplied":
        code = "NATIVE_HELPER_SKILLS_NOT_SUPPLIED"
    if case.startswith("valid"):
        require_catalog(runtime.db.connection, runtime.cas, plan, request, role)
    else:
        with pytest.raises(Fault, match=code):
            require_catalog(runtime.db.connection, runtime.cas, plan, request, role)


@pytest.mark.parametrize("mutation", ["extra", "changed", "missing"])
def test_materialized_view_requires_exact_names_and_bytes(stopped, tmp_path, mutation):
    service, checkpoint = activate(stopped)
    ref = service.create(checkpoint)
    body = service.load(ref)
    root = Path(service.materialize(ref, tmp_path / "view")["path"])
    target = root / ".agents/skills/learned-crafting/SKILL.md"
    if mutation == "extra":
        (root / ".agents/skills/partial.md").write_text("uncommitted skill")
    elif mutation == "changed":
        target.write_text("changed")
    else:
        target.unlink()
    with pytest.raises(Fault, match="NATIVE_SKILL_VIEW_CHANGED"):
        service._verify_files(root, service.view_files(body))


def launch_view(stopped, tmp_path):
    runtime, plan, _ = stopped
    service, checkpoint = activate(stopped)
    ref = service.create(checkpoint)
    body = service.load(ref)
    target = tmp_path / "native-view"
    service.materialize(ref, target)
    manifest = {"schema": "strata/NativeBootstrap/1", "inventory": {"trees": [{"path": str(target)}],
        "files": [{"path": str(target / p), "sha256": r[11:]} for p, r in service.view_files(body).items()]}}
    raw = canonical(manifest)
    path = tmp_path / "bootstrap.json"
    path.write_bytes(raw)
    plan = plan.model_copy(update={"job_id": "resumed", "epoch": 2, "workspace": str(target),
        "bootstrap_manifest": str(path), "bootstrap_digest": hashlib.sha256(raw).hexdigest(),
        "skill_activation_ref": ref, "helper_skill_activation_ref": ref})
    return service, body, plan


@pytest.mark.parametrize("case", ["valid", "uncommitted-view", "missing-hold", "foreign-model", "advanced-epoch"])
def test_launch_requires_committed_held_view_and_current_scope(stopped, tmp_path, case):
    service, body, plan = launch_view(stopped, tmp_path)
    code = "NATIVE_SKILL_SCOPE"
    if case == "uncommitted-view":
        service.db.connection.execute("DELETE FROM native_skill_views")
        code = "NATIVE_SKILL_VIEW_UNCOMMITTED"
    elif case == "missing-hold":
        plan = plan.model_copy(update={"bootstrap_manifest": None, "bootstrap_digest": None})
        code = "SKILL_BOOTSTRAP_REQUIRED"
    elif case == "foreign-model":
        plan = plan.model_copy(update={"model": "other"})
    elif case == "advanced-epoch":
        service.db.connection.execute("UPDATE campaigns SET epoch=3")
    if case == "valid":
        assert service.validate_launch(plan) == body
    else:
        with pytest.raises(Fault, match=code):
            service.validate_launch(plan)


@pytest.mark.parametrize("role", ["executor", "helper"])
def test_atomic_scoped_projection_preserves_later_mutable_writes(stopped, tmp_path, role):
    from mcbench.broker import NativeBroker
    service, body, plan = launch_view(stopped, tmp_path)
    # Isolate the projection transaction from separately tested grant admission.
    # No fake grant is installed or used as native integration evidence.
    grant = SimpleNamespace(runtime_id=plan.job_id, profile_digest=plan.profile_digest(),
        campaign_id=plan.campaign_id, agent_id=plan.agent_id, epoch=plan.epoch,
        role=role, namespace="projection:" + role, thread_id="fresh-" + role)
    broker = SimpleNamespace(_path=NativeBroker._path, _grant=lambda db, thread: (grant, None))
    service.project(plan, grant, broker)
    def files():
        return {r["path"]: (r["ref"], r["immutable"]) for r in service.db.connection.execute(
            "SELECT * FROM broker_files WHERE namespace=?", (grant.namespace,))}
    actual = files()
    assert {p: r[0] for p, r in actual.items() if p.startswith("active/")} == active_files(body)
    assert all(r[1] for p, r in actual.items() if p.startswith(("active/", "initial/", "docs/")))
    if role == "helper":
        assert set(actual) == set(active_files(body))
    else:
        assert "notes/root.md" in actual and not actual["notes/root.md"][1]
        service.db.connection.execute("UPDATE broker_files SET ref=? WHERE namespace=? AND path='notes/root.md'",
                                      (actual["notes/development.md"][0], grant.namespace))
    before = files()
    service.project(plan, grant, broker)
    assert files() == before


def test_projection_failure_rolls_back_every_file(stopped, tmp_path):
    from mcbench.broker import NativeBroker
    service, _, plan = launch_view(stopped, tmp_path)
    grant = SimpleNamespace(runtime_id=plan.job_id, profile_digest=plan.profile_digest(),
        campaign_id=plan.campaign_id, agent_id=plan.agent_id, epoch=plan.epoch,
        role="executor", namespace="crash-projection", thread_id="fresh-root")
    broker = SimpleNamespace(_path=NativeBroker._path, _grant=lambda db, thread: (grant, None))
    service.db.connection.execute("CREATE TRIGGER fail_projection BEFORE INSERT ON broker_files "
        "WHEN NEW.namespace='crash-projection' AND NEW.path='notes/root.md' "
        "BEGIN SELECT RAISE(ABORT,'synthetic projection crash'); END")
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError, match="synthetic projection crash"):
        service.project(plan, grant, broker)
    assert not service.db.connection.execute("SELECT 1 FROM broker_files WHERE namespace=?", (grant.namespace,)).fetchone()
    assert not service.db.connection.execute("SELECT 1 FROM native_skill_projections").fetchone()


@pytest.mark.parametrize("request_change", ["lineage"])
def test_version_two_source_publication_activates_without_rewriting_legacy(stopped, request_change):
    service, checkpoint = activate(stopped)
    body = service.load(service.create(checkpoint))
    for skill in body["skills"].values():
        bundle = service.cas.json(OPERATOR, "operator", skill["revision"]["content"])
        assert bundle["schema"] == "strata/NativeSkillBundle/2"
        assert bundle["policy"] == "native-root-written-skill-bundles/2"


@pytest.mark.parametrize("case", ["valid", "wrong-parent", "reused-id", "other-skill-id", "unbound-name"])
def test_lineage_requires_exact_predecessor_and_unused_revision(case):
    from mcbench.native_revisions import parent_for
    previous = {"learned-route": {"revision": {"revision_id": "route:1"}},
                "learned-craft": {"revision": {"revision_id": "craft:1"}}}
    candidate = SimpleNamespace(name="learned-route", revision_id="route:2", parent_revision_id="route:1")
    if case == "wrong-parent":
        candidate.parent_revision_id = "foreign:1"
    elif case == "reused-id":
        candidate.revision_id = "route:1"
    elif case == "other-skill-id":
        candidate.revision_id = "craft:1"
    elif case == "unbound-name":
        candidate.name = "foreign"
    if case == "valid":
        assert parent_for(previous, candidate) is previous["learned-route"]
    else:
        with pytest.raises(Fault, match="REVISION_CONFLICT"):
            parent_for(previous, candidate)


def test_helper_catalog_denial_precedes_enrollment_and_reservation(admitted):
    admission, gate, _, plan, request, _, put = admitted
    # A committed-set lookup fixture isolates request admission from the
    # checkpoint producer, which is covered by the complete-set tests above.
    NativeSkillSets(NativeExec(admission.db, admission.cas, simulation=True))
    body = {"schema": "strata/NativeSkillSet/1", "policy": "native-checkpoint-learned-overlay/1",
        "checkpoint_ref": "cas:sha256:" + "a" * 64, "campaign_id": "c1", "agent_id": "a1",
        "model_identity": plan.model, "source_epoch": 1, "skills": {}}
    plan.epoch = 2
    plan.skill_activation_ref = put(body)
    admission.db.connection.execute("INSERT INTO native_skill_sets VALUES(?,?)", (body["checkpoint_ref"], plan.skill_activation_ref))
    admission.db.connection.execute("UPDATE native_jobs SET plan=?", (plan.model_dump_json(),))
    def with_catalog(value):
        value["input"][0] = catalog(body, plan.workspace)["input"][0]
    attempt, reserve, raw, child = request("root-new", mutate=with_catalog)
    reserve = reserve.model_copy(update={"epoch": 2})
    admission.prepare("a1", attempt, reserve, raw, child_envelope=child)
    before = gate.budgets.status("a1")
    attempt, reserve, raw, child = request("child-new", thread="child-new", name="/root/new",
                                         parent="root", mutate=with_catalog, child=True)
    reserve = reserve.model_copy(update={"epoch": 2})
    with pytest.raises(Fault, match="NATIVE_HELPER_SKILLS_NOT_SUPPLIED"):
        admission.prepare("a1", attempt, reserve, raw, child_envelope=child)
    assert gate.budgets.status("a1") == before
    assert admission.db.connection.execute("SELECT count(*) FROM native_participants").fetchone()[0] == 1
    assert not admission.db.connection.execute("SELECT 1 FROM operations WHERE id=?", (child.operation_id,)).fetchone()
