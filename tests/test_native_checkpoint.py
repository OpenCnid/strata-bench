"""Synthetic complete-set/retention integration; no game or model qualification."""

import copy

import pytest

from mcbench.artifacts import Artifacts
from mcbench.checkpoints import Checkpoints
from mcbench.controller import Controller
from mcbench.native import NativeExec
from mcbench.native_checkpoint import POLICY, NativeCheckpointStates
from mcbench.records import AgentConfig, BudgetLedger, CheckpointManifest
from mcbench.storage import CAS, Database, Fault, Principal, canonical
from test_checkpoints_artifacts import checkpoint_fixture
from test_native_admission import admitted as _admitted
from test_native_export import stopped as _stopped

stopped = _stopped
OPERATOR = Principal("operator", "operator")


@pytest.fixture
def admitted(database, cas, tmp_path, example, configs, request):
    config, body, namespace, stop, _ = checkpoint_fixture(example, configs, cas, OPERATOR)
    for row in database.connection.execute("SELECT * FROM objects WHERE namespace=?", (namespace,)).fetchall():
        cas.put(OPERATOR, "operator", "operator", cas.read(OPERATOR, namespace, row["ref"]), media_type=row["media_type"])
    def put(value):
        return cas.put(OPERATOR, "operator", "operator", canonical(value))
    initial = {"initial/SKILL.md": "Immutable initial body.", "docs/allowed.md": "Admitted document.",
        "notes/seed.md": "Initial note.", "skills/seed.md": "Initial draft.", "handoff/seed.md": "Initial handoff."}
    initial_files = {k: cas.put(OPERATOR, "operator", "operator", v.encode()) for k, v in initial.items()}
    baseline = put({"schema": "strata/NativeInitialArtifacts/1", "files": initial_files})
    arm = getattr(request, "param", "full")
    policy = put({"schema": "strata/NativeRetentionPolicy/1", "policy": POLICY, "is_example": True,
        "campaign_id": "c1", "agent_id": "a1", "system_digest": config.system_digest, "arm": arm,
        "initial_artifacts": baseline, "resume_mode": "fresh_handoff"})
    config = type(config).model_validate(config.model_dump() | {"recovery_policy": "resume_development"})
    agent = AgentConfig.model_validate(configs()[1][0].model_dump() | {"memory_policy": policy,
        "initial_skills": baseline, "resume_mode": "fresh_handoff", "self_play": arm != "no-self-play",
        "requested_model": "gpt-5.6-luna"})
    Controller(database, simulation=True).create(config, [agent])
    native = NativeCheckpointStates(NativeExec(database, cas, simulation=True))
    native.register(config, agent)
    database.checkpoint_fixture = {"config": config, "agent": agent, "body": body, "stop": stop,
        "put": put, "arm": arm, "initial": initial_files}
    return _admitted.__wrapped__(database, cas, tmp_path, example)


def stage(stopped, *, boundary="episode"):
    runtime, _, _ = stopped
    service = NativeCheckpointStates(runtime)
    export = runtime.export_broker_state("job")
    state, ref = service.seal(export, "cp1", boundary=boundary)
    fixture = runtime.db.checkpoint_fixture
    body, stop = copy.deepcopy(fixture["body"]), copy.deepcopy(fixture["stop"])
    if boundary == "recovery":
        body["scheduled_active_s"] = None
    body["agents"][0] |= {"workspace": state.workspace, "skills": state.skills,
        "runtime_state": ref, "model_identity": state.model_identity}
    body["ledger_cursor"] = runtime.db.connection.execute("SELECT max(rowid) FROM ledger").fetchone()[0]
    body["event_cursor"] = runtime.db.connection.execute("SELECT max(cursor) FROM outbox").fetchone()[0]
    stop |= {"snapshot_refs": {"world_and_external_state": body["world_and_external_state"], "agents": body["agents"]},
        "ledger_cursor": body["ledger_cursor"], "event_cursor": body["event_cursor"]}
    body["clean_stop_report"] = fixture["put"](stop)
    return service, state, ref, CheckpointManifest.model_validate(body)


