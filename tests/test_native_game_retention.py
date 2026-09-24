"""Synthetic native lifecycle and input failures, no game or model dispatch."""

import copy
import hashlib
import json
import shutil
import sqlite3
from types import SimpleNamespace

import pytest

from mcbench.native import NativeExec
from mcbench.native_checkpoint import POLICY
from mcbench.provisioning import TARGETS
from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT
from mcbench.storage import Fault, canonical
from mcbench.native_game_retention import GameRetention, INITIAL
from test_native_admission import admitted as fixture_admitted, broker_meta
from test_native_retirement import scenario, settle
from test_vanilla_persistence import installed as _installed, stopped

installed = _installed


@pytest.fixture
def package(configs, tmp_path):
    config, agents = configs()
    objects = {}
    def put(value):
        text = value if isinstance(value, str) else canonical(value).decode()
        ref = "cas:sha256:" + hashlib.sha256(text.encode()).hexdigest()
        objects[ref] = text
        return ref
    initial = put({"schema": "strata/NativeInitialArtifacts/1", "files": {p: put(t) for p, t in INITIAL.items()}})
    policy = put({"schema": "strata/NativeRetentionPolicy/1", "policy": POLICY, "is_example": True,
        "campaign_id": config.campaign_id, "agent_id": "a1", "system_digest": config.system_digest,
        "arm": "full", "initial_artifacts": initial, "resume_mode": "fresh_handoff"})
    agent = agents[0].model_dump() | {"initial_skills": initial, "memory_policy": policy,
        "learned_overlay": None, "resume_mode": "fresh_handoff", "requested_model": "gpt-5.6-luna",
        "runtime": {"version": CODEX_VERSION, "digest": "a" * 64},
        "dovetail_commit": DOVETAIL_COMMIT, "helper_limit": 2, "helper_depth": 2}
    body = {"schema": "strata/NativeGameRetentionInput/1", "qualification": "component_only",
        "campaign": config.model_dump() | {"recovery_policy": "resume_development"}, "agent": agent,
        "objects": objects}
    context = put({"schema": "strata/SyntheticDevelopmentContext/1", "is_example": True})
    for key in ("protocol_ref", "world_baseline", "information_policy", "communication_policy", "runtime_profile"):
        body["campaign"][key] = context
    body["campaign"]["backend"]["capability_manifest"] = context
    for key in ("inference_config", "capability_profile"):
        body["agent"][key] = context
    body["campaign"]["pack_lock"] = put({"schema": "mcbench/PackLock/1", "is_example": False,
        "lock_id": "synthetic-candidate", "status": "candidate", "provider": "curseforge", **TARGETS["vanilla"],
        "distribution_refs": [], "resolved_inventory": None, "installed_root_digest": None, "java": None,
        "launcher": None, "launch_profile": None, "expert_assertions": None, "harness_additions": [],
        "acquisition_report": None, "sealed_at": None})
    def save(value=None, raw=None):
        raw = raw if raw is not None else canonical(body if value is None else value)
        path = tmp_path / "retention.json"
        path.write_bytes(raw)
        return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    plan = SimpleNamespace(campaign_id="c1", agent_id="a1", role="executor", purpose="conformance",
        model="gpt-5.6-luna", dovetail_commit=DOVETAIL_COMMIT, binary_digest="a" * 64,
        binary_version=CODEX_VERSION, helper_limit=2, job_id="job", account="a1")
    plan.model_dump = lambda: {"campaign_id": "c1", "agent_id": "a1"}
    return body, save, plan


def test_registration_before_jobs_is_durable_draft_and_no_budget_mutation(package, database, cas):
    _, save, plan = package
    runtime = NativeExec(database, cas, simulation=True)
    retention = GameRetention(save())
    before = list(database.connection.execute("SELECT * FROM accounts"))
    retention.register(runtime, plan)
    retention.register(runtime, plan)
    assert [r[0] for r in database.connection.execute("SELECT state FROM campaigns")] == ["DRAFT"]
    assert database.connection.execute("SELECT count(*) FROM native_retention_policies").fetchone()[0] == 1
    assert list(database.connection.execute("SELECT * FROM accounts")) == before
    assert database.connection.execute("SELECT count(*) FROM native_jobs").fetchone()[0] == 0


