"""Whole-pair protected world copying under live preparation and writer custody.

The originals stay immutable. Copies are borrowed only inside an operator
continuation; this stage cannot authorize native gameplay or resurrect a copy.
"""

from pathlib import Path

from mcbench.launch_integrity import FileLease
from mcbench.runtime import CODEX_COMPANION_PINS
from mcbench.storage import canonical, digest, extended_path, require

from .craft_reference import check_tree
from .reference_pair import LOG_LIMIT
from .writer_preparation import WriterPreparations, parse_preparation_plan, pinned_inventory

POLICY = "held-pair-protected-world-copies/1"


def runtime_inventory(plans):
    """Hold the same reviewed native executable and every execution companion."""
    pins = {}
    for plan in plans.values():
        pins[plan.codex.path] = plan.codex.model_dump()
        for name, sha in CODEX_COMPANION_PINS.items():
            path = Path(plan.codex.path).parent / name
            pins[str(path)] = {"path": str(path), "sha256": sha, "bytes": path.stat().st_size}
    return pinned_inventory(pins.values())


class HeldProbeWorldCopies:
    def __init__(self, preparation, pair, writers):
        self.preparation, self.pair, self.writers = preparation, pair, writers
        self.closed = False

    def check(self):
        require(not self.closed, "PROBE_WORLD_CUSTODY_CLOSED")
        self.preparation.check()
        require(set(self.writers) == set(self.pair["arm_order"]), "PROBE_WORLD_ROSTER")
        for writer in self.writers.values():
            writer.check()
            require(not writer.launched and not writer.completed, "PROBE_WORLD_ALREADY_LAUNCHED")
            check_tree(writer.tree.path, writer.plan.sources)
        return {
            "policy": POLICY,
            "world_digest": self.pair["world_digest"],
            "roots": {arm: str(writer.tree.path) for arm, writer in self.writers.items()},
            "native_launch_authorized": False,
            "live_initial_state_verified": False,
        }


