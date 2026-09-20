import hashlib
from pathlib import Path

import pytest

from mcbench.artifacts import Artifacts, episode_projection
from mcbench.checkpoints import Checkpoints
from mcbench.records import CheckpointManifest, SkillRevision
from mcbench.storage import Fault, Principal, canonical


def checkpoint_fixture(example, configs, cas, operator):
    namespace = "campaign:c1"
    def put(data):
        return cas.put(operator, namespace, "operator", canonical(data))
    config, _ = configs()
    dependency = put({"synthetic": "development-evidence-only"})
    lock_body = example("PackLock") | {"is_example": False, "status": "sealed",
        "distribution_refs": [dependency], "resolved_inventory": dependency,
        "installed_root_digest": "b" * 64, "java": {"version": "fixture", "digest": "b" * 64},
        "launcher": {"version": "fixture", "digest": "b" * 64}, "launch_profile": dependency,
        "expert_assertions": dependency, "acquisition_report": dependency,
        "sealed_at": "2026-09-18T12:00:00Z"}
    lock = put(lock_body)
    config = type(config).model_validate(config.model_dump() | {"pack_lock": lock})
    blob = put({"synthetic": "snapshot-bytes"})
    manifest = example("CheckpointManifest") | {"is_example": False, "pack_lock": lock}
    manifest["agents"][0] |= dict.fromkeys(("workspace", "skills", "backend_state", "runtime_state"), blob)
    manifest["world_and_external_state"] = put({"schema": "strata/StateInventory/1", "epoch": 1,
        "server_boot_id": "boot1", "server_tick": 72000,
        "files": {"world/level.dat": blob, "external/teams.dat": blob}})
    stop = {"schema": "strata/CleanStop/2", "checkpoint_id": "cp1", "campaign_id": "c1", "epoch": 1,
            "server_boot_id": "boot1", "server_tick": 72000, "event_cursor": 120, "ledger_cursor": 150,
            "agents": ["a1"], "required_persistence_paths": ["world/level.dat", "external/teams.dat"]}
    stop["snapshot_refs"] = {"world_and_external_state": manifest["world_and_external_state"],
                             "agents": [dict(agent) for agent in manifest["agents"]]}
    stop |= dict.fromkeys(("server_stopped", "runtimes_stopped", "keys_released", "calls_settled",
                          "save_complete", "retention_applied"), True)
    manifest["clean_stop_report"] = put(stop)
    return config, manifest, namespace, stop, put


def test_complete_checkpoint_digest_restore_and_cost_boundary(example, configs, cas, database,
                                                            operator, tmp_path):
    config, body, namespace, _, _ = checkpoint_fixture(example, configs, cas, operator)
    service = Checkpoints(database, cas)
    committed = service.commit(config, CheckpointManifest.model_validate(body), namespace)
    assert service.commit(config, CheckpointManifest.model_validate(body), namespace) == committed
    assert service.load("cp1")[0] == committed
    target = tmp_path / "fresh"
    service.materialize_world("cp1", target)
    assert (target / "world/level.dat").read_bytes() == (target / "external/teams.dat").read_bytes()
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        service.materialize_world("cp1", target)
    with pytest.raises(Fault, match="CONFIRMATORY_STATE_LOSS"):
        service.recovery_plan("cp1", config, 2)
    config = type(config).model_validate(config.model_dump() | {"recovery_policy": "resume_development"})
    plan = service.recovery_plan("cp1", config, 2)
    assert not plan["cost_rollback"] and plan["requires_fresh_grants"]
    assert plan["checkpoint"]["agents"] == body["agents"]
    with pytest.raises(Fault, match="STALE_EPOCH"):
        service.recovery_plan("cp1", config, 1)


@pytest.mark.parametrize("failure", ["mixed", "partial", "running", "missing-agent", "traversal"])
def test_incomplete_checkpoints_never_commit(failure, example, configs, cas, database, operator):
    config, body, namespace, stop, put = checkpoint_fixture(example, configs, cas, operator)
    if failure == "mixed":
        stop["server_tick"] = 1
    if failure == "partial":
        stop["required_persistence_paths"].append("external/quests.dat")
    if failure == "running":
        stop["server_stopped"] = False
    if failure == "missing-agent":
        config, _ = configs(2)
        config = type(config).model_validate(config.model_dump() | {"pack_lock": body["pack_lock"]})
    if failure == "traversal":
        world = cas.json(operator, namespace, body["world_and_external_state"])
        world["files"]["../escape"] = world["files"]["world/level.dat"]
        body["world_and_external_state"] = put(world)
        stop["snapshot_refs"]["world_and_external_state"] = body["world_and_external_state"]
    body["clean_stop_report"] = put(stop)
    service = Checkpoints(database, cas)
    with pytest.raises(Fault):
        service.commit(config, CheckpointManifest.model_validate(body), namespace)
    assert database.connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0] == 0