@pytest.mark.parametrize("registered,authorized", [("gpt-6-luna", "gpt-6-luna"),
    ("gpt-5.6-luna", "gpt-6-luna"), ("gpt-6-luna", "gpt-5.6-luna")])
@pytest.mark.parametrize("version", [1, 2])
def test_pilot_launcher_uses_authorized_model_before_pack_or_output(package, tmp_path, monkeypatch,
                                                                  registered, authorized, version):
    import m0_native_game
    import native_pilot_trial
    from contextlib import ExitStack
    body, save, _ = package
    body["agent"].update(requested_model=registered, helper_limit=0,
                         runtime={"version": CODEX_VERSION, "digest": m0_native_game.BINARY_SHA256})
    source = save()
    # Only authorization admission is synthetic; exercise the real driver and
    # real sealed-retention identity check. Pack setup must not precede it.
    monkeypatch.setattr(native_pilot_trial, "check_inputs", lambda _: {"model": authorized, "budget_decision": None})
    def stop_before_pack(_):
        raise RuntimeError("IDENTITY_ACCEPTED_BEFORE_PACK")
    monkeypatch.setattr(m0_native_game, "parse_pack_binding", stop_before_pack)
    output = tmp_path / "unused-output"
    plan = {"schema": f"strata/M0NativePilot/{version}", "pilot": {}, "retention_source": source,
            "output": str(output), "pack": {}}
    with ExitStack() as resources:
        if registered == authorized:
            with pytest.raises(RuntimeError, match="IDENTITY_ACCEPTED_BEFORE_PACK"):
                m0_native_game.run_plan(plan, resources)
        else:
            with pytest.raises(Fault, match="RETENTION_INPUT_PROFILE"):
                m0_native_game.run_plan(plan, resources)
    assert not output.exists()


@pytest.mark.parametrize("case,code", [
    ("hash", "RETENTION_INPUT_CHANGED"), ("extra", "RETENTION_INPUT_INVALID"),
    ("duplicate", "RETENTION_INPUT_INVALID"), ("scope", "RETENTION_INPUT_SCOPE"),
    ("roster", "RETENTION_INPUT_SCOPE"), ("track", "RETENTION_INPUT_SCOPE"),
    ("missing", "RETENTION_INPUT_INCOMPLETE"), ("object", "RETENTION_INPUT_CHANGED"),
    ("extra-object", "RETENTION_INPUT_EXTRA_OBJECTS"), ("baseline", "RETENTION_INPUT_BASELINE"),
    ("qualified", "RETENTION_INPUT_INVALID"), ("policy", "RETENTION_INPUT_SCOPE"),
    ("context", "RETENTION_INPUT_INCOMPLETE"), ("pack", "RETENTION_INPUT_PROFILE"),
    ("hardlink", "RETENTION_INPUT_INVALID"), ("oversize", "RETENTION_INPUT_INVALID")])
