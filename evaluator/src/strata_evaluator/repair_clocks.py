"""Bind observed live clock sources to owned native repairs, without resuming them."""

import json

from pydantic import TypeAdapter

from mcbench.contracts import Id
from mcbench.control_lock import profile_operation
from mcbench.native_control_plan import TARGET
from mcbench.native_game import GameIdentity, NativeGameClient
from mcbench.native_repair_flow import NativeRepairFlow
from mcbench.storage import digest, require
from .bound_clocks import BoundClockSource


class RepairClockEvidence:
    def __init__(self, repairs):
        self.repairs, self.database = repairs, repairs.database
        self.flow = NativeRepairFlow(repairs)
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS repair_clock_marks (repair TEXT, mark TEXT, "
                       "source_binding TEXT NOT NULL, cursor INTEGER NOT NULL, source_ref TEXT NOT NULL, "
                       "PRIMARY KEY(repair,mark))")
            db.execute("CREATE TABLE IF NOT EXISTS repair_clock_barriers (repair TEXT, mark TEXT, "
                       "request_ref TEXT NOT NULL, PRIMARY KEY(repair,mark))")

    def _barrier_scope(self, repair, mark, owner, epoch, admission):
        return {"transaction_id": repair["id"], "mark": mark, "campaign_id": repair["campaign"],
            "owner": owner, "epoch": epoch, "controller_clock_id": self.repairs.clock_instance,
            "worker_plan_digest": digest(admission.worker_plan.model_dump()),
            "repair_deadline_mono": repair["request"]["deadline_mono"],
            "repair_deadline_unix": repair["request"]["deadline_unix"]}

    def request_barrier(self, transaction, mark, owner, epoch, worker, native, source):
        """Request one after-repair clock boundary without renewing the repair."""
        TypeAdapter(Id).validate_python(mark)
        require(isinstance(source, BoundClockSource), "CLOCK_SOURCE_REQUIRED")
        profile = self.repairs.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, _, admission = self.flow._context(transaction, owner, epoch, worker, native, False, observe=False)
            with self.database.transaction() as db:
                campaign = self.repairs.controller.owned(db, repair["campaign"], owner, epoch)
                agents = json.loads(campaign["config"])["agent_ids"]
                old = db.execute("SELECT request_ref FROM repair_clock_barriers WHERE repair=? AND mark=?",
                                 (transaction, mark)).fetchone()
                require(old is not None or db.execute("SELECT 1 FROM repair_clock_marks WHERE repair=? AND mark=?",
                        (transaction, mark)).fetchone() is None, "IDEMPOTENCY_CONFLICT")
                require(old is not None or db.execute("SELECT count(*) FROM repair_clock_barriers WHERE repair=?",
                        (transaction,)).fetchone()[0] < 32, "REPAIR_CLOCK_QUOTA")
            require((source.plan.mode == "synthetic-fixture") is self.repairs.controller.simulation,
                    "PROFILE_MISMATCH")
            require(source.setup.campaign_id == repair["campaign"] and source.setup.epoch == epoch
                    and set(source.setup.roster) == set(agents), "REPAIR_CLOCK_SCOPE")
            scope = self._barrier_scope(repair, mark, owner, epoch, admission)
            remaining = min(scope["repair_deadline_mono"] - self.repairs.monotonic(),
                            scope["repair_deadline_unix"] - self.repairs.clock())
            request = source.begin_barrier(digest(scope), scope, remaining)
            if old:
                require(self.repairs.controller.evidence(old["request_ref"]) == request, "CLOCK_BARRIER_CHANGED")
                return {"request_ref": old["request_ref"], "receipt_cursor_after": request["receipt_cursor_after"]}
            ref = self.flow._put(request)
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.repairs._budget(db, repair["request"])
                db.execute("INSERT INTO repair_clock_barriers VALUES (?,?,?)", (transaction, mark, ref))
                self.database.event(db, "repair.clock_requested", {"transaction_id": transaction,
                    "mark": mark, "request_ref": ref})
            return {"request_ref": ref, "receipt_cursor_after": request["receipt_cursor_after"]}

    def capture(self, transaction, mark, owner, epoch, worker, native, source, cursor=None):
        """Retain a sample with original repair authority and the actual body join.

        A requested barrier proves generation after its durable request, never
        freshness at this later read. Marks do not claim complete start/end
        coverage or permit settlement, publication or gameplay on their own.
        """
        TypeAdapter(Id).validate_python(mark)
        require(isinstance(source, BoundClockSource), "CLOCK_SOURCE_REQUIRED")
        profile = self.repairs.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, _, admission = self.flow._context(transaction, owner, epoch, worker, native, False, observe=False)
            old = self.database.connection.execute("SELECT * FROM repair_clock_marks WHERE repair=? AND mark=?",
                                                   (transaction, mark)).fetchone()
            barrier = self.database.connection.execute("SELECT request_ref FROM repair_clock_barriers WHERE repair=? AND mark=?",
                                                       (transaction, mark)).fetchone()
            request = self.repairs.controller.evidence(barrier["request_ref"]) if barrier else None
            if request:
                scope = self._barrier_scope(repair, mark, owner, epoch, admission)
                require(request["scope"] == scope and request["request_id"] == digest(scope), "REPAIR_CLOCK_SCOPE")
            if cursor is None and old:
                cursor = old["cursor"]
            def observe():
                return source.barrier_sample(request, cursor) if request else source.observe(cursor)
            with self.database.transaction() as db:
                campaign = self.repairs.controller.owned(db, repair["campaign"], owner, epoch)
                agents = json.loads(campaign["config"])["agent_ids"]
            if old:
                # Revalidate source ownership but retain the original observation
                # times and CAS bytes; this is not a new freshness observation.
                observed = observe()
                require(old["source_binding"] == observed["source_binding"] and old["cursor"] == cursor,
                        "IDEMPOTENCY_CONFLICT")
                saved = self.repairs.controller.evidence(old["source_ref"])
                require(saved["source"] == observed, "REPAIR_CLOCK_CHANGED")
                return {"source_ref": old["source_ref"], "complete_repair_accounting": False}
            marks = self.database.connection.execute("SELECT source_binding,cursor FROM repair_clock_marks WHERE repair=?",
                                                     (transaction,)).fetchall()
            require(len(marks) < 32, "REPAIR_CLOCK_QUOTA")
            began = self.repairs.monotonic()
            observed = observe()
            require(observed["is_example"] is self.repairs.controller.simulation, "PROFILE_MISMATCH")
            prefix = observed["prefix"]
            cursor = prefix["cursor"]
            require(prefix["campaign_id"] == repair["campaign"] and prefix["epoch"] == epoch
                    and set(observed["roster"]) == set(agents), "REPAIR_CLOCK_SCOPE")
            require(all(row["source_binding"] == observed["source_binding"] and row["cursor"] < cursor
                        for row in marks), "REPAIR_CLOCK_DISCONTINUITY")
            handoff = self.database.connection.execute("SELECT target FROM repair_native_handoffs WHERE id=?",
                                                       (transaction,)).fetchone()
            target = TARGET.validate_json(handoff["target"])
            identity = GameIdentity.model_validate(NativeGameClient(native.connection).call(
                "identity", {}, timeout_ms=self.flow._timeout(repair)))
            require(identity.body_fingerprint == target.body_fingerprint
                    == observed["body_fingerprints"][repair["agent"]], "REPAIR_CLOCK_BODY")
            end, wall = self.repairs.monotonic(), self.repairs.clock()
            require(end >= began >= repair["request"]["started_mono"], "REPAIR_CLOCK_DISCONTINUITY")
            witness = {"schema": "strata/RepairClockWitness/2" if request else "strata/RepairClockWitness/1",
                "is_example": self.repairs.controller.simulation,
                "transaction_id": transaction, "mark": mark, "worker_plan": admission.worker_plan.model_dump(),
                "source": observed, "native_identity": identity.model_dump(),
                "controller_clock_id": self.repairs.clock_instance, "read_started_mono": began,
                "read_finished_mono": end, "observed_unix": wall,
                "sample_generation_after_read_start_proven": False,
                "complete_repair_accounting": False, "consumption_settled": False,
                "campaign_permission_published": False}
            if request:
                witness.update(barrier_request_ref=barrier["request_ref"],
                               sample_generation_after_request_proven=True)
            ref = self.flow._put(witness)
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.repairs._budget(db, repair["request"])
                db.execute("INSERT INTO repair_clock_marks VALUES (?,?,?,?,?)",
                           (transaction, mark, observed["source_binding"], cursor, ref))
                self.database.event(db, "repair.clock_observed", {"transaction_id": transaction,
                    "mark": mark, "source_ref": ref, "source_binding": observed["source_binding"], "cursor": cursor})
            return {"source_ref": ref, "complete_repair_accounting": False}
