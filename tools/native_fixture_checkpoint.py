"""Complete synthetic-world checkpoint around an actual stopped native fixture.

This intentionally reuses fake world bytes, boot and tick data. It proves the
native retention path, never an authentic same-boundary game checkpoint.
"""

from mcbench.checkpoints import Checkpoints
from mcbench.native_checkpoint import NativeCheckpointStates
from mcbench.native_export import OPERATOR
from mcbench.native_revisions import NativeSkillPublications
from mcbench.native_skill_activation import NativeSkillSets
from mcbench.records import CheckpointManifest
from mcbench.storage import canonical, require


def next_checkpoint(runtime, job, parent_id, checkpoint_id, *, boundary):
    require(runtime.simulation is True, "SYNTHETIC_STORE_REQUIRED")
    before = runtime.budgets.status("a1")
    checkpoints = Checkpoints(runtime.db, runtime.cas)
    parent, namespace = checkpoints.load(parent_id)
    require(namespace == "operator", "SYNTHETIC_FIXTURE_SCOPE")
    export = runtime.export_broker_state(job)
    publication = NativeSkillPublications(runtime).publish(export)
    states = NativeCheckpointStates(runtime)
    state, ref = states.seal(export, checkpoint_id, boundary=boundary)
    _, config = states.load(ref)
    def put(body):
        return runtime.cas.put(OPERATOR, "operator", "operator", canonical(body))
    body = parent.model_dump() | {"checkpoint_id": checkpoint_id, "parent_checkpoint_id": parent_id,
        "source_epoch": state.source_epoch, "status": "preparing", "manifest_digest": None,
        "scheduled_active_s": config.episode_s if boundary == "episode" else None}
    body["agents"][0] |= {"workspace": state.workspace, "skills": state.skills, "runtime_state": ref,
                          "model_identity": state.model_identity}
    world = runtime.cas.json(OPERATOR, "operator", body["world_and_external_state"])
    world["epoch"] = state.source_epoch
    body["world_and_external_state"] = put(world)
    body["event_cursor"] = runtime.db.connection.execute("SELECT max(cursor) FROM outbox").fetchone()[0]
    body["ledger_cursor"] = runtime.db.connection.execute("SELECT max(rowid) FROM ledger").fetchone()[0]
    stop = runtime.cas.json(OPERATOR, "operator", body["clean_stop_report"])
    stop |= {"checkpoint_id": checkpoint_id, "epoch": state.source_epoch,
        "ledger_cursor": body["ledger_cursor"], "event_cursor": body["event_cursor"],
        "snapshot_refs": {"world_and_external_state": body["world_and_external_state"], "agents": body["agents"]}}
    body["clean_stop_report"] = put(stop)
    committed = checkpoints.commit(config, CheckpointManifest.model_validate(body), "operator")
    sets = NativeSkillSets(runtime)
    active = sets.create(ref)
    require(runtime.budgets.status("a1") == before, "FIXTURE_ACCOUNTING_CHANGED")
    return {"is_example": True, "real_game_checkpoint": False, "export": export, "publication": publication,
        "state": ref, "manifest_digest": committed.manifest_digest, "skill_set_ref": active,
        "active_skills": sorted(sets.load(active)["skills"]), "costs_unchanged": True, "budget": before}