def test_preflight_rejections(package, tmp_path, case, code):
    body, save, _ = package
    body = copy.deepcopy(body)
    if case == "extra":
        body["allow_dispatch"] = True
    elif case == "scope":
        body["agent"]["system_digest"] = "b" * 64
    elif case == "roster":
        body["campaign"]["n"] = 2
        body["campaign"]["agent_ids"].append("a2")
    elif case == "track":
        body["campaign"]["track"] = "pixels-os/v1"
    elif case == "missing":
        del body["objects"][body["agent"]["memory_policy"]]
    elif case == "object":
        body["objects"][body["agent"]["memory_policy"]] += " "
    elif case == "extra-object":
        body["objects"]["cas:sha256:" + hashlib.sha256(b"unused").hexdigest()] = "unused"
    elif case in {"baseline", "policy"}:
        key = "initial_skills" if case == "baseline" else "memory_policy"
        value = json.loads(body["objects"].pop(body["agent"][key]))
        if case == "baseline":
            value["files"]["docs/hidden.md"] = next(iter(body["objects"]))
        else:
            value["arm"] = "frozen-skills"
        raw = canonical(value).decode()
        ref = "cas:sha256:" + hashlib.sha256(raw.encode()).hexdigest()
        body["objects"][ref] = raw
        body["agent"][key] = ref
        if case == "baseline":
            policy = json.loads(body["objects"].pop(body["agent"]["memory_policy"]))
            policy["initial_artifacts"] = ref
            raw = canonical(policy).decode()
            ref = "cas:sha256:" + hashlib.sha256(raw.encode()).hexdigest()
            body["objects"][ref] = raw
            body["agent"]["memory_policy"] = ref
    elif case == "qualified":
        body["qualification"] = "complete_checkpoint"
    elif case == "context":
        del body["objects"][body["campaign"]["protocol_ref"]]
    elif case == "pack":
        value = json.loads(body["objects"].pop(body["campaign"]["pack_lock"]))
        value["is_example"] = True
        raw = canonical(value).decode()
        ref = "cas:sha256:" + hashlib.sha256(raw.encode()).hexdigest()
        body["objects"][ref] = raw
        body["campaign"]["pack_lock"] = ref
    source = save(body)
    if case == "hash":
        source["sha256"] = "0" * 64
    elif case == "duplicate":
        source = save(raw=b'{"schema":1,"schema":2}')
    elif case == "hardlink":
        (tmp_path / "alias").hardlink_to(source["path"])
    elif case == "oversize":
        source = save(raw=b" " * (1024 * 1024 + 1))
    with pytest.raises(Fault, match=code):
        GameRetention(source)


@pytest.mark.parametrize("change", ["scope", "model", "binary", "helpers", "mode", "late"])
def test_registration_scope_and_lateness_fail_closed(package, database, cas, change):
    _, save, plan = package
    retention = GameRetention(save())
    runtime = NativeExec(database, cas, simulation=True)
    if change == "scope":
        plan.model_dump = lambda: {"campaign_id": "wrong", "agent_id": "a1"}
    elif change == "model":
        plan.model = "different"
    elif change == "binary":
        plan.binary_digest = "b" * 64
    elif change == "helpers":
        plan.helper_limit = 3
    elif change == "mode":
        runtime.simulation = False
    elif change == "late":
        database.connection.execute("INSERT INTO native_jobs(id,campaign,agent) VALUES('prior','c1','a1')")
    with pytest.raises(Fault, match="RETENTION"):
        retention.register(runtime, plan)
    assert not database.connection.execute("SELECT 1 FROM sqlite_master WHERE name='campaigns'").fetchone()


@pytest.fixture
def stopped_retention(package, database, cas, tmp_path, example):
    body, save, plan = package
    body["agent"]["helper_limit"] = plan.helper_limit = 1
    runtime = NativeExec(database, cas, simulation=True)
    retention = GameRetention(save())
    retention.register(runtime, plan)
    admitted = fixture_admitted.__wrapped__(database, cas, tmp_path, example)
    admission, gate, broker, launch, _, _, put = admitted
    with database.transaction() as db:
        database.event(db, "runtime.prepared", {"job_id": "job"})
    def files():
        for path, text in INITIAL.items():
            broker.project("root", path, text)
        broker.call("artifact_write", {"path": "notes/root.md", "text": "Before the stop.", "expected_ref": None}, broker_meta())
        broker.call("artifact_write", {"path": "results/private.md", "text": "Unshared.", "expected_ref": None}, broker_meta("child", "root"))
    _, ref, _, observed = scenario(admitted, before_revoke=files)
    settle(admitted, observed)
    admission.retire("job", "child", ref)
    database.connection.execute("UPDATE native_jobs SET state='UNSETTLED',returncode=0")
    seal = put({"schema": "strata/InferenceIngressSeal/1", "is_example": True, "job_id": "job",
        "profile_digest": launch.profile_digest(), "process_tree_dead": True, "ingress_closed": True,
        "handlers_fenced": True, "participant_threads": ["child", "root"],
        "attempt_ids": ["child-call", "root-call", "status-issue", "status-observed"]})
    runtime.close_dispatch_budget("job", seal)
    return retention, runtime, launch


