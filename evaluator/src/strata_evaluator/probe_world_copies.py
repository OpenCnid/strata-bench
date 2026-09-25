"""Whole-pair protected world copying under live preparation and writer custody.

The originals stay immutable. Copies are borrowed only inside an operator
continuation; this stage cannot authorize native gameplay or resurrect a copy.
"""

from pathlib import Path

from mcbench.launch_integrity import FileLease
from mcbench.runtime import CODEX_COMPANION_PINS
from mcbench.storage import Fault, canonical, digest, extended_path, require

from .craft_reference import check_tree
from .reference_pair import LOG_LIMIT
from .writer_preparation import (
    WriterPreparations,
    WriterPreparationPlanV4,
    parse_preparation_plan,
    pinned_inventory,
)
from .probe_vanilla_inputs import VanillaProbeInputs, POLICY as SOFTWARE_POLICY

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
    def __init__(self, preparation, pair, writers, software=None):
        self.preparation, self.pair, self.writers = preparation, pair, writers
        self.software = software
        self.closed = False

    def check(self):
        require(not self.closed, "PROBE_WORLD_CUSTODY_CLOSED")
        self.preparation.check()
        if self.software is not None:
            self.software.check()
        require(set(self.writers) == set(self.pair["arm_order"]), "PROBE_WORLD_ROSTER")
        for writer in self.writers.values():
            writer.check()
            require(not writer.launched and not writer.completed, "PROBE_WORLD_ALREADY_LAUNCHED")
            check_tree(writer.tree.path, writer.plan.sources)
            if isinstance(writer.plan, WriterPreparationPlanV4):
                require(
                    {
                        p.relative_to(writer.tree.path).as_posix()
                        for p in writer.tree.path.rglob("*")
                        if p.is_dir()
                    }
                    == set(writer.plan.directories),
                    "PROBE_PACK_DIRECTORIES",
                )
        return {
            "policy": POLICY if self.software is None else self.software.record["policy"],
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

    def run(
        self, principal, values, *, continuation, pack_binding=None, software_policy=SOFTWARE_POLICY
    ):
        self.preparation.views.pairs._authorize(principal)
        require(pack_binding is not None or software_policy == SOFTWARE_POLICY, "PROBE_PACK_POLICY")
        if pack_binding is not None:
            with VanillaProbeInputs(
                self.preparation, pack_binding, policy=software_policy
            ) as software:
                return self._run(principal, values, continuation=continuation, software=software)
        return self._run(principal, values, continuation=continuation)

    def run_vanilla_reference(self, principal, values, launches, *, continuation, pack_binding):
        """Separate server-reference path; never native probe/body admission.

        An operator plan factory may use the held software's compiled sources.
        Its result goes through the same full plan/custody checks as a supplied
        dictionary. This avoids acquiring the same software twice just to plan.
        """
        from .probe_vanilla_runtime import PairedVanillaRuntime

        self.preparation.views.pairs._authorize(principal)
        pair, *_ = self.preparation._source(self.preparation.pair_id)
        runtime = PairedVanillaRuntime(pair, launches)
        with VanillaProbeInputs(
            self.preparation, pack_binding, policy=runtime.software_policy
        ) as software:
            if callable(values):
                values = values(software)
                software.check()
            return self._run(
                principal, values, continuation=continuation, software=software, runtime=runtime
            )

    def run_vanilla_worker_reference(self, principal, values, launches, invocations, *, pack_binding):
        """Registered server/worker reference. No model, action or native admission."""
        from .probe_vanilla_inputs import BODY_POLICY
        from .probe_worker_runtime import PairedWorkerReference

        self.preparation.views.pairs._authorize(principal)
        pair, *_ = self.preparation._source(self.preparation.pair_id)
        with VanillaProbeInputs(self.preparation, pack_binding, policy=BODY_POLICY) as software:
            with software.hold_worker_inputs(principal, invocations) as inputs:
                runtime = PairedWorkerReference(pair, launches, inputs)
                if callable(values):
                    values = values(software)
                    inputs.check()
                return self._run(principal, values, continuation=lambda *_: None,
                                 software=software, runtime=runtime)

    def _run(self, principal, values, *, continuation, software=None, runtime=None):
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
        if software is not None:
            total += sum(entry["bytes"] for entry in software.lease.inventory["files"])
        if runtime is not None:
            total += runtime.storage_bound
        for arm, plan in plans.items():
            root = target / pair["arm_directories"][arm] / "server"
            if software is not None:
                software.validate(arm, plan)
            else:
                require(
                    not isinstance(plan, WriterPreparationPlanV4)
                    and "world_directories" not in pair,
                    "PROBE_WORLD_DIRECTORY_POLICY",
                )
                require(
                    extended_path(Path(plan.source_root)) == root
                    and set(plan.sources) == set(pair["world_files"]),
                    "PROBE_WORLD_SOURCE",
                )
            require((plan.evidence_kind == "synthetic") is pair["is_example"], "PROFILE_MISMATCH")
            for name, ref in pair["world_files"].items() if software is None else []:
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
                        for q in [
                            target,
                            view_target,
                            *namespaces,
                            *(
                                [
                                    extended_path(Path(software.binding.instance)),
                                    extended_path(Path(software.binding.store)),
                                ]
                                if software is not None
                                else []
                            ),
                        ]
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
            "policy": POLICY if software is None else software.record["policy"],
            "preparation_digest": digest(prep.plan),
            "world_digest": pair["world_digest"],
            "writers": {arm: p.model_dump(by_alias=True) for arm, p in plans.items()},
            "copy_storage_bound": total,
            "native_launch_authorized": False,
        }
        if software is not None:
            plan["software"] = software.record
        if runtime is not None:
            plan.update(policy=runtime.record["policy"], runtime=runtime.record)
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
            "policy": plan["policy"],
            "plan_digest": digest(plan),
            "native_launch_authorized": False,
            "live_initial_state_verified": False,
            "results": results,
        }

        def stage(index):
            nonlocal borrowed
            if index == len(pair["arm_order"]):
                borrowed = HeldProbeWorldCopies(prep, pair, writers, software)
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
                    if runtime is None:
                        continuation(borrowed)
                        borrowed.check()
                    else:
                        body["runtime"] = runtime.result
                        runtime.run(borrowed, continuation)
                        # run() verifies both stopped exports before returning.
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
                    if runtime is None:
                        writer.discard_unlaunched()
                    else:
                        require(
                            writer.completed
                            and writer.result["status"] == "stopped"
                            and writer.native is None,
                            "PROBE_WORLD_CLOSE_UNCERTAIN",
                        )
                finally:
                    writers.pop(arm, None)

            results[arm] = WriterPreparations(self.db).run(
                plans[arm].model_dump(by_alias=True), continuation=held
            )
            closed = (
                results[arm]["status"]
                == ("discarded_preparation" if runtime is None else "stopped_reference")
                and results[arm]["custody"]["status"]
                == ("discarded" if runtime is None else "stopped")
                and results[arm]["custody"]["live"] is False
            )
            if not closed:
                cause = results[arm].get("error")
                if isinstance(cause, str):
                    body.setdefault("writer_failure", {"arm": arm, "code": cause})
                    raise Fault("PROBE_WORLD_CLOSE_UNCERTAIN") from Fault(body["writer_failure"]["code"])
                raise Fault("PROBE_WORLD_CLOSE_UNCERTAIN")

        try:
            with FileLease(runtime_inventory(plans)) as native_inputs:
                body["native_input_inventory"] = native_inputs.inventory
                stage(0)
                native_inputs.recheck()
            prep.check()
            if software is not None:
                software.check()
            with self.db.transaction() as db:
                db.execute(
                    "UPDATE probe_world_copies SET state=?,body=? WHERE namespace=? AND pair=?",
                    (
                        "DISCARDED" if runtime is None else "STOPPED_REFERENCE",
                        canonical(body).decode(),
                        *key,
                    ),
                )
                self.db.event(
                    db,
                    "probe.world_copies_discarded"
                    if runtime is None
                    else "probe.world_references_stopped",
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