class ProbeWorldCopies:
    def __init__(self, preparation):
        self.preparation = preparation
        self.db = preparation.db
        with self.db.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS probe_world_copies (namespace TEXT,pair TEXT,"
                "plan TEXT,state TEXT,body TEXT,PRIMARY KEY(namespace,pair))"
            )

    def run(self, principal, values, *, continuation):
        """Prepare both exact worlds, borrow them together, then discard unlaunched.

        A later game-launch policy must explicitly extend this lifetime. A
        returned map or surviving directory grants no writer/runtime authority.
        """
        prep = self.preparation
        prep.views.pairs._authorize(principal)
        require(callable(continuation), "PROBE_WORLD_CONTINUATION")
        prep.check()
        pair, _, target, view_target, _, _ = prep._source(prep.pair_id)
        require(
            isinstance(values, dict) and set(values) == set(pair["arm_order"]), "PROBE_WORLD_ROSTER"
        )
        plans = {arm: parse_preparation_plan(value) for arm, value in values.items()}
        namespaces = []
        total = sum(entry["bytes"] for entry in prep.plan["inventory"]["files"])
        for arm, plan in plans.items():
            root = target / pair["arm_directories"][arm] / "server"
            require(
                extended_path(Path(plan.source_root)) == root
                and set(plan.sources) == set(pair["world_files"]),
                "PROBE_WORLD_SOURCE",
            )
            require((plan.evidence_kind == "synthetic") is pair["is_example"], "PROFILE_MISMATCH")
            for name, ref in pair["world_files"].items():
                pin = plan.sources[name]
                record = self.db.connection.execute(
                    "SELECT bytes FROM objects WHERE namespace=? AND ref=?",
                    (prep.views.namespace, ref),
                ).fetchone()
                require(
                    record is not None
                    and pin.sha256 == ref[11:]
                    and pin.bytes == record[0]
                    and extended_path(Path(pin.path)) == root / name,
                    "PROBE_WORLD_SOURCE",
                )
            paths = [
                extended_path(Path(p)) for p in (plan.workspace_directory, plan.evidence_directory)
            ]
            require(
                all(
                    not p.exists()
                    and all(
                        not p.is_relative_to(q) and not q.is_relative_to(p)
                        for q in [target, view_target, *namespaces]
                    )
                    for p in paths
                ),
                "PROBE_WORLD_NAMESPACE",
            )
            namespaces.extend(paths)
            # Finite copier inputs + destination + manifest, helper and two
            # bounded private logs. Full game/runtime storage is a later gate.
            total += (
                sum(pin.bytes for pin in plan.sources.values()) * 2
                + plan.helper_class.bytes
                + 8 * 1024**2
                + 2 * LOG_LIMIT
            )
            require(plan.max_wall_s < prep.deadline - prep.monotonic(), "PROBE_WORLD_DEADLINE")
        require(len({p.id for p in plans.values()}) == 2, "PROBE_WORLD_IDENTITY")
        require(total <= prep.plan["resources"]["disk_bytes"], "PROBE_STORAGE_LIMIT")
        plan = {
            "policy": POLICY,
            "preparation_digest": digest(prep.plan),
            "world_digest": pair["world_digest"],
            "writers": {arm: p.model_dump(by_alias=True) for arm, p in plans.items()},
            "copy_storage_bound": total,
            "native_launch_authorized": False,
        }
        key = (prep.views.namespace, prep.pair_id)
        with self.db.transaction() as db:
            require(
                db.execute(
                    "SELECT 1 FROM probe_world_copies WHERE namespace=? AND pair=?", key
                ).fetchone()
                is None,
                "PROBE_WORLD_COPIES_CONSUMED",
            )
            db.execute(
                "INSERT INTO probe_world_copies VALUES(?,?,?,'PREPARING','{}')",
                (*key, canonical(plan).decode()),
            )
            self.db.event(
                db,
                "probe.world_copies_preparing",
                {"namespace": key[0], "pair": key[1], "plan_digest": digest(plan)},
            )
        writers, results, borrowed = {}, {}, None
        body = {
            "policy": POLICY,
            "plan_digest": digest(plan),
            "native_launch_authorized": False,
            "live_initial_state_verified": False,
            "results": results,
        }

        def stage(index):
            nonlocal borrowed
            if index == len(pair["arm_order"]):
                borrowed = HeldProbeWorldCopies(prep, pair, writers)
                body["held"] = borrowed.check()
                with self.db.transaction() as db:
                    db.execute(
                        "UPDATE probe_world_copies SET state='HELD',body=? WHERE namespace=? AND pair=?",
                        (canonical(body).decode(), *key),
                    )
                    self.db.event(
                        db,
                        "probe.world_copies_held",
                        {"namespace": key[0], "pair": key[1], **body["held"]},
                    )
                try:
                    continuation(borrowed)
                    borrowed.check()
                finally:
                    borrowed.closed = True
                return
            arm = pair["arm_order"][index]
            prep.check()
            require(
                plans[arm].max_wall_s < prep.deadline - prep.monotonic(), "PROBE_WORLD_DEADLINE"
            )
            require(
                all(
                    plans[arm].max_wall_s < writer.deadline - prep.monotonic()
                    for writer in writers.values()
                ),
                "PROBE_WORLD_DEADLINE",
            )

            def held(writer):
                writers[arm] = writer
                try:
                    stage(index + 1)
                    writer.discard_unlaunched()
                finally:
                    writers.pop(arm, None)

            results[arm] = WriterPreparations(self.db).run(
                plans[arm].model_dump(by_alias=True), continuation=held
            )
            require(
                results[arm]["status"] == "discarded_preparation"
                and results[arm]["custody"]["status"] == "discarded"
                and results[arm]["custody"]["live"] is False,
                "PROBE_WORLD_CLOSE_UNCERTAIN",
            )

        try:
            with FileLease(runtime_inventory(plans)) as native_inputs:
                body["native_input_inventory"] = native_inputs.inventory
                stage(0)
                native_inputs.recheck()
            prep.check()
            with self.db.transaction() as db:
                db.execute(
                    "UPDATE probe_world_copies SET state='DISCARDED',body=? WHERE namespace=? AND pair=?",
                    (canonical(body).decode(), *key),
                )
                self.db.event(
                    db,
                    "probe.world_copies_discarded",
                    {"namespace": key[0], "pair": key[1], "body_digest": digest(body)},
                )
            return body
        except BaseException as error:
            body["failure"] = getattr(error, "code", type(error).__name__)
            try:
                with self.db.transaction() as db:
                    db.execute(
                        "UPDATE probe_world_copies SET state='FAILED',body=? WHERE namespace=? AND pair=?",
                        (canonical(body).decode(), *key),
                    )
                    self.db.event(
                        db,
                        "probe.world_copies_failed",
                        {"namespace": key[0], "pair": key[1], **body},
                    )
            finally:
                prep.close()  # Child writer/process cleanup has already unwound.
            raise