def test_complete_native_component_keeps_own_state_and_costs(stopped_retention):
    retention, runtime, launch = stopped_retention
    before = runtime.budgets.status("a1")
    report = retention.finish()
    assert report == retention.finish()
    assert runtime.budgets.status("a1") == before
    assert not report["complete_checkpoint"] and not report["dispatch_authorized"] and report["G0"] == "fail"
    from mcbench.native_export import OPERATOR
    retained = runtime.cas.json(OPERATOR, "operator", report["component"]["workspace"])["files"]
    assert set(retained) == {*INITIAL, "notes/root.md"}
    assert not any(path.startswith("results/") for path in retained)
    with pytest.raises(Fault, match="NATIVE_RETENTION_TOO_LATE"):
        retention.register(runtime, retention.plan)


@pytest.fixture
def archived_retention(stopped_retention, tmp_path):
    retention, runtime, launch = stopped_retention
    report = retention.finish()
    root = tmp_path / "archive"
    native = root / "run/native"
    native.mkdir(parents=True)
    with sqlite3.connect(native / "synthetic.sqlite") as target:
        runtime.db.connection.backup(target)
    shutil.copytree(runtime.cas.root, native / "objects")
    (root / "run/retention-input.json").write_bytes(retention.raw)
    (root / "run/native-result.json").write_bytes(canonical({"retention": report}))
    (root / "run/result.json").write_bytes(canonical({"native_retention": report}))
    intent = {"plan": {"schema": "strata/M0NativeGameSmoke/2", "retention_source": retention.source}}
    return root, launch, intent


