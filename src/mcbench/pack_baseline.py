"""Explicit stopped-world baseline import after a worker-only profile change.

Operator-only: a new declared starting world, never old-campaign recovery or
checkpoint admission. Original snapshot/PackLock bytes retain their identity.
"""

from contextlib import closing
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from .inference_transport import strict_json
from .pack_launch import WorkerProfileBaseline, _absolute
from .provisioning import VanillaLaunchProfile
from .records import PackLock
from .storage import CAS, Principal, digest, require

POLICY = "vanilla1192-worker-profile-baseline/1"
LIFETIME_POLICY = "vanilla1192-worker-profile-baseline/2"


def profile_documents(binding):
    """Read both durable sealed identities in one WAL-aware, read-only snapshot."""
    source = binding.restoration
    require(isinstance(source, WorkerProfileBaseline), "PACK_BASELINE_POLICY")
    store = _absolute(binding.store)
    database = _absolute(str(store / "controller.sqlite"))
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        require([tuple(r) for r in db.execute("SELECT simulation FROM provisioning_profile")] == [(0,)],
                "SIMULATION_STORE")
        cas = CAS(SimpleNamespace(connection=db), _absolute(str(store / "objects")))
        documents = {}
        for prefix, request_id, ref in (("source", source.source_request_id, source.source_lock),
                                       ("target", binding.request_id, binding.lock)):
            row = db.execute("SELECT state,sealed,inventory,target FROM provisioning WHERE id=?",
                             (request_id,)).fetchone()
            require(row is not None and row["state"] == "SEALED" and row["sealed"] == ref
                    and row["target"] == "vanilla", "PACK_BASELINE_AUTHORITY")
            def read(reference):
                namespace = "pack:" + request_id
                metadata = db.execute("SELECT visibility FROM objects WHERE namespace=? AND ref=?",
                                      (namespace, reference)).fetchone()
                require(metadata is not None and metadata[0] == "operator", "FORBIDDEN")
                return strict_json(cas.read(Principal("pack-baseline", "operator"), namespace, reference,
                                            max_bytes=8 * 1024**2))
            lock = read(ref)
            require(lock["resolved_inventory"] == row["inventory"], "PACK_BASELINE_AUTHORITY")
            documents[prefix + "_lock"] = lock
            documents[prefix + "_profile"] = read(lock["launch_profile"])
        return documents


def verify_profile_baseline(binding, world, inventory, documents, source_root):
    """Shared live/offline validation; no archived absolute path is followed."""
    source = binding.restoration
    require(isinstance(source, WorkerProfileBaseline) and source.policy in {POLICY, LIFETIME_POLICY},
            "PACK_BASELINE_POLICY")
    require(source.source_request_id != binding.request_id and source.source_lock != binding.lock,
            "PACK_BASELINE_IDENTITY")
    parsed = {}
    for prefix, request_id, ref in (("source", source.source_request_id, source.source_lock),
                                   ("target", binding.request_id, binding.lock)):
        lock = PackLock.model_validate(documents[prefix + "_lock"])
        profile = VanillaLaunchProfile.model_validate(documents[prefix + "_profile"])
        require("cas:sha256:" + digest(lock.model_dump()) == ref and lock.lock_id == request_id
                and lock.status == "sealed" and lock.is_example is False and lock.pack_slug == "vanilla"
                and lock.minecraft == "1.19.2" and profile.is_example is False
                and "cas:sha256:" + digest(profile.model_dump()) == lock.launch_profile
                and lock.installed_root_digest == digest(inventory)
                and lock.resolved_inventory == "cas:sha256:" + digest(inventory), "PACK_BASELINE_IDENTITY")
        parsed[prefix] = lock, profile
    old_lock, old = parsed["source"]
    new_lock, new = parsed["target"]
    changed_lock_fields = {"lock_id", "launch_profile", "acquisition_report", "sealed_at"}
    lifetime = source.policy == LIFETIME_POLICY
    excluded = {"client", "worker_runtime"} | ({"worker_settings"} if lifetime else set())
    require((old.worker_settings.model_dump(exclude={"max_wall_ms"}) ==
             new.worker_settings.model_dump(exclude={"max_wall_ms"}) and
             old.worker_settings.max_wall_ms < new.worker_settings.max_wall_ms == 360000)
            if lifetime else old.worker_runtime.sha256 != new.worker_runtime.sha256,
            "PACK_BASELINE_PROFILE_CHANGED")
    require(old_lock.model_dump(exclude=changed_lock_fields) == new_lock.model_dump(exclude=changed_lock_fields)
            and old.model_dump(exclude=excluded) == new.model_dump(exclude=excluded)
            and old.client.model_dump(exclude={"executable_path", "arguments", "reviewed_bootstrap"})
            == new.client.model_dump(exclude={"executable_path", "arguments", "reviewed_bootstrap"}), "PACK_BASELINE_PROFILE_CHANGED")
    require(world["schema"] == "strata/StoppedVanillaSnapshot/2" and world["installed_inventory"] == inventory
            and world["pack"] == {"lock": source.source_lock, "request_id": source.source_request_id,
                                  "inventory_digest": digest(inventory)}, "PACK_BASELINE_SOURCE")
    # This narrow dedicated-server baseline rejects recorded player history.
    # It does not infer save semantics or certify absence of every intervention.
    require(not any(p.startswith(("world/playerdata/", "world/stats/", "world/advancements/"))
                    for p in world["files"]), "PACK_BASELINE_PLAYER_STATE")
    require(strict_json((Path(source_root) / "state/usercache.json").read_bytes()) == [],
            "PACK_BASELINE_PLAYER_STATE")
    return {"policy": source.policy, "source_lock": source.source_lock, "target_lock": binding.lock,
            "snapshot_sha256": source.sha256, "same_installed_inventory": True, "same_server_profile": True,
            "new_campaign_baseline": True, "complete_checkpoint": False, "dispatch_authorized": False}