@pytest.mark.parametrize("admitted", ["full", "frozen-persistence", "frozen-skills", "no-self-play"], indirect=True)
def test_declared_retention_atomic_complete_set_and_restart(stopped, tmp_path):
    runtime, _, _ = stopped
    before = runtime.budgets.status("a1")
    service, state, ref, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    assert service.seal(state.source_export, "cp1", boundary="episode") == (state, ref)
    assert service.load(ref)[0] == state
    files = runtime.cas.json(OPERATOR, "operator", state.workspace)["files"] | runtime.cas.json(OPERATOR, "operator", state.skills)["files"]
    if fixture["arm"] == "frozen-persistence":
        assert files == fixture["initial"]
    elif fixture["arm"] == "frozen-skills":
        assert "skills/seed.md" in files and "skills/draft.md" not in files
        assert "notes/root.md" in files and "handoff/next.md" in files
    else:
        assert set(files) == {"initial/SKILL.md", "docs/allowed.md", "notes/root.md", "skills/draft.md", "handoff/next.md"}
    assert not any(x.startswith("results/") for x in files)
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    committed = checkpoints.commit(fixture["config"], manifest, "operator")
    target = tmp_path / "whole-set"
    restored = checkpoints.materialize_set("cp1", fixture["config"], 2, target)
    assert not restored["dispatch_authorized"] and not restored["cost_rollback"]
    assert (target / "server/world/level.dat").read_bytes() == (target / "server/external/teams.dat").read_bytes()
    workspace = target / restored["members"]["a1"]["directory"] / "workspace"
    assert {x.relative_to(workspace).as_posix() for x in workspace.rglob("*") if x.is_file()} == set(files)
    for path, value in files.items():
        assert (workspace / path).read_bytes() == runtime.cas.read(OPERATOR, "operator", value)
    assert {x.name for x in (workspace.parent / "private").iterdir()} == {"backend_state.json", "runtime_state.json"}
    assert runtime.budgets.status("a1") == before
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        checkpoints.materialize_set("cp1", fixture["config"], 2, target)
    db = Database(runtime.db.path)
    try:
        fresh = NativeCheckpointStates(NativeExec(db, CAS(db, runtime.cas.root), simulation=True))
        assert fresh.load(ref)[0] == state
        assert Checkpoints(db, fresh.cas).load("cp1")[0] == committed
    finally:
        db.close()


@pytest.mark.parametrize("admitted", ["frozen-persistence", "frozen-skills"], indirect=True)
def test_mid_episode_recovery_keeps_same_checkpoint_knowledge(stopped):
    runtime, _, _ = stopped
    _, state, _, _ = stage(stopped, boundary="recovery")
    assert "notes/root.md" in runtime.cas.json(OPERATOR, "operator", state.workspace)["files"]
    assert "skills/draft.md" in runtime.cas.json(OPERATOR, "operator", state.skills)["files"]
    assert state.session is None and state.runtime_cache is None


@pytest.mark.parametrize("change,code", [("runtime", "NATIVE_CHECKPOINT_REQUIRED"),
    ("workspace", "MIXED_SNAPSHOT"), ("model", "MIXED_SNAPSHOT"), ("epoch", "CLEAN_STOP_INCOMPLETE"),
    ("ledger", "MIXED_SNAPSHOT"), ("other-agent", "INCOMPLETE_CHECKPOINT")])
def test_mixed_components_cannot_commit_even_with_matching_stop_claim(stopped, change, code):
    runtime, _, _ = stopped
    _, state, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    body = manifest.model_dump()
    if change == "runtime":
        body["agents"][0]["runtime_state"] = state.source_export
    elif change == "workspace":
        body["agents"][0]["workspace"] = state.skills
    elif change == "model":
        body["agents"][0]["model_identity"] = "different-model"
    elif change == "epoch":
        body["source_epoch"] = 2
    elif change == "ledger":
        body["ledger_cursor"] = 0
    else:
        body["agents"][0]["agent_id"] = "other"
    stop = runtime.cas.json(OPERATOR, "operator", body["clean_stop_report"])
    stop["snapshot_refs"]["agents"] = body["agents"]
    stop["ledger_cursor"] = body["ledger_cursor"]
    body["clean_stop_report"] = fixture["put"](stop)
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    with pytest.raises(Fault, match=code):
        checkpoints.commit(fixture["config"], CheckpointManifest.model_validate(body), "operator")
    assert runtime.db.connection.execute("SELECT count(*) FROM checkpoints").fetchone()[0] == 0