def inspect_archive_retention(root, launch, intent):
    from strata_evaluator.evidence_bundle import EvidenceBundle, EvidenceCAS
    from strata_evaluator.native_game_retention import inspect_retention
    from test_native_game_evidence import seal
    bundle = EvidenceBundle(root, seal(root))
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with bundle.database("run/native/synthetic.sqlite") as db:
        result = inspect_retention(db, EvidenceCAS(db, bundle, "run/native/objects"), bundle, launch, intent)
    assert before == {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    return result


def test_read_only_reconstruction_keeps_archive_unchanged(archived_retention):
    result = inspect_archive_retention(*archived_retention)
    assert result["preregistered"] and result["costs_preserved"] and result["retained_files"] == 4
    assert not result["complete_checkpoint"]


@pytest.mark.parametrize("case,code", [("late", "NATIVE_RETENTION_TOO_LATE"),
    ("policy", "NATIVE_GAME_RETENTION_INPUT"), ("component", "NATIVE_CHECKPOINT_UNCOMMITTED"),
    ("claim", "NATIVE_GAME_RETENTION_COMPONENT"), ("scope", "RETENTION_INPUT_SCOPE"),
    ("old-profile", "NATIVE_GAME_RETENTION_PROFILE")])
def test_reconstruction_rejects_derived_corruption(archived_retention, case, code):
    root, launch, intent = archived_retention
    with sqlite3.connect(root / "run/native/synthetic.sqlite") as db:
        if case == "late":
            db.execute("UPDATE outbox SET cursor=cursor+10000 WHERE kind='native.retention_registered'")
        elif case == "policy":
            db.execute("UPDATE native_retention_policies SET ref=?", ("cas:sha256:" + "b" * 64,))
        elif case == "component":
            db.execute("DELETE FROM native_checkpoint_states")
    db.close()
    if case == "claim":
        for name, key in (("native-result.json", "retention"), ("result.json", "native_retention")):
            path = root / "run" / name
            body = json.loads(path.read_bytes())
            body[key]["complete_checkpoint"] = True
            path.write_bytes(canonical(body))
    elif case == "scope":
        launch = launch.model_copy(update={"campaign_id": "wrong"})
    elif case == "old-profile":
        intent["plan"]["schema"] = "strata/M0NativeGameSmoke/1"
    with pytest.raises(Fault, match=code):
        inspect_archive_retention(root, launch, intent)


@pytest.mark.parametrize("server", [None, {}, {"stopped_snapshot": None}])
def test_missing_server_capture_has_typed_failure(tmp_path, server):
    from mcbench.native_game_retention import paired_components
    with pytest.raises(Fault, match="M0_CAPTURE_INCOMPLETE"):
        paired_components(tmp_path, {"status": "fail", "server_result": server}, "a" * 64, {})


@pytest.mark.parametrize("case", ["valid", "wrong-plan", "world-changed", "joint-changed",
                                 "player-copy-changed", "player-copy-same-size", "player-copy-missing", "no-player", "two-players"])
def test_stopped_world_and_native_component_join(archived_retention, installed, case):
    from mcbench.storage import digest
    from mcbench.vanilla_persistence import VanillaPersistence
    from strata_evaluator.evidence_bundle import EvidenceBundle
    from strata_evaluator.native_game_retention import inspect_stopped_components
    from test_native_game_evidence import seal
    root, _, _ = archived_retention
    retention = inspect_archive_retention(*archived_retention)
    server_plan = {"schema": "strata/DevelopmentServer/2"}
    target = root / "run/server/stopped-instance"
    target.parent.mkdir()
    players = installed / "world/playerdata"
    players.mkdir()
    if case != "no-player":
        (players / "11111111-1111-1111-1111-111111111111.dat").write_bytes(b"synthetic saved player")
    if case == "two-players":
        (players / "22222222-2222-2222-2222-222222222222.dat").write_bytes(b"synthetic sibling")
    if case != "player-copy-missing":
        (root / "run/player-after.dat").write_bytes(
            b"different player" if case == "player-copy-changed" else
            b"x" * len(b"synthetic saved player") if case == "player-copy-same-size" else b"synthetic saved player")
    service = VanillaPersistence(installed)
    try:
        snapshot = service.capture(target, stopped(), plan_digest=digest(server_plan))
    finally:
        service.close()
    from mcbench.native_game_retention import paired_components
    summary = {"status": "pass", "server_result": {"stopped_snapshot": snapshot},
               "native_retention": {"component_ref": retention["component_ref"]}}
    paired = paired_components(root / "run", summary, retention["input_sha256"], server_plan)
    assert paired["snapshot_sha256"] == snapshot["manifest_sha256"] and not paired["complete_checkpoint"]
    with pytest.raises(Fault, match="M0_CAPTURE_INCOMPLETE"):
        paired_components(root / "run", summary | {"status": "fail"}, retention["input_sha256"], server_plan)
    with pytest.raises(Fault, match="M0_CAPTURE_INCOMPLETE"):
        paired_components(root / "wrong-run", summary, retention["input_sha256"], server_plan)
    # Never follow historical absolute paths, even when the summary contains one.
    snapshot["path"] = "C:/not-an-authorized-input"
    joint = {"schema": "strata/NativeGameStoppedComponents/1", "native_component": retention["component_ref"],
        "snapshot_sha256": snapshot["manifest_sha256"], "retention_input_sha256": retention["input_sha256"],
        "complete_checkpoint": False, "dispatch_authorized": False, "G0": "fail"}
    (root / "run/joint-components.json").write_bytes(canonical(joint))
    if case == "wrong-plan":
        server_plan["extra"] = "changed"
    elif case == "world-changed":
        (target / "state/world/level.dat").write_bytes(b"later knowledge")
    elif case == "joint-changed":
        joint = joint | {"dispatch_authorized": True}
    bundle = EvidenceBundle(root, seal(root))
    def inspect():
        return inspect_stopped_components(bundle, retention, {"stopped_snapshot": snapshot},
                                          server_plan, {"joint_components": joint})
    if case == "valid":
        assert inspect()["stopped_world_captured"] and not inspect()["complete_checkpoint"]
        assert inspect()["saved_player_bound_to_snapshot"]
    else:
        with pytest.raises(Fault):
            inspect()
