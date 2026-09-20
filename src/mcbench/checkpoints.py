"""Complete-set checkpoint commit and safe, fresh-directory materialization.

Clean-stop attestations are supplied by the private supervisor; authentic pack
path coverage and actual restore semantics still require integration evidence.
"""

import os
import tempfile
from pathlib import Path

from .records import CampaignConfig, CheckpointManifest, PackLock
from .storage import CAS, Database, Principal, canonical, digest, reject_links, require, safe_relative

OPERATOR = Principal("operator", "operator")


class Checkpoints:
    def __init__(self, database: Database, cas: CAS):
        self.database, self.cas = database, cas
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS checkpoints (id TEXT PRIMARY KEY, campaign TEXT, "
                       "epoch INTEGER, digest TEXT, ref TEXT, namespace TEXT)")

    def commit(self, config: CampaignConfig, manifest: CheckpointManifest, namespace: str):
        require(not manifest.is_example and not config.is_example, "EXAMPLE_NOT_EXECUTABLE")
        require(manifest.status == "preparing" and manifest.campaign_id == config.campaign_id and
                manifest.system_digest == config.system_digest and manifest.pack_lock == config.pack_lock,
                "CHECKPOINT_IDENTITY")
        require(len(manifest.agents) == config.n and
                {a.agent_id for a in manifest.agents} == set(config.agent_ids), "INCOMPLETE_CHECKPOINT")
        require(manifest.scheduled_active_s is None or
                manifest.scheduled_active_s in config.checkpoints_active_s and
                manifest.clocks.active_wall_s >= manifest.scheduled_active_s, "CHECKPOINT_SCHEDULE")
        stop = self.cas.json(OPERATOR, namespace, manifest.clean_stop_report)
        require(stop.get("schema") == "strata/CleanStop/2" and
                stop.get("checkpoint_id") == manifest.checkpoint_id and
                stop.get("campaign_id") == config.campaign_id and
                stop.get("epoch") == manifest.source_epoch and
                stop.get("server_boot_id") == manifest.server_boot_id and
                stop.get("server_tick") == manifest.server_tick and
                stop.get("event_cursor") == manifest.event_cursor and
                stop.get("ledger_cursor") == manifest.ledger_cursor and
                set(stop.get("agents", [])) == set(config.agent_ids) and
                all(stop.get(k) is True for k in ("server_stopped", "runtimes_stopped", "keys_released",
                    "calls_settled", "save_complete", "retention_applied")), "CLEAN_STOP_INCOMPLETE")
        require(stop.get("snapshot_refs") == {
            "world_and_external_state": manifest.world_and_external_state,
            "agents": [agent.model_dump() for agent in manifest.agents]}, "MIXED_SNAPSHOT")
        world = self.cas.json(OPERATOR, namespace, manifest.world_and_external_state)
        require(world.get("schema") == "strata/StateInventory/1" and
                world.get("epoch") == manifest.source_epoch and
                world.get("server_boot_id") == manifest.server_boot_id and
                world.get("server_tick") == manifest.server_tick, "MIXED_SNAPSHOT")
        files = world.get("files", {})
        require(isinstance(files, dict) and len(files) <= 200000, "INCOMPLETE_PERSISTENCE")
        require(len({path.casefold() for path in files}) == len(files), "AMBIGUOUS_PATHS")
        folded = {path.casefold() for path in files}
        required = stop.get("required_persistence_paths")
        require(isinstance(required, list) and bool(required) and set(required) <= set(files),
                "INCOMPLETE_PERSISTENCE")
        for path, ref in files.items():
            relative = safe_relative(path)
            require(not any(str(parent).casefold() in folded for parent in relative.parents
                            if str(parent) != "."), "AMBIGUOUS_PATHS")
            require(not {p.casefold() for p in relative.parts} & {
                ".git", ".codex", ".ssh", ".aws", "auth.json", "credentials.json", "keys.json",
                "launcher_accounts.json", "launcher_msa_credentials.bin", "auth-cache", "auth_cache"},
                    "SECRET_IN_SNAPSHOT")
            self.cas.verify(OPERATOR, namespace, ref)
        lock = PackLock.model_validate(self.cas.json(OPERATOR, namespace, manifest.pack_lock))
        require(lock.status == "sealed" and not lock.is_example, "PACK_NOT_SEALED")
        for agent in manifest.agents:
            for field in ("workspace", "skills", "keymap", "backend_state", "runtime_state"):
                if ref := getattr(agent, field):
                    self.cas.verify(OPERATOR, namespace, ref)
        body = manifest.model_dump() | {"status": "committed"}
        body["manifest_digest"] = digest({k: v for k, v in body.items() if k != "manifest_digest"})
        committed = CheckpointManifest.model_validate(body)
        ref = self.cas.put(OPERATOR, namespace, "operator", canonical(body), quota_bytes=2**53 - 1)
        with self.database.transaction() as db:
            prior = db.execute("SELECT * FROM checkpoints WHERE id=?", (manifest.checkpoint_id,)).fetchone()
            if prior:
                require(prior["digest"] == committed.manifest_digest, "IDEMPOTENCY_CONFLICT")
                return committed
            if manifest.parent_checkpoint_id:
                parent = db.execute("SELECT * FROM checkpoints WHERE id=?",
                                    (manifest.parent_checkpoint_id,)).fetchone()
                require(parent is not None and parent["campaign"] == config.campaign_id and
                        parent["epoch"] <= manifest.source_epoch, "CHECKPOINT_PARENT")
            db.execute("INSERT INTO checkpoints VALUES (?,?,?,?,?,?)", (manifest.checkpoint_id,
                       config.campaign_id, manifest.source_epoch, committed.manifest_digest, ref, namespace))
            self.database.event(db, "checkpoint.committed", body)
        return committed

    def load(self, checkpoint_id):
        row = self.database.connection.execute("SELECT * FROM checkpoints WHERE id=?",
                                               (checkpoint_id,)).fetchone()
        require(row is not None, "CHECKPOINT_MISSING")
        body = self.cas.json(OPERATOR, row["namespace"], row["ref"])
        require(digest({k: v for k, v in body.items() if k != "manifest_digest"}) == row["digest"] ==
                body["manifest_digest"], "CORRUPT_EVIDENCE")
        return CheckpointManifest.model_validate(body), row["namespace"]

    def materialize_world(self, checkpoint_id, target: Path):
        manifest, namespace = self.load(checkpoint_id)
        target = target.absolute()
        reject_links(target)
        require(not target.exists(), "TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        files = self.cas.json(OPERATOR, namespace, manifest.world_and_external_state)["files"]
        # Hash every blob before creating staging, then recheck during streamed copy.
        # A multi-gigabyte save must not be buffered as one Python byte array.
        for ref in files.values():
            self.cas.verify(OPERATOR, namespace, ref)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".restore-") as temporary:
            staging = Path(temporary) / "instance"
            staging.mkdir()
            for path, ref in files.items():
                file = staging.joinpath(*safe_relative(path).parts)
                file.parent.mkdir(parents=True, exist_ok=True)
                self.cas.copy_to(OPERATOR, namespace, ref, file)
            os.rename(staging, target)
        return manifest

    def recovery_plan(self, checkpoint_id, config: CampaignConfig, current_epoch: int):
        manifest, _ = self.load(checkpoint_id)
        require(manifest.campaign_id == config.campaign_id and manifest.system_digest == config.system_digest
                and manifest.pack_lock == config.pack_lock, "CHECKPOINT_IDENTITY")
        require(config.recovery_policy == "resume_development", "CONFIRMATORY_STATE_LOSS")
        require(current_epoch > manifest.source_epoch, "STALE_EPOCH")
        # Deliberately includes all agent/backend/runtime references; no world-only resume.
        return {"checkpoint": manifest.model_dump(), "new_epoch": current_epoch,
                "label": "development-lost-interval", "cost_rollback": False,
                "requires_fresh_grants": True, "requires_restore_assertions": True}
