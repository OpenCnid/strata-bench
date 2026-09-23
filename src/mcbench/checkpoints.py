"""Complete-set checkpoint commit and safe, fresh-directory materialization.

Clean-stop attestations are supplied by the private supervisor; authentic pack
path coverage and actual restore semantics still require integration evidence.
"""

import hashlib
import json
import os
import stat
import tempfile
from contextlib import nullcontext
from pathlib import Path

from .contracts import MAX_INT
from .records import CampaignConfig, CheckpointManifest, PackLock
from .storage import CAS, Database, Principal, canonical, digest, extended_path, reject_links, require, safe_relative

OPERATOR = Principal("operator", "operator")


class Checkpoints:
    def __init__(self, database: Database, cas: CAS):
        self.database, self.cas = database, cas
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS checkpoints (id TEXT PRIMARY KEY, campaign TEXT, "
                       "epoch INTEGER, digest TEXT, ref TEXT, namespace TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS checkpoint_restorations (path TEXT PRIMARY KEY, "
                       "checkpoint TEXT NOT NULL, epoch INTEGER NOT NULL, receipt TEXT NOT NULL)")

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

    def _set_inventory(self, manifest, namespace, native):
        """Derive every member from the committed source, not a destination manifest."""
        copied = {"server/" + k: (namespace, v) for k, v in
                  self.cas.json(OPERATOR, namespace, manifest.world_and_external_state)["files"].items()}
        directories, members = {"server", "agents"}, {}
        for agent in manifest.agents:
            state = native.validate_snapshot(manifest, agent, namespace)
            files = {}
            for ref in (state.workspace, state.skills):
                files |= self.cas.json(OPERATOR, "operator", ref)["files"]
            directory = "agents/" + digest({"agent_id": agent.agent_id})
            directories.update({directory, directory + "/workspace", directory + "/private"})
            copied.update({directory + "/workspace/" + p: ("operator", r) for p, r in files.items()})
            for field in ("backend_state", "keymap", "runtime_state"):
                if ref := getattr(agent, field):
                    copied[directory + "/private/" + field + ".json"] = (namespace, ref)
            skill_part = self.cas.json(OPERATOR, "operator", state.skills)
            if activation_ref := skill_part.get("activation_ref"):
                from .native_skill_activation import read_set
                read_set(self.database.connection, self.cas, activation_ref)
                copied[directory + "/private/active_skills.json"] = ("operator", activation_ref)
            if publication_ref := skill_part.get("publication_ref"):
                publication = native.publications.load(publication_ref)
                copied[directory + "/private/skill_candidates.json"] = ("operator", publication_ref)
                directories.add(directory + "/private/skill-bundles")
                for record in publication["records"]:
                    path = directory + "/private/skill-bundles/" + record["content"][11:] + ".json"
                    copied[path] = ("operator", record["content"])
            members[agent.agent_id] = {"directory": directory, "files_digest": digest(files),
                "runtime_state": agent.runtime_state, "helper_state_imported": False, "skills_activated": False}
        for path in copied:
            directories.update(str(p) for p in safe_relative(path).parents if str(p) != ".")
        return copied, directories, members

    def _restore_source(self, checkpoint_id, config, current_epoch, *, native=None):
        require(type(current_epoch) is int and 0 < current_epoch <= MAX_INT, "STALE_EPOCH")
        manifest, namespace = self.load(checkpoint_id, _native=native)
        require(manifest.campaign_id == config.campaign_id and manifest.system_digest == config.system_digest
                and manifest.pack_lock == config.pack_lock, "CHECKPOINT_IDENTITY")
        require(config.recovery_policy == "resume_development", "CONFIRMATORY_STATE_LOSS")
        require(current_epoch > manifest.source_epoch, "STALE_EPOCH")
        native = native or self._native_components(manifest, namespace)
        require(native is not None, "NATIVE_CHECKPOINT_REQUIRED")
        require(all(native.load(a.runtime_state)[1] == config for a in manifest.agents), "CHECKPOINT_IDENTITY")
        campaign = self.database.connection.execute("SELECT epoch,config FROM campaigns WHERE id=?",
                                                   (config.campaign_id,)).fetchone()
        require(campaign is not None and current_epoch >= campaign["epoch"], "STALE_EPOCH")
        require(json.loads(campaign["config"]) == config.model_dump(), "CHECKPOINT_IDENTITY")
        copied, directories, members = self._set_inventory(manifest, namespace, native)
        result = {"schema": "strata/RestoredCheckpoint/2", "checkpoint_id": checkpoint_id,
            "is_example": native.runtime.simulation, "manifest_digest": manifest.manifest_digest,
            "new_epoch": current_epoch, "members": members, "cost_rollback": False,
            "dispatch_authorized": False, "requires_fresh_grants": True, "requires_restore_assertions": True,
            "inventory_digest": digest({"files": {p: r for p, (_, r) in copied.items()},
                                        "directories": sorted(directories)})}
        return copied, directories, result, native

    def _verify_staged_tree(self, root, files, directories, receipt=None):
        """Point-in-time byte check; no process, write-exclusion or launch authority."""
        reject_links(root)
        require(root.is_dir(), "RESTORE_SET_MISSING")
        expected = {p: r for p, (_, r) in files.items()}
        sizes = {}
        for path, (namespace, ref) in files.items():
            self.cas.verify(OPERATOR, namespace, ref)
            sizes[path] = self.database.connection.execute(
                "SELECT bytes FROM objects WHERE namespace=? AND ref=?", (namespace, ref)).fetchone()[0]
        if receipt is not None:
            expected["restore.json"] = "cas:sha256:" + hashlib.sha256(receipt).hexdigest()
            sizes["restore.json"] = len(receipt)
        pending, seen_files, seen_dirs = [root], set(), set()
        while pending:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    reject_links(path)
                    relative = path.relative_to(root).as_posix()
                    # Windows DirEntry metadata may omit inode/link counts.
                    # Query the actual path before comparing the open handle.
                    info = path.lstat()
                    if stat.S_ISDIR(info.st_mode):
                        require(relative in directories and relative not in seen_dirs, "MIXED_SNAPSHOT")
                        seen_dirs.add(relative)
                        pending.append(path)
                    else:
                        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "UNSAFE_PATH")
                        require(relative in expected and relative not in seen_files, "MIXED_SNAPSHOT")
                        require(info.st_size == sizes[relative], "CORRUPT_EVIDENCE")
                        with path.open("rb") as stream:
                            held = os.fstat(stream.fileno())
                            require((held.st_dev, held.st_ino, held.st_size, held.st_mtime_ns, held.st_nlink) ==
                                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, 1), "CORRUPT_EVIDENCE")
                            require("cas:sha256:" + hashlib.file_digest(stream, "sha256").hexdigest() ==
                                    expected[relative], "CORRUPT_EVIDENCE")
                            after = os.fstat(stream.fileno())
                            require((after.st_size, after.st_mtime_ns, after.st_nlink) ==
                                    (held.st_size, held.st_mtime_ns, 1), "CORRUPT_EVIDENCE")
                        seen_files.add(relative)
        require(seen_files == set(expected) and seen_dirs == directories, "MIXED_SNAPSHOT")

    @staticmethod
    def _restore_path(target):
        target = extended_path(Path(target))
        reject_links(target)
        return target, os.path.normcase(str(target))

    def verify_set(self, checkpoint_id, config: CampaignConfig, current_epoch: int, target: Path):
        """Recheck a committed staged set before launch; never infer live restore success.

        A copied receipt, legacy unregistered output or interrupted publication
        cannot become authority. Full game assertions and fresh grants remain due.
        Current costs and uncertainty are never in the rollback/materialization domain.
        """
        target, key = self._restore_path(target)
        _, _, _, native = self._restore_source(checkpoint_id, config, current_epoch)
        with self.database.transaction() as db:
            row = db.execute("SELECT * FROM checkpoint_restorations WHERE path=?", (key,)).fetchone()
            require(row is not None, "RESTORE_SET_UNCOMMITTED")
            require(row["checkpoint"] == checkpoint_id and row["epoch"] == current_epoch, "RESTORE_SET_SCOPE")
            files, directories, expected, _ = self._restore_source(checkpoint_id, config, current_epoch, native=native)
            receipt = canonical(expected)
            require(row["receipt"].encode() == receipt, "RESTORE_SET_SOURCE_CHANGED")
            self._verify_staged_tree(target, files, directories, receipt)
            # Repeat the authority check after I/O under the same writer lock.
            require(self._restore_source(checkpoint_id, config, current_epoch, native=native)[2] == expected,
                    "MIXED_SNAPSHOT")
        return expected | {"verified_staging_only": True}

    def materialize_set(self, checkpoint_id, config: CampaignConfig, current_epoch: int, target: Path):
        """Stage every recorded member in one fresh private operator directory.

        Only each agent's workspace is a candidate for later broker projection.
        The set grants no process launch, capabilities, or restore assertions.
        """
        copied, directories, result, native = self._restore_source(checkpoint_id, config, current_epoch)
        target, key = self._restore_path(target)
        require(not target.exists(), "TARGET_EXISTS")
        require(self.database.connection.execute("SELECT 1 FROM checkpoint_restorations WHERE path=?", (key,)).fetchone()
                is None, "TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".restore-set-") as temporary:
            staging = Path(temporary) / "instance"
            staging.mkdir()
            for path in sorted(directories):
                staging.joinpath(*safe_relative(path).parts).mkdir(parents=True, exist_ok=True)
            for path, (namespace, ref) in copied.items():
                self.cas.copy_to(OPERATOR, namespace, ref, staging.joinpath(*safe_relative(path).parts))
            self._verify_staged_tree(staging, copied, directories)
            receipt = canonical(result)
            with (staging / "restore.json").open("xb") as stream:
                stream.write(receipt)
                stream.flush()
                os.fsync(stream.fileno())
            with self.database.transaction() as db:
                require(self._restore_source(checkpoint_id, config, current_epoch, native=native)[2] == result,
                        "MIXED_SNAPSHOT")
                self._verify_staged_tree(staging, copied, directories, receipt)
                require(db.execute("SELECT 1 FROM checkpoint_restorations WHERE path=?", (key,)).fetchone()
                        is None and not target.exists(), "TARGET_EXISTS")
                os.rename(staging, target)
                # A crash here leaves an occupied, unregistered output. Neither
                # retry nor a forged restore.json may bless or overwrite it.
                db.execute("INSERT INTO checkpoint_restorations VALUES(?,?,?,?)",
                           (key, checkpoint_id, current_epoch, receipt.decode()))
                self.database.event(db, "checkpoint.restored_set", {"path": key, **result})
        return result