def test_skill_revision_cas_provenance_probe_import_and_handoff(example, cas, database, operator):
    agent = Principal("campaign:c1:agent:a1", "executor")
    ref = cas.put(agent, agent.namespace, "agent", b"learned ordinary recipe notes")
    body = example("SkillRevision") | {"is_example": False, "agent_id": "a1", "revision_id": "r1",
        "kind": "notes", "parent_revision_id": None, "content": ref, "provenance_refs": [ref],
        "generating_call_ids": ["call1"], "origin": "campaign", "status": "active",
        "activated_at": "2026-09-18T12:00:00Z"}
    service = Artifacts(database, cas)
    revision = SkillRevision.model_validate(body)
    service.publish(agent, revision, at_boundary=True)
    service.publish(agent, revision, at_boundary=True)
    assert len(service.active(agent)) == 1
    with pytest.raises(Fault, match="REVISION_CONFLICT"):
        service.publish(agent, SkillRevision.model_validate(body | {"revision_id": "r2"}), at_boundary=True)
    service.publish(agent, SkillRevision.model_validate(body | {"revision_id": "r2",
                     "parent_revision_id": "r1"}), at_boundary=True)
    with pytest.raises(Fault, match="PROBE_IMPORT"):
        service.publish(agent, SkillRevision.model_validate(body | {"origin": "probe"}), at_boundary=True)
    with pytest.raises(Fault, match="INITIAL_IMMUTABLE"):
        service.publish(agent, SkillRevision.model_validate(body | {"kind": "initial"}), at_boundary=True)
    big = cas.put(agent, agent.namespace, "agent", b"x" * 8001)
    with pytest.raises(Fault, match="QUOTA"):
        service.publish(agent, SkillRevision.model_validate(body | {"kind": "handoff", "content": big}),
                        at_boundary=True)


@pytest.mark.parametrize("change,code", [
    ("agent", "MIXED_SNAPSHOT"), ("world", "MIXED_SNAPSHOT"),
    ("checkpoint", "CLEAN_STOP_INCOMPLETE"), ("legacy", "CLEAN_STOP_INCOMPLETE"),
    ("parent-collision", "AMBIGUOUS_PATHS"), ("case-collision", "AMBIGUOUS_PATHS"),
    ("credential", "SECRET_IN_SNAPSHOT"),
])
def test_stop_proof_binds_complete_snapshot(change, code, example, configs, cas, database, operator):
    config, body, namespace, stop, put = checkpoint_fixture(example, configs, cas, operator)
    if change == "agent":
        body["agents"][0]["runtime_state"] = put({"state": "unfair-future-knowledge"})
    elif change == "checkpoint":
        stop["checkpoint_id"] = "another-checkpoint"
    elif change == "legacy":
        stop["schema"] = "strata/CleanStop/1"
    else:
        world = cas.json(operator, namespace, body["world_and_external_state"])
        path = {"world": "extra.dat", "parent-collision": "WORLD", "case-collision": "WORLD/level.dat",
                "credential": "private/.codex/auth.json"}[change]
        world["files"][path] = world["files"]["world/level.dat"]
        body["world_and_external_state"] = put(world)
        if change != "world":
            stop["snapshot_refs"]["world_and_external_state"] = body["world_and_external_state"]
    body["clean_stop_report"] = put(stop)
    with pytest.raises(Fault, match=code):
        Checkpoints(database, cas).commit(config, CheckpointManifest.model_validate(body), namespace)
    assert database.connection.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0] == 0


def test_large_restore_streams_and_corrupt_copy_never_publishes(
        example, configs, cas, database, operator, tmp_path, monkeypatch):
    config, body, namespace, stop, put = checkpoint_fixture(example, configs, cas, operator)
    source = tmp_path / "large-save.dat"
    with source.open("wb") as stream:
        for _ in range(9):
            stream.write(b"save-data" * 131072)
    with source.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    ref = cas.put_file(operator, namespace, "operator", source, sha,
                       quota_bytes=32 * 1024**2, max_object_bytes=16 * 1024**2)
    world = cas.json(operator, namespace, body["world_and_external_state"])
    world["files"]["world/region/r.0.0.mca"] = ref
    body["world_and_external_state"] = put(world)
    stop["snapshot_refs"]["world_and_external_state"] = body["world_and_external_state"]
    body["clean_stop_report"] = put(stop)
    original_read = Path.read_bytes

    def bounded_read(path):
        assert path.name != sha, "world blob must be streamed"
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", bounded_read)
    service = Checkpoints(database, cas)
    service.commit(config, CheckpointManifest.model_validate(body), namespace)
    service.materialize_world("cp1", tmp_path / "restored")
    restored = tmp_path / "restored/world/region/r.0.0.mca"
    with restored.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == sha
    original_copy = cas.copy_to

    def corrupt_during_copy(principal, ns, blob_ref, target):
        if blob_ref == ref:
            with cas._path(ref).open("r+b") as stream:
                stream.write(b"CORRUPTED")
        return original_copy(principal, ns, blob_ref, target)

    monkeypatch.setattr(cas, "copy_to", corrupt_during_copy)
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE"):
        service.materialize_world("cp1", tmp_path / "failed-restore")
    assert not (tmp_path / "failed-restore").exists()
    assert not list(tmp_path.glob(".restore-*"))
    with restored.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == sha


def test_episode_controls_clear_sessions_and_exact_artifacts():
    initial = dict.fromkeys(("notes", "procedures", "executables", "handoff", "session", "runtime_cache"),
                            "initial")
    current = dict.fromkeys(initial, "learned")
    frozen = episode_projection("frozen-persistence", initial, current)
    assert frozen == initial | {"session": None, "runtime_cache": None}
    skills = episode_projection("frozen-skills", initial, current)
    assert skills["notes"] == skills["handoff"] == "learned"
    assert skills["procedures"] == skills["executables"] == "initial"
    assert episode_projection("full", initial, current)["session"] is None