def test_policy_cannot_be_registered_after_execution_or_replaced(stopped):
    runtime, _, _ = stopped
    fixture = runtime.db.checkpoint_fixture
    service = NativeCheckpointStates(runtime)
    changed = fixture["config"].model_copy(update={"episode_s": 90})
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        service.register(changed, fixture["agent"])
    runtime.db.connection.execute("DELETE FROM native_retention_policies")
    with pytest.raises(Fault, match="NATIVE_RETENTION_TOO_LATE"):
        service.register(fixture["config"], fixture["agent"])
    with pytest.raises(Fault, match="NATIVE_RETENTION_NOT_REGISTERED"):
        service.seal(runtime.export_broker_state("job"), "cp1", boundary="episode")


@pytest.mark.parametrize("case,code", [("initial", "NATIVE_INITIAL_CHANGED"), ("handoff", "ARTIFACT_QUOTA"),
                                      ("revision", "NATIVE_REVISION_EXPORT_REQUIRED")])
def test_incomplete_retention_never_silently_discards_or_activates_artifacts(stopped, case, code):
    runtime, _, _ = stopped
    db = runtime.db.connection
    if case == "initial":
        ref = db.execute("SELECT ref FROM broker_files WHERE path='notes/root.md'").fetchone()[0]
        db.execute("UPDATE broker_files SET ref=? WHERE path='initial/SKILL.md'", (ref,))
    elif case == "handoff":
        namespace = db.execute("SELECT namespace FROM broker_files WHERE path='notes/root.md'").fetchone()[0]
        ref = runtime.cas.put(OPERATOR, namespace, "agent", b"x" * 8000)
        db.execute("INSERT INTO broker_files VALUES(?,?,?,0)", (namespace, "handoff/too-much.md", ref))
    else:
        Artifacts(runtime.db, runtime.cas)
        db.execute("INSERT INTO revisions VALUES('active','campaign:c1:agent:a1','a1','procedure','{}','digest',1)")
    with pytest.raises(Fault, match=code):
        stage(stopped)


def test_corruption_during_copy_never_publishes_partial_set(stopped, tmp_path, monkeypatch):
    runtime, _, _ = stopped
    _, state, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(fixture["config"], manifest, "operator")
    original = runtime.cas.copy_to
    workspace = runtime.cas.json(OPERATOR, "operator", state.workspace)["files"]
    def corrupt(principal, namespace, ref, target):
        if ref == workspace["notes/root.md"]:
            runtime.cas._path(ref).write_bytes(b"changed")
        return original(principal, namespace, ref, target)
    monkeypatch.setattr(runtime.cas, "copy_to", corrupt)
    target = tmp_path / "partial"
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        checkpoints.materialize_set("cp1", fixture["config"], 2, target)
    assert not target.exists() and not list(tmp_path.glob(".restore-set-*"))


def test_materialization_requires_fresh_epoch_and_development_policy(stopped, tmp_path):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(fixture["config"], manifest, "operator")
    for config, epoch, error in [(fixture["config"], 1, "STALE_EPOCH"),
        (fixture["config"].model_copy(update={"recovery_policy": "terminate_confirmatory"}), 2, "CONFIRMATORY_STATE_LOSS")]:
        with pytest.raises(Fault, match=error):
            checkpoints.materialize_set("cp1", config, epoch, tmp_path / "denied")
    assert not (tmp_path / "denied").exists()


def test_private_component_and_helpers_are_never_root_readable(stopped):
    runtime, plan, _ = stopped
    _, state, ref, _ = stage(stopped)
    namespace = runtime.db.connection.execute("SELECT namespace FROM broker_files WHERE path='notes/root.md'").fetchone()[0]
    for value in (ref, state.workspace, state.skills, state.source_export):
        with pytest.raises(Fault, match="FORBIDDEN"):
            runtime.cas.read(Principal(namespace, "executor"), "operator", value)
    with pytest.raises(Fault, match="NATIVE_COMPLETE_RESTORE_REQUIRED"):
        runtime.resume(ref, plan, None)


def test_checkpoint_commit_recaptures_native_source_under_writer_lock(stopped, monkeypatch):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    put = runtime.cas.put
    changed = False
    def mutate(*args, **kwargs):
        nonlocal changed
        ref = put(*args, **kwargs)
        if not changed:
            changed = True
            runtime.db.connection.execute("DELETE FROM broker_files WHERE path='notes/root.md'")
        return ref
    monkeypatch.setattr(runtime.cas, "put", mutate)
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    with pytest.raises(Fault, match="NATIVE_EXPORT_SOURCE_CHANGED"):
        checkpoints.commit(fixture["config"], manifest, "operator")
    assert runtime.db.connection.execute("SELECT count(*) FROM checkpoints").fetchone()[0] == 0


