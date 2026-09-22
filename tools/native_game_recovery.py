"""Continue the scripted M0 native/game path from its sealed stopped components."""

import json
import math
import os
from pathlib import Path
import shutil
import sqlite3

from mcbench.inventory import file_hash
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.native_export import OPERATOR, inspect_native_source
from mcbench.native_game_retention import GameRetention
from mcbench.storage import canonical, digest, require
from mcbench.vanilla_persistence import layout, verify_snapshot
from strata_evaluator.evidence_bundle import EvidenceBundle, EvidenceCAS
from strata_evaluator.native_game_evidence import bootstrap_inventory
from strata_evaluator.native_game_retention import inspect_retention
from strata_evaluator.saved_blocks import NbtReader, field, unpack_chunk


def player_matches(player, state):
    """Compare only own visible state; raw saved NBT stays operator-side."""
    positions, rotations = field(player, "Pos", 9), field(player, "Rotation", 9)
    require(positions[0] == 6 and len(positions[1]) == 3 and rotations[0] == 5
            and len(rotations[1]) == 2, "GAME_RECOVERY_PLAYER")
    position, rotation = ([t.value for t in value[1]] for value in (positions, rotations))
    require(all(math.isfinite(v) for v in position + rotation), "GAME_RECOVERY_PLAYER")
    items = field(player, "Inventory", 9)
    require(items[0] == 10, "GAME_RECOVERY_PLAYER")
    inventory = {}
    for item in items[1]:
        slot = field(item.value, "Slot", 1)
        slot = slot + 36 if 0 <= slot <= 8 else 45 if slot == -106 else 108 - slot if 100 <= slot <= 103 else slot
        require(5 <= slot <= 45 and slot not in inventory, "GAME_RECOVERY_PLAYER")
        inventory[slot] = (field(item.value, "id", 8), field(item.value, "Count", 1))
    observed = {i["slot"]: (i["item_id"], i["count"]) for i in state["inventory"] if i["count"]}
    yaw = (180 - math.degrees(state["yaw"]) + 180) % 360 - 180
    return (state["connected"] and state["dimension"] == field(player, "Dimension", 8)
        and state["health"] == field(player, "Health", 5) and state["food"] == field(player, "foodLevel", 3)
        and inventory == observed and abs((rotation[0] - yaw + 180) % 360 - 180) <= .01
        and abs(rotation[1] + math.degrees(state["pitch"])) <= .01
        and all(abs(position[i] - state["position"][axis]) <= .01 for i, axis in enumerate(("x", "y", "z"))))


