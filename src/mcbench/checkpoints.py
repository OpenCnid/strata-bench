"""Complete-set checkpoint commit and safe, fresh-directory materialization.

Clean-stop attestations are supplied by the private supervisor; authentic pack
path coverage and actual restore semantics still require integration evidence.
"""

import hashlib
import json
import os
import tempfile
from contextlib import nullcontext
from pathlib import Path

from .records import CampaignConfig, CheckpointManifest, PackLock
from .storage import CAS, Database, Principal, canonical, digest, extended_path, reject_links, require, safe_relative

OPERATOR = Principal("operator", "operator")


class Checkpoints:
    def __init__(self, database: Database, cas: CAS):
        self.database, self.cas = database, cas
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS checkpoints (id TEXT PRIMARY KEY, campaign TEXT, "
                       "epoch INTEGER, digest TEXT, ref TEXT, namespace TEXT)")

    def _native_components(self, manifest, namespace):
        db = self.database.connection
        required = False
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='native_retention_policies'").fetchone():
            required = db.execute("SELECT 1 FROM native_retention_policies WHERE campaign=?",
                                  (manifest.campaign_id,)).fetchone() is not None
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='native_jobs'").fetchone():
            required |= db.execute("SELECT 1 FROM native_jobs WHERE campaign=? AND "
                "json_extract(plan,'$.broker_policy') IS NOT NULL", (manifest.campaign_id,)).fetchone() is not None
        # A native component remains typed even if its registration store is missing.
        for agent in manifest.agents:
            raw = self.cas.read(OPERATOR, namespace, agent.runtime_state, max_bytes=4 * 1024 * 1024)
            try:
                body = json.loads(raw)
            except (ValueError, UnicodeError):
                body = None
            if isinstance(body, dict):
                required |= body.get("schema") in {"strata/NativeState/2", "strata/NativeCheckpointState/1"}
        if not required:
            return None
        require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_profile'").fetchone(),
                "NATIVE_EXPORT_PROFILE")
        from .native import NativeExec
        from .native_checkpoint import NativeCheckpointStates
        mode = db.execute("SELECT simulation FROM native_profile WHERE singleton=1").fetchone()
        require(mode is not None, "NATIVE_EXPORT_PROFILE")
        return NativeCheckpointStates(NativeExec(self.database, self.cas, simulation=bool(mode[0])))

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
        native = self._native_components(manifest, namespace)
        if native:
            for agent in manifest.agents:
                native.validate_snapshot(manifest, agent, namespace)
                require(native.load(agent.runtime_state)[1] == config, "CHECKPOINT_IDENTITY")
        body = manifest.model_dump() | {"status": "committed"}
        body["manifest_digest"] = digest({k: v for k, v in body.items() if k != "manifest_digest"})
        committed = CheckpointManifest.model_validate(body)
        ref = self.cas.put(OPERATOR, namespace, "operator", canonical(body), quota_bytes=2**53 - 1)
        with self.database.transaction() as db:
            if native:
                for agent in manifest.agents:
                    native.validate_snapshot(manifest, agent, namespace)
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

    def load(self, checkpoint_id, *, _native=None):
        row = self.database.connection.execute("SELECT * FROM checkpoints WHERE id=?",
                                               (checkpoint_id,)).fetchone()
        require(row is not None, "CHECKPOINT_MISSING")
        body = self.cas.json(OPERATOR, row["namespace"], row["ref"])
        require(digest({k: v for k, v in body.items() if k != "manifest_digest"}) == row["digest"] ==
                body["manifest_digest"], "CORRUPT_EVIDENCE")
        manifest = CheckpointManifest.model_validate(body)
        native = _native or self._native_components(manifest, row["namespace"])
        if native:
            with (nullcontext(self.database.connection) if self.database.connection.in_transaction else self.database.transaction()):
                for agent in manifest.agents:
                    native.validate_snapshot(manifest, agent, row["namespace"])
        return manifest, row["namespace"]

    def materialize_world(self, checkpoint_id, target: Path):
        manifest, namespace = self.load(checkpoint_id)
        target = extended_path(target)
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

    def materialize_set(self, checkpoint_id, config: CampaignConfig, current_epoch: int, target: Path):
        """Stage every recorded member in one fresh private operator directory.

        Only each agent's workspace is a candidate for later broker projection.
        The set grants no process launch, capabilities, or restore assertions.
        """
        self.recovery_plan(checkpoint_id, config, current_epoch)
        manifest, namespace = self.load(checkpoint_id)
        native = self._native_components(manifest, namespace)
        require(native is not None, "NATIVE_CHECKPOINT_REQUIRED")
        require(all(native.load(a.runtime_state)[1] == config for a in manifest.agents), "CHECKPOINT_IDENTITY")
        campaign = self.database.connection.execute("SELECT epoch FROM campaigns WHERE id=?", (config.campaign_id,)).fetchone()
        require(campaign is not None and current_epoch >= campaign[0], "STALE_EPOCH")
        target = extended_path(target)
        reject_links(target)
        require(not target.exists(), "TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        members = {}
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".restore-set-") as temporary:
            staging = Path(temporary) / "instance"
            staging.mkdir()
            self.materialize_world(checkpoint_id, staging / "server")
            copied = {"server/" + k: v for k, v in
                      self.cas.json(OPERATOR, namespace, manifest.world_and_external_state)["files"].items()}
            for agent in manifest.agents:
                state = native.validate_snapshot(manifest, agent, namespace)
                files = {}
                for ref in (state.workspace, state.skills):
                    files |= self.cas.json(OPERATOR, "operator", ref)["files"]
                # IDs allow punctuation that is not a safe Windows path. Use an
                # identity digest, never an agent-supplied directory component.
                directory = "agents/" + digest({"agent_id": agent.agent_id})
                workspace = staging.joinpath(*directory.split("/")) / "workspace"
                workspace.mkdir(parents=True)
                for path, ref in files.items():
                    file = workspace.joinpath(*safe_relative(path).parts)
                    file.parent.mkdir(parents=True, exist_ok=True)
                    self.cas.copy_to(OPERATOR, "operator", ref, file)
                    copied[directory + "/workspace/" + path] = ref
                private = workspace.parent / "private"
                private.mkdir()
                for field in ("backend_state", "keymap", "runtime_state"):
                    if ref := getattr(agent, field):
                        self.cas.copy_to(OPERATOR, namespace, ref, private / (field + ".json"))
                        copied[directory + "/private/" + field + ".json"] = ref
                skill_part = self.cas.json(OPERATOR, "operator", state.skills)
                if activation_ref := skill_part.get("activation_ref"):
                    from .native_skill_activation import read_set
                    read_set(self.database.connection, self.cas, activation_ref)
                    self.cas.copy_to(OPERATOR, "operator", activation_ref, private / "active_skills.json")
                    copied[directory + "/private/active_skills.json"] = activation_ref
                if publication_ref := skill_part.get("publication_ref"):
                    publication = native.publications.load(publication_ref)
                    self.cas.copy_to(OPERATOR, "operator", publication_ref, private / "skill_candidates.json")
                    copied[directory + "/private/skill_candidates.json"] = publication_ref
                    bundles = private / "skill-bundles"
                    bundles.mkdir()
                    for record in publication["records"]:
                        name = record["content"][11:] + ".json"
                        self.cas.copy_to(OPERATOR, "operator", record["content"], bundles / name)
                        copied[directory + "/private/skill-bundles/" + name] = record["content"]
                members[agent.agent_id] = {"directory": directory,
                                          "files_digest": digest(files), "runtime_state": agent.runtime_state,
                                          "helper_state_imported": False, "skills_activated": False}
            # Revalidate after copy. No mixed/changed source can publish a set.
            require(self.load(checkpoint_id)[0] == manifest, "MIXED_SNAPSHOT")
            actual = {p.relative_to(staging).as_posix(): p for p in staging.rglob("*") if p.is_file()}
            require(set(actual) == set(copied), "MIXED_SNAPSHOT")
            for path, file in actual.items():
                reject_links(file)
                with file.open("rb") as stream:
                    require(hashlib.file_digest(stream, "sha256").hexdigest() == copied[path][11:], "CORRUPT_EVIDENCE")
            result = {"schema": "strata/RestoredCheckpoint/1", "checkpoint_id": checkpoint_id,
                "is_example": native.runtime.simulation,
                "manifest_digest": manifest.manifest_digest, "new_epoch": current_epoch,
                "members": members, "cost_rollback": False, "dispatch_authorized": False,
                "requires_fresh_grants": True, "requires_restore_assertions": True}
            with (staging / "restore.json").open("xb") as stream:
                stream.write(canonical(result))
                stream.flush()
                os.fsync(stream.fileno())
            with self.database.transaction() as db:
                campaign = db.execute("SELECT epoch,config FROM campaigns WHERE id=?", (config.campaign_id,)).fetchone()
                require(campaign is not None and current_epoch >= campaign["epoch"], "STALE_EPOCH")
                require(json.loads(campaign["config"]) == config.model_dump(), "CHECKPOINT_IDENTITY")
                for agent in manifest.agents:
                    native.validate_snapshot(manifest, agent, namespace)
                os.rename(staging, target)
        return result