def test_future_uncertain_costs_survive_whole_set_materialization(stopped, tmp_path):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(fixture["config"], manifest, "operator")
    db = runtime.db.connection
    reserve = BudgetLedger.model_validate_json(db.execute("SELECT body FROM ledger WHERE "
        "json_extract(body,'$.operation_id')='child-call' AND json_extract(body,'$.posting')='reserve'").fetchone()[0])
    reserve.operation_id = reserve.ledger_id = reserve.source_event_id = "later-unknown"
    reserve.parent_operation_id = None
    runtime.budgets.post("a1", reserve)
    db.execute("UPDATE operations SET uncertain=1 WHERE id='later-unknown'")
    before = runtime.budgets.status("a1")
    checkpoints.materialize_set("cp1", fixture["config"], 2, tmp_path / "retained-costs")
    assert runtime.budgets.status("a1") == before
    assert before["uncertain"] and not before["dispatch_allowed"]


def test_registered_policy_and_durable_epoch_cannot_be_overridden(stopped, tmp_path):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(fixture["config"], manifest, "operator")
    with pytest.raises(Fault, match="CHECKPOINT_IDENTITY"):
        checkpoints.materialize_set("cp1", fixture["config"].model_copy(update={"episode_s": 90}), 2, tmp_path / "changed")
    runtime.db.connection.execute("UPDATE campaigns SET epoch=10")
    with pytest.raises(Fault, match="STALE_EPOCH"):
        checkpoints.materialize_set("cp1", fixture["config"], 2, tmp_path / "stale")
    assert not (tmp_path / "changed").exists() and not (tmp_path / "stale").exists()


def test_scheduled_episode_cannot_preserve_frozen_notes_by_claiming_recovery(stopped):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped, boundary="recovery")
    manifest.scheduled_active_s = 3600
    fixture = runtime.db.checkpoint_fixture
    with pytest.raises(Fault, match="NATIVE_RETENTION_BOUNDARY"):
        Checkpoints(runtime.db, runtime.cas).commit(fixture["config"], manifest, "operator")


def test_new_component_cannot_use_older_runtime_but_committed_history_survives(stopped):
    runtime, _, _ = stopped
    service, state, ref, _ = stage(stopped)
    runtime.db.connection.execute("INSERT INTO native_jobs SELECT 'later',campaign,agent,epoch,role,parent,"
        "plan_digest,plan,state,started,ended,returncode,reason FROM native_jobs WHERE id='job'")
    assert service.load(ref)[0] == state
    with pytest.raises(Fault, match="NATIVE_LATER_STATE"):
        service.seal(state.source_export, "cp2", boundary="episode")


def test_synthetic_native_state_cannot_be_promoted_to_live_controller(stopped):
    runtime, _, _ = stopped
    runtime.db.connection.execute("UPDATE controller_profile SET simulation=0")
    with pytest.raises(Fault, match="PROFILE_MISMATCH"):
        stage(stopped)


@pytest.mark.parametrize("change,code", [("epoch", "STALE_EPOCH"), ("file", "CORRUPT_EVIDENCE"),
                                        ("extra", "MIXED_SNAPSHOT")])
def test_staging_race_cannot_publish_stale_or_changed_set(stopped, tmp_path, monkeypatch, change, code):
    runtime, _, _ = stopped
    _, _, _, manifest = stage(stopped)
    fixture = runtime.db.checkpoint_fixture
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    checkpoints.commit(fixture["config"], manifest, "operator")
    original = runtime.cas.copy_to
    def after_copy(principal, namespace, ref, target):
        result = original(principal, namespace, ref, target)
        if target.name == "runtime_state.json":
            if change == "epoch":
                runtime.db.connection.execute("UPDATE campaigns SET epoch=10")
            elif change == "file":
                (target.parent.parent / "workspace/notes/root.md").write_text("future knowledge", encoding="utf-8")
            else:
                (target.parent.parent / "workspace/unregistered.txt").write_text("private artifact", encoding="utf-8")
        return result
    monkeypatch.setattr(runtime.cas, "copy_to", after_copy)
    target = tmp_path / "unpublished"
    with pytest.raises(Fault, match=code):
        checkpoints.materialize_set("cp1", fixture["config"], 2, target)
    assert not target.exists() and not list(tmp_path.glob(".restore-set-*"))