class GameRecovery:
    def __init__(self, source, *, sealed=False):
        require(type(sealed) is bool and isinstance(source, dict)
                and set(source) == {"bundle", "seal_sha256"} | (set() if sealed else {"template_directory"}),
                "GAME_RECOVERY_SOURCE")
        self.sealed = sealed
        self.bundle = b = EvidenceBundle(source["bundle"], source["seal_sha256"], inventory_extension=bootstrap_inventory)
        self.source, self.template = source, None if sealed else safe(Path(source["template_directory"]))
        self.worker = b.json("run/worker-config.json")
        if sealed:
            from strata_evaluator.native_game_evidence import NativeGameEvidencePlan, inspect_native_game
            require(b.json("run/intent.json")["plan"]["schema"] == "strata/M0NativeGameSmoke/5", "GAME_RECOVERY_SOURCE")
            self.source_report = inspect_native_game(NativeGameEvidencePlan.model_validate({
                "schema": "strata/NativeGameEvidencePlan/1", "bundle": source["bundle"],
                "seal_sha256": source["seal_sha256"], "job_id": "root",
                **{k: self.worker[k] for k in ("campaign_id", "agent_id", "epoch")}}))
        self.result, self.server = b.json("run/result.json"), b.json("run/server/result.json")
        require(all(b.json("run/native-result.json")["checks"].values())
                and self.result.get("error") is None and self.result["native_worker_journal_join"], "GAME_RECOVERY_STOP")
        require(self.result["logs_complete"] and not self.result.get("forced_worker_cleanup")
                and not self.result.get("forced_server_cleanup")
                and all(self.result[n] == {"returncode": 0} for n in ("worker-preflight", "worker-driver", "server-driver"))
                and self.server["status"] == "stopped_unqualified" and self.server["exit_code"] == 0
                and not self.server["forced_stop"] and self.server["logs_complete"], "GAME_RECOVERY_STOP")
        with b.database("run/native/synthetic.sqlite") as db:
            cas = EvidenceCAS(db, b, "run/native/objects")
            self.native, _, _ = inspect_native_source(db, cas, "root", simulation=True)
            self.retained = inspect_retention(db, cas, b, self.native, b.json("run/intent.json"))
        require(self.retained["preregistered"], "GAME_RECOVERY_RETENTION")
        self.retention = GameRetention({"path": str(b.path("run/retention-input.json")),
                                       "sha256": self.retained["input_sha256"]})
        self.world_root = b.path("run/server/stopped-instance/manifest.json").parent
        self.world = verify_snapshot(self.world_root, self.server["stopped_snapshot"]["manifest_sha256"])
        require(self.world["server_plan_digest"] == digest(b.json("run/server/plan.json")), "GAME_RECOVERY_SOURCE")
        players = [p for p in self.world["files"] if p.startswith("world/playerdata/") and p.endswith(".dat")]
        require(len(players) == 1 and file_hash(self.world_root / "state" / players[0]) ==
                file_hash(b.path("run/player-after.dat")), "GAME_RECOVERY_PLAYER")
        self.player = NbtReader(unpack_chunk(b.read("run/player-after.dat"), 1)).root()
        # Case 04's explicitly retained publication failure did not invalidate its
        # independently verified components. Never relabel it as a successful run.
        require(self.result["status"] == "pass" or self.result.get("capture_error") == "M0_CAPTURE_INCOMPLETE"
                and "joint_components" not in self.result
                and Path(self.server["stopped_snapshot"]["path"]) != Path(source["bundle"]) / "run/server/stopped-instance"
                and safe(Path(self.server["stopped_snapshot"]["path"])) == safe(Path(source["bundle"]) / "run/server/stopped-instance"),
                "GAME_RECOVERY_STOP")
        with b.database("run/worker/actions.sqlite") as db:
            self.old_actions = [tuple(r) for r in db.execute("SELECT * FROM actions ORDER BY epoch,seq")]
            self.old_primitives = db.execute("SELECT value FROM counters WHERE name='primitive_events'").fetchone()[0]
        require(len(self.old_actions) == 1, "GAME_RECOVERY_SOURCE")

    def check_worker_runtime(self, reference):
        """Pinned recovery must retain the source run's exact worker runtime."""
        plan = self.bundle.json("run/intent.json")["plan"]
        require(plan["schema"] == ("strata/M0NativeGameSmoke/5" if getattr(self, "sealed", False) else "strata/M0NativeGameSmoke/3")
                and plan.get("worker_runtime", {}).get("sha256") == reference["sha256"]
                and self.bundle.files["run/worker-runtime.json"].sha256 == reference["sha256"]
                and self.result.get("worker_runtime", {}).get("manifest_sha256") == reference["sha256"]
                and self.result["worker_runtime"].get("held_through_owned_stop") is True,
                "GAME_RECOVERY_WORKER_CHANGED")

    def validate_sealed_binding(self, binding, invocation):
        from mcbench.pack_launch import RestoredPackLaunchBinding
        require(self.sealed and isinstance(binding, RestoredPackLaunchBinding)
                and binding.lock == self.retention.config.pack_lock == self.world["pack"]["lock"]
                and binding.request_id == self.world["pack"]["request_id"]
                and binding.restoration.sha256 == self.server["stopped_snapshot"]["manifest_sha256"]
                and safe(binding.restoration.snapshot) == safe(self.world_root), "GAME_RECOVERY_SOURCE")
        require(invocation["campaign_id"] == self.worker["campaign_id"]
                and invocation["agent_id"] == self.worker["agent_id"]
                and invocation["epoch"] == self.worker["epoch"] + 1
                and invocation["lease_id"] != self.worker["lease_id"], "GAME_RECOVERY_SCOPE")

    def restore_worker(self, prepared, output):
        require(self.sealed, "GAME_RECOVERY_SOURCE")
        self.validate_sealed_binding(prepared.binding, prepared.resolved["worker_configuration"])
        reference = {"path": str(self.bundle.path("run/worker/actions.sqlite")),
            "sha256": self.bundle.files["run/worker/actions.sqlite"].sha256,
            **{k: self.worker[k] for k in ("campaign_id", "agent_id", "epoch")}}
        prepared.restore_journal(reference)
        with (output / "player-before.dat").open("xb") as stream:
            stream.write(self.bundle.read("run/player-after.dat"))
        self.record_source(output, prepared.resolved["worker_configuration"])

    def record_source(self, output, worker):
        with (output / "recovery-source.json").open("xb") as stream:
            stream.write(canonical({"source": self.source,
                "component": self.retained["component_ref"], "original_outer_result": self.result["status"],
                "world_snapshot": self.server["stopped_snapshot"]["manifest_sha256"], "epoch": worker["epoch"],
                "worker_rows_preserved": len(self.old_actions), "full_checkpoint": False, "G0": "fail"}))

    def verify_start(self, descriptor, observed):
        from datetime import datetime, timezone
        from mcbench.broker_stdio import WorkerTransport
        from mcbench.contracts import RpcRequest
        import time
        require(player_matches(self.player, observed["result"]["state"]), "GAME_RECOVERY_PLAYER_CHANGED")
        require(observed["result"]["last_action_seq"] is None
                and observed["result"]["state"]["active_request_id"] is None, "GAME_RECOVERY_REPLAYED")
        old = self.bundle.json(f"run/worker/grant-{self.worker['epoch']}.json")
        require(descriptor["token"] != old["token"], "GAME_RECOVERY_CREDENTIAL_REUSED")
        results = {}
        for case, grant, epoch, expected in (
            ("old_token", descriptor | {"token": old["token"]}, descriptor["epoch"], "FORBIDDEN"),
            ("old_epoch", descriptor | {"epoch": old["epoch"]}, old["epoch"], "STALE_EPOCH")):
            request = RpcRequest.model_validate({"schema": "strata/GameRequest/1",
                "campaign_id": descriptor["campaign_id"], "agent_id": descriptor["agent_id"], "epoch": epoch,
                "request_id": "recovery-denied-" + case, "method": "observe", "action": None,
                "deadline_at": datetime.fromtimestamp(time.time() + 5, timezone.utc).isoformat(
                    timespec="milliseconds").replace("+00:00", "Z"), "target_request_id": None, "after": None})
            response = WorkerTransport(grant)(request)
            require(response["status"] == "error" and response["error"]["code"] == expected,
                    "GAME_RECOVERY_STALE_ACCEPTED")
            results[case] = response
        return {"own_saved_state_matches": True, "no_action_replayed": True, "negative_requests": results,
                "original_outer_result": self.result["status"], "full_checkpoint": False}

    def materialize(self, output, server_plan, worker):
        require(not self.sealed, "GAME_RECOVERY_SOURCE")
        require(worker["campaign_id"] == self.worker["campaign_id"] and worker["agent_id"] == self.worker["agent_id"]
                and worker["epoch"] == self.worker["epoch"] + 1 and worker["port"] == self.worker["port"]
                and worker["lease_id"] != self.worker["lease_id"], "GAME_RECOVERY_SCOPE")
        target = safe(Path(server_plan["launch"]["working_directory"]))
        require(not target.exists() and not target.is_relative_to(self.template) and
                not target.is_relative_to(self.bundle.root), "GAME_RECOVERY_TARGET")
        inventory, entries, _ = layout(self.template)
        immutable = {p: e for p, e in self.world["files"].items() if e["disposition"] == "immutable"}
        require({p: e for p, e in entries.items() if e["disposition"] == "immutable"} == immutable,
                "GAME_RECOVERY_TEMPLATE")
        selected = [f for f in inventory["files"] if Path(f["path"]).relative_to(self.template).as_posix() in immutable]
        staged = target.with_name(target.name + ".preparing")
        require(not staged.exists() and shutil.disk_usage(target.parent).free >= 5 * 1024**3 + self.world["state_bytes"],
                "GAME_RECOVERY_TARGET")
        with FileLease({"schema": "strata/LaunchFileInventory/1", "files": selected,
                        "trees": snapshot([], [self.template / "libraries", self.template / "versions"])["trees"]}):
            staged.mkdir()
            for directory in self.world["directories"]:
                if directory == "world" or directory.startswith("world/"):
                    (staged / directory).mkdir(parents=True, exist_ok=True)
            for name, entry in self.world["files"].items():
                if entry["disposition"] not in {"state", "immutable"}:
                    continue
                source = (self.world_root / "state" if entry["disposition"] == "state" else self.template) / name
                dest = staged / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
                require(dest.stat().st_size == entry["bytes"] and file_hash(dest) == entry["sha256"],
                        "GAME_RECOVERY_CHANGED")
            # Session lock is a fresh empty transient; never import an old lock.
            (staged / "world/session.lock").write_bytes(b"")
            restored = layout(staged)[1]
            require({p: e for p, e in restored.items() if e["disposition"] in {"state", "immutable"}} ==
                    {p: e for p, e in self.world["files"].items() if e["disposition"] in {"state", "immutable"}},
                    "GAME_RECOVERY_CHANGED")
            self.bundle.verify()
            os.rename(staged, target)
        with self.bundle.database("run/worker/actions.sqlite") as source_db:
            with sqlite3.connect(output / "worker/actions.sqlite") as dest_db:
                source_db.backup(dest_db)
            dest_db.close()
        self.record_source(output, worker)

    def copy_native(self, output):
        require(not (output / "synthetic.sqlite").exists() and not (output / "objects").exists(), "TARGET_EXISTS")
        with self.bundle.database("run/native/synthetic.sqlite") as source:
            with sqlite3.connect(output / "synthetic.sqlite") as dest:
                source.backup(dest)
            dest.close()
        (output / "objects").mkdir()
        for name in self.bundle.files:
            if name.startswith("run/native/objects/"):
                relative = name.removeprefix("run/native/objects/")
                require('/' not in relative, "GAME_RECOVERY_SOURCE")
                (output / "objects" / relative).write_bytes(self.bundle.read(name))
        self.bundle.verify()

    def prepare(self, runtime, plan):
        self.runtime = runtime
        self.before = runtime.budgets.status(plan.account)
        require(not self.before["uncertain"], "METERING_UNKNOWN")
        self.old_limits = [tuple(r) for r in runtime.db.connection.execute("SELECT * FROM accounts ORDER BY id")]
        plan = plan.model_copy(update={"resume_component_ref": self.retained["component_ref"]})
        self.old_note = runtime.cas.json(OPERATOR,
            "operator", self.bundle.json("run/native-result.json")["retention"]["component"]["workspace"])["files"]["notes/root.md"]
        return plan

    def report(self, runtime, plan, provider):
        rows = list(runtime.db.connection.execute("SELECT f.path,f.ref FROM broker_files f JOIN broker_grants g "
            "ON json_extract(g.body,'$.namespace')=f.namespace WHERE g.runtime=? AND g.parent IS NULL", (plan.job_id,)))
        root = dict(rows)
        before = self.before["committed_and_reserved"]
        after = runtime.budgets.status(plan.account)["committed_and_reserved"]
        calls = [dict(r) for r in runtime.db.connection.execute("SELECT p.depth,l.* FROM outbox o "
            "JOIN broker_call_lifecycle l ON l.event=o.cursor "
            "JOIN native_participants p ON p.job=json_extract(o.body,'$.runtime') "
            "AND p.thread=json_extract(o.body,'$.thread') WHERE o.kind='broker.call' "
            "AND p.job=? AND json_extract(o.body,'$.tool')='artifact_read' "
            "AND json_extract(o.body,'$.arguments_digest')=?",
            (plan.job_id, digest({"path": "notes/root.md"})))]
        expected = {"path": "notes/root.md", "ref": self.old_note, "text": "STRATA_OWN_ARTIFACT"}
        def has_read(value):
            if isinstance(value, dict):
                return value == expected or any(has_read(v) for v in value.values())
            if isinstance(value, list):
                return any(has_read(v) for v in value)
            if isinstance(value, str):
                for line in [value, *value.splitlines()]:
                    try:
                        parsed = json.loads(line)
                    except ValueError:
                        continue
                    if parsed != value and has_read(parsed):
                        return True
            return False
        return {"source_component": self.retained["component_ref"], "old_epoch": self.worker["epoch"],
            "new_epoch": plan.epoch, "checks": {
                "recovery_prior_costs_preserved": all(after[k] == before[k] + increment for k, increment in
                    {"model_calls": len(provider.requests), "input_tokens": 10 * len(provider.requests),
                     "output_tokens": 4 * len(provider.requests), "spend_microusd": 14 * len(provider.requests)}.items()),
                "recovery_limits_unchanged": self.old_limits == [tuple(r) for r in runtime.db.connection.execute("SELECT * FROM accounts ORDER BY id")],
                "recovery_root_continued": root.get("notes/root.md") != self.old_note and
                    runtime.cas.read(OPERATOR, "operator", self.old_note) == b"STRATA_OWN_ARTIFACT" and
                    runtime.cas.read(OPERATOR, "operator", root["notes/root.md"]) == b"STRATA_RESTORED_AND_CONTINUED",
                "recovery_root_read_retained_note": any(r["depth"] == 0 and r["state"] == "RETURNED"
                    and r["result_digest"] == digest(expected) for r in calls)
                    and has_read(provider.outputs_by_agent.get("/root", [])),
                "recovery_helper_history_denied": any(r["depth"] == 1 and r["state"] == "REJECTED"
                    and r["fault"] == "BROKER_FORBIDDEN" for r in calls)
                    and not has_read(provider.outputs_by_agent.get("/root/identity_child", [])),
                "recovery_projection_once": runtime.db.connection.execute("SELECT count(*) FROM native_recovery_projections WHERE runtime=?", (plan.job_id,)).fetchone()[0] == 1}}

    def worker_report(self, path):
        from strata_evaluator.run_costs import frozen_database
        frozen_database(path)
        with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as db:
            old = [tuple(r) for r in db.execute("SELECT * FROM actions WHERE epoch=? ORDER BY epoch,seq", (self.worker["epoch"],))]
            current = db.execute("SELECT count(*) FROM actions WHERE epoch=?", (self.worker["epoch"] + 1,)).fetchone()[0]
            primitives = db.execute("SELECT value FROM counters WHERE name='primitive_events'").fetchone()[0]
        db.close()
        require(old == self.old_actions and current == 1 and primitives > self.old_primitives, "GAME_RECOVERY_JOURNAL")
        return {"old_actions_unchanged": True, "new_actions": current, "prior_primitives": self.old_primitives,
                "total_primitives": primitives, "full_checkpoint": False}
