"""Continuous reserved avatar ticks across repairs; no inferred wall/body time.

One immutable window per campaign epoch. It starts at an authenticated sample,
not an invented zero or a retroactive campaign origin. Repair coverage requires
that window to predate the request and a causal sample after publication.
"""

import json
import time

from pydantic import TypeAdapter

from mcbench.budgets import Budgets, DIMENSIONS
from mcbench.contracts import Id
from mcbench.storage import Principal, canonical, digest, require
from mcbench.worker_publication import WorkerPublicationAccounting
from .bound_clocks import BoundClockSource
from .telemetry_clocks import ServerClockSample, advance_clock


class BodyTicks:
    def __init__(self, controller):
        self.controller, self.database = controller, controller.database
        self.budgets = Budgets(self.database)
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS body_tick_windows (id TEXT PRIMARY KEY, campaign TEXT, "
                       "epoch INTEGER, opening_cursor INTEGER, body TEXT, UNIQUE(campaign,epoch))")
            db.execute("CREATE TABLE IF NOT EXISTS body_tick_operations (operation TEXT PRIMARY KEY, window TEXT, agent TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS body_tick_samples (window TEXT, cursor INTEGER, ref TEXT, "
                       "body TEXT, PRIMARY KEY(window,cursor))")
            db.execute("CREATE TABLE IF NOT EXISTS body_tick_repair_barriers (repair TEXT PRIMARY KEY, window TEXT, "
                       "publication_ref TEXT, request_ref TEXT)")

    def _put(self, body):
        return self.controller.cas.put(Principal("operator", "operator"), self.controller.evidence_namespace,
                                       "operator", canonical(body))

    def _owned(self, db, campaign, owner, epoch, source):
        require(isinstance(source, BoundClockSource), "CLOCK_SOURCE_REQUIRED")
        row = self.controller.owned(db, campaign, owner, epoch)
        require(row["state"] == "RUNNING", "INVALID_TRANSITION")
        agents = set(json.loads(row["config"])["agent_ids"])
        require(source.setup.campaign_id == campaign and source.setup.epoch == epoch
                and set(source.setup.roster) == agents, "BODY_TICK_SCOPE")
        require((source.plan.mode == "synthetic-fixture") is self.controller.simulation, "PROFILE_MISMATCH")
        return agents

    def _operations(self, db, window):
        for agent, allocation in window["allocations"].items():
            require(type(allocation) is dict and set(allocation) == {"account", "operation"}, "BODY_TICK_ALLOCATION")
            for value in allocation.values():
                TypeAdapter(Id).validate_python(value)
            row = db.execute("SELECT o.*,a.campaign,a.agent FROM operations o JOIN accounts a ON a.id=o.account "
                             "WHERE o.id=?", (allocation["operation"],)).fetchone()
            require(row is not None and row["account"] == allocation["account"]
                    and row["campaign"] == window["campaign"] and row["agent"] == agent
                    and row["kind"] == "tool" and row["actual"] is None and not row["uncertain"], "BODY_TICK_RESERVATION")
            reserved = json.loads(row["reserved"])
            require(reserved["avatar_ticks"] is not None
                    and all(reserved[k] == 0 for k in DIMENSIONS if k != "avatar_ticks"), "BODY_TICK_RESERVATION")
            require(db.execute("SELECT 1 FROM budget_envelopes WHERE operation=?", (row["id"],)).fetchone() is None,
                    "BODY_TICK_RESERVATION")

    def open(self, window_id, campaign, owner, epoch, source, cursor, allocations):
        TypeAdapter(Id).validate_python(window_id)
        with self.database.transaction() as db:
            agents = self._owned(db, campaign, owner, epoch, source)
            require(type(allocations) is dict and set(allocations) == agents, "BODY_TICK_ROSTER")
        observed = source.observe(cursor)
        window = {"schema": "strata/BodyTickWindow/1", "id": window_id, "campaign": campaign,
            "epoch": epoch, "source_binding": observed["source_binding"], "origin": observed,
            "allocations": allocations, "is_example": self.controller.simulation}
        raw = canonical(window).decode()
        require(len(raw.encode()) <= 131072, "BODY_TICK_QUOTA")
        with self.database.transaction() as db:
            self._owned(db, campaign, owner, epoch, source)
            old = db.execute("SELECT body FROM body_tick_windows WHERE id=?", (window_id,)).fetchone()
            if old:
                require(old[0] == raw, "IDEMPOTENCY_CONFLICT")
                return window
            self._operations(db, window)
            require(db.execute("SELECT 1 FROM body_tick_windows WHERE campaign=? AND epoch=?", (campaign, epoch)).fetchone()
                    is None, "BODY_TICK_WINDOW_EXISTS")
            for agent, allocation in allocations.items():
                operation = allocation["operation"]
                require(not self.budgets.consumption_floors(db).get(operation), "BODY_TICK_DOUBLE_ALLOCATION")
                require(db.execute("SELECT 1 FROM body_tick_operations WHERE operation=?", (operation,)).fetchone()
                        is None, "BODY_TICK_DOUBLE_ALLOCATION")
                if db.execute("SELECT 1 FROM sqlite_master WHERE name='repairs'").fetchone():
                    require(db.execute("SELECT 1 FROM repairs WHERE budget_operation=?", (operation,)).fetchone()
                            is None, "BODY_TICK_DOUBLE_ALLOCATION")
                db.execute("INSERT INTO body_tick_operations VALUES (?,?,?)", (operation, window_id, agent))
                require(self.budgets.status(allocation["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")
            event = self.database.event(db, "body_ticks.opened", window)
            db.execute("INSERT INTO body_tick_windows VALUES (?,?,?,?,?)", (window_id, campaign, epoch, event, raw))
        return window

    def _window(self, db, window_id, owner, epoch, source):
        row = db.execute("SELECT * FROM body_tick_windows WHERE id=?", (window_id,)).fetchone()
        require(row is not None and row["epoch"] == epoch, "BODY_TICK_WINDOW_REQUIRED")
        window = json.loads(row["body"])
        self._owned(db, row["campaign"], owner, epoch, source)
        self._operations(db, window)
        opening = db.execute("SELECT kind,body FROM outbox WHERE cursor=?", (row["opening_cursor"],)).fetchone()
        require(opening is not None and opening["kind"] == "body_ticks.opened"
                and json.loads(opening["body"]) == window, "BODY_TICK_CHANGED")
        require(source.observe(window["origin"]["prefix"]["cursor"]) == window["origin"], "BODY_TICK_CHANGED")
        return row, window

    def _check_bounds(self, window, body):
        for agent, a in window["allocations"].items():
            reserved = json.loads(self.database.connection.execute(
                "SELECT reserved FROM operations WHERE id=?", (a["operation"],)).fetchone()[0])
            floor = self.budgets.consumption_floors(self.database.connection).get(a["operation"], {}).get("avatar_ticks", 0)
            require(max(floor, body["avatar_ticks"][agent]) <= reserved["avatar_ticks"]
                    and self.budgets.status(a["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")

    def advance(self, window_id, owner, epoch, source, cursor):
        # Read the source before taking the controller writer lock: its broker may
        # share this database and must remain free to commit its own receipts.
        require(isinstance(source, BoundClockSource), "CLOCK_SOURCE_REQUIRED")
        observed = source.observe(cursor)
        ref = "cas:sha256:" + digest(observed)
        with self.database.transaction() as db:
            _, window = self._window(db, window_id, owner, epoch, source)
            require(observed["source_binding"] == window["source_binding"]
                    and observed["roster"] == window["origin"]["roster"], "BODY_TICK_CHANGED")
            origin = window["origin"]["prefix"]
            require(cursor > origin["cursor"], "BODY_TICK_ORDER")
            old = db.execute("SELECT * FROM body_tick_samples WHERE window=? AND cursor=?", (window_id, cursor)).fetchone()
            if old:
                require(old["ref"] == ref and json.loads(old["body"])["observed"] == observed, "BODY_TICK_CHANGED")
            previous = db.execute("SELECT body FROM body_tick_samples WHERE window=? ORDER BY cursor DESC LIMIT 1",
                                  (window_id,)).fetchone()
            before = origin["clock"]
            if previous:
                previous = json.loads(previous[0])
                require(old is not None or cursor > previous["cursor"], "BODY_TICK_ORDER")
                before = (observed if old else previous["observed"])["prefix"]["clock"]
            require(old is not None or db.execute("SELECT count(*) FROM body_tick_samples WHERE window=?", (window_id,)).fetchone()[0] < 128,
                    "BODY_TICK_QUOTA")
            current = ServerClockSample.model_validate(observed["prefix"]["clock"])
            advance_clock(ServerClockSample.model_validate(before), current)
            start = ServerClockSample.model_validate(origin["clock"])
            totals = {agent: current.avatar_tick_events.get(actor, 0) - start.avatar_tick_events.get(actor, 0)
                      for agent, actor in observed["roster"].items()}
            require(all(v >= 0 for v in totals.values()), "BODY_TICK_ORDER")
            body = {"schema": "strata/BodyTickConsumption/1", "window_id": window_id,
                "cursor": cursor, "source_ref": ref, "window_digest": digest(window), "avatar_ticks": totals,
                "observed": observed,
                "complete_repair_accounting": False, "consumption_settled": False}
            raw = canonical(body).decode()
            require(len(raw.encode()) <= 131072, "BODY_TICK_QUOTA")
            if old:
                require(old["body"] == raw, "BODY_TICK_CHANGED")
            else:
                for agent, allocation in window["allocations"].items():
                    self.budgets.retain_consumption_floor(db, allocation["account"], allocation["operation"],
                        "body-ticks:" + digest(body), "avatar_ticks", totals[agent],
                        {"window_id": window_id, "sample_ref": ref, "body_digest": digest(body)})
                db.execute("INSERT INTO body_tick_samples VALUES (?,?,?,?)", (window_id, cursor, ref, raw))
                self.database.event(db, "body_ticks.consumed", body)
        # Store the verified source and consumption first: a later CAS fault may
        # not erase real ticks. Retrying repairs only the missing evidence copy.
        require(self._put(observed) == ref, "BODY_TICK_CHANGED")
        # Actual overruns survive refusal; every original reservation remains held.
        self._check_bounds(window, body)
        return body

    def request_repair_coverage(self, window_id, repairs, transaction, owner, epoch, source):
        """Request the closing sample only after immutable publication evidence."""
        require(repairs.controller is self.controller, "BODY_TICK_SCOPE")
        with self.database.transaction() as db:
            row, window = self._window(db, window_id, owner, epoch, source)
            repair = repairs.status(transaction)
            repairs._owned(db, repair, owner, epoch, unexpired=False)
            require(repair["campaign"] == window["campaign"], "BODY_TICK_SCOPE")
            requested = db.execute("SELECT cursor FROM outbox WHERE kind='repair.requested' "
                "AND json_extract(body,'$.transaction_id')=?", (transaction,)).fetchall()
            require(len(requested) == 1 and row["opening_cursor"] < requested[0][0], "BODY_TICK_OPENED_TOO_LATE")
            allocation = window["allocations"][repair["agent"]]
            require(allocation["operation"] != repair["budget_operation"], "BODY_TICK_DOUBLE_ALLOCATION")
            operation = db.execute("SELECT reserved FROM operations WHERE id=?", (repair["budget_operation"],)).fetchone()
            require(json.loads(operation[0])["avatar_ticks"] == 0
                    and self.budgets.consumption_floors(db).get(repair["budget_operation"], {}).get("avatar_ticks", 0) == 0,
                    "BODY_TICK_DOUBLE_ALLOCATION")
            require(db.execute("SELECT 1 FROM sqlite_master WHERE name='repair_publication_evidence'").fetchone(),
                    "CONTROL_PUBLICATION_UNCONFIRMED")
            publication = db.execute("SELECT source_ref FROM repair_publication_evidence WHERE id=?", (transaction,)).fetchone()
            require(publication is not None, "CONTROL_PUBLICATION_UNCONFIRMED")
            published = self.controller.evidence(publication[0])
            require(published["schema"] == "strata/ControllerPublicationEvidence/1"
                    and published["transaction_id"] == transaction, "BODY_TICK_SCOPE")
            plan = WorkerPublicationAccounting.model_validate(published["worker_receipt"]).commit.decision.worker_plan
            require(plan.campaign_id == window["campaign"] and plan.agent_id == repair["agent"]
                    and plan.epoch == epoch and plan.transaction_id == transaction, "BODY_TICK_SCOPE")
            # Match the original admitted native body, not merely the avatar label.
            target = db.execute("SELECT target FROM repair_native_handoffs WHERE id=? AND phase='CONFIRMED'",
                                (transaction,)).fetchone()
            require(target is not None and json.loads(target[0])["body_fingerprint"]
                    == window["origin"]["body_fingerprints"][repair["agent"]], "BODY_TICK_SCOPE")
        scope = {"window_id": window_id, "window_digest": digest(window), "repair": transaction,
                 "publication_ref": publication[0]}
        request = source.begin_barrier(digest(scope), scope, min(900, source.broker.deadline - time.monotonic()))
        ref = self._put(request)
        with self.database.transaction() as db:
            repairs._owned(db, repairs.status(transaction), owner, epoch, unexpired=False)
            old = db.execute("SELECT * FROM body_tick_repair_barriers WHERE repair=?", (transaction,)).fetchone()
            if old:
                require(old["window"] == window_id and old["publication_ref"] == publication[0]
                        and old["request_ref"] == ref, "BODY_TICK_CHANGED")
            else:
                db.execute("INSERT INTO body_tick_repair_barriers VALUES (?,?,?,?)", (transaction, window_id, publication[0], ref))
                self.database.event(db, "body_ticks.repair_closing_requested", scope | {"request_ref": ref})
        return {"request_ref": ref}

    def cover_repair(self, window_id, repairs, transaction, owner, epoch, source, cursor=None):
        request = self.request_repair_coverage(window_id, repairs, transaction, owner, epoch, source)
        barrier = self.controller.evidence(request["request_ref"])
        observed = source.barrier_sample(barrier, cursor)
        consumed = self.advance(window_id, owner, epoch, source, observed["prefix"]["cursor"])
        # The continuous operation includes surrounding gameplay. These totals
        # must never be represented as an exact per-repair tick delta or reposted.
        return {"schema": "strata/RepairBodyTickCoverage/1", "window_id": window_id,
            "transaction_id": transaction, "closing_request_ref": request["request_ref"],
            "continuous_consumption": consumed, "repair_tick_cost_reposted": False,
            "exact_repair_ticks": None, "complete_repair_accounting": False,
            "campaign_permission_published": False}
